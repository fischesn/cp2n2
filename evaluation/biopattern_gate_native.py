"""Recompute E3 decisions from native SDK events, not archived features."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from cl import RecordingView

from applications.biopattern_gate.cl_api_port import (
    STREAM_NAMES, technical_e3_runtime_config,
)
from applications.biopattern_gate.cl_recording import reconstruct_cl_recording
from applications.biopattern_gate.control_plane_contract import CONFIG_SHA256, DECODER_SHA256
from applications.biopattern_gate.features import SpikeEvent, extract_features
from applications.biopattern_gate.runner import decision_commit
from applications.biopattern_gate.scheduler import TrialKind, build_trial_schedule
from applications.biopattern_gate.config import BioPatternGateConfig
from applications.biopattern_gate.decoder import load_decoder


APP_ROOT = Path(__file__).resolve().parents[1] / "applications" / "biopattern_gate"
CONFIG_PATH = APP_ROOT / "presets" / "simulator" / "technical-e3.json"
DECODER_PATH = APP_ROOT / "artifacts" / "simulator" / "pattern-gate-linear-v1.json"


def file_sha256(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_native_execution(
    recording_path: Path, result_path: Path, *, expected_run_id: str,
) -> dict:
    """Validate a complete frozen E3 execution and reconstruct its summary.

    Trial markers are part of the native recording. Feature vectors, online
    observation windows and reported decisions are comparison targets only.
    This checks local consistency, not honesty of a compromised SDK/provider.
    """
    config = BioPatternGateConfig.model_validate_json(CONFIG_PATH.read_text(encoding="utf-8"))
    decoder = load_decoder(DECODER_PATH)
    _require(config.sha256() == CONFIG_SHA256, "verifier configuration drift")
    _require(decoder.sha256() == DECODER_SHA256, "verifier decoder drift")
    online = json.loads(result_path.read_text(encoding="utf-8"))
    for key, value in {
        "run_id": expected_run_id, "config_sha256": CONFIG_SHA256,
        "decoder_sha256": DECODER_SHA256, "runtime_kind": "sdk_simulator",
        "evidence_ceiling": "E3", "biological_claim": False,
        "substrate_executed": False, "pnn_evidence": False,
        "cl_api_exercised": True, "attestation": "cl.is_simulator() == true",
    }.items():
        matches = online.get(key) is value if isinstance(value, bool) else online.get(key) == value
        _require(matches, f"online identity/evidence mismatch: {key}")
    _require(online.get("recording_artifact", {}).get("filename") == recording_path.name,
             "online recording filename mismatch")
    evidence = reconstruct_cl_recording(
        recording_path, expected_run_id=expected_run_id,
        expected_runtime_kind="sdk_simulator", expected_stream_names=STREAM_NAMES,
    )
    _require(evidence.terminal_state == "complete", "partial recording is not a complete result")
    _require(evidence.evidence_ceiling == "E3", "recording evidence ceiling mismatch")
    plans = build_trial_schedule(config.schedule)
    indices = list(range(len(plans)))
    trials = online.get("trials", [])
    _require([trial.get("trial_index") for trial in trials] == indices, "online trial set mismatch")
    _require([row.get("trial_index") for row in evidence.feature_records] == indices,
             "recorded feature trial set mismatch")
    _require([row.get("trial_index") for row in evidence.decision_records] == indices,
             "recorded decision trial set mismatch")
    mapping = technical_e3_runtime_config()
    channel_to_group = {
        channel: group for group, channels in mapping.readout_group_map.items() for channel in channels
    }
    scored = correct = shams = used_stims = used_spikes = 0
    reconstructed = []
    with RecordingView(str(recording_path)) as recording:
        attrs = dict(recording.attributes)
        _require(attrs.get("frames_per_second") == 25_000, "unexpected native sample rate")
        _require(attrs.get("channel_count") == 64, "unexpected native channel count")
        _require(attrs.get("application", {}).get("config_sha256") == CONFIG_SHA256,
                 "native configuration hash mismatch")
        _require(attrs.get("file_format", {}).get("stim_and_spike_timestamps_relative_to_start") is True,
                 "unsupported native timestamp convention")
        _require(recording.spikes is not None and recording.stims is not None, "missing native event tables")
        markers = list(recording.data_streams["pattern_gate_trial"].items())
        feature_items = list(recording.data_streams["pattern_gate_features"].items())
        decision_items = list(recording.data_streams["pattern_gate_decision"].items())
        _require([row.get("trial_index") for _, row in markers] == indices, "native trial marker set mismatch")
        marker_times = [int(timestamp) for timestamp, _ in markers]
        _require(all(a < b for a, b in zip(marker_times, marker_times[1:])), "nonmonotonic trial markers")
        stims = [(int(row["timestamp"]), int(row["channel"])) for row in recording.stims]
        spikes = [(int(row["timestamp"]), int(row["channel"])) for row in recording.spikes]
        duration = int(attrs["duration_frames"])
        _require(all(0 <= timestamp < duration and 0 <= channel < 64 for timestamp, channel in stims + spikes),
                 "native event outside recording bounds")
        fps = 25_000
        lead = round(mapping.base_lead_time_us * fps / 1_000_000)
        step = round(config.timing.inter_step_ms * fps / 1000)
        delay = round(config.timing.observation_start_ms * fps / 1000)
        window = round(config.timing.observation_duration_ms * fps / 1000)
        for index, plan in enumerate(plans):
            before, marker = markers[index]
            before = int(before)
            end = marker_times[index + 1] if index + 1 < len(markers) else duration
            _require(marker.get("block_index") == plan.block_index and marker.get("label_hidden") is True,
                     f"invalid native trial marker {index}")
            trial_stims = [(t, ch) for t, ch in stims if before <= t < end]
            is_sham = plan.kind == TrialKind.SHAM
            _require(marker.get("status") == ("sham" if is_sham else "stimulating"),
                     f"native trial kind mismatch {index}")
            if is_sham:
                _require(not trial_stims, f"sham trial {index} contains stimulation")
                last_stim = before + lead + step
                shams += 1
            else:
                sequence = config.pattern_a.sequence if plan.kind == TrialKind.PATTERN_A else config.pattern_b.sequence
                expected_channels = [mapping.input_group_map[group][0] for group in sequence]
                ordered = sorted(trial_stims)
                _require(len(ordered) == 2 and [ch for _, ch in ordered] == expected_channels,
                         f"native stimulation mapping mismatch {index}")
                _require(abs(ordered[0][0] - before - lead) <= 1 and
                         abs(ordered[1][0] - ordered[0][0] - step) <= 1,
                         f"native stimulation timing mismatch {index}")
                last_stim = ordered[-1][0]
            start, stop = last_stim + delay, last_stim + delay + window
            _require(before <= start < stop <= end, f"incomplete native observation window {index}")
            _require(int(feature_items[index][0]) >= stop and
                     int(decision_items[index][0]) >= int(feature_items[index][0]),
                     f"feature/decision recorded before observation completed {index}")
            trial_spikes = [(t, ch) for t, ch in spikes if start <= t < stop]
            _require(all(ch in channel_to_group for _, ch in trial_spikes), f"unknown readout channel {index}")
            events = [SpikeEvent((t - start) * 1000.0 / fps, channel_to_group[ch]) for t, ch in trial_spikes]
            features = extract_features(events, readout_group_refs=config.readout_group_refs,
                                        observation_duration_ms=config.timing.observation_duration_ms,
                                        config=config.features)
            decision = decoder.decide(features)
            commitment = decision_commit(run_id=expected_run_id, trial_index=index,
                                         feature_values=features.values, predicted_label=decision.predicted_label,
                                         route=decision.route)
            trial = trials[index]
            _require(trial.get("feature_values") == features.values and
                     evidence.feature_records[index].get("values") == features.values,
                     f"native spike feature mismatch {index}")
            _require(evidence.feature_records[index].get("schema_version") == features.schema_version,
                     f"recorded feature schema mismatch {index}")
            _require(evidence.decision_records[index].get("linear_score") == decision.linear_score,
                     f"recorded decoder score mismatch {index}")
            expected_decision = {
                "predicted_label": decision.predicted_label, "route": decision.route,
                "probability_a": decision.probability_a, "decision_commit_sha256": commitment,
            }
            for key, value in expected_decision.items():
                _require(trial.get(key) == value and evidence.decision_records[index].get(key) == value,
                         f"native decision mismatch {index}: {key}")
            _require(evidence.decision_records[index].get("label_hidden_at_commit") is True,
                     f"missing blinded commit marker {index}")
            _require(trial.get("expected_label") == plan.hidden_label and trial.get("kind") == plan.kind.value,
                     f"online schedule mismatch {index}")
            relative_start = start + int(attrs["start_timestamp"])
            telemetry = trial.get("telemetry", {})
            _require(telemetry.get("observation_start_timestamp") == relative_start and
                     telemetry.get("observation_stop_timestamp") == relative_start + window,
                     f"online/native observation window mismatch {index}")
            expected_correct = None if is_sham else decision.predicted_label == plan.hidden_label
            _require(trial.get("correct") == expected_correct, f"online correctness mismatch {index}")
            if not is_sham:
                scored += 1
                correct += int(expected_correct)
            used_stims += len(trial_stims)
            used_spikes += len(trial_spikes)
            reconstructed.append({"trial_index": index, **expected_decision})
        _require(used_stims == len(stims), "unassigned native stimulation")
        _require(used_spikes == len(spikes), "unassigned native spike")
    accuracy = correct / scored
    for key, value in {"trial_count": len(plans), "scored_trial_count": scored, "sham_trial_count": shams}.items():
        _require(online.get(key) == value, f"online count mismatch: {key}")
    _require(math.isfinite(online.get("accuracy", math.nan)) and online["accuracy"] == accuracy,
             "online accuracy mismatch")
    return {
        "schema_version": "r2-native-validation-v1", "verified": True,
        "sdk_run_id": expected_run_id, "sdk_run_id_origin": "controller_assigned",
        "runtime_kind": "sdk_simulator", "evidence_level": "E3", "biological_claim": False,
        "terminal_state": "complete", "config_sha256": CONFIG_SHA256, "decoder_sha256": DECODER_SHA256,
        "native_recording_sha256": file_sha256(recording_path), "online_result_sha256": file_sha256(result_path),
        "trial_count": len(plans), "scored_trial_count": scored, "sham_trial_count": shams,
        "stim_count": used_stims, "spike_count": used_spikes, "pipeline_assertion_accuracy": accuracy,
        "reconstructed_decisions": reconstructed,
    }
