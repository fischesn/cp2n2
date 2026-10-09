"""Run the frozen, non-LLM R2 SDK recovery conformance campaign."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from threading import RLock
from time import monotonic, sleep
from unittest.mock import patch
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.biopattern_gate_sdk_adapter import BioPatternGateSDKAdapter
from applications.biopattern_gate.control_plane_contract import BACKEND_ID
from cl import RecordingView
from evaluation.biopattern_gate_native import file_sha256, verify_native_execution
from evaluation.verify_r2_sdk_recovery import CASES, native_status, verify_recovery_campaign, verify_recovery_case
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_biopattern_gate_sdk_e3 import build_sdk_surface
import tables


PROTOCOL = ROOT / "docs" / "revision" / "r2-recovery-protocol.md"


def wait_checkpoint(runtime, timeout_s=20):
    deadline = monotonic() + timeout_s
    while monotonic() < deadline:
        directory = runtime.attempt_directory
        if directory and (directory / "checkpoint.json").is_file():
            value = json.loads((directory / "checkpoint.json").read_text(encoding="utf-8"))
            if value["sdk_run_id"] != runtime.attempt["sdk_run_id"] or value["completed_decision_count"] != 2:
                raise RuntimeError("SDK diagnostic checkpoint binding mismatch")
            return
        if directory and runtime._worker_done.is_set():
            raise RuntimeError("SDK ended before diagnostic checkpoint")
        sleep(0.02)
    raise RuntimeError("SDK checkpoint not reached before harness deadline")


def run_case(directory: Path, case: str) -> dict:
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    surface = build_sdk_surface(directory)
    runtime = surface.orchestrator.registry.get_adapter(BACKEND_ID).runtime
    calls, lock = [], RLock()
    def call(tool, arguments):
        response = surface.invoke(tool, arguments)
        with lock:
            calls.append({"tool": tool, "arguments": arguments, "response": response.model_dump(mode="json")})
        return response
    call("discover_resources", {"include_unavailable": True, "limit": 100})
    reservation = call("reserve_resource", {"resource_id": BACKEND_ID, "ttl_seconds": 60})
    if not reservation.ok:
        raise RuntimeError("positive reservation failed")
    prepare_args = {"resource_id": BACKEND_ID, "preset_id": "pattern_gate_v1", "dry_run": False,
                    "lease_id": reservation.result["lease_id"], "expected_lease_version": reservation.result["lease_version"]}
    if case == "invalid_configuration":
        call("prepare_assay", {**prepare_args, "config_sha256": "0" * 64})
        call("release_resource", {"resource_id": BACKEND_ID, "lease_id": reservation.result["lease_id"]})
    else:
        prepared = call("prepare_assay", prepare_args)
        if not prepared.ok:
            raise RuntimeError("positive preparation failed")
        run_id = prepared.result["run_id"]
        run_args = {"run_id": run_id, "idempotency_key": f"recovery-{run_id}"}
        if case == "launch_failure":
            runtime._python_executable = str(directory / "deliberately-absent-python.exe")
        if case in {"cooperative_abort", "sdk_crash", "timeout_confirmed", "timeout_unconfirmed"}:
            runtime._diagnostic_pause_after_decisions = 2
        if case.startswith("timeout_"):
            # Host-owned fixture only; this setting is not a tool argument.
            surface.run_store._records[run_id].task.invocation_timeout_ms = 12_000
        if case == "validation_failure":
            def corrupt_native(recording, result, *, expected_run_id):
                with RecordingView(str(recording)) as view:
                    node = view.spikes._v_pathname
                with tables.open_file(recording, mode="a") as file:
                    file.get_node(node).cols.channel[0] = 63
                return verify_native_execution(recording, result, expected_run_id=expected_run_id)
            with patch("adapters.biopattern_gate_sdk_adapter.verify_native_execution", corrupt_native):
                call("run_assay", run_args)
        elif case in {"cooperative_abort", "sdk_crash", "timeout_confirmed", "timeout_unconfirmed"}:
            with ThreadPoolExecutor(max_workers=1) as executor:
                if case == "timeout_unconfirmed":
                    try:
                        with patch.object(runtime, "abort", return_value=False):
                            future = executor.submit(call, "run_assay", run_args)
                            wait_checkpoint(runtime)
                            future.result(timeout=20)
                            snapshot = surface.orchestrator.registry.lifecycle_store.snapshot(BACKEND_ID)
                            write_json(directory / "quarantine.json", {
                                "lifecycle": snapshot.model_dump(mode="json"),
                                "process_observation": runtime._guard.observe(),
                            })
                            call("reserve_resource", {"resource_id": BACKEND_ID})
                    finally:
                        # The patch has unwound even if the checkpoint failed.
                        if not runtime.abort():
                            raise RuntimeError("late SDK cleanup did not confirm termination")
                    reconciliation = surface.orchestrator.reconcile_backend(BACKEND_ID)
                    write_json(directory / "reconciliation.json", reconciliation.model_dump(mode="json"))
                else:
                    future = executor.submit(call, "run_assay", run_args)
                    try:
                        wait_checkpoint(runtime)
                        if case == "cooperative_abort":
                            call("abort_run", {"run_id": run_id})
                        elif case == "sdk_crash":
                            runtime._process.kill()  # Only the owned SDK parent, deliberately.
                        future.result(timeout=25)
                    finally:
                        if not runtime._worker_done.is_set():
                            runtime.abort()
        else:
            # In lost_reply_duplicate, deliberately disregard this response.
            call("run_assay", run_args)
            if case == "lost_reply_duplicate":
                call("run_assay", run_args)
        call("get_run_status", {"run_id": run_id})
        call("get_result_summary", {"run_id": run_id})
        record = surface.run_store.get(run_id)
        write_json(directory / "run-record.json", record.model_dump(mode="json"))
        if runtime.attempt_directory is not None:
            recordings = list((runtime.attempt_directory / "sdk-output").glob("*.h5"))
            if recordings and case in {"cooperative_abort", "sdk_crash", "timeout_confirmed", "timeout_unconfirmed"}:
                write_json(directory / "native-status.json", native_status(recordings[0], runtime.attempt["sdk_run_id"]))
    sequence = {event.request_id: event.sequence for event in surface.audit_trail.events() if event.phase == "received"}
    calls.sort(key=lambda value: sequence[value["response"]["request_id"]])
    write_json(directory / "calls.json", {"client_kind": "deterministic_non_llm", "calls": calls})
    snapshot = surface.orchestrator.registry.lifecycle_store.snapshot(BACKEND_ID)
    lease = surface.orchestrator.registry.lease_store.current(BACKEND_ID)
    write_json(directory / "final-state.json", {"lifecycle": snapshot.model_dump(mode="json"),
        "lease": lease.model_dump(mode="json") if lease else None, "worker_done": runtime._worker_done.is_set()})
    write_json(directory / "lifecycle.json", {"history": [row.model_dump(mode="json")
        for row in surface.orchestrator.registry.lifecycle_store.history(resource_id=BACKEND_ID)]})
    write_json(directory / "manifest.json", {
        "schema_version": "r2-recovery-case-v1", "protocol": "r2-recovery-v1", "case": case,
        "principal_id": surface.principal.principal_id, "runtime_kind": "sdk_simulator",
        "evidence_level": "E3", "biological_claim": False, "mcp_call_count": len(calls),
        "audit_event_count": len(surface.audit_trail.events()),
        "sdk_start_count": len(list((directory / "attempts").glob("*/sdk-started.json"))),
        "files": {path.relative_to(directory).as_posix(): file_sha256(path)
                  for path in sorted(directory.rglob("*")) if path.is_file()},
    })
    report = verify_recovery_case(directory)
    write_json(directory / "verification.json", report)
    return report


def snapshot_sources(directory):
    files = set()
    for folder in ("adapters", "agent", "applications", "cl-apps/cp2n2-biopattern-gate", "core", "descriptors",
                   "evaluation", "mcp_surface", "runtimes", "scripts", "tests"):
        files.update(path for path in (ROOT / folder).rglob("*") if path.is_file() and path.suffix in {".py", ".json"}
                     and "__pycache__" not in path.parts and ".run-output" not in path.parts)
    files.add(ROOT / "requirements.txt")
    with zipfile.ZipFile(directory / "source-snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            content = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
            archive.writestr(path.relative_to(ROOT).as_posix(), content)


def run_campaign(directory):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    snapshot_sources(directory)
    campaign = {"protocol": "r2-recovery-v1", "case_order": list(CASES), "repetitions": 2,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "inputs": {name: file_sha256(directory / name) for name in ("protocol.md", "source-snapshot.zip")}}
    write_json(directory / "campaign.json", campaign)
    failures = []
    for repeat in (1, 2):
        for case in CASES:
            path = directory / f"repeat-{repeat:02d}" / case
            try:
                report = run_case(path, case)
                print(f"{repeat}/2 {case}: verified ({report['sdk_start_count']} SDK starts)", flush=True)
            except Exception as exc:
                failures.append({"repeat": repeat, "case": case, "error": str(exc)})
                path.mkdir(parents=True, exist_ok=True)
                write_json(path / "harness-failure.json", failures[-1])
                print(f"{repeat}/2 {case}: FAILED {exc}", flush=True)
    write_json(directory / "failures.json", {"failures": failures})
    if failures:
        raise RuntimeError(f"{len(failures)} cases failed; retained in {directory}")
    report = verify_recovery_campaign(directory)
    write_json(directory / "verification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cp2n2" / f"r2-recovery-{uuid4()}")
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--development-case", choices=CASES)
    args = parser.parse_args()
    if args.verify:
        report = verify_recovery_campaign(args.verify)
    elif args.development_case:
        report = run_case(args.output.resolve(), args.development_case)
    else:
        report = run_campaign(args.output)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
