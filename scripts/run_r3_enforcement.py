"""Run or independently reverify the frozen direct-enforcement campaign."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
from uuid import uuid4
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_enforcement import CASES, ORACLE, run_case
from evaluation.verify_r3_enforcement import verify_case
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_r2_sdk_recovery import snapshot_sources

PROTOCOL = ROOT / "docs/revision/r3-enforcement-protocol.md"


def verify_campaign(directory):
    root = Path(directory).resolve(strict=True)
    campaign = json.loads((root / "campaign.json").read_text(encoding="utf-8"))
    if campaign["protocol"] != "r3-direct-v1" or campaign["repetitions"] != 2:
        raise ValueError("unknown direct campaign protocol")
    oracle = json.loads((root / "oracle.json").read_text(encoding="utf-8"))
    if campaign["case_order"] != list(oracle["cases"]): raise ValueError("case order mismatch")
    for name, digest in campaign["inputs"].items():
        if file_sha256(root / name) != digest: raise ValueError("frozen campaign input mismatch")
    with zipfile.ZipFile(root / "source-snapshot.zip") as archive:
        if oracle != json.loads(archive.read("evaluation/fixtures/r3-direct-v1.json")):
            raise ValueError("oracle differs from frozen source fixture")
    failures = json.loads((root / "failures.json").read_text(encoding="utf-8"))["failures"]
    reports = []
    for repeat in (1, 2):
        if {p.name for p in (root / f"repeat-{repeat:02d}").iterdir() if p.is_dir()} != set(campaign["case_order"]):
            raise ValueError("direct campaign case inventory mismatch")
        for case in campaign["case_order"]:
            path = root / f"repeat-{repeat:02d}" / case
            if file_sha256(path / "oracle.json") != campaign["inputs"]["oracle.json"]:
                raise ValueError("case oracle differs from campaign")
            reports.append({"repeat": repeat, **verify_case(path)})
    ordinary = [r for r in reports if not r["detector_control"]]
    controls = [r for r in reports if r["detector_control"]]
    return {"protocol": campaign["protocol"], "verified": not failures and all(r["verified"] for r in reports),
        "ordinary_cases": len(ordinary), "ordinary_verified": sum(r["verified"] for r in ordinary),
        "detector_controls": len(controls), "controls_detected": sum(r["verified"] for r in controls),
        "ordinary_starts": sum(r["observed_starts"] for r in ordinary),
        "ordinary_commits": sum(r["observed_commits"] for r in ordinary),
        "ordinary_successful_deliveries": sum(r["successful_deliveries"] for r in ordinary),
        "mcp_calls": sum(r["mcp_calls"] for r in reports), "audit_events": sum(r["audit_events"] for r in reports),
        "cases": reports, "harness_failures": failures}


def run_campaign(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    (root / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    (root / "oracle.json").write_bytes(ORACLE.read_bytes())
    snapshot_sources(root)
    write_json(root / "environment.json", {"python": sys.version, "platform": platform.platform(),
        "packages": {p: version(p) for p in ("mcp", "pydantic", "pytest", "cl-sdk", "tables")}})
    write_json(root / "campaign.json", {"protocol": "r3-direct-v1", "case_order": list(CASES), "repetitions": 2,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {n: file_sha256(root / n) for n in ("protocol.md", "oracle.json", "source-snapshot.zip", "environment.json")}})
    failures = []
    for repeat in (1, 2):
        for case in CASES:
            directory = root / f"repeat-{repeat:02d}" / case
            try:
                report = run_case(directory, case)
                write_json(directory / "verification.json", report)
                print(f"{repeat}/2 {case}: {report['verified']}", flush=True)
            except Exception as exc:
                failure = {"repeat": repeat, "case": case, "error_type": type(exc).__name__, "error": str(exc)}
                failures.append(failure)
                directory.mkdir(parents=True, exist_ok=True)
                write_json(directory / "harness-failure.json", failure)
                print(f"{repeat}/2 {case}: HARNESS FAILURE", flush=True)
    write_json(root / "failures.json", {"failures": failures})
    if failures: raise RuntimeError("direct campaign has retained harness failures")
    report = verify_campaign(root)
    write_json(root / "verification.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / ".cp2n2" / f"r3-direct-{uuid4()}")
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    report = verify_campaign(args.verify) if args.verify else run_campaign(args.output)
    print(json.dumps({k: v for k, v in report.items() if k != "cases"}, indent=2))
    if not report["verified"]: raise SystemExit(1)


if __name__ == "__main__": main()
