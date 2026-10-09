"""Fresh official CL SDK executions behind the frozen MCP assay contract."""

from __future__ import annotations

import json
from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys
from threading import RLock
from time import perf_counter
from uuid import uuid4

import cl

from adapters.contracts import (
    AdapterInvocationResult, ExecutionLocation, RuntimeArtifact,
    RuntimeCapabilityDeclaration, RuntimeOperation,
)
from applications.biopattern_gate.control_plane_contract import (
    APPLICATION_ID, BACKEND_ID, CONFIG_SHA256, DECODER_SHA256,
)
from core.task_model import TaskRequest
from descriptors.capability_schema import ResetMode
from descriptors.resource_contract import RuntimeKind
from runtimes.biopattern_gate_e3_runtime import (
    BioPatternGateE3Runtime, PROJECT_ROOT, application_source_digest,
)


SDK_APP_ROOT = PROJECT_ROOT / "cl-apps" / "cp2n2-biopattern-gate"


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


class BioPatternGateSDKRuntime(BioPatternGateE3Runtime):
    """Launch the official runner; never treat a timed-out child as stopped.

    This first checkpoint has no cooperative provider abort. An active child
    therefore keeps the resource unavailable until its exit is observed.
    """

    def __init__(self, output_directory: Path, *, backend_id: str = BACKEND_ID) -> None:
        super().__init__(backend_id=backend_id)
        self.output_directory = Path(output_directory).resolve()
        self._lock = RLock()
        self._process: subprocess.Popen | None = None
        self._executing = False
        self._cleanup_unknown = False
        self.attempt_directory: Path | None = None
        self.attempt: dict | None = None
        self.sdk_application_source_sha256 = application_source_digest(SDK_APP_ROOT / "src")
        self._runtime_capabilities = RuntimeCapabilityDeclaration(
            runtime_id=f"{backend_id}:official-sdk-subprocess-v1",
            runtime_kind=RuntimeKind.SDK_SIMULATOR,
            execution_location=ExecutionLocation.SAME_HOST_SERVICE,
            operations={RuntimeOperation.PREPARE, RuntimeOperation.EXECUTE, RuntimeOperation.TELEMETRY,
                        RuntimeOperation.RESET, RuntimeOperation.ARTIFACTS},
            artifact_kinds=["cl_native_recording", "native_validation_report"],
            time_critical_execution_local=True, provider_abort_supported=False,
        )

    def _check_sources(self) -> None:
        if application_source_digest() != self.application_source_sha256:
            raise ValueError("application source changed after runtime registration")
        if application_source_digest(SDK_APP_ROOT / "src" / "biopattern_gate") != self.application_source_sha256:
            raise ValueError("bundled SDK application core differs from frozen MCP core")
        if application_source_digest(SDK_APP_ROOT / "src") != self.sdk_application_source_sha256:
            raise ValueError("SDK application shell changed after runtime registration")

    def prepare(self, task: TaskRequest):
        with self._lock:
            if self._cleanup_unknown or self._executing or (self._process is not None and self._process.poll() is None):
                raise RuntimeError("SDK execution is still active or unresolved")
            if cl.is_simulator() is not True:
                raise RuntimeError("official SDK bridge is simulator-only")
            self._check_sources()
            result = super().prepare(task)
            self.attempt_directory = None
            self.attempt = None
            self._process = None
            return result

    def execute(self, task: TaskRequest) -> AdapterInvocationResult:
        with self._lock:
            self._validate_task(task)
            self._check_sources()
            if cl.is_simulator() is not True:
                raise RuntimeError("official SDK bridge is simulator-only")
            if task.task_id != self._prepared_task_id or self._aborted:
                raise RuntimeError("task is not prepared or was aborted")
            if self._executing or self.attempt is not None:
                raise RuntimeError("execution attempt already exists; retry through the control plane")
            self._executing = True
            self._last_status = "running"
        started = perf_counter()
        try:
            attempt_id = str(uuid4())
            sdk_run_id = f"cp2n2-sdk-{attempt_id}"
            directory = self.output_directory / attempt_id
            directory.mkdir(parents=True, exist_ok=False)
            self.attempt_directory = directory
            config = {
                "name": "CP2N2 R2 technical E3", "timeout_s": 30,
                "preset_id": "technical-e3", "config_sha256": CONFIG_SHA256,
                "decoder_sha256": DECODER_SHA256, "run_id": sdk_run_id,
            }
            write_json(directory / "sdk-config.json", config)
            self.attempt = {
                "schema_version": "r2-sdk-attempt-v1", "execution_attempt_id": attempt_id,
                "sdk_run_id": sdk_run_id, "sdk_run_id_origin": "controller_assigned",
                "principal_id": task.client_id, "task_id": task.task_id,
                "application_run_id": task.task_id.removeprefix("mcp-assay-"),
                "resource_id": self.backend_id, "lease_id": task.lease_id,
                "expected_lease_version": task.expected_lease_version,
                "idempotency_key": task.idempotency_key,
                "config_sha256": CONFIG_SHA256, "decoder_sha256": DECODER_SHA256,
                "application_source_sha256": self.application_source_sha256,
                "sdk_application_source_sha256": self.sdk_application_source_sha256,
                "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False,
                "cl_sdk_version": version("cl-sdk"), "python_version": sys.version.split()[0],
                "status": "launching",
            }
            write_json(directory / "attempt.json", self.attempt)
            env = dict(os.environ)
            env.update(PYTHONUTF8="1", CL_SDK_VISUALISATION="0", CL_SDK_ACCELERATED_TIME="1")
            with (directory / "sdk.log").open("w", encoding="utf-8") as log:
                with self._lock:
                    if self._aborted:
                        raise RuntimeError("execution cancelled before SDK launch")
                    process = subprocess.Popen(
                        [sys.executable, "-m", "cl.app.run", str(SDK_APP_ROOT),
                         str(directory / "sdk-config.json"), str(directory / "sdk-output")],
                        cwd=PROJECT_ROOT, env=env, stdout=log, stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                    )
                    self._process = process
                code = process.wait()
            self.attempt.update(status="exited", exit_code=code)
            write_json(directory / "attempt.json", self.attempt)
            if code != 0:
                # A failed parent process does not confirm SDK child cleanup.
                # Keep quarantine until a future provider reconciliation path
                # can establish termination, rather than infer it from exit.
                self._cleanup_unknown = True
                self._last_status = "failed"
                raise RuntimeError(f"official CL SDK runner exited with code {code}")
            self._last_status = "awaiting_validation"
            return AdapterInvocationResult(
                backend_id=self.backend_id, task_id=task.task_id,
                execution_latency_ms=(perf_counter() - started) * 1000, backend_state="ready",
                output_payload={"application_summary": {
                    "application_id": APPLICATION_ID,
                    "application_run_id": self.attempt["application_run_id"],
                    "execution_attempt_id": attempt_id, "sdk_run_id": sdk_run_id,
                    "sdk_run_id_origin": "controller_assigned", "application_status": "unvalidated",
                    "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False,
                    "config_sha256": CONFIG_SHA256, "decoder_sha256": DECODER_SHA256,
                    "application_source_sha256": self.application_source_sha256,
                    "sdk_application_source_sha256": self.sdk_application_source_sha256,
                    "native_validation_verified": False,
                }},
            )
        except Exception:
            self._last_status = "failed"
            if self.attempt is not None:
                self.attempt["status"] = "failed"
                write_json(self.attempt_directory / "attempt.json", self.attempt)
            raise
        finally:
            with self._lock:
                self._executing = False

    def telemetry(self) -> dict:
        with self._lock:
            active = self._cleanup_unknown or self._executing or (self._process is not None and self._process.poll() is None)
            return {
                "readiness_state": "unreachable" if active else "ready",
                "health_status": "unknown" if active else "healthy",
                "age_of_information_ms": 0.0, "application_status": self._last_status,
                "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False,
            }

    def abort(self) -> bool:
        with self._lock:
            self._aborted = True
            return not self._cleanup_unknown and not self._executing and (self._process is None or self._process.poll() is not None)

    def reset(self, mode: ResetMode | None = None) -> bool:
        with self._lock:
            if self._cleanup_unknown or self._executing or (self._process is not None and self._process.poll() is None):
                return False
            self._prepared_task_id = None
            self._last_status = "idle"
            self._aborted = False
            return True

    def artifacts(self) -> list[RuntimeArtifact]:
        return [item.model_copy(deep=True) for item in self._artifacts]
