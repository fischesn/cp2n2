"""Prepare a public R5 evidence copy; never uploads or edits original evidence.

Only provider-account budget metadata is redacted. Frozen trial payloads remain
byte-identical. Changed input manifests are rehashed and their original bytes
retained in a public provenance directory (which contains no budget values).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

from dotenv import dotenv_values

from package_r5_evidence import CHECKPOINT, scan

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_SHA256 = "df0895efe7964af7b6b58611d60e304170da68ecaef33cc1a07f11c6497ee7f8"
DOCUMENTATION_COMMIT = "d758e9e2a9d5f9b988015abbe54089d27d04a5b2"
VERSION = "R5-2026-10-10"
LIVE = "evidence/r3-agent-live-qwen-20261010-01/"
FINANCIAL_FIELDS = {"spend", "max_budget", "reset_schedule"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def zip_bytes(files: dict[str, bytes]) -> bytes:
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (2026, 10, 10, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    return stream.getvalue()


def provider_public(data: bytes) -> bytes:
    value = json.loads(data)
    budget = value.pop("budget")
    if not isinstance(budget, dict) or not set(budget).issubset(FINANCIAL_FIELDS):
        raise ValueError("Unexpected provider budget fields require review")
    value["budget_metadata_redacted_for_publication"] = True
    return encoded(value)


def financial_fields(value) -> bool:
    if isinstance(value, dict):
        return bool(FINANCIAL_FIELDS.intersection(value)) or any(financial_fields(v) for v in value.values())
    if isinstance(value, list):
        return any(financial_fields(v) for v in value)
    return False


def audit_public(files: dict[str, bytes], secrets: list[bytes]) -> int:
    count = 0
    for name, data in files.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name:
            raise ValueError("Unsafe archive member: " + name)
        scan(name, data)
        if any(secret in data for secret in secrets):
            raise ValueError("Known local credential found; content is not printed: " + name)
        count += 1
        if name.endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(data)) as nested:
                if nested.testzip() is not None:
                    raise ValueError("Nested ZIP CRC failure: " + name)
                count += audit_public({n: nested.read(n) for n in nested.namelist() if not n.endswith("/")}, secrets)
        elif name.endswith(".json") and financial_fields(json.loads(data)):
            raise ValueError("Provider financial metadata remains: " + name)
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original = args.candidate.resolve(strict=True)
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / ".cp2n2").resolve()) or output == (ROOT / ".cp2n2").resolve():
        raise ValueError("Output must be a new directory within .cp2n2")
    original_bytes = original.read_bytes()
    if sha(original_bytes) != CANDIDATE_SHA256:
        raise ValueError("Unexpected frozen candidate identity")
    with zipfile.ZipFile(io.BytesIO(original_bytes)) as archive:
        if archive.testzip() is not None:
            raise ValueError("Original candidate CRC failure")
        files = {n: archive.read(n) for n in archive.namelist() if not n.endswith("/")}
    prior = json.loads(files["R5-EVIDENCE-MANIFEST.json"])
    for name, item in prior["files"].items():
        if len(files[name]) != item["bytes"] or sha(files[name]) != item["sha256"]:
            raise ValueError("Original candidate payload mismatch: " + name)
    original_payload = dict(files)
    changes = []

    def replace(name, data, reason):
        before = files[name]
        files[name] = data
        changes.append({"path": name, "action": "replace", "reason": reason,
                        "original_sha256": sha(before), "public_sha256": sha(data)})

    for name in ("budget-after.json", "budget-checks.json"):
        path = LIVE + name
        changes.append({"path": path, "action": "omit", "reason": "Private provider account/budget metadata, not scientific results",
                        "original_sha256": sha(files.pop(path))})
    provider = LIVE + "provider.json"
    replace(provider, provider_public(files[provider]), "Remove provider budget object only; retain model/endpoint/capability metadata")

    probe_path = LIVE + "capability-probe.zip"
    with zipfile.ZipFile(io.BytesIO(files[probe_path])) as archive:
        probe = {n: archive.read(n) for n in archive.namelist()}
    files["publication-provenance/capability-probe-original-manifest.json"] = probe["manifest.json"]
    original_probe_provider_sha = sha(probe["provider.json"])
    probe["provider.json"] = provider_public(probe["provider.json"])
    probe_manifest = json.loads(probe["manifest.json"])
    probe_manifest["files"]["provider.json"] = sha(probe["provider.json"])
    probe["manifest.json"] = encoded(probe_manifest)
    for name in probe_manifest["files"]:
        if sha(probe[name]) != probe_manifest["files"][name]:
            raise ValueError("Public capability probe input mismatch: " + name)
    replace(probe_path, zip_bytes(probe), "Remove nested provider budget object and rehash probe manifest; other nested payloads unchanged")
    changes.append({"path": probe_path + "!/provider.json", "action": "replace",
                    "reason": "Private provider budget only", "original_sha256": original_probe_provider_sha,
                    "public_sha256": sha(probe["provider.json"])})

    campaign_path = LIVE + "campaign.json"
    files["publication-provenance/agent-campaign-original.json"] = files[campaign_path]
    campaign = json.loads(files[campaign_path])
    for name in ("provider.json", "capability-probe.zip"):
        campaign["inputs"][name] = sha(files[LIVE + name])
    replace(campaign_path, encoded(campaign), "Rebind only the two sanitized metadata/probe input hashes; trial protocol/settings/results unchanged")

    files["publication-provenance/original-candidate-manifest.json"] = files.pop("R5-EVIDENCE-MANIFEST.json")
    files["publication-provenance/original-candidate-readme.txt"] = files.pop("README.txt")
    documentation = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", DOCUMENTATION_COMMIT, "docs/revision"], cwd=ROOT, text=True)
    docs = [p for p in documentation.splitlines() if p.endswith(".md") and p.count("/") == 2]
    docs.append("docs/ieee-access-revision-roadmap.md")
    for path in docs:
        destination = "documentation/" + Path(path).name
        data = subprocess.check_output(["git", "show", DOCUMENTATION_COMMIT + ":" + path], cwd=ROOT)
        if destination in files and files[destination] != data:
            replace(destination, data, "Use the committed R5 documentation snapshot; historical candidate descriptions remain labelled as local")
        else:
            files[destination] = data
    files["prepare_r5_zenodo.py"] = Path(__file__).read_bytes()
    files["LICENSE"] = subprocess.check_output(["git", "show", CHECKPOINT + ":LICENSE"], cwd=ROOT)
    files["PUBLICATION-TRANSFORMATIONS.json"] = encoded({
        "schema": "cp2n2-publication-transformations-v1", "candidate_sha256": CANDIDATE_SHA256,
        "private_originals_modified": False, "trial_payloads_modified": False,
        "financial_metadata_removed": True, "changes": changes,
        "note": "Original input-manifest bytes are provenance, not manifests for the sanitized public files. Use PUBLIC-EVIDENCE-MANIFEST.json for this copy."})
    files["README.txt"] = (
        "CP2N2 R2-R5 public revision evidence — " + VERSION + "\n\n"
        "Evaluated software commit: " + CHECKPOINT + "\n"
        "Documentation commit: " + DOCUMENTATION_COMMIT + "\n"
        "This is an evidence archive version, not a new GitHub software tag.\n\n"
        "Contains continuous MCP-to-SDK simulator execution/recovery, effect-based\n"
        "enforcement, bounded state exploration, the executing Qwen agent campaign,\n"
        "selection, contention, timing, same-host TCP/container fault campaigns,\n"
        "and the existing clean-source local reproduction workflow.\n"
        "All failures and negative controls are retained. There are no physical\n"
        "CL1 or biological observations, independent coauthor reproduction, new\n"
        "live LLM runs, or multi-host measurements. Reproduction reused the host\n"
        "and Python environment; original timing was recomputed, not remeasured.\n\n"
        "Only provider-account budget metadata is removed. Public input manifests\n"
        "are rehashed with explicit original/public hashes and preserved original\n"
        "manifest bytes in publication-provenance/. Scientific trial payloads,\n"
        "prompts, oracles, logs and audit chains are otherwise byte-identical.\n"
        "The private frozen candidate remains unchanged. Consult\n"
        "PUBLICATION-TRANSFORMATIONS.json and PUBLIC-EVIDENCE-MANIFEST.json.\n\n"
        "For local verification, extract cp2n2-evaluation-source.zip into a clean\n"
        "source folder, use the recorded Python dependencies, and run its scripts\n"
        "with --verify and the corresponding evidence directory.\n"
        "The provider capability probe is excluded from agent denominators.\n"
        "The R4 container export-inventory repair is retained/disclosed in the\n"
        "original candidate manifest and the container packaging-repair folder.\n"
        "Historical v5.1.1 evidence is unchanged under DOI 10.5281/zenodo.21887895.\n"
        "This builder does not upload or publish; consult the Zenodo record for\n"
        "the actual publication identifier and server-side file checksums.\n"
    ).encode("utf-8")
    known_secrets = {**dotenv_values(ROOT / ".env"), **os.environ}
    secrets = [v.encode() for k, v in known_secrets.items() if v and len(v) >= 12 and
               any(term in k.upper() for term in ("TOKEN", "SECRET", "API_KEY", "PASSWORD"))]
    audited = audit_public(files, secrets)
    changed_evidence = [c["path"] for c in changes if c["path"].startswith("evidence/")]
    allowed = {LIVE + n for n in ("budget-after.json", "budget-checks.json", "provider.json", "capability-probe.zip", "campaign.json")}
    unchanged = sum(name.startswith("evidence/") and name not in allowed and files.get(name) == data
                    for name, data in original_payload.items())
    for name, data in original_payload.items():
        if name.startswith("evidence/") and name not in allowed and files.get(name) != data:
            raise ValueError("Scientific evidence payload changed unexpectedly: " + name)
    manifest = {"schema": "cp2n2-r5-public-evidence-v1", "version": VERSION,
                "evaluated_source_commit": CHECKPOINT, "documentation_commit": DOCUMENTATION_COMMIT,
                "original_candidate_sha256": CANDIDATE_SHA256, "publication_by_builder": False,
                "financial_metadata_removed": True, "independent_coauthor_reproduction": False,
                "physical_substrate_observations": 0, "byte_identical_evidence_payloads": unchanged,
                "files": {n: {"bytes": len(d), "sha256": sha(d)} for n, d in sorted(files.items())}}
    files["PUBLIC-EVIDENCE-MANIFEST.json"] = encoded(manifest)
    output.mkdir(parents=True, exist_ok=False)
    final = output / "cp2n2-r5-2026-10-10-public-evidence.zip"
    final.write_bytes(zip_bytes(files))
    with zipfile.ZipFile(final) as archive:
        if archive.testzip() is not None:
            raise ValueError("Final public archive CRC failure")
        for n, item in manifest["files"].items():
            if sha(archive.read(n)) != item["sha256"]:
                raise ValueError("Final public manifest mismatch: " + n)
    report = {"archive": final.name, "bytes": final.stat().st_size, "sha256": sha(final.read_bytes()),
              "md5": hashlib.md5(final.read_bytes()).hexdigest(), "inventory_files": len(manifest["files"]),
              "audited_payloads_including_nested": audited, "financial_metadata_removed": True,
              "byte_identical_evidence_payloads": unchanged, "changed_evidence_paths": changed_evidence,
              "original_candidate_preserved": sha(original.read_bytes()) == CANDIDATE_SHA256,
              "crc_and_payload_hashes_verified": True, "publication_performed": False}
    (output / "PUBLIC-PACKAGE-VERIFICATION.json").write_bytes(encoded(report))
    (output / "SHA256SUMS.txt").write_bytes((report["sha256"] + "  " + final.name + "\n").encode())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
