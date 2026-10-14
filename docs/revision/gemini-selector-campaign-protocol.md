# Gemini selector campaign protocol

14 October 2026. This protocol fixes the supplementary selector study before
the first production observation on the externally authored cases. The author
has [approved the cases and interpretations](gemini-selector-approval.json)
and confirmed an isolated new Gemini chat, without the implementation, paper
or previous results. The original [intake](gemini-selector-blind-v1/README.md)
is immutable; its pending-approval fields describe that earlier checkpoint.

## Inputs and source boundary

Use exactly the twelve unchanged Gemini cases, with original response SHA-256
`24ac85aa6f4266eef574cedbb42861931aa0907339d45b689b4669d18ef229a1`.
Preserve the issued prompt, original response, author-reported model/effort,
intake receipt, preexecution review, approval and this protocol. The model is
author-reported as Gemini Flash 3.8 with high effort; no API request identifier,
exact backend model identifier or generation timestamp is invented.

All 290 normalized source hashes from the pre-receipt
[AP1–AP3 freeze](ap1-ap3-source-freeze.json) must match before and after this
study. No adapter, matcher, orchestrator, task model, old oracle or historical
campaign may be tuned to the Gemini outcomes. A new harness/source snapshot
adds only the reader, production bridge, offline verifier and tests. A dirty
base Git commit does not identify those new bytes.

Before production imports, freeze all inputs, environment and source ZIP with
per-file SHA-256 bindings, including a canonical digest for each complete
Gemini case and its expected outputs. Validate JSON types, explicit fields,
finite input numbers, unique identifiers and expectation-set consistency.

## Fixed observation matrix

Twelve cases × three policies × two resource orders gives **72 deterministic
cells**, not 72 independent workloads. Policies are `lexicographic`,
`latency_first` and `locality_cost_first`. Orders are the original resource
array and its exact reversal. A fresh matcher is used for each cell.

The primary outcomes are exact agreement with Gemini's eligible resource set,
complete ranking and selected resource (including null). Report these metrics
separately as well as their conjunction. Preserve every first-run raw report
and any exception; an exception is a failed cell, not an omitted observation.
No retry, case deletion or expected-outcome adjustment is permitted.

This tests `BackendMatcher.rank_backends`, not MCP transport, an executing
agent, physical PNN performance or real-world placement optimality. No external
provider, biological substrate, simulator execution or network call is needed.

## Input-only bridge

Reuse the frozen R4 `production_inputs` bridge on a deep copy containing only
case identifier, task and resources. Never pass the `expected` section to this
bridge. Add only fixed harness fields `policy="lexicographic"` and `seed=41`;
the observed policy is supplied explicitly. Do not replace the matcher's
default drift threshold or use the old R4 oracle to produce expectations.

The bridge retains classification/digital-vector input, undirected selection,
false continuous monitoring/repeated-invocation requirements, supported
confidence reporting (the inherited minimum confidence is 0.2), common false
health sensitivity (S second component zero), and nonempty supported reset
modes. These fixed capabilities do not vary with expected outputs. All supplied
age/cost nulls, reservability and contract-admissibility booleans are preserved.
Retain serialized tasks, descriptors and runtime state for offline checks.

## Rejection annotations

Eligibility means passing both admission and feasibility. Rejection-stage and
semantic-rule conformance are secondary outcomes, separate from placement.
The author-approved convention reports required missing drift as F4 and the
numeric drift limit as F6. The original overlapping F4/F6 wording remains
visible in the immutable review and does not change exclusion or ranking.

| Production constraint | Prompt rule |
| --- | --- |
| input_modality_compatible | A1 |
| freshness_observable | A2 |
| human_supervision_policy | A3 |
| resource_contract_safety | A4 |
| runtime_available | F1 |
| lifecycle_available | F2 |
| resource_reservable | F3 |
| latency_budget | F5 |
| drift_threshold | F6 |
| telemetry_freshness | F7 |
| cost_budget | F8 |

`required_telemetry_available` is property-specific: missing `drift_score` maps
to F4, missing `age_of_information_ms` to F7, and missing active-budget
`estimated_cost` to F8. The aggregate required-runtime message names only drift
in this restricted domain. Preserve duplicate raw violations; deduplicate
only their normalized semantic-rule IDs. Admission failures retain the raw
feasibility-not-evaluated marker but score only their admission violations.

Any unmapped rule, unexpected `required_telemetry_semantics` diagnostic, or
additional violated condition remains visible and fails annotation agreement;
it is not silently folded into a permitted error. The approved numeric domain
excludes malformed numbers and negative ages/costs, so such a diagnostic would
require investigation. There are 282 candidate records across the full matrix;
they are repeated checks of 47 authored candidates, not 282 independent cases.

## Verification and interpretation

Archive all 72 outputs, source inventory, input/freeze/manifest receipts and
the complete report. The offline verifier imports no production selector:
it verifies hashes and source binding, exact matrix coverage, input-only
bridge identity, normalized rules, raw report identities and full
report recomputation. Historical archive files are never overwritten.

Unit development uses fabricated report-shaped objects, not scored outcomes
from these cases. The confirmatory run is the first production evaluation on
the frozen dataset. Report failures honestly; correcting a harness error needs
a separately identified and disclosed new run, not replacement of first-run data.

The study strengthens external case authorship under a written contract. It
does not establish independent human validation, representative empirical
workloads, software reproduction by an external team or physical safety.
Paper/reviewer-response integration and evidence publication remain separate
steps after the results are known.
