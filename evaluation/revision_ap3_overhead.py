"""AP3 paired, single-host overhead observations with measured CPU context.

This is a new campaign, not a rewrite of the frozen R4 benchmark. Monitoring
runs outside each operation timer and is present under both load conditions.
"""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import platform
from queue import Empty
import subprocess
import sys
from threading import Event, Lock, Thread
from time import monotonic, perf_counter_ns, sleep
import zipfile

import numpy as np
import psutil

from adapters.edge_adapter import EdgeAdapter
from core.orchestrator import CP2N2Orchestrator
from demos.common import make_edge_task
from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_archives import verify_files
from evaluation.r4_overhead import TimedEdgeAdapter
from mcp.shared.memory import create_connected_server_and_client_session
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.auth import Scope
from mcp_surface.models import MCPPrincipal
from mcp_surface.server import create_mcp_server
from mcp_surface.service import MCPControlSurface
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_r2_sdk_recovery import snapshot_sources


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/revision/ap3-overhead-protocol.md"
GROUPS = ("execution-1", "execution-3", "execution-12", "discovery-3")
CONDITIONS = ("idle_baseline", "bounded_cpu_load")


def specification(*, development=False, observations=200, repetitions=10, warmup=20):
    """Confirmatory denominators cannot be silently reduced by CLI flags."""
    if not development and (observations, repetitions, warmup) != (200, 10, 20):
        raise ValueError("confirmatory denominator must be 200/10/20")
    if any(not isinstance(v, int) or isinstance(v, bool) or v <= 0
           for v in (observations, repetitions, warmup)):
        raise ValueError("positive integer timing denominators required")
    return {
        "schema": "ap3-overhead-specification-v1",
        "mode": "development" if development else "confirmatory",
        "groups": list(GROUPS), "conditions": list(CONDITIONS),
        "observations": observations, "repetitions": repetitions, "warmup": warmup,
        "bootstrap_seed": 73401, "bootstrap_count": 2000,
        "closed_loop_outstanding": 1, "payload": [.1, .3, .5, .7],
        "condition_order": "idle/load on even trial; load/idle on odd trial",
        "path_order": "direct/controlled on even trial; controlled/direct on odd trial",
        "load_workers": 1, "load_duty_fraction": .6, "load_period_seconds": .02,
        "load_settle_seconds": .5, "monitor_interval_seconds": .02,
        "worker_ready_timeout_seconds": 20, "worker_stop_timeout_seconds": 3,
        "monitoring": "same asynchronous sampler in both conditions; endpoint reads outside operation timers",
        "environment_scope": "one physical host; synthetic EdgeAdapter and in-memory MCP discovery",
    }


def _condition_order(index):
    return list(CONDITIONS if index % 2 == 0 else reversed(CONDITIONS))


def _path_order(kind, index):
    paths = ["direct", "controlled"] if kind == "execution" else ["direct_surface", "mcp_memory"]
    return paths if index % 2 == 0 else paths[::-1]


def _cpu_load_worker(stop, ready, duty, period):
    """One cooperatively stoppable process; no external commands or descendants."""
    ready.put({"pid": os.getpid(), "ready": True})
    accumulator = 0
    while not stop.is_set():
        began = monotonic()
        busy_until = began + duty * period
        while monotonic() < busy_until and not stop.is_set():
            accumulator = (accumulator * 1664525 + 1013904223) & 0xFFFFFFFF
        stop.wait(max(0., period - (monotonic() - began)))


def _cpu_snapshot(workers):
    now = perf_counter_ns()
    processes = {"benchmark": psutil.Process(os.getpid())}
    processes.update({f"worker-{index}": psutil.Process(worker.pid) for index, worker in enumerate(workers)})
    system = psutil.cpu_times()._asdict()
    return {"perf_counter_ns": now, "system_cpu_seconds": dict(system),
            "process_cpu_seconds": {name: {"user": proc.cpu_times().user,
                                             "system": proc.cpu_times().system}
                                     for name, proc in processes.items()}}


def _cpu_delta(start, end):
    elapsed = (end["perf_counter_ns"] - start["perf_counter_ns"]) / 1e9
    if elapsed <= 0:
        raise ValueError("nonpositive CPU observation interval")
    system = {name: end["system_cpu_seconds"][name] - value
              for name, value in start["system_cpu_seconds"].items()}
    total = sum(value for name, value in system.items() if name not in ("guest", "guest_nice"))
    idle = system.get("idle", 0.) + system.get("iowait", 0.)
    return {"interval_seconds": elapsed,
            "system_cpu_percent": max(0., min(100., 100. * (1. - idle / total))) if total > 0 else None,
            "system_cpu_delta_seconds": system,
            "processes": {name: {
                "cpu_seconds": sum(end["process_cpu_seconds"][name].values()) - sum(values.values()),
                "cpu_percent_one_core_basis": 100. * (sum(end["process_cpu_seconds"][name].values())
                                                     - sum(values.values())) / elapsed,
            } for name, values in start["process_cpu_seconds"].items()}}


