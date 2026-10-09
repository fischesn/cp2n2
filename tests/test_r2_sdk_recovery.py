"""Partial evidence, owned termination and concurrent finalization checks."""

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
from threading import Event

import pytest
import tables

from applications.biopattern_gate.control_plane_contract import BACKEND_ID
from core.orchestrator import CP2N2Orchestrator
from demos.common import build_biopattern_gate_e3_orchestrator
from evaluation.biopattern_gate_native import file_sha256
from evaluation.verify_r2_sdk_recovery import verify_recovery_case
from mcp_surface.models import MCPPrincipal
from mcp_surface.auth import Scope
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.service import MCPControlSurface
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_biopattern_gate_sdk_e3 import build_sdk_surface
from scripts.run_r2_sdk_recovery import run_case


@pytest.fixture(scope="module")
def aborted_case(tmp_path_factory):
    if os.name != "nt":
        pytest.skip("confirmed SDK process job requires Windows")
    directory = tmp_path_factory.mktemp("r2-recovery") / "aborted"
    return directory, run_case(directory, "cooperative_abort")


def test_cooperative_abort_retains_native_partial_and_confirms_empty_job(aborted_case):
    directory, report = aborted_case
    assert report["verified"] and report["result_success"] is False
    assert verify_recovery_case(directory) == report
    native = json.loads((directory / "native-status.json").read_text(encoding="utf-8"))
    assert native["terminal_state"] == "aborted" and native["decision_count"] == 2
    assert native["stim_count"] == 2 and native["spike_count"] > 0
    termination = json.loads(next(directory.rglob("termination.json")).read_text(encoding="utf-8"))
    assert termination["active_process_count"] == 0 and termination["termination_confirmed"]
    assert termination["forced_cleanup"] is False
    record = json.loads((directory / "run-record.json").read_text(encoding="utf-8"))
    assert record["state"] == "aborted" and record["summary"]["success"] is False
    assert record["summary"]["artifact_references"]
    assert all(item["metadata"]["validated"] is False for item in record["summary"]["artifact_references"])


@pytest.mark.parametrize("field,value", [
    ("principal_id", "substitute"), ("sdk_start_count", 2), ("mcp_call_count", 99),
    ("audit_event_count", 1), ("case", "success"), ("protocol", "different"), ("biological_claim", True),
])
def test_recovery_verifier_rejects_false_case_claims(aborted_case, tmp_path, field, value):
    directory = tmp_path / "copy"
    shutil.copytree(aborted_case[0], directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest[field] = value
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError):
        verify_recovery_case(directory)


def test_partial_cannot_be_relabelled_complete_even_after_rehash(aborted_case, tmp_path):
    directory = tmp_path / "copy"
    shutil.copytree(aborted_case[0], directory)
    recording = next(directory.rglob("*.h5"))
    with tables.open_file(recording, mode="a") as file:
        application = dict(file.root._v_attrs.application)
        application["terminal_state"] = "complete"
        file.root._v_attrs.application = application
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"][recording.relative_to(directory).as_posix()] = file_sha256(recording)
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="partial status"):
        verify_recovery_case(directory)


@pytest.mark.parametrize("artifact", ["lifecycle.json", "sdk-config.json"])
def test_rehashed_case_still_checks_lifecycle_and_config(aborted_case, tmp_path, artifact):
    directory = tmp_path / "copy"
    shutil.copytree(aborted_case[0], directory)
    path = next(directory.rglob(artifact))
    value = json.loads(path.read_text(encoding="utf-8"))
    if artifact == "lifecycle.json":
        value["history"][0]["from_version"] = 42
    else:
        value["timeout_s"] = 99
    write_json(path, value)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"][path.relative_to(directory).as_posix()] = file_sha256(path)
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="lifecycle chain|configuration substitution"):
        verify_recovery_case(directory)


def test_case_must_match_campaign_source_snapshot(aborted_case):
    with pytest.raises(ValueError, match="archived application source"):
        verify_recovery_case(aborted_case[0], source_bindings={"application_source_sha256": "0" * 64})


def _surface(tmp_path):
    return MCPControlSurface(orchestrator=build_biopattern_gate_e3_orchestrator(),
        principal=MCPPrincipal(principal_id="recovery-tests", scopes=[scope.value for scope in Scope]),
        audit_trail=JsonlHashChainAuditTrail(tmp_path / "audit.jsonl"))


def test_concurrent_finalizers_share_registry_adapter_lock(tmp_path, monkeypatch):
    surface = _surface(tmp_path)
    orchestrator = surface.orchestrator
    other = CP2N2Orchestrator(registry=orchestrator.registry)
    reservation = orchestrator.reserve_backend(BACKEND_ID, owner_id=surface.principal.principal_id)
    adapter = orchestrator.registry.get_adapter(BACKEND_ID)
    entered, release = Event(), Event()
    effects = []
    def abort():
        effects.append("abort")
        entered.set()
        assert release.wait(5)
        return True
    monkeypatch.setattr(adapter, "abort", abort)
    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(orchestrator._abort_and_reconcile, adapter, reservation.lease,
                                surface.principal.principal_id, "first", timeout_ms=5000, uncertain=True)
        assert entered.wait(3)
        second = executor.submit(other._abort_and_reconcile, adapter, reservation.lease,
                                 surface.principal.principal_id, "second", timeout_ms=5000, uncertain=True)
        release.set()
        assert first.result(timeout=5)[1].state == second.result(timeout=5)[1].state == "ready"
    assert effects == ["abort"]


def test_late_original_finalizer_leaves_new_lease_untouched(tmp_path, monkeypatch):
    surface = _surface(tmp_path)
    orchestrator = surface.orchestrator
    adapter = orchestrator.registry.get_adapter(BACKEND_ID)
    first = orchestrator.reserve_backend(BACKEND_ID, owner_id="old-owner")
    orchestrator.abort_backend(BACKEND_ID, lease_id=first.lease.lease_id, owner_id="old-owner")
    second = orchestrator.reserve_backend(BACKEND_ID, owner_id="new-owner")
    monkeypatch.setattr(adapter, "abort", lambda: pytest.fail("old finalizer touched new provider execution"))
    actions, state = orchestrator._abort_and_reconcile(adapter, first.lease, "old-owner", "late",
                                                     timeout_ms=1000, uncertain=True)
    assert state.state == "reserved"
    assert orchestrator.registry.lease_store.current(BACKEND_ID).lease_id == second.lease.lease_id
    assert "superseded" in actions[0]


@pytest.mark.skipif(os.name != "nt", reason="Windows process containment")
def test_failed_containment_never_authorizes_sdk_start(tmp_path, monkeypatch):
    def reject(process):
        raise OSError("injected containment refusal")
    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.SDKProcessGuard", reject)
    surface = build_sdk_surface(tmp_path)
    reservation = surface.invoke("reserve_resource", {"resource_id": BACKEND_ID})
    prepared = surface.invoke("prepare_assay", {"resource_id": BACKEND_ID, "preset_id": "pattern_gate_v1",
        "dry_run": False, "lease_id": reservation.result["lease_id"],
        "expected_lease_version": reservation.result["lease_version"]})
    response = surface.invoke("run_assay", {"run_id": prepared.result["run_id"]})
    assert response.result["summary"]["success"] is False
    assert not list(tmp_path.rglob("sdk-started.json")) and not list(tmp_path.rglob("launch-authorized.json"))
    assert surface.orchestrator.registry.lifecycle_store.snapshot(BACKEND_ID).state == "ready"
