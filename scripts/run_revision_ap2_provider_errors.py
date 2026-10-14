"""Freeze, run and verify the AP2 prospective provider-failure campaign."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from evaluation.artifact_io import write_json
from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_archives import verify_files
from evaluation.r4_common import environment
from evaluation.revision_ap2_provider_errors import CONDITIONS, trial, verify_trial
from scripts.run_r2_sdk_recovery import snapshot_sources

PROTOCOL = ROOT / "docs/revision/revision-ap2-provider-errors-protocol.md"
SCHEMA = "revision-ap2-provider-errors-v2"


def specification():
    return {"schema": SCHEMA, "conditions": list(CONDITIONS), "repetitions": 3,
        "preparation_timeout_ms": 1_000, "single_host": True,
        "physical_execution": False, "automatic_state_changing_retries": False,
        "provider_stop_failure_reasons": ["transport", "timeout"]}


def verify(directory):
    root = Path(directory).resolve(strict=True)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"] != SCHEMA:
        raise ValueError("Unknown AP2 archive")
    verify_files(root, manifest["files"], excluded=("manifest.json",))
    frozen = json.loads((root / "freeze.json").read_text(encoding="utf-8"))
    if frozen["schema"] != SCHEMA or set(frozen["inputs"]) != {"specification.json", "protocol.md", "environment.json", "source-snapshot.zip"}:
        raise ValueError("Invalid AP2 frozen inputs")
    for name, digest in frozen["inputs"].items():
        if file_sha256(root / name) != digest:
            raise ValueError("Changed AP2 frozen input")
    spec = json.loads((root / "specification.json").read_text(encoding="utf-8"))
    if spec != specification():
        raise ValueError("AP2 specification differs from the prospective protocol")
    rows = [verify_trial(root / condition / f"trial-{index:02d}") for condition in spec["conditions"] for index in range(spec["repetitions"])]
    return {"schema": SCHEMA, "verified": all(row["verified"] for row in rows), "trial_count": len(rows), "trials": rows,
        "independent_effect_observation": True, "physical_execution": False, "durable_controller_state": False}


def run(directory):
    root = Path(directory).resolve()
    root.mkdir(parents=True, exist_ok=False)
    spec = specification()
    write_json(root / "specification.json", spec)
    (root / "protocol.md").write_bytes(PROTOCOL.read_bytes())
    write_json(root / "environment.json", environment())
    snapshot_sources(root)
    # This prospective study starts remote/testbed subprocesses. Include those
    # dependencies without modifying any earlier frozen snapshot mechanism.
    with zipfile.ZipFile(root / "source-snapshot.zip", "a", zipfile.ZIP_DEFLATED) as archive:
        present = set(archive.namelist())
        for folder in ("demos", "twins", "remote", "testbed", "deployments"):
            for source in sorted((ROOT / folder).rglob("*")):
                name = source.relative_to(ROOT).as_posix()
                if source.is_file() and source.suffix in {".py", ".json"} and name not in present:
                    archive.write(source, name)
                    present.add(name)
        if (ROOT / "pyproject.toml").is_file() and "pyproject.toml" not in present:
            archive.write(ROOT / "pyproject.toml", "pyproject.toml")
    names = ("specification.json", "protocol.md", "environment.json", "source-snapshot.zip")
    write_json(root / "freeze.json", {"schema": SCHEMA, "frozen_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {name: file_sha256(root / name) for name in names}})
    for condition in spec["conditions"]:
        for index in range(spec["repetitions"]):
            row = trial(root / condition / f"trial-{index:02d}", condition)
            print(f"{condition} {index + 1}/{spec['repetitions']}: verified={row['verified']}", flush=True)
    # Finalize once. Verification is regenerated offline without mutation.
    rows = [verify_trial(root / condition / f"trial-{index:02d}") for condition in spec["conditions"] for index in range(spec["repetitions"])]
    report = {"schema": SCHEMA, "verified": all(row["verified"] for row in rows), "trial_count": len(rows), "trials": rows,
        "independent_effect_observation": True, "physical_execution": False, "durable_controller_state": False}
    write_json(root / "verification.json", report)
    write_json(root / "manifest.json", {"schema": SCHEMA,
        "files": {path.relative_to(root).as_posix(): file_sha256(path) for path in sorted(root.rglob("*")) if path.is_file() and path.name != "manifest.json"}})
    if verify(root) != report:
        raise ValueError("AP2 offline verification differs")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    report = verify(args.directory) if args.verify_only else run(args.directory)
    print(json.dumps(report, indent=2))
    return 0 if report["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