class CpuMonitor:
    def __init__(self, workers, interval):
        self.workers, self.interval = workers, interval
        self.stop = Event()
        self.lock = Lock()
        self.snapshots, self.errors = [], []
        self.thread = Thread(target=self._sample, name="ap3-cpu-monitor", daemon=True)

    def _sample(self):
        while not self.stop.is_set():
            try:
                snapshot = _cpu_snapshot(self.workers)
                with self.lock:
                    self.snapshots.append(snapshot)
            except (psutil.Error, OSError) as exc:
                with self.lock:
                    self.errors.append({"type": type(exc).__name__, "message": str(exc)})
            self.stop.wait(self.interval)

    def begin(self):
        self.thread.start()

    def end(self):
        self.stop.set()
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise RuntimeError("owned CPU monitor did not stop")


@contextmanager
def condition_context(condition, spec):
    """Only owned worker objects are stopped; never enumerate/kill system PIDs."""
    if condition not in CONDITIONS:
        raise ValueError("unknown load condition")
    workers = []
    stop = mp.get_context("spawn").Event()
    ready = mp.get_context("spawn").Queue()
    monitor = CpuMonitor(workers, spec["monitor_interval_seconds"])
    result = {"condition": condition, "owned_worker_pids": [], "worker_ready": [],
              "cleanup": [], "all_owned_workers_stopped": False}
    try:
        if condition == "bounded_cpu_load":
            for _ in range(spec["load_workers"]):
                worker = mp.get_context("spawn").Process(
                    target=_cpu_load_worker,
                    args=(stop, ready, spec["load_duty_fraction"], spec["load_period_seconds"]),
                    name="cp2n2-ap3-bounded-load", daemon=True,
                )
                worker.start()
                workers.append(worker)
                result["owned_worker_pids"].append(worker.pid)
                try:
                    signal = ready.get(timeout=spec["worker_ready_timeout_seconds"])
                except Empty as exc:
                    raise RuntimeError("owned load worker failed to signal readiness") from exc
                if signal != {"pid": worker.pid, "ready": True}:
                    raise RuntimeError("load worker readiness binding mismatch")
                result["worker_ready"].append(signal)
        monitor.begin()
        sleep(spec["load_settle_seconds"])
        yield workers, result
    finally:
        # Even a monitor shutdown exception must not skip load-worker cleanup.
        try:
            if monitor.thread.ident is not None:
                monitor.end()
        finally:
            stop.set()
            for worker in workers:
                worker.join(timeout=spec["worker_stop_timeout_seconds"])
                forced = False
                if worker.is_alive():
                    forced = True
                    worker.terminate()
                    worker.join(timeout=spec["worker_stop_timeout_seconds"])
                if worker.is_alive():
                    worker.kill()
                    worker.join(timeout=spec["worker_stop_timeout_seconds"])
                result["cleanup"].append({"pid": worker.pid, "exitcode": worker.exitcode,
                                          "forced_stop": forced, "stopped": not worker.is_alive()})
            result["all_owned_workers_stopped"] = all(not worker.is_alive() for worker in workers)
            result["monitor_snapshots"] = monitor.snapshots
            result["monitor_errors"] = monitor.errors
            result["condition_cpu_observation"] = (_cpu_delta(monitor.snapshots[0], monitor.snapshots[-1])
                                                   if len(monitor.snapshots) > 1 else None)
            result["condition_cpu_observation_scope"] = "whole condition interval, including settle, warmups and measured blocks"
            ready.close()
            ready.join_thread()


def _block(invoke, *, spec, workers):
    """Warmups excluded; exception observations retained with no automatic retry."""
    warmup_rows = [invoke(number, False) for number in range(spec["warmup"])]
    cpu_start = _cpu_snapshot(workers)
    block_started = perf_counter_ns()
    rows = [invoke(number, True) for number in range(spec["observations"])]
    block_wall_ms = (perf_counter_ns() - block_started) / 1e6
    cpu_end = _cpu_snapshot(workers)
    return {"observations": rows, "warmup_observations": warmup_rows,
            "wall_ms": [row["wall_ms"] for row in rows],
            "success": [row["success"] for row in rows],
            "block_wall_ms": block_wall_ms, "cpu_start": cpu_start, "cpu_end": cpu_end,
            "cpu_observation": _cpu_delta(cpu_start, cpu_end)}


