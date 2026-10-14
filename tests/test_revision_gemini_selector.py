"""Fabricated report tests only; never observe the external Gemini cases."""
from copy import deepcopy
import hashlib
import json
import zipfile

import pytest

from evaluation import revision_gemini_selector as campaign


def _resource(identifier):
    return {"id": identifier, "latency": 10.0, "drift": .1, "age": 5.0, "health": "healthy",
        "lifecycle": "ready", "reservable": True, "cost": .5, "currency": "eur", "locality": "edge",
        "stochastic": False, "stateful": False, "age_supported": True,
        "supervision_required": False, "contract_admissible": True, "modalities": ["digital_vector"]}


def _case(identifier="fabricated-01"):
    # Entirely fabricated data; not any externally authored case or outcome.
    return {"id": identifier, "scenario": "Fabricated structural verifier fixture",
        "task": {"latency_budget": 20.0, "max_age": 100.0, "max_cost": 1.0,
            "required_telemetry": ["drift_score"], "supervision": False, "locality": "edge",
            "stochasticity_tolerance": .5, "reset_free": False},
        "resources": [_resource("a"), _resource("b"), _resource("c")],
        "expected": {"admissible_resource_ids": ["a", "b", "c"], "rejections": {},
            "rankings": {policy: ["a", "b", "c"] for policy in campaign.POLICIES},
            "selected": {policy: "a" for policy in campaign.POLICIES},
            "reasoning_by_policy": {policy: "Fabricated tie by identifier" for policy in campaign.POLICIES}},
        "test_purpose": "Unit-level parser and report validation"}


def _dataset():
    return {"schema_version": campaign.SCHEMA,
        "cases": [_case(f"fabricated-{index:02}") for index in range(1, 13)],
        "coverage_summary": ["Fabricated verifier fixtures"], "specification_questions": []}


def _candidate(identifier, rank=None, *, stage=None, violations=()):
    admission = {"stage": "admission", "passed": stage != "admission", "violations": list(violations) if stage == "admission" else []}
    feasibility = {"stage": "feasibility", "passed": stage is None,
        "violations": (["Feasibility was not evaluated because admission failed."] if stage == "admission"
            else list(violations) if stage == "feasibility" else [])}
    return {"backend_id": identifier, "accepted": stage is None, "admission": admission,
        "feasibility": feasibility, "ranking": {"rank": rank}}


def _serialized(case, policy, reverse=False):
    task = case["task"]
    saved_task = {"task_id": case["id"], "task_kind": "classification",
        "required_input_modalities": ["digital_vector"], "direct_backend_id": None,
        "continuous_monitoring_required": False, "repeated_invocation_expected": False,
        "min_confidence": .2, "selection_seed": 41, "selection_policy": policy,
        "latency_budget_ms": task["latency_budget"], "max_twin_age_ms": task["max_age"],
        "max_estimated_cost": task["max_cost"], "cost_currency": "eur" if task["max_cost"] is not None else None,
        "required_telemetry_fields": task["required_telemetry"], "human_supervision_available": task["supervision"],
        "preferred_locality": task["locality"], "stochasticity_tolerance": task["stochasticity_tolerance"],
        "reset_free_preferred": task["reset_free"]}
    descriptors, runtime = [], {}
    for resource in case["resources"]:
        descriptors.append({"backend_id": resource["id"], "capability": {"supported_task_types": ["classification"],
            "health_sensitive": False, "resettable": True, "stochastic": resource["stochastic"]},
            "telemetry": {"supports_health_status": True, "supports_confidence": True,
                "supports_drift_reporting": True, "metrics": [{"name": "drift_score"}],
                "supports_age_of_information": resource["age_supported"]},
            "lifecycle": {"supported_reset_modes": ["soft_reset"], "stateful": resource["stateful"]},
            "policy": {"locality": resource["locality"], "human_supervision_required": resource["supervision_required"]},
            "timing": {"typical_latency_ms": resource["latency"]},
            "input_contracts": [{"modality": resource["modalities"][0]}]})
        runtime[resource["id"]] = {"health_status": resource["health"], "control_plane_lifecycle": resource["lifecycle"],
            "reservable": resource["reservable"], "age_of_information_ms": resource["age"],
            "estimated_cost": resource["cost"], "cost_currency": resource["currency"],
            "contract_safety_admissible": resource["contract_admissible"], "drift_score": resource["drift"]}
    if reverse:
        descriptors.reverse()
    return {"task": saved_task, "descriptors": descriptors, "runtime": runtime}


