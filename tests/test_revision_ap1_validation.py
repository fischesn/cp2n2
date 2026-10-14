"""AP1 semantic checks, cache provenance and explicitly bounded regressions."""

from datetime import datetime, timedelta, timezone

import pytest

from adapters.edge_adapter import EdgeAdapter
from core.matcher import BackendMatcher
from core.telemetry_validation import (
    TelemetryPayloadError,
    finite_number,
    validate_required_observations,
    validate_required_values,
)
from demos.common import make_edge_task
from descriptors.resource_contract import ObservationSource


INVALID_NUMBERS = [None, True, False, "0.2", "unknown", float("nan"), float("inf"), -float("inf")]


@pytest.mark.parametrize("value", INVALID_NUMBERS)
def test_required_drift_cannot_bypass_numeric_semantics(value):
    task = make_edge_task()
    task.required_telemetry_fields = ["drift_score"]
    candidate = BackendMatcher().evaluate_descriptor(
        task, EdgeAdapter().describe(), runtime_state={"drift_score": value},
    )
    assert candidate.admission.passed
    assert not candidate.feasibility.passed
    assert not candidate.accepted
    assert candidate.ranking.rank_key == []
    assert any("drift_score" in reason for reason in candidate.rejection_reasons)


def test_required_unknown_drift_closes_historical_missing_telemetry_bug():
    """An existing historical selector oracle admitted this malformed value.

    Archived results are not changed: the new contract deliberately requires
    a finite numeric drift instead of treating the string as absent/optional.
    """
    task = make_edge_task()
    task.required_telemetry_fields = ["drift_score"]
    assert validate_required_values(task, {"drift_score": "unknown"})
    assert validate_required_values(task, {"drift_score": 0.0}) == []


def test_optional_absent_metrics_do_not_create_requirements():
    task = make_edge_task()
    assert validate_required_values(task, {}, phase="preconditions") == []
    task.min_confidence = 0
    assert validate_required_values(task, {}, phase="postconditions") == []
    assert BackendMatcher().evaluate_descriptor(task, EdgeAdapter().describe(), {}).accepted


@pytest.mark.parametrize("value", INVALID_NUMBERS + [-1.0])
def test_active_age_constraint_requires_nonnegative_finite_number(value):
    task = make_edge_task()
    task.max_twin_age_ms = 100
    assert validate_required_values(task, {"age_of_information_ms": value})


def test_inclusive_age_cost_and_confidence_boundaries():
    task = make_edge_task(min_confidence=0.5)
    task.max_twin_age_ms = 100
    task.max_estimated_cost = 2
    task.cost_currency = "EUR"
    values = {"age_of_information_ms": 100, "estimated_cost": 2}
    assert validate_required_values(task, values) == []
    assert validate_required_values(task, values, confidence=0.5, phase="postconditions") == []
    assert validate_required_values(task, {**values, "age_of_information_ms": 100.001})
    assert validate_required_values(task, {**values, "estimated_cost": 2.001})


@pytest.mark.parametrize("confidence", INVALID_NUMBERS + [-0.1, 1.1, 0.49])
def test_positive_confidence_requires_this_invocations_usable_result(confidence):
    task = make_edge_task(min_confidence=0.5)
    # Fresh telemetry confidence cannot stand in for the returned result.
    assert validate_required_values(
        task, {"confidence": 1.0}, confidence=confidence, phase="postconditions",
    )
    assert validate_required_values(task, {}, confidence=0.5, phase="postconditions") == []
    assert validate_required_values(task, {}, confidence=None, phase="preconditions") == []


@pytest.mark.parametrize("status", [None, "", "stale", "missing", "unknown", False])
def test_calibration_status_is_checked_only_when_required(status):
    task = make_edge_task()
    assert validate_required_values(task, {"calibration_status": status}) == []
    task.required_telemetry_fields = ["calibration_status"]
    assert validate_required_values(task, {"calibration_status": status})
    assert validate_required_values(task, {"calibration_status": "valid"}) == []


def test_required_health_is_task_scoped():
    task = make_edge_task()
    assert validate_required_values(task, {"health_status": "unknown"}) == []
    task.continuous_monitoring_required = True
    assert validate_required_values(task, {"health_status": "unknown"})
    assert validate_required_values(task, {"health_status": "healthy"}) == []


