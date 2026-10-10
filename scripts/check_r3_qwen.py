"""One bounded transport-capability probe, excluded from R3 outcome denominators."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agent.ai_lab_agent import AILabConfiguration, OpenAICompatibleAILabClient, strip_reasoning_wrapper, completion_has_exposed_reasoning
from evaluation.biopattern_gate_native import file_sha256
from runtimes.biopattern_gate_sdk_runtime import write_json

MODEL = "qwen3.8-27b"


def check(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    config = AILabConfiguration.from_environment().model_copy(update={
        "model": MODEL, "timeout_s": 60, "enable_thinking": False, "max_tokens": 128,
    })
    client = OpenAICompatibleAILabClient(config)
    catalog = client.list_models()
    budget = client.budget_info()
    if MODEL not in catalog:
        raise RuntimeError("Qwen absent from model catalog; no completion sent")
    if isinstance(budget["spend"], (float, int)) and isinstance(budget["max_budget"], (float, int)) and budget["spend"] >= budget["max_budget"]:
        raise RuntimeError("AI-Lab budget exhausted; no completion sent")
    write_json(root / "provider.json", {"model_catalog": catalog, "budget": budget, "base_url": config.base_url})
    messages = [{"role": "system", "content": "Return exactly one JSON object, with no explanation."},
                {"role": "user", "content": 'Return {"status":"ok"}.'}]
    write_json(root / "request.json", {"model": MODEL, "messages": messages, "temperature": 0.0,
        "response_format": {"type": "json_object"}, "chat_template_kwargs": {"enable_thinking": False},
        "max_tokens": 128, "started_at": datetime.now(timezone.utc).isoformat()})
    write_json(root / "request-binding.json", {"request_sha256": file_sha256(root / "request.json")})
    completion = client.complete(messages, temperature=0.0, json_mode=True)
    data = completion.model_dump(mode="json")
    data["content"] = data["content"].replace(config.api_key.get_secret_value(), "[REDACTED_SECRET]")
    write_json(root / "completion.json", data)
    try:
        valid_json = json.loads(strip_reasoning_wrapper(completion.content)) == {"status": "ok"}
    except ValueError:
        valid_json = False
    report = {"model": MODEL, "response_model": completion.response_model, "completion_requests": 1,
        "json_probe_passed": valid_json, "nonthinking_requested": True,
        "exposed_reasoning_observed": completion_has_exposed_reasoning(completion),
        "reasoning_token_count": completion.reasoning_token_count,
        "finish_reason": completion.finish_reason, "usage": completion.usage,
        "internal_reasoning_independently_verified": False,
        "excluded_from_campaign_denominators": True, "pnns_executed": 0,
        "passed": valid_json and not completion_has_exposed_reasoning(completion) and completion.finish_reason != "length"}
    write_json(root / "verification.json", report)
    write_json(root / "manifest.json", {"schema": "r3-qwen-capability-v1",
        "files": {p.name: file_sha256(p) for p in sorted(root.iterdir()) if p.is_file()}})
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cp2n2" / f"r3-qwen-check-{uuid4()}")
    report = check(parser.parse_args().output)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit(1)
