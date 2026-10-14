"""Separate AP1 official-MCP effect evidence; historical campaigns are immutable."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
from unittest.mock import patch

from descriptors.capability_schema import TelemetryField
from adapters.contracts import AdapterPreparationResult
from descriptors.resource_contract import TelemetryObservation, ObservationSource, Uncertainty, UncertaintyKind
from evaluation.r3_enforcement import Environment
from evaluation.r3_effect_backend import MOCK_PRESET, json_safe
from evaluation.r3_archives import check_audit_calls, verify_files
from evaluation.verify_r3_enforcement import effect_observations
from evaluation.biopattern_gate_native import file_sha256
from mcp_surface.catalog import get_preset
from runtimes.biopattern_gate_sdk_runtime import write_json


# Expectations concern real effects, not agreement with production code.
CASES = {
    "positive_required": [1, 1, 1],
    "positive_optional_missing_drift": [1, 1, 1],
    "drift_null": [0, 0, 0], "drift_string": [0, 0, 0],
    "drift_bool": [0, 0, 0], "drift_nan": [0, 0, 0], "drift_inf": [0, 0, 0],
    "age_null": [0, 0, 0], "age_bool": [0, 0, 0], "age_negative": [0, 0, 0],
    "age_nan": [0, 0, 0], "age_expired": [0, 0, 0],
    "calibration_missing": [0, 0, 0], "calibration_stale": [0, 0, 0],
    "fresh_cached_health": [1, 1, 1], "expired_cached_health": [0, 0, 0],
    "contradictory_health": [0, 0, 0],
    "confidence_missing": [1, 1, 0], "confidence_nan": [1, 1, 0],
    "confidence_bool": [1, 1, 0], "confidence_low": [1, 1, 0],
    "post_null_drift": [1, 1, 0], "post_negative_age": [1, 1, 0],
    "bypass_detector": [0, 0, 0], "deny_all_detector": [1, 1, 1],
}
DETECTORS = {"bypass_detector": "forbidden_effect", "deny_all_detector": "valid_execution_missing"}
FAULTS = {
    "drift_null": ("drift_score", None), "drift_string": ("drift_score", "unknown"),
    "drift_bool": ("drift_score", True), "drift_nan": ("drift_score", float("nan")),
    "drift_inf": ("drift_score", float("inf")), "age_null": ("age_of_information_ms", None),
    "age_bool": ("age_of_information_ms", True), "age_negative": ("age_of_information_ms", -1.0),
    "age_nan": ("age_of_information_ms", float("nan")), "age_expired": ("age_of_information_ms", 10_001.0),
    "calibration_missing": ("calibration_status", None), "calibration_stale": ("calibration_status", "stale"),
    "positive_optional_missing_drift": ("drift_score", None), "bypass_detector": ("drift_score", "unknown"),
}
CONFIDENCE_FAULTS = {"confidence_missing": None, "confidence_nan": float("nan"),
    "confidence_bool": True, "confidence_low": 0.1}


def same_evidence(left, right):
    """JSON type equality: booleans must not compare equal to numeric 0/1."""
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(right, sort_keys=True, separators=(",", ":"))


def specification():
    return {"schema": "ap1-required-evidence-v1", "cases": CASES, "case_order": list(CASES),
            "detector_controls": DETECTORS, "repetitions": 2,
            "transport": "official_mcp_memory", "min_result_confidence": 0.25,
            "ordinary_cases_per_repetition": len(CASES) - len(DETECTORS),
            "fixture_overrides": {name: json_safe({key: value}) for name, (key, value) in FAULTS.items()},
            "confidence_faults": json_safe(CONFIDENCE_FAULTS),
            "physical_observations": 0, "gemini_cases_used": False}


def contract_evidence(contract):
    """Preserve fault values that Pydantic's JSON mode converts to null."""
    value = contract.model_dump(mode="json")
    for name, observation in contract.telemetry.items():
        value["telemetry"][name]["value"] = json_safe(observation.value)
    for name in ("health", "drift", "calibration", "lifecycle", "occupancy"):
        observation = getattr(contract.state, name)
        if observation is not None:
            value["state"][name]["value"] = json_safe(observation.value)
    return value


