"""Native-validated official SDK binding for the existing MCP assay preset."""

from pathlib import Path

from adapters.base_adapter import BaseAdapter
from adapters.biopattern_gate_e3_adapter import BioPatternGateE3Adapter
from adapters.contracts import RuntimeArtifact, make_adapter_capability_declaration
from applications.biopattern_gate.control_plane_contract import BACKEND_ID
from descriptors.resource_contract import EvidenceLevel, ObservationSource, RuntimeKind
from evaluation.biopattern_gate_native import file_sha256, verify_native_execution
from runtimes.biopattern_gate_sdk_runtime import BioPatternGateSDKRuntime, write_json


class BioPatternGateSDKAdapter(BaseAdapter):
    def __init__(self, output_directory: Path) -> None:
        descriptor = BioPatternGateE3Adapter._build_descriptor(BACKEND_ID)
        descriptor.version = "r2-sdk-bridge-v1"
        descriptor.twin_binding.twin_kind = "official_cl_sdk_responsive_simulator"
        runtime = BioPatternGateSDKRuntime(output_directory)
        super().__init__(
            descriptor, runtime=runtime,
            capability_declaration=make_adapter_capability_declaration(
                adapter_id=f"{type(self).__module__}.{type(self).__qualname__}",
                descriptor=descriptor, runtime=runtime.capabilities,
                evidence_ceiling=EvidenceLevel.E3_SDK_SIMULATOR,
                notes="Fresh official SDK runner, native spike reconstruction and confirmed local process-job cancellation.",
            ),
            runtime_kind=RuntimeKind.SDK_SIMULATOR, provider_id="cortical-labs-sdk-simulator",
            attestation_method="local_sdk_simulator_guard_and_native_recording_validation",
            telemetry_source=ObservationSource.OBSERVED,
        )

    def validate_result(self, task, invocation) -> list[str]:
        runtime = self.runtime
        summary = invocation.output_payload["application_summary"]
        try:
            if invocation.task_id != task.task_id or invocation.backend_id != self.backend_id():
                raise ValueError("invocation task/resource mismatch")
            runtime._check_sources()
            attempt = runtime.attempt
            if attempt is None or any(attempt[key] != value for key, value in {
                "task_id": task.task_id, "principal_id": task.client_id, "lease_id": task.lease_id,
                "execution_attempt_id": summary["execution_attempt_id"], "sdk_run_id": summary["sdk_run_id"],
            }.items()):
                raise ValueError("execution attempt identity mismatch")
            attempt_directory = runtime.attempt_directory
            output = attempt_directory / "sdk-output"
            recordings = list(output.glob("*.h5"))
            if len(recordings) != 1:
                raise ValueError("expected exactly one fresh native SDK recording")
            report = verify_native_execution(recordings[0], output / "result.json", expected_run_id=attempt["sdk_run_id"])
            write_json(attempt_directory / "native-validation.json", report)
            artifacts = [
                RuntimeArtifact(
                    artifact_id=f"{attempt['execution_attempt_id']}:{kind}", kind=kind,
                    uri=f"evidence://r2/{attempt['execution_attempt_id']}/{path.name}", media_type=media_type,
                    metadata={"sha256": file_sha256(path), "runtime_kind": "sdk_simulator",
                              "evidence_level": "E3", "biological_claim": False, "validated": True},
                )
                for kind, path, media_type in (
                    ("cl_native_recording", recordings[0], "application/x-hdf5"),
                    ("native_validation_report", attempt_directory / "native-validation.json", "application/json"),
                )
            ]
            with runtime._lock:
                if runtime.attempt is not attempt or runtime._aborted:
                    raise ValueError("attempt invalidated before validation completed")
                summary.update({key: report[key] for key in (
                    "trial_count", "scored_trial_count", "sham_trial_count",
                    "pipeline_assertion_accuracy", "native_recording_sha256",
                )})
                summary.update(application_status="complete", native_validation_verified=True)
                runtime._last_status = "complete"
                runtime._artifacts = artifacts
            return []
        except Exception as exc:
            summary.update(application_status="invalid", native_validation_verified=False)
            with runtime._lock:
                if runtime._prepared_task_id == task.task_id:
                    runtime._last_status = "invalid"
            return [f"native SDK result validation failed: {exc}"]
