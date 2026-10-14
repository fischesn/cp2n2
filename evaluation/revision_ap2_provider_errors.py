"""Prospective separate-process provider-failure trials and offline verifier."""
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from demos.common import make_edge_task
from evaluation.verify_r3_enforcement import effect_observations
from evaluation.artifact_io import write_json
from testbed.deployment import _free_port, _wait_until_ready, ManagedService

ROOT = Path(__file__).resolve().parents[1]
CONDITIONS = ("baseline", "planning_partition", "provider_stop", "invalid_telemetry", "healthy_alternative", "lost_invoke_reply")
PRIMARY, SECONDARY = "remote-edge-backend", "remote-edge-secondary"


def request(base_url, path, payload):
    started = perf_counter_ns()
    try:
        with urlopen(Request(base_url + path, data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}, method="POST"), timeout=20) as response:
            row = {"delivered": True, "http_status": response.status, "result": json.loads(response.read())}
    except HTTPError as exc:
        row = {"delivered": True, "http_status": exc.code, "result": json.loads(exc.read())}
    except (OSError, TimeoutError) as exc:
        row = {"delivered": False, "http_status": None, "error_type": type(exc).__name__}
    return {"path": path, "payload": payload, "wall_ms": (perf_counter_ns() - started) / 1e6, **row}