def _output(case, policy, order):
    return {"schema": "gemini-selector-observation-v1", "case_id": case["id"], "policy": policy,
        "input_order": order, "bridge_input": campaign.production_case(case),
        "production_inputs": _serialized(case, policy, order == "reversed"), "error": None,
        "raw_report": {"task_id": case["id"], "policy": policy, "provider_errors": {},
            "candidates": [_candidate(identifier, rank) for rank, identifier in enumerate(["a", "b", "c"], 1)]}}


def _outputs(dataset):
    return [_output(case, policy, order) for case in dataset["cases"]
        for policy in campaign.POLICIES for order in campaign.ORDERS]


def test_fabricated_dataset_isolated_copy_and_input_only_bridge():
    dataset = _dataset()
    validated = campaign.validate_dataset(dataset)
    validated["cases"][0]["task"]["latency_budget"] = 50.0
    assert dataset["cases"][0]["task"]["latency_budget"] == 20.0
    bridge = campaign.production_case(dataset["cases"][0])
    assert set(bridge) == {"id", "task", "resources"}
    assert bridge["task"]["policy"] == "lexicographic" and bridge["task"]["seed"] == 41
    bridge["resources"][0]["health"] = "offline"
    assert dataset["cases"][0]["resources"][0]["health"] == "healthy"


@pytest.mark.parametrize("field,value", [("latency_budget", True), ("latency_budget", "20"),
    ("latency_budget", 0), ("latency_budget", float("nan")), ("max_age", float("inf")),
    ("max_cost", -1), ("stochasticity_tolerance", 1.01), ("supervision", 1),
    ("required_telemetry", ["health_status"]), ("locality", "fog")])
def test_invalid_task_domain(field, value):
    data = _dataset()
    data["cases"][0]["task"][field] = value
    with pytest.raises(ValueError):
        campaign.validate_dataset(data)


@pytest.mark.parametrize("field,value", [("latency", True), ("latency", "10"), ("latency", 0),
    ("latency", float("nan")), ("drift", float("inf")), ("drift", 1.01), ("age", -1),
    ("cost", False), ("currency", "usd"), ("health", "alien"), ("health", []),
    ("lifecycle", "running"), ("reservable", 1), ("modalities", ["digital_vector", "spikes"]),
    ("id", "UPPER"), ("id", "nönascii")])
def test_invalid_resource_domain(field, value):
    data = _dataset()
    data["cases"][0]["resources"][0][field] = value
    with pytest.raises(ValueError):
        campaign.validate_dataset(data)


@pytest.mark.parametrize("mutation", ["case_count", "duplicate_case", "duplicate_resource", "extra_field",
    "missing_field", "duplicate_eligible", "unsorted_eligible", "ranking_missing", "ranking_duplicate",
    "selected_not_first", "rejection_missing", "stage_rules", "boolean_numeric"])
def test_invalid_schema_and_expected_internal_consistency(mutation):
    data = _dataset()
    case = data["cases"][0]
    if mutation == "case_count": data["cases"].pop()
    elif mutation == "duplicate_case": data["cases"][1]["id"] = case["id"]
    elif mutation == "duplicate_resource": case["resources"][1]["id"] = "a"
    elif mutation == "extra_field": case["task"]["unknown"] = 2
    elif mutation == "missing_field": del case["resources"][0]["age"]
    elif mutation == "duplicate_eligible": case["expected"]["admissible_resource_ids"] = ["a", "a", "b", "c"]
    elif mutation == "unsorted_eligible": case["expected"]["admissible_resource_ids"].reverse()
    elif mutation == "ranking_missing": case["expected"]["rankings"]["latency_first"].pop()
    elif mutation == "ranking_duplicate": case["expected"]["rankings"]["latency_first"] = ["a", "a", "c"]
    elif mutation == "selected_not_first": case["expected"]["selected"]["latency_first"] = "b"
    elif mutation == "rejection_missing": case["expected"]["admissible_resource_ids"] = ["a", "b"]
    elif mutation == "stage_rules":
        case["expected"]["admissible_resource_ids"] = ["a", "b"]
        case["expected"]["rejections"]["c"] = {"stage": "admission", "failed_rules": ["F6"], "explanation": "bad"}
    else: case["resources"][0]["drift"] = True
    with pytest.raises(ValueError):
        campaign.validate_dataset(data)


