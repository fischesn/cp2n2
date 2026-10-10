"""Small archive helpers; no production admission/selection dependency."""
import hashlib
import json
from pathlib import Path
import zipfile

from evaluation.biopattern_gate_native import file_sha256
from mcp_surface.audit import JsonlHashChainAuditTrail


def check_audit_calls(root):
    root = Path(root)
    calls = json.loads((root / "calls.json").read_text(encoding="utf-8"))["calls"]
    events = JsonlHashChainAuditTrail(root / "audit.jsonl").events()
    if len(events) != 2 * len(calls): raise ValueError("unpaired MCP audit")
    for call in calls:
        pair = [e for e in events if e.request_id == call["response"]["request_id"]]
        if (len(pair) != 2 or [e.phase for e in pair] != ["received", "completed"] or
            any(e.tool != call["tool"] or e.principal_id != call["principal_id"] for e in pair) or
            pair[0].arguments != call["arguments"] or pair[0].argument_digest != call["argument_digest"] or
            (pair[1].outcome == "success") != call["response"]["ok"]): raise ValueError("MCP audit binding mismatch")
    return calls, events


def source_bindings(path):
    with zipfile.ZipFile(path) as archive:
        def digest(prefix):
            value = hashlib.sha256()
            names = sorted(n for n in archive.namelist() if n.startswith(prefix) and Path(n).suffix in {".py", ".json"})
            if not names: raise ValueError("application sources absent from snapshot")
            for name in names:
                content = archive.read(name).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
                value.update(name.removeprefix(prefix).encode() + b"\0" + content.encode() + b"\0")
            return value.hexdigest()
        result = {"application_source_sha256": digest("applications/biopattern_gate/"),
                  "sdk_application_source_sha256": digest("cl-apps/cp2n2-biopattern-gate/src/")}
        if digest("cl-apps/cp2n2-biopattern-gate/src/biopattern_gate/") != result["application_source_sha256"]:
            raise ValueError("SDK core differs from canonical application")
        return result


def verify_files(root, files, *, excluded=("manifest.json", "verification.json")):
    root = Path(root).resolve(strict=True)
    inventory = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()
                 and p.relative_to(root).as_posix() not in excluded}
    if inventory != set(files): raise ValueError("archive file inventory mismatch")
    for name, digest in files.items():
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or file_sha256(path) != digest: raise ValueError("archive checksum/path mismatch")
