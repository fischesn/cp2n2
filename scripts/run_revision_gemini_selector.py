"""Freeze and score the approved external Gemini cases without functional tuning."""
from datetime import datetime, timezone
from importlib.metadata import version
import argparse
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import traceback
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.revision_gemini_selector import (
    ORDERS, POLICIES, analyse, canonical_sha256, load_json, observe,
    production_case, validate_dataset, verify_bindings,
)

INTAKE = ROOT / "docs/revision/gemini-selector-blind-v1"
APPROVAL = ROOT / "docs/revision/gemini-selector-approval.json"
PRIOR = ROOT / "docs/revision/ap1-ap3-source-freeze.json"
PROTOCOL = ROOT / "docs/revision/gemini-selector-campaign-protocol.md"
HARNESS_FILES = ("evaluation/revision_gemini_selector.py",
    "scripts/run_revision_gemini_selector.py", "tests/test_revision_gemini_selector.py",
    "requirements-evaluation.txt", ".gitattributes")
ARCHIVE_SCHEMA = "gemini-selector-campaign-archive-v1"


def file_sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        handle.write("\n")


def specification(dataset):
    return {"schema": "gemini-selector-campaign-specification-v1",
        "case_order": [case["id"] for case in dataset["cases"]],
        "policies": list(POLICIES), "input_orders": list(ORDERS),
        "independent_case_count": 12, "expected_cell_count": 72,
        "candidate_descriptions": 47, "expected_candidate_records": 282,
        "bridge": "unchanged R4 production_inputs; input only; fixed policy lexicographic/seed 41",
        "expected_source": "unchanged Gemini response, not R4 oracle or production output",
        "functional_source_identity": "original 290 normalized source hashes fixed before Gemini receipt",
        "automatic_retries": False, "physical_execution": False, "provider_calls": False}