def trial(directory, condition):
    if condition not in CONDITIONS:
        raise ValueError("Unknown AP2 condition")
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=False)
    services, processes, calls = [], [], []
    def start(name, module, arguments, port=None):
        selected_port = port or _free_port("127.0.0.1")
        logs = root / "logs"
        logs.mkdir(exist_ok=True)
        handle = (logs / f"{name}.log").open("w", encoding="utf-8")
        try:
            process = subprocess.Popen([sys.executable, "-m", module, "--host", "127.0.0.1", "--port", str(selected_port), *arguments],
                cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except BaseException:
            handle.close()
            raise
        service = ManagedService(name, process, f"http://127.0.0.1:{selected_port}", handle)
        services.append(service)
        processes.append({"name": name, "pid": process.pid, "url": service.base_url, "module": module, "arguments": arguments})
        _wait_until_ready(service)
        return service
    def port(service):
        return urlparse(service.base_url).port
    def observe_effects():
        return {name: {key: value for key, value in effect_observations(root / name).items() if key != "results"}
            for name in ("primary", "secondary") if (root / name / "backend" / "state.json").exists()}
    def call(label, path, payload):
        row = {"label": label, **request(control.base_url, path, payload), "effects": observe_effects()}
        calls.append(row)
        return row
    primary_fault, secondary_fault = root / "primary-fault.json", root / "secondary-fault.json"
    rule = root / "proxy-rule.json"
    for path in (primary_fault, secondary_fault, rule):
        write_json(path, {})
    primary_args = ["--directory", str(root / "primary/backend"), "--backend-id", PRIMARY, "--fault-path", str(primary_fault)]
    try:
        primary = start("primary", "evaluation.revision_ap2_services", primary_args)
        proxy = start("proxy", "evaluation.r4_transport_services", ["--mode", "proxy", "--target-port", str(port(primary)),
            "--rule", str(rule), "--events", str(root / "proxy-events.jsonl")])
        control_args = ["--adapter-url", proxy.base_url, "--profile", str(ROOT / "deployments/network-profiles/baseline-v1.json"),
            "--trace-path", str(root / "control-spans.jsonl")]
        if condition in {"healthy_alternative", "lost_invoke_reply"}:
            secondary = start("secondary", "evaluation.revision_ap2_services", ["--directory", str(root / "secondary/backend"),
                "--backend-id", SECONDARY, "--fault-path", str(secondary_fault)])
            control_args += ["--secondary-adapter-url", secondary.base_url]
        control = start("control", "remote.control_plane_service", control_args)
        # All interventions happen after registration and readiness.
        if condition in {"planning_partition", "healthy_alternative"}:
            write_json(rule, {"id": "planning-partition", "path": "/telemetry", "action": "partition"})
        elif condition == "provider_stop":
            primary.stop()
        elif condition == "invalid_telemetry":
            write_json(primary_fault, {"invalid_frame": True})
        elif condition == "lost_invoke_reply":
            write_json(rule, {"id": "lost-invoke", "path": "/invoke", "action": "lost_reply", "once": True})
        task = make_edge_task(task_id="ap2-first")
        task.client_id = "ap2-client"
        task.idempotency_key = "ap2-first-key"
        task.preparation_timeout_ms = 1_000
        task.allow_fallback = True
        task.direct_backend_id = None if condition in {"healthy_alternative", "lost_invoke_reply"} else PRIMARY
        payload = task.model_dump(mode="json")
        call("first", "/execute", {"task": payload})
        call("same_key", "/execute", {"task": payload})
        if condition != "baseline":
            if condition != "lost_invoke_reply":
                call("reconcile_fault_active", "/reconcile", {"resource_id": PRIMARY, "timeout_ms": 1_000})
            if condition == "provider_stop":
                primary = start("primary-recovered", "evaluation.revision_ap2_services", primary_args, port=port(primary))
            write_json(rule, {})
            write_json(primary_fault, {})
            blocked_payload = {**payload, "task_id": "ap2-before-reconcile", "idempotency_key": "ap2-before-key", "direct_backend_id": PRIMARY}
            call("before_reconciliation", "/execute", {"task": blocked_payload})
            call("reconciliation", "/reconcile", {"resource_id": PRIMARY, "timeout_ms": 1_000})
            recovered_payload = {**payload, "task_id": "ap2-after-reconcile", "idempotency_key": "ap2-after-key", "direct_backend_id": PRIMARY}
            call("after_reconciliation", "/execute", {"task": recovered_payload})
            if condition == "lost_invoke_reply":
                call("old_key_after_reconciliation", "/execute", {"task": payload})
        write_json(root / "calls.json", {"condition": condition, "calls": calls})
    finally:
        for service in reversed(services):
            service.stop()
        write_json(root / "processes.json", {"processes": processes,
            "all_stopped": all(service.process.poll() is not None for service in services),
            "scope": "separate processes over actual loopback TCP; single host, no physical substrate"})
    return verify_trial(root)


def verify_trial(directory):
    root = Path(directory)
    data = json.loads((root / "calls.json").read_text(encoding="utf-8"))
    condition = data["condition"]
    calls = {row["label"]: row for row in data["calls"]}
    if len(calls) != len(data["calls"]):
        raise ValueError("Repeated AP2 call label")
    violations = []
    def require(test, name):
        if not test:
            violations.append(name)
    def result(label):
        return calls[label].get("result", {})
    def success(label):
        return bool(result(label).get("success"))
    first = result("first")
    for row in calls.values():
        require(row["delivered"] and row["http_status"] == 200, "structured_http_delivery:" + row["label"])
    effects = {name: effect_observations(root / name) for name in ("primary", "secondary") if (root / name / "backend" / "state.json").exists()}
    primary = effects["primary"]
    secondary = effects.get("secondary", {"starts": [], "commits": [], "active": 0, "overlaps": 0})
    require(not primary["active"] and not primary["overlaps"] and not secondary["active"] and not secondary["overlaps"], "pending_effect_or_overlap")
    require(result("same_key").get("idempotent_replay") is True, "same_key_cached")
    if condition == "baseline":
        require(success("first") and success("same_key"), "baseline_execution")
        expected_primary, expected_secondary = 1, 0
    else:
        require(not success("before_reconciliation"), "automatic_reuse_after_provider_recovery")
        require(success("reconciliation") and result("reconciliation")["final_lifecycle"]["state"] == "ready", "explicit_reconciliation")
        require(success("after_reconciliation"), "recovery_execution")
        if condition == "healthy_alternative":
            require(success("first") and first["decision"]["selected_backend_id"] == SECONDARY, "healthy_secondary_selection")
            error = first["decision"].get("provider_errors", {}).get(PRIMARY, {})
            expected_primary, expected_secondary = 1, 1
        elif condition == "lost_invoke_reply":
            require(not success("first") and first.get("error", {}).get("details", {}).get("execution_status") == "unknown", "unknown_committed_outcome")
            require(first.get("error", {}).get("details", {}).get("automatic_retry") is False, "no_automatic_retry")
            require(result("old_key_after_reconciliation").get("idempotent_replay") and not success("old_key_after_reconciliation"), "uncertain_historical_result_not_rewritten")
            error = None
            expected_primary, expected_secondary = 2, 0
        else:
            require(not success("first") and not success("same_key"), "preinvoke_failure_not_success")
            error = first.get("error", {})
            expected_primary, expected_secondary = 1, 0
        if condition != "lost_invoke_reply":
            require(not success("reconcile_fault_active"), "fault_active_reconciliation")
            require(error.get("code") == "TELEMETRY_STALE", "provider_error_code")
            details = error.get("details", {})
            require(details.get("phase") == "planning" and details.get("execution_status") == "not_started", "preinvoke_error_scope")
            expected_reasons = {"transport", "timeout"} if condition == "provider_stop" else {
                "invalid_telemetry" if condition == "invalid_telemetry" else "transport"}
            require(details.get("provider_failure") in expected_reasons, "provider_error_reason")
    require(len(primary["commits"]) == expected_primary and len(secondary["commits"]) == expected_secondary, "effect_denominator")
    for row in data["calls"]:
        for name, observed in row["effects"].items():
            final = effects[name]
            require(observed["starts"] == final["starts"][:len(observed["starts"])] and observed["commits"] == final["commits"][:len(observed["commits"])], "checkpoint_ledger_prefix:" + row["label"])
    expected_before = 1 if condition == "lost_invoke_reply" else 0
    if condition != "baseline":
        require(len(calls["before_reconciliation"]["effects"]["primary"]["commits"]) == expected_before, "no_primary_effect_before_reconciliation")
    proxy_events = [json.loads(line) for line in (root / "proxy-events.jsonl").read_text(encoding="utf-8").splitlines()]
    if condition in {"planning_partition", "healthy_alternative"}:
        require(any(row["action"] == "partition" and row["forwarded_bytes"] == 0 and row["path"] == "/telemetry" for row in proxy_events), "tcp_partition_evidence")
    if condition == "lost_invoke_reply":
        lost = [row for row in proxy_events if row["action"] == "lost_reply"]
        require(len(lost) == 1 and lost[0]["forwarded_bytes"] > 0 and lost[0]["withheld_response_bytes"] > 0 and lost[0]["path"] == "/invoke", "lost_response_bytes")
    stopped = json.loads((root / "processes.json").read_text(encoding="utf-8"))["all_stopped"]
    require(stopped, "owned_process_cleanup")
    return {"condition": condition, "verified": not violations, "violations": violations,
        "primary_starts": len(primary["starts"]), "primary_commits": len(primary["commits"]),
        "secondary_starts": len(secondary["starts"]), "secondary_commits": len(secondary["commits"]),
        "scope": "new prospective single-host separate-process TCP campaign; not durable restart or physical evidence"}
