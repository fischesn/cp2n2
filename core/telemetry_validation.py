"""Task-scoped semantic checks for required telemetry and result confidence.

These checks establish interpretability, not physical truth. Observation
expiry is a freshness check, not cryptographic replay protection. Optional
unknown fields are not made mandatory and no substrate safety limits are
inferred from a field name.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Mapping

from core.task_model import TaskRequest
from descriptors.resource_contract import PhysicalNeuralResourceContract


# Names with numeric semantics in the existing prototype descriptors/contracts.
NUMERIC_FIELDS = frozenset({
    "drift_score", "age_of_information_ms", "estimated_cost", "confidence",
    "last_confidence", "calibration_confidence", "last_latency_ms",
    "energy_proxy_mj", "contamination_level", "last_convergence_time_ms",
    "viability_score", "noise_level", "response_delay_ms",
})
CONFIDENCE_FIELDS = frozenset({"confidence", "last_confidence", "calibration_confidence"})
NONNEGATIVE_FIELDS = frozenset({
    "age_of_information_ms", "estimated_cost", "last_latency_ms",
    "energy_proxy_mj", "last_convergence_time_ms", "response_delay_ms",
})


class TelemetryPayloadError(ValueError):
    """A provider returned a non-object telemetry payload."""


def finite_number(value: Any) -> float | None:
    """Return a finite real JSON number without coercing bools or strings."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = float(value)
    except (OverflowError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _required_fields(task: TaskRequest, phase: str) -> set[str]:
    if phase not in {"preconditions", "postconditions"}:
        raise ValueError("phase must be 'preconditions' or 'postconditions'")
    required = set(task.required_telemetry_fields)
    if task.max_twin_age_ms is not None:
        required.add("age_of_information_ms")
    if phase == "preconditions" and task.max_estimated_cost is not None:
        required.add("estimated_cost")
    if task.continuous_monitoring_required:
        required.add("health_status")
    return required


def validate_required_values(
    task: TaskRequest,
    values: Mapping[str, Any],
    *,
    confidence: Any = None,
    phase: str = "preconditions",
) -> list[str]:
    """Check necessary fields before selection or before successful release.

Active age/cost constraints require usable observations even if their names
were not separately listed. Positive result-confidence requirements are
enforced only in the postcondition phase; prior telemetry cannot substitute
for confidence attached to this invocation's result.
    """
    failures: list[str] = []
    for name in sorted(_required_fields(task, phase)):
        value = values.get(name)
        if value is None:
            failures.append(f"required_telemetry_available: {name} is required but missing")
            continue
        if name in NUMERIC_FIELDS:
            number = finite_number(value)
            if number is None:
                failures.append(f"required_telemetry_semantics: {name} must be a finite number (not bool or string)")
            elif name in NONNEGATIVE_FIELDS and number < 0:
                failures.append(f"required_telemetry_semantics: {name} must be nonnegative")
            elif name in CONFIDENCE_FIELDS and not 0 <= number <= 1:
                failures.append(f"required_telemetry_semantics: {name} must lie in [0, 1]")
        elif name == "calibration_status":
            # 'valid' is the explicit status used by the binding contract.
            if not isinstance(value, str) or value.strip().lower() != "valid":
                failures.append("required_telemetry_semantics: calibration_status must be 'valid'")
        elif name == "health_status":
            if not isinstance(value, str) or value.strip().lower() not in {"healthy", "ready", "degraded"}:
                failures.append("required_telemetry_semantics: required health_status must be a known available state")
        elif isinstance(value, str) and not value.strip():
            failures.append(f"required_telemetry_semantics: {name} must not be empty")

    age = finite_number(values.get("age_of_information_ms"))
    if task.max_twin_age_ms is not None and age is not None and age > task.max_twin_age_ms:
        failures.append(f"telemetry_freshness: age_of_information_ms {age:g} exceeds bound {task.max_twin_age_ms:g}")
    cost = finite_number(values.get("estimated_cost"))
    if phase == "preconditions" and task.max_estimated_cost is not None and cost is not None and cost > task.max_estimated_cost:
        failures.append(f"cost_budget: estimated_cost {cost:g} exceeds bound {task.max_estimated_cost:g}")

    if phase == "postconditions" and task.min_confidence > 0:
        number = finite_number(confidence)
        if number is None or not 0 <= number <= 1:
            failures.append("result_confidence: positive min_confidence requires finite result confidence in [0, 1]")
        elif number < task.min_confidence:
            failures.append(f"result_confidence: confidence {number:g} is below required threshold {task.min_confidence:g}")
    return failures


def validate_required_observations(
    task: TaskRequest,
    contract: PhysicalNeuralResourceContract,
    *,
    at: datetime | None = None,
    phase: str = "preconditions",
) -> list[str]:
    """Check task-relevant observation expiry and same-property consistency.

Only duplicate representations of the *same* property are compared, e.g.
state.drift and telemetry.drift_score. Related-but-distinct health/lifecycle
and calibration-confidence/status properties are never conflated. Providers
remain responsible for truthful values and meaningful expiry bounds.
    """
    point = at or datetime.now(timezone.utc)
    required = _required_fields(task, phase)
    aliases = {
        "health_status": contract.state.health,
        "drift_score": contract.state.drift,
        "calibration_confidence": contract.state.calibration,
        "estimated_cost": None if contract.cost is None else contract.cost.estimated_cost,
    }
    failures: list[str] = []
    values: dict[str, Any] = {}
    for name in sorted(required):
        observation = contract.telemetry.get(name)
        alias = aliases.get(name)
        representations = [item for item in (observation, alias) if item is not None]
        if not representations:
            failures.append(f"required_observation_missing: {name} has no observation")
            continue
        values[name] = representations[0].value
        for item in representations:
            if not item.is_fresh(point):
                failures.append(f"required_observation_expired: {name} observation is stale")
                break
        if observation is not None and alias is not None:
            left, right = observation.value, alias.value
            same = left == right and (isinstance(left, bool) == isinstance(right, bool))
            if not same:
                failures.append(f"required_observation_conflict: {name} contradicts its state/cost representation")
        # Future observation/receipt metadata is inconsistent at the control
        # plane's evaluation time even without an explicit maximum age. This
        # requires normalized provider timestamps; no clock-skew tolerance is
        # inferred. Configured values have only a receipt timestamp.
        # A new envelope cannot hide the original required observation's age.
        for item in representations:
            baseline = item.observed_at or item.received_at
            actual_age_ms = (point - baseline).total_seconds() * 1000
            if actual_age_ms < 0 or item.received_at > point:
                failures.append(f"required_observation_future: {name} observation or receipt timestamp is in the future")
                break
            if task.max_twin_age_ms is not None and actual_age_ms > task.max_twin_age_ms:
                failures.append(f"required_observation_age: {name} observation exceeds task age bound")
                break
    # Result confidence belongs to invocation rather than contract telemetry.
    # Here validate field semantics without enforcing that separate obligation.
    validation_task = task
    if phase == "postconditions" and task.min_confidence > 0:
        validation_task = task.model_copy(update={"min_confidence": 0.0})
    failures.extend(validate_required_values(validation_task, values, phase=phase))
    return list(dict.fromkeys(failures))