def test_strict_json_loader_rejects_duplicate_and_nan(tmp_path):
    target = tmp_path / "fabricated.json"
    target.write_text('{"x":1,"x":2}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        campaign.load_json(target)
    target.write_text('{"x":NaN}', encoding="utf-8")
    with pytest.raises(ValueError, match="non-finite"):
        campaign.load_json(target)
    assert campaign.canonical_sha256(True) != campaign.canonical_sha256(1)


def test_all_fabricated_cells_offline_complete_and_invariant():
    dataset = _dataset()
    result = campaign.analyse(_outputs(dataset), dataset)
    assert result["passed"]
    assert result["selection_matches"] == result["ranking_matches"] == result["eligible_matches"] == 72
    assert result["annotation_matches"] == result["passed_cells"] == 72
    assert result["order_invariant_pairs"] == 36
    assert result["independent_case_count"] == 12


def test_stage_mapping_preserves_duplicates_and_ignores_only_not_evaluated_marker():
    raw = {"candidates": [_candidate("a", 1), _candidate("b", stage="feasibility", violations=[
        "required_telemetry_available: drift_score is required but missing",
        "required_telemetry_available: Required runtime telemetry is unavailable: drift_score",
        "required_telemetry_available: age_of_information_ms is required but missing",
        "telemetry_freshness: Runtime age_of_information_ms is unavailable.",
        "required_telemetry_available: estimated_cost is required but missing",
        "cost_budget: Estimated cost is unavailable or has a different currency."]),
        _candidate("c", stage="admission", violations=["input_modality_compatible: no modality",
            "freshness_observable: no age", "human_supervision_policy: no human", "resource_contract_safety: no"])]}
    normalized = campaign.normalize_report(raw)
    assert normalized["rejections"]["b"] == {"stage": "feasibility", "failed_rules": ["F4", "F7", "F8"]}
    assert normalized["rejections"]["c"] == {"stage": "admission", "failed_rules": ["A1", "A2", "A3", "A4"]}
    assert normalized["unmapped"] == normalized["structural_errors"] == []
    assert len(raw["candidates"][1]["feasibility"]["violations"]) == 6


@pytest.mark.parametrize("code,rule", list(campaign.FEASIBILITY_RULES.items()))
def test_every_declared_feasibility_code_has_explicit_rule(code, rule):
    normalized = campaign.normalize_report({"candidates": [_candidate("a", stage="feasibility", violations=[f"{code}: fabricated"])]})
    assert normalized["rejections"]["a"] == {"stage": "feasibility", "failed_rules": [rule]}
    assert not normalized["unmapped"]


def test_rejection_agreement_and_unknown_diagnostic_is_secondary_mismatch():
    dataset = _dataset()
    for case in dataset["cases"]:
        case["resources"][2]["drift"] = .95
        case["expected"]["admissible_resource_ids"] = ["a", "b"]
        case["expected"]["rejections"] = {"c": {"stage": "feasibility", "failed_rules": ["F6"], "explanation": "Fabricated boundary failure"}}
        case["expected"]["rankings"] = {policy: ["a", "b"] for policy in campaign.POLICIES}
    outputs = _outputs(dataset)
    for output in outputs:
        output["raw_report"]["candidates"][2] = _candidate("c", stage="feasibility", violations=["drift_threshold: fabricated boundary"])
    report = campaign.analyse(outputs, dataset)
    assert report["passed"] and report["annotation_matches"] == 72
    for output in outputs[:6]:
        output["raw_report"]["candidates"][2]["feasibility"]["violations"].append("new_rule: unanticipated")
    report = campaign.analyse(outputs, dataset)
    assert not report["passed"] and report["annotation_matches"] == 66
    assert report["eligible_matches"] == report["ranking_matches"] == report["selection_matches"] == 72
    assert report["cells"][0]["unmapped"]


def test_admission_short_circuit_must_not_hide_extra_feasibility_failure():
    candidate = _candidate("a", stage="admission", violations=["input_modality_compatible: fabricated"])
    candidate["feasibility"]["violations"].append("new_rule: unexpected feasibility evaluation")
    normalized = campaign.normalize_report({"candidates": [candidate]})
    assert normalized["structural_errors"] == ["a: admission short-circuit marker mismatch"]


@pytest.mark.parametrize("violation", ["required_telemetry_semantics: drift_score must be finite",
    "required_telemetry_available: energy_proxy_mj is required but missing",
    "required_telemetry_available: Required runtime telemetry is unavailable: drift_score, new_field",
    "required_telemetry_available: nonsense", "new_gateway_rule: new failure"])
def test_unmapped_diagnostics_never_disappear(violation):
    normalized = campaign.normalize_report({"candidates": [_candidate("a", stage="feasibility", violations=[violation])]})
    assert normalized["unmapped"] == [{"resource_id": "a", "stage": "feasibility", "violation": violation}]


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "unknown", "exception", "input", "runtime_null", "descriptor",
    "task", "fixed_bool_as_numeric", "policy", "rank", "stage", "reversed_ranking", "unmapped"])
