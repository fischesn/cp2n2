"""R2 development checks; the success fixture really launches the CL SDK."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import shutil
from threading import Event

from cl import RecordingView
import pytest
import tables

from applications.biopattern_gate.control_plane_contract import BACKEND_ID
from evaluation.biopattern_gate_native import verify_native_execution
from evaluation.verify_biopattern_gate_sdk_bundle import verify_sdk_bundle
from runtimes.biopattern_gate_sdk_runtime import BioPatternGateSDKRuntime, write_json
from scripts.run_biopattern_gate_sdk_e3 import build_sdk_surface, run_bundle
from mcp_surface.catalog import get_preset


@pytest.fixture(scope="module")
def sdk_bundle(tmp_path_factory):
    if os.name != "nt":
        pytest.skip("R2 confirmed process containment currently requires Windows")
    directory = tmp_path_factory.mktemp("r2-sdk") / "bundle"
    report = run_bundle(directory)
    return directory, report


def _task():
    return get_preset("pattern_gate_v1").build_task(
        run_id="r2-test", principal_id="r2-client", resource_id=BACKEND_ID,
        lease_id="r2-test-lease", expected_lease_version=1,
    )


def _prepare(surface):
    reservation = surface.invoke("reserve_resource", {"resource_id": BACKEND_ID, "ttl_seconds": 60})
    assert reservation.ok
    response = surface.invoke("prepare_assay", {
        "resource_id": BACKEND_ID, "preset_id": "pattern_gate_v1", "dry_run": False,
        "lease_id": reservation.result["lease_id"], "expected_lease_version": reservation.result["lease_version"],
    })
    assert response.ok
    return response.result["run_id"]


def _paths(directory):
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    output = directory / "attempts" / manifest["execution_attempt_id"] / "sdk-output"
    return manifest, next(output.glob("*.h5")), output / "result.json"


def test_fresh_official_sdk_success_and_independent_bundle(sdk_bundle):
    directory, report = sdk_bundle
    assert report["verified"] and report["lease_released"]
    assert (report["trial_count"], report["stim_count"], report["spike_count"]) == (14, 24, 60)
    assert report["evidence_level"] == "E3" and report["biological_claim"] is False
    assert verify_sdk_bundle(directory) == report
    record = json.loads((directory / "run-record.json").read_text(encoding="utf-8"))
    assert record["summary"]["application"]["native_validation_verified"] is True
    assert record["summary"]["raw_output_included"] is False
    assert [row["to_state"] for row in record["result"]["lifecycle_history"]] == [
        "preparing", "running", "validating", "cooldown", "ready",
    ]


@pytest.mark.parametrize("change", ["checksum", "principal", "sdk_run", "lease", "counts", "result", "config"])
def test_bundle_rejects_substitution(sdk_bundle, tmp_path, change):
    source, _ = sdk_bundle
    directory = tmp_path / "copy"
    shutil.copytree(source, directory)
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if change == "checksum":
        (directory / "protocol.md").write_text("substitution", encoding="utf-8")
    else:
        field = {"principal": "principal_id", "sdk_run": "sdk_run_id", "lease": "lease_id",
                 "counts": "mcp_call_count", "result": "native_recording_sha256", "config": "config_sha256"}[change]
        manifest[field] = 999 if change == "counts" else "substitution"
        write_json(manifest_path, manifest)
    with pytest.raises(ValueError):
        verify_sdk_bundle(directory)


def test_native_recomputation_rejects_changed_spikes_even_without_a_checksum_oracle(sdk_bundle, tmp_path):
    manifest, recording, result = _paths(sdk_bundle[0])
    changed = tmp_path / recording.name
    shutil.copy2(recording, changed)
    with RecordingView(str(changed)) as view:
        node_path = view.spikes._v_pathname
    with tables.open_file(changed, mode="a") as file:
        file.get_node(node_path).cols.channel[0] = 63
    with pytest.raises(ValueError, match="unknown readout channel"):
        verify_native_execution(changed, result, expected_run_id=manifest["sdk_run_id"])


@pytest.mark.parametrize("kind", ["wrong-run", "partial"])
def test_native_identity_and_partial_are_rejected(sdk_bundle, tmp_path, kind):
    manifest, recording, result = _paths(sdk_bundle[0])
    changed = tmp_path / recording.name
    shutil.copy2(recording, changed)
    with tables.open_file(changed, mode="a") as file:
        attributes = dict(file.root._v_attrs.application)
        attributes["run_id" if kind == "wrong-run" else "terminal_state"] = "wrong" if kind == "wrong-run" else "aborted"
        file.root._v_attrs.application = attributes
    with pytest.raises(ValueError):
        verify_native_execution(changed, result, expected_run_id=manifest["sdk_run_id"])


def test_invalid_task_binding_has_no_launch(tmp_path, monkeypatch):
    runtime = BioPatternGateSDKRuntime(tmp_path / "attempts")
    task = _task()
    task.metadata["config_sha256"] = "0" * 64
    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.subprocess.Popen", lambda *a, **k: pytest.fail("forbidden start"))
    with pytest.raises(ValueError, match="binding mismatch"):
        runtime.prepare(task)
    assert runtime.attempt is None and not (tmp_path / "attempts").exists()


def test_physical_mode_has_no_launch(tmp_path, monkeypatch):
    runtime = BioPatternGateSDKRuntime(tmp_path / "attempts")
    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.cl.is_simulator", lambda: False)
    with pytest.raises(RuntimeError, match="simulator-only"):
        runtime.prepare(_task())
    assert runtime.attempt is None


@pytest.mark.parametrize("failure", ["launch", "exit"])
def test_failed_sdk_start_cannot_deliver_success_and_uses_truthful_reconciliation(tmp_path, monkeypatch, failure):
    class FailedChild:
        def wait(self):
            return 7

        def poll(self):
            return 7

    def start(*args, **kwargs):
        if failure == "launch":
            raise OSError("injected missing executable")
        return FailedChild()

    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.subprocess.Popen", start)
    surface = build_sdk_surface(tmp_path)
    run_id = _prepare(surface)
    response = surface.invoke("run_assay", {"run_id": run_id})
    assert response.ok and response.result["summary"]["success"] is False
    assert surface.orchestrator.registry.lease_store.current(BACKEND_ID) is None
    assert surface.orchestrator.registry.lifecycle_store.snapshot(BACKEND_ID).state == (
        "ready" if failure == "launch" else "unreachable"
    )
    runtime = surface.orchestrator.registry.get_adapter(BACKEND_ID).runtime
    assert runtime.attempt["status"] == "failed"
    assert (runtime.attempt_directory / "attempt.json").is_file()
    assert runtime.reset() is (failure == "launch")


@pytest.mark.skipif(os.name != "nt", reason="confirmed SDK process containment requires Windows")
def test_validation_failure_cannot_deliver_success(tmp_path, monkeypatch):
    def reject(*args, **kwargs):
        raise ValueError("injected independent validation failure")

    monkeypatch.setattr("adapters.biopattern_gate_sdk_adapter.verify_native_execution", reject)
    surface = build_sdk_surface(tmp_path)
    run_id = _prepare(surface)
    response = surface.invoke("run_assay", {"run_id": run_id})
    summary = response.result["summary"]
    assert summary["success"] is False and summary["error_code"] == "POSTCONDITION_FAILED"
    assert summary["application"]["native_validation_verified"] is False
    assert summary["artifact_references"] == []


@pytest.mark.skipif(os.name != "nt", reason="confirmed SDK process containment requires Windows")
def test_lost_reply_retrieval_and_duplicate_run_do_not_start_another_sdk(tmp_path, monkeypatch):
    surface = build_sdk_surface(tmp_path)
    run_id = _prepare(surface)
    first = surface.invoke("run_assay", {"run_id": run_id, "idempotency_key": "r2-reply-test"})
    assert first.result["summary"]["success"] is True
    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.subprocess.Popen", lambda *a, **k: pytest.fail("duplicate SDK start"))
    duplicate = surface.invoke("run_assay", {"run_id": run_id, "idempotency_key": "r2-reply-test"})
    assert duplicate.ok is False
    recovered = surface.invoke("get_result_summary", {"run_id": run_id})
    assert recovered.ok and recovered.result["summary"] == first.result["summary"]
    assert len(list((tmp_path / "attempts").iterdir())) == 1


def test_timeout_quarantines_until_observed_termination(tmp_path, monkeypatch):
    started, finish, exited = Event(), Event(), Event()

    class WaitingChild:
        def wait(self):
            started.set()
            assert finish.wait(15), "test must release simulated child"
            exited.set()
            return 7

        def poll(self):
            return 7 if exited.is_set() else None

    class UnconfirmableGuard:
        def __init__(self, process):
            pass

        def observe(self):
            return {"active_process_count": 0 if exited.is_set() else 1, "termination_confirmed": exited.is_set()}

        def wait_empty(self, timeout_s):
            return exited.is_set()

        def terminate(self):
            pass

        def close_if_empty(self):
            return exited.is_set()

    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.subprocess.Popen", lambda *a, **k: WaitingChild())
    monkeypatch.setattr("runtimes.biopattern_gate_sdk_runtime.SDKProcessGuard", UnconfirmableGuard)
    surface = build_sdk_surface(tmp_path)
    runtime = surface.orchestrator.registry.get_adapter(BACKEND_ID).runtime
    task = _task().model_copy(update={"lease_id": None, "expected_lease_version": None, "invocation_timeout_ms": 250})
    try:
        with ThreadPoolExecutor() as executor:
            future = executor.submit(surface.orchestrator.execute_task, task)
            assert started.wait(5)
            result = future.result(timeout=5)
            assert result.success is False and result.error.code == "EXECUTION_STATUS_UNKNOWN"
            assert result.final_lifecycle.state == "unreachable"
            assert runtime.reset() is False and runtime.abort() is False
            assert runtime.telemetry()["health_status"] == "unknown"
            reservation = surface.invoke("reserve_resource", {"resource_id": BACKEND_ID})
            assert reservation.ok is False
    finally:
        finish.set()
    assert exited.wait(5)
    # A process exit is necessary, but registry reuse still needs explicit reconciliation.
    assert surface.orchestrator.registry.lifecycle_store.snapshot(BACKEND_ID).state == "unreachable"
