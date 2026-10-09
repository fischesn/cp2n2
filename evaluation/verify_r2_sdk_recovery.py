"""Independent offline checks for case-level SDK cancellation evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

from cl import RecordingView

from applications.biopattern_gate.control_plane_contract import BACKEND_ID, CONFIG_SHA256, DECODER_SHA256, TASK_METADATA
from core.lifecycle import ALLOWED_TRANSITIONS
from evaluation.biopattern_gate_native import file_sha256, verify_native_execution
from mcp_surface.audit import JsonlHashChainAuditTrail


CASES = ("success", "invalid_configuration", "launch_failure", "cooperative_abort", "sdk_crash",
         "validation_failure", "lost_reply_duplicate", "timeout_confirmed", "timeout_unconfirmed")


def native_status(path: Path, run_id: str) -> dict:
    """Truthful partial status: a crash file is not repaired into an abort."""
    try:
        with RecordingView(str(path)) as view:
            application = dict(view.attributes).get("application", {})
            if application.get("run_id") != run_id:
                raise ValueError("native run identity mismatch")
            if application.get("runtime_kind") != "sdk_simulator" or application.get("biological_claim") is not False:
                raise ValueError("native evidence mismatch")
            streams = view.data_streams
            return {"readable": True, "terminal_state": application.get("terminal_state", "unfinalized"),
                    "decision_count": len(list(streams["pattern_gate_decision"].items())),
                    "feature_count": len(list(streams["pattern_gate_features"].items())),
                    "stim_count": 0 if view.stims is None else len(view.stims),
                    "spike_count": 0 if view.spikes is None else len(view.spikes)}
    except ValueError:
        raise
    except Exception as exc:
        return {"readable": False, "terminal_state": "unreadable_or_unfinalized", "error_type": type(exc).__name__}


def verify_recovery_case(directory: Path, *, source_bindings: dict | None = None) -> dict:
    root = Path(directory).resolve(strict=True)
    def read(name):
        return json.loads((root / name).read_text(encoding="utf-8"))
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    manifest = read("manifest.json")
    case = manifest["case"]
    require(manifest["schema_version"] == "r2-recovery-case-v1", "unknown case schema")
    require(case in CASES and manifest["protocol"] == "r2-recovery-v1", "unknown case/protocol")
    require(manifest["evidence_level"] == "E3" and manifest["runtime_kind"] == "sdk_simulator" and
            manifest["biological_claim"] is False, "evidence boundary mismatch")
    inventory = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                 and p.relative_to(root).as_posix() not in {"manifest.json", "verification.json"}}
    require(inventory == set(manifest["files"]), "file inventory mismatch")
    for name, digest in manifest["files"].items():
        path = (root / name).resolve(strict=True)
        require(path.is_relative_to(root) and file_sha256(path) == digest, f"artifact hash/path mismatch: {name}")
    transcript, final = read("calls.json"), read("final-state.json")
    require(transcript["client_kind"] == "deterministic_non_llm", "client kind mismatch")
    events = JsonlHashChainAuditTrail(root / "audit.jsonl").events()
    calls = transcript["calls"]
    require(len(events) == 2 * len(calls), "unpaired audit calls")
    require(manifest["mcp_call_count"] == len(calls) and manifest["audit_event_count"] == len(events), "call/event denominator mismatch")
    for call in calls:
        pair = [event for event in events if event.request_id == call["response"]["request_id"]]
        require(len(pair) == 2 and [event.phase for event in pair] == ["received", "completed"], "invalid request audit pair")
        require(all(event.tool == call["tool"] and event.principal_id == manifest["principal_id"] for event in pair),
                "principal/tool mismatch")
        require(pair[0].argument_digest == JsonlHashChainAuditTrail._digest(call["arguments"]), "argument binding mismatch")
        require((pair[1].outcome == "success") == call["response"]["ok"], "response/audit outcome mismatch")
    starts = list((root / "attempts").glob("*/sdk-started.json"))
    require(len(starts) == manifest["sdk_start_count"], "SDK start count mismatch")
    require(final["lease"] is None and final["lifecycle"]["state"] == "ready", "resource not finally usable/unleased")
    require(final["worker_done"] is True, "original worker still active")
    history = read("lifecycle.json")["history"]
    state, state_version = "discovered", 0
    for row in history:
        require(row["resource_id"] == BACKEND_ID and row["from_state"] == state and
                row["from_version"] == state_version and row["to_version"] == state_version + 1 and
                row["to_state"] in ALLOWED_TRANSITIONS[state], "lifecycle chain mismatch")
        state, state_version = row["to_state"], row["to_version"]
    require(final["lifecycle"]["resource_id"] == BACKEND_ID and final["lifecycle"]["state"] == state and
            final["lifecycle"]["version"] == state_version, "final lifecycle version mismatch")
    if case == "invalid_configuration":
        require(not starts and not list((root / "attempts").glob("*")), "invalid configuration started SDK")
        denied = next(c for c in calls if c["tool"] == "prepare_assay" and "config_sha256" in c["arguments"])
        require(denied["response"]["ok"] is False and denied["response"]["error"]["code"] == "INVALID_REQUEST",
                "configuration override not rejected")
        return {"verified": True, "case": case, "sdk_start_count": 0, "mcp_call_count": len(calls), "audit_event_count": len(events)}
    record = read("run-record.json")
    attempt_dirs = list((root / "attempts").iterdir())
    require(len(attempt_dirs) == 1, "more than one execution attempt")
    attempt_dir = attempt_dirs[0]
    attempt = json.loads((attempt_dir / "attempt.json").read_text(encoding="utf-8"))
    require(record["run_id"] == attempt["application_run_id"] and record["task"]["task_id"] == attempt["task_id"] and
            record["owner_id"] == attempt["principal_id"] == manifest["principal_id"] and
            record["resource_id"] == attempt["resource_id"] == BACKEND_ID and
            record["lease_id"] == attempt["lease_id"], "execution identity mismatch")
    require(attempt["config_sha256"] == CONFIG_SHA256 and attempt["decoder_sha256"] == DECODER_SHA256 and
            attempt["runtime_kind"] == "sdk_simulator" and attempt["evidence_level"] == "E3" and
            attempt["sdk_run_id_origin"] == "controller_assigned", "attempt preset/evidence mismatch")
    require(attempt["execution_attempt_id"] == attempt_dir.name, "attempt directory mismatch")
    require(record["task"]["metadata"] == {**TASK_METADATA, "application_source_sha256": attempt["application_source_sha256"]}
            and record["task"]["task_id"] == f"mcp-assay-{record['run_id']}" and
            record["task"]["client_id"] == record["owner_id"] and record["task"]["lease_id"] == record["lease_id"] and
            record["lease_version"] == attempt["expected_lease_version"], "task/source/lease binding mismatch")
    if source_bindings is not None:
        require(all(attempt[key] == value for key, value in source_bindings.items()), "archived application source mismatch")
    config = json.loads((attempt_dir / "sdk-config.json").read_text(encoding="utf-8"))
    require(config == {"name": "CP2N2 R2 technical E3", "timeout_s": 30, "preset_id": "technical-e3",
                       "config_sha256": CONFIG_SHA256, "decoder_sha256": DECODER_SHA256,
                       "run_id": attempt["sdk_run_id"]}, "SDK configuration substitution")
    require(all(row in history for row in record["result"]["lifecycle_history"]), "result lifecycle substitution")
    run_calls = [c for c in calls if c["tool"] == "run_assay"]
    require(all(c["arguments"]["run_id"] == record["run_id"] for c in run_calls), "MCP run identity mismatch")
    require(run_calls[0]["arguments"]["idempotency_key"] == attempt["idempotency_key"], "attempt retry binding mismatch")
    require(record["summary"] == run_calls[0]["response"]["result"]["summary"], "delivered/stored result mismatch")
    summary = record["summary"]
    positive = case in {"success", "lost_reply_duplicate"}
    require(summary["success"] is positive and summary["raw_output_included"] is False, "success/sanitization mismatch")
    if case == "launch_failure":
        require(not starts and not list((attempt_dir / "sdk-output").glob("*.h5")), "launch failure started SDK")
        require(summary["error_code"] == "INVOCATION_FAILED", "launch failure type mismatch")
    else:
        require(len(starts) == 1, "case did not execute exactly one SDK run")
        started = json.loads(starts[0].read_text(encoding="utf-8"))
        require(started["sdk_run_id"] == attempt["sdk_run_id"], "SDK start/run mismatch")
        term = json.loads((attempt_dir / "termination.json").read_text(encoding="utf-8"))
        require(term["mechanism"] == "windows_job_object" and term["contained"] is True and
                term["termination_confirmed"] is True and term["active_process_count"] == 0,
                "SDK tree termination not confirmed")
        recordings = list((attempt_dir / "sdk-output").glob("*.h5"))
        require(len(recordings) == 1, "native evidence missing or duplicated")
        if positive:
            native = verify_native_execution(recordings[0], attempt_dir / "sdk-output" / "result.json",
                                              expected_run_id=attempt["sdk_run_id"])
            require(summary["application"]["native_validation_verified"] is True, "positive result not validated")
            require(summary["application"]["sdk_run_id"] == attempt["sdk_run_id"] and
                    summary["application"]["execution_attempt_id"] == attempt["execution_attempt_id"] and
                    summary["application"]["application_run_id"] == record["run_id"], "sanitized run identity mismatch")
            for key in ("native_recording_sha256", "trial_count", "scored_trial_count", "sham_trial_count", "pipeline_assertion_accuracy"):
                require(summary["application"][key] == native[key], f"native/sanitized mismatch: {key}")
        elif case == "validation_failure":
            require(summary["error_code"] == "POSTCONDITION_FAILED", "invalid result not rejected")
            try:
                verify_native_execution(recordings[0], attempt_dir / "sdk-output" / "result.json", expected_run_id=attempt["sdk_run_id"])
            except ValueError:
                pass
            else:
                raise ValueError("validation-failure native negative control is actually valid")
        else:
            status = native_status(recordings[0], attempt["sdk_run_id"])
            require(status == read("native-status.json"), "partial status substitution")
            require(not (attempt_dir / "sdk-output" / "result.json").exists(), "partial run published complete result")
            if case != "sdk_crash":
                require(status["readable"] is True and status["terminal_state"] == "aborted" and status["decision_count"] == 2
                        and status["stim_count"] == 2 and status["spike_count"] > 0,
                        "cooperative partial recording mismatch")
                partial = json.loads((attempt_dir / "sdk-output" / "partial-result.json").read_text(encoding="utf-8"))
                require(partial["sdk_run_id"] == attempt["sdk_run_id"] and partial["success"] is False and
                        partial["completed_decision_count"] == status["decision_count"], "partial summary mismatch")
            else:
                require(attempt["exit_code"] != 0 and status["terminal_state"] != "complete", "crash disguised as completion")
    if case == "cooperative_abort":
        require(record["state"] == "aborted" and record["abort_requested"] is True, "owner abort state mismatch")
        require(any(c["tool"] == "abort_run" and c["response"]["ok"] for c in calls), "missing owner abort")
    if case == "lost_reply_duplicate":
        require(len(run_calls) == 2 and run_calls[1]["response"]["ok"] is False, "duplicate unexpectedly accepted")
        recovered = next(c for c in calls if c["tool"] == "get_result_summary")
        require(recovered["response"]["result"]["summary"] == summary, "lost reply recovery differs")
    if case.startswith("timeout_"):
        require(summary["error_code"] == "EXECUTION_STATUS_UNKNOWN", "timeout type mismatch")
    if case == "timeout_unconfirmed":
        interim = read("quarantine.json")
        require(interim["lifecycle"]["state"] == "unreachable" and interim["process_observation"]["active_process_count"] > 0,
                "unknown completion did not quarantine active SDK")
        require(any(c["tool"] == "reserve_resource" and c["response"]["ok"] is False for c in calls), "quarantine reuse not rejected")
        require(read("reconciliation.json")["success"] is True, "late cleanup not explicitly reconciled")
    return {"verified": True, "case": case, "sdk_start_count": len(starts), "mcp_call_count": len(calls),
            "audit_event_count": len(events), "result_success": positive, "lease_released": True, "final_state": "ready"}


def verify_recovery_campaign(directory: Path) -> dict:
    root = Path(directory).resolve(strict=True)
    manifest = json.loads((root / "campaign.json").read_text(encoding="utf-8"))
    if manifest["protocol"] != "r2-recovery-v1" or manifest["case_order"] != list(CASES) or manifest["repetitions"] != 2:
        raise ValueError("campaign design differs from frozen protocol")
    if set(manifest["inputs"]) != {"protocol.md", "source-snapshot.zip"}:
        raise ValueError("campaign input inventory mismatch")
    for name, digest in manifest["inputs"].items():
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or file_sha256(path) != digest:
            raise ValueError("campaign input hash mismatch")
    if json.loads((root / "failures.json").read_text(encoding="utf-8"))["failures"]:
        raise ValueError("campaign contains reported failures")
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        def digest(prefix):
            result = hashlib.sha256()
            names = sorted(name for name in archive.namelist() if name.startswith(prefix) and
                           Path(name).suffix in {".py", ".json"})
            if not names:
                raise ValueError("application sources missing from snapshot")
            for name in names:
                content = archive.read(name).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
                result.update(name.removeprefix(prefix).encode("utf-8") + b"\0" + content.encode("utf-8") + b"\0")
            return result.hexdigest()
        source_bindings = {"application_source_sha256": digest("applications/biopattern_gate/"),
                           "sdk_application_source_sha256": digest("cl-apps/cp2n2-biopattern-gate/src/")}
        if digest("cl-apps/cp2n2-biopattern-gate/src/biopattern_gate/") != source_bindings["application_source_sha256"]:
            raise ValueError("archived SDK core differs from canonical application")
    cases = []
    for repeat in (1, 2):
        folder = root / f"repeat-{repeat:02d}"
        if {path.name for path in folder.iterdir() if path.is_dir()} != set(CASES):
            raise ValueError("campaign case inventory mismatch")
        for case in CASES:
            path = folder / case
            if file_sha256(path / "protocol.md") != manifest["inputs"]["protocol.md"]:
                raise ValueError("per-case protocol differs from frozen campaign")
            cases.append(verify_recovery_case(path, source_bindings=source_bindings))
    return {"verified": True, "protocol": manifest["protocol"], "case_execution_count": len(cases),
            "verified_case_count": sum(report["verified"] for report in cases),
            "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False, "cases": cases}