def test_offline_mismatch_and_tamper_retained(mutation):
    dataset = _dataset()
    outputs = _outputs(dataset)
    if mutation == "duplicate": outputs.append(deepcopy(outputs[0]))
    elif mutation == "missing": outputs.pop()
    elif mutation == "unknown": outputs[0]["case_id"] = "unknown"
    elif mutation == "exception":
        outputs[0]["error"] = {"type": "ValueError", "message": "fabricated", "traceback": "saved"}
        outputs[0]["raw_report"] = None
    elif mutation == "input": outputs[0]["bridge_input"]["task"]["latency_budget"] = 50.0
    elif mutation == "runtime_null": outputs[0]["production_inputs"]["runtime"]["a"]["drift_score"] = None
    elif mutation == "descriptor": outputs[0]["production_inputs"]["descriptors"][0]["timing"]["typical_latency_ms"] = 1.0
    elif mutation == "task": outputs[0]["production_inputs"]["task"]["min_confidence"] = 0.0
    elif mutation == "fixed_bool_as_numeric": outputs[0]["production_inputs"]["task"]["continuous_monitoring_required"] = 0
    elif mutation == "policy": outputs[0]["raw_report"]["policy"] = "latency_first"
    elif mutation == "rank": outputs[0]["raw_report"]["candidates"][0]["ranking"]["rank"] = True
    elif mutation == "stage": outputs[0]["raw_report"]["candidates"][0]["admission"]["passed"] = False
    elif mutation == "reversed_ranking":
        outputs[1]["raw_report"]["candidates"].reverse()
        for rank, candidate in enumerate(outputs[1]["raw_report"]["candidates"], 1): candidate["ranking"]["rank"] = rank
    else:
        for output in outputs[:6]:
            output["raw_report"]["candidates"][2] = _candidate("c", stage="feasibility", violations=["required_telemetry_semantics: unanticipated"])
    result = campaign.analyse(outputs, dataset)
    assert not result["passed"]
    if mutation not in {"duplicate", "missing", "unknown"}:
        assert result["passed_cells"] < 72
    if mutation == "exception":
        assert result["cells"][0]["error"]["message"] == "fabricated"
        assert not result["cells"][0]["selection_match"]
    if mutation == "reversed_ranking":
        assert result["eligible_matches"] == 72 and result["selection_matches"] == 71
        assert result["order_invariant_pairs"] == 35


