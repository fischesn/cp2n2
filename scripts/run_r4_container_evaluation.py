"""Build/freeze and run R4's separate-container extension, or verify offline."""
import argparse
import json
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.r4_container import prepare, run, trial, verify, repair_packaging, CONDITIONS
from evaluation.artifact_io import write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--repair-packaging", type=Path, help="Preserve and repair only a known nested source-manifest omission; never rerun measurements")
    parser.add_argument("--development-case", choices=(*CONDITIONS, "all"))
    args = parser.parse_args()
    if args.repair_packaging:
        report = repair_packaging(args.repair_packaging)
    elif args.verify:
        report = verify(args.verify)
    else:
        root, spec, image = prepare(args.output or ROOT / ".cp2n2" / f"r4-container-{uuid4()}")
        if args.development_case:
            rows = []
            for case in CONDITIONS if args.development_case == "all" else [args.development_case]:
                path = root / case / "trial-00"
                try:
                    row = trial(path, case, image, spec)
                    rows.append(row)
                    print(f"development {case}: effects={row['commits']}, expectation={row['expectation_matched']}", flush=True)
                except Exception as exc:
                    path.mkdir(parents=True, exist_ok=True)
                    write_json(path / "harness-failure.json", {"condition": case, "error_type": type(exc).__name__, "error": str(exc)})
                    raise
            report = {"development_only": True, "verified": all(row["expectation_matched"] for row in rows), "trials": rows}
            write_json(root / "development-results.json", report)
            print(json.dumps(report, indent=2))
            raise SystemExit(0 if report["verified"] else 1)
        run(root, spec, image)
        report = verify(root)
    print(json.dumps(report, indent=2))
    if not report.get("verified", report.get("expectation_matched", False)):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