def run_case(root, name):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    env = Environment(root)
    # The historical E0 fixture independently rejects invalid age/calibration
    # during preparation. This new experiment must instead expose those effects
    # if the gateway fails to reject: validate fixed input only, not telemetry.
    def prepare_input_only(task):
        vector = task.metadata.get("input_vector")
        valid = (isinstance(vector, list) and len(vector) == 4
            and all(type(x) in {int, float} and math.isfinite(x) and -1 <= x <= 1 for x in vector)
            and task.metadata.get("input_unit", "relative") == "relative")
        env.runtime.cancelled = False
        write_json(root / "preparation-input-only.json", {"task_id": task.task_id,
            "prepared": valid, "metadata": json_safe(task.metadata),
            "provider_enforces_required_telemetry": False})
        return AdapterPreparationResult(prepared=valid, details="AP1 fixed input only; gateway enforces telemetry")
    env.runtime.prepare = prepare_input_only
    env.adapter._descriptor.telemetry.supports_age_of_information = True
    env.adapter._descriptor.telemetry.metrics.append(TelemetryField(
        name="calibration_status", units="state", description="Isolated E0 calibration state"))
    required = ["health_status", "drift_score", "age_of_information_ms", "calibration_status"]
    if name == "positive_optional_missing_drift":
        required.remove("drift_score")
    preset = replace(get_preset(MOCK_PRESET), required_telemetry_fields=tuple(required), max_twin_age_ms=10_000.0)
    original_contract = env.adapter.resource_contract
    cached = None
    if name in FAULTS:
        key, value = FAULTS[name]
        env.runtime.overrides[key] = value
    if name in {"fresh_cached_health", "expired_cached_health"}:
        now = datetime.now(timezone.utc)
        observed = now - timedelta(milliseconds=20) if name.startswith("fresh") else now - timedelta(seconds=60)
        cached = TelemetryObservation(value="healthy", unit="state", source=ObservationSource.OBSERVED,
            observed_at=observed, received_at=observed,
            valid_until=observed + timedelta(seconds=30), uncertainty=Uncertainty(kind=UncertaintyKind.NONE))
        env.adapter._resource_contract_observations = lambda: {"health_status": cached}
    if name == "contradictory_health":
        def contradictory():
            contract = original_contract()
            contract.state.health = contract.state.health.model_copy(update={"value": "degraded"})
            return contract
        env.adapter.resource_contract = contradictory
    original_invoke = env.adapter.invoke
    def exposed_invoke(task):
        result = original_invoke(task)
        original = json_safe(result.model_dump(mode="json"))
        if name.startswith("confidence_"):
            result.confidence = CONFIDENCE_FAULTS[name]
        if name == "post_null_drift": env.runtime.overrides["drift_score"] = None
        if name == "post_negative_age": env.runtime.overrides["age_of_information_ms"] = -1.0
        exposed = json_safe(result.model_dump(mode="json"))
        exposed["confidence"] = json_safe(result.confidence)
        write_json(root / "exposed-invocation.json", {"original": original,
            "exposed": exposed, "source": "isolated_adapter_return_boundary"})
        return result
    env.adapter.invoke = exposed_invoke
    write_json(root / "fixture.json", {"case": name, "expected": CASES[name],
        "required_fields": required, "min_confidence": 0.25, "overrides": json_safe(env.runtime.overrides),
        "provider_enforces_required_telemetry": False,
        "cached_health": None if cached is None else cached.model_dump(mode="json")})
    try:
        with patch("mcp_surface.service.get_preset", return_value=preset):
            reservation = env.reserve()
            prepared = env.prepare(reservation) if reservation["ok"] else reservation
            if prepared["ok"]:
                record = env.records._records[prepared["result"]["run_id"]]
                record.task.min_confidence = 0.25
                probe = env.run(prepared, surface=env.surface("owner-a", execute=False)) if name == "deny_all_detector" else env.run(prepared)
            else:
                probe = prepared
            if name == "bypass_detector":
                task = preset.build_task(run_id="isolated-bypass", principal_id="owner-a",
                    resource_id=env.resource_id, lease_id=None, expected_lease_version=None)
                env.runtime.execute(task)
            write_json(root / "measured-contract.json", contract_evidence(env.adapter.resource_contract()))
            write_json(root / "probe.json", json_safe(probe))
    finally:
        env.runtime.overrides.clear()
        env.adapter.resource_contract = original_contract
        env.adapter._resource_contract_observations = lambda: {}
        env.cleanup()
        env.save()
    return analyse_case(root, name)


