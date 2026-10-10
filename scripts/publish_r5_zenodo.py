"""Publish the verified R5 evidence as a NEW version of the CP2N2 Zenodo record.

Requires explicit --publish, a locally stored ZENODO_ACCESS_TOKEN and verified
public package/campaign receipts. Never deletes or edits the old published
record, creates a GitHub release, or sends credentials in URLs/logs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse

from dotenv import load_dotenv
import requests

ROOT = Path(__file__).resolve().parents[1]
BASE_RECORD = 21887895
CONCEPT = "19595082"
VERSION = "R5-2026-10-10"
TITLE = "CP²N² — Control Plane for Physical Neural Networks: R2–R5 revision evidence (2026-10-10)"
SOURCE = "f5802a3d1c2695637a5840ab5ed94d46ce64063c"
DOCS = "d758e9e2a9d5f9b988015abbe54089d27d04a5b2"
API = "https://zenodo.org/api/"


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def checksum(path, algorithm="sha256"):
    result = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def checked_url(url):
    value = urlparse(url)
    if value.scheme != "https" or value.netloc != "zenodo.org" or value.query or value.fragment:
        raise ValueError("Unexpected Zenodo API URL; credentials not sent")
    return url


def request(session, method, url, **kwargs):
    for _ in range(4):
        result = session.request(method, checked_url(url), timeout=(30, 300), allow_redirects=False, **kwargs)
        if method == "GET" and result.status_code in (301, 302, 307, 308):
            url = checked_url(urljoin(url, result.headers["Location"]))
            continue
        break
    if not 200 <= result.status_code < 300:
        # Do not echo arbitrary server bodies, requests or credential headers.
        raise RuntimeError(f"Zenodo {method} returned HTTP {result.status_code} at {urlparse(url).path}")
    return result


def metadata(original):
    return {
        "title": TITLE, "upload_type": "software", "version": VERSION,
        "publication_date": "2026-10-10", "access_right": "open",
        "license": original["license"], "creators": original["creators"], "language": "eng",
        "keywords": ["physical neural networks", "control plane", "Model Context Protocol", "agentic AI",
                     "reproducible systems", "SDK simulator", "fault injection", "execution enforcement"],
        "description": (
            "<p>CP²N² is a substrate-neutral control plane for heterogeneous physical-neural resources. "
            "This evidence version archives the R2–R5 systems-paper revision, evaluated at software commit "
            + SOURCE + ", with documentation at " + DOCS + ". It is not a new GitHub software tag.</p>"
            "<p>The public bundle includes continuous MCP-to-official CL SDK Simulator execution and recovery; "
            "effect-based enforcement and bounded state exploration; the executing University of Lübeck AI-Lab "
            "Qwen campaign (24/32 strict planner matches, 6/8 permitted executions, all eight deviations retained); "
            "selection, contention and timing measurements; same-host TCP and separate-container fault campaigns; "
            "protocols, oracles, prompts, raw traces, scoring tools, source snapshots and hash manifests. "
            "Negative findings, including restart duplicates and ambiguous-drift admission, are preserved.</p>"
            "<p>The existing clean-source local reproduction passed 286 tests and 18 jobs. The public sanitized "
            "copy was separately verified across all ten original campaign archives using the evaluated source. "
            "Reproduction reused the same physical host and Python environment; original hosted-model and "
            "container observations were verified rather than rerun, and timing was recomputed rather than remeasured. "
            "There is no independent co-author reproduction, multi-host experiment, physical CL1 execution, "
            "biological performance result or general physical-safety guarantee.</p>"
            "<p>Only private provider-account budget metadata is removed from the public copy. "
            "Two budget-only JSON files are omitted; provider budget objects in the main campaign and capability "
            "probe are redacted, with affected input hashes explicitly rebound. Original safe manifest bytes "
            "and original/public hashes are retained in the transformation provenance. 12,427 scientific evidence "
            "payloads remain byte-identical; trial settings, prompts, oracles, measurements and audit chains "
            "are unchanged. Consult PUBLICATION-TRANSFORMATIONS.json and PUBLIC-EVIDENCE-MANIFEST.json inside "
            "cp2n2-r5-2026-10-10-public-evidence.zip, and the separately uploaded verification receipts.</p>"
            "<p>The inherited v5.1.1 source/evidence files are the historical baseline, not the new campaign. "
            "The previous published record and files remain unchanged under DOI 10.5281/zenodo.21887895. "
            "The historical dry-run agent study is not retroactively rewritten or treated as a controlled "
            "comparison with the new executing study.</p>"),
        "related_identifiers": [
            {"identifier": "10.5281/zenodo.21887895", "relation": "isDerivedFrom", "scheme": "doi", "resource_type": "software"},
            {"identifier": "https://github.com/fischesn/cp2n2/tree/" + SOURCE,
             "relation": "isSupplementTo", "scheme": "url", "resource_type": "software"},
            {"identifier": "https://github.com/fischesn/cp2n2/blob/" + DOCS + "/docs/revision/r5-integration-results.md",
             "relation": "isDocumentedBy"}],
        "notes": "Software/simulator evidence only (E0–E3). Privacy transformations are disclosed; private originals are unchanged. No manuscript submission or GitHub release is performed by this deposit.",
    }


def load_package(base):
    report = json.loads((base / "PUBLIC-PACKAGE-VERIFICATION.json").read_text(encoding="utf-8"))
    verified = json.loads((base / "PUBLIC-CAMPAIGN-VERIFICATION.json").read_text(encoding="utf-8"))
    package = base / report["archive"]
    if (not report["financial_metadata_removed"] or not report["original_candidate_preserved"]
            or not report["crc_and_payload_hashes_verified"] or not verified["verified"]
            or len(verified["campaigns"]) != 10 or any(r["exit_code"] for r in verified["campaigns"])
            or report["sha256"] != verified["archive_sha256"] or checksum(package) != report["sha256"]):
        raise ValueError("Public-package verification gate failed")
    return package, report, verified


def verify_remote_files(deposit, paths):
    inventory = {entry["filename"]: entry for entry in deposit["files"]}
    for path in paths:
        entry = inventory.get(path.name)
        if not entry or entry["checksum"].removeprefix("md5:") != checksum(path, "md5") or int(entry["filesize"]) != path.stat().st_size:
            raise ValueError("Zenodo upload checksum/size differs: " + path.name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--publish", action="store_true", help="Explicitly authorize the irreversible public deposit")
    args = parser.parse_args()
    base = args.package_dir.resolve(strict=True)
    if not base.is_relative_to((ROOT / ".cp2n2").resolve()):
        raise ValueError("Package must be inside .cp2n2")
    package, package_report, verified = load_package(base)
    if not args.publish:
        print(json.dumps({"ready_for_authorized_publication": True, "archive_sha256": package_report["sha256"], "version": VERSION}))
        return
    load_dotenv(ROOT / ".env")
    token = os.environ.get("ZENODO_ACCESS_TOKEN")
    if not token:
        raise ValueError("ZENODO_ACCESS_TOKEN is absent; never put it in command arguments")
    session = requests.Session()
    session.headers["Authorization"] = "Bearer " + token
    old_url = API + "deposit/depositions/" + str(BASE_RECORD)
    old = request(session, "GET", old_url).json()
    if str(old["conceptrecid"]) != CONCEPT or not old["submitted"]:
        raise ValueError("Unexpected historical record identity/state")
    old_files = {p["filename"]: (p["checksum"], p["filesize"]) for p in old["files"]}
    state_path = base / "ZENODO-PUBLICATION-STATE.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if state["base_record"] != BASE_RECORD or state["archive_sha256"] != package_report["sha256"]:
            raise ValueError("Publication resume state belongs to another package")
        draft_url = state["draft_url"]
        draft = request(session, "GET", draft_url).json()
    else:
        latest = request(session, "GET", old["links"]["latest"]).json()
        if latest["id"] != BASE_RECORD:
            raise ValueError("Another version exists; do not overwrite or create a competing revision")
        if old["links"].get("latest_draft", old_url) != old_url:
            raise ValueError("An untracked new-version draft exists; author review required")
        print("Creating new version; old record and inherited files will not be changed", flush=True)
        created = request(session, "POST", old["links"]["newversion"]).json()
        draft_url = created["links"]["latest_draft"]
        if draft_url == old_url:
            raise ValueError("New-version action did not identify a new draft")
        state = {"base_record": BASE_RECORD, "draft_url": draft_url, "archive_sha256": package_report["sha256"], "version": VERSION}
        write(state_path, state)
        draft = request(session, "GET", draft_url).json()
    if str(draft["conceptrecid"]) != CONCEPT or draft["id"] == BASE_RECORD:
        raise ValueError("New draft is not a separate version of the intended concept")
    md = metadata(old["metadata"])
    metadata_path = base / "ZENODO-METADATA.json"
    write(metadata_path, md)
    paths = [package, base / "PUBLIC-PACKAGE-VERIFICATION.json", base / "PUBLIC-CAMPAIGN-VERIFICATION.json", metadata_path]
    sums = base / "ZENODO-SHA256SUMS.txt"
    sums.write_text("".join(checksum(p) + "  " + p.name + "\n" for p in paths), encoding="utf-8", newline="\n")
    paths.append(sums)
    if not draft["submitted"]:
        draft = request(session, "PUT", draft_url, json={"metadata": md}).json()
        for path in paths:
            inventory = {p["filename"]: p for p in draft["files"]}
            if path.name in inventory:
                verify_remote_files(draft, [path])
                continue
            bucket = draft["links"]["bucket"].rstrip("/")
            print("Uploading " + path.name + " (" + str(path.stat().st_size) + " bytes)", flush=True)
            with path.open("rb") as stream:
                uploaded = request(session, "PUT", bucket + "/" + quote(path.name, safe=""), data=stream).json()
            if uploaded["checksum"].removeprefix("md5:") != checksum(path, "md5") or uploaded["size"] != path.stat().st_size:
                raise ValueError("Bucket upload hash/size differs: " + path.name)
            draft = request(session, "GET", draft_url).json()
        verify_remote_files(draft, paths)
        if draft["metadata"]["version"] != VERSION or draft["metadata"]["title"] != TITLE:
            raise ValueError("Draft metadata verification failed")
        print("Publishing verified new-version draft " + str(draft["id"]), flush=True)
        published = request(session, "POST", draft["links"]["publish"]).json()
    else:
        verify_remote_files(draft, paths)
        published = draft
    # Fetch read-only state before reporting success; never repeat publish blindly.
    final = request(session, "GET", draft_url).json()
    if not final["submitted"] or final["state"] != "done":
        raise RuntimeError("Publish accepted, but final done state is not yet verified; resume without a second deposit")
    verify_remote_files(final, paths)
    record = request(session, "GET", API + "records/" + str(final["id"])).json()
    if record["metadata"]["version"] != VERSION or record["conceptdoi"] != "10.5281/zenodo." + CONCEPT:
        raise ValueError("Published public record identity differs")
    after = request(session, "GET", old_url).json()
    if {p["filename"]: (p["checksum"], p["filesize"]) for p in after["files"]} != old_files:
        raise ValueError("Unexpected historical file change")
    receipt = {"schema": "cp2n2-r5-zenodo-publication-v1", "published": True, "record_id": final["id"],
               "doi": record["doi"], "concept_doi": record["conceptdoi"], "url": record["links"]["self_html"],
               "version": VERSION, "evaluated_source_commit": SOURCE, "documentation_commit": DOCS,
               "archive_sha256": package_report["sha256"], "old_record_files_unchanged": True,
               "uploaded_files": {p.name: {"bytes": p.stat().st_size, "sha256": checksum(p), "md5": checksum(p, "md5")} for p in paths},
               "campaign_archives_verified": len(verified["campaigns"]), "physical_substrate_observations": 0,
               "independent_coauthor_reproduction": False}
    write(base / "ZENODO-PUBLICATION-RECEIPT.json", receipt)
    print(json.dumps(receipt, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
