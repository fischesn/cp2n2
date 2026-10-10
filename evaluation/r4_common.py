"""Frozen R4 inputs and verifiable raw-artifact packaging."""
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

from evaluation.biopattern_gate_native import file_sha256
from evaluation.r3_archives import verify_files
from runtimes.biopattern_gate_sdk_runtime import write_json
from scripts.run_r2_sdk_recovery import snapshot_sources

ROOT = Path(__file__).resolve().parents[1]


def environment():
    result={"python":sys.version,"platform":platform.platform(),"processor":platform.processor(),
        "logical_cpus":os.cpu_count(),"timer":"perf_counter_ns",
        "packages":{p:version(p) for p in ("mcp","pydantic","requests","matplotlib","numpy")},
        "git_commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
        "git_dirty":bool(subprocess.check_output(["git","status","--porcelain"],cwd=ROOT,text=True)),
        "single_environment":True}
    if platform.system()=="Windows":
        for key,command in (("cpu","Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,NumberOfLogicalProcessors | ConvertTo-Json -Compress"),
                            ("memory","Get-CimInstance Win32_ComputerSystem | Select-Object TotalPhysicalMemory | ConvertTo-Json -Compress")):
            try:
                result[key]=json.loads(subprocess.check_output(["powershell","-NoProfile","-Command",command],text=True,timeout=10))
            except (subprocess.SubprocessError,OSError,ValueError): result[key]={"available":False}
    return result


def freeze(directory, kind, specification):
    root=Path(directory).resolve(); root.mkdir(parents=True,exist_ok=False)
    write_json(root/"specification.json",specification)
    (root/"protocol.md").write_bytes((ROOT/"docs/revision/r4-protocol.md").read_bytes())
    write_json(root/"environment.json",environment())
    snapshot_sources(root)
    names=("specification.json","protocol.md","environment.json","source-snapshot.zip")
    write_json(root/"freeze.json",{"schema":"r4-freeze-v1","kind":kind,
        "frozen_at":datetime.now(timezone.utc).isoformat(),"inputs":{n:file_sha256(root/n) for n in names}})
    return root


def finish(root, report):
    root=Path(root)
    write_json(root/"verification.json",report)
    write_json(root/"manifest.json",{"schema":"r4-archive-v1",
        "files":{p.relative_to(root).as_posix():file_sha256(p) for p in sorted(root.rglob("*"))
                 if p.is_file() and p.relative_to(root).as_posix()!="manifest.json"}})


def check(root):
    root=Path(root).resolve(strict=True)
    manifest=json.loads((root/"manifest.json").read_text(encoding="utf-8"))
    if manifest["schema"]!="r4-archive-v1": raise ValueError("unknown R4 archive schema")
    verify_files(root,manifest["files"],excluded=("manifest.json",))
    frozen=json.loads((root/"freeze.json").read_text(encoding="utf-8"))
    if frozen["schema"]!="r4-freeze-v1": raise ValueError("unknown R4 freeze")
    if set(frozen["inputs"])!={"specification.json","protocol.md","environment.json","source-snapshot.zip"}:
        raise ValueError("R4 frozen input inventory changed")
    if frozen["kind"] not in ("selection","contention","overhead","transport"):
        raise ValueError("unknown R4 kind")
    for name,digest in frozen["inputs"].items():
        if file_sha256(root/name)!=digest: raise ValueError("pre-run R4 input mismatch")
    return root,json.loads((root/"specification.json").read_text(encoding="utf-8"))
