# R5 integration results — 10 October 2026

**Status:** technical draft prepared; public evidence archive published on
10 October 2026 as DOI `10.5281/zenodo.23281161`. Author review, independent
reproduction and submission approval
remain open. See the [publication record](r5-zenodo-publication.md).
Commit/push was authorized separately; Zenodo publication does not authorize
a GitHub release or external manuscript submission.

## What is prepared

- R2--R4 results and limitations are integrated into the authoritative
  `cp2n2.tex` in the paper repository. The neutral arXiv source is generated
  from it; clean and yellow-marked IEEE views use the same scientific source.
- Journal PDFs/source ZIPs: 19 pages each; neutral arXiv preview/source ZIP:
  27 pages. Revision marking is cumulative against the confirmed original
  submission, not reset to R1 or an intermediate working copy.
- All 22 reviewer concerns have substantive response/action/location/evidence
  drafts. The supplied IEEE Word template is used; only document-body XML was
  edited, with all other package parts and section geometry preserved.
- The response PDF has 10 pages. The supplied checklist has 3 pages and all
  ten author checkboxes remain unchecked pending author review.
- See the paper repository's `R5-REVISION-HANDOFF.md` for artifact links and
  `IEEE-ACCESS-RESPONSE-TO-REVIEWERS.md` for the canonical response text.
- The [versioned reviewer material](ieee-access/README.md) mirrors all 22
  response drafts as Markdown/Word/PDF and retains the official checklist.
  Its [ten-item status](ieee-access/RESUBMISSION-CHECKLIST-STATUS.md) distinguishes
  prepared files from final author checks and upload actions. Exact copy hashes
  are in `ieee-access/REVIEW-MATERIAL-MANIFEST.json`.

## Old and new agent studies

The executing Qwen study is the sole main agent evaluation: 24/32 strict
planner matches, 6/8 permitted opportunities executed, including two SDK
runs; two stale-health execution attempts were blocked. All eight deviations
remain reported, with no observed forbidden effects in these bounded cases.

The historical MiniMax dry-run tables are omitted from the main paper, with
one brief design-history note retained. Raw evidence, protocol and scores are
unchanged in the historical archive. The response explicitly retains 141/160
and the physical-class 1/20 (19 clarifications fail the refusal oracle).
Different models/cases/harnesses forbid a controlled improvement claim. The
new study addresses executing effects; it does not retroactively fix the old
study or prove general physical safety.

Other negative findings remain: controller-restart duplicates, early generic
HTTP errors, ambiguous string-valued drift admission, authored oracle coverage,
model-visible freshness limitations, and single-host/performance-environment
bounds. No E5/biological result is added.

## Clean-source local reproduction

Runner: `scripts/run_r5_reproduction.py`; checkpoint:
`f5802a3d1c2695637a5840ab5ed94d46ce64063c`.

Output: `.cp2n2/r5-reproduction-20261010-01/verification.json`.
All 18 jobs exited zero; verification passed and the detached source checkout
remained clean. The suite passed **286 tests**, with two dependency deprecation
warnings. Original campaign archives were verified, and non-LLM R2/R3/R4
execution/enforcement/selection/contention/TCP checks were freshly rerun.

This used the same physical host and existing Python environment, not a fresh
installation or an independent co-author. The hosted LLM and original container
campaign were verified, not rerun; original overhead was recomputed, not
remeasured. No new LLM request or physical observation occurred.

## Local candidate, not publication

Runner: `scripts/package_r5_evidence.py`. The candidate includes eleven raw
campaign/reproduction archives, the exact evaluated source ZIP, current
supporting revision documents and both R5 orchestration scripts.

Output:
`.cp2n2/r5-release-candidate-20261010-02/cp2n2-r5-local-evidence-candidate.zip`.
Its `R5-PACKAGE-VERIFICATION.json` records **12,453** inventory payloads,
**134,137,097 bytes**, verified ZIP CRC and individual SHA-256 values. SHA-256:
`df0895efe7964af7b6b58611d60e304170da68ecaef33cc1a07f11c6497ee7f8`.
It is a frozen local draft package, predating this final documentation update;
regenerate a new candidate after author review rather than silently replacing
its inventory. No raw campaign measurements were rewritten.

The path/structured-field credential scan passed. It is not a guarantee against
arbitrary secrets in binary content, and provider budget metadata is retained
locally for author review. Public privacy approval remains mandatory. The R4
container export-inventory repair is preserved/disclosed; underlying measurements
and nested manifests are unchanged. Existing v5.1.1/Zenodo references cover
historical evidence, not the new local campaigns.

The subsequent [public evidence version](r5-zenodo-publication.md) is a
separate sanitized copy. It removes provider-account budget metadata and
explicitly rebinds affected metadata hashes; scientific trial payloads remain
unchanged. All ten campaign verifiers passed again, with the same output-log
hashes as the original verification. The private candidate above is still
unchanged and must not be substituted for the public ZIP.

The public transformations remove structured account-budget objects and two
budget-only logs. Already-public textual spend/account-cap summaries remain;
the publication does not claim that all budget-related text was removed.

## Manuscript and document verification

- After integrating DOI `10.5281/zenodo.23281161`, all 78 rebuilt output pages
  were visually reviewed: 19 clean journal, 19 marked journal, 27 arXiv,
  10 response and 3 checklist. The current local QA receipt is
  `tmp/r5-doi-qa/verification.json` in the paper repository.
- Fifteen manuscript markup/generator, DOI integration and synchronization-guard
  tests pass; the checked-in neutral source
  exactly matches the generator. Both journal ZIPs contain the exact current
  authoritative source; arXiv contains the generator's intended flat form,
  with the bibliography/figure-path transformations checked.
- All three submission ZIPs pass CRC and manifest SHA-256 checks. Both IEEE
  ZIPs are below 18 MB; no blocking unresolved-reference/citation build errors.
- Word template fidelity passes: preserve-only package parts and section
  geometry match the supplied originals, with all 22 responses exported and
  all ten checklist checkboxes still unchecked.
- `git diff --check` passes in both repositories (Windows line-ending notices
  only). Root-level comparison PDFs and unrelated temporary files were untouched.
- The current software regression suite passes 296 tests with two dependency
  deprecation warnings, including ten new public-packaging tests. This check is
  distinct from the frozen 286-test reproduction above and adds no new campaign
  observation or independent reproduction.

Final manuscript PDF hashes (working drafts, not the original submission):

- Clean journal: `511222f1128b7dc14e2901b0b3aaf554f1c62bb04e0f5bd968d314349a0b3cbf`.
- Yellow-marked journal: `af545a67a86d79fe85d655a5e603271e91fe49d6fdae3d5c2cf2ae492d54b896`.
- Neutral arXiv: `5b169f4fa48997f8cf74157adbf14b6f0d11fd1dcc0e8c96f35d3fe4d9f74232`.

## Remaining gates

1. Author review of manuscripts, responses, tone and unchecked checklist.
2. Independent co-author reproduction of key execution/enforcement results.
3. Editor response and explicit venue decision; the author reports no reply yet.
4. Review the regenerated manuscript/response packages, which now cite the
   published version DOI. Public archival and DOI integration are complete.
5. Final author approval for packaging/submission and any separate GitHub release.
   Commit/push and Zenodo authorization do not close the remaining R5 gates.

Until these pass, R5 remains `IN_PROGRESS`, not a completed resubmission.
