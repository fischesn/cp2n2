"""Provider failures are per-resource failures, not hidden programming bugs."""
import json
from time import sleep
from threading import Event
from urllib.error import URLError

import pytest

from adapters.edge_adapter import EdgeAdapter
from core.errors import ControlPlaneErrorCode
from core.orchestrator import CP2N2Orchestrator
from demos.common import make_edge_task
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.models import MCPPrincipal
from mcp_surface.service import MCPControlSurface


class FaultAdapter(EdgeAdapter):
    def __init__(self, backend_id="bad"):
        super().__init__(backend_id=backend_id)
        self.failure = None
        self.invokes = 0
        self.started = Event()
        self.release = Event()

    def collect_telemetry(self):
        if self.failure == "transport":
            raise URLError("diagnostic provider unavailable")
        if self.failure == "invalid_json":
            raise json.JSONDecodeError("diagnostic invalid JSON", "x", 0)
        if self.failure == "invalid_frame":
            return []
        if self.failure == "bug":
            raise RuntimeError("unrelated bug must not become an available backend")
        if self.failure == "blocked":
            self.started.set()
            self.release.wait(5)
        return super().collect_telemetry()

    def invoke(self, task):
        self.invokes += 1
        if self.failure == "lost_reply":
            raise URLError("invocation may already have committed")
        return super().invoke(task)


def setup_pair():
    orchestrator = CP2N2Orchestrator()
    bad, good = FaultAdapter(), FaultAdapter("good")
    for adapter in (bad, good):
        orchestrator.register_adapter(adapter)
    return orchestrator, bad, good


@pytest.mark.parametrize("fault,kind", [("transport", "transport"), ("invalid_json", "invalid_telemetry"), ("invalid_frame", "invalid_telemetry")])
def test_provider_failure_is_structured_and_healthy_candidate_survives(fault, kind):
    orchestrator, bad, good = setup_pair()
    bad.failure = fault
    result = orchestrator.execute_task(make_edge_task(task_id="healthy-alternative"))
    assert result.success and result.decision.selected_backend_id == "good"
    assert bad.invokes == 0 and good.invokes == 1
    error = result.decision.provider_errors["bad"]
    assert error.code == ControlPlaneErrorCode.TELEMETRY_STALE
    assert error.details["provider_failure"] == kind
    assert error.details["execution_status"] == "not_started"
    assert orchestrator.registry.lifecycle_store.snapshot("bad").state == "unreachable"


def test_directed_provider_failure_requires_explicit_reconciliation():
    orchestrator, bad, _ = setup_pair()
    task = make_edge_task(task_id="direct")
    task.direct_backend_id = "bad"
    bad.failure = "transport"
    failed = orchestrator.execute_task(task)
    assert not failed.success and failed.error.details["phase"] == "planning"
    bad.failure = None
    assert not orchestrator.execute_task(task).success
    assert orchestrator.reconcile_backend("bad").success
    assert orchestrator.execute_task(task).success
    assert bad.invokes == 1


def test_planning_timeout_is_bounded_and_pending_worker_blocks_reconciliation():
    orchestrator, bad, _ = setup_pair()
    task = make_edge_task(task_id="timed-out-read")
    task.direct_backend_id = "bad"
    task.preparation_timeout_ms = 20
    bad.failure = "blocked"
    try:
        result = orchestrator.execute_task(task)
        assert bad.started.is_set() and not result.success
        assert result.error.details["provider_failure"] == "timeout"
        assert result.error.details["worker_pending"]
        assert not orchestrator.reconcile_backend("bad", timeout_ms=20).success
        assert bad.invokes == 0
    finally:
        bad.release.set()


def test_arbitrary_programming_error_is_not_reclassified():
    orchestrator, bad, _ = setup_pair()
    bad.failure = "bug"
    with pytest.raises(RuntimeError, match="unrelated bug"):
        orchestrator.execute_task(make_edge_task(task_id="programming-error"))


def test_unknown_invocation_outcome_does_not_execute_fallback():
    orchestrator, bad, good = setup_pair()
    bad.failure = "lost_reply"
    task = make_edge_task(task_id="unknown-commit")
    result = orchestrator.execute_task(task)
    assert not result.success
    assert result.error.details["execution_status"] == "unknown"
    assert result.error.details["automatic_retry"] is False
    assert bad.invokes == 1 and good.invokes == 0


def test_mcp_discovery_preserves_healthy_resources_and_reports_provider_failure(tmp_path):
    orchestrator, bad, _ = setup_pair()
    bad.failure = "transport"
    surface = MCPControlSurface(orchestrator=orchestrator,
        principal=MCPPrincipal(principal_id="reader", scopes=["resources:read"]),
        audit_trail=JsonlHashChainAuditTrail(tmp_path / "audit.jsonl"))
    response = surface.invoke("discover_resources", {})
    assert response.ok
    assert [row["resource_id"] for row in response.result["resources"]] == ["good"]
    assert response.result["unavailable_resources"][0]["resource_id"] == "bad"
    assert not surface.invoke("describe_resource", {"resource_id": "bad"}).ok