def _error(exc):
    return {"type": type(exc).__name__, "message": str(exc)}


def _execution_trial(root, *, resources, index, condition, spec, workers):
    controller = CP2N2Orchestrator()
    controlled, direct = (TimedEdgeAdapter(backend_id="bench-0") for _ in range(2))
    controller.register_adapter(controlled)
    for resource in range(1, resources):
        controller.register_adapter(EdgeAdapter(backend_id=f"bench-{resource}"))
    blocks = {}
    for path in _path_order("execution", index):
        adapter = direct if path == "direct" else controlled

        def invoke(number, measured):
            # Identical reset/recalibration and fixed task setup, outside call timer.
            adapter.reset()
            adapter.recalibrate()
            task = make_edge_task(task_id=f"ap3-{condition}-{index}-{path}-{int(measured)}-{number}")
            task.client_id = "ap3-benchmark"
            task.idempotency_key = task.task_id
            task.direct_backend_id = "bench-0"
            task.allow_fallback = False
            before = len(adapter.invoke_wall_ms)
            began = perf_counter_ns()
            success, latency, error = False, None, None
            try:
                if path == "direct":
                    preparation = adapter.prepare(task)
                    invocation = adapter.invoke(task)
                    adapter.collect_telemetry()
                    success, latency = preparation.prepared, invocation.execution_latency_ms
                    if not success:
                        error = {"type": "direct_preparation_unsuccessful", "message": "direct preparation did not succeed"}
                else:
                    result = controller.execute_task(task)
                    success = result.success
                    latency = result.invocation.execution_latency_ms if result.invocation else None
                    if not success:
                        error = {"type": "controlled_unsuccessful", "message": str(result.failure_reason),
                                 "control_error": result.error.model_dump(mode="json") if result.error else None}
            except Exception as exc:
                error = _error(exc)
            elapsed = (perf_counter_ns() - began) / 1e6
            return {"number": number, "measured": measured, "wall_ms": elapsed,
                    "success": bool(success), "error": error,
                    "invoke_wall_ms": adapter.invoke_wall_ms[-1] if len(adapter.invoke_wall_ms) > before else None,
                    "synthetic_reported_latency_ms": latency}

        blocks[path] = _block(invoke, spec=spec, workers=workers)
    return {"schema": "ap3-overhead-trial-v1", "kind": "execution", "resources": resources,
            "trial": index, "condition": condition, "condition_order": _condition_order(index),
            "order": _path_order("execution", index), "blocks": blocks,
            "observations": spec["observations"], "warmup": spec["warmup"]}


async def _discovery_trial(root, *, index, condition, spec, workers):
    controller = CP2N2Orchestrator()
    for resource in range(3):
        controller.register_adapter(EdgeAdapter(backend_id=f"bench-{resource}"))
    surface = MCPControlSurface(orchestrator=controller,
        principal=MCPPrincipal(principal_id="ap3-benchmark", authenticated=True,
                               scopes=[Scope.RESOURCES_READ.value]),
        audit_trail=JsonlHashChainAuditTrail(root / "audit.jsonl"))
    calls, blocks = [], {}
    async with create_connected_server_and_client_session(create_mcp_server(surface)) as session:
        for path in _path_order("discovery", index):
            async def invoke(number, measured):
                began = perf_counter_ns()
                error, response, success = None, None, False
                try:
                    if path == "direct_surface":
                        response = surface.invoke("discover_resources", {}).model_dump(mode="json")
                    else:
                        response = (await session.call_tool("discover_resources", {})).structuredContent
                    success = bool(response["ok"])
                    if not success:
                        error = {"type": "tool_unsuccessful", "message": "discover_resources returned ok=false"}
                except Exception as exc:
                    error = _error(exc)
                elapsed = (perf_counter_ns() - began) / 1e6
                calls.append({"path": path, "number": number, "measured": measured,
                              "response": response, "error": error})
                return {"number": number, "measured": measured, "wall_ms": elapsed,
                        "success": success, "error": error}

            warmup_rows = [await invoke(number, False) for number in range(spec["warmup"])]
            cpu_start = _cpu_snapshot(workers)
            began = perf_counter_ns()
            rows = [await invoke(number, True) for number in range(spec["observations"])]
            elapsed = (perf_counter_ns() - began) / 1e6
            cpu_end = _cpu_snapshot(workers)
            blocks[path] = {"observations": rows, "warmup_observations": warmup_rows,
                           "wall_ms": [row["wall_ms"] for row in rows],
                           "success": [row["success"] for row in rows], "block_wall_ms": elapsed,
                           "cpu_start": cpu_start, "cpu_end": cpu_end,
                           "cpu_observation": _cpu_delta(cpu_start, cpu_end)}
    write_json(root / "calls.json", {"calls": calls})
    return {"schema": "ap3-overhead-trial-v1", "kind": "discovery", "resources": 3,
            "trial": index, "condition": condition, "condition_order": _condition_order(index),
            "order": _path_order("discovery", index), "blocks": blocks,
            "observations": spec["observations"], "warmup": spec["warmup"]}


