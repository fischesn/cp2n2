import json
import pytest
from pydantic import ValidationError
from adapters.contracts import AdapterInvocationResult

from evaluation.revision_ap1_evidence import CASES, analyse_case, run_case
from runtimes.biopattern_gate_sdk_runtime import write_json
from evaluation.biopattern_gate_native import file_sha256


@pytest.mark.parametrize("case", CASES)
def test_required_evidence_effect_case(tmp_path, case):
    report = run_case(tmp_path / case, case)
    assert report["verified"], report
    if not report["detector_control"]:
        assert not report["violations"]


def test_cached_publication_is_not_retimestamped(tmp_path):
    assert run_case(tmp_path / "fresh", "fresh_cached_health")["successful_deliveries"] == 1
    assert run_case(tmp_path / "expired", "expired_cached_health")["observed_starts"] == 0


@pytest.mark.parametrize("value", [True, "0.8", float("nan"), float("inf")])
def test_provider_confidence_is_not_coerced(value):
    with pytest.raises(ValidationError):
        AdapterInvocationResult(backend_id="x", task_id="y", confidence=value)


def test_complete_archive_verifies_after_sorted_json_serialization(tmp_path):
    from scripts.run_revision_ap1_evidence import campaign
    from evaluation.revision_ap1_evidence import verify_campaign
    directory = tmp_path / "development-unit-archive"
    report = campaign(directory)
    assert report["verified"]
    assert report["ordinary_trials"] == 46 and report["detector_trials"] == 4
    assert verify_campaign(directory) == report
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest["schema"] = "unknown"
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="schema"):
        verify_campaign(directory)
    manifest["schema"] = "ap1-archive-v1"
    freeze = json.loads((directory / "freeze.json").read_text(encoding="utf-8"))
    freeze["inputs"] = {}
    write_json(directory / "freeze.json", freeze)
    manifest["files"]["freeze.json"] = file_sha256(directory / "freeze.json")
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="input inventory"):
        verify_campaign(directory)


@pytest.mark.parametrize("case", ["bypass_detector", "deny_all_detector"])
def test_detector_cannot_hide_cleanup_failure(tmp_path, case):
    directory = tmp_path / case
    assert run_case(directory, case)["verified"]
    final = json.loads((directory / "final.json").read_text(encoding="utf-8"))
    final["worker_done"] = False
    write_json(directory / "final.json", final)
    assert not analyse_case(directory, case)["verified"]


def test_case_analysis_binds_exact_fault_fixture(tmp_path):
    directory = tmp_path / "drift"
    assert run_case(directory, "drift_string")["verified"]
    fixture = json.loads((directory / "fixture.json").read_text(encoding="utf-8"))
    fixture["overrides"] = {}
    write_json(directory / "fixture.json", fixture)
    report = analyse_case(directory, "drift_string")
    assert not report["verified"] and "fixture_fault_mismatch" in report["violations"]


def test_boolean_fault_is_distinct_from_numeric_one(tmp_path):
    directory = tmp_path / "boolean"
    assert run_case(directory, "drift_bool")["verified"]
    contract = json.loads((directory / "measured-contract.json").read_text(encoding="utf-8"))
    contract["telemetry"]["drift_score"]["value"] = 1
    write_json(directory / "measured-contract.json", contract)
    report = analyse_case(directory, "drift_bool")
    assert not report["verified"] and "measured_fault_mismatch" in report["violations"]
