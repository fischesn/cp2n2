# CP²N² revision evidence on Zenodo

The R2–R5 evidence was published on 10 October 2026 as a new version of the
existing CP²N² Zenodo record. This closes the public evidence-archive gate,
not the independent reproduction, manuscript approval or submission gates.

## Archive identity

| Field | Published value |
| --- | --- |
| Version DOI | [10.5281/zenodo.23281161](https://doi.org/10.5281/zenodo.23281161) |
| Record | [Zenodo 23281161](https://zenodo.org/records/23281161) |
| Concept DOI | `10.5281/zenodo.19595082` |
| Evidence version | `R5-2026-10-10` |
| Evaluated software commit | `f5802a3d1c2695637a5840ab5ed94d46ce64063c` |
| Documentation commit | `d758e9e2a9d5f9b988015abbe54089d27d04a5b2` |
| Public ZIP | `cp2n2-r5-2026-10-10-public-evidence.zip` |
| ZIP bytes | 134,633,211 |
| ZIP SHA-256 | `a57b98f0a2afc2a2b39ad3557bdb1733b1f995041011466cf6a082c17ed7cf0a` |
| ZIP server MD5 | `44623ed60c284e6ec76f22e1ec07ea25` |

This is an evidence version, not a new GitHub software release or tag. The
previous record, DOI `10.5281/zenodo.21887895`, and its files remain unchanged.
Its two inherited files are retained in the new record as the historical
v5.1.1 baseline; they do not represent the new revision campaign.

## Contents and privacy

The ZIP includes eleven campaign/reproduction archives, the exact evaluated
source snapshot, protocols, oracles, prompts, traces, scoring code, revision
documentation and per-file hashes. The record also contains the public package
and campaign verification receipts, deposit metadata and SHA-256 sums.

The private local candidate remains unchanged. In the public copy, two
budget-only JSON files are omitted and provider-account budget objects are
removed from the main Qwen metadata and its nested capability probe. The
affected probe manifest and campaign input hashes are rebound explicitly.
Original safe manifest bytes and original/public hashes are retained in
`publication-provenance/` and `PUBLICATION-TRANSFORMATIONS.json`.

This is structured budget-object/log redaction, not removal of every earlier
textual budget reference. The already-public Qwen report and byte-preserved
source snapshots retain their published provider-unit spend/account-cap
summary. The Zenodo description was clarified accordingly without changing
any archived file. `ZENODO-METADATA.json` in the deposit is the initial
metadata snapshot, not the subsequently clarified description; the
[metadata clarification receipt](r5-zenodo-metadata-clarification.json)
records that metadata-only update.

All 12,427 other evidence payloads are byte-identical to the frozen candidate.
Trial settings, prompts, oracles, measurements, failures and audit chains were
not rewritten. Structured credential/path checks and comparisons against
locally known credential values passed, including nested archives. These
checks are not a general guarantee against arbitrary hidden binary content.

## Verification and limits

All ten original campaign verifiers passed against the extracted public copy
using the evaluated source. Each produced the same output-log hash as the
earlier verification of the private original. The Qwen study still reports
24/32 strict planner matches, 6/8 permitted completions and zero observed
forbidden effects in the bounded tested cases; all eight deviations remain.
Zenodo's uploaded-file sizes and MD5 checksums match the local files.
All five newly uploaded files were then downloaded without authentication;
their complete SHA-256 values and byte counts also match. The
[public download verification](r5-zenodo-public-download-verification.json)
records this independent transfer check, including the full evidence ZIP.

The archived clean-source workflow passed 286 tests and 18 jobs on the original
host and Python environment. Publication verification made no new LLM calls,
container trials, timing measurements or physical observations. Independent
co-author reproduction remains open. There is no physical CL1 or biological
evidence, multi-host experiment, durable replicated controller or general
physical-safety guarantee. Restart duplicates and other negative findings are
retained, including the previously disclosed R4 container inventory repair.

The machine-readable [publication receipt](r5-zenodo-publication.json)
records the uploaded files, sizes and hashes without credentials.

## Manuscript integration and remaining gates

The paper and reviewer response now cite this exact version DOI. Matching
clean/marked journal, neutral arXiv and response exports/source packages are
rebuilt and inspected together. This publication does not mark
the ten official resubmission checkboxes author-approved or upload any journal
or arXiv manuscript.
