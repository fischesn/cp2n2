"""Specification-derived synthetic cases and an oracle independent of BackendMatcher."""
from copy import deepcopy
import hashlib


POLICIES = ("lexicographic", "latency_first", "locality_cost_first", "static_priority", "random_admissible")


def resource(identifier="a", **changes):
    return {"id": identifier, "latency": 5.0, "drift": 0.1, "age": 10.0,
        "health": "healthy", "lifecycle": "ready", "reservable": True,
        "cost": 0.5, "currency": "eur", "locality": "edge", "stochastic": False,
        "stateful": True, "age_supported": True, "supervision_required": False,
        "contract_admissible": True, "modalities": ["digital_vector"], **changes}


def cases():
    """16 authored families x four variants; not an independently sampled workload."""
    rows = []
    def add(family, variant, resources, **task):
        rows.append({"id": f"{family}-{variant}", "family": family, "synthetic": True,
            "task": {"latency_budget": 20.0, "max_age": 1000.0, "max_cost": None,
                     "required_telemetry": [], "supervision": False, "locality": "edge",
                     "stochasticity_tolerance": 0.5, "reset_free": False,
                     "policy": "lexicographic", "seed": 41, **task}, "resources": resources})
    for i in range(4):
        add("singleton", i, [resource(latency=1+i)])
        add("empty_inventory", i, [], latency_budget=10+i)
        add("latency_boundary", i, [resource(latency=10)], latency_budget=[9.999,10,10.001,5][i])
        add("drift_boundary", i, [resource(drift=[0.949,0.95,0.951,0.0][i])])
        add("freshness_boundary", i, [resource(age=[999,1000,1001,None][i])])
        add("cost_boundary", i, [resource(cost=[0.999,1,1.001,None][i])], max_cost=1)
        add("missing_telemetry", i, [resource(drift=[None,"MISSING","unknown",0.0][i])], required_telemetry=["drift_score"])
        add("lifecycle", i, [resource(latency=5+i,lifecycle=["failed","unreachable","aborting","ready"][i])])
        add("competing_lease", i, [resource(latency=5+i,reservable=i%2 == 1), resource("b", latency=10, reservable=False)])
        add("conflicting_constraints", i, [resource(drift=0.99,latency=1), resource("b",latency=30)], latency_budget=10+i)
        identifiers = [("a","b"),("b","a"),("z","x"),("x","z")][i]
        add("identifier_tie", i, [resource(identifier=n) for n in identifiers])
        add("policy_tradeoff", i, [resource("a",latency=2,drift=0.4,locality="cloud"),
            resource("b",latency=10,drift=0.05)], policy=["lexicographic","latency_first","locality_cost_first","static_priority"][i])
        add("supervision", i, [resource(cost=0.1+i*0.1,supervision_required=True), resource("b",latency=15)], supervision=i%2 == 1)
        add("freshness_capability", i, [resource(age=10+i,age_supported=i%2 == 1)])
        add("quality_reset", i, [resource(latency=10,stateful=False), resource("b",latency=2,stochastic=True)],
            stochasticity_tolerance=[0.1,0.5,0.1,0.5][i], reset_free=i>=2)
        add("contract_modality", i, [resource(contract_admissible=i!=0,
            modalities=["spikes"] if i==1 else ["digital_vector"], health="offline" if i==2 else "healthy")])
    assert len(rows) == 64
    return rows


def exclusions(case, r, *, drift_limit=0.95):
    """Written from the declared inequalities; no production matcher imports/calls."""
    t, reasons = case["task"], []
    if "digital_vector" not in r["modalities"]: reasons.append("input_modality_compatible")
    if t["max_age"] is not None and not r["age_supported"]: reasons.append("freshness_observable")
    if r["supervision_required"] and not t["supervision"]: reasons.append("human_supervision_policy")
    if not r["contract_admissible"]: reasons.append("resource_contract_safety")
    if reasons: return reasons
    if r["health"] in ("offline","failed","unreachable"): reasons.append("runtime_available")
    if r["lifecycle"] in ("failed","unreachable","aborting"): reasons.append("lifecycle_available")
    if not r["reservable"]: reasons.append("resource_reservable")
    if "drift_score" in t["required_telemetry"] and r["drift"] in (None,"MISSING"):
        reasons.append("required_telemetry_available")
    if r["latency"] > t["latency_budget"]: reasons.append("latency_budget")
    if isinstance(r["drift"], (float,int)) and r["drift"] >= drift_limit: reasons.append("drift_threshold")
    if t["max_age"] is not None and (r["age"] is None or r["age"] > t["max_age"]): reasons.append("telemetry_freshness")
    if t["max_cost"] is not None and (r["cost"] is None or r["currency"] != "eur" or r["cost"] > t["max_cost"]):
        reasons.append("cost_budget")
    return sorted(reasons)


def key(case, r, policy):
    t = case["task"]
    safety = [0 if r["health"] in ("healthy","ready") else 1 if r["health"]=="degraded" else 2,
              0, r["drift"] if isinstance(r["drift"],(float,int)) else 1,
              r["age"]/t["max_age"] if r["age"] is not None and t["max_age"] else 0 if r["age"] is not None else 1]
    quality = [int(t["stochasticity_tolerance"] < 0.25 and r["stochastic"]), int(t["reset_free"] and r["stateful"])]
    latency = [r["latency"]/t["latency_budget"]]
    locality = [0 if t["locality"] is None or r["locality"] == t["locality"] else 6,
                int(r["cost"] is None), r["cost"] if r["cost"] is not None else 0]
    if policy == "static_priority": return (0 if r["id"]=="b" else 1 if r["id"]=="a" else 2, r["id"])
    if policy == "random_admissible":
        return (hashlib.sha256(f"{t['seed']}:{case['id']}:{r['id']}".encode()).hexdigest(),r["id"])
    groups = {"lexicographic": safety+quality+latency+locality,
              "latency_first": latency+safety+locality+quality,
              "locality_cost_first": locality+safety+latency+quality}
    return (*groups[policy],r["id"])


