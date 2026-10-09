"""Run-bound local cancellation and diagnostic checkpoint for SDK E3 only."""

from __future__ import annotations

import json
from pathlib import Path
from time import monotonic, sleep

from .biopattern_gate.cl_api_port import CLApiBioPatternGatePort


class SDKRunCancelled(RuntimeError):
    pass


def write_control_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(".pending")
    temporary.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


class ControlledSDKPort(CLApiBioPatternGatePort):
    """Check cancellation between trials; never change the neural preset."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.control_directory = Path(self.output_directory).parent
        self.control_enabled = (self.control_directory / "launch-authorized.json").is_file()
        self.completed_decisions = 0

    def _cancelled(self) -> bool:
        if not self.control_enabled:
            return False
        path = self.control_directory / "cancel-request.json"
        if not path.exists():
            return False
        request = json.loads(path.read_text(encoding="utf-8"))
        if request.get("sdk_run_id") != self.run_id or request.get("action") != "cancel":
            raise ValueError("cancellation request/run binding mismatch")
        return True

    def observe_trial(self, plan, *, logical_sequence, config):
        if self._cancelled():
            raise SDKRunCancelled("CP2N2 owner requested cancellation")
        diagnostic = self.control_directory / "diagnostic-control.json"
        if self.control_enabled and diagnostic.exists():
            settings = json.loads(diagnostic.read_text(encoding="utf-8"))
            if settings.get("sdk_run_id") != self.run_id:
                raise ValueError("diagnostic checkpoint/run binding mismatch")
            if self.completed_decisions == settings["pause_after_decisions"]:
                write_control_json(self.control_directory / "checkpoint.json", {
                    "sdk_run_id": self.run_id, "completed_decision_count": self.completed_decisions,
                    "status": "paused", "diagnostic_only": True,
                })
                deadline = monotonic() + 30
                while not (self.control_directory / "resume.json").exists():
                    if self._cancelled():
                        raise SDKRunCancelled("CP2N2 owner requested cancellation")
                    if monotonic() >= deadline:
                        raise RuntimeError("diagnostic checkpoint expired")
                    sleep(0.02)
        return super().observe_trial(plan, logical_sequence=logical_sequence, config=config)

    def record_decision(self, plan, *, decision, decision_commit_sha256):
        super().record_decision(plan, decision=decision, decision_commit_sha256=decision_commit_sha256)
        self.completed_decisions += 1
        if self.control_enabled:
            write_control_json(self.control_directory / "progress.json", {
                "sdk_run_id": self.run_id, "completed_decision_count": self.completed_decisions,
            })

    def abort(self, reason: str) -> None:
        # Finalize the native partial file before interrupting pending input.
        self._aborted_reason = reason
        if self._recording is not None:
            self._recording.update_attributes({"terminal_state": "aborted", "abort_reason": reason})
            self._append_stream("pattern_gate_control_status", {
                "lifecycle_state": "aborted", "lease_state": "provider-managed", "reason": reason,
            })
            self._append_stream("pattern_gate_session", {
                "status": "aborted", "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False,
            })
            self._recording.stop()
            path = self._recording.file.get("path")
            if path:
                self.recording_path = Path(path)
            self._recording = None
        super().abort(reason)
