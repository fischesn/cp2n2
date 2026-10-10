"""Freeze, run or offline verify the bounded R3 macro-transition exploration."""
from __future__ import annotations
import argparse
from collections import deque
from datetime import datetime, timezone
from dataclasses import asdict
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_archives import check_audit_calls, verify_files
from evaluation.r3_state_exploration import ALPHABET, State, explore, transition
from evaluation.verify_r3_enforcement import effect_observations
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_r2_sdk_recovery import snapshot_sources


def verify(directory):
    root = Path(directory).resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema_version"] != "r3-state-archive-v1": raise ValueError("unknown exploration archive")
    verify_files(root, manifest["files"])
    report = json.loads((root / "exploration.json").read_text(encoding="utf-8"))
    if report["max_depth"] != 6: raise ValueError("exploration bound differs from protocol")
    design = json.loads((root / "design.json").read_text(encoding="utf-8"))
    for name, digest in design["inputs"].items():
        if file_sha256(root / name) != digest: raise ValueError("frozen exploration input changed")
    queue, witnesses, expected_traces = deque([State()]), {State(): ()}, []
    while queue:
        source = queue.popleft()
        witness = witnesses[source]
        if len(witness) >= 6: continue
        for event in ALPHABET:
            prediction = transition(source, event)
            if prediction is None: continue
            target, _ = prediction
            trace = (*witness, event)
            expected_traces.append(list(trace))
            if target not in witnesses:
                witnesses[target] = trace
                queue.append(target)
    if (expected_traces != [r["trace"] for r in report["transitions_detail"]] or
        report["states"] != len(witnesses) or report["alphabet"] != list(ALPHABET)):
        raise ValueError("exploration alphabet/coverage changed")
    unique_states = {State()}
    matched, audit_count, call_count = 0, 0, 0
    for index, row in enumerate(report["transitions_detail"], 1):
        path = root / f"transition-{index:05d}"
        observed = json.loads((path / "observations.json").read_text(encoding="utf-8"))
        if observed["trace"] != row["trace"] or len(row["trace"]) > 6: raise ValueError("trace substitution")
        expected, ok = State(), True
        for event, observation in zip(row["trace"], observed["observations"], strict=True):
            expected, accepted = transition(expected, event)
            ok = ok and observation["event"] == event and observation["state"] == json.loads(json.dumps(asdict(expected))) and observation["accepted"] == accepted
            unique_states.add(expected)
        backend = effect_observations(path)
        ok = ok and len(backend["starts"]) == expected.starts and len(backend["commits"]) == expected.commits and not backend["overlaps"] and not backend["active"]
        calls, audit = check_audit_calls(path)
        call_count += len(calls)
        audit_count += len(audit)
        final = json.loads((path / "final.json").read_text(encoding="utf-8"))
        if final["lease"] is not None or final["lifecycle"]["state"] != "ready" or not final["worker_done"]: raise ValueError("exploration cleanup unresolved")
        if row["matched"] != ok: raise ValueError("exploration outcome substitution")
        matched += ok
    if len(unique_states) != report["states"] or len(report["transitions_detail"]) != report["transitions"]:
        raise ValueError("exploration denominator mismatch")
    return {"verified": matched == report["transitions"] and not report["mismatches"], "max_depth":6,
        "states": report["states"], "transitions":report["transitions"], "matched_transitions":matched,
        "mcp_surface_calls":call_count, "audit_events":audit_count}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cp2n2" / f"r3-state-{uuid4()}")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.verify: report = verify(args.verify)
    else:
        root = args.output.resolve()
        root.mkdir(parents=True, exist_ok=False)
        snapshot_sources(root)
        (root / "protocol.md").write_bytes((ROOT / "docs/revision/r3-enforcement-protocol.md").read_bytes())
        write_json(root / "design.json", {"started_at":datetime.now(timezone.utc).isoformat(), "max_depth":6,
            "inputs":{n:file_sha256(root / n) for n in ("protocol.md", "source-snapshot.zip")}})
        report = explore(root, max_depth=6, prepared=True)
        write_json(root / "manifest.json", {"schema_version":"r3-state-archive-v1",
            "files": {p.relative_to(root).as_posix():file_sha256(p) for p in sorted(root.rglob("*")) if p.is_file()}})
        report = verify(root)
        write_json(root / "verification.json", report)
    print(json.dumps(report, indent=2))
    if not report["verified"]: raise SystemExit(1)


if __name__ == "__main__": main()
