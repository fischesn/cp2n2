"""Offline integrity and causal-identity checks for R2 SDK success bundles."""

from __future__ import annotations

import json
from pathlib import Path

from applications.biopattern_gate.control_plane_contract import BACKEND_ID, TASK_METADATA
from evaluation.biopattern_gate_native import file_sha256, verify_native_execution
from mcp_surface.audit import JsonlHashChainAuditTrail
from runtimes.biopattern_gate_e3_runtime import application_source_digest
from runtimes.biopattern_gate_sdk_runtime import SDK_APP_ROOT


def verify_sdk_bundle(directory: Path) -> dict:
    directory = Path(directory).resolve(strict=True)

    def read(name):
        return json.loads((directory / name).read_text(encoding="utf-8"))

    def check(condition, message):
        if not condition:
            raise ValueError(message)

    manifest = read("manifest.json")
    check(manifest.get("schema_version") == "r2-sdk-bundle-v1", "unsupported bundle schema")
    check(manifest.get("runtime_kind") == "sdk_simulator" and manifest.get("evidence_level") == "E3"
          and manifest.get("biological_claim") is False, "bundle evidence mismatch")
    check(manifest.get("sdk_run_id_origin") == "controller_assigned" and
          manifest.get("provider_execution_id") is None, "unsupported provider identity claim")
    expected_files = manifest["files"]
    observed_files = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()
                      and p.relative_to(directory).as_posix() not in {"manifest.json", "verification.json"}}
    check(set(expected_files) == observed_files, "bundle file inventory mismatch")
    for name, digest in expected_files.items():
        path = (directory / name).resolve(strict=True)
        check(path.is_relative_to(directory), "artifact path escapes bundle")
        check(file_sha256(path) == digest, f"artifact checksum mismatch: {name}")
    transcript, record, final = read("transcript.json"), read("run-record.json"), read("final-state.json")
    check(transcript["client_kind"] == manifest["client_kind"] == "deterministic_non_llm",
          "client kind mismatch")
    calls = [step for step in transcript["steps"] if step["tool"] is not None]
    audit_path = directory / "audit.jsonl"
    check(audit_path.is_file(), "missing audit")
    audit = JsonlHashChainAuditTrail(audit_path)
    events = audit.events()
    check(audit.verify() is True, "invalid audit chain")
    check(manifest["mcp_call_count"] == len(calls) and manifest["audit_event_count"] == len(events),
          "observed call/event count mismatch")
    check(len(events) == len(calls) * 2, "incomplete request/completion audit pairs")
    for index, call in enumerate(calls):
        received, completed = events[2 * index:2 * index + 2]
        check(received.phase == "received" and completed.phase == "completed", "invalid audit phase order")
        check(received.request_id == completed.request_id == call["request_id"] and
              received.tool == completed.tool == call["tool"] and
              received.principal_id == completed.principal_id == manifest["principal_id"],
              "audit/transcript identity mismatch")
        check(call["ok"] is True and completed.outcome == "success", "success bundle has a denied call")
    run_call = next(step for step in calls if step["tool"] == "run_assay")
    run_event = next(event for event in events if event.request_id == run_call["request_id"] and event.phase == "received")
    check(manifest["run_request_id"] == run_call["request_id"] and
          run_event.arguments["run_id"] == record["run_id"] == manifest["application_run_id"],
          "MCP request/run mismatch")
    reservation = next(step["result"] for step in calls if step["tool"] == "reserve_resource")
    check(reservation["lease_id"] == record["lease_id"] == manifest["lease_id"], "lease identity mismatch")
    task = record["task"]
    core_hash = application_source_digest()
    check(task["metadata"] == {**TASK_METADATA, "application_source_sha256": core_hash},
          "task configuration/source binding mismatch")
    check(record["owner_id"] == task["client_id"] == manifest["principal_id"] and
          record["resource_id"] == task["direct_backend_id"] == manifest["resource_id"] == BACKEND_ID and
          task["task_id"] == manifest["task_id"] == f"mcp-assay-{record['run_id']}" and
          task["lease_id"] == record["lease_id"], "principal/task/resource binding mismatch")
    attempt_dir = (directory / "attempts" / manifest["execution_attempt_id"]).resolve(strict=True)
    check(attempt_dir.parent == (directory / "attempts").resolve(), "attempt path escapes bundle namespace")
    attempt = json.loads((attempt_dir / "attempt.json").read_text(encoding="utf-8"))
    for key in ("principal_id", "task_id", "resource_id", "lease_id", "application_run_id", "execution_attempt_id",
                "sdk_run_id", "sdk_run_id_origin", "config_sha256", "decoder_sha256",
                "application_source_sha256", "sdk_application_source_sha256"):
        check(attempt[key] == manifest[key], f"attempt/manifest mismatch: {key}")
    check(attempt["exit_code"] == 0 and attempt["status"] == "exited", "SDK process did not complete")
    check(run_event.arguments.get("idempotency_key_sha256") ==
          JsonlHashChainAuditTrail._digest(attempt["idempotency_key"]), "request/attempt idempotency mismatch")
    check(reservation["lease_version"] == record["lease_version"] == task["expected_lease_version"] ==
          attempt["expected_lease_version"], "lease version mismatch")
    check(attempt["application_source_sha256"] == core_hash and
          attempt["sdk_application_source_sha256"] == application_source_digest(SDK_APP_ROOT / "src"),
          "SDK source version mismatch")
    sdk_config = json.loads((attempt_dir / "sdk-config.json").read_text(encoding="utf-8"))
    check(sdk_config == {"name": "CP2N2 R2 technical E3", "timeout_s": 30, "preset_id": "technical-e3",
                         "config_sha256": TASK_METADATA["config_sha256"],
                         "decoder_sha256": TASK_METADATA["decoder_sha256"], "run_id": manifest["sdk_run_id"]},
          "SDK configuration substitution")
    recordings = list((attempt_dir / "sdk-output").glob("*.h5"))
    check(len(recordings) == 1, "wrong native recording count")
    native = verify_native_execution(recordings[0], attempt_dir / "sdk-output" / "result.json",
                                     expected_run_id=manifest["sdk_run_id"])
    stored = json.loads((attempt_dir / "native-validation.json").read_text(encoding="utf-8"))
    check(native == stored, "native validation report substitution")
    check(native["native_recording_sha256"] == manifest["native_recording_sha256"], "native checksum mismatch")
    summary = transcript["result_summary"]
    check(record["state"] == "succeeded" and record["summary"] == summary and summary["success"] is True,
          "delivered result is not successful or differs from stored result")
    check(run_call["result"]["summary"] == summary, "run/result-summary mismatch")
    application = summary["application"]
    check(application["native_validation_verified"] is True and application["application_status"] == "complete",
          "unvalidated success")
    for key in ("sdk_run_id", "sdk_run_id_origin", "config_sha256", "decoder_sha256", "native_recording_sha256",
                "trial_count", "scored_trial_count", "sham_trial_count", "pipeline_assertion_accuracy"):
        check(application[key] == native[key], f"native/sanitized result mismatch: {key}")
    check(application["execution_attempt_id"] == attempt["execution_attempt_id"] and
          application["application_run_id"] == record["run_id"], "sanitized identity mismatch")
    correlation = manifest["orchestration_correlation_id"]
    history = transcript["lifecycle_history"]
    check(history == record["result"]["lifecycle_history"] and
          all(row["correlation_id"] == correlation and row["resource_id"] == BACKEND_ID for row in history),
          "lifecycle correlation mismatch")
    check([row["to_state"] for row in history] == ["preparing", "running", "validating", "cooldown", "ready"],
          "unexpected successful lifecycle")
    check(final["lease"] is None and final["lifecycle"]["state"] == "ready", "resource not finalized")
    return {"verified": True, "bundle": str(directory), "purpose": manifest["purpose"],
            "mcp_call_count": len(calls), "audit_event_count": len(events),
            "execution_attempt_id": manifest["execution_attempt_id"], "sdk_run_id": manifest["sdk_run_id"],
            "trial_count": native["trial_count"], "stim_count": native["stim_count"], "spike_count": native["spike_count"],
            "pipeline_assertion_accuracy": native["pipeline_assertion_accuracy"], "lease_released": True,
            "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False}
