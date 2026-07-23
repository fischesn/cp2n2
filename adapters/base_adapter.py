"""Abstract adapter interface for phys-MCP backend integrations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from core.task_model import TaskRequest
from descriptors.capability_schema import ResetMode, SubstrateDescriptor
from descriptors.resource_contract import (
    CONTRACT_SCHEMA_VERSION,
    EXPECTED_EVIDENCE_LEVEL,
    AccessContract,
    BillingModel,
    CostContract,
    DataGovernanceContract,
    EvidenceLevel,
    ObservationSource,
    PhysicalNeuralResourceContract,
    ResourceIdentity,
    ResourceLifecycleState,
    ResourceState,
    RuntimeEvidence,
    RuntimeKind,
    SafetyContract,
    SafetyLimit,
    TelemetryObservation,
    Uncertainty,
    UncertaintyKind,
)


class AdapterPreparationResult(BaseModel):
    """Outcome of a backend preparation step."""

    model_config = ConfigDict(extra="forbid")

    prepared: bool = Field(..., description="Whether preparation succeeded.")
    details: str = Field(default="", description="Short preparation summary.")


class AdapterInvocationResult(BaseModel):
    """Normalized result returned by a backend adapter invocation."""

    model_config = ConfigDict(extra="forbid")

    backend_id: str = Field(..., description="Identifier of the backend that produced the result.")
    task_id: str = Field(..., description="Identifier of the task that was executed.")
    output_payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Backend output payload normalized into a Python dictionary.",
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Optional confidence value reported by the backend.",
    )
    execution_latency_ms: float = Field(
        default=0.0,
        ge=0.0,
        description="Observed or estimated execution latency.",
    )
    backend_state: str = Field(
        default="ready",
        description="Backend-reported lifecycle state after invocation.",
    )
    notes: str | None = Field(default=None, description="Optional result notes.")


class BaseAdapter(ABC):
    """Common adapter interface used by the phys-MCP control plane.

    Each concrete adapter translates generic control-plane operations into the
    substrate-specific behavior of one backend or one digital twin.
    """

    def __init__(
        self,
        descriptor: SubstrateDescriptor,
        *,
        runtime_kind: RuntimeKind = RuntimeKind.SYNTHETIC_TWIN,
        provider_id: str = "phys-mcp",
        hardware_id: str | None = None,
        attestation_method: str = "in_process_adapter_construction",
        telemetry_source: ObservationSource = ObservationSource.ESTIMATED,
    ) -> None:
        self._descriptor = descriptor
        self._contract_runtime_kind = runtime_kind
        self._contract_provider_id = provider_id
        self._contract_hardware_id = hardware_id
        self._contract_attestation_method = attestation_method
        self._contract_telemetry_source = telemetry_source
        self._contract_attested_at = (
            None if runtime_kind == RuntimeKind.UNKNOWN else datetime.now(timezone.utc)
        )

    @property
    def descriptor(self) -> SubstrateDescriptor:
        """Return the immutable descriptor published by this adapter."""
        return self._descriptor

    def backend_id(self) -> str:
        """Return the backend identifier."""
        return self._descriptor.backend_id

    def resource_contract(self) -> PhysicalNeuralResourceContract:
        """Publish a versioned Physical Neural Resource Contract.

        The existing ``describe()`` method remains the compatibility API.
        This method adds evidence, provenance, and conservative safety
        semantics without changing substrate-specific invocation behavior.
        """

        now = datetime.now(timezone.utc)
        telemetry = self.collect_telemetry()
        source = self._resource_contract_telemetry_source()
        units = {metric.name: metric.units for metric in self.descriptor.telemetry.metrics}
        valid_until = now + timedelta(seconds=30)

        observations = {
            name: self._make_observation(
                value=value,
                unit=units.get(name),
                source=source,
                now=now,
                valid_until=valid_until,
            )
            for name, value in telemetry.items()
        }

        health_value = telemetry.get("health_status", "unknown")
        health_source = source if "health_status" in telemetry else ObservationSource.CONFIGURED
        health = self._make_observation(
            value=health_value,
            unit="state",
            source=health_source,
            now=now,
            valid_until=valid_until,
        )
        lifecycle_value = self._normalize_lifecycle_state(
            telemetry.get("readiness_state"),
            health_value,
        )
        lifecycle_source = (
            source
            if "readiness_state" in telemetry or "health_status" in telemetry
            else ObservationSource.CONFIGURED
        )
        lifecycle = self._make_observation(
            value=lifecycle_value,
            unit="state",
            source=lifecycle_source,
            now=now,
            valid_until=valid_until,
        )

        runtime_kind, evidence_level, method, attested_at, details = (
            self._resource_contract_runtime_evidence()
        )
        safety = SafetyContract(
            permitted_operations=self._resource_contract_permitted_operations(),
            hard_limits=self._resource_contract_hard_limits(),
            human_supervision_required=self.descriptor.policy.human_supervision_required,
            operator_acknowledgement_required=(
                True if self.descriptor.policy.human_supervision_required else False
            ),
            emergency_stop_supported=None,
            exclusive_access_required=self.descriptor.policy.exclusive_access_required,
            notes=self.descriptor.policy.safety_notes,
        )

        return PhysicalNeuralResourceContract(
            schema_version=CONTRACT_SCHEMA_VERSION,
            published_at=now,
            identity=ResourceIdentity(
                resource_id=self.backend_id(),
                provider_id=self._contract_provider_id,
                adapter_id=f"{self.__class__.__module__}.{self.__class__.__qualname__}",
                substrate_id=str(self.descriptor.capability.substrate_class),
                hardware_id=self._contract_hardware_id,
            ),
            evidence=RuntimeEvidence(
                runtime_kind=runtime_kind,
                evidence_level=evidence_level,
                attestation_method=method,
                attested_at=attested_at,
                attestation_details=details,
            ),
            capabilities=self.describe(),
            state=ResourceState(
                lifecycle=lifecycle,
                occupancy=observations.get("occupancy"),
                health=health,
                calibration=observations.get("calibration_confidence"),
                drift=observations.get("drift_score"),
            ),
            telemetry=observations,
            safety=safety,
            access=AccessContract(
                locality=str(self.descriptor.policy.locality),
                tenancy=str(self.descriptor.policy.tenancy),
                authentication_required=None,
                reservation_required=(
                    True if str(self.descriptor.policy.tenancy) == "reserved" else False
                ),
            ),
            cost=CostContract(
                billing_model=BillingModel.UNKNOWN,
                notes="No cost information has been published by this prototype adapter.",
            ),
            data_governance=DataGovernanceContract(
                notes="No provider data-retention declaration is available."
            ),
        )

    def _resource_contract_runtime_evidence(
        self,
    ) -> tuple[RuntimeKind, EvidenceLevel, str, datetime | None, dict[str, Any]]:
        """Return runtime evidence; concrete adapters may override this hook."""

        return (
            self._contract_runtime_kind,
            EXPECTED_EVIDENCE_LEVEL[self._contract_runtime_kind],
            self._contract_attestation_method,
            self._contract_attested_at,
            {},
        )

    def _resource_contract_telemetry_source(self) -> ObservationSource:
        return self._contract_telemetry_source

    def _resource_contract_hard_limits(self) -> dict[str, SafetyLimit]:
        """Return explicitly known hard limits; an empty mapping means unknown."""

        return {}

    def _resource_contract_permitted_operations(self) -> list[str]:
        operations = ["describe", "collect_telemetry", "prepare", "invoke"]
        if self.descriptor.lifecycle.supported_reset_modes:
            operations.append("reset")
        if self.descriptor.lifecycle.recalibration_supported:
            operations.append("recalibrate")
        if self.abort_supported():
            operations.append("abort")
        return operations

    @staticmethod
    def _make_observation(
        *,
        value: Any,
        unit: str | None,
        source: ObservationSource,
        now: datetime,
        valid_until: datetime | None,
    ) -> TelemetryObservation:
        return TelemetryObservation(
            value=value,
            unit=unit,
            source=source,
            observed_at=None if source == ObservationSource.CONFIGURED else now,
            received_at=now,
            uncertainty=Uncertainty(kind=UncertaintyKind.UNKNOWN),
            valid_until=valid_until,
        )

    @staticmethod
    def _normalize_lifecycle_state(readiness: Any, health: Any) -> str:
        candidate = str(readiness or health or "unknown").strip().lower()
        aliases = {
            "healthy": ResourceLifecycleState.READY.value,
            "unavailable": ResourceLifecycleState.UNREACHABLE.value,
            "error": ResourceLifecycleState.FAILED.value,
            "rejected": ResourceLifecycleState.FAILED.value,
        }
        candidate = aliases.get(candidate, candidate)
        allowed = {state.value for state in ResourceLifecycleState}
        if candidate in allowed:
            return candidate
        return ResourceLifecycleState.UNKNOWN.value

    @abstractmethod
    def describe(self) -> SubstrateDescriptor:
        """Return the published substrate descriptor."""
        raise NotImplementedError

    @abstractmethod
    def prepare(self, task: TaskRequest) -> AdapterPreparationResult:
        """Prepare the backend for task execution.

        Examples include warmup, priming, loading weights, or validating the
        task against backend-specific preconditions.
        """
        raise NotImplementedError

    @abstractmethod
    def invoke(self, task: TaskRequest) -> AdapterInvocationResult:
        """Execute the task through the backend and return a normalized result."""
        raise NotImplementedError

    @abstractmethod
    def collect_telemetry(self) -> dict[str, float | int | str | bool | None]:
        """Return the latest telemetry snapshot from the backend."""
        raise NotImplementedError

    @abstractmethod
    def reset(self, mode: ResetMode | None = None) -> bool:
        """Reset or recover the backend state.

        If *mode* is None, the adapter may choose a sensible default reset mode.
        """
        raise NotImplementedError

    @abstractmethod
    def recalibrate(self) -> bool:
        """Trigger backend recalibration if supported."""
        raise NotImplementedError

    def abort(self) -> bool:
        """Attempt to stop an uncertain or active operation.

        Adapters must override this method only when their provider API offers
        a meaningful abort or session-close operation. Returning ``False`` is
        conservative: the control plane will not infer successful cancellation.
        """

        return False

    def abort_supported(self) -> bool:
        """Return whether ``abort()`` has provider-level semantics."""

        return False
