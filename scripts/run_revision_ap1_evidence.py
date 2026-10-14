"""Freeze and verify the separately declared AP1 MCP evidence campaign."""
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.revision_ap1_evidence import CASES, analyse_case, run_case, specification, verify_campaign
from evaluation.r4_common import environment
from evaluation.biopattern_gate_native import file_sha256
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_r2_sdk_recovery import snapshot_sources


def campaign(root):
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    spec = specification()
    write_json(root / "specification.json", spec)
    (root / "protocol.md").write_bytes((ROOT / "docs/revision/ap1-validation-protocol.md").read_bytes())
    write_json(root / "environment.json", environment())
    snapshot_sources(root)
    # The historical helper's allowlist predates remote/testbed/twin imports.
    # Extend this new snapshot only, never the old campaign archive.
    with zipfile.ZipFile(root / "source-snapshot.zip", "a", zipfile.ZIP_DEFLATED) as archive:
        names = set(archive.namelist())
        for folder in ("demos", "twins", "remote", "testbed", "deployments"):
            for path in sorted((ROOT / folder).rglob("*")):
                if (not path.is_file() or path.suffix not in {".py", ".json"}
                        or "__pycache__" in path.parts):
                    continue
                name = path.relative_to(ROOT).as_posix()
                if name not in names:
                    archive.writestr(name, path.read_text(encoding="utf-8").replace("\r\n", "\n"))
                    names.add(name)
        if (ROOT / "pyproject.toml").exists():
            archive.writestr("pyproject.toml", (ROOT / "pyproject.toml").read_text(encoding="utf-8").replace("\r\n", "\n"))
    write_json(root / "freeze.json", {"schema": "ap1-freeze-v1", "frozen_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {n: file_sha256(root / n) for n in ("specification.json", "protocol.md", "environment.json", "source-snapshot.zip")}})
    rows = []
    for repeat in range(1, spec["repetitions"] + 1):
        for name in spec["case_order"]:
            row = run_case(root / f"repeat-{repeat:02d}" / name, name)
            rows.append(row)
            print(f"AP1 {repeat}/2 {name}: {row['verified']}", flush=True)
    ordinary = [r for r in rows if not r["detector_control"]]
    report = {"verified": all(r["verified"] for r in rows), "trials": rows,
        "ordinary_trials": len(ordinary), "detector_trials": len(rows) - len(ordinary),
        "starts": sum(r["observed_starts"] for r in ordinary), "commits": sum(r["observed_commits"] for r in ordinary),
        "successful_deliveries": sum(r["successful_deliveries"] for r in ordinary),
        "mcp_calls": sum(r["mcp_calls"] for r in rows), "audit_events": sum(r["audit_events"] for r in rows),
        "physical_observations": 0, "generic_replay_resistance": False, "gemini_cases_used": False}
    write_json(root / "verification.json", report)
    write_json(root / "manifest.json", {"schema": "ap1-archive-v1", "files": {
        p.relative_to(root).as_posix(): file_sha256(p) for p in sorted(root.rglob("*"))
        if p.is_file() and p.relative_to(root).as_posix() != "manifest.json"}})
    return verify_campaign(root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    args = parser.parse_args()
    if not args.verify and not args.output: parser.error("--output or --verify is required")
    report = verify_campaign(args.verify) if args.verify else campaign(args.output)
    print(json.dumps(report, indent=2))
    if not report["verified"]: raise SystemExit(1)
