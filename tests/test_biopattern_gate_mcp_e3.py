from __future__ import annotations

from uuid import uuid4

from agent.biopattern_gate_client import BioPatternGateDeterministicClient
from applications.biopattern_gate.control_plane_contract import (
    BACKEND_ID,
    CONFIG_SHA256,
    DECODER_SHA256,
)
from demos.common import build_biopattern_gate_e3_orchestrator
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.auth import Scope
from mcp_surface.models import MCPPrincipal
from mcp_surface.service import MCPControlSurface
from mcp_surface.server import build_default_surface


def _surface(tmp_path, *, orchestrator=None, principal_id="e3-client"):
    return MCPControlSurface(
        orchestrator=orchestrator or build_biopattern_gate_e3_orchestrator(),
        principal=MCPPrincipal(
            principal_id=principal_id,
            scopes=[scope.value for scope in Scope],
        ),
        audit_trail=JsonlHashChainAuditTrail(
            tmp_path / f"biopattern-e3-{uuid4()}.jsonl"
        ),
    )


def _reserve_prepare(surface):
    reservation = surface.invoke(
        "reserve_resource",
        {"resource_id": BACKEND_ID, "ttl_seconds": 60},
    )
    assert reservation.ok, reservation
    prepared = surface.invoke(
        "prepare_assay",
        {
            "resource_id": BACKEND_ID,
            "preset_id": "pattern_gate_v1",
            "dry_run": False,
            "lease_id": reservation.result["lease_id"],
            "expected_lease_version": reservation.result["lease_version"],
        },
    )
    assert prepared.ok, prepared
    return reservation.result, prepared.result


def test_deterministic_client_executes_complete_audited_e3_lifecycle(tmp_path):
    surface = _surface(tmp_path)

    transcript = BioPatternGateDeterministicClient(surface).run()
    rendered = transcript.as_dict()
    summary = rendered["result_summary"]
    application = summary["application"]

    assert [step["stage"] for step in rendered["steps"]] == [
        "discover",
        "dry_run",
        "reserve",
        "prepare",
        "status_prepared",
        "run",
        "status_terminal",
        "result",
        "automatic_release",
    ]
    assert summary["success"] is True
    assert summary["runtime_kind"] == "sdk_simulator"
    assert summary["evidence_level"] == "E3"
    assert summary["raw_output_included"] is False
    assert application["config_sha256"] == CONFIG_SHA256
    assert application["decoder_sha256"] == DECODER_SHA256
    assert (
        application["application_source_sha256"]
        == "4229151b731c8685e35ff46534f955cb48f040ca3307335f168b792b71bd09e4"
    )
    assert application["biological_claim"] is False
    assert application["application_status"] == "complete"
    assert application["trial_count"] == 14
    assert len(summary["artifact_references"]) == 1
    assert len(transcript.audit_request_ids) == 8
    assert surface.audit_trail.verify()
    assert (
        surface.orchestrator.registry.lease_store.current(BACKEND_ID) is None
    )


def test_public_schema_rejects_agent_supplied_physical_parameters(tmp_path):
    surface = _surface(tmp_path)

    response = surface.invoke(
        "prepare_assay",
        {
            "resource_id": BACKEND_ID,
            "preset_id": "pattern_gate_v1",
            "dry_run": True,
            "electrode": 42,
            "amplitude": 2.0,
        },
    )

    assert response.ok is False
    assert response.error.code == "INVALID_REQUEST"
    assert surface.audit_trail.verify()


def test_competing_reservation_is_rejected_and_owner_can_release(tmp_path):
    orchestrator = build_biopattern_gate_e3_orchestrator()
    owner = _surface(
        tmp_path,
        orchestrator=orchestrator,
        principal_id="reservation-owner",
    )
    competitor = _surface(
        tmp_path,
        orchestrator=orchestrator,
        principal_id="reservation-competitor",
    )
    reservation = owner.invoke(
        "reserve_resource",
        {"resource_id": BACKEND_ID, "ttl_seconds": 60},
    )
    assert reservation.ok

    denied = competitor.invoke(
        "reserve_resource",
        {"resource_id": BACKEND_ID, "ttl_seconds": 60},
    )
    assert denied.ok is False
    assert denied.error.code == "CONFLICT"

    released = owner.invoke(
        "release_resource",
        {
            "resource_id": BACKEND_ID,
            "lease_id": reservation.result["lease_id"],
        },
    )
    assert released.ok
    assert released.result["released"] is True


