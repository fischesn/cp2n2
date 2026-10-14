"""Package frozen supplementary evidence; verify archives without new observations.

This script has no Zenodo API, network, experiment runner, or production caller.
Publication is a separate, explicitly authorized step. No frozen input is edited.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from urllib.parse import quote
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DATE = (2026, 10, 14, 0, 0, 0)
PACKAGE_NAME = "cp2n2-supplementary-2026-10-14-public-evidence.zip"
MANIFEST_NAME = "SUPPLEMENTARY-PACKAGE-MANIFEST.json"
CAMPAIGNS = (
    "ap1-required-evidence-confirmatory-20261014-01",
    "ap2-provider-errors-confirmatory-20261014-01",
    "ap3-overhead-confirmatory-20261014-01",
    "gemini-selector-confirmatory-20261014-01",
)
DEVELOPMENT = (
    "revision-ap2-development-20261014-b",
    "revision-ap2-development-20261014-c",
)
OFFLINE_EXTENSION = "ap3-r4-offline-20261014-01"
DOCUMENTS = (
    "docs/revision/ap1-validation-protocol.md",
    "docs/revision/revision-ap2-provider-errors-protocol.md",
    "docs/revision/ap3-overhead-protocol.md",
    "docs/revision/ap1-ap3-results.md",
    "docs/revision/ap3-overhead-results.md",
    "docs/revision/ap1-ap3-source-freeze.json",
    "docs/revision/ap1-ap3-evidence-index.json",
    "docs/revision/gemini-selector-campaign-protocol.md",
    "docs/revision/gemini-selector-results.md",
    "docs/revision/gemini-selector-evidence-index.json",
    "docs/revision/gemini-selector-approval.json",
    "docs/revision/supplementary-paper-integration.md",
)
CREDENTIAL_KEY = re.compile(
    r"^(?:(?:[a-z0-9]+_)*(?:api_key|access_token|auth_token|refresh_token|"
    r"client_secret|password|private_key|authorization|cookie|secret_key|"
    r"credentials|credential))$", re.I
)
BUDGET_KEY = re.compile(r"(?:budget|cost|currency|price|funding|financial)", re.I)
MAX_EXPANDED_BYTES = 512 * 1024 * 1024


def sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def json_bytes(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def load_json(content: bytes):
    # Raw experiments deliberately contain NaN fixtures. Do not rewrite them.
    return json.loads(content.decode("utf-8-sig"), object_pairs_hook=_pairs)


def safe_name(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise ValueError("invalid public relative path")
    parts = name.split("/")
    if (name.startswith("/") or any(p in ("", ".", "..") for p in parts)
            or any(":" in p for p in parts) or PurePosixPath(name).is_absolute()):
        raise ValueError("unsafe public relative path")
    for part in parts:
        lower = part.lower()
        if (lower in {".git", ".aws", ".venv", "__pycache__"}
                or lower.startswith(".env") or lower.endswith((".pem", ".key"))):
            raise ValueError("private environment or credential file excluded")
    return name


def zip_members(content: bytes) -> dict[str, bytes]:
    result = {}
    folded = set()
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            name = safe_name(info.filename)
            # Windows case aliases and symbolic links are not publication files.
            if name.casefold() in folded or ((info.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("duplicate or symbolic-link archive member")
            if info.file_size > MAX_EXPANDED_BYTES:
                raise ValueError("archive expansion limit")
            result[name] = archive.read(info)
            folded.add(name.casefold())
    if sum(map(len, result.values())) > MAX_EXPANDED_BYTES:
        raise ValueError("archive expansion limit")
    return result


def deterministic_zip(files: dict[str, bytes]) -> bytes:
    target = io.BytesIO()
    folded = set()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            safe_name(name)
            if name.casefold() in folded:
                raise ValueError("case-alias duplicate")
            info = zipfile.ZipInfo(name, DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, files[name], compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
            folded.add(name.casefold())
    return target.getvalue()


def known_credentials(root: Path) -> tuple[bytes, ...]:
    """Read only credential-like .env values in memory, never return/print names.

    No .env bytes or secret hashes enter any public file. An absent local .env
    still permits verification by recipients, using structural credential checks.
    """
    source = root / ".env"
    if not source.exists():
        return ()
    from dotenv import dotenv_values
    values = dotenv_values(source, interpolate=False)
    result = set()
    for key, value in values.items():
        if value and CREDENTIAL_KEY.fullmatch(key):
            raw = value.encode("utf-8")
            result.update((raw, base64.b64encode(raw), quote(value, safe="").encode("utf-8")))
    return tuple(sorted(result))


def _is_placeholder(value) -> bool:
    if value is None or value is False or value == "":
        return True
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return (stripped.startswith("${") and stripped.endswith("}")) or stripped.lower() in {
        "redacted", "<redacted>", "your-api-key", "your_api_key", "example", "placeholder"
    }


def scan_public_files(files: dict[str, bytes], *, known=()) -> dict:
    """Fail closed for credentials; count budget fields without changing data.

    Financial/cost fixture values are legitimate selector inputs. This scan
    reports their presence rather than silently redacting scientific evidence.
    """
    budgets = Counter()
    inspected = 0
    expanded = 0

    def walk_json(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if CREDENTIAL_KEY.fullmatch(key) and not _is_placeholder(child):
                    raise ValueError("credential-valued field present in publication input")
                if BUDGET_KEY.search(key):
                    budgets[key] += 1
                walk_json(child, path)
        elif isinstance(value, list):
            for child in value:
                walk_json(child, path)

    def walk_blob(name, content, depth):
        nonlocal inspected, expanded
        safe_name(name)
        inspected += 1
        expanded += len(content)
        if expanded > MAX_EXPANDED_BYTES or depth > 4:
            raise ValueError("recursive publication scan limit")
        if any(secret and secret in content for secret in known):
            raise ValueError("known private credential detected in publication input")
        lower = name.lower()
        if lower.endswith(".zip"):
            for inner, data in zip_members(content).items():
                walk_blob(inner, data, depth + 1)
        elif lower.endswith(".json"):
            walk_json(load_json(content), name)
        elif lower.endswith(".jsonl"):
            for line in content.splitlines():
                if line.strip():
                    walk_json(load_json(line), name)

    for name, content in sorted(files.items()):
        walk_blob(name, content, 0)
    return {"credential_scan_passed": True, "known_credentials_not_published": True,
            "recursive_blobs_checked": inspected, "expanded_bytes_checked": expanded,
            "budget_field_counts": dict(sorted(budgets.items())),
            "financial_values_redacted": False,
            "scan_scope": "recursive JSON/JSONL credential fields and raw known credential encodings; no .env packaged"}


def read_tree(directory: Path) -> dict[str, bytes]:
    if not directory.is_dir() or directory.is_symlink():
        raise ValueError("archive directory missing or symbolic link")
    result = {}
    for path in sorted(directory.rglob("*")):
        if path.is_symlink():
            raise ValueError("symbolic link in publication input")
        if path.is_file():
            result[safe_name(path.relative_to(directory).as_posix())] = path.read_bytes()
    return result


def verify_campaign_bytes(files: dict[str, bytes]) -> dict:
    manifest = load_json(files["manifest.json"])
    expected = manifest["files"]
    if set(expected) != set(files) - {"manifest.json"}:
        raise ValueError("campaign manifest inventory differs")
    for name, digest in expected.items():
        safe_name(name)
        if sha256(files[name]) != digest:
            raise ValueError("campaign output hash differs")
    freeze = load_json(files["freeze.json"])
    for name, digest in freeze["inputs"].items():
        safe_name(name)
        if sha256(files[name]) != digest:
            raise ValueError("campaign frozen input hash differs")
    return {"schema": manifest["schema"], "file_count": len(files),
            "manifest_sha256": sha256(files["manifest.json"]),
            "freeze_sha256": sha256(files["freeze.json"]),
            "source_snapshot_sha256": sha256(files["source-snapshot.zip"])}


def normalized_hash(content: bytes) -> str:
    text = content.decode("utf-8")
    return sha256(text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8"))


def source_binding(files: dict[str, bytes], original: dict[str, str], *, gemini=False) -> dict:
    members = zip_members(files["source-snapshot.zip"])
    if gemini:
        receipt = load_json(files["freeze.json"])
        wanted = receipt["source_files"]
        if len(wanted) != 295 or wanted != load_json(files["source-hashes.json"]):
            raise ValueError("Gemini source inventory differs")
        if not all(wanted.get(name) == digest for name, digest in original.items()):
            raise ValueError("Gemini changed original functional source")
    else:
        wanted = original
    if set(members) != set(wanted):
        raise ValueError("source archive inventory differs")
    for name, digest in wanted.items():
        if normalized_hash(members[name]) != digest:
            raise ValueError("normalized scientific source identity differs")
    return {"source_files": len(wanted), "original_unchanged_source_files": len(original),
            "source_identity": "normalized archived file SHA-256 values, not base Git commit"}


def build_files(root: Path) -> tuple[dict[str, bytes], dict]:
    freeze = load_json((root / "docs/revision/ap1-ap3-source-freeze.json").read_bytes())
    original = freeze["source_files"]
    if len(original) != 290:
        raise ValueError("unexpected coordinated source freeze size")
    files = {}
    bindings = {}
    for name in CAMPAIGNS + DEVELOPMENT:
        raw = read_tree(root / ".cp2n2" / name)
        receipt = verify_campaign_bytes(raw)
        if name in CAMPAIGNS:
            receipt.update(source_binding(raw, original, gemini=name.startswith("gemini")))
        else:
            receipt["classification"] = "unscored development evidence; not included in confirmatory totals"
        bindings[name] = receipt
        prefix = "campaigns" if name in CAMPAIGNS else "development"
        files.update({f"{prefix}/{name}/{entry}": content for entry, content in raw.items()})
    for name, content in read_tree(root / ".cp2n2" / OFFLINE_EXTENSION).items():
        files[f"historical-analysis/{OFFLINE_EXTENSION}/{name}"] = content
    # These snapshots are current interpretation documents, not modified frozen protocols.
    for name in DOCUMENTS:
        files[f"documentation/{name}"] = (root / name).read_bytes()
    for path in sorted((root / "docs/revision/gemini-selector-blind-v1").iterdir()):
        if path.is_file():
            files[f"documentation/docs/revision/gemini-selector-blind-v1/{safe_name(path.name)}"] = path.read_bytes()
    files["LICENSE"] = (root / "LICENSE").read_bytes()
    files["requirements-evaluation.txt"] = (root / "requirements-evaluation.txt").read_bytes()
    files["tools/prepare_supplementary_zenodo.py"] = (root / "scripts/prepare_supplementary_zenodo.py").read_bytes()
    files["README.md"] = README.encode("utf-8")
    metadata = {"campaign_bindings": bindings,
                "scientific_source_base_git_commit": freeze["base_git_commit"],
                "scientific_source_was_uncommitted": freeze["working_tree_dirty"],
                "scientific_source_identity": freeze["source_identity"],
                "new_observations_during_packaging": False,
                "new_provider_or_model_calls_during_packaging": False,
                "physical_substrate_execution": False}
    return files, metadata


README = """# CP2N2 supplementary frozen evidence — 14 October 2026

