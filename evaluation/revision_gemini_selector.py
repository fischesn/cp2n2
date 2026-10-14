"""Frozen, externally authored selector cases; no production-derived oracle.

Importing this module and analysing saved reports are offline operations. The
production matcher/bridge are imported only by ``observe`` after the explicit
campaign-freeze gate. Expectations always come from the unchanged external JSON.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
import traceback
import zipfile


SCHEMA = "gemini-selector-blind-v1"
POLICIES = ("lexicographic", "latency_first", "locality_cost_first")
ORDERS = ("original", "reversed")
ADMISSION_RULES = {"input_modality_compatible": "A1", "freshness_observable": "A2",
    "human_supervision_policy": "A3", "resource_contract_safety": "A4"}
FEASIBILITY_RULES = {"runtime_available": "F1", "lifecycle_available": "F2",
    "resource_reservable": "F3", "latency_budget": "F5", "drift_threshold": "F6",
    "telemetry_freshness": "F7", "cost_budget": "F8"}
REQUIRED_FIELDS = {"drift_score": "F4", "age_of_information_ms": "F7", "estimated_cost": "F8"}
TASK_KEYS = {"latency_budget", "max_age", "max_cost", "required_telemetry", "supervision",
    "locality", "stochasticity_tolerance", "reset_free"}
RESOURCE_KEYS = {"id", "latency", "drift", "age", "health", "lifecycle", "reservable",
    "cost", "currency", "locality", "stochastic", "stateful", "age_supported",
    "supervision_required", "contract_admissible", "modalities"}
IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def canonical_sha256(value):
    """Canonical JSON identity, retaining numeric/bool distinctions and expectations."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def load_json(path):
    """Reject non-JSON numbers and duplicate object keys rather than normalising them."""
    def object_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def constant(value):
        raise ValueError(f"non-finite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=object_pairs, parse_constant=constant)


def _keys(value, expected, path):
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{path}: exact object fields required")


def _text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: nonempty text required")


def _identifier(value, path):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError(f"{path}: lowercase ASCII identifier required")


def _number(value, path, *, nullable=False, positive=False, maximum=None):
    if nullable and value is None:
        return
    if type(value) not in {int, float}:
        raise ValueError(f"{path}: finite numeric value required (not bool/string)")
    try:
        valid = math.isfinite(value) and (value > 0 if positive else value >= 0)
    except OverflowError:
        valid = False
    if not valid or maximum is not None and value > maximum:
        raise ValueError(f"{path}: numeric value outside restricted domain")


def _boolean(value, path):
    if type(value) is not bool:
        raise ValueError(f"{path}: boolean required")


def validate_dataset(dataset):
    """Validate structure/domain/internal expectation consistency, never make an oracle.

This does not recalculate eligibility or ranking semantics. Those independent
preexecution arithmetic checks and author approval are separate frozen inputs.
"""
    _keys(dataset, {"schema_version", "cases", "coverage_summary", "specification_questions"}, "dataset")
    if dataset["schema_version"] != SCHEMA or not isinstance(dataset["cases"], list) or len(dataset["cases"]) != 12:
        raise ValueError("dataset: exactly twelve cases with declared schema required")
    for key in ("coverage_summary", "specification_questions"):
        if not isinstance(dataset[key], list):
            raise ValueError(f"dataset.{key}: text array required")
        for value in dataset[key]:
            _text(value, f"dataset.{key}")
    seen = set()
    for case in dataset["cases"]:
        validate_case(case)
        if case["id"] in seen:
            raise ValueError("duplicate case identifier")
        seen.add(case["id"])
    return deepcopy(dataset)


def validate_case(case):
    _keys(case, {"id", "scenario", "task", "resources", "expected", "test_purpose"}, "case")
    _identifier(case["id"], "case.id")
    _text(case["scenario"], "case.scenario")
    _text(case["test_purpose"], "case.test_purpose")
    task = case["task"]
    _keys(task, TASK_KEYS, "case.task")
    for name in ("latency_budget", "max_age"):
        _number(task[name], f"task.{name}", positive=True)
    _number(task["max_cost"], "task.max_cost", nullable=True)
    _number(task["stochasticity_tolerance"], "task.stochasticity_tolerance", maximum=1)
    if task["required_telemetry"] not in ([], ["drift_score"]):
        raise ValueError("task.required_telemetry: restricted field list required")
    for name in ("supervision", "reset_free"):
        _boolean(task[name], f"task.{name}")
    if task["locality"] not in ("edge", "cloud", None):
        raise ValueError("task.locality: restricted locality required")
    resources = case["resources"]
    if not isinstance(resources, list) or not 3 <= len(resources) <= 5:
        raise ValueError("case.resources: three to five resources required")
    identifiers = []
    for resource in resources:
        _keys(resource, RESOURCE_KEYS, "resource")
        _identifier(resource["id"], "resource.id")
        identifiers.append(resource["id"])
        _number(resource["latency"], "resource.latency", positive=True)
        _number(resource["drift"], "resource.drift", nullable=True, maximum=1)
        for name in ("age", "cost"):
            _number(resource[name], f"resource.{name}", nullable=True)
        for name in ("reservable", "stochastic", "stateful", "age_supported", "supervision_required", "contract_admissible"):
            _boolean(resource[name], f"resource.{name}")
        if not isinstance(resource["health"], str) or resource["health"] not in {"healthy", "ready", "degraded", "unknown", "offline", "failed", "unreachable"}:
            raise ValueError("resource.health: restricted state required")
        if not isinstance(resource["lifecycle"], str) or resource["lifecycle"] not in {"ready", "failed", "unreachable", "aborting"}:
            raise ValueError("resource.lifecycle: restricted lifecycle required")
        if resource["currency"] != "eur" or not isinstance(resource["locality"], str) or resource["locality"] not in {"edge", "cloud"}:
            raise ValueError("resource.currency/locality outside restricted domain")
        if resource["modalities"] not in (["digital_vector"], ["spikes"]):
            raise ValueError("resource.modalities: one restricted modality required")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate resource identifier")
    expected = case["expected"]
    _keys(expected, {"admissible_resource_ids", "rejections", "rankings", "selected", "reasoning_by_policy"}, "case.expected")
    eligible = expected["admissible_resource_ids"]
    if (not isinstance(eligible, list) or any(not isinstance(x, str) for x in eligible)
        or eligible != sorted(set(eligible)) or not set(eligible) <= set(identifiers)):
        raise ValueError("expected admissible IDs must be sorted unique known resources")
    rejections = expected["rejections"]
    if not isinstance(rejections, dict) or set(rejections) != set(identifiers) - set(eligible):
        raise ValueError("expected rejection coverage differs from eligible complement")
    for identifier, rejection in rejections.items():
        _keys(rejection, {"stage", "failed_rules", "explanation"}, f"rejection.{identifier}")
        stage = rejection["stage"]
        if stage not in {"admission", "feasibility"}:
            raise ValueError("expected rejection stage invalid")
        rules = rejection["failed_rules"]
        allowed = {f"A{i}" for i in range(1, 5)} if stage == "admission" else {f"F{i}" for i in range(1, 9)}
        if (not isinstance(rules, list) or not rules or any(not isinstance(x, str) for x in rules)
            or len(rules) != len(set(rules)) or not set(rules) <= allowed):
            raise ValueError("expected rejection rules invalid for stage")
        _text(rejection["explanation"], "rejection.explanation")
    for field in ("rankings", "selected", "reasoning_by_policy"):
        _keys(expected[field], set(POLICIES), f"expected.{field}")
    for policy in POLICIES:
        ranking = expected["rankings"][policy]
        if (not isinstance(ranking, list) or any(not isinstance(x, str) for x in ranking)
            or len(ranking) != len(set(ranking)) or set(ranking) != set(eligible)):
            raise ValueError("expected complete ranking must permute eligible IDs")
        if expected["selected"][policy] != (ranking[0] if ranking else None):
            raise ValueError("expected selection differs from first ranked resource")
        _text(expected["reasoning_by_policy"][policy], "expected.reasoning_by_policy")


def production_case(case):
    """Input-only bridge payload. Do not pass expected outcomes to production."""
    validate_case(case)
    value = {"id": case["id"], "task": deepcopy(case["task"]), "resources": deepcopy(case["resources"])}
    value["task"].update(policy="lexicographic", seed=41)
    return value


def require_frozen_receipt(receipt, case=None):
    """Explicit run gate; archived file/source checks are performed by verify_bindings."""
    if not isinstance(receipt, dict) or receipt.get("schema") != "gemini-selector-campaign-freeze-v1" or receipt.get("status") != "frozen_for_scored_run":
        raise ValueError("explicit frozen campaign receipt required before production import")
    approval = receipt.get("approval", {})
    if approval.get("isolated_new_chat") is not True or approval.get("cases_and_interpretations_approved") is not True:
        raise ValueError("confirmed isolation and author approval required")
    for name in ("inputs", "source_files", "dataset_cases_sha256"):
        rows = receipt.get(name)
        if not isinstance(rows, dict) or not rows or any(not isinstance(k, str) or not isinstance(v, str) or not SHA256.fullmatch(v) for k, v in rows.items()):
            raise ValueError(f"frozen receipt {name} hashes required")
    if len(receipt["dataset_cases_sha256"]) != 12 or not SHA256.fullmatch(str(receipt.get("dataset_sha256", ""))):
        raise ValueError("frozen dataset identity required")
    if case is not None and receipt["dataset_cases_sha256"].get(case["id"]) != canonical_sha256(case):
        raise ValueError("case differs from frozen external input/expectation")


def _safe_path(root, name):
    if not isinstance(name, str) or not name or Path(name).is_absolute() or "\\" in name:
        raise ValueError("unsafe archive/source path")
    target = (root / name).resolve(strict=True)
    if not target.is_relative_to(root):
        raise ValueError("archive/source path escapes root")
    return target


def verify_bindings(directory, receipt, *, source_root=None):
    """Offline raw intake/approval/source binding checks; no selector imports/calls."""
    errors = []
    try:
        require_frozen_receipt(receipt)
        root = Path(directory).resolve(strict=True)
        for name, expected_hash in receipt["inputs"].items():
            if hashlib.sha256(_safe_path(root, name).read_bytes()).hexdigest() != expected_hash:
                errors.append(f"input checksum mismatch: {name}")
        def unique_file(basename):
            names = [name for name in receipt["inputs"] if Path(name).name == basename]
            if len(names) != 1:
                raise ValueError(f"one frozen {basename} required")
            return _safe_path(root, names[0])
        dataset_path = unique_file("gemini-response-original.json")
        if hashlib.sha256(dataset_path.read_bytes()).hexdigest() != receipt["dataset_sha256"]:
            errors.append("external raw dataset identity mismatch")
        dataset = validate_dataset(load_json(dataset_path))
        if {case["id"]: canonical_sha256(case) for case in dataset["cases"]} != receipt["dataset_cases_sha256"]:
            errors.append("complete external case/expectation identity mismatch")
        approval = load_json(unique_file("gemini-selector-approval.json"))
        if (approval.get("schema") != "gemini-selector-author-approval-v1"
            or approval.get("isolated_new_chat") is not True
            or approval.get("cases_and_interpretations_approved") is not True
            or approval.get("raw_response_sha256") != receipt["dataset_sha256"]):
            errors.append("archived author approval binding mismatch")
        intake_path = unique_file("intake-manifest.json")
        intake = load_json(intake_path)
        for row in intake["files"]:
            original = _safe_path(intake_path.parent, row["file"])
            if hashlib.sha256(original.read_bytes()).hexdigest() != row["sha256"]:
                errors.append(f"historical intake changed: {row['file']}")
            relative = original.relative_to(root).as_posix()
            if receipt["inputs"].get(relative) != row["sha256"]:
                errors.append(f"historical intake not frozen: {row['file']}")
        previous = load_json(unique_file("ap1-ap3-source-freeze.json"))
        if (previous.get("schema") != "ap1-ap3-coordinated-source-freeze-v1"
            or previous.get("gemini_cases_received") is not False
            or previous.get("gemini_cases_used") is not False):
            errors.append("pre-receipt functional freeze identity invalid")
        for name, expected_hash in previous["source_files"].items():
            if receipt["source_files"].get(name) != expected_hash:
                errors.append(f"functional source freeze overwritten: {name}")
        if load_json(unique_file("source-hashes.json")) != receipt["source_files"]:
            errors.append("source hash inventory differs from freeze receipt")
        with zipfile.ZipFile(unique_file("source-snapshot.zip")) as archive:
            if len(archive.namelist()) != len(set(archive.namelist())):
                errors.append("duplicate source zip entries")
            if set(archive.namelist()) != set(receipt["source_files"]):
                errors.append("source ZIP inventory differs from frozen source mapping")
            for name, expected_hash in receipt["source_files"].items():
                content = archive.read(name).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
                if hashlib.sha256(content).hexdigest() != expected_hash:
                    errors.append(f"source snapshot mismatch: {name}")
        if source_root is not None:
            source = Path(source_root).resolve(strict=True)
            for name, expected_hash in receipt["source_files"].items():
                content = _safe_path(source, name).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
                if hashlib.sha256(content).hexdigest() != expected_hash:
                    errors.append(f"working source changed after freeze: {name}")
    except (ValueError, KeyError, TypeError, OSError, UnicodeError, zipfile.BadZipFile) as error:
        errors.append(f"binding validation error: {type(error).__name__}: {error}")
    return errors


def validate_saved_production_inputs(case, saved, policy, reverse):
    """Offline flat-case binding of serialized production inputs and fixed constants."""
    _keys(saved, {"task", "descriptors", "runtime"}, "saved production inputs")
    task_json, descriptors_json, runtime = saved["task"], saved["descriptors"], saved["runtime"]
    if not isinstance(task_json, dict) or not isinstance(descriptors_json, list) or not isinstance(runtime, dict):
        raise ValueError("serialized bridge objects required")
    fixed = {"task_kind": "classification", "required_input_modalities": ["digital_vector"],
        "direct_backend_id": None, "continuous_monitoring_required": False,
        "repeated_invocation_expected": False, "min_confidence": 0.2, "selection_seed": 41,
        "selection_policy": policy}
    if any(key not in task_json or canonical_sha256(task_json[key]) != canonical_sha256(value) for key, value in fixed.items()):
        raise ValueError("bridge changed fixed task-domain constants")
    source_task = case["task"]
    task_fields = {"task_id": case["id"], "latency_budget_ms": source_task["latency_budget"],
        "max_twin_age_ms": source_task["max_age"], "max_estimated_cost": source_task["max_cost"],
        "cost_currency": "eur" if source_task["max_cost"] is not None else None,
        "required_telemetry_fields": source_task["required_telemetry"],
        "human_supervision_available": source_task["supervision"], "preferred_locality": source_task["locality"],
        "stochasticity_tolerance": source_task["stochasticity_tolerance"], "reset_free_preferred": source_task["reset_free"]}
    if any(key not in task_json or canonical_sha256(task_json[key]) != canonical_sha256(value) for key, value in task_fields.items()):
        raise ValueError("serialized task differs from external input")
    expected_ids = [item["id"] for item in case["resources"]]
    if reverse:
        expected_ids.reverse()
    if [item["backend_id"] for item in descriptors_json] != expected_ids:
        raise ValueError("bridge resource/order mismatch")
    for descriptor in descriptors_json:
        capability, telemetry = descriptor["capability"], descriptor["telemetry"]
        if ("classification" not in capability["supported_task_types"]
            or capability["health_sensitive"] is not False or capability["resettable"] is not True
            or telemetry["supports_health_status"] is not True or telemetry["supports_confidence"] is not True
            or telemetry["supports_drift_reporting"] is not True
            or "drift_score" not in [item["name"] for item in telemetry["metrics"]]
            or not descriptor["lifecycle"]["supported_reset_modes"]):
            raise ValueError("bridge changed fixed resource-domain constants")
        resource = next(item for item in case["resources"] if item["id"] == descriptor["backend_id"])
        actual = {"latency": descriptor["timing"]["typical_latency_ms"],
            "age_supported": telemetry["supports_age_of_information"],
            "locality": descriptor["policy"]["locality"],
            "supervision_required": descriptor["policy"]["human_supervision_required"],
            "stochastic": capability["stochastic"], "stateful": descriptor["lifecycle"]["stateful"]}
        if any(canonical_sha256(value) != canonical_sha256(resource[key]) for key, value in actual.items()):
            raise ValueError("serialized descriptor differs from external input")
        contracts = descriptor["input_contracts"]
        if not contracts or any(contract["modality"] != resource["modalities"][0] for contract in contracts):
            raise ValueError("serialized descriptor modalities differ from external input")
    expected_runtime = {}
    for resource in case["resources"]:
        expected_runtime[resource["id"]] = {"health_status": resource["health"],
            "control_plane_lifecycle": resource["lifecycle"], "reservable": resource["reservable"],
            "age_of_information_ms": resource["age"], "estimated_cost": resource["cost"],
            "cost_currency": resource["currency"], "contract_safety_admissible": resource["contract_admissible"],
            "drift_score": resource["drift"]}
    if canonical_sha256(runtime) != canonical_sha256(expected_runtime):
        raise ValueError("bridge altered explicit runtime values or dropped null observations")
    return saved


def _preflight_bridge(case, task, descriptors, runtime, policy, reverse):
    """Reject changes to fixed-domain bridge constants without tuning production."""
    saved = {"task": task.model_dump(mode="json"),
        "descriptors": [item.model_dump(mode="json") for item in descriptors], "runtime": deepcopy(runtime)}
    return validate_saved_production_inputs(case, saved, policy, reverse)


def observe(case, policy, reverse=False, *, frozen_receipt):
    """One scored call after receipt. All exceptions are retained, never retried."""
    require_frozen_receipt(frozen_receipt, case)
    if policy not in POLICIES or type(reverse) is not bool:
        raise ValueError("unknown scored policy/order")
    input_only = production_case(case)
    row = {"schema": "gemini-selector-observation-v1", "case_id": case["id"],
        "policy": policy, "input_order": "reversed" if reverse else "original",
        "bridge_input": input_only, "production_inputs": None, "raw_report": None, "error": None}
    try:
        # This is the sole import boundary for production evaluation. No oracle.
        from core.matcher import BackendMatcher
        from evaluation.r4_selection import production_inputs
        task, descriptors, runtime = production_inputs(deepcopy(input_only))
        task.selection_policy = policy
        if reverse:
            descriptors.reverse()
        row["production_inputs"] = _preflight_bridge(case, task, descriptors, runtime, policy, reverse)
        matcher = BackendMatcher()
        if matcher.DRIFT_INADMISSIBLE_THRESHOLD != 0.95:
            raise ValueError("frozen production drift threshold changed")
        row["raw_report"] = matcher.rank_backends(task, descriptors, runtime_state=runtime,
            policy=policy).model_dump(mode="json")
    except Exception as error:
        row["error"] = {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}
    return row


def _mapped_rules(violations, stage):
    rules, unmapped = set(), []
    mapping = ADMISSION_RULES if stage == "admission" else FEASIBILITY_RULES
    for violation in violations:
        code, _, detail = violation.partition(":")
        code = code.strip()
        if code in mapping:
            rules.add(mapping[code])
        elif stage == "feasibility" and code == "required_telemetry_available":
            # Both AP1 helper and original matcher may report the same missing
            # field. Aggregate known mentioned fields, never guess unknown ones.
            if detail.strip().startswith("Required runtime telemetry is unavailable:"):
                fields = [item.strip() for item in detail.split(":", 1)[1].split(",")]
            else:
                match = re.fullmatch(r"\s*([a-z_]+) is required but missing\s*", detail)
                fields = [match.group(1)] if match else []
            if fields and all(field in REQUIRED_FIELDS for field in fields):
                rules.update(REQUIRED_FIELDS[field] for field in fields)
            else:
                unmapped.append({"stage": stage, "violation": violation})
        else:
            # Includes required_telemetry_semantics: malformed values were
            # deliberately excluded and must not disappear in normalization.
            unmapped.append({"stage": stage, "violation": violation})
    return sorted(rules), unmapped


def normalize_report(raw_report):
    """Offline MatchReport-shaped extraction, including all unmapped violations."""
    result = {"eligible": [], "ranking": [], "selected": None, "rejections": {},
        "unmapped": [], "structural_errors": []}
    try:
        if not isinstance(raw_report, dict) or not isinstance(raw_report.get("candidates"), list):
            raise ValueError("raw MatchReport candidates array required")
        if raw_report.get("provider_errors", {}) != {}:
            result["structural_errors"].append("unexpected provider errors in pure selector fixture")
        seen, ranks = set(), []
        for candidate in raw_report["candidates"]:
            if not isinstance(candidate, dict):
                raise ValueError("candidate object required")
            identifier = candidate["backend_id"]
            _identifier(identifier, "report.backend_id")
            if identifier in seen:
                raise ValueError("duplicate report resource")
            seen.add(identifier)
            accepted = candidate["accepted"]
            _boolean(accepted, "report.accepted")
            admission, feasibility = candidate["admission"], candidate["feasibility"]
            for stage, decision in (("admission", admission), ("feasibility", feasibility)):
                if not isinstance(decision, dict) or decision.get("stage") != stage:
                    raise ValueError("candidate stage identity mismatch")
                _boolean(decision["passed"], "report.stage.passed")
                if not isinstance(decision["violations"], list) or any(not isinstance(x, str) for x in decision["violations"]):
                    raise ValueError("raw violation strings required")
            if accepted != (admission["passed"] and feasibility["passed"]):
                result["structural_errors"].append(f"{identifier}: accepted/stages inconsistent")
            if accepted:
                if admission["violations"] or feasibility["violations"]:
                    result["structural_errors"].append(f"{identifier}: passing candidate has violations")
                result["ranking"].append(identifier)
                rank = candidate["ranking"]["rank"]
                if type(rank) is not int:
                    raise ValueError("accepted numeric rank required")
                ranks.append(rank)
                continue
            stage = "feasibility" if admission["passed"] else "admission"
            decision = candidate[stage]
            if not decision["violations"]:
                result["structural_errors"].append(f"{identifier}: failed stage without violations")
            rules, unmapped = _mapped_rules(decision["violations"], stage)
            result["rejections"][identifier] = {"stage": stage, "failed_rules": rules}
            result["unmapped"].extend({"resource_id": identifier, **item} for item in unmapped)
            if admission["passed"] and admission["violations"]:
                result["structural_errors"].append(f"{identifier}: passing admission has violations")
            if not admission["passed"] and feasibility["passed"]:
                result["structural_errors"].append(f"{identifier}: failed admission with evaluated passing feasibility")
            if not admission["passed"] and feasibility["violations"] != ["Feasibility was not evaluated because admission failed."]:
                result["structural_errors"].append(f"{identifier}: admission short-circuit marker mismatch")
        if ranks != list(range(1, len(ranks) + 1)):
            result["structural_errors"].append("accepted rank/order mismatch")
        result["eligible"] = sorted(result["ranking"])
        result["selected"] = result["ranking"][0] if result["ranking"] else None
    except (ValueError, KeyError, TypeError) as error:
        result["structural_errors"].append(f"report structure: {type(error).__name__}: {error}")
    return result


def analyse(outputs, dataset):
    """Recompute exact72-cell comparisons exclusively from saved reports/data."""
    cases = {case["id"]: case for case in validate_dataset(dataset)["cases"]}
    expected_cells = {(identifier, policy, order) for identifier in cases for policy in POLICIES for order in ORDERS}
    cells, seen, coverage_errors = [], set(), []
    if not isinstance(outputs, list):
        raise ValueError("saved observations array required")
    for index, output in enumerate(outputs):
        if not isinstance(output, dict):
            coverage_errors.append(f"observation {index}: object required")
            continue
        key = (output.get("case_id"), output.get("policy"), output.get("input_order"))
        try:
            known = key in expected_cells
        except TypeError:
            known = False
        if not known:
            coverage_errors.append(f"observation {index}: unknown cell")
            continue
        if key in seen:
            coverage_errors.append(f"duplicate cell: {key}")
        seen.add(key)
        case, policy, order = cases[key[0]], key[1], key[2]
        expected = case["expected"]
        normalized = normalize_report(output.get("raw_report"))
        errors = list(normalized["structural_errors"])
        if output.get("schema") != "gemini-selector-observation-v1":
            errors.append("observation schema mismatch")
        try:
            if canonical_sha256(output.get("bridge_input")) != canonical_sha256(production_case(case)):
                errors.append("saved input-only bridge binding mismatch")
        except (TypeError, ValueError, OverflowError):
            errors.append("saved input-only bridge invalid JSON/domain")
        try:
            validate_saved_production_inputs(case, output.get("production_inputs"), policy, order == "reversed")
        except (KeyError, TypeError, ValueError, OverflowError):
            errors.append("serialized production input binding mismatch")
        raw = output.get("raw_report")
        if isinstance(raw, dict):
            if raw.get("task_id") != case["id"] or raw.get("policy") != policy:
                errors.append("raw report task/policy binding mismatch")
            try:
                ids = [candidate["backend_id"] for candidate in raw["candidates"]]
                if len(ids) != len(set(ids)) or set(ids) != {resource["id"] for resource in case["resources"]}:
                    errors.append("raw candidate inventory binding mismatch")
            except (KeyError, TypeError):
                errors.append("raw candidate inventory invalid")
        expected_rejections = {identifier: {"stage": rejection["stage"],
            "failed_rules": sorted(rejection["failed_rules"])} for identifier, rejection in expected["rejections"].items()}
        succeeded = output.get("error") is None and not errors
        row = {"case_id": case["id"], "policy": policy, "input_order": order,
            "eligible_match": succeeded and normalized["eligible"] == expected["admissible_resource_ids"],
            "ranking_match": succeeded and normalized["ranking"] == expected["rankings"][policy],
            "selection_match": succeeded and normalized["selected"] == expected["selected"][policy],
            "annotation_match": succeeded and not normalized["unmapped"] and normalized["rejections"] == expected_rejections,
            "error": deepcopy(output.get("error")), "structural_errors": errors,
            "unmapped": normalized["unmapped"], "observed": normalized,
            "expected": {"eligible": deepcopy(expected["admissible_resource_ids"]),
                "ranking": deepcopy(expected["rankings"][policy]), "selected": expected["selected"][policy],
                "rejections": expected_rejections}}
        row["passed"] = all(row[name] for name in ("eligible_match", "ranking_match", "selection_match", "annotation_match"))
        cells.append(row)
    missing = sorted(expected_cells - seen)
    if missing:
        coverage_errors.append(f"missing {len(missing)} declared policy/order cells")
    ordering = []
    for identifier in cases:
        for policy in POLICIES:
            pair = [row for row in cells if row["case_id"] == identifier and row["policy"] == policy]
            original = [row for row in pair if row["input_order"] == "original"]
            reverse = [row for row in pair if row["input_order"] == "reversed"]
            same = False
            if len(original) == len(reverse) == 1:
                same = all(original[0]["observed"][field] == reverse[0]["observed"][field]
                    for field in ("eligible", "ranking", "selected", "rejections", "unmapped"))
                same = same and not original[0]["error"] and not reverse[0]["error"] and not original[0]["structural_errors"] and not reverse[0]["structural_errors"]
            ordering.append({"case_id": identifier, "policy": policy, "order_invariant": same})
    return {"schema": "gemini-selector-analysis-v1", "independent_case_count": 12,
        "expected_cell_count": 72, "observed_cell_count": len(outputs), "analysed_cell_count": len(cells),
        "coverage_errors": coverage_errors, "missing_cells": [list(key) for key in missing],
        "eligible_matches": sum(row["eligible_match"] for row in cells),
        "ranking_matches": sum(row["ranking_match"] for row in cells),
        "selection_matches": sum(row["selection_match"] for row in cells),
        "annotation_matches": sum(row["annotation_match"] for row in cells),
        "passed_cells": sum(row["passed"] for row in cells),
        "order_invariant_pairs": sum(row["order_invariant"] for row in ordering),
        "cells": cells, "order_invariance": ordering,
        "passed": not coverage_errors and len(cells) == 72 and all(row["passed"] for row in cells) and all(row["order_invariant"] for row in ordering)}
