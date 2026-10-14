import json

import pytest

from evaluation.r4_selection import cases,oracle,observe,POLICIES,sensitivity_cases
from evaluation.r4_contention import trial,expiry_probe
from evaluation.r4_overhead import execution_trial,mcp_trial,analyse,confidence
from evaluation.r4_transport import trial as transport_trial
from scripts.run_r4_evaluation import specification,freeze,run,verify


def test_selector_specification_and_independent_review():
    spec=specification("selection")
    assert len(spec["cases"])==64
    assert len(spec["manual_review"]["cases"])==12
    assert len({c["family"] for c in cases()})==16
    for c in cases():
        for policy in POLICIES:
            expected=oracle(c,policy)
            for reverse in (False,True):
                observed=observe(c,policy,reverse=reverse)
                if c["id"] == "missing_telemetry-2":
                    # The immutable v1 oracle documents the formerly permissive
                    # required-string-drift rule. AP1 intentionally closes it;
                    # do not rewrite the historical expectation to hide that.
                    assert expected["eligible"] == ["a"]
                    assert observed["eligible"] == []
                    assert "required_telemetry_semantics" in observed["exclusions"]["a"]
                else:
                    for key in ("eligible", "ranking", "selected"):
                        assert expected[key] == observed[key], (c["id"], policy, key)
                    for resource, reasons in expected["exclusions"].items():
                        assert set(reasons) <= set(observed["exclusions"][resource])


def test_active_threshold_priority_and_tie_sensitivity():
    assert len(sensitivity_cases())==19
    for s in sensitivity_cases():
        expected=oracle(s["case"],drift_limit=s["drift_limit"])
        observed=observe(s["case"],drift_limit=s["drift_limit"])
        for key in ("eligible", "ranking", "selected"):
            assert observed[key] == expected[key]
        for resource, reasons in expected["exclusions"].items():
            assert set(reasons) <= set(observed["exclusions"][resource])


def test_selector_archive_and_tamper_detection(tmp_path):
    spec=specification("selection")
    root=freeze(tmp_path/"selection","selection",spec)
    report=run(root,"selection",spec)
    assert verify(root)==report
    # A current run against the unmodified historical oracle must expose the
    # semantic change, rather than falsely claim reproduction of v1 behavior.
    assert report["verified"] is False
    (root/"selection.json").write_text("{}",encoding="utf-8")
    with pytest.raises(ValueError,match="checksum"): verify(root)


@pytest.mark.parametrize("clients",[3,6,12])
def test_multiple_resource_contention(tmp_path,clients):
    report=trial(tmp_path/"trial",clients)
    assert report["verified"],report
    assert all(r["overlaps"]==0 and r["completed"]==1 for r in report["resources"])
    assert report["resources"][2]["declared_exclusive"] is False


def test_idle_expiry_requires_reconciliation(tmp_path):
    assert expiry_probe(tmp_path/"expiry")


def test_overhead_raw_analysis_and_cluster_resampling(tmp_path):
    spec={"groups":["execution-3","discovery-3"],"repetitions":2,"observations":4,"warmup":2,"bootstrap_seed":73401}
    for index in range(2):
        execution_trial(tmp_path/"execution-3"/f"trial-{index:02d}",resources=3,observations=4,warmup=2,index=index)
        mcp_trial(tmp_path/"discovery-3"/f"trial-{index:02d}",observations=4,warmup=2,index=index)
    report=analyse(tmp_path,spec)
    assert report["verified"]
    assert len(report["groups"][0]["paired_trial_median_difference_ms"])==2
    assert confidence([1,2,3])==confidence([1,2,3])
    assert "trial" in report["resampling_unit"]


@pytest.mark.parametrize("condition",["baseline","delay","partition","lost_provider_reply","lost_client_reply","provider_interrupt","controller_restart"])
def test_actual_tcp_transport_and_restart_limit(tmp_path,condition):
    report=transport_trial(tmp_path/condition,condition)
    assert report["expectation_matched"],report
    assert report["all_owned_processes_stopped"]
    if condition=="controller_restart":
        assert report["duplicate_after_restart_observed"]
        assert report["restart_safety_supported"] is False
