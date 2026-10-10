"""Three-resource, single-controller effect-observed contention, not a scheduler."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json
from pathlib import Path
from threading import Barrier
from time import perf_counter_ns,sleep,monotonic

from adapters.edge_adapter import EdgeAdapter
from core.orchestrator import CP2N2Orchestrator
from demos.common import make_edge_task
from evaluation.r3_effect_backend import EffectAdapter
from evaluation.verify_r3_enforcement import effect_observations
from runtimes.biopattern_gate_sdk_runtime import write_json

RESOURCE_IDS=("r4-resource-a","r4-resource-b","r4-resource-c")
TTLS=(5000,10000,20000)


def setup(root):
    controller=CP2N2Orchestrator(); adapters=[]
    for index,name in enumerate(RESOURCE_IDS):
        adapter=EffectAdapter(Path(root)/name/"backend",wrapped=EdgeAdapter(backend_id=name))
        # Nonexclusive descriptor probe: current controller still uses capacity one.
        adapter.descriptor.policy.exclusive_access_required=index!=2
        controller.register_adapter(adapter); adapters.append(adapter)
        original_append=adapter.runtime.append
        def observed_append(kind, *, _original=original_append, _name=name, **values):
            if kind=="start":
                lease=controller.registry.lease_store.current(_name)
                values["observed_lease"]=lease.model_dump(mode="json") if lease else None
            _original(kind,**values)
        adapter.runtime.append=observed_append
    return controller,adapters


def trial(root, clients):
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    controller,adapters=setup(root)
    for a in adapters: a.runtime.block=True
    barrier=Barrier(clients)
    def submit(index):
        target=index%3
        task=make_edge_task(task_id=f"r4-task-{index}")
        task.client_id=f"client-{index}"; task.idempotency_key=f"request-{index}"
        task.direct_backend_id=RESOURCE_IDS[target]; task.allow_fallback=False; task.lease_ttl_ms=TTLS[target]
        barrier.wait(timeout=10)
        started=perf_counter_ns(); result=controller.execute_task(task)
        return {"client":index,"resource":task.direct_backend_id,"latency_ms":(perf_counter_ns()-started)/1e6,
            "task":task.model_dump(mode="json"),"result":result.model_dump(mode="json")}
    with ThreadPoolExecutor(max_workers=clients) as pool:
        futures=[pool.submit(submit,i) for i in range(clients)]
        try:
            deadline=monotonic()+10
            while sum(f.done() for f in futures)<clients-3 or not all(a.runtime.started.is_set() for a in adapters):
                if monotonic()>deadline: raise RuntimeError("contention gate did not observe three starts and all immediate rejections")
                sleep(0.005)
        finally:
            for a in adapters: a.runtime.release.set()
        rows=[f.result(timeout=10) for f in futures]
    write_json(root/"requests.json",{"clients":clients,"requests":rows})
    write_json(root/"final.json",{"resources":{a.backend_id():{
        "lease":controller.registry.lease_store.current(a.backend_id()),
        "state":controller.registry.lifecycle_store.snapshot(a.backend_id()).state,
        "worker_done":a.runtime.done.is_set(),"declared_exclusive":a.descriptor.policy.exclusive_access_required,
    } for a in adapters}})
    return verify_trial(root)


def verify_trial(root):
    root=Path(root); payload=json.loads((root/"requests.json").read_text(encoding="utf-8"))
    final=json.loads((root/"final.json").read_text(encoding="utf-8"))["resources"]
    details=[]
    for name in RESOURCE_IDS:
        rows=[r for r in payload["requests"] if r["resource"]==name]
        effects=effect_observations(root/name)
        active,overlaps,starts,commits=(effects[k] for k in ("active","overlaps","starts","commits"))
        durable=json.loads((root/name/"backend/state.json").read_text(encoding="utf-8"))
        successful=[r for r in rows if r["result"]["success"]]
        bound=all(e["observed_lease"] is not None and any(
            r["task"]["task_id"]==e["task_id"] and r["task"]["client_id"]==e["principal_id"]
            and r["result"]["lease"]["lease_id"]==e["observed_lease"]["lease_id"]
            and e["principal_id"]==e["observed_lease"]["owner_id"] for r in successful) for e in starts)
        safe=not active and overlaps==0 and len(starts)==len(commits)==durable["commit_count"]==len(successful)==1 and bound
        safe=safe and final[name]["lease"] is None and final[name]["state"]=="ready" and final[name]["worker_done"]
        details.append({"resource":name,"requests":len(rows),"completed":len(successful),
            "rejected":len(rows)-len(successful),"starts":len(starts),"commits":len(commits),"overlaps":overlaps,
            "rejection_codes":[r["result"]["error"]["code"] for r in rows if not r["result"]["success"]],
            "latencies_ms":[r["latency_ms"] for r in rows],"verified":safe,
            "declared_exclusive":final[name]["declared_exclusive"]})
    return {"clients":payload["clients"],"verified":all(r["verified"] for r in details),"resources":details}


def expiry_probe(root):
    root=Path(root); root.mkdir(parents=True,exist_ok=False)
    controller,adapters=setup(root); rows=[]
    for a in adapters:
        first=controller.reserve_backend(a.backend_id(),owner_id="expiry-owner",ttl_ms=60)
        if not first.success: raise RuntimeError("expiry positive acquisition failed")
        began=monotonic(); sleep(0.1)
        expired=controller.registry.lease_store.current(a.backend_id()) is None
        before=controller.reserve_backend(a.backend_id(),owner_id="next-owner",ttl_ms=2000)
        reconciled=controller.reconcile_backend(a.backend_id())
        after=controller.reserve_backend(a.backend_id(),owner_id="next-owner",ttl_ms=2000)
        if after.success: controller.release_lease(a.backend_id(),lease_id=after.lease.lease_id,owner_id="next-owner")
        rows.append({"resource":a.backend_id(),"elapsed_ms":(monotonic()-began)*1000,"first":first.model_dump(mode="json"),
            "lease_expired":expired,"before_reconciliation":before.model_dump(mode="json"),
            "reconciliation":reconciled.model_dump(mode="json"),"after_reconciliation":after.model_dump(mode="json"),
            "final_state":controller.registry.lifecycle_store.snapshot(a.backend_id()).state})
    write_json(root/"expiry.json",{"rows":rows,"scope":"idle resource; not an active-worker expiry/preemption test"})
    return all(r["lease_expired"] and not r["before_reconciliation"]["success"] and r["reconciliation"]["success"]
               and r["after_reconciliation"]["success"] and r["final_state"]=="ready" for r in rows)