def freeze(directory):
    """All bytes and author gates are recorded before the first observe call."""
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    approval = load_json(APPROVAL)
    if (approval.get("isolated_new_chat") is not True
            or approval.get("cases_and_interpretations_approved") is not True):
        raise ValueError("author approval and isolated generation required")
    dataset_path = INTAKE / "gemini-response-original.json"
    if file_sha256(dataset_path) != approval["raw_response_sha256"]:
        raise ValueError("approved original dataset changed")
    dataset = validate_dataset(load_json(dataset_path))
    prior = load_json(PRIOR)
    source_names = sorted(set(prior["source_files"]) | set(HARNESS_FILES))
    source_hashes = {}
    with zipfile.ZipFile(root / "source-snapshot.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in source_names:
            path = (ROOT / name).resolve(strict=True)
            if not path.is_relative_to(ROOT):
                raise ValueError("source path escapes repository")
            content = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
            source_hashes[name] = hashlib.sha256(content).hexdigest()
            if name in prior["source_files"] and source_hashes[name] != prior["source_files"][name]:
                raise ValueError(f"functional source changed after blind receipt: {name}")
            archive.writestr(name, content)
    inputs_dir = root / "inputs"
    inputs_dir.mkdir()
    for path in sorted(INTAKE.iterdir()):
        if path.is_file():
            (inputs_dir / path.name).write_bytes(path.read_bytes())
    for path in (APPROVAL, PRIOR):
        (inputs_dir / path.name).write_bytes(path.read_bytes())
    (root / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    write_json(root / "specification.json", specification(dataset))
    write_json(root / "source-hashes.json", source_hashes)
    write_json(root / "environment.json", {"python": sys.version,
        "platform": platform.platform(), "processor": platform.processor(),
        "packages": {name: version(name) for name in ("pydantic", "numpy", "mcp")},
        "base_git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "working_tree_dirty": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)),
        "source_identity": "archived source bytes and per-file hashes, not dirty base commit",
        "model_metadata": "author-reported Gemini Flash 3.8, high effort; original first response",
        "provider_calls": False, "physical_execution": False})
    inputs = {path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*")) if path.is_file()}
    receipt = {"schema": "gemini-selector-campaign-freeze-v1", "status": "frozen_for_scored_run",
        "frozen_at": datetime.now(timezone.utc).isoformat(), "inputs": inputs,
        "source_files": source_hashes, "prior_source_file_count": len(prior["source_files"]),
        "dataset_sha256": file_sha256(dataset_path),
        "dataset_cases_sha256": {case["id"]: canonical_sha256(case) for case in dataset["cases"]},
        "approval": {"isolated_new_chat": True, "cases_and_interpretations_approved": True}}
    write_json(root / "freeze.json", receipt)
    errors = verify_bindings(root, receipt, source_root=ROOT)
    if errors:
        raise ValueError("preexecution binding failed: " + "; ".join(errors))
    return root, dataset, receipt


def markdown_report(report):
    lines = ["# Gemini selector observations", "",
        "Twelve externally model-authored synthetic cases; 72 deterministic policy/order cells.", "",
        f"- Eligible-set agreement: {report['eligible_matches']}/72.",
        f"- Full-ranking agreement: {report['ranking_matches']}/72.",
        f"- Selected-resource agreement: {report['selection_matches']}/72.",
        f"- Normalized rejection-stage/rule agreement: {report['annotation_matches']}/72.",
        f"- All checks passed: {report['passed_cells']}/72.",
        f"- Input-order invariant pairs: {report['order_invariant_pairs']}/36.",
        f"- Overall passed: {report['passed']}.", "",
        "| Case | Policy | Order | Eligible | Ranking | Choice | Reasons | Passed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in report["cells"]:
        lines.append("| " + " | ".join(str(row[key]) for key in
            ("case_id", "policy", "input_order", "eligible_match", "ranking_match",
             "selection_match", "annotation_match", "passed")) + " |")
    lines += ["", "These are specification-conformance observations, not physical PNN performance",
        "or real-workload optimality. Reversed-order repeats are not independent samples.",
        "Original expected outcomes and functional source were not changed after scoring.", ""]
    return "\n".join(lines)


def verify(directory, *, check_live_source=False):
    """Read-only complete archive and report recomputation without production calls."""
    root = Path(directory).resolve(strict=True)
    manifest = load_json(root / "manifest.json")
    if manifest.get("schema") != ARCHIVE_SCHEMA:
        raise ValueError("unknown Gemini selector archive schema")
    inventory = {path.relative_to(root).as_posix() for path in root.rglob("*")
        if path.is_file() and path.relative_to(root).as_posix() != "manifest.json"}
    if inventory != set(manifest["files"]):
        raise ValueError("Gemini selector archive inventory mismatch")
    for name, digest in manifest["files"].items():
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or file_sha256(path) != digest:
            raise ValueError("Gemini selector archive checksum/path mismatch")
    receipt = load_json(root / "freeze.json")
    errors = verify_bindings(root, receipt, source_root=ROOT if check_live_source else None)
    if errors:
        raise ValueError("Gemini selector binding failure: " + "; ".join(errors))
    dataset = validate_dataset(load_json(root / "inputs/gemini-response-original.json"))
    if canonical_sha256(load_json(root / "specification.json")) != canonical_sha256(specification(dataset)):
        raise ValueError("Gemini selector frozen specification mismatch")
    outputs = load_json(root / "outputs.json")
    report = analyse(outputs, dataset)
    stored = load_json(root / "verification.json")
    if canonical_sha256(report) != canonical_sha256(stored):
        raise ValueError("Gemini selector stored report differs from raw evidence")
    expected_observation_files = set()
    for output in outputs:
        name = f"observations/{output['case_id']}/{output['policy']}/{output['input_order']}.json"
        expected_observation_files.add(name)
        if canonical_sha256(load_json(root / name)) != canonical_sha256(output):
            raise ValueError("Gemini selector per-cell report differs from aggregate")
    actual_observation_files = {path.relative_to(root).as_posix() for path in (root / "observations").rglob("*.json")}
    if actual_observation_files != expected_observation_files:
        raise ValueError("Gemini selector cell-file inventory mismatch")
    if (root / "report.md").read_text(encoding="utf-8") != markdown_report(report):
        raise ValueError("Gemini selector Markdown report differs from analysis")
    return report


def run(directory):
    root, dataset, receipt = freeze(directory)
    outputs = []
    for case in dataset["cases"]:
        for policy in POLICIES:
            for order in ORDERS:
                try:
                    row = observe(case, policy, reverse=order == "reversed", frozen_receipt=receipt)
                except Exception as error:
                    row = {"schema": "gemini-selector-observation-v1", "case_id": case["id"],
                        "policy": policy, "input_order": order, "bridge_input": production_case(case),
                        "production_inputs": None, "raw_report": None,
                        "error": {"type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc()}}
                outputs.append(row)
                write_json(root / "observations" / case["id"] / policy / f"{order}.json", row)
                print(f"Gemini {case['id']} {policy} {order}: retained", flush=True)
    write_json(root / "outputs.json", outputs)
    report = analyse(outputs, dataset)
    errors = verify_bindings(root, receipt, source_root=ROOT)
    if errors:
        write_json(root / "source-integrity-failure.json", {"errors": errors})
        raise ValueError("source/input changed during scoring: " + "; ".join(errors))
    write_json(root / "verification.json", report)
    (root / "report.md").write_text(markdown_report(report), encoding="utf-8", newline="\n")
    write_json(root / "manifest.json", {"schema": ARCHIVE_SCHEMA, "files": {
        path.relative_to(root).as_posix(): file_sha256(path) for path in sorted(root.rglob("*"))
        if path.is_file() and path.relative_to(root).as_posix() != "manifest.json"}})
    return verify(root, check_live_source=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--check-live-source", action="store_true")
    args = parser.parse_args()
    if bool(args.output) == bool(args.verify):
        parser.error("exactly one of --output or --verify is required")
    result = verify(args.verify, check_live_source=args.check_live_source) if args.verify else run(args.output)
    print(json.dumps({key: value for key, value in result.items() if key not in {"cells", "order_invariance"}}, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
