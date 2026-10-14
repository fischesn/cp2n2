"""AP3 protocol/development checks; not a scored load experiment."""

import json
from pathlib import Path

import pytest

from evaluation import revision_ap3_overhead as ap3


def test_protocol_denominators_and_counterbalanced_orders():
    spec = ap3.specification()
    assert len(spec["groups"]) * len(spec["conditions"]) * spec["repetitions"] * 2 * spec["observations"] == 32000
    assert ap3._condition_order(0) == ["idle_baseline", "bounded_cpu_load"]
    assert ap3._condition_order(1) == ["bounded_cpu_load", "idle_baseline"]
    assert ap3._path_order("execution", 0) == ["direct", "controlled"]
    assert ap3._path_order("discovery", 1) == ["mcp_memory", "direct_surface"]
    with pytest.raises(ValueError, match="confirmatory denominator"):
        ap3.specification(observations=4)
    with pytest.raises(ValueError, match="positive integer"):
        ap3.specification(development=True, observations=True)


def test_cpu_time_scope_and_system_normalization():
    start = {"perf_counter_ns": 0, "system_cpu_seconds": {"user": 2., "system": 1., "idle": 7.},
             "process_cpu_seconds": {"benchmark": {"user": 0., "system": 0.},
                                     "worker-0": {"user": 0., "system": 0.}}}
    end = {"perf_counter_ns": 1_000_000_000, "system_cpu_seconds": {"user": 4., "system": 1., "idle": 9.},
           "process_cpu_seconds": {"benchmark": {"user": 1.2, "system": .2},
                                   "worker-0": {"user": .6, "system": 0.}}}
    result = ap3._cpu_delta(start, end)
    assert result["system_cpu_percent"] == 50
    assert result["processes"]["benchmark"]["cpu_percent_one_core_basis"] == 140
    assert result["processes"]["worker-0"]["cpu_percent_one_core_basis"] == 60
    assert result["processes"]["benchmark"]["cpu_seconds"] == 1.4


@pytest.mark.parametrize("group", ["execution-3", "discovery-3"])
def test_development_trial_cpu_outside_timer_and_raw_binding(tmp_path, group):
    spec = ap3.specification(development=True, observations=3, repetitions=2, warmup=2)
    root = tmp_path / group
    ap3.trial(root, group=group, index=1, condition="idle_baseline", spec=spec)
    row, context = ap3._validate_trial(root, group, 1, "idle_baseline", spec)
    assert context["all_owned_workers_stopped"] and context["owned_worker_pids"] == []
    assert not context["monitor_errors"]
    for block in row["blocks"].values():
        assert all(block["success"]), block["observations"]
        assert len(block["warmup_observations"]) == 2
        assert "benchmark" in block["cpu_observation"]["processes"]
    row["blocks"][row["order"][0]]["observations"][0]["number"] = 900
    ap3.write_json(root / "timings.json", row)
    with pytest.raises(ValueError, match="operation order"):
        ap3._validate_trial(root, group, 1, "idle_baseline", spec)


def test_owned_load_worker_observed_and_cleanup(monkeypatch):
    # Bounded development check only: no gateway timings or scored summary.
    spec = ap3.specification(development=True, observations=2, repetitions=2, warmup=1)
    with ap3.condition_context("bounded_cpu_load", spec) as (workers, context):
        assert len(workers) == 1 and workers[0].is_alive()
        snapshot = ap3._cpu_snapshot(workers)
        assert set(snapshot["process_cpu_seconds"]) == {"benchmark", "worker-0"}
    assert context["all_owned_workers_stopped"]
    assert context["worker_ready"] == [{"pid": context["owned_worker_pids"][0], "ready": True}]
    assert context["cleanup"][0]["forced_stop"] is False
    assert context["cleanup"][0]["exitcode"] == 0
    assert len(context["monitor_snapshots"]) > 1


def test_all_failures_retained_without_retry(tmp_path, monkeypatch):
    spec = ap3.specification(development=True, observations=3, repetitions=2, warmup=2)
    calls = []
    def fail(self, task):
        calls.append(task.task_id)
        raise ValueError("development injected failure")
    monkeypatch.setattr(ap3.TimedEdgeAdapter, "invoke", fail)
    root = tmp_path / "failure"
    ap3.trial(root, group="execution-1", index=0, condition="idle_baseline", spec=spec)
    row, _ = ap3._validate_trial(root, "execution-1", 0, "idle_baseline", spec)
    # Direct path invokes five times; controlled path invokes once and then
    # quarantines that resource. All ten requested observations remain stored;
    # the harness does not retry to turn subsequent rejections into successes.
    assert len(calls) == 6
    assert sum(len(block["observations"]) + len(block["warmup_observations"]) for block in row["blocks"].values()) == 10
    for block in row["blocks"].values():
        assert block["success"] == [False, False, False]
        assert all(r["error"] is not None for r in block["observations"])
        assert len(block["warmup_observations"]) == 2


def test_freeze_source_inventory_and_manifest_tamper_guard(tmp_path, monkeypatch):
    spec = ap3.specification(development=True, observations=2, repetitions=2, warmup=1)
    root = ap3.freeze(tmp_path / "archive", spec)
    hashes = json.loads((root / "source-hashes.json").read_text(encoding="utf-8"))
    assert "evaluation/revision_ap3_overhead.py" in hashes
    assert "scripts/run_revision_ap3_overhead.py" in hashes
    assert "tests/test_revision_ap3_overhead.py" in hashes
    assert "demos/common.py" in hashes
    assert any(name.startswith("twins/") for name in hashes)
    assert any(name.startswith("remote/") for name in hashes)
    assert any(name.startswith("testbed/") for name in hashes)
    import zipfile
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
    report = {"schema": "ap3-overhead-report-v1", "verified": True, "groups": [], "mode": "development",
              "measured_operations": 0, "warmup_operations": 0, "all_operations_succeeded": True}
    # Do not run a timing campaign inside this archive guard unit test.
    monkeypatch.setattr(ap3, "analyse", lambda root, spec: report)
    ap3.finish(root, report)
    assert ap3.verify(root) == report
    (root / "environment.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        ap3.verify(root)


def test_previous_r4_report_is_read_only_and_honest_ci(tmp_path, monkeypatch):
    source = tmp_path / "old"
    source.mkdir()
    for name in ("manifest.json", "verification.json", "freeze.json"):
        (source / name).write_text("{}", encoding="utf-8")
    summary = {"median_trial_median_ms": .2, "median_trial_median_95ci_ms": [.1, .3],
               "median_trial_p95_ms": .7, "median_trial_p95_95ci_ms": [.5, 1.]}
    monkeypatch.setattr("scripts.run_r4_evaluation.verify", lambda _: {
        "kind": "overhead", "verified": True,
        "groups": [{"group": "execution-1", "paths": {"direct": summary}}]})
    before = {path.name: path.read_bytes() for path in source.iterdir()}
    result = ap3.report_r4(source, tmp_path / "new")
    assert result["new_measurements"] is False
    assert result["groups"][0]["paths"]["direct"] == summary
    assert "not population" in result["interval_scope"]
    assert before == {path.name: path.read_bytes() for path in source.iterdir()}
    with pytest.raises(ValueError, match="separate"):
        ap3.report_r4(source, source / "bad")


def test_trial_summary_bootstrap_is_deterministic():
    spec = ap3.specification()
    assert ap3._confidence([.1, .2, .4], spec) == ap3._confidence([.1, .2, .4], spec)