This additive supplement contains the complete raw AP1, AP2, AP3 and externally
authored Gemini selector archives, their frozen inputs, original reports,
manifests, audit records, observations and exact source-snapshot ZIP bytes.
It does not replace the earlier R2–R5 record. No physical substrate was run.
Packaging and public verification make no new measurements or model/provider calls.

## Contents and interpretation

- AP1: 46 ordinary trials and four detector controls; 120 MCP calls, 240 audit events.
- AP2: 18 prospective separate-process TCP trials. Structured failures and explicit
  healthy-alternative recovery are not persistent restart or automatic invoke retry.
- AP3: 80 trial summaries, 32,000 measured and 3,200 warm-up observations. Intervals
  summarize repeated-trial median/p95 statistics, not population extreme tails.
- Gemini: 12 externally authored synthetic cases, three policies, two input orders;
  72/72 matching cells and 36/36 order pairs. These are not 72 independent workloads.
- `development/` preserves the AP2 v1 negative classifier evidence and subsequent
  v2 development run, separately from confirmatory denominators. The provider-stop
  classifier was broadened from transport-only to transport-or-timeout before
  confirmation; the original negative evidence is retained unchanged.
- `historical-analysis/` contains only confidence-interval summaries read
  from the already published R4 archive, with its original receipt hashes.
