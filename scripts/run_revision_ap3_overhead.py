"""Freeze/run new AP3 overhead campaign, verify it, or report old R4 CIs offline."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.revision_ap3_overhead import freeze, report_r4, run, specification, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", type=Path)
    mode.add_argument("--report-r4", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--development", action="store_true",
                        help="Unscored smoke run with reduced denominators, explicitly labeled development")
    args = parser.parse_args()
    if args.verify:
        report = verify(args.verify)
    elif args.report_r4:
        if not args.output:
            parser.error("--report-r4 requires a separate --output directory")
        report = report_r4(args.report_r4, args.output)
    else:
        if not args.output:
            parser.error("new campaign requires explicit --output directory")
        spec = (specification(development=True, observations=4, repetitions=2, warmup=2)
                if args.development else specification())
        root = freeze(args.output, spec)
        report = run(root, spec)
    print(json.dumps(report, indent=2))
    if not report.get("verified", report.get("source_verified", False)):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
