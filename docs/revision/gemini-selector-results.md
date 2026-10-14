# Gemini-authored selector results

14 October 2026. The first scored run on twelve externally authored synthetic
selection cases is complete. All **72 policy/order cells** match the frozen
expected eligible sets, complete rankings, selected resources and normalized
rejection annotations. All **36 original/reversed order pairs** are invariant.
The final software regression suite passes **486 tests** (195.35 s; two
dependency deprecation warnings).

These results test the production selector against a written contract. They
do not constitute 72 independent workloads or a physical PNN experiment.

## Authorship, approval and freeze

Stefan Fischer supplied Gemini's unchanged first response and reported the
model display name as **Gemini Flash 3.8**, with high effort. He then confirmed
that the response came from a new isolated chat without the paper, repository
or previous results, and approved all twelve cases and the documented
interpretations. The [approval record](gemini-selector-approval.json)
supersedes the pending status at the immutable
[intake checkpoint](gemini-selector-blind-v1/README.md). Those earlier files
have not been rewritten.

The [issued prompt](gemini-selector-blind-v1/prompt-issued.txt) and
[original response](gemini-selector-blind-v1/gemini-response-original.json)
are preserved. The response's byte SHA-256 is
`24ac85aa6f4266eef574cedbb42861931aa0907339d45b689b4669d18ef229a1`.
The display name and effort are author-reported; no API request ID, exact
backend model identifier or generation timestamp is inferred. The preserved
prompt is the text issued to the author, not an exported Gemini API request.

The [prospective protocol](gemini-selector-campaign-protocol.md), inputs,
approval, environment and source snapshot were frozen at
**2026-10-14 19:06:44.866402 UTC**, before the first production observation.
The dataset contains twelve cases, 47 candidate resource descriptions, 27
eligible-resource declarations and 36 expected policy decisions.

The functional implementation was frozen before the Gemini response was
received. All **290 normalized source hashes** from the
[AP1–AP3 checkpoint](ap1-ap3-source-freeze.json) match before and after the run.
The supplementary snapshot has **295 files**: the original 290 plus the new
campaign module, runner and test file, evaluation dependency manifest and
Git byte-preservation attributes. No matcher, adapter, orchestrator, old
oracle or expected outcome was tuned to the Gemini results. Base commit
`bba19db333011aa5c59bc6fa56f29eede536a723` does not identify these uncommitted
source bytes; the archived ZIP and per-file hashes do.

## Observation matrix and outcomes

Each case was evaluated with `lexicographic`, `latency_first` and
`locality_cost_first`, first with the original resource array and then its
exact reversal. A fresh matcher was used for each cell. The input bridge
received only case inputs, not Gemini's expected outcomes; scoring compared
the observed report against those expectations afterwards. Unit development
used fabricated report-shaped objects rather than production observations on
the withheld cases.

| Outcome | Agreement |
| --- | --- |
| Eligible resource set | 72/72 |
| Complete eligible-resource ranking | 72/72 |
| Selected resource, including null | 72/72 |
| Normalized rejection stage and semantic rule IDs | 72/72 |
| Conjunction of all four checks | 72/72 |
| Original/reversed order invariant pairs | 36/36 |

Each policy contributes 24 passing cells (twelve cases × two orders). No cell
was omitted, retried or corrected after scoring. Original raw reports, input
task/descriptor/runtime serializations and all first-run observations remain
in the archive.

One case has no eligible resource, three have exactly one, and eight have
multiple eligible resources. Five cases select different winners under at
least two policies. Coverage includes admission failures, feasibility
boundaries, null age/cost/drift semantics, health versus fatal lifecycle,
stochasticity/reset preferences, locality trade-offs and identifier tie-breaking.
The 282 candidate-record checks repeat the same 47 authored candidates six
times; they are not 282 independent examples.

## Approved interpretations and limits

“Admissible” in the supplied expectations means passing both admission and
feasibility. The prompt contains overlapping F4/F6 wording for missing
required drift. The approved convention records missing required drift as F4
and the numeric drift limit as F6, matching the unchanged Gemini annotations.
Either reading excludes the missing-drift resource; eligibility, ranking and
choice are unaffected. This ambiguity is disclosed in the original review.

Production diagnostics are mapped to the prompt's semantic rule IDs using the
mapping fixed before execution. Field-specific missing evidence maps to F4
(drift), F7 (age) or F8 (active-budget cost). Duplicate raw violations are
retained and only normalized rule IDs are deduplicated. Unexpected or unmapped
diagnostics fail annotation agreement rather than being discarded.

The cases use finite, explicitly typed inputs, fixed supported capabilities
and a common computational task. Malformed numeric payloads are outside this
dataset; [AP1](ap1-ap3-results.md) covers separate required-evidence failures.
Case 06's null-age exclusion applies to tasks with an active positive age
bound in this dataset, not every possible task.

The contribution is **external case authorship by a different LLM**, followed
by author review and a first-run test on unchanged functional source. The
cases are synthetic and contract-guided, not sampled user workloads.
Author approval does not establish independent human reproduction, and a
model-generated expectation is not guaranteed ground truth. Dependent
policy/order repetitions do not justify a statistical success-rate estimate
for unseen workloads.

This campaign calls `BackendMatcher.rank_backends` locally. It makes no new
LLM/provider network calls, executes no simulator or physical substrate, and
does not test MCP transport, agent dialogue, placement optimality or physical
safety. Those boundaries must remain explicit in the paper and reviewer
responses.

## Evidence and verification

Local raw archive: `.cp2n2/gemini-selector-confirmatory-20261014-01`.
It contains 72 per-cell observations, aggregate outputs, the complete report,
frozen inputs, source ZIP/hash inventory, environment and freeze/manifest
receipts. The [evidence index](gemini-selector-evidence-index.json) binds the
principal artifacts by SHA-256.

The separate offline verifier passed, including a live source-hash comparison.
It verifies the immutable input bindings, original 290-file source subset,
295-file snapshot, exact matrix coverage, serialized input-only bridge,
raw report identities, normalized reasons and complete report recomputation.
It does not import or call the production selector.

With the existing virtual environment active, verify without rescoring:

```powershell
python -B scripts/run_revision_gemini_selector.py --verify .cp2n2/gemini-selector-confirmatory-20261014-01 --check-live-source
```

For a separate reproduction, use a fresh output directory and omit
`--verify`. Never overwrite or replace the preserved first-run archive.
Later functional source edits will intentionally fail this archive's optional
live-source check; its archived snapshot remains the evaluated source.

## Paper integration status

The subsequent [paper integration](supplementary-paper-integration.md) incorporates
these results with AP1–AP3 into both manuscript views, the cumulative marked
journal version and all relevant entries in the 22-comment response. The
official-template response/checklist and matching source/PDF packages are
rebuilt. Historical source/campaign identities and negative results remain
distinct. New raw publication and final author/submission review remain open.

The existing R5 evidence DOI `10.5281/zenodo.23281161` does **not** cover these
new local campaigns. No commit, push, release, evidence upload or manuscript
submission was performed at this checkpoint.