def oracle(case, policy=None, *, drift_limit=0.95):
    eligible = [r for r in case["resources"] if not exclusions(case,r,drift_limit=drift_limit)]
    ranked = sorted(eligible,key=lambda r:key(case,r,policy or case["task"]["policy"]))
    return {"eligible": sorted(r["id"] for r in eligible), "ranking": [r["id"] for r in ranked],
            "selected": ranked[0]["id"] if ranked else None,
            "exclusions": {r["id"]:exclusions(case,r,drift_limit=drift_limit) for r in case["resources"]}}


def production_inputs(case):
    """Bridge flat, published test data into production types; not the oracle."""
    from adapters.edge_adapter import EdgeAdapter
    from demos.common import make_edge_task
    t = case["task"]
    task = make_edge_task(task_id=case["id"])
    task.latency_budget_ms, task.max_twin_age_ms = t["latency_budget"], t["max_age"]
    task.max_estimated_cost, task.cost_currency = t["max_cost"], "eur" if t["max_cost"] is not None else None
    task.required_telemetry_fields, task.human_supervision_available = t["required_telemetry"], t["supervision"]
    task.preferred_locality, task.stochasticity_tolerance, task.reset_free_preferred = t["locality"], t["stochasticity_tolerance"], t["reset_free"]
    task.selection_policy, task.selection_seed = t["policy"], t["seed"]
    descriptors, runtime = [], {}
    for r in case["resources"]:
        descriptor = EdgeAdapter(backend_id=r["id"]).describe().model_copy(deep=True)
        descriptor.timing.typical_latency_ms = r["latency"]
        descriptor.telemetry.supports_age_of_information = r["age_supported"]
        descriptor.policy.locality, descriptor.policy.human_supervision_required = r["locality"], r["supervision_required"]
        descriptor.capability.stochastic, descriptor.lifecycle.stateful = r["stochastic"], r["stateful"]
        for contract in descriptor.input_contracts: contract.modality = r["modalities"][0]
        descriptors.append(descriptor)
        runtime[r["id"]] = {"health_status":r["health"], "control_plane_lifecycle":r["lifecycle"],
            "reservable":r["reservable"], "age_of_information_ms":r["age"], "estimated_cost":r["cost"],
            "cost_currency":r["currency"], "contract_safety_admissible":r["contract_admissible"]}
        if r["drift"] != "MISSING": runtime[r["id"]]["drift_score"] = r["drift"]
    return task, descriptors, runtime


def observe(case, policy=None, *, drift_limit=0.95, reverse=False):
    from core.matcher import BackendMatcher
    task, descriptors, runtime = production_inputs(case)
    matcher = BackendMatcher(static_priority=["b","a"])
    matcher.DRIFT_INADMISSIBLE_THRESHOLD = drift_limit  # isolated test instance only
    report = matcher.rank_backends(task,list(reversed(descriptors)) if reverse else descriptors,
                                  runtime_state=runtime,policy=policy or case["task"]["policy"])
    selected = report.best_candidate()
    return {"eligible":sorted(c.backend_id for c in report.accepted_candidates()),
        "ranking":[c.backend_id for c in report.accepted_candidates()],
        "selected":selected.backend_id if selected else None,
        "exclusions":{c.backend_id:sorted(v.split(":",1)[0] for v in (c.admission.violations if not c.admission.passed else c.feasibility.violations)) for c in report.candidates},
        "report":report.model_dump(mode="json")}


def sensitivity_cases():
    """Changes to active hard boundaries and priority/tie rules, not unused weights."""
    rows = []
    base = {"id":"sensitivity", "family":"sensitivity", "synthetic":True,
            "task":cases()[0]["task"], "resources":[resource(age=1000,latency=10,cost=1,drift=0.949)]}
    for factor in (0.99,1.0,1.01):
        for name,field,center in (("freshness","max_age",1000),("latency","latency_budget",10),("cost","max_cost",1)):
            case=deepcopy(base); case["id"]=f"{name}-{factor}"; case["task"][field]=center*factor
            rows.append({"kind":name,"parameter":center*factor,"case":case,"drift_limit":0.95})
        case=deepcopy(base); case["id"]=f"drift-{factor}"; case["resources"][0]["drift"]=0.95
        rows.append({"kind":"drift_threshold","parameter":0.95*factor,"case":case,"drift_limit":0.95*factor})
    tradeoff=next(c for c in cases() if c["id"]=="policy_tradeoff-0")
    for policy in ("lexicographic","latency_first","locality_cost_first"):
        case=deepcopy(tradeoff); case["task"]["policy"]=policy; case["id"]=f"priority-{policy}"
        rows.append({"kind":"priority_order","parameter":policy,"case":case,"drift_limit":0.95})
    for i in range(4):
        case=next(c for c in cases() if c["id"]==f"identifier_tie-{i}")
        rows.append({"kind":"identifier_tie","parameter":i,"case":case,"drift_limit":0.95})
    return rows
