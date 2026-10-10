"""Offline evidence checks independent of admission and adapter validators."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

from evaluation.biopattern_gate_native import file_sha256
from mcp_surface.audit import JsonlHashChainAuditTrail


def effect_observations(root):
    backend = Path(root) / "backend"
    ledger = backend / "effects.jsonl"
    events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()] if ledger.exists() else []
    previous = "0" * 64
    active, overlaps = set(), 0
    for index, event in enumerate(events, 1):
        payload = {key: value for key, value in event.items() if key != "event_hash"}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if event["sequence"] != index or event["previous_hash"] != previous or event["event_hash"] != digest:
            raise ValueError("backend effect chain mismatch")
        previous = digest
        if event["kind"] == "start":
            overlaps += bool(active)
            active.add(event["attempt_id"])
        if event["kind"] == "finish":
            if event["attempt_id"] not in active:
                raise ValueError("backend finish has no start")
            active.remove(event["attempt_id"])
    state = json.loads((backend / "state.json").read_text(encoding="utf-8"))
    commits = [event for event in events if event["kind"] == "commit"]
    if state["commit_count"] != len(commits) or len(state["commits"]) != len(commits):
        raise ValueError("durable backend state differs from effect log")
    for index, (event, stored) in enumerate(zip(commits, state["commits"]), 1):
        if event["commit_index"] != index or any(event[key] != value for key, value in stored.items()):
            raise ValueError("backend commit identity mismatch")
    starts = [e for e in events if e["kind"] == "start"]
    if any(sum(s["attempt_id"] == c["attempt_id"] for s in starts) != 1 for c in commits):
        raise ValueError("commit has no unique start")
    results = {}
    for event in events:
        if event["kind"] == "result":
            path = (backend / event["file"]).resolve(strict=True)
            if not path.is_relative_to(backend.resolve()): raise ValueError("backend result path escape")
            results[event["task_id"]] = json.loads(path.read_text(encoding="utf-8"))
    return {"starts": starts, "commits": commits, "active": len(active), "overlaps": overlaps, "results": results}


def verify_case(directory):
    root = Path(directory).resolve(strict=True)
    def read(name): return json.loads((root / name).read_text(encoding="utf-8"))
    manifest = read("manifest.json")
    if manifest["schema_version"] != "r3-direct-case-v1": raise ValueError("unknown direct case schema")
    inventory = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                 and p.name not in {"manifest.json", "verification.json"}}
    if inventory != set(manifest["files"]): raise ValueError("direct case inventory mismatch")
    for name, digest in manifest["files"].items():
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or file_sha256(path) != digest: raise ValueError("direct case hash mismatch")
    specification, oracle, final = read("case.json"), read("oracle.json"), read("final.json")
    name = specification["case"]
    if oracle["protocol"] != "r3-direct-v1" or name not in oracle["cases"]: raise ValueError("unknown frozen direct case")
    expected_starts, expected_commits, expected_successes, expected_probe, detector = oracle["cases"][name]
    calls = read("calls.json")["calls"]
    events = JsonlHashChainAuditTrail(root / "audit.jsonl").events()
    if len(events) != 2 * len(calls): raise ValueError("unpaired protocol audit calls")
    for call in calls:
        pair = [e for e in events if e.request_id == call["response"]["request_id"]]
        if (len(pair) != 2 or [e.phase for e in pair] != ["received", "completed"] or
            any(e.tool != call["tool"] or e.principal_id != call["principal_id"] for e in pair) or
            pair[0].argument_digest != call["argument_digest"] or pair[0].arguments != call["arguments"] or
            (pair[1].outcome == "success") != call["response"]["ok"]):
            raise ValueError("protocol/audit request binding mismatch")
    observation = effect_observations(root)
    violations = []
    if len(observation["starts"]) != expected_starts: violations.append("start_count")
    if len(observation["commits"]) != expected_commits: violations.append("commit_count")
    if observation["overlaps"] or observation["active"]: violations.append("exclusive_overlap_or_active_worker")
    records = read("records.json")["records"]
    successes = [c for c in calls if c["tool"] == "run_assay" and c["response"]["ok"] and
                 c["response"]["result"].get("summary", {}).get("success") is True]
    if len(successes) != expected_successes: violations.append("permitted_delivery_count")
    accepted_runs = {c["arguments"]["run_id"] for c in calls if c["tool"] == "run_assay" and c["response"]["ok"]}
    for commit in observation["commits"]:
        record = next((r for r in records if r["task"]["task_id"] == commit["task_id"]), None)
        if (record is None or record["run_id"] not in accepted_runs or record["owner_id"] != commit["principal_id"] or
                record["lease_id"] != commit["lease_id"]): violations.append("unauthorized_commit")
    tasks = [c["task_id"] for c in observation["commits"]]
    if len(tasks) != len(set(tasks)): violations.append("duplicate_commit")
    for call in successes:
        record = next(r for r in records if r["run_id"] == call["arguments"]["run_id"])
        result = observation["results"].get(record["task"]["task_id"])
        if result is None or result["backend_id"] != record["resource_id"] or result["task_id"] != record["task"]["task_id"]:
            violations.append("invalid_success_identity")
        elif specification["runtime_kind"] == "mock":
            if result["output_payload"] != {"probabilities": [0.2, 0.3, 0.5], "label_index": 2}:
                violations.append("invalid_success_payload")
        if call["response"]["result"]["summary"] != record["summary"] or record["state"] != "succeeded":
            violations.append("stored_delivered_result_mismatch")
    probe = specification["probe"]
    if probe not in [call["response"] for call in calls]:
        raise ValueError("probe is not a recorded protocol response")
    actual_probe = "denied" if not probe["ok"] else (
        "dry_run" if probe["result"].get("dry_run") is True else
        "succeeded" if probe["result"].get("summary", {}).get("success") is True else "failed_result")
    if actual_probe != expected_probe: violations.append("probe_outcome")
    if final["lease"] is not None or final["lifecycle"]["state"] != "ready" or not final["worker_done"]:
        raise ValueError("direct case cleanup did not restore known terminal state")
    if name == "unresolved_quarantine":
        quarantine = read("quarantine.json")
        if quarantine["lifecycle"]["state"] != "unreachable" or not quarantine["worker_active"] or quarantine["reuse_response"]["ok"]:
            violations.append("unknown_completion_reused")
    expected_detector = {"faulty_commit_detector": "unauthorized_commit", "deny_all_detector": "permitted_delivery_count"}
    passed = expected_detector[name] in violations if detector else not violations
    return {"case": name, "verified": passed, "detector_control": detector, "violations": violations,
            "observed_starts": len(observation["starts"]), "observed_commits": len(observation["commits"]),
            "successful_deliveries": len(successes), "mcp_calls": len(calls), "audit_events": len(events)}
