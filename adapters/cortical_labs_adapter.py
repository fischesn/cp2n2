"""Cortical Labs adapter for the phys-MCP prototype."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from adapters.base_adapter import AdapterInvocationResult, AdapterPreparationResult, BaseAdapter
from backends.cortical.cl_client import (
    CLClient,
    CorticalLabsInvocationError,
    CorticalLabsUnavailableError,
)
from core.task_model import TaskRequest
from descriptors.capability_schema import (
    CapabilityDescriptor,
    IOContract,
    IOEncoding,
    LifecycleContract,
    Locality,
    ObservabilityLevel,
    PolicyConstraints,
    ResetMode,
    SignalModality,
    SubstrateClass,
    SubstrateDescriptor,
    TelemetryContract,
    TelemetryField,
    TenancyModel,
    TimingContract,
    TimingRegime,
    TrainingMode,
    TwinBinding,
)
from descriptors.resource_contract import (
    EXPECTED_EVIDENCE_LEVEL,
    EvidenceLevel,
    ObservationSource,
    RuntimeKind,
)


class CorticalLabsAdapter(BaseAdapter):
    def __init__(
        self,
        backend_id: str = "cortical-labs-backend",
        *,
        use_simulator: bool | None = True,
    ) -> None:
        self._client = CLClient(use_simulator=use_simulator)
        self._expected_runtime_kind = (
            "sdk_simulator"
            if use_simulator is True
            else "physical_hardware"
            if use_simulator is False
            else "unknown"
        )
        self._last_runtime_kind: str = "unknown"
        self._session_open = False
        self._last_backend_latency_ms: float | None = None
        self._last_observation_latency_ms: float | None = None
        self._last_recording_artifact: dict | None = None
        self._last_health_status: str = "unknown"
        self._last_readiness_state: str = "unavailable"
        self._last_channel_count: int | None = None
        self._last_fps: float | None = None
        self._last_age_of_information_ms: float | None = None
        self._last_prepare_timestamp: float | None = None
        self._last_attested_at: datetime | None = None

        descriptor = self._build_descriptor(
            backend_id=backend_id,
            expected_runtime_kind=self._expected_runtime_kind,
        )
        super().__init__(
            descriptor=descriptor,
            runtime_kind=RuntimeKind.UNKNOWN,
            provider_id="cortical-labs",
            attestation_method="cl_sdk_is_simulator",
            telemetry_source=ObservationSource.OBSERVED,
        )

    def describe(self) -> SubstrateDescriptor:
        return self.descriptor

    def prepare(self, task: TaskRequest) -> AdapterPreparationResult:
        human_supervision_available = getattr(task, "human_supervision_available", True)
        if not human_supervision_available:
            self._last_readiness_state = "rejected"
            self._last_health_status = "unknown"
            return AdapterPreparationResult(
                prepared=False,
                details="Cortical Labs backend requires human supervision.",
            )

        if not self._client.is_available():
            self._session_open = False
            self._last_readiness_state = "unavailable"
            self._last_health_status = "unknown"
            return AdapterPreparationResult(
                prepared=False,
                details="Cortical Labs SDK is not installed or importable.",
            )

        try:
            info = self._client.open_session()
        except CorticalLabsUnavailableError as exc:
            self._session_open = False
            self._last_readiness_state = "unavailable"
            self._last_health_status = "unknown"
            return AdapterPreparationResult(prepared=False, details=str(exc))

        self._session_open = True
        self._last_readiness_state = "ready"
        self._last_health_status = "unknown"
        self._last_runtime_kind = info.runtime_kind
        self._last_attested_at = datetime.now(timezone.utc)
        self._last_channel_count = info.channel_count
        self._last_fps = info.fps
        self._last_prepare_timestamp = time.perf_counter()

        details = "Cortical Labs session opened successfully."
        if info.channel_count is not None:
            details += f" channels={info.channel_count}"
        if info.fps is not None:
            details += f", fps={info.fps}"

        return AdapterPreparationResult(prepared=True, details=details)

    def invoke(self, task: TaskRequest) -> AdapterInvocationResult:
        if not self._session_open:
            return AdapterInvocationResult(
                backend_id=self.backend_id(),
                task_id=task.task_id,
                output_payload={},
                confidence=None,
                execution_latency_ms=0.0,
                backend_state="unavailable",
                notes="Cortical Labs session is not open; call prepare() first.",
            )

        channel, amplitude_ua = self._extract_stimulation(task)
        observation_window_ms = self._extract_observation_window(task)
        pre_delay_ms = self._extract_pre_delay(task)

        try:
            result = self._client.stimulate_and_record(
                channel=channel,
                amplitude_ua=amplitude_ua,
                observation_window_ms=observation_window_ms,
                pre_delay_ms=pre_delay_ms,
            )
        except CorticalLabsInvocationError as exc:
            self._last_health_status = "degraded"
            self._last_readiness_state = "ready"
            return AdapterInvocationResult(
                backend_id=self.backend_id(),
                task_id=task.task_id,
                output_payload={},
                confidence=None,
                execution_latency_ms=0.0,
                backend_state="error",
                notes=str(exc),
            )

        self._last_backend_latency_ms = result.backend_latency_ms
        self._last_observation_latency_ms = result.observation_latency_ms
        self._last_recording_artifact = result.recording_artifact
        self._last_health_status = "unknown"
        self._last_readiness_state = "ready"
        self._last_runtime_kind = self._client.runtime_kind()

        output_payload = {
            "response_fingerprint": result.response_summary.get(
                "response_fingerprint",
                "recording_completed",
            ),
            "observation_window_ms": observation_window_ms,
            "stim_channel": channel,
            "stim_amplitude_ua": amplitude_ua,
            "recording_artifact": result.recording_artifact,
            "raw_backend_metadata": result.raw_backend_metadata,
        }

        notes = (
            "Cortical Labs stimulation/recording cycle completed "
            f"on {self._last_runtime_kind}."
        )
        if result.recording_artifact and result.recording_artifact.get("path"):
            notes += f" recording_path={result.recording_artifact['path']}"

        return AdapterInvocationResult(
            backend_id=self.backend_id(),
            task_id=task.task_id,
            output_payload=output_payload,
            confidence=None,
            execution_latency_ms=result.backend_latency_ms,
            backend_state="ready",
            notes=notes,
        )

    def collect_telemetry(self) -> dict[str, float | int | str | bool | None]:
        health = self._client.get_health_status()
        readiness_state = str(health.get("readiness_state", self._last_readiness_state))
        health_status = str(health.get("health_status", self._last_health_status))
        channel_count = health.get("channel_count", self._last_channel_count)
        fps = health.get("fps", self._last_fps)

        age_of_information_ms = None
        if self._last_prepare_timestamp is not None:
            age_of_information_ms = (time.perf_counter() - self._last_prepare_timestamp) * 1000.0

        telemetry = {
            "readiness_state": readiness_state,
            "health_status": health_status,
            "backend_latency_ms": self._last_backend_latency_ms,
            "observation_latency_ms": self._last_observation_latency_ms,
            "channel_count": channel_count,
            "fps": fps,
            "runtime_kind": health.get("runtime_kind", self._last_runtime_kind),
            "drift_score": None,
            "age_of_information_ms": age_of_information_ms,
            "telemetry_source": "local_session_observation",
            "sdk_available": self._client.is_available(),
        }

        if self._last_recording_artifact and self._last_recording_artifact.get("path"):
            telemetry["recording_path"] = self._last_recording_artifact["path"]

        return telemetry

    def reset(self, mode: ResetMode | None = None) -> bool:
        self._client.close_session()
        self._session_open = False
        self._last_readiness_state = "unavailable"
        self._last_health_status = "unknown"
        self._last_backend_latency_ms = None
        self._last_observation_latency_ms = None
        self._last_recording_artifact = None
        self._last_age_of_information_ms = None
        self._last_runtime_kind = "unknown"
        self._last_attested_at = None
        return True

    def recalibrate(self) -> bool:
        self._client.close_session()
        self._session_open = False
        self._last_readiness_state = "unavailable"
        self._last_health_status = "unknown"
        if not self._client.is_available():
            return False
        try:
            info = self._client.open_session()
        except CorticalLabsUnavailableError:
            return False
        self._session_open = True
        self._last_readiness_state = "ready"
        self._last_health_status = "unknown"
        self._last_runtime_kind = info.runtime_kind
        self._last_attested_at = datetime.now(timezone.utc)
        self._last_channel_count = info.channel_count
        self._last_fps = info.fps
        self._last_prepare_timestamp = time.perf_counter()
        return True

    def abort(self) -> bool:
        """Close the active CL session without issuing further stimulation."""
        return self.reset(mode=ResetMode.SOFT_RESET)

    def abort_supported(self) -> bool:
        return True

    def _resource_contract_runtime_evidence(
        self,
    ) -> tuple[RuntimeKind, EvidenceLevel, str, datetime | None, dict]:
        try:
            runtime_kind = RuntimeKind(self._last_runtime_kind)
        except ValueError:
            runtime_kind = RuntimeKind.UNKNOWN
        method = (
            "cl_sdk_is_simulator"
            if runtime_kind != RuntimeKind.UNKNOWN
            else "runtime_not_yet_attested"
        )
        return (
            runtime_kind,
            EXPECTED_EVIDENCE_LEVEL[runtime_kind],
            method,
            self._last_attested_at,
            {"configured_expectation": self._expected_runtime_kind},
        )

    @staticmethod
    def _extract_stimulation(task: TaskRequest) -> tuple[int, float]:
        pattern = task.metadata.get("stimulation_pattern", {})
        channels = pattern.get("channels", [1])
        amplitude = pattern.get("amplitude", 0.4)
        try:
            channel = int(channels[0]) if channels else 1
        except (TypeError, ValueError, IndexError):
            channel = 1
        try:
            amplitude_ua = float(amplitude)
        except (TypeError, ValueError):
            amplitude_ua = 0.4
        return channel, amplitude_ua

    @staticmethod
    def _extract_observation_window(task: TaskRequest) -> int:
        raw_value = task.metadata.get("observation_window_ms", 100)
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return 100

    @staticmethod
    def _extract_pre_delay(task: TaskRequest) -> int:
        raw_value = task.metadata.get("pre_delay_ms", 20)
        try:
            return int(raw_value)
        except (TypeError, ValueError):
            return 20

    @staticmethod
    def _build_descriptor(
        backend_id: str,
        expected_runtime_kind: str,
    ) -> SubstrateDescriptor:
        return SubstrateDescriptor(
            backend_id=backend_id,
            display_name="Cortical Labs CL API Backend",
            version="0.1.1",
            description=(
                "Optional adapter targeting the public Cortical Labs CL API / "
                "CL SDK. The active runtime is attested as simulator, physical "
                "hardware, or unknown before a session is opened."
            ),
            input_contracts=[
                IOContract(
                    name="stimulation_input",
                    modality=SignalModality.SPIKES,
                    encoding=IOEncoding.EVENT_STREAM,
                    description="Spike-oriented stimulation requests mapped onto CL API stimulation calls.",
                ),
                IOContract(
                    name="control_input",
                    modality=SignalModality.CONTROL_SIGNAL,
                    encoding=IOEncoding.JSON,
                    required=False,
                    description="Optional session and recording configuration metadata.",
                ),
            ],
            output_contracts=[
                IOContract(
                    name="recording_and_state",
                    modality=SignalModality.SPIKES,
                    encoding=IOEncoding.JSON,
                    description="Recording metadata and session-visible wetware state.",
                )
            ],
            timing=TimingContract(
                regime=TimingRegime.MILLISECONDS,
                typical_latency_ms=100.0,
                latency_jitter_ms=20.0,
                warmup_required=True,
                streaming_supported=True,
            ),
            lifecycle=LifecycleContract(
                supported_reset_modes=[ResetMode.SOFT_RESET, ResetMode.REST, ResetMode.RECALIBRATE],
                reprogrammable=True,
                recalibration_supported=True,
                stateful=True,
                notes="Physical reset and wetware handling remain application-specific; the adapter models session-level recovery.",
            ),
            telemetry=TelemetryContract(
                metrics=[
                    TelemetryField(
                        name="backend_latency_ms",
                        units="ms",
                        description="Most recent CL API round-trip latency including the observation cycle.",
                        lower_is_better=True,
                    ),
                    TelemetryField(
                        name="observation_latency_ms",
                        units="ms",
                        description="Latency measured from stimulation until the observation cycle completes.",
                        lower_is_better=True,
                    ),
                    TelemetryField(
                        name="readiness_state",
                        units="state",
                        description="Current readiness state of the Cortical Labs session.",
                        lower_is_better=None,
                    ),
                    TelemetryField(
                        name="health_status",
                        units="state",
                        description="Provider health status when available; otherwise unknown.",
                        lower_is_better=None,
                    ),
                    TelemetryField(
                        name="recording_path",
                        units="path",
                        description="Path to the most recent recording artifact when available.",
                        lower_is_better=None,
                    ),
                    TelemetryField(
                        name="channel_count",
                        units="count",
                        description="Channel count reported by the active CL session.",
                        lower_is_better=None,
                    ),
                    TelemetryField(
                        name="fps",
                        units="frames_per_second",
                        description="Frames per second reported by the CL session.",
                        lower_is_better=None,
                    ),
                    TelemetryField(
                        name="runtime_kind",
                        units="kind",
                        description="Attested CL runtime: sdk_simulator, physical_hardware, or unknown.",
                        lower_is_better=None,
                    ),
                    TelemetryField(
                        name="age_of_information_ms",
                        units="ms",
                        description="Elapsed time since local session attributes were observed.",
                        lower_is_better=True,
                    ),
                    TelemetryField(
                        name="telemetry_source",
                        units="source",
                        description="Provenance of the reported telemetry snapshot.",
                        lower_is_better=None,
                    ),
                ],
                supports_health_status=False,
                supports_confidence=False,
                supports_drift_reporting=False,
                supports_age_of_information=True,
            ),
            twin_binding=TwinBinding(
                twin_kind=expected_runtime_kind,
                fidelity_level="interface_compatibility_only",
                calibration_confidence=0.0,
                twin_notes=(
                    "No substrate calibration confidence is inferred by this adapter. "
                    "The active runtime is attested at session open."
                ),
            ),
            policy=PolicyConstraints(
                locality=Locality.LAB,
                tenancy=TenancyModel.RESERVED,
                safety_notes="Wetware access with explicit stimulation and recording semantics.",
                exclusive_access_required=True,
                human_supervision_required=True,
            ),
            capability=CapabilityDescriptor(
                substrate_class=SubstrateClass.WETWARE,
                supported_task_types=["monitoring", "control", "temporal_inference"],
                training_mode=TrainingMode.HYBRID,
                observability=ObservabilityLevel.PARTIAL,
                stochastic=True,
                resettable=True,
                programmable=True,
                health_sensitive=True,
                repeated_invocation_supported=True,
            ),
            custom_metadata={
                "paper_role": "existing wetware API integration target",
                "sdk_package": "cl-sdk",
                "expected_runtime_kind": expected_runtime_kind,
                "evidence_level": "E3" if expected_runtime_kind == "sdk_simulator" else "unattested",
            },
        )
