"""Verify every original campaign from an extracted public evidence archive.

No fresh measurements, LLM calls, container runs or physical runs are made.
Logs and the verification receipt live outside the immutable evidence ZIP.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGNS = [
    ("r2", "run_r2_sdk_recovery.py", "r2-recovery-confirmatory-20261009-01"),
    ("r3-direct", "run_r3_enforcement.py", "r3-direct-confirmatory-20261010-01"),
    ("r3-state", "run_r3_state_exploration.py", "r3-state-confirmatory-20261010-01"),
    ("r3-reference", "run_r3_agent_campaign.py", "r3-agent-reference-20261010-01"),
    ("r3-live", "run_r3_agent_campaign.py", "r3-agent-live-qwen-20261010-01"),
    *[("r4-" + k, "run_r4_evaluation.py", "r4-" + k + "-confirmatory-20261010-01")
      for k in ("selection", "contention", "overhead", "transport")],
    ("r4-container", "run_r4_container_evaluation.py", "r4-container-confirmatory-20261010-01"),
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract_checked(archive, destination):
    for info in archive.infolist():
        if not (destination / info.filename).resolve().is_relative_to(destination.resolve()):
            raise ValueError("Archive traversal")
    if archive.testzip() is not None:
        raise ValueError("Archive CRC mismatch")
    archive.extractall(destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    args = parser.parse_args()
    base = args.package_dir.resolve(strict=True)
    if not base.is_relative_to((ROOT / ".cp2n2").resolve()):
        raise ValueError("Package must be under repository .cp2n2")
    report = json.loads((base / "PUBLIC-PACKAGE-VERIFICATION.json").read_text(encoding="utf-8"))
    package = base / report["archive"]
    if sha(package.read_bytes()) != report["sha256"]:
        raise ValueError("Package hash mismatch")
    work = base / "public-verification"
    work.mkdir(exist_ok=False)
    extracted = work / "extracted"
    extracted.mkdir()
    with zipfile.ZipFile(package) as archive:
        manifest = json.loads(archive.read("PUBLIC-EVIDENCE-MANIFEST.json"))
        for name, item in manifest["files"].items():
            if sha(archive.read(name)) != item["sha256"]:
                raise ValueError("Public manifest mismatch: " + name)
        extract_checked(archive, extracted)
    source = work / "source"
    source.mkdir()
    with zipfile.ZipFile(extracted / "cp2n2-evaluation-source.zip") as archive:
        extract_checked(archive, source)
    environment = {k: v for k, v in os.environ.items()
                   if not any(t in k.upper() for t in ("TOKEN", "API_KEY", "SECRET", "PASSWORD"))}
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    results = []
    for label, script, directory in CAMPAIGNS:
        log = work / (label + ".log")
        print("VERIFY " + label, flush=True)
        command = [sys.executable, "-B", "scripts/" + script, "--verify", str(extracted / "evidence" / directory)]
        with log.open("w", encoding="utf-8", newline="\n") as stream:
            completed = subprocess.run(command, cwd=source, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        if completed.returncode:
            raise RuntimeError("Public verification failed: " + label + "; inspect " + str(log))
        results.append({"campaign": label, "exit_code": completed.returncode,
                        "log_sha256": sha(log.read_bytes())})
    # Verification is read-only: validate all unpacked immutable payloads again.
    for name, item in manifest["files"].items():
        if sha((extracted / name).read_bytes()) != item["sha256"]:
            raise ValueError("Verifier changed archived payload: " + name)
    live = json.loads((extracted / "evidence/r3-agent-live-qwen-20261010-01/verification.json").read_text(encoding="utf-8"))
    if (live["planner_conformant"], live["permitted_completions"], live["case_forbidden_effects"]) != (24, 6, 0):
        raise ValueError("Unexpected executing Qwen results")
    result = {"schema": "cp2n2-r5-public-verification-v1", "verified": True,
              "archive_sha256": report["sha256"], "campaigns": results,
              "evaluated_source_commit": manifest["evaluated_source_commit"],
              "scientific_payloads_unchanged_after_verification": True,
              "qwen_planner_matches": 24, "qwen_decisions": 32, "qwen_permitted_completions": 6,
              "new_llm_requests": 0, "new_physical_observations": 0,
              "independent_coauthor_reproduction": False}
    (base / "PUBLIC-CAMPAIGN-VERIFICATION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
