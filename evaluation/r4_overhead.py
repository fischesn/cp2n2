"""Paired single-environment timings, with independent fresh-registry trial blocks."""
import asyncio
import json
from pathlib import Path
from time import perf_counter_ns

import numpy as np

from adapters.edge_adapter import EdgeAdapter
from core.orchestrator import CP2N2Orchestrator
from demos.common import make_edge_task
from mcp.shared.memory import create_connected_server_and_client_session
from mcp_surface.audit import JsonlHashChainAuditTrail
from mcp_surface.auth import Scope
from mcp_surface.models import MCPPrincipal
from mcp_surface.server import create_mcp_server
from mcp_surface.service import MCPControlSurface
from runtimes.biopattern_gate_sdk_runtime import write_json


class TimedEdgeAdapter(EdgeAdapter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.invoke_wall_ms=[]

    def invoke(self, task):
        began=perf_counter_ns()
        result=super().invoke(task)
        self.invoke_wall_ms.append((perf_counter_ns()-began)/1e6)
        return result


def execution_trial(root, *, resources, observations, warmup, index):
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    controller=CP2N2Orchestrator()
    controlled=TimedEdgeAdapter(backend_id="bench-0")
    direct=TimedEdgeAdapter(backend_id="bench-0")
    controller.register_adapter(controlled)
    for i in range(1,resources):
        controller.register_adapter(EdgeAdapter(backend_id=f"bench-{i}"))
    order=["direct","controlled"] if index%2==0 else ["controlled","direct"]
    blocks={}
    for path in order:
        adapter=direct if path=="direct" else controlled
        timings=[]; invocations=[]; success=[]; reported=[]
        block_started=None
        for number in range(warmup+observations):
            # Both paths receive the same payload and reset policy; housekeeping
            # is outside the per-operation timer but inside block throughput.
            adapter.reset(); adapter.recalibrate()
            task=make_edge_task(task_id=f"bench-{index}-{path}-{number}")
            task.client_id="r4-benchmark"; task.idempotency_key=task.task_id
            task.direct_backend_id="bench-0"; task.allow_fallback=False
            if number==warmup: block_started=perf_counter_ns()
            began=perf_counter_ns()
            if path=="direct":
                preparation=adapter.prepare(task); result=adapter.invoke(task)
                adapter.collect_telemetry()
                ok=preparation.prepared; latency=result.execution_latency_ms
            else:
                result=controller.execute_task(task)
                ok=result.success
                latency=result.invocation.execution_latency_ms if result.invocation else None
            elapsed=(perf_counter_ns()-began)/1e6
            if number>=warmup:
                timings.append(elapsed); invocations.append(adapter.invoke_wall_ms[-1] if ok else None)
                success.append(ok); reported.append(latency)
        blocks[path]={"wall_ms":timings,"invoke_wall_ms":invocations,"success":success,
            "synthetic_reported_latency_ms":reported,
            "block_wall_ms":(perf_counter_ns()-block_started)/1e6}
    write_json(root/"timings.json",{"kind":"execution","trial":index,"resources":resources,
        "observations":observations,"warmup":warmup,"order":order,"blocks":blocks})


async def _mcp_trial(root, *, observations, warmup, index):
    controller=CP2N2Orchestrator()
    for i in range(3): controller.register_adapter(EdgeAdapter(backend_id=f"bench-{i}"))
    audit=JsonlHashChainAuditTrail(root/"audit.jsonl")
    surface=MCPControlSurface(orchestrator=controller,
        principal=MCPPrincipal(principal_id="r4-benchmark",authenticated=True,scopes=[Scope.RESOURCES_READ.value]),
        audit_trail=audit)
    order=["direct_surface","mcp_memory"] if index%2==0 else ["mcp_memory","direct_surface"]
    blocks={}; calls=[]
    async with create_connected_server_and_client_session(create_mcp_server(surface)) as session:
        for path in order:
            timings=[]; success=[]; block_started=None
            for number in range(warmup+observations):
                if number==warmup: block_started=perf_counter_ns()
                began=perf_counter_ns()
                if path=="direct_surface":
                    response=surface.invoke("discover_resources",{}).model_dump(mode="json")
                else:
                    response=(await session.call_tool("discover_resources",{})).structuredContent
                elapsed=(perf_counter_ns()-began)/1e6
                calls.append({"path":path,"measured":number>=warmup,"response":response})
                if number>=warmup: timings.append(elapsed); success.append(response["ok"])
            blocks[path]={"wall_ms":timings,"success":success,"block_wall_ms":(perf_counter_ns()-block_started)/1e6}
    write_json(root/"calls.json",{"calls":calls})
    write_json(root/"timings.json",{"kind":"discovery","trial":index,"resources":3,
        "observations":observations,"warmup":warmup,"order":order,"blocks":blocks})


def mcp_trial(root, **kwargs):
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    asyncio.run(_mcp_trial(root,**kwargs))


def confidence(values, *, seed=73401, bootstrap=2000):
    """Resample trial summaries, never the dependent calls within one trial."""
    values=np.asarray(values,dtype=float)
    rng=np.random.default_rng(seed)
    medians=np.median(rng.choice(values,size=(bootstrap,len(values)),replace=True),axis=1)
    return [float(v) for v in np.quantile(medians,[0.025,0.975])]


def analyse(root, specification):
    rows=[]
    for group in specification["groups"]:
        trials=[]
        for index in range(specification["repetitions"]):
            path=Path(root)/group/ f"trial-{index:02d}"
            row=json.loads((path/"timings.json").read_text(encoding="utf-8"))
            expected_kind="discovery" if group.startswith("discovery") else "execution"
            if row["trial"]!=index or row["kind"]!=expected_kind or row["resources"]!=int(group.split("-")[1]):
                raise ValueError("timing trial/configuration substitution")
            if row["observations"]!=specification["observations"] or row["warmup"]!=specification["warmup"]:
                raise ValueError("timing denominator differs from frozen specification")
            expected_order=(["direct_surface","mcp_memory"] if row["kind"]=="discovery" else ["direct","controlled"])
            if index%2: expected_order=list(reversed(expected_order))
            if row["order"]!=expected_order: raise ValueError("paired timing order changed")
            for block in row["blocks"].values():
                if len(block["wall_ms"])!=specification["observations"] or len(block["success"])!=specification["observations"]:
                    raise ValueError("timing sample substitution")
                if any(not np.isfinite(v) or v<0 for v in block["wall_ms"]): raise ValueError("invalid raw timing")
            if row["kind"]=="discovery":
                calls=json.loads((path/"calls.json").read_text(encoding="utf-8"))["calls"]
                events=JsonlHashChainAuditTrail(path/"audit.jsonl").events()
                count=2*(specification["warmup"]+specification["observations"])
                if len(calls)!=count or len(events)!=2*count: raise ValueError("discovery audit denominator")
                for call in calls:
                    pair=[e for e in events if e.request_id==call["response"]["request_id"]]
                    if len(pair)!=2 or [e.phase for e in pair]!=["received","completed"] or pair[-1].outcome!="success":
                        raise ValueError("discovery audit binding")
            trials.append(row)
        paths=list(trials[0]["blocks"])
        # Fixed display order independent of the alternating collection order.
        paths=(["direct_surface","mcp_memory"] if trials[0]["kind"]=="discovery" else ["direct","controlled"])
        summary={}
        for path in paths:
            medians=[float(np.median(t["blocks"][path]["wall_ms"])) for t in trials]
            tails=[float(np.quantile(t["blocks"][path]["wall_ms"],.95)) for t in trials]
            summary[path]={"trial_medians_ms":medians,"median_trial_median_ms":float(np.median(medians)),
                "trial_p95_ms":tails,"median_trial_p95_ms":float(np.median(tails)),
                "trial_median_iqr_ms":[float(v) for v in np.quantile(medians,[.25,.75])],
                "median_trial_median_95ci_ms":confidence(medians,seed=specification["bootstrap_seed"]),
                "median_trial_p95_95ci_ms":confidence(tails,seed=specification["bootstrap_seed"]),
                "trial_throughput_ops_s":[specification["observations"]*1000/t["blocks"][path]["block_wall_ms"] for t in trials],
                "successes":sum(sum(t["blocks"][path]["success"]) for t in trials)}
            if trials[0]["kind"]=="execution":
                invocations=[]; remainder=[]
                for t in trials:
                    block=t["blocks"][path]
                    if len(block["invoke_wall_ms"])!=specification["observations"]: raise ValueError("invoke timing sample substitution")
                    pairs=[(wall,invoke) for wall,invoke,ok in zip(block["wall_ms"],block["invoke_wall_ms"],block["success"],strict=True) if ok and invoke is not None]
                    if pairs:
                        invocations.append(float(np.median([i for _,i in pairs])))
                        remainder.append(float(np.median([w-i for w,i in pairs])))
                summary[path].update(median_trial_invoke_wall_ms=float(np.median(invocations)) if invocations else None,
                    median_trial_noninvoke_wall_ms=float(np.median(remainder)) if remainder else None,
                    invoke_summary_scope="successful operations only; all failures retained in successes/raw blocks")
        differences=[float(np.median(t["blocks"][paths[1]]["wall_ms"])-np.median(t["blocks"][paths[0]]["wall_ms"])) for t in trials]
        rows.append({"group":group,"paths":summary,"paired_trial_median_difference_ms":differences,
            "median_paired_difference_ms":float(np.median(differences)),
            "paired_difference_95ci_ms":confidence(differences,seed=specification["bootstrap_seed"]),
            "verified":all(all(b["success"]) for t in trials for b in t["blocks"].values())})
    return {"verified":all(r["verified"] for r in rows),"groups":rows,
        "measured_operations":len(specification["groups"])*2*specification["repetitions"]*specification["observations"],
        "warmup_operations":len(specification["groups"])*2*specification["repetitions"]*specification["warmup"],
        "resampling_unit":"fresh-registry trial block; ten repeated trials on one machine, not ten environments",
        "load":"one synchronous outstanding request; housekeeping included only in block throughput",
        "single_environment":True,"physical_execution":False}
