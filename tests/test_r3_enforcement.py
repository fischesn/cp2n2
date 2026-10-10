import json

import pytest

from evaluation.r3_enforcement import CASES, run_case
from evaluation.verify_r3_enforcement import verify_case


@pytest.mark.parametrize("case", CASES)
def test_direct_enforcement_case(tmp_path, case):
    report = run_case(tmp_path / case, case)
    assert report["verified"], report
    assert verify_case(tmp_path / case) == report
    if not report["detector_control"]:
        assert not report["violations"]
    else:
        assert report["violations"]


def test_independent_observer_rejects_state_substitution(tmp_path):
    directory = tmp_path / "original"
    run_case(directory, "positive_mock")
    state = json.loads((directory / "backend/state.json").read_text(encoding="utf-8"))
    state["commit_count"] = 0
    from runtimes.biopattern_gate_sdk_runtime import write_json
    from evaluation.biopattern_gate_native import file_sha256
    write_json(directory / "backend/state.json", state)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    manifest["files"]["backend/state.json"] = file_sha256(directory / "backend/state.json")
    write_json(directory / "manifest.json", manifest)
    with pytest.raises(ValueError, match="durable backend state"):
        verify_case(directory)
