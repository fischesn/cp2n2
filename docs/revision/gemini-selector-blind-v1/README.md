# Gemini selector case review

14 October 2026. The supplied dataset contains **12 synthetic cases**, **47
candidate-resource descriptions**, and **36 policy decisions**. A preexecution
check against the original written prompt finds the declared eligible sets,
complete rankings and selected identifiers consistent under the proposed
failure-label convention below. No production selector has been imported or
executed for this review, and no expected outcome has been changed.

The source and expectations remain separate from the AP1–AP3 functional freeze.
Stefan Fischer confirms that this is the unchanged first response from
**Gemini Flash 3.8 with high effort**. This is an author-reported display name,
not an archived API model identifier. Separate-chat isolation from code,
previous results and the paper still needs explicit author confirmation.

## Preserved material

- [Issued English prompt](prompt-issued.txt), recovered from its original message.
- [Original Gemini response](gemini-response-original.json), copied byte-for-byte
  from the attachment. Its SHA-256 is
  `24ac85aa6f4266eef574cedbb42861931aa0907339d45b689b4669d18ef229a1`.
- [Provenance](provenance.json), including the author's model/effort and
  unchanged-first-response confirmation.
- [Preexecution review](preexecution-review.json), containing the declared
  rule interpretation, resource sets, rankings, selections and the literal
  overlapping-rule alternative.

The receipt date is known; a generation date and provider request identifier
are not inferred. The issued prompt is not a captured Gemini API request.

## Proposed rule interpretations for approval

1. `admissible_resource_ids` denotes resources that pass **both admission and
   feasibility**, hence all and only those entering ranking.
2. **F4** reports required-but-missing drift. **F6** reports numeric drift
   `>= 0.95`. The prompt's additional F6 sentence restates the null requirement.
   A strictly literal reading could label case 07's `res-missing-drift` with
   both F4 and F6, while Gemini reports F4. Both readings reject exactly the
   same resource and produce the same rankings. Keep the original F4-only
   annotation and record this prospective convention before any scored run;
   do not infer it from software results.
3. The second component of **S is explicitly fixed to zero in the prompt**.
   The general specification names health sensitivity at this tuple position;
   this restricted fixture uses a neutral constant. It is not a new confidence
   score or an implemented placeholder for future work.

Under these interpretations, all 12 eligible sets, all 36 complete rankings,
and all 36 selected values agree with the prompt-derived arithmetic. There
are 27 eligible resource declarations across cases. Case 01 has no eligible
resource; cases 02, 04 and 08 each have one; the remaining eight have several.

Gemini's original prose has two minor wording inaccuracies: case 01 mentions
multi-rule admission failures although its own admission failures are
single-rule (case 08 covers simultaneous admission failures); case 05 calls
the resources identical although only A/B form the exact tie and C has a
different latency. Neither affects an input or an expected outcome. Every task
in this restricted domain has an active positive age bound, so case 06's
null-age exclusion is consistent; do not generalize it to tasks outside that
domain.

## Expected choices for author review

The second column gives candidates / eligible resources. The full inputs,
exclusion reasons and complete ranking orders are in the original response.

| Case | Candidates / eligible | Lexicographic | Latency first | Locality and cost first |
| --- | --- | --- | --- | --- |
| 01 | 4 / 0 | none | none | none |
| 02 | 4 / 1 | edge-workhorse | edge-workhorse | edge-workhorse |
| 03 | 3 / 3 | res-alpha-health | res-beta-speed | res-gamma-local |
| 04 | 5 / 1 | node-exact-boundary | node-exact-boundary | node-exact-boundary |
| 05 | 3 / 3 | cluster-worker-a | cluster-worker-a | cluster-worker-a |
| 06 | 4 / 3 | res-cost-known-free | res-cost-known-free | res-cost-known-free |
| 07 | 4 / 2 | res-telemetry-ok-precise | res-telemetry-ok-fast | res-telemetry-ok-precise |
| 08 | 4 / 1 | res-autonomous-vector | res-autonomous-vector | res-autonomous-vector |
| 09 | 5 / 3 | node-healthy | node-unknown | node-healthy |
| 10 | 4 / 4 | worker-clean | worker-clean | worker-clean |
| 11 | 4 / 3 | dev-faster-cloud | dev-faster-cloud | dev-deterministic-node |
| 12 | 3 / 3 | host-cloud-hyperscale | host-cloud-hyperscale | host-edge-cheap |

## Campaign gate and next step

Author approval is pending for the case semantics, expected sets/rankings/
choices and the three interpretations above. Confirm that the generation
used a fresh Gemini chat with only the issued prompt and no implementation,
paper or previous results. Then freeze the unchanged dataset, interpretation
decision, provenance and existing functional source identity before creating
any production outcome.

The scored extension will compare eligible sets, full ranking and selected
resource for all three policies, then repeat with reversed input order.
Those 72 policy/order comparisons are deterministic checks, not 72 independent
cases. Exclusion reporting must use a predefined semantic rule mapping that
keeps the F4/F6 ambiguity visible; no case expectation may be tuned after
observing production output.

For the paper, describe **externally model-authored synthetic cases reviewed
against a written contract**, not independent human validation, real workloads
or proven placement optimality. The current review is not a completed selector
experiment. No paper edits, commit, push, publication or provider call accompany
this intake.
