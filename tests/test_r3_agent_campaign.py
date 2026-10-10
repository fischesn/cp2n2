import json
import pytest

from agent.ai_lab_agent import AILabCompletion
from evaluation.r3_agent_campaign import FIXTURE, parse_decision, run_case, verify_case
from scripts.run_r3_agent_campaign import budget_available, configuration_for, input_paths, run_campaign

CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))["cases"]


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
def test_local_reference_pipeline(tmp_path, case):
    report = run_case(tmp_path / case["id"], case)
    assert report["planner_conformant"] and report["reconciled"]
    assert not report["server_enforcement_findings"] and not report["case_forbidden_effect"]
    assert report["permitted_completion"] == report["permitted_opportunity"]
    assert verify_case(tmp_path / case["id"]) == report


class StaticClient:
    model = "test-double-not-llm"
    def __init__(self, payload): self.payload = payload
    def complete(self, *args, **kwargs):
        return AILabCompletion(content=self.payload, requested_model=self.model)


def test_invalid_model_arguments_reach_real_mcp_server(tmp_path):
    case = next(c for c in CASES if c["id"] == "parameter_injection")
    decision = {"disposition":"refuse", "tool":"prepare_assay", "arguments":{
        "resource_id":"r3-effect-mock", "preset_id":"edge_vector_classification_v1", "dry_run":False,
        "amplitude":1000, "runtime_kind":"physical_hardware"}}
    report = run_case(tmp_path / "invalid", case, client=StaticClient(json.dumps(decision)))
    calls = json.loads((tmp_path / "invalid/calls.json").read_text(encoding="utf-8"))["calls"]
    attempted = next(c for c in calls if c["tool"] == "prepare_assay")
    assert attempted["arguments"]["amplitude"] == 1000 and not attempted["response"]["ok"]
    assert report["starts"] == 0 and report["server_rejections"] >= 1 and not report["planner_conformant"]


def test_semantic_misrouting_is_not_hidden_as_server_enforcement_success(tmp_path):
    case = next(c for c in CASES if c["id"] == "physical_request")
    decision = {"disposition":"execute", "tool":"prepare_assay", "arguments":{
        "resource_id":"r3-effect-mock", "preset_id":"edge_vector_classification_v1", "dry_run":False}}
    report = run_case(tmp_path / "misroute", case, client=StaticClient(json.dumps(decision)))
    assert not report["planner_conformant"] and report["case_forbidden_effect"] and report["starts"] == 1
    assert not report["server_enforcement_findings"]  # Valid server request, wrong original user intent.


def test_malformed_reply_retained_without_oracle_repair(tmp_path):
    report = run_case(tmp_path / "malformed", CASES[0], client=StaticClient("not JSON"))
    assert report["format_error"] and not report["planner_conformant"] and report["starts"] == 0
    assert json.loads((tmp_path / "malformed/completion.json").read_text(encoding="utf-8"))["content"] == "not JSON"


def test_parser_preserves_extra_unsafe_fields():
    assert parse_decision('{"disposition":"execute","tool":"raw_stimulate","arguments":{"amplitude":1000}}')["arguments"]["amplitude"] == 1000


def test_provider_failure_retains_denominator_and_request(tmp_path):
    class FailedClient:
        model = "test-double-not-llm"
        def complete(self, *args, **kwargs): raise RuntimeError("sensitive error body must not be recorded")
    report = run_case(tmp_path / "provider-error", CASES[0], client=FailedClient())
    assert report["provider_error"] == "RuntimeError" and not report["planner_conformant"] and report["starts"] == 0
    assert (tmp_path / "provider-error/request.json").is_file()
    assert "sensitive" not in (tmp_path / "provider-error/decision.json").read_text(encoding="utf-8")


def test_unexpected_secret_echo_is_redacted(tmp_path):
    secret = "fake-secret-for-test-only"
    client = StaticClient(json.dumps({"disposition":"clarify", "message": secret}))
    run_case(tmp_path / "redaction", CASES[-1], client=client, secret_values=(secret,))
    completion = json.loads((tmp_path / "redaction/completion.json").read_text(encoding="utf-8"))
    assert secret not in completion["content"] and completion["secret_redaction_count"] == 1


def test_qwen_fixture_keeps_v1_cases_and_oracle_unchanged():
    fixture, _ = input_paths("v2")
    v2 = json.loads(fixture.read_text(encoding="utf-8"))
    assert v2["cases"] == CASES
    assert v2["max_completion_requests"] == 32 and v2["repetitions"] == 2
    assert v2["model"] == "qwen3.8-27b"
    assert v2["provider_parameters"] == {"chat_template_kwargs": {"enable_thinking": False}, "max_tokens": 1024}


def test_qwen_freeze_does_not_inherit_unavailable_environment_model(monkeypatch):
    monkeypatch.setenv("AI_LAB_API_KEY", "fake-test-key")
    monkeypatch.setenv("AI_LAB_MODEL", "minimax-m2.7")
    fixture, _ = input_paths("v2")
    config = configuration_for(json.loads(fixture.read_text(encoding="utf-8")))
    assert config.model == "qwen3.8-27b" and config.enable_thinking is False and config.max_tokens == 1024


@pytest.mark.parametrize("budget", [
    {"spend": 50, "max_budget": 50}, {"unavailable": "error"},
    {"spend": 0, "max_budget": float("inf")}, {"spend": False, "max_budget": 50},
])
def test_campaign_budget_gate_is_fail_closed(budget):
    with pytest.raises(RuntimeError): budget_available(budget)


def test_live_qwen_requires_successful_probe_before_network_or_archive(tmp_path):
    with pytest.raises(RuntimeError, match="retained capability probe"):
        run_campaign(tmp_path / "absent", live=True)
    assert not (tmp_path / "absent").exists()


def test_qwen_settings_are_bound_to_each_concrete_request(tmp_path):
    fixture, _ = input_paths("v2")
    settings = json.loads(fixture.read_text(encoding="utf-8"))
    case = next(c for c in CASES if c["id"] == "dry_run_mock")
    run_case(tmp_path / "request", case, settings=settings)
    request = json.loads((tmp_path / "request/request.json").read_text(encoding="utf-8"))
    assert request["provider_parameters"] == settings["provider_parameters"]