def analyse_case(root, name):
    root = Path(root)
    calls, events = check_audit_calls(root)
    effects = effect_observations(root)
    deliveries = [c for c in calls if c["tool"] == "run_assay" and c["response"]["ok"]
                  and c["response"]["result"].get("summary", {}).get("success") is True]
    actual = [len(effects["starts"]), len(effects["commits"]), len(deliveries)]
    expected = CASES[name]
    violations = []
    fixture = json.loads((root / "fixture.json").read_text(encoding="utf-8"))
    contract = json.loads((root / "measured-contract.json").read_text(encoding="utf-8"))
    probe = json.loads((root / "probe.json").read_text(encoding="utf-8"))
    if probe not in [call["response"] for call in calls]: violations.append("unbound_probe")
    if (fixture["case"] != name or not same_evidence(fixture["expected"], expected)
            or fixture.get("provider_enforces_required_telemetry") is not False
            or fixture["min_confidence"] != 0.25):
        violations.append("fixture_policy_mismatch")
    required = ["health_status", "drift_score", "age_of_information_ms", "calibration_status"]
    if name == "positive_optional_missing_drift": required.remove("drift_score")
    if fixture["required_fields"] != required: violations.append("fixture_required_fields_mismatch")
    overrides = json_safe(dict([FAULTS[name]])) if name in FAULTS else {}
    if not same_evidence(fixture["overrides"], overrides): violations.append("fixture_fault_mismatch")
    for field, value in overrides.items():
        if not same_evidence(contract["telemetry"][field]["value"], value): violations.append("measured_fault_mismatch")
    if name == "contradictory_health" and not (
            contract["state"]["health"]["value"] == "degraded"
            and contract["telemetry"]["health_status"]["value"] == "healthy"):
        violations.append("measured_contradiction_mismatch")
    if name in {"post_null_drift", "post_negative_age"}:
        field, value = ("drift_score", None) if name == "post_null_drift" else ("age_of_information_ms", -1.0)
        if contract["telemetry"][field]["value"] != value: violations.append("postcondition_fault_mismatch")
    exposed_path = root / "exposed-invocation.json"
    if name in CONFIDENCE_FAULTS:
        exposed = json.loads(exposed_path.read_text(encoding="utf-8"))
        if (exposed["source"] != "isolated_adapter_return_boundary"
                or exposed["original"]["confidence"] != 0.5
                or not same_evidence(exposed["exposed"]["confidence"], json_safe(CONFIDENCE_FAULTS[name]))):
            violations.append("confidence_corruption_mismatch")
    if expected[0] == 0 and (actual[0] or actual[1]): violations.append("forbidden_effect")
    if expected[0] > 0 and actual[0] < expected[0]: violations.append("valid_execution_missing")
    if actual != expected: violations.append("outcome_counts")
    if effects["active"] or effects["overlaps"]: violations.append("active_or_overlapping_effect")
    if name in {"fresh_cached_health", "expired_cached_health"}:
        for key in ("observed_at", "received_at", "valid_until"):
            if contract["state"]["health"][key] != fixture["cached_health"][key]:
                violations.append("cached_observation_retimestamped")
        attempted_at = next(e.occurred_at for e in events if e.phase == "received" and e.request_id == probe["request_id"])
        cached = fixture["cached_health"]
        observed = datetime.fromisoformat(cached["observed_at"])
        received = datetime.fromisoformat(cached["received_at"])
        expires = datetime.fromisoformat(cached["valid_until"])
        age_ms = (attempted_at - observed).total_seconds() * 1000
        fresh = observed <= attempted_at and received <= attempted_at < expires and age_ms <= 10_000
        if fresh != (name == "fresh_cached_health"): violations.append("cached_fault_not_present_at_attempt")
    records = json.loads((root / "records.json").read_text(encoding="utf-8"))["records"]
    accepted_runs = {c["arguments"]["run_id"] for c in calls if c["tool"] == "run_assay" and c["response"]["ok"]}
    if name != "bypass_detector":
        for commit in effects["commits"]:
            record = next((r for r in records if r["task"]["task_id"] == commit["task_id"]), None)
            if (record is None or record["run_id"] not in accepted_runs
                    or record["owner_id"] != commit["principal_id"] or record["lease_id"] != commit["lease_id"]):
                violations.append("unauthorized_commit")
    tasks = [c["task_id"] for c in effects["commits"]]
    if len(tasks) != len(set(tasks)): violations.append("duplicate_commit")
    for delivery in deliveries:
        record = next(r for r in records if r["run_id"] == delivery["arguments"]["run_id"])
        if record["state"] != "succeeded" or record["summary"] != delivery["response"]["result"]["summary"]:
            violations.append("delivery_record_mismatch")
        if not any(e["task_id"] == record["task"]["task_id"] for e in effects["commits"]):
            violations.append("delivery_without_commit")
        result = effects["results"].get(record["task"]["task_id"])
        if (result is None or result["backend_id"] != record["resource_id"]
                or result["task_id"] != record["task"]["task_id"]
                or result["output_payload"] != {"probabilities": [0.2, 0.3, 0.5], "label_index": 2}):
            violations.append("delivery_result_identity_or_payload")
    final = json.loads((root / "final.json").read_text(encoding="utf-8"))
    if final["lease"] is not None or final["lifecycle"]["state"] != "ready" or not final["worker_done"]:
        violations.append("cleanup_unknown")
    verified = (DETECTORS[name] in violations and set(violations) <= {DETECTORS[name], "outcome_counts"}) if name in DETECTORS else not violations
    return {"case": name, "verified": verified, "detector_control": name in DETECTORS,
            "observed_starts": actual[0], "observed_commits": actual[1], "successful_deliveries": actual[2],
            "mcp_calls": len(calls), "audit_events": len(events), "violations": violations}