def test_bad_freeze_gate_runs_before_any_production_import(monkeypatch):
    import builtins
    previous = builtins.__import__
    seen = []
    def guarded(name, *args, **kwargs):
        if name == "core.matcher" or name == "evaluation.r4_selection":
            seen.append(name)
            raise AssertionError("production import forbidden in verifier unit tests")
        return previous(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", guarded)
    with pytest.raises(ValueError, match="receipt"):
        campaign.observe(_case(), "lexicographic", frozen_receipt={})
    assert not seen
    result = campaign.analyse(_outputs(_dataset()), _dataset())
    assert result["passed"] and not seen


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def _archive(tmp_path):
    root, source = tmp_path / "archive", tmp_path / "source"
    root.mkdir()
    source.mkdir()
    inputs = root / "inputs"
    inputs.mkdir()
    dataset = _dataset()
    _write_json(inputs / "gemini-response-original.json", dataset)
    raw_digest = hashlib.sha256((inputs / "gemini-response-original.json").read_bytes()).hexdigest()
    for name in ("prompt-issued.txt", "provenance.json", "preexecution-review.json", "README.md"):
        (inputs / name).write_text("Fabricated immutable intake", encoding="utf-8")
    intake_files = [{"file": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        for path in sorted(inputs.iterdir())]
    _write_json(inputs / "intake-manifest.json", {"schema": "gemini-selector-intake-manifest-v1", "files": intake_files})
    _write_json(inputs / "gemini-selector-approval.json", {"schema": "gemini-selector-author-approval-v1",
        "isolated_new_chat": True, "cases_and_interpretations_approved": True, "raw_response_sha256": raw_digest})
    (source / "fabricated.py").write_bytes(b"# fabricated\r\n")
    source_hash = hashlib.sha256(b"# fabricated\n").hexdigest()
    _write_json(inputs / "ap1-ap3-source-freeze.json", {"schema": "ap1-ap3-coordinated-source-freeze-v1",
        "gemini_cases_received": False, "gemini_cases_used": False, "source_files": {"fabricated.py": source_hash}})
    _write_json(root / "source-hashes.json", {"fabricated.py": source_hash})
    with zipfile.ZipFile(root / "source-snapshot.zip", "w") as archive:
        archive.write(source / "fabricated.py", "fabricated.py")
    receipt = {"schema": "gemini-selector-campaign-freeze-v1", "status": "frozen_for_scored_run",
        "approval": {"isolated_new_chat": True, "cases_and_interpretations_approved": True},
        "dataset_sha256": raw_digest, "dataset_cases_sha256": {case["id"]: campaign.canonical_sha256(case) for case in dataset["cases"]},
        "source_files": {"fabricated.py": source_hash},
        "inputs": {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in root.rglob("*") if path.is_file()}}
    return root, source, receipt


def test_fabricated_archive_bindings_and_normalized_crlf_identity(tmp_path):
    root, source, receipt = _archive(tmp_path)
    assert campaign.verify_bindings(root, receipt, source_root=source) == []
    campaign.require_frozen_receipt(receipt, _dataset()["cases"][0])
    changed = _dataset()["cases"][0]
    changed["expected"]["reasoning_by_policy"]["lexicographic"] = "changed explanation"
    with pytest.raises(ValueError, match="case differs"):
        campaign.require_frozen_receipt(receipt, changed)


@pytest.mark.parametrize("target", ["dataset", "approval", "intake", "source", "snapshot", "source_receipt", "source_hashes", "dropped_source", "extra_zip", "path"])
def test_archive_binding_tamper(target, tmp_path):
    root, source, receipt = _archive(tmp_path)
    if target == "dataset": (root / "inputs/gemini-response-original.json").write_text("{}", encoding="utf-8")
    elif target == "approval":
        _write_json(root / "inputs/gemini-selector-approval.json", {"schema": "gemini-selector-author-approval-v1", "isolated_new_chat": False})
    elif target == "intake": (root / "inputs/prompt-issued.txt").write_text("changed", encoding="utf-8")
    elif target == "source": (source / "fabricated.py").write_text("# changed\n", encoding="utf-8")
    elif target == "snapshot":
        with zipfile.ZipFile(root / "source-snapshot.zip", "w") as archive: archive.writestr("fabricated.py", "# changed\n")
    elif target == "source_receipt": receipt["source_files"]["fabricated.py"] = "0" * 64
    elif target == "source_hashes": _write_json(root / "source-hashes.json", {"fabricated.py": "0" * 64})
    elif target == "dropped_source": receipt["source_files"] = {"fabricated-other.py": "0" * 64}
    elif target == "extra_zip":
        with zipfile.ZipFile(root / "source-snapshot.zip", "a") as archive: archive.writestr("unfrozen.py", "# extra\n")
    else: receipt["inputs"]["../escape"] = "0" * 64
    assert campaign.verify_bindings(root, receipt, source_root=source)


def test_valid_receipt_requires_approval_flags(tmp_path):
    _, _, receipt = _archive(tmp_path)
    receipt["approval"]["isolated_new_chat"] = False
    with pytest.raises(ValueError, match="isolation"):
        campaign.require_frozen_receipt(receipt)