def trial(root, *, group, index, condition, spec):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    with condition_context(condition, spec) as (workers, context):
        if group.startswith("execution-"):
            result = _execution_trial(root, resources=int(group.split("-")[1]), index=index,
                                      condition=condition, spec=spec, workers=workers)
        else:
            result = asyncio.run(_discovery_trial(root, index=index, condition=condition,
                                                  spec=spec, workers=workers))
    write_json(root / "timings.json", result)
    write_json(root / "cpu-context.json", context)


def _confidence(values, spec):
    # Resample independent fresh-registry trial summaries, not dependent calls.
    rng = np.random.default_rng(spec["bootstrap_seed"])
    values = np.asarray(values, dtype=float)
    medians = np.median(rng.choice(values, size=(spec["bootstrap_count"], len(values)), replace=True), axis=1)
    return [float(value) for value in np.quantile(medians, [.025, .975])]


def _validate_trial(root, group, index, condition, spec):
    row = json.loads((root / "timings.json").read_text(encoding="utf-8"))
    context = json.loads((root / "cpu-context.json").read_text(encoding="utf-8"))
    kind = "execution" if group.startswith("execution-") else "discovery"
    expected = {"schema": "ap3-overhead-trial-v1", "kind": kind, "trial": index,
                "condition": condition, "resources": int(group.split("-")[1]),
                "observations": spec["observations"], "warmup": spec["warmup"],
                "order": _path_order(kind, index), "condition_order": _condition_order(index)}
    if any(row.get(key) != value for key, value in expected.items()):
        raise ValueError("AP3 trial/configuration/denominator substitution")
    if set(row["blocks"]) != set(expected["order"]):
        raise ValueError("AP3 path inventory substitution")
    if context["condition"] != condition:
        raise ValueError("CPU condition mismatch")
    expected_workers = 0 if condition == "idle_baseline" else spec["load_workers"]
    if len(context["owned_worker_pids"]) != expected_workers or len(context["worker_ready"]) != expected_workers:
        raise ValueError("load-worker denominator mismatch")
    if [r["pid"] for r in context["worker_ready"]] != context["owned_worker_pids"] or not all(r["ready"] for r in context["worker_ready"]):
        raise ValueError("load-worker readiness mismatch")
    if [r["pid"] for r in context["cleanup"]] != context["owned_worker_pids"]:
        raise ValueError("load-worker cleanup binding mismatch")
    if not context["all_owned_workers_stopped"] or not all(r["stopped"] for r in context["cleanup"]):
        raise ValueError("owned worker still running")
    if not context["monitor_snapshots"]:
        raise ValueError("CPU monitoring observations absent")
    expected_cpu = (_cpu_delta(context["monitor_snapshots"][0], context["monitor_snapshots"][-1])
                    if len(context["monitor_snapshots"]) > 1 else None)
    if context["condition_cpu_observation"] != expected_cpu:
        raise ValueError("whole-condition CPU summary mismatch")
    for block in row["blocks"].values():
        if len(block["observations"]) != spec["observations"] or len(block["warmup_observations"]) != spec["warmup"]:
            raise ValueError("timing sample substitution")
        for measured, observations in ((True, block["observations"]), (False, block["warmup_observations"])):
            for number, observation in enumerate(observations):
                if (observation["number"], observation["measured"]) != (number, measured):
                    raise ValueError("operation order/measurement flag changed")
                if not isinstance(observation["success"], bool) or not math.isfinite(observation["wall_ms"]) or observation["wall_ms"] < 0:
                    raise ValueError("invalid raw timing or success flag")
                if not observation["success"] and observation["error"] is None:
                    raise ValueError("failure observation lacks reason")
        if block["wall_ms"] != [r["wall_ms"] for r in block["observations"]] or block["success"] != [r["success"] for r in block["observations"]]:
            raise ValueError("raw operation summary mismatch")
        if not math.isfinite(block["block_wall_ms"]) or block["block_wall_ms"] <= 0:
            raise ValueError("invalid block duration")
        for endpoint in (block["cpu_start"], block["cpu_end"]):
            values = list(endpoint["system_cpu_seconds"].values())
            values.extend(value for process in endpoint["process_cpu_seconds"].values() for value in process.values())
            if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0 for value in values):
                raise ValueError("invalid raw CPU observation")
        if block["cpu_observation"] != _cpu_delta(block["cpu_start"], block["cpu_end"]):
            raise ValueError("CPU summary does not match raw endpoints")
        if set(block["cpu_start"]["process_cpu_seconds"]) != {"benchmark", *(f"worker-{i}" for i in range(expected_workers))}:
            raise ValueError("observed CPU process inventory differs from condition")
    if kind == "discovery":
        calls = json.loads((root / "calls.json").read_text(encoding="utf-8"))["calls"]
        expected_calls = [(path, measured, number) for path in expected["order"]
                          for measured, count in ((False, spec["warmup"]), (True, spec["observations"]))
                          for number in range(count)]
        if [(c["path"], c["measured"], c["number"]) for c in calls] != expected_calls:
            raise ValueError("MCP discovery operation denominator/order mismatch")
        events = JsonlHashChainAuditTrail(root / "audit.jsonl").events()
        ids = []
        for call in calls:
            response = call["response"]
            if response is None:
                continue
            request_id = response["request_id"]
            ids.append(request_id)
            pair = [event for event in events if event.request_id == request_id]
            if len(pair) != 2 or [e.phase for e in pair] != ["received", "completed"] or (pair[-1].outcome == "success") != response["ok"]:
                raise ValueError("discovery response/audit binding mismatch")
            if any(e.tool != "discover_resources" or e.principal_id != "ap3-benchmark" for e in pair):
                raise ValueError("discovery tool/principal mismatch")
            if response["ok"]:
                result = response["result"]
                if len(result["resources"]) != 3:
                    raise ValueError("discovery result resource denominator mismatch")
        if len(ids) != len(set(ids)):
            raise ValueError("discovery request identifier duplicated")
        if all(call["error"] is None for call in calls) and len(events) != 2 * len(calls):
            raise ValueError("discovery audit denominator mismatch")
    return row, context