def verify_campaign(root):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"] != "ap1-archive-v1": raise ValueError("Unknown AP1 archive schema")
    verify_files(root, manifest["files"], excluded=("manifest.json",))
    frozen = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    if (frozen["schema"] != "ap1-freeze-v1" or set(frozen["inputs"]) != {
            "specification.json", "protocol.md", "environment.json", "source-snapshot.zip"}):
        raise ValueError("AP1 frozen input inventory mismatch")
    for name, digest in frozen["inputs"].items():
        if file_sha256(root / name) != digest: raise ValueError("AP1 frozen input hash mismatch")
    spec = json.loads((root / "specification.json").read_text(encoding="utf-8"))
    if not same_evidence(spec, specification()): raise ValueError("AP1 specification mismatch")
    rows = [analyse_case(root / f"repeat-{i:02d}" / name, name)
            for i in range(1, spec["repetitions"] + 1) for name in spec["case_order"]]
    ordinary = [r for r in rows if not r["detector_control"]]
    report = {"verified": all(r["verified"] for r in rows), "trials": rows,
        "ordinary_trials": len(ordinary), "detector_trials": len(rows) - len(ordinary),
        "starts": sum(r["observed_starts"] for r in ordinary), "commits": sum(r["observed_commits"] for r in ordinary),
        "successful_deliveries": sum(r["successful_deliveries"] for r in ordinary),
        "mcp_calls": sum(r["mcp_calls"] for r in rows), "audit_events": sum(r["audit_events"] for r in rows),
        "physical_observations": 0, "generic_replay_resistance": False, "gemini_cases_used": False}
    stored = json.loads((root / "verification.json").read_text(encoding="utf-8"))
    if not same_evidence(stored, report): raise ValueError("AP1 stored report differs from raw evidence")
    return report
