"""Publish supplementary evidence as a new CP2N2 Zenodo version.

Requires --publish and a verified local package. Never edits old records,
overwrites inherited files or sends credentials in URLs. No automatic
POST retry: ambiguous outcomes must be reconciled through the saved draft.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

from dotenv import dotenv_values
import requests

from publish_r5_zenodo import checked_url, request, checksum, verify_remote_files

ROOT = Path(__file__).resolve().parents[1]
BASE_RECORD = 23281161
CONCEPT = "19595082"
VERSION = "SUPPLEMENTARY-2026-10-14"
TITLE = "CP²N² — Control Plane for Physical Neural Networks: AP1–AP3 and Gemini selector evidence (2026-10-14)"
API = "https://zenodo.org/api/"

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

def inventory(deposit):
    files = deposit["files"]
    if len({f["filename"] for f in files}) != len(files):
        raise ValueError("Duplicate remote file names")
    return {f["filename"]: (f["checksum"].removeprefix("md5:"), int(f["filesize"])) for f in files}

def metadata(original):
    return {
        "title": TITLE, "upload_type": "software", "version": VERSION,
        "publication_date": "2026-10-14", "access_right": "open",
        "license": original["license"], "creators": original["creators"], "language": "eng",
        "keywords": ["physical neural networks", "control plane", "Model Context Protocol",
                     "telemetry validation", "provider recovery", "reproducible systems",
                     "synthetic selection cases", "CPU load", "fault injection"],
        "description": (
            "<p>This new CP²N² evidence version adds the separately frozen 14 October 2026 "
            "AP1–AP3 and externally model-authored selector campaigns. Earlier R5 and historical "
            "v5.1.1 deposit files are inherited unchanged and remain distinct source checkpoints. "
            "This is not a GitHub software release.</p>"
            "<p>AP1 contains 46 ordinary required-evidence trials and four detector controls: "
            "28 invalid preconditions cause no backend starts/commits; six valid controls execute "
            "and deliver; twelve invalid post-execution cases commit legitimately but withhold "
            "successful delivery. AP2 has 18 separate-process/loopback TCP trials and 96 structured "
            "HTTP responses, with per-resource quarantine and explicit reconciliation. An uncertain "
            "invocation prohibits automatic retry/fallback; recovery does not resolve the lost result "
            "or make in-memory state durable.</p>"
            "<p>AP3 retains 80 fresh-registry trials, 32,000 measured operations and 3,200 warmups, "
            "under no intentionally added load and one owned CPU worker. Measured worker utilization "
            "is approximately 29–37% of one core, not whole-host saturation. Intervals concern trial "
            "summary medians, including the median of trial p95 values, not population tail guarantees. "
            "Directed execution is not a general selector-scaling experiment.</p>"
            "<p>Twelve synthetic selector cases were generated as an unchanged first response in a "
            "new isolated Gemini chat, without the paper, repository or prior results. The author-reported "
            "display name is Gemini Flash 3.8 with high effort; no unavailable backend model or API ID "
            "is invented. Pre-run author approval and an explicit missing-drift annotation interpretation "
            "are preserved. Three policies and two orders produce 72 matching eligible-set/ranking/"
            "choice/normalized-annotation cells and 36 invariant order pairs. These are dependent "
            "deterministic checks, not 72 independent real workloads or independent human reproduction.</p>"
            "<p>The original 290 AP source hashes remain unchanged within the Gemini 295-file snapshot. "
            "Exact evaluated source ZIPs and per-file hashes identify uncommitted source bytes; the base "
            "Git commit does not identify them. The archive includes complete raw observations, protocols, "
            "inputs, original Gemini output and issued prompt, approvals, manifests, offline verification "
            "tools, the disclosed AP2 v1 negative development classifier report and separate v2 development "
            "archive, and old-R4 offline summaries. Scientific payloads are byte-preserved; no privacy "
            "redaction was required by the credential/account-metadata scan. Documentation describes the "
            "pre-publication checkpoint and is not retroactively rewritten.</p>"
            "<p>All four scored campaigns are verified offline using their archived source, without new "
            "LLM, provider, timing, container or physical observations. The earlier R5 DOI "
            "10.5281/zenodo.23281161 does not contain this supplement. Its historical failures remain "
            "unchanged. Software/simulator evidence does not establish biological performance, physical "
            "safety, hardware attestation, durable replicated coordination or independent co-author "
            "reproduction. No journal/arXiv manuscript is submitted by this deposit.</p>"),
        "related_identifiers": [
            {"identifier": "10.5281/zenodo.23281161", "relation": "isDerivedFrom", "scheme": "doi", "resource_type": "software"},
            {"identifier": "https://github.com/fischesn/cp2n2", "relation": "isSupplementTo", "scheme": "url", "resource_type": "software"},
        ],
        "notes": "Four scored campaigns plus separately labelled development and historical-analysis records. Exact bytes and source identities are bound by the public manifest. Inherited older files do not represent the supplementary source.",
    }

def load_package(base):
    package = json.loads((base / "SUPPLEMENTARY-PACKAGE-VERIFICATION.json").read_text(encoding="utf-8"))
    campaigns = json.loads((base / "SUPPLEMENTARY-CAMPAIGN-VERIFICATION.json").read_text(encoding="utf-8"))
    archive = base / package["archive"]
    if archive.parent != base or not archive.is_file():
        raise ValueError("Unexpected package target")
    if checksum(archive) != package["sha256"]:
        raise ValueError("Package hash mismatch")
    for flag in ("crc_and_payload_hashes_verified", "originals_unchanged", "credential_scan_passed"):
        if package.get(flag) is not True:
            raise ValueError("Package gate failed: " + flag)
    results = campaigns.get("campaigns", [])
    if campaigns.get("verified") is not True or len(results) != 4 or any(r.get("exit_code") != 0 for r in results):
        raise ValueError("Four offline campaign verification gates required")
    expected_names = {
        "ap1-required-evidence-confirmatory-20261014-01",
        "ap2-provider-errors-confirmatory-20261014-01",
        "ap3-overhead-confirmatory-20261014-01",
        "gemini-selector-confirmatory-20261014-01",
    }
    if {r.get("name") for r in results} != expected_names or any(r.get("verified") is not True for r in results):
        raise ValueError("Unexpected or incomplete scored campaign identities")
    if campaigns.get("package_sha256") != package["sha256"]:
        raise ValueError("Campaign verification belongs to another ZIP")
    return archive, package, campaigns

def verify_inherited(deposit, expected):
    now = inventory(deposit)
    if any(now.get(name) != tuple(value) for name, value in expected.items()):
        raise ValueError("Inherited baseline files differ")

def public_downloads(record, paths, base):
    anonymous = requests.Session()
    files = {f["key"]: f for f in record["files"]}
    report = []
    for path in paths:
        entry = files.get(path.name)
        if not entry:
            raise ValueError("Published file missing: " + path.name)
        url = entry["links"].get("content") or entry["links"].get("self")
        if not url:
            url = API + "records/" + str(record["id"]) + "/files/" + quote(path.name, safe="") + "/content"
        digest = hashlib.sha256()
        size = 0
        response = request(anonymous, "GET", url, stream=True)
        try:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    size += len(chunk)
                    digest.update(chunk)
        finally:
            response.close()
        if size != path.stat().st_size or digest.hexdigest() != checksum(path):
            raise ValueError("Anonymous full download mismatch: " + path.name)
        report.append({"file": path.name, "bytes": size, "sha256": digest.hexdigest(), "authentication_used": False})
        print("Public download verified: " + path.name, flush=True)
    result = {"schema": "cp2n2-supplementary-public-download-verification-v1", "record_id": record["id"],
              "all_files_match": True, "complete_downloads": report}
    write(base / "SUPPLEMENTARY-PUBLIC-DOWNLOAD-VERIFICATION.json", result)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    base = args.package_dir.resolve(strict=True)
    if base == (ROOT / ".cp2n2").resolve() or not base.is_relative_to((ROOT / ".cp2n2").resolve()):
        raise ValueError("Package directory must be a concrete .cp2n2 child")
    archive, report, campaigns = load_package(base)
    if not args.publish:
        print(json.dumps({"ready": True, "archive_sha256": report["sha256"], "version": VERSION}))
        return
    token = dotenv_values(ROOT / ".env").get("ZENODO_ACCESS_TOKEN")
    if not token:
        raise ValueError("Local ZENODO_ACCESS_TOKEN is absent")
    session = requests.Session()
    session.headers["Authorization"] = "Bearer " + token
    old_url = API + "deposit/depositions/" + str(BASE_RECORD)
    old = request(session, "GET", old_url).json()
    if str(old["conceptrecid"]) != CONCEPT or not old["submitted"]:
        raise ValueError("Unexpected base record identity/state")
    inherited = inventory(old)
    state_path = base / "SUPPLEMENTARY-ZENODO-STATE.json"
    if state_path.is_file():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state["base_record"] != BASE_RECORD or state["archive_sha256"] != report["sha256"]:
            raise ValueError("Resume state belongs to another publication")
        draft_url = checked_url(state["draft_url"])
        if state["inherited_files"] != {k: list(v) for k, v in inherited.items()}:
            raise ValueError("Baseline changed since creation")
        draft = request(session, "GET", draft_url).json()
    else:
        latest = request(session, "GET", old["links"]["latest"]).json()
        if latest["id"] != BASE_RECORD:
            raise ValueError("Another published version exists")
        if old["links"].get("latest_draft", old_url) != old_url:
            raise ValueError("Untracked new-version draft requires review")
        print("Creating supplementary version; earlier records remain unchanged", flush=True)
        created = request(session, "POST", old["links"]["newversion"]).json()
        draft_url = checked_url(created["links"]["latest_draft"])
        if draft_url == old_url:
            raise ValueError("New-version action did not return a separate draft")
        state = {"base_record": BASE_RECORD, "draft_url": draft_url,
                 "archive_sha256": report["sha256"], "inherited_files": inherited,
                 "version": VERSION, "created_at": datetime.now(timezone.utc).isoformat()}
        write(state_path, state)
        draft = request(session, "GET", draft_url).json()
    if draft["id"] == BASE_RECORD or str(draft["conceptrecid"]) != CONCEPT:
        raise ValueError("Wrong draft identity")
    verify_inherited(draft, inherited)
    md = metadata(old["metadata"])
    metadata_path = base / "SUPPLEMENTARY-ZENODO-METADATA.json"
    if metadata_path.is_file():
        if json.loads(metadata_path.read_text(encoding="utf-8")) != md:
            raise ValueError("Saved publication metadata differs")
    else:
        write(metadata_path, md)
    paths = [archive, base / "SUPPLEMENTARY-PACKAGE-VERIFICATION.json",
             base / "SUPPLEMENTARY-CAMPAIGN-VERIFICATION.json", metadata_path]
    sums = base / "SUPPLEMENTARY-SHA256SUMS.txt"
    wanted = "".join(checksum(p) + "  " + p.name + "\n" for p in paths)
    if sums.is_file() and sums.read_text(encoding="utf-8") != wanted:
        raise ValueError("Saved checksum receipt differs")
    if not sums.is_file():
        sums.write_text(wanted, encoding="utf-8", newline="\n")
    paths.append(sums)
    if set(p.name for p in paths).intersection(inherited):
        raise ValueError("Supplement names would overwrite inherited files")
    if not draft["submitted"]:
        draft = request(session, "PUT", draft_url, json={"metadata": md}).json()
        for path in paths:
            if path.name in inventory(draft):
                verify_remote_files(draft, [path])
                continue
            print("Uploading " + path.name + " (" + str(path.stat().st_size) + " bytes)", flush=True)
            with path.open("rb") as stream:
                uploaded = request(session, "PUT", draft["links"]["bucket"].rstrip("/") + "/" + quote(path.name, safe=""), data=stream).json()
            if uploaded["checksum"].removeprefix("md5:") != checksum(path, "md5") or int(uploaded["size"]) != path.stat().st_size:
                raise ValueError("Upload hash/size differs: " + path.name)
            draft = request(session, "GET", draft_url).json()
        verify_remote_files(draft, paths)
        verify_inherited(draft, inherited)
        if draft["metadata"]["title"] != TITLE or draft["metadata"]["version"] != VERSION:
            raise ValueError("Draft metadata mismatch")
        if set(inventory(draft)) != set(inherited).union(p.name for p in paths):
            raise ValueError("Unexpected draft files")
        print("Publishing verified supplementary draft " + str(draft["id"]), flush=True)
        request(session, "POST", draft["links"]["publish"])
    final = request(session, "GET", draft_url).json()
    if not final["submitted"] or final["state"] != "done":
        raise RuntimeError("Final done state not verified; resume saved draft without creating another")
    verify_remote_files(final, paths)
    verify_inherited(final, inherited)
    record = request(requests.Session(), "GET", API + "records/" + str(final["id"])).json()
    if record["metadata"]["version"] != VERSION or record["conceptdoi"] != "10.5281/zenodo." + CONCEPT:
        raise ValueError("Published record identity differs")
    if inventory(request(session, "GET", old_url).json()) != inherited:
        raise ValueError("Historical record changed")
    receipt = {"schema": "cp2n2-supplementary-zenodo-publication-v1", "published": True,
               "record_id": final["id"], "doi": record["doi"], "concept_doi": record["conceptdoi"],
               "url": record["links"]["self_html"], "version": VERSION,
               "archive_sha256": report["sha256"], "old_record_files_unchanged": True,
               "inherited_files_unchanged": True, "scored_campaigns_verified": 4,
               "evaluated_source_identity": "archived ZIPs/per-file hashes, not dirty base Git commit",
               "uploaded_files": {p.name: {"bytes": p.stat().st_size, "sha256": checksum(p), "md5": checksum(p, "md5")} for p in paths},
               "new_scored_observations": False, "physical_substrate_observations": 0,
               "independent_coauthor_reproduction": False}
    write(base / "SUPPLEMENTARY-ZENODO-PUBLICATION.json", receipt)
    public_downloads(record, paths, base)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