def test_reconciliation_timeout_tracks_worker_until_read_finishes():
    orchestrator, bad, _ = setup_pair()
    bad.failure = "blocked"
    try:
        first = orchestrator.reconcile_backend("bad", timeout_ms=20)
        assert not first.success
        assert orchestrator.registry.lifecycle_store.snapshot("bad").state == "unreachable"
        assert not orchestrator.reconcile_backend("bad", timeout_ms=20).success
        pending = next(iter(orchestrator._provider_failures["bad"][1]))
        bad.failure = None
        bad.release.set()
        assert pending.wait(1)
        assert orchestrator.reconcile_backend("bad").success
    finally:
        bad.release.set()


def test_concurrent_quarantine_keeps_all_pending_reads():
    orchestrator, _, _ = setup_pair()
    first, second = Event(), Event()
    error = orchestrator._provider_error("bad", "planning", "timeout", execution_status="not_started", worker_pending=True)
    orchestrator._quarantine_provider("bad", error, first)
    orchestrator._quarantine_provider("bad", error, second)
    # A later known transport error must not erase either timed-out worker.
    orchestrator._quarantine_provider("bad", error)
    first.set()
    assert not orchestrator.reconcile_backend("bad").success
    second.set()
    assert orchestrator.reconcile_backend("bad").success


def test_drift_changed_during_preparation_blocks_actual_invocation():
    class MutatingAdapter(FaultAdapter):
        drift = 0.0
        def collect_telemetry(self):
            return {**super().collect_telemetry(), "drift_score": self.drift}
        def prepare(self, task):
            result = super().prepare(task)
            self.drift = 0.99
            return result
    orchestrator = CP2N2Orchestrator()
    adapter = MutatingAdapter()
    orchestrator.register_adapter(adapter)
    task = make_edge_task(task_id="live-drift")
    task.allow_fallback = False
    result = orchestrator.execute_task(task)
    assert not result.success and adapter.invokes == 0
    assert "drift_threshold" in result.error.message


def test_lease_expired_during_final_admission_blocks_actual_invocation():
    class SlowAdmissionAdapter(FaultAdapter):
        reads = 0
        def resource_contract(self):
            self.reads += 1
            if self.reads == 3:
                sleep(0.15)
            return super().resource_contract()
    orchestrator = CP2N2Orchestrator()
    adapter = SlowAdmissionAdapter()
    orchestrator.register_adapter(adapter)
    task = make_edge_task(task_id="expired-live-admission")
    task.allow_fallback = False
    task.lease_ttl_ms = 60
    result = orchestrator.execute_task(task)
    assert not result.success and result.error.code == "LEASE_EXPIRED"
    assert adapter.invokes == 0


@pytest.mark.parametrize("blocked_read", [3, 4])
def test_late_live_read_worker_remains_quarantined_despite_abort_ack(blocked_read):
    class BlockingContractAdapter(FaultAdapter):
        reads = 0
        def resource_contract(self):
            self.reads += 1
            if self.reads == blocked_read:
                self.started.set()
                self.release.wait(5)
            return super().resource_contract()
        def abort(self):
            return True  # acknowledgement is not cancellation of a read worker
    orchestrator = CP2N2Orchestrator()
    adapter = BlockingContractAdapter()
    orchestrator.register_adapter(adapter)
    task = make_edge_task(task_id="late-live-read")
    task.allow_fallback = False
    task.validation_timeout_ms = 20
    try:
        result = orchestrator.execute_task(task)
        assert not result.success and adapter.started.is_set()
        assert result.final_lifecycle.state == "unreachable"
        assert not orchestrator.reconcile_backend("bad").success
        pending = next(iter(orchestrator._provider_failures["bad"][1]))
        adapter.release.set()
        assert pending.wait(1)
        assert orchestrator.reconcile_backend("bad").success
        assert adapter.invokes == (0 if blocked_read == 3 else 1)
    finally:
        adapter.release.set()


def test_unexpected_precondition_bug_releases_acquired_lease_then_propagates():
    class BugOnSecondRead(FaultAdapter):
        reads = 0
        def resource_contract(self):
            self.reads += 1
            if self.reads == 2:
                raise RuntimeError("unexpected post-reservation bug")
            return super().resource_contract()
    orchestrator = CP2N2Orchestrator()
    adapter = BugOnSecondRead()
    orchestrator.register_adapter(adapter)
    with pytest.raises(RuntimeError, match="post-reservation bug"):
        orchestrator.execute_task(make_edge_task(task_id="cleanup-bug"))
    assert orchestrator.registry.lease_store.current("bad") is None
    assert orchestrator.registry.lifecycle_store.snapshot("bad").state == "unreachable"
    assert adapter.invokes == 0
