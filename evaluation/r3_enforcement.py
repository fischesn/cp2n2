"""Direct, protocol-level active enforcement cases with independent effects."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from threading import RLock
from unittest.mock import patch
from uuid import uuid4

from adapters.chemical_adapter import ChemicalAdapter
from adapters.edge_adapter import EdgeAdapter
from adapters.wetware_adapter import WetwareAdapter
from core.leases import InMemoryLeaseStore
from core.orchestrator import CP2N2Orchestrator
from descriptors.resource_contract import ResourceLifecycleState
from evaluation.r3_effect_backend import EffectAdapter, MOCK_ID, MOCK_PRESET, json_safe
from evaluation.r3_protocol_client import protocol_call
from evaluation.biopattern_gate_native import file_sha256
from mcp_surface.approvals import ApprovalRequirement, InMemoryHumanApprovalAuthority
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.auth import Scope
from mcp_surface.catalog import get_preset
from mcp_surface.models import MCPPrincipal
from mcp_surface.records import RunRecordStore
from mcp_surface.service import MCPControlSurface
from runtimes.biopattern_gate_sdk_runtime import write_json


CASES = (
    "positive_mock", "dry_run", "unauthenticated", "no_execute_scope", "unknown_tool",
    "physical_parameter", "policy_override", "evidence_override", "unknown_preset", "unknown_resource",
    "missing_approval", "wrong_approval", "valid_approval", "lease_conflict", "cross_owner_run",
    "cross_owner_release", "expired_lease", "stale_lease_version", "stale_lifecycle_version",
    "stale_health", "missing_health", "unknown_health", "stale_telemetry_age", "missing_calibration",
    "stale_calibration", "invalid_unit", "invalid_shape", "nonfinite_input", "out_of_range",
    "wrong_result_task", "wrong_result_backend", "nonfinite_result", "invalid_probabilities",
    "duplicate_terminal", "inprogress_duplicate", "unresolved_quarantine", "invalid_lifecycle",
    "faulty_commit_detector", "deny_all_detector", "positive_chemical", "positive_edge", "positive_wetware",
)
POSITIVE = {"positive_mock", "valid_approval", "duplicate_terminal", "inprogress_duplicate",
            "positive_chemical", "positive_edge", "positive_wetware"}
BAD_RESULT = {"wrong_result_task", "wrong_result_backend", "nonfinite_result", "invalid_probabilities"}
DETECTOR_CONTROLS = {"faulty_commit_detector", "deny_all_detector"}
ORACLE = Path(__file__).parent / "fixtures" / "r3-direct-v1.json"


class Environment:
    def __init__(self, directory, *, wrapped=None, protocol=True):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.adapter = EffectAdapter(self.directory / "backend", wrapped=wrapped)
        self.runtime = self.adapter.runtime
        self.resource_id = self.adapter.backend_id()
        self.preset = MOCK_PRESET
        if wrapped and str(wrapped.describe().capability.substrate_class) == "wetware":
            self.preset = "wetware_temporal_probe_v1"
        elif wrapped and str(wrapped.describe().capability.substrate_class) == "chemical":
            self.preset = "chemical_sensing_v1"
        self.orchestrator = CP2N2Orchestrator()
        self.orchestrator.register_adapter(self.adapter)
        self.clock = [datetime.now(timezone.utc)]
        self.orchestrator.registry._lease_store = InMemoryLeaseStore(clock=lambda: self.clock[0])
        self.records = RunRecordStore()
        self.approvals = InMemoryHumanApprovalAuthority()
        self.audit = JsonlHashChainAuditTrail(self.directory / "audit.jsonl")
        self.calls, self.lock = [], RLock()
        self.protocol = protocol
        self.owner = self.surface("owner-a")
        self.other = self.surface("owner-b")

    def surface(self, owner, *, execute=True, authenticated=True):
        return MCPControlSurface(orchestrator=self.orchestrator,
            principal=MCPPrincipal(principal_id=owner, authenticated=authenticated,
                scopes=[s.value for s in Scope if execute or s != Scope.ASSAYS_EXECUTE]),
            audit_trail=self.audit, approval_verifier=self.approvals, run_store=self.records)

    def call(self, tool, args, *, surface=None, measured=True):
        surface = surface or self.owner
        response = protocol_call(surface, tool, args) if self.protocol else surface.invoke(tool, args).model_dump(mode="json")
        with self.lock:
            self.calls.append({"principal_id": surface.principal.principal_id, "tool": tool,
                "arguments": JsonlHashChainAuditTrail._redact(args),
                "argument_digest": JsonlHashChainAuditTrail._digest(args),
                "response": response, "measured": measured})
        return response

    def reserve(self, **kwargs):
        return self.call("reserve_resource", {"resource_id": self.resource_id}, **kwargs)

    def prepare(self, reservation=None, **kwargs):
        reservation = reservation or self.reserve()
        if not reservation["ok"]:
            raise RuntimeError("positive setup reservation failed")
        return self.call("prepare_assay", {"resource_id": self.resource_id, "preset_id": self.preset,
            "dry_run": False, "lease_id": reservation["result"]["lease_id"],
            "expected_lease_version": reservation["result"]["lease_version"]}, **kwargs)

    def run(self, prepared, **kwargs):
        if not prepared["ok"]:
            raise RuntimeError("positive setup preparation failed")
        return self.call("run_assay", {"run_id": prepared["result"]["run_id"],
            "idempotency_key": f"r3:{prepared['result']['run_id']}"}, **kwargs)

    def token(self, prepared, *, owner="owner-a"):
        record = self.records.get(prepared["result"]["run_id"])
        return self.approvals.issue(ApprovalRequirement(run_id=record.run_id, resource_id=record.resource_id,
            preset_id=record.preset_id, principal_id=owner), approver_id="isolated-test-authority").token

    def cleanup(self):
        self.runtime.release.set()
        if not self.runtime.done.wait(2):
            raise RuntimeError("isolated worker cleanup unresolved")
        lease = self.orchestrator.registry.lease_store.current(self.resource_id)
        if lease:
            response = self.orchestrator.abort_backend(self.resource_id, lease_id=lease.lease_id, owner_id=lease.owner_id)
            if not response.success:
                # The worker has independently ended. Expire a stranded fixture
                # lease before explicit reconciliation; never force state READY.
                self.clock[0] += timedelta(seconds=61)
        response = self.orchestrator.reconcile_backend(self.resource_id)
        if not response.success:
            raise RuntimeError("isolated fixture reconciliation failed")

    def save(self):
        sequence = {e.request_id: e.sequence for e in self.audit.events() if e.phase == "received"}
        self.calls.sort(key=lambda c: sequence[c["response"]["request_id"]])
        write_json(self.directory / "calls.json", {"transport": "official_mcp_memory_sessions" if self.protocol else "direct_surface_state_exploration", "calls": self.calls})
        write_json(self.directory / "records.json", json_safe({"records": [r.model_dump(mode="json") for r in self.records._records.values()]}))
        write_json(self.directory / "final.json", {
            "lifecycle": self.orchestrator.registry.lifecycle_store.snapshot(self.resource_id).model_dump(mode="json"),
            "lease": None if self.orchestrator.registry.lease_store.current(self.resource_id) is None else "active",
            "worker_done": self.runtime.done.is_set(),
            "history": [r.model_dump(mode="json") for r in self.orchestrator.registry.lifecycle_store.history(resource_id=self.resource_id)]})


def exercise_case(env, case):
    resource, preset = env.resource_id, env.preset
    if case in {"positive_mock", "positive_chemical", "positive_edge"}:
        return env.run(env.prepare())
    if case == "dry_run":
        return env.call("prepare_assay", {"resource_id": resource, "preset_id": preset, "dry_run": True})
    if case == "unauthenticated":
        return env.reserve(surface=env.surface("anonymous", authenticated=False))
    if case in {"no_execute_scope", "deny_all_detector"}:
        prepared = env.prepare()
        return env.run(prepared, surface=env.surface("owner-a", execute=False))
    if case in {"unknown_tool", "physical_parameter", "policy_override", "evidence_override", "unknown_preset", "unknown_resource"}:
        args = {"resource_id": resource, "preset_id": preset, "dry_run": True}
        if case == "unknown_tool":
            return env.call("raw_stimulate", {"channel": 8, "amplitude": 1000})
        if case == "physical_parameter": args["amplitude"] = 1000
        if case == "policy_override": args["allow_fallback"] = True
        if case == "evidence_override": args["runtime_kind"] = "physical_hardware"
        if case == "unknown_preset": args["preset_id"] = "unsafe-new-preset"
        if case == "unknown_resource": args["resource_id"] = "physical-cl1-unpublished"
        return env.call("prepare_assay", args)
    if case in {"missing_approval", "wrong_approval", "valid_approval", "positive_wetware"}:
        prepared = env.prepare()
        if case != "positive_wetware":
            # Approval authority conformance fixture. E1 is still E1: this
            # does not publish a synthetic twin as physical hardware.
            env.records._records[prepared["result"]["run_id"]].approval_required = True
        args = {"run_id": prepared["result"]["run_id"]}
        if case != "missing_approval":
            args["approval_token"] = env.token(prepared, owner="owner-b" if case == "wrong_approval" else "owner-a")
        return env.call("run_assay", args)
    if case in {"lease_conflict", "cross_owner_release", "stale_lease_version", "stale_lifecycle_version"}:
        reservation = env.reserve()
        lease = reservation["result"]["lease_id"]
        if case == "lease_conflict": return env.reserve(surface=env.other)
        if case == "cross_owner_release":
            return env.call("release_resource", {"resource_id": resource, "lease_id": lease}, surface=env.other)
        if case == "stale_lifecycle_version":
            return env.call("release_resource", {"resource_id": resource, "lease_id": lease, "expected_state_version": 0})
        return env.call("prepare_assay", {"resource_id": resource, "preset_id": preset, "dry_run": False,
            "lease_id": lease, "expected_lease_version": 99})
    if case in {"stale_health", "missing_health", "unknown_health", "stale_telemetry_age", "missing_calibration", "stale_calibration"}:
        reservation = env.reserve()
        if case == "stale_health": env.adapter.stale_health = True
        elif case == "missing_health": env.adapter.missing_health = True
        elif case == "unknown_health": env.runtime.overrides["health_status"] = "unknown"
        elif case == "stale_telemetry_age": env.runtime.overrides["age_of_information_ms"] = 1001.0
        elif case == "missing_calibration": env.runtime.overrides["calibration_status"] = None
        elif case == "stale_calibration": env.runtime.overrides["calibration_status"] = "stale"
        prepared = env.prepare(reservation)
        return env.run(prepared) if prepared["ok"] else prepared
    if case in {"invalid_unit", "invalid_shape", "nonfinite_input", "out_of_range"}:
        metadata = {"input_vector": [0.1, 0.3, 0.5, 0.7]}
        if case == "invalid_unit": metadata["input_unit"] = "microampere"
        if case == "invalid_shape": metadata["input_vector"] = [0.1]
        if case == "nonfinite_input": metadata["input_vector"][0] = float("nan")
        if case == "out_of_range": metadata["input_vector"][0] = 2
        with patch("mcp_surface.service.get_preset", return_value=replace(get_preset(preset), metadata=metadata)):
            return env.run(env.prepare())
    if case in BAD_RESULT:
        env.runtime.fault = case
        return env.run(env.prepare())
    if case == "faulty_commit_detector":
        # This deliberately calls a fixture runtime outside the production path.
        prepared = env.prepare()
        response = env.run(prepared, surface=env.surface("owner-a", execute=False))
        task = env.records.get(prepared["result"]["run_id"]).task
        env.runtime.execute(task)
        return response
    prepared = env.prepare()
    if case == "cross_owner_run": return env.run(prepared, surface=env.other)
    if case == "expired_lease":
        env.clock[0] += timedelta(seconds=61)
        return env.run(prepared)
    if case == "invalid_lifecycle":
        env.orchestrator.registry.lifecycle_store.transition(resource, ResourceLifecycleState.FAILED, reason="isolated fixture")
        return env.run(prepared)
    if case == "duplicate_terminal":
        env.run(prepared)
        return env.run(prepared)
    if case in {"inprogress_duplicate", "unresolved_quarantine"}:
        env.runtime.block = True
        env.runtime.abort_confirmed = case != "unresolved_quarantine"
        if case == "unresolved_quarantine":
            env.records._records[prepared["result"]["run_id"]].task.invocation_timeout_ms = 250
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(env.run, prepared)
            try:
                if not env.runtime.started.wait(3): raise RuntimeError("isolated worker did not start")
                if case == "inprogress_duplicate":
                    response = env.run(prepared)
                    env.runtime.release.set()
                    future.result(timeout=3)
                else:
                    response = future.result(timeout=3)
                    write_json(env.directory / "quarantine.json", {
                        "lifecycle": env.orchestrator.registry.lifecycle_store.snapshot(resource).model_dump(mode="json"),
                        "worker_active": not env.runtime.done.is_set(),
                        "reuse_response": env.reserve()})
            finally:
                env.runtime.cancelled = case == "unresolved_quarantine"
                env.runtime.release.set()
                env.runtime.done.wait(3)
        return response
    raise ValueError(case)


def run_case(directory, case):
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "oracle.json").write_bytes(ORACLE.read_bytes())
    wrapped = None
    if case in {"missing_approval", "wrong_approval", "valid_approval", "positive_wetware"}: wrapped = WetwareAdapter()
    elif case == "positive_chemical": wrapped = ChemicalAdapter()
    elif case == "positive_edge": wrapped = EdgeAdapter()
    env = Environment(directory, wrapped=wrapped)
    try:
        probe = exercise_case(env, case)
    finally:
        env.cleanup()
    env.save()
    specification = {"case": case, "probe": probe,
        "runtime_kind": str(env.runtime.capabilities.runtime_kind), "resource_id": env.resource_id}
    write_json(directory / "case.json", specification)
    write_json(directory / "manifest.json", {"schema_version": "r3-direct-case-v1",
        "files": {p.relative_to(directory).as_posix(): file_sha256(p) for p in sorted(directory.rglob("*")) if p.is_file()}})
    from evaluation.verify_r3_enforcement import verify_case
    return verify_case(directory)