class CachedObservationEdge(EdgeAdapter):
    def __init__(self, observations=None):
        super().__init__()
        self.supplied = observations or {}

    def _resource_contract_observations(self):
        return self.supplied


def _observation(adapter, *, value=0.2, seconds_old=0, expires_after=30):
    observed_at = datetime.now(timezone.utc) - timedelta(seconds=seconds_old)
    return adapter._make_observation(
        value=value, unit="fraction", source=ObservationSource.PROVIDER_REPORTED,
        now=observed_at, valid_until=observed_at + timedelta(seconds=expires_after),
    )


def test_republishing_cached_observation_preserves_expiration_and_provenance():
    adapter = CachedObservationEdge()
    original = _observation(adapter, seconds_old=60, expires_after=1)
    adapter.supplied["drift_score"] = original
    first, second = adapter.resource_contract(), adapter.resource_contract()
    for contract in (first, second):
        assert contract.telemetry["drift_score"].model_dump() == original.model_dump()
        assert contract.state.drift.model_dump() == original.model_dump()
        assert contract.published_at > original.received_at
    task = make_edge_task()
    task.required_telemetry_fields = ["drift_score"]
    failures = validate_required_observations(task, second)
    assert any("required_observation_expired" in failure for failure in failures)
    # Fresh positive control, distinct from the expired cached observation.
    adapter.supplied["drift_score"] = _observation(adapter)
    assert validate_required_observations(task, adapter.resource_contract()) == []


def test_actual_required_observation_age_survives_fresh_zero_age_publication():
    adapter = CachedObservationEdge()
    adapter.supplied["drift_score"] = _observation(adapter, seconds_old=2)
    adapter.supplied["age_of_information_ms"] = _observation(adapter, value=0.0)
    task = make_edge_task()
    task.required_telemetry_fields = ["drift_score"]
    task.max_twin_age_ms = 1000
    failures = validate_required_observations(task, adapter.resource_contract())
    assert any("required_observation_age: drift_score" in failure for failure in failures)


def test_conflict_is_only_between_required_same_property_representations():
    adapter = EdgeAdapter()
    contract = adapter.resource_contract()
    contract.state.drift = contract.state.drift.model_copy(update={"value": 0.3})
    task = make_edge_task()
    assert validate_required_observations(task, contract) == []
    task.required_telemetry_fields = ["drift_score"]
    assert any("required_observation_conflict" in item for item in validate_required_observations(task, contract))
    contract.state.drift = contract.telemetry["drift_score"].model_copy(deep=True)
    assert validate_required_observations(task, contract) == []


@pytest.mark.parametrize("future_component", ["observation_and_receipt", "receipt_only"])
def test_required_future_provenance_is_rejected_without_max_age(future_component):
    adapter = CachedObservationEdge()
    point = datetime.now(timezone.utc)
    future = point + timedelta(seconds=30)
    observed = future if future_component == "observation_and_receipt" else point - timedelta(seconds=1)
    observation = _observation(adapter).model_copy(update={
        "observed_at": observed, "received_at": future,
        "valid_until": future + timedelta(seconds=30),
    })
    adapter.supplied["drift_score"] = observation
    task = make_edge_task()
    task.required_telemetry_fields = ["drift_score"]
    assert task.max_twin_age_ms is None
    failures = validate_required_observations(task, adapter.resource_contract())
    assert any("required_observation_future" in failure for failure in failures)


def test_default_synthetic_observations_are_newly_sampled_not_cached():
    adapter = EdgeAdapter()
    first, second = adapter.resource_contract(), adapter.resource_contract()
    assert first.telemetry["drift_score"].observed_at == first.published_at
    assert second.telemetry["drift_score"].observed_at == second.published_at
    assert second.telemetry["drift_score"].observed_at >= first.telemetry["drift_score"].observed_at


def test_non_object_provider_telemetry_has_specific_schema_error():
    adapter = EdgeAdapter()
    adapter.collect_telemetry = lambda: ["not", "an", "object"]
    with pytest.raises(TelemetryPayloadError):
        adapter.resource_contract()


def test_finite_number_never_coerces_or_overflows():
    assert finite_number(10 ** 1000) is None
    assert all(finite_number(item) is None for item in INVALID_NUMBERS)
    assert finite_number(0) == 0


def test_invalid_validation_phase_is_not_silently_interpreted():
    with pytest.raises(ValueError):
        validate_required_values(make_edge_task(), {}, phase="typo")
