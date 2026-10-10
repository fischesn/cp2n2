"""Freeze, run and offline verify one bounded R4 subpackage."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from evaluation.r4_common import freeze,finish,check
from evaluation.r4_selection import cases,sensitivity_cases,oracle,observe,POLICIES
from evaluation import r4_contention,r4_overhead,r4_transport
from runtimes.biopattern_gate_sdk_runtime import write_json


def specification(kind):
    if kind=="selection":
        manual=json.loads((ROOT/"evaluation/fixtures/r4-selection-review-v1.json").read_text(encoding="utf-8"))
        frozen=cases()
        by_id={c["id"]:c for c in frozen}
        for row in manual["cases"]:
            prediction=oracle(by_id[row["id"]])
            if prediction["eligible"]!=row["eligible"] or prediction["selected"]!=row["selected"]:
                raise ValueError("independent manual review and oracle disagree")
        return {"cases":frozen,"manual_review":manual,"policies":list(POLICIES),"orders":[False,True],
            "sensitivity":sensitivity_cases(),"case_count":64,"family_count":16}
    if kind=="contention":
        return {"client_levels":[3,6,12,24],"repetitions":5,"resource_ids":list(r4_contention.RESOURCE_IDS),
            "lease_ttls_ms":list(r4_contention.TTLS),"capacity_per_resource":1,"expiry_wait_ms":100,"expiry_ttl_ms":60}
    if kind=="overhead":
        return {"groups":["execution-1","execution-3","execution-12","discovery-3"],
            "repetitions":10,"observations":200,"warmup":20,"bootstrap_seed":73401,"bootstrap_count":2000,
            "payload":[.1,.3,.5,.7],"closed_loop_outstanding":1}
    if kind=="transport":
        return {"conditions":list(r4_transport.CONDITIONS),"repetitions":3,"delay_ms":50,
            "containers_available":False,"single_host":True,"packet_impairment":False}
    raise ValueError("unknown R4 kind")


def selection_score(root,spec):
    data=json.loads((Path(root)/"selection.json").read_text(encoding="utf-8"))
    by_id={c["id"]:c for c in spec["cases"]}
    if len(by_id)!=64 or len(Counter(c["family"] for c in by_id.values()))!=16:
        raise ValueError("selection denominator changed")
    expected_keys=[(c["id"],p,o) for c in spec["cases"] for p in spec["policies"] for o in spec["orders"]]
    if [(r["case_id"],r["policy"],r["reverse"]) for r in data["observations"]]!=expected_keys:
        raise ValueError("selection coverage/order substitution")
    comparisons=[]
    for policy in spec["policies"]:
        matching=sets=choices=0
        for row in data["observations"]:
            if row["policy"]!=policy: continue
            expected=oracle(by_id[row["case_id"]],policy)
            matching+=all(row["observed"][k]==expected[k] for k in expected)
            sets+=row["observed"]["eligible"]==expected["eligible"]
            choices+=row["observed"]["selected"]==oracle(by_id[row["case_id"]],"lexicographic")["selected"]
        comparisons.append({"policy":policy,"comparisons":len(spec["cases"])*len(spec["orders"]),
            "oracle_conformant":matching,"admissible_set_matches":sets,"principal_choice_agreements":choices})
    expected_sensitivity=[(s["case"]["id"],o) for s in spec["sensitivity"] for o in spec["orders"]]
    if [(r["case_id"],r["reverse"]) for r in data["sensitivity"]]!=expected_sensitivity:
        raise ValueError("sensitivity denominator changed")
    sensitivity=0
    for condition in spec["sensitivity"]:
        expected=oracle(condition["case"],drift_limit=condition["drift_limit"])
        for row in data["sensitivity"]:
            if row["case_id"]==condition["case"]["id"]:
                sensitivity+=all(row["observed"][k]==expected[k] for k in expected)
    principal=[oracle(c,"lexicographic") for c in spec["cases"]]
    return {"verified":all(r["oracle_conformant"]==r["comparisons"] for r in comparisons) and sensitivity==len(expected_sensitivity),
        "cases":64,"families":16,"synthetic":True,"manual_review_cases":len(spec["manual_review"]["cases"]),
        "empty_admissible_sets":sum(not r["eligible"] for r in principal),
        "single_admissible_sets":sum(len(r["eligible"])==1 for r in principal),
        "multiple_admissible_sets":sum(len(r["eligible"])>1 for r in principal),
        "policies":comparisons,"sensitivity_conditions":len(spec["sensitivity"]),"sensitivity_comparisons_matched":sensitivity}


def contention_score(root,spec):
    trials=[r4_contention.verify_trial(Path(root)/f"clients-{clients}/trial-{index:02d}")
            for clients in spec["client_levels"] for index in range(spec["repetitions"])]
    expiry=json.loads((Path(root)/"expiry/expiry.json").read_text(encoding="utf-8"))["rows"]
    expiry_ok=len(expiry)==3 and all(r["lease_expired"] and r["elapsed_ms"]>=spec["expiry_wait_ms"]
        and not r["before_reconciliation"]["success"] and r["reconciliation"]["success"]
        and r["after_reconciliation"]["success"] and r["final_state"]=="ready" for r in expiry)
    return {"verified":all(t["verified"] for t in trials) and expiry_ok,"trials":trials,
        "requests":sum(t["clients"] for t in trials),"completions":sum(r["completed"] for t in trials for r in t["resources"]),
        "rejections":sum(r["rejected"] for t in trials for r in t["resources"]),
        "overlaps":sum(r["overlaps"] for t in trials for r in t["resources"]),"idle_expiry_probes_verified":expiry_ok,
        "scope":"single controller, capacity one, no queue; third nonexclusive descriptor still serialized"}


def transport_score(root,spec):
    rows=[r4_transport.verify_trial(Path(root)/f"{condition}/trial-{index:02d}")
        for condition in spec["conditions"] for index in range(spec["repetitions"])]
    return {"verified":all(r["expectation_matched"] for r in rows),"trials":rows,
        "expectation_matches":sum(r["expectation_matched"] for r in rows),
        "restart_duplicate_effect_trials":sum(r["duplicate_after_restart_observed"] for r in rows),
        "container_host_extension_complete":False,"durable_restart_safety_supported":False}


def score(root,kind,spec):
    methods={"selection":selection_score,"contention":contention_score,"overhead":r4_overhead.analyse,"transport":transport_score}
    return {"kind":kind,**methods[kind](root,spec)}


def plots(root,kind,spec,report):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    if kind=="selection":
        data=json.loads((root/"selection.json").read_text(encoding="utf-8"))
        fig,axes=plt.subplots(2,2,figsize=(7,4),sharex=True,sharey=True)
        for i,name in enumerate(("freshness","latency","cost","drift_threshold")):
            ax=axes.flat[i]
            rows=[r for r in data["sensitivity"] if r["kind"]==name and not r["reverse"]]
            ax.plot([.99,1,1.01],[bool(r["observed"]["eligible"]) for r in rows],
                marker=("o","s","^","D")[i],linestyle=("-","--",":","-.")[i])
            ax.set(title=name.replace("_"," "),yticks=[0,1],ylim=(-.08,1.15),xticks=[.99,1,1.01])
        fig.supxlabel("Bound / declared boundary"); fig.supylabel("Resource admitted")
        fig.tight_layout(); fig.savefig(root/"sensitivity.png",dpi=180); plt.close(fig)
    elif kind=="overhead":
        rows=report["groups"][:3]; fig,ax=plt.subplots(figsize=(6,3))
        for path,marker,style in (("direct","o","--"),("controlled","s","-")):
            centers=[r["paths"][path]["median_trial_median_ms"] for r in rows]
            bounds=[r["paths"][path]["median_trial_median_95ci_ms"] for r in rows]
            ax.errorbar([1,3,12],centers,yerr=[[c-b[0] for c,b in zip(centers,bounds)],[b[1]-c for c,b in zip(centers,bounds)]],
                marker=marker,linestyle=style,label=path,capsize=3)
        ax.set(xlabel="Registered synthetic resources",ylabel="Median wall time (ms)",xticks=[1,3,12])
        ax.legend(); fig.tight_layout(); fig.savefig(root/"overhead.png",dpi=180); plt.close(fig)


def run(root,kind,spec):
    if kind=="selection":
        rows=[{"case_id":c["id"],"policy":policy,"reverse":reverse,"observed":observe(c,policy,reverse=reverse)}
            for c in spec["cases"] for policy in spec["policies"] for reverse in spec["orders"]]
        sensitivity=[{"case_id":s["case"]["id"],"kind":s["kind"],"parameter":s["parameter"],"reverse":reverse,
            "observed":observe(s["case"],drift_limit=s["drift_limit"],reverse=reverse)}
            for s in spec["sensitivity"] for reverse in spec["orders"]]
        write_json(root/"selection.json",{"observations":rows,"sensitivity":sensitivity})
        # A compact case table keeps all principal expectations and reasons searchable.
        lines=["# R4 synthetic selection case table","","| Case | Expected set | Observed set | Expected choice | Observed choice | Exclusions |","| --- | --- | --- | --- | --- | --- |"]
        for c in spec["cases"]:
            e=oracle(c,"lexicographic")
            observed=next(r["observed"] for r in rows if r["case_id"]==c["id"] and r["policy"]=="lexicographic" and not r["reverse"])
            reasons="; ".join(f"{k}: {','.join(v)}" for k,v in e["exclusions"].items() if v)
            lines.append(f"| {c['id']} | {','.join(e['eligible']) or 'none'} | {','.join(observed['eligible']) or 'none'} | {e['selected'] or 'none'} | {observed['selected'] or 'none'} | {reasons} |")
        (root/"case-table.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    elif kind=="contention":
        for clients in spec["client_levels"]:
            for index in range(spec["repetitions"]):
                r4_contention.trial(root/f"clients-{clients}/trial-{index:02d}",clients)
                print(f"contention {clients} clients trial {index+1}/{spec['repetitions']}",flush=True)
        r4_contention.expiry_probe(root/"expiry")
    elif kind=="overhead":
        for group in spec["groups"]:
            for index in range(spec["repetitions"]):
                path=root/group/f"trial-{index:02d}"
                args={"observations":spec["observations"],"warmup":spec["warmup"],"index":index}
                if group.startswith("execution"): r4_overhead.execution_trial(path,resources=int(group.split("-")[1]),**args)
                else: r4_overhead.mcp_trial(path,**args)
                print(f"{group} trial {index+1}/{spec['repetitions']}",flush=True)
    elif kind=="transport":
        for condition in spec["conditions"]:
            for index in range(spec["repetitions"]):
                r4_transport.trial(root/condition/f"trial-{index:02d}",condition)
                print(f"transport {condition} trial {index+1}/{spec['repetitions']}",flush=True)
    report=score(root,kind,spec)
    plots(root,kind,spec,report)
    finish(root,report)
    return report


def verify(root):
    root,spec=check(root)
    kind=json.loads((root/"freeze.json").read_text(encoding="utf-8"))["kind"]
    report=score(root,kind,spec)
    if json.loads((root/"verification.json").read_text(encoding="utf-8"))!=report:
        raise ValueError("stored report differs from raw-artifact recomputation")
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind",choices=("selection","contention","overhead","transport"))
    parser.add_argument("--output",type=Path)
    parser.add_argument("--verify",type=Path)
    args=parser.parse_args()
    if args.verify: report=verify(args.verify)
    else:
        if args.kind is None: parser.error("--kind is required unless verifying")
        spec=specification(args.kind)
        root=freeze(args.output or ROOT/".cp2n2"/f"r4-{args.kind}-{uuid4()}",args.kind,spec)
        run(root,args.kind,spec)
        report=verify(root)
    print(json.dumps(report,indent=2))
    if not report["verified"]: raise SystemExit(1)


if __name__=="__main__": main()