def analyse(root, spec):
    rows = []
    for group in spec["groups"]:
        for condition in spec["conditions"]:
            trials = [_validate_trial(Path(root) / group / f"trial-{index:02d}" / condition,
                                      group, index, condition, spec)
                      for index in range(spec["repetitions"])]
            paths = _path_order(trials[0][0]["kind"], 0)
            summaries = {}
            for path in paths:
                blocks = [row["blocks"][path] for row, _ in trials]
                medians = [float(np.median(block["wall_ms"])) for block in blocks]
                tails = [float(np.quantile(block["wall_ms"], .95)) for block in blocks]
                summaries[path] = {
                    "trial_medians_ms": medians, "median_trial_median_ms": float(np.median(medians)),
                    "median_trial_median_95ci_ms": _confidence(medians, spec),
                    "trial_p95_ms": tails, "median_trial_p95_ms": float(np.median(tails)),
                    "median_trial_p95_95ci_ms": _confidence(tails, spec),
                    "median_trial_p95_scope": "bootstrap CI for median of trial p95 values, not a population p95/p99 guarantee",
                    "measured_operations": len(blocks) * spec["observations"],
                    "successes": sum(sum(block["success"]) for block in blocks),
                    "warmup_failures": sum(sum(not r["success"] for r in block["warmup_observations"]) for block in blocks),
                    "trial_throughput_ops_s": [spec["observations"] * 1000. / block["block_wall_ms"] for block in blocks],
                    "trial_cpu_observations": [block["cpu_observation"] for block in blocks],
                }
                system_values = [block["cpu_observation"]["system_cpu_percent"] for block in blocks
                                 if block["cpu_observation"]["system_cpu_percent"] is not None]
                summaries[path]["cpu_summary"] = {
                    "median_trial_system_cpu_percent": float(np.median(system_values)) if system_values else None,
                    "system_cpu_available_trials": len(system_values),
                    "median_trial_benchmark_cpu_seconds": float(np.median([
                        block["cpu_observation"]["processes"]["benchmark"]["cpu_seconds"] for block in blocks])),
                    "median_trial_benchmark_cpu_percent_one_core_basis": float(np.median([
                        block["cpu_observation"]["processes"]["benchmark"]["cpu_percent_one_core_basis"] for block in blocks])),
                    "median_trial_load_worker_cpu_percent_one_core_basis": float(np.median([
                        block["cpu_observation"]["processes"]["worker-0"]["cpu_percent_one_core_basis"] for block in blocks]))
                        if condition == "bounded_cpu_load" else None,
                }
                if trials[0][0]["kind"] == "execution":
                    invocation_medians, remainder_medians = [], []
                    for block in blocks:
                        successful = [r for r in block["observations"] if r["success"] and r["invoke_wall_ms"] is not None]
                        if successful:
                            invocation_medians.append(float(np.median([r["invoke_wall_ms"] for r in successful])))
                            remainder_medians.append(float(np.median([r["wall_ms"] - r["invoke_wall_ms"] for r in successful])))
                    summaries[path].update(
                        median_trial_invoke_wall_ms=float(np.median(invocation_medians)) if invocation_medians else None,
                        median_trial_noninvoke_wall_ms=float(np.median(remainder_medians)) if remainder_medians else None,
                        invoke_summary_scope="successful operations only; all failed observations retained in denominators/raw rows")
            differences = [float(np.median(row["blocks"][paths[1]]["wall_ms"]) - np.median(row["blocks"][paths[0]]["wall_ms"]))
                           for row, _ in trials]
            cpu_errors = sum(len(context["monitor_errors"]) for _, context in trials)
            condition_cpu = [context["condition_cpu_observation"] for _, context in trials]
            rows.append({"group": group, "condition": condition, "paths": summaries,
                         "paired_trial_median_difference_ms": differences,
                         "median_paired_difference_ms": float(np.median(differences)),
                         "paired_difference_95ci_ms": _confidence(differences, spec),
                         "monitor_errors": cpu_errors,
                         "trial_condition_cpu_observations": condition_cpu,
                         "condition_cpu_scope": "whole condition interval, including settle, warmups and measured blocks; block CPU observation reported separately",
                         "median_condition_load_worker_cpu_percent_one_core_basis": float(np.median([
                             observation["processes"]["worker-0"]["cpu_percent_one_core_basis"]
                             for observation in condition_cpu if observation is not None]))
                             if condition == "bounded_cpu_load" else None,
                         "forced_worker_stops": sum(sum(c["forced_stop"] for c in context["cleanup"]) for _, context in trials)})
    success = all(path["successes"] == path["measured_operations"] and path["warmup_failures"] == 0
                  for row in rows for path in row["paths"].values())
    cpu_ok = all(row["monitor_errors"] == 0 and row["forced_worker_stops"] == 0 for row in rows)
    return {"schema": "ap3-overhead-report-v1", "verified": success and cpu_ok,
            "artifact_integrity_verified": True, "all_operations_succeeded": success,
            "mode": spec["mode"], "groups": rows,
            "measured_operations": len(rows) * 2 * spec["repetitions"] * spec["observations"],
            "warmup_operations": len(rows) * 2 * spec["repetitions"] * spec["warmup"],
            "fresh_registry_trials": len(rows) * spec["repetitions"],
            "resampling_unit": "fresh-registry trial block; repeated trials on one host, not independent environments",
            "single_environment": True, "physical_execution": False,
            "cpu_observation_scope": "system percentage across logical CPUs; per-process percentage on one-core basis; monitoring outside timed calls",
            "load_scope": "idle_baseline means no intentional load; bounded_cpu_load is one duty-cycled worker, not guaranteed whole-machine load",
            "sampling_scope": "all operation timing observations retained, including failures; no automatic retries or p99 claim"}


