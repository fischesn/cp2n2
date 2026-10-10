"""R3 executing-agent campaign. Default is offline reference, never a network call."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import math
from pathlib import Path
import platform
import sys
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.ai_lab_agent import AILabConfiguration, AILabCompletion, OpenAICompatibleAILabClient, completion_has_exposed_reasoning, strip_reasoning_wrapper
from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_agent_campaign import SYSTEM_PROMPT, run_case, verify_case
from evaluation.r3_archives import source_bindings
from mcp_surface.service import TOOL_SPECS
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_r2_sdk_recovery import snapshot_sources

PROTOCOL = ROOT / "docs/revision/r3-agent-protocol.md"


def input_paths(protocol_version):
    if protocol_version not in {"v1", "v2"}: raise ValueError("unknown agent protocol version")
    return (ROOT / f"evaluation/fixtures/r3-agent-{protocol_version}.json",
            PROTOCOL if protocol_version == "v1" else ROOT / "docs/revision/r3-agent-protocol-v2.md")


def configuration_for(fixture):
    parameters = fixture.get("provider_parameters", {})
    return AILabConfiguration.from_environment().model_copy(update={
        "model": fixture["model"], "timeout_s": fixture["timeout_s"],
        "enable_thinking": parameters.get("chat_template_kwargs", {}).get("enable_thinking"),
        "max_tokens": parameters.get("max_tokens"),
    })


def budget_available(budget):
    spend, maximum = budget.get("spend"), budget.get("max_budget")
    if not isinstance(spend, (int, float)) or not isinstance(maximum, (int, float)) or isinstance(spend, bool) or isinstance(maximum, bool):
        raise RuntimeError("AI-Lab budget unavailable; refusing additional completions")
    if not math.isfinite(spend) or not math.isfinite(maximum) or not 0 <= spend < maximum:
        raise RuntimeError("AI-Lab budget exhausted or invalid; refusing additional completions")


def verify_probe_files(files):
    manifest = json.loads(files["manifest.json"])
    if manifest["schema"] != "r3-qwen-capability-v1" or set(files) != set(manifest["files"]) | {"manifest.json"}:
        raise ValueError("capability probe inventory mismatch")
    for name, digest in manifest["files"].items():
        if hashlib.sha256(files[name]).hexdigest() != digest: raise ValueError("capability probe hash mismatch")
    request, binding = json.loads(files["request.json"]), json.loads(files["request-binding.json"])
    if binding["request_sha256"] != hashlib.sha256(files["request.json"]).hexdigest():
        raise ValueError("capability request binding mismatch")
    if (request["model"] != "qwen3.8-27b" or request["chat_template_kwargs"] != {"enable_thinking": False}
        or request["max_tokens"] != 128 or request["temperature"] != 0 or request["response_format"] != {"type": "json_object"}):
        raise ValueError("capability settings mismatch")
    completion = AILabCompletion.model_validate(json.loads(files["completion.json"]))
    report = json.loads(files["verification.json"])
    if (json.loads(strip_reasoning_wrapper(completion.content)) != {"status": "ok"}
        or completion.requested_model != "qwen3.8-27b" or completion.response_model != "qwen3.8-27b"
        or completion_has_exposed_reasoning(completion) or completion.finish_reason == "length"
        or not report["passed"] or report["completion_requests"] != 1 or not report["excluded_from_campaign_denominators"]):
        raise ValueError("capability probe did not pass")
    return report


def preflight(configuration):
    client = OpenAICompatibleAILabClient(configuration)
    catalog = client.list_models()
    if configuration.model not in catalog: raise RuntimeError("frozen model absent from AI-Lab catalog")
    try: budget = client.budget_info()
    except Exception as exc: budget = {"unavailable": type(exc).__name__}
    return client, {"checked_at": datetime.now(timezone.utc).isoformat(), "model_catalog": catalog,
        "budget": budget, "base_url": configuration.base_url, "requested_model": configuration.model,
        "immutable_weights_verified": False}


def verify_campaign(directory):
    root = Path(directory).resolve(strict=True)
    read = lambda n: json.loads((root / n).read_text(encoding="utf-8"))
    campaign, fixture = read("campaign.json"), read("fixture.json")
    if campaign["protocol"] not in {"r3-agent-v1", "r3-agent-v2"} or fixture["protocol"] != campaign["protocol"]:
        raise ValueError("unknown agent campaign protocol")
    for name, digest in campaign["inputs"].items():
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or file_sha256(path) != digest: raise ValueError("frozen agent input mismatch")
    bindings = source_bindings(root / "source-snapshot.zip")
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        if fixture != json.loads(archive.read(f"evaluation/fixtures/{campaign['protocol']}.json")):
            raise ValueError("agent fixture differs from frozen source")
    if campaign["protocol"] == "r3-agent-v2" and campaign["client_kind"] == "llm":
        with zipfile.ZipFile(root / "capability-probe.zip") as archive:
            verify_probe_files({n: archive.read(n) for n in archive.namelist()})
    if campaign["client_kind"] == "llm" and campaign["requested_model"] != fixture["model"]:
        raise ValueError("campaign model differs from frozen fixture")
    reports, missing = [], []
    for repeat in range(1, fixture["repetitions"] + 1):
        for case in fixture["cases"]:
            path = root / f"repeat-{repeat:02d}" / case["id"]
            if not (path / "manifest.json").exists():
                missing.append({"repeat": repeat, "case": case["id"]})
                continue
            if json.loads((path / "case.json").read_text(encoding="utf-8"))["case"] != case:
                raise ValueError("agent case oracle changed")
            report = verify_case(path, source_bindings=bindings)
            if report["client_kind"] != campaign["client_kind"]: raise ValueError("client kind differs from campaign")
            request = json.loads((path / "request.json").read_text(encoding="utf-8"))
            if (request["requested_model"] != campaign["requested_model"] or request["temperature"] != fixture["temperature"]
                or request["json_mode"] != fixture["json_mode"] or request["messages"][0]["content"] != (root / "system-prompt.txt").read_text(encoding="utf-8")):
                raise ValueError("model/settings/system prompt changed")
            if request.get("provider_parameters", {}) != fixture.get("provider_parameters", {}):
                raise ValueError("provider parameters changed")
            context = json.loads(request["messages"][1]["content"].split("\n", 1)[1])
            if {n:t["input_schema"] for n,t in context["tools"].items()} != read("tool-schemas.json"):
                raise ValueError("model-visible tool schema changed")
            reports.append({"repeat": repeat, **report})
    failures = read("failures.json")["failures"]
    opportunities = sum(c["allowed_effects"] == 1 for c in fixture["cases"]) * fixture["repetitions"]
    return {"protocol": campaign["protocol"], "client_kind": campaign["client_kind"],
        "evidence_verified": not missing and not failures and all(r["evidence_verified"] for r in reports),
        "expected_cases": len(fixture["cases"]) * fixture["repetitions"], "recorded_cases": len(reports),
        "planner_conformant": sum(r["planner_conformant"] for r in reports),
        "permitted_opportunities": opportunities, "permitted_completions": sum(r["permitted_completion"] for r in reports),
        "case_forbidden_effects": sum(r["case_forbidden_effect"] for r in reports),
        "server_enforcement_findings": sum(bool(r["server_enforcement_findings"]) for r in reports),
        "result_integrity_failures": sum(bool(r["result_integrity_findings"]) for r in reports),
        "reconciled_cases": sum(r["reconciled"] for r in reports),
        "execution_attempts": sum(r["execution_attempts"] for r in reports),
        "server_rejections": sum(r["server_rejections"] for r in reports),
        "backend_starts": sum(r["starts"] for r in reports), "mock_commits": sum(r["mock_commits"] for r in reports),
        "sdk_completed": sum(r["sdk_completed"] for r in reports),
        "mcp_calls": sum(r["mcp_calls"] for r in reports), "audit_events": sum(r["audit_events"] for r in reports),
        "provider_errors": sum(bool(r["provider_error"]) for r in reports),
        "exposed_reasoning_cases": sum(r["exposed_reasoning_observed"] for r in reports),
        "format_errors": sum(bool(r["format_error"]) for r in reports), "missing": missing, "failures": failures, "cases": reports}


def run_campaign(directory, *, live=False, protocol_version="v2", capability_probe=None):
    fixture_path, protocol_path = input_paths(protocol_version)
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    if len(fixture["cases"]) * fixture["repetitions"] != fixture["max_completion_requests"]: raise ValueError("request budget mismatch")
    client, credentials = None, ()
    probe_files = None
    if live:
        if protocol_version == "v2":
            if capability_probe is None: raise RuntimeError("live v2 requires a retained capability probe")
            probe_root = Path(capability_probe).resolve(strict=True)
            probe_files = {p.name: p.read_bytes() for p in probe_root.iterdir() if p.is_file()}
            verify_probe_files(probe_files)
        config = configuration_for(fixture)
        client, provider = preflight(config)
        budget_available(provider["budget"])
        credentials = (config.api_key.get_secret_value(),)
    else: provider = {"network_used": False, "immutable_weights_verified": False}
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / "protocol.md").write_bytes(protocol_path.read_bytes())
    (root / "fixture.json").write_bytes(fixture_path.read_bytes())
    if probe_files:
        with zipfile.ZipFile(root / "capability-probe.zip", "x", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, value in sorted(probe_files.items()): archive.writestr(name, value)
    # Generated evidence writes, not source edits.
    (root / "system-prompt.txt").write_text(SYSTEM_PROMPT, encoding="utf-8", newline="\n")
    write_json(root / "tool-schemas.json", {n: s.input_model.model_json_schema() for n, s in TOOL_SPECS.items()})
    write_json(root / "provider.json", provider)
    write_json(root / "environment.json", {"python": sys.version, "platform": platform.platform(),
        "packages": {p: version(p) for p in ("mcp", "pydantic", "cl-sdk", "requests", "tables")}})
    snapshot_sources(root)
    inputs = ("protocol.md", "fixture.json", "system-prompt.txt", "tool-schemas.json", "provider.json", "environment.json", "source-snapshot.zip")
    if probe_files: inputs += ("capability-probe.zip",)
    write_json(root / "campaign.json", {"protocol": fixture["protocol"], "client_kind": "llm" if live else "deterministic_reference",
        "requested_model": client.model if client else "deterministic-reference", "max_completion_requests": fixture["max_completion_requests"],
        "started_at": datetime.now(timezone.utc).isoformat(), "inputs": {n: file_sha256(root / n) for n in inputs}})
    failures, consecutive_errors, budget_checks, stopped = [], 0, [], False
    for repeat in range(1, fixture["repetitions"] + 1):
        for case in fixture["cases"]:
            path = root / f"repeat-{repeat:02d}" / case["id"]
            if client:
                try:
                    budget = client.budget_info()
                    budget_checks.append({"repeat": repeat, "case": case["id"], "checked_at": datetime.now(timezone.utc).isoformat(), "budget": budget})
                    write_json(root / "budget-checks.json", {"checks": budget_checks})
                    budget_available(budget)
                except Exception as exc:
                    failures.append({"repeat": repeat, "case": case["id"], "reason": "budget_gate", "error_type": type(exc).__name__})
                    stopped = True
                    break
            try:
                report = run_case(path, case, client=client, secret_values=credentials, settings=fixture)
                write_json(path / "verification.json", report)
                consecutive_errors = consecutive_errors + 1 if report["provider_error"] else 0
                print(f"{repeat}/{fixture['repetitions']} {case['id']}: planner={report['planner_conformant']} starts={report['starts']} rejected={report['server_rejections']}", flush=True)
            except Exception as exc:
                failure = {"repeat": repeat, "case": case["id"], "error_type": type(exc).__name__}
                failures.append(failure)
                path.mkdir(parents=True, exist_ok=True)
                write_json(path / "harness-failure.json", failure)
                print(f"{repeat}/2 {case['id']}: HARNESS FAILURE (retained)", flush=True)
                # Unknown local execution state must not be followed by more calls.
                write_json(root / "failures.json", {"failures": failures})
                raise RuntimeError("campaign stopped on retained harness failure") from exc
            if report["exposed_reasoning_observed"] and protocol_version == "v2":
                failures.append({"reason": "reasoning_returned_despite_nonthinking_request"})
                stopped = True
                break
            if consecutive_errors >= 3:
                failures.append({"reason": "three_consecutive_provider_errors"})
                stopped = True
                break
        if stopped: break
    write_json(root / "failures.json", {"failures": failures})
    report = verify_campaign(root)
    write_json(root / "verification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cp2n2" / f"r3-agent-{uuid4()}")
    parser.add_argument("--protocol-version", choices=("v1", "v2"), default="v2")
    parser.add_argument("--capability-probe", type=Path, help="Retained successful Qwen capability archive, required for live v2.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true", help="Uses AI-Lab budget; requires University VPN.")
    mode.add_argument("--preflight", action="store_true", help="Read model catalog/budget only; no completion requests.")
    mode.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if args.preflight:
        fixture_path, _ = input_paths(args.protocol_version)
        config = configuration_for(json.loads(fixture_path.read_text(encoding="utf-8"))).model_copy(update={"timeout_s": 30})
        _, report = preflight(config)
    elif args.verify: report = verify_campaign(args.verify)
    else: report = run_campaign(args.output, live=args.live, protocol_version=args.protocol_version, capability_probe=args.capability_probe)
    print(json.dumps({k:v for k,v in report.items() if k != "cases"}, indent=2))
    if report.get("evidence_verified") is False: raise SystemExit(1)


if __name__ == "__main__": main()
