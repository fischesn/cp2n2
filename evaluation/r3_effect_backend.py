"""Isolated effect-producing E0 binding and observers for existing E1 twins.

The backend does not read the control-plane audit or validate leases itself.
Every invocation really increments durable state, including duplicate calls.
Only the controller may prevent those effects. No physical device is exposed.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
import os
from pathlib import Path
from threading import Event, RLock
from uuid import uuid4

from adapters.base_adapter import BaseAdapter
from adapters.contracts import (AdapterInvocationResult, AdapterPreparationResult, ExecutionLocation,
    RuntimeCapabilityDeclaration, RuntimeOperation, make_adapter_capability_declaration)
from adapters.edge_adapter import EdgeAdapter
from descriptors.resource_contract import EvidenceLevel, ObservationSource, RuntimeKind
from runtimes.base_runtime import SubstrateRuntime
from evaluation.artifact_io import write_json


MOCK_ID = "r3-effect-mock"
MOCK_PRESET = "edge_vector_classification_v1"


def json_safe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


class EffectRuntime(SubstrateRuntime):
    def __init__(self, directory: Path, backend_id=MOCK_ID, *, delegate=None):
        capabilities = delegate.capabilities if delegate is not None else RuntimeCapabilityDeclaration(
            runtime_id=f"{backend_id}:effect-fixture-v1", runtime_kind=RuntimeKind.MOCK,
            execution_location=ExecutionLocation.IN_PROCESS,
            operations={RuntimeOperation.PREPARE, RuntimeOperation.EXECUTE, RuntimeOperation.TELEMETRY,
                        RuntimeOperation.RESET, RuntimeOperation.RECALIBRATE, RuntimeOperation.ABORT},
            time_critical_execution_local=True, provider_abort_supported=True,
        )
        super().__init__(capabilities)
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.backend_id, self.delegate = backend_id, delegate
        self.lock = RLock()
        self.started, self.release, self.done = Event(), Event(), Event()
        self.done.set()
        self.block = False
        self.abort_confirmed = True
        self.cancelled = False
        self.fault = None
        self.overrides = {}
        self._events = []
        write_json(self.directory / "state.json", {"commit_count": 0, "commits": []})

    def append(self, kind, *, task=None, **values):
        with self.lock:
            row = {"sequence": len(self._events) + 1, "kind": kind, "backend_id": self.backend_id,
                   "at": datetime.now(timezone.utc).isoformat(), **values}
            if task is not None:
                row.update(task_id=task.task_id, principal_id=task.client_id, lease_id=task.lease_id,
                           request_key=task.idempotency_key)
            row["previous_hash"] = self._events[-1]["event_hash"] if self._events else "0" * 64
            row["event_hash"] = hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            with (self.directory / "effects.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self._events.append(row)

    def prepare(self, task):
        if self.delegate is not None:
            return self.delegate.prepare(task)
        vector = task.metadata.get("input_vector")
        telemetry = self.telemetry()
        valid = (isinstance(vector, list) and len(vector) == 4 and
                 all(type(x) in {int, float} and math.isfinite(x) and -1 <= x <= 1 for x in vector) and
                 task.metadata.get("input_unit", "relative") == "relative" and
                 telemetry.get("health_status") == "healthy" and
                 telemetry.get("calibration_status") == "valid" and
                 type(telemetry.get("age_of_information_ms")) in {int, float} and
                 math.isfinite(telemetry["age_of_information_ms"]) and 0 <= telemetry["age_of_information_ms"] <= 1000)
        self.cancelled = False
        return AdapterPreparationResult(prepared=valid, details="Frozen E0 vector/state contract" if valid else "E0 input/state contract rejected")

    def execute(self, task):
        attempt = str(uuid4())
        self.done.clear()
        self.append("start", task=task, attempt_id=attempt, inputs=json_safe(task.metadata))
        self.started.set()
        try:
            if self.block and not self.release.wait(15):
                raise RuntimeError("isolated diagnostic wait expired")
            if self.cancelled:
                raise RuntimeError("isolated operation cancelled")
            result = self.delegate.execute(task) if self.delegate is not None else AdapterInvocationResult(
                backend_id=self.backend_id, task_id=task.task_id,
                output_payload={"probabilities": [0.2, 0.3, 0.5], "label_index": 2},
                confidence=0.5, execution_latency_ms=1,
            )
            if self.fault == "wrong_result_task":
                result.task_id = "substituted-task"
            elif self.fault == "wrong_result_backend":
                result.backend_id = "substituted-backend"
            elif self.fault == "nonfinite_result":
                result.output_payload["probabilities"][0] = float("nan")
            elif self.fault == "invalid_probabilities":
                result.output_payload["probabilities"] = [0.8, 0.8, -0.6]
            with self.lock:
                state = json.loads((self.directory / "state.json").read_text(encoding="utf-8"))
                state["commit_count"] += 1
                state["commits"].append({"attempt_id": attempt, "task_id": task.task_id,
                                         "principal_id": task.client_id, "lease_id": task.lease_id})
                write_json(self.directory / "state.json", state)
                self.append("commit", task=task, attempt_id=attempt, commit_index=state["commit_count"])
                write_json(self.directory / f"result-{attempt}.json", json_safe(result.model_dump(mode="json")))
                self.append("result", task=task, attempt_id=attempt, file=f"result-{attempt}.json")
            return result
        finally:
            self.append("finish", task=task, attempt_id=attempt)
            self.done.set()

    def telemetry(self):
        value = self.delegate.telemetry() if self.delegate is not None else {
            "readiness_state": "ready" if self.done.is_set() else "unreachable", "health_status": "healthy",
            "age_of_information_ms": 0.0, "calibration_status": "valid", "drift_score": 0.0,
        }
        return {**value, **self.overrides}

    def abort(self):
        self.append("cancel_requested", confirmed=self.abort_confirmed)
        if not self.abort_confirmed:
            return False
        self.cancelled = True
        self.release.set()
        return self.done.wait(1)

    def reset(self, mode=None):
        return self.delegate.reset(mode) if self.delegate else self.done.is_set()

    def recalibrate(self):
        return self.delegate.recalibrate() if self.delegate else self.done.is_set()


class EffectAdapter(BaseAdapter):
    """Fixture-only strict E0 contract, or an observation wrapper around E1."""
    def __init__(self, directory, *, wrapped=None):
        descriptor = wrapped.describe().model_copy(deep=True) if wrapped else EdgeAdapter._build_descriptor(MOCK_ID)
        descriptor.display_name = "Observed software effect fixture" if not wrapped else descriptor.display_name
        descriptor.policy.exclusive_access_required = True
        runtime = EffectRuntime(directory, descriptor.backend_id, delegate=wrapped.runtime if wrapped else None)
        kind = RuntimeKind(wrapped.capability_declaration.runtime.runtime_kind) if wrapped else RuntimeKind.MOCK
        self.stale_health = False
        self.missing_health = False
        self.unknown_evidence = False
        super().__init__(descriptor, runtime=runtime,
            capability_declaration=make_adapter_capability_declaration(adapter_id=f"r3:{descriptor.backend_id}",
                descriptor=descriptor, runtime=runtime.capabilities,
                evidence_ceiling=EvidenceLevel.E1_SYNTHETIC_TWIN if wrapped else EvidenceLevel.E0_MOCK),
            runtime_kind=kind, telemetry_source=ObservationSource.OBSERVED)

    def resource_contract(self):
        contract = super().resource_contract()
        if self.stale_health:
            old = datetime.now(timezone.utc) - timedelta(seconds=60)
            contract.state.health = contract.state.health.model_copy(update={
                "observed_at": old, "received_at": old, "valid_until": old + timedelta(seconds=1)})
        if self.missing_health:
            contract.state.health = None
        if self.unknown_evidence:
            contract.evidence = contract.evidence.model_copy(update={"runtime_kind": "unknown", "evidence_level": "E0"})
        return contract

    def validate_result(self, task, invocation):
        failures = super().validate_result(task, invocation)
        if self.runtime.delegate is None:
            probabilities = invocation.output_payload.get("probabilities")
            if not (isinstance(probabilities, list) and len(probabilities) == 3 and
                    all(type(x) in {float, int} and math.isfinite(x) and 0 <= x <= 1 for x in probabilities) and
                    abs(sum(probabilities) - 1) <= 1e-9 and
                    invocation.output_payload.get("label_index") == probabilities.index(max(probabilities))):
                failures.append("E0 probability/label contract rejected")
        return failures