def test_stale_e3_telemetry_fails_dry_run_without_reservation(tmp_path):
    orchestrator = build_biopattern_gate_e3_orchestrator(
        telemetry_age_ms=5_000.0
    )
    surface = _surface(tmp_path, orchestrator=orchestrator)

    response = surface.invoke(
        "prepare_assay",
        {
            "resource_id": BACKEND_ID,
            "preset_id": "pattern_gate_v1",
            "dry_run": True,
        },
    )

    assert response.ok
    assert response.result["plan"]["admissible_and_feasible"] is False
    report = response.result["plan"]["selection_report"]["candidates"][0]
    assert any(
        "age_of_information_ms" in reason
        for reason in report["rejection_reasons"]
    )
    assert orchestrator.registry.lease_store.current(BACKEND_ID) is None


def test_controlled_abort_of_prepared_run_releases_resource(tmp_path):
    surface = _surface(tmp_path)
    _, prepared = _reserve_prepare(surface)

    aborted = surface.invoke(
        "abort_run",
        {"run_id": prepared["run_id"]},
    )

    assert aborted.ok
    assert aborted.result["state"] == "aborted"
    assert aborted.result["resource_lifecycle"]["state"] == "ready"
    assert (
        surface.orchestrator.registry.lease_store.current(BACKEND_ID) is None
    )
    summary = surface.invoke(
        "get_result_summary",
        {"run_id": prepared["run_id"]},
    )
    assert summary.ok
    assert summary.result["state"] == "aborted"


def test_interrupted_application_is_failed_with_partial_artifact(tmp_path):
    orchestrator = build_biopattern_gate_e3_orchestrator(
        fail_after_trials=3
    )
    surface = _surface(tmp_path, orchestrator=orchestrator)
    _, prepared = _reserve_prepare(surface)

    executed = surface.invoke(
        "run_assay",
        {"run_id": prepared["run_id"]},
    )

    assert executed.ok
    assert executed.result["state"] == "failed"
    summary = executed.result["summary"]
    assert summary["success"] is False
    assert summary["raw_output_included"] is False
    assert summary["application"] == {}
    assert len(summary["artifact_references"]) == 1
    partial = summary["artifact_references"][0]
    assert partial["kind"] == "biopattern_gate_partial_summary"
    assert partial["metadata"]["application_status"] == "partial"
    assert partial["metadata"]["completed_trial_count"] == 3
    assert partial["metadata"]["biological_claim"] is False
    assert orchestrator.registry.lease_store.current(BACKEND_ID) is None


def test_stdio_server_can_register_e3_application_from_environment(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("CP2N2_PRINCIPAL_ID", "e3-server-client")
    monkeypatch.setenv("CP2N2_SCOPES", Scope.RESOURCES_READ.value)
    monkeypatch.setenv("CP2N2_INCLUDE_BIOPATTERN_GATE_E3", "1")
    monkeypatch.setenv("CP2N2_INCLUDE_CORTICAL_LABS", "0")
    monkeypatch.setenv("CP2N2_AUDIT_PATH", str(tmp_path / "server-audit.jsonl"))

    surface = build_default_surface()
    discovered = surface.invoke(
        "discover_resources",
        {"include_unavailable": True, "limit": 100},
    )

    assert discovered.ok
    resources = {
        resource["resource_id"]: resource
        for resource in discovered.result["resources"]
    }
    assert resources[BACKEND_ID]["runtime_kind"] == "sdk_simulator"
    assert resources[BACKEND_ID]["evidence_level"] == "E3"