def _environment():
    return {"python": sys.version, "platform": platform.platform(), "processor": platform.processor(),
            "logical_cpus": os.cpu_count(), "physical_cores": psutil.cpu_count(logical=False),
            "total_memory_bytes": psutil.virtual_memory().total,
            "timer": "perf_counter_ns", "cpu_monitor": "psutil CPU times; raw endpoints and background samples",
            "packages": {name: version(name) for name in ("psutil", "numpy", "mcp", "pydantic")},
            "base_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)),
            "source_identity": "source-snapshot.zip plus declared per-file hashes; includes new untracked evaluation sources",
            "single_physical_host": True}


def freeze(root, spec):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    write_json(root / "specification.json", spec)
    (root / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    write_json(root / "environment.json", _environment())
    snapshot_sources(root)
    # The generic R2 snapshot predates this harness. Include explicit local
    # runtime/test dependencies too; never append unrelated workspace data.
    extra_files = set()
    for folder in ("demos", "twins", "remote", "testbed"):
        extra_files.update(path for path in (ROOT / folder).rglob("*")
                           if path.is_file() and path.suffix in {".py", ".json"}
                           and "__pycache__" not in path.parts and ".run-output" not in path.parts)
    extra_files.update(path for path in (ROOT / "deployments").rglob("*.json") if path.is_file())
    if (ROOT / "pyproject.toml").is_file():
        extra_files.add(ROOT / "pyproject.toml")
    with zipfile.ZipFile(root / "source-snapshot.zip", "a", zipfile.ZIP_DEFLATED) as archive:
        present = set(archive.namelist())
        for path in sorted(extra_files):
            name = path.relative_to(ROOT).as_posix()
            if name not in present:
                archive.writestr(name, path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n"))
                present.add(name)
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        import hashlib
        write_json(root / "source-hashes.json", {name: hashlib.sha256(archive.read(name)).hexdigest()
                                                 for name in sorted(archive.namelist())})
    names = ("specification.json", "protocol.md", "environment.json", "source-snapshot.zip", "source-hashes.json")
    write_json(root / "freeze.json", {"schema": "ap3-overhead-freeze-v1",
               "frozen_at": datetime.now(timezone.utc).isoformat(),
               "inputs": {name: file_sha256(root / name) for name in names}})
    return root


def finish(root, report):
    write_json(root / "verification.json", report)
    with (root / "raw-timings.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("group", "condition", "trial", "path", "measured",
                                                     "number", "wall_ms", "success", "error_type",
                                                     "invoke_wall_ms", "synthetic_reported_latency_ms"))
        writer.writeheader()
        for timing_file in sorted(root.glob("*/trial-*/*/timings.json")):
            trial_row = json.loads(timing_file.read_text(encoding="utf-8"))
            group = timing_file.parents[2].name
            for path in trial_row["order"]:
                block = trial_row["blocks"][path]
                for observation in block["warmup_observations"] + block["observations"]:
                    writer.writerow({"group": group, "condition": trial_row["condition"], "trial": trial_row["trial"],
                                     "path": path, "measured": observation["measured"], "number": observation["number"],
                                     "wall_ms": observation["wall_ms"], "success": observation["success"],
                                     "error_type": observation["error"]["type"] if observation["error"] else "",
                                     "invoke_wall_ms": observation.get("invoke_wall_ms"),
                                     "synthetic_reported_latency_ms": observation.get("synthetic_reported_latency_ms")})
    lines = ["# AP3 overhead observations", "", "Synthetic execution and in-memory MCP discovery on one physical host.", "",
             "Confidence intervals resample fresh-registry trial summaries. The p95 interval is for the median of trial p95 values; it is not a population tail guarantee.", "",
             "| Group | Condition | Path | Median-of-trial-medians [95% CI], ms | Median-of-trial-p95 [95% CI], ms | Successes / measured |", "| --- | --- | --- | --- | --- | --- |"]
    for row in report["groups"]:
        for path, summary in row["paths"].items():
            median, tail = summary["median_trial_median_ms"], summary["median_trial_p95_ms"]
            ci, tail_ci = summary["median_trial_median_95ci_ms"], summary["median_trial_p95_95ci_ms"]
            lines.append(f"| {row['group']} | {row['condition']} | {path} | {median:.4f} [{ci[0]:.4f}, {ci[1]:.4f}] | {tail:.4f} [{tail_ci[0]:.4f}, {tail_ci[1]:.4f}] | {summary['successes']} / {summary['measured_operations']} |")
    lines.extend(["", "## Observed CPU context", "",
                  "| Group | Condition | Path | Benchmark CPU seconds / block (median) | Benchmark CPU %, one-core basis (median) | System CPU % (median) | Load-worker CPU %, one-core basis (median) |",
                  "| --- | --- | --- | --- | --- | --- | --- |"])
    for row in report["groups"]:
        for path, summary in row["paths"].items():
            cpu = summary["cpu_summary"]
            def display(value):
                return "unavailable / not applicable" if value is None else f"{value:.4f}"
            lines.append(f"| {row['group']} | {row['condition']} | {path} | {display(cpu['median_trial_benchmark_cpu_seconds'])} | {display(cpu['median_trial_benchmark_cpu_percent_one_core_basis'])} | {display(cpu['median_trial_system_cpu_percent'])} | {display(cpu['median_trial_load_worker_cpu_percent_one_core_basis'])} |")
    lines.extend(["", "Condition-level worker utilization (one-core basis, including settle/warmups/measurements):"])
    for row in report["groups"]:
        if row["condition"] == "bounded_cpu_load":
            lines.append(f"- {row['group']}: {row['median_condition_load_worker_cpu_percent_one_core_basis']:.4f}% median across trials.")
    lines.extend(["", "Per-block process CPU time and actual system/worker utilization are retained in verification.json and raw trial CPU endpoints. Idle baseline does not assert an otherwise idle host.",
                  "", f"Mode: {report['mode']}. Measured operations: {report['measured_operations']}; warmups: {report['warmup_operations']}.",
                  f"All operations succeeded: {report['all_operations_succeeded']}. Overall verified: {report['verified']}.", ""])
    (root / "report.md").write_text("\n".join(lines), encoding="utf-8")
    write_json(root / "manifest.json", {"schema": "ap3-overhead-archive-v1",
              "files": {p.relative_to(root).as_posix(): file_sha256(p) for p in sorted(root.rglob("*"))
                        if p.is_file() and p.name != "manifest.json"}})


def verify(root):
    root = Path(root).resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"] != "ap3-overhead-archive-v1":
        raise ValueError("unknown AP3 archive schema")
    verify_files(root, manifest["files"], excluded=("manifest.json",))
    frozen = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    names = {"specification.json", "protocol.md", "environment.json", "source-snapshot.zip", "source-hashes.json"}
    if frozen["schema"] != "ap3-overhead-freeze-v1" or set(frozen["inputs"]) != names:
        raise ValueError("AP3 frozen inventory/schema mismatch")
    for name, digest in frozen["inputs"].items():
        if file_sha256(root / name) != digest:
            raise ValueError("frozen AP3 input mismatch")
    spec = json.loads((root / "specification.json").read_text(encoding="utf-8"))
    if spec != specification(development=spec["mode"] == "development", observations=spec["observations"],
                              repetitions=spec["repetitions"], warmup=spec["warmup"]):
        raise ValueError("AP3 specification differs from declared protocol")
    import hashlib
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        expected = {name: hashlib.sha256(archive.read(name)).hexdigest() for name in sorted(archive.namelist())}
    if json.loads((root / "source-hashes.json").read_text(encoding="utf-8")) != expected:
        raise ValueError("source file hashes mismatch")
    report = analyse(root, spec)
    if report != json.loads((root / "verification.json").read_text(encoding="utf-8")):
        raise ValueError("stored AP3 report differs from raw recomputation")
    return report


def run(root, spec):
    for group in spec["groups"]:
        for index in range(spec["repetitions"]):
            for condition in _condition_order(index):
                trial(root / group / f"trial-{index:02d}" / condition,
                      group=group, index=index, condition=condition, spec=spec)
                print(f"AP3 {group} trial {index + 1}/{spec['repetitions']} {condition}", flush=True)
    report = analyse(root, spec)
    finish(root, report)
    return verify(root)


def report_r4(source, output):
    """Read/verify old receipt and raw artifacts; never write inside source."""
    source, output = Path(source).resolve(strict=True), Path(output).resolve()
    if output == source or output.is_relative_to(source):
        raise ValueError("offline report output must be separate from immutable R4 archive")
    from scripts.run_r4_evaluation import verify as verify_r4
    report = verify_r4(source)
    if report["kind"] != "overhead":
        raise ValueError("previous archive is not R4 overhead")
    output.mkdir(parents=True, exist_ok=False)
    rows = [{"group": row["group"], "paths": {
        path: {key: summary[key] for key in ("median_trial_median_ms", "median_trial_median_95ci_ms",
                                             "median_trial_p95_ms", "median_trial_p95_95ci_ms")}
        for path, summary in row["paths"].items()}} for row in report["groups"]]
    receipt = {"schema": "ap3-r4-offline-report-v1", "source_verified": report["verified"],
               "source_manifest_sha256": file_sha256(source / "manifest.json"),
               "source_verification_sha256": file_sha256(source / "verification.json"),
               "source_freeze_sha256": file_sha256(source / "freeze.json"),
               "new_measurements": False, "groups": rows,
               "interval_scope": "bootstrap CI for median of fresh-trial p95 values; not population tail guarantee",
               "historical_source_bytes_changed": False}
    write_json(output / "previous-r4-summary.json", receipt)
    lines = ["# Previously archived R4 intervals (offline report)", "", receipt["interval_scope"], "",
             "No new measurements; source archive verified before reading. Source files were not changed.", "",
             "| Group | Path | Median [95% CI], ms | Median-of-trial-p95 [95% CI], ms |", "| --- | --- | --- | --- |"]
    for row in rows:
        for path, summary in row["paths"].items():
            ci, tail_ci = summary["median_trial_median_95ci_ms"], summary["median_trial_p95_95ci_ms"]
            lines.append(f"| {row['group']} | {path} | {summary['median_trial_median_ms']:.4f} [{ci[0]:.4f}, {ci[1]:.4f}] | {summary['median_trial_p95_ms']:.4f} [{tail_ci[0]:.4f}, {tail_ci[1]:.4f}] |")
    (output / "previous-r4-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return receipt