- `documentation/` includes interpretation snapshots, protocols and provenance.

The AP1–AP3 source archives bind 290 normalized source files. The Gemini archive
binds 295 files and the unchanged original 290-file subset. The recorded base Git
commit is background provenance, not the identity of this uncommitted evaluated
source. Archived per-file hashes identify the scientific source. Source ZIP bytes
are retained even where their internal timestamps/newline conventions differ.
The historical pending fields in the Gemini intake describe the receipt-time
state; the separate author approval and scored campaign freeze supersede them.

## Offline verification

Use a Python environment with the archived requirements and evaluation dependencies.
Run this command against the downloaded ZIP, with a fresh extraction directory:

```
python -B tools/prepare_supplementary_zenodo.py --verify downloaded-evidence.zip --extract fresh-verification-directory
```

The helper verifies all public hashes and frozen input/output/source bindings,
then extracts the Gemini 295-file source snapshot into the fresh directory and
runs the four archived verifier CLIs in offline verification mode. No live source,
new experiment, production observation, or API key is required. The archived
development v1 classifier is retained as evidence, not silently re-scored by v2.

Scientific synthetic cost/budget values are preserved; no arbitrary financial
redaction is applied. Credentials and local environment files are excluded, and
recursive structured-field/known-credential checks precede packaging. Software
source licensing is specified by `LICENSE`; the Zenodo record governs dataset
licensing. Follow original archive documentation for the scope of each claim.
"""


def prepare(root: Path, output: Path) -> dict:
    root, output = root.resolve(strict=True), output.resolve()
    allowed = (root / ".cp2n2").resolve()
    if not output.is_relative_to(allowed) or output == allowed or output.exists():
        raise ValueError("publication output must be a fresh directory beneath .cp2n2")
    files, metadata = build_files(root)
    scan = scan_public_files(files, known=known_credentials(root))
    manifest = {"schema": "cp2n2-supplementary-public-package-v1", **metadata,
                "files": {name: sha256(content) for name, content in sorted(files.items())},
                "credential_and_budget_scan": scan,
                "preserved_raw_bytes": True,
                "outer_zip_timestamp": "2026-10-14T00:00:00; deterministic metadata"}
    files[MANIFEST_NAME] = json_bytes(manifest)
    package = deterministic_zip(files)
    # Re-read generated container before publication output is created.
    if zip_members(package) != files:
        raise ValueError("generated ZIP does not preserve original bytes")
    output.mkdir(parents=True, exist_ok=False)
    (output / PACKAGE_NAME).write_bytes(package)
    receipt = {"schema": "cp2n2-supplementary-package-preparation-v1",
               "archive": PACKAGE_NAME, "sha256": sha256(package),
               "bytes": len(package), "file_count": len(files),
               "manifest_sha256": sha256(files[MANIFEST_NAME]), **metadata,
               "crc_and_payload_hashes_verified": True,
               "originals_unchanged": True, "credential_scan_passed": True,
               "credential_and_budget_scan": scan}
    (output / "SUPPLEMENTARY-PACKAGE-VERIFICATION.json").write_bytes(json_bytes(receipt))
    return receipt


def extract_files(files: dict[str, bytes], target: Path):
    target.mkdir(parents=True, exist_ok=False)
    for name, content in files.items():
        safe_name(name)
        path = target / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def verify_public(package: Path, extract: Path, *, python=sys.executable) -> dict:
    package = package.resolve(strict=True)
    extract = extract.resolve()
    if extract.exists():
        raise ValueError("public verification extraction target must be fresh")
    files = zip_members(package.read_bytes())
    manifest = load_json(files[MANIFEST_NAME])
    if manifest.get("schema") != "cp2n2-supplementary-public-package-v1":
        raise ValueError("unknown supplementary public package")
    if set(manifest["files"]) != set(files) - {MANIFEST_NAME}:
        raise ValueError("public package inventory differs")
    for name, digest in manifest["files"].items():
        if sha256(files[name]) != digest:
            raise ValueError("public package hash differs")
    scan_public_files(files)
    original = load_json(files["documentation/docs/revision/ap1-ap3-source-freeze.json"])["source_files"]
    if len(original) != 290:
        raise ValueError("public source freeze inventory differs")
    for name in CAMPAIGNS + DEVELOPMENT:
        folder = "campaigns" if name in CAMPAIGNS else "development"
        prefix = f"{folder}/{name}/"
        raw = {entry[len(prefix):]: content for entry, content in files.items() if entry.startswith(prefix)}
        verify_campaign_bytes(raw)
        if name in CAMPAIGNS:
            source_binding(raw, original, gemini=name.startswith("gemini"))
    extract_files(files, extract)
    source_bytes = files[f"campaigns/{CAMPAIGNS[3]}/source-snapshot.zip"]
    source = extract / "offline-source"
    extract_files(zip_members(source_bytes), source)
    commands = (
        ("scripts/run_revision_ap1_evidence.py", "--verify", extract / "campaigns" / CAMPAIGNS[0]),
        ("scripts/run_revision_ap2_provider_errors.py", "--directory", extract / "campaigns" / CAMPAIGNS[1], "--verify-only"),
        ("scripts/run_revision_ap3_overhead.py", "--verify", extract / "campaigns" / CAMPAIGNS[2]),
        ("scripts/run_revision_gemini_selector.py", "--verify", extract / "campaigns" / CAMPAIGNS[3]),
    )
    reports = {}
    records = []
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for name, command in zip(CAMPAIGNS, commands, strict=True):
        argv = [str(python), "-B", str(source / command[0]), *(str(arg) for arg in command[1:])]
        result = subprocess.run(argv, cwd=source, env=environment, capture_output=True,
                                text=True, encoding="utf-8", timeout=120)
        if result.returncode:
            # Never echo raw subprocess output which could contain unforeseen secrets.
            raise ValueError(f"archived offline verifier failed: {name}")
        report = json.loads(result.stdout, object_pairs_hook=_pairs)
        if not report.get("verified", report.get("passed", False)):
            raise ValueError(f"archived offline verifier did not pass: {name}")
        reports[name] = report
        records.append({"name": name, "classification": "confirmatory",
                        "exit_code": result.returncode, "verified": True,
                        "archived_offline_cli": command[0]})
    receipt = {"schema": "cp2n2-supplementary-public-offline-verification-v1",
               "package_sha256": sha256(package.read_bytes()),
               "source_snapshot_sha256": sha256(source_bytes),
               "all_four_archived_offline_verifiers_passed": True,
               "verified": True, "campaigns": records,
               "live_source_used": False, "new_observations": False,
               "new_provider_or_model_calls": False, "reports": reports}
    scan_public_files({"verification.json": json_bytes(receipt)})
    (extract / "SUPPLEMENTARY-CAMPAIGN-VERIFICATION.json").write_bytes(json_bytes(receipt))
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--output", type=Path)
    modes.add_argument("--verify", type=Path)
    parser.add_argument("--extract", type=Path)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    if args.verify:
        if not args.extract:
            parser.error("--verify requires a fresh --extract directory")
        receipt = verify_public(args.verify, args.extract, python=args.python)
        print(json.dumps({key: value for key, value in receipt.items() if key != "reports"}, indent=2))
    else:
        receipt = prepare(args.root, args.output)
        print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
