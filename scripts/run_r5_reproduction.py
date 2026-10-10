"""Reproduce bounded revision evidence from a clean local source checkout.

Never sends LLM/provider requests, changes branches, or publishes artifacts.
Uses the invoking Python environment, which is recorded rather than described
as an independently installed environment. Original evidence is read only.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = "f5802a3d1c2695637a5840ab5ed94d46ce64063c"


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(output, commit=CHECKPOINT):
    output = Path(output).resolve()
    if not output.is_relative_to((ROOT / ".cp2n2").resolve()):
        raise ValueError("reproduction outputs must be inside repository .cp2n2")
    output.mkdir(parents=True, exist_ok=False)
    checkout = output / "checkout"
    git = shutil.which("git")
    resolved = subprocess.check_output([git, "rev-parse", f"{commit}^{{commit}}"], cwd=ROOT, text=True).strip()
    subprocess.run([git, "clone", "--no-hardlinks", "--no-checkout", str(ROOT), str(checkout)], check=True)
    subprocess.run([git, "checkout", "--detach", resolved], cwd=checkout, check=True)
    if subprocess.check_output([git, "status", "--porcelain"], cwd=checkout, text=True).strip():
        raise RuntimeError("source checkout is not clean")
    if (checkout / ".env").exists():
        raise RuntimeError("credentials present in reproduction checkout")
    shutil.copy2(__file__, output / "orchestration-source.py")
    environment = {key: value for key, value in os.environ.items()
                   if not any(token in key.upper() for token in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"))}
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    write(output / "environment.json", {
        "started_at": datetime.now(timezone.utc).isoformat(), "source_commit": resolved,
        "python": sys.version, "python_executable": sys.executable, "platform": platform.platform(),
        "packages": {name: version(name) for name in ("mcp", "pydantic", "cl-sdk", "pytest", "tables", "numpy")},
        "clean_source_checkout": True, "existing_python_environment_reused": True,
        "same_physical_host": True, "independent_coauthor_reproduction": False,
        "llm_requests": 0, "physical_substrate_runs": 0,
    })
    originals = [
        ("r2", "run_r2_sdk_recovery.py", "r2-recovery-confirmatory-20261009-01"),
        ("r3-direct", "run_r3_enforcement.py", "r3-direct-confirmatory-20261010-01"),
        ("r3-state", "run_r3_state_exploration.py", "r3-state-confirmatory-20261010-01"),
        ("r3-reference", "run_r3_agent_campaign.py", "r3-agent-reference-20261010-01"),
        ("r3-live", "run_r3_agent_campaign.py", "r3-agent-live-qwen-20261010-01"),
        *[(f"r4-{kind}", "run_r4_evaluation.py", f"r4-{kind}-confirmatory-20261010-01")
          for kind in ("selection", "contention", "overhead", "transport")],
        ("r4-container", "run_r4_container_evaluation.py", "r4-container-confirmatory-20261010-01"),
    ]
    jobs = [(f"verify-{name}", [sys.executable, "scripts/" + script, "--verify", str(ROOT / ".cp2n2" / archive)])
            for name, script, archive in originals]
    jobs += [
        ("tests", [sys.executable, "-m", "pytest", "-q", "--basetemp", str(output / "pytest")]),
        ("reproduce-r2", [sys.executable, "scripts/run_r2_sdk_recovery.py", "--output", str(output / "r2")]),
        ("reproduce-r3-direct", [sys.executable, "scripts/run_r3_enforcement.py", "--output", str(output / "r3-direct")]),
        ("reproduce-r3-state", [sys.executable, "scripts/run_r3_state_exploration.py", "--output", str(output / "r3-state")]),
        ("reproduce-r3-reference", [sys.executable, "scripts/run_r3_agent_campaign.py", "--protocol-version", "v1", "--output", str(output / "r3-reference")]),
        *[(f"reproduce-r4-{kind}", [sys.executable, "scripts/run_r4_evaluation.py", "--kind", kind,
                                   "--output", str(output / f"r4-{kind}")])
          for kind in ("selection", "contention", "transport")],
    ]
    write(output / "jobs.json", {"jobs": [{"id": name, "command": command} for name, command in jobs]})
    results = []
    for name, command in jobs:
        print(f"START {name}", flush=True)
        started = time.monotonic()
        log = output / f"{name}.log"
        with log.open("w", encoding="utf-8") as stream:
            process = subprocess.run(command, cwd=checkout, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        results.append({"id": name, "exit_code": process.returncode, "elapsed_s": time.monotonic() - started,
                        "log_sha256": hashlib.sha256(log.read_bytes()).hexdigest()})
        write(output / "progress.json", {"completed": results, "verified": all(row["exit_code"] == 0 for row in results)})
        print(f"END {name}: exit={process.returncode}", flush=True)
        if process.returncode:
            raise RuntimeError(f"retained reproduction failure: {name}; inspect its log before rerunning")
    final_clean = not subprocess.check_output([git, "status", "--porcelain"], cwd=checkout, text=True).strip()
    write(output / "verification.json", {"verified": final_clean and all(row["exit_code"] == 0 for row in results),
        "jobs": results, "source_commit": resolved, "source_checkout_clean_at_end": final_clean,
        "independent_coauthor_reproduction": False, "fresh_environment_installation": False,
        "new_live_llm_observations": 0, "new_physical_observations": 0,
        "original_overhead_recomputed_not_remeasured": True,
        "original_container_archive_verified_not_rerun": True})
    print(f"Reproduction verified: {len(results)} jobs; clean checkout={final_clean}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", default=CHECKPOINT)
    args = parser.parse_args()
    run(args.output, args.commit)
