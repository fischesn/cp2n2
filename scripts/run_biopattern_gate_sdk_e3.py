"""Create a fresh continuous MCP to official SDK E3 development bundle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from adapters.biopattern_gate_sdk_adapter import BioPatternGateSDKAdapter
from agent.biopattern_gate_client import BioPatternGateDeterministicClient
from applications.biopattern_gate.control_plane_contract import BACKEND_ID
from core.orchestrator import CP2N2Orchestrator
from evaluation.biopattern_gate_native import file_sha256
from evaluation.verify_biopattern_gate_sdk_bundle import verify_sdk_bundle
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.auth import Scope
from mcp_surface.models import MCPPrincipal
from mcp_surface.service import MCPControlSurface
from runtimes.biopattern_gate_sdk_runtime import write_json


def build_sdk_surface(directory: Path) -> MCPControlSurface:
    orchestrator = CP2N2Orchestrator()
    orchestrator.register_adapter(BioPatternGateSDKAdapter(directory / "attempts"))
    return MCPControlSurface(
        orchestrator=orchestrator,
        principal=MCPPrincipal(principal_id="r2-sdk-development-client", scopes=[scope.value for scope in Scope]),
        audit_trail=JsonlHashChainAuditTrail(directory / "audit.jsonl"),
    )


def run_bundle(directory: Path) -> dict:
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    protocol = ROOT / "docs" / "revision" / "r2-sdk-execution.md"
    # Retain the exact protocol present before this development execution.
    (directory / "protocol.md").write_bytes(protocol.read_bytes())
    surface = build_sdk_surface(directory)
    transcript = BioPatternGateDeterministicClient(surface).run().as_dict()
    write_json(directory / "transcript.json", transcript)
    application = transcript["result_summary"].get("application", {})
    if transcript["result_summary"].get("success") is not True:
        raise RuntimeError(f"SDK execution or validation failed: {transcript['result_summary']}")
    record = surface.run_store.get(application["application_run_id"])
    write_json(directory / "run-record.json", record.model_dump(mode="json"))
    snapshot = surface.orchestrator.registry.lifecycle_store.snapshot(BACKEND_ID)
    lease = surface.orchestrator.registry.lease_store.current(BACKEND_ID)
    write_json(directory / "final-state.json", {"lifecycle": snapshot.model_dump(mode="json"),
                                               "lease": lease.model_dump(mode="json") if lease else None})
    runtime = surface.orchestrator.registry.get_adapter(BACKEND_ID).runtime
    attempt = runtime.attempt
    calls = [step for step in transcript["steps"] if step["tool"] is not None]
    run_call = next(step for step in calls if step["tool"] == "run_assay")
    files = {
        path.relative_to(directory).as_posix(): file_sha256(path)
        for path in sorted(directory.rglob("*")) if path.is_file()
    }
    manifest = {
        "schema_version": "r2-sdk-bundle-v1", "purpose": "development_checkpoint",
        "client_kind": "deterministic_non_llm", "runtime_kind": "sdk_simulator",
        "evidence_level": "E3", "biological_claim": False, "provider_execution_id": None,
        "principal_id": surface.principal.principal_id, "run_request_id": run_call["request_id"],
        "task_id": record.task.task_id, "resource_id": BACKEND_ID, "lease_id": record.lease_id,
        "application_run_id": record.run_id, "execution_attempt_id": attempt["execution_attempt_id"],
        "sdk_run_id": attempt["sdk_run_id"], "sdk_run_id_origin": "controller_assigned",
        "orchestration_correlation_id": record.result.correlation_id,
        "mcp_call_count": len(calls), "audit_event_count": len(surface.audit_trail.events()),
        "config_sha256": attempt["config_sha256"], "decoder_sha256": attempt["decoder_sha256"],
        "application_source_sha256": attempt["application_source_sha256"],
        "sdk_application_source_sha256": attempt["sdk_application_source_sha256"],
        "native_recording_sha256": application["native_recording_sha256"], "files": files,
    }
    write_json(directory / "manifest.json", manifest)
    verification = verify_sdk_bundle(directory)
    write_json(directory / "verification.json", verification)
    return verification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cp2n2" / f"r2-sdk-{uuid4()}")
    parser.add_argument("--verify", type=Path, help="Verify an existing bundle without starting the SDK")
    args = parser.parse_args()
    report = verify_sdk_bundle(args.verify) if args.verify else run_bundle(args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
