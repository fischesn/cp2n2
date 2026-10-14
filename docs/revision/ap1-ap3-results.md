# Supplementary control plane revision results

14 October 2026. AP1–AP3 are implemented and their new, predeclared local
campaigns are verified. The final regression suite passes **402 tests**
(170.46 s; two dependency deprecation warnings). Gemini cases were withheld
during development and measurement; they were subsequently supplied and
[reviewed before execution](gemini-selector-blind-v1/README.md).
After author approval, the [first frozen Gemini run](gemini-selector-results.md)
matches all four outcomes in 72/72 policy/order cells, with 36/36 invariant order
pairs and all original 290 functional/source hashes unchanged. Its later
regression checkpoint passes 486 tests; the AP1–AP3 counts above describe the
earlier checkpoint.
The later [manuscript/response integration](supplementary-paper-integration.md)
updates both paper views and all 22 responses, preserving the earlier R5
checkpoint and negative findings. New raw publication and final author review
remain separate gates.

| Package | Implementation | New verified evidence |
| --- | --- | --- |
| AP1 | Task-scoped telemetry and result validation, preserved cached timestamps | 46 ordinary trials and four detector controls over official MCP sessions |
| AP2 | Structured provider failures, per-resource quarantine and explicit recovery | 18 trials using separate provider/controller/TCP-proxy processes; 96 structured HTTP responses |
| AP3 | Paired timings and measured CPU context under bounded additional load | 80 fresh-registry trials; 32,000 measured operations and 3,200 warmups, all successful |

## Source and evidence identity

The [coordinated source freeze](ap1-ap3-source-freeze.json) was saved before
scored execution. Each campaign contains the same **290 source files**, with
no normalized-content mismatches or duplicate ZIP entries. Per-file hashes
identify the evaluated, uncommitted source; base commit
`bba19db333011aa5c59bc6fa56f29eede536a723` does not identify those new bytes.
The [evidence index](ap1-ap3-evidence-index.json) binds protocols, specifications,
source ZIPs, manifests and verification reports with SHA-256 receipts.

Old R2–R5 archives, their selection oracle and the published evidence remain
unchanged. The historical oracle admits one required `unknown`-drift case;
the updated selector rejects it. Regression tests record that intentional
divergence rather than silently changing the old oracle or asserting that its
original outcomes are reproduced by the new implementation.

## AP1 required evidence and successful delivery

Required numeric evidence rejects nulls, booleans, strings and nonfinite values.
Information age and cost cannot be negative; task-required calibration status
must be `valid`. A positive result-confidence requirement rejects missing,
nonfinite, out-of-range or insufficient confidence. Provider-result parsing no
longer coerces booleans or numeric strings into confidence values.

These checks apply to fields required by the task or its active constraints.
They do not impose an invented universal neural-output schema or make optional
telemetry mandatory. A control with absent optional drift succeeds.

The adapter hook preserves available observation/receipt/expiry timestamps
when republishing cached observations. Required observations reject future
timestamps, expired validity and a violated task age bound. Comparisons between
duplicate representations of the same required property detect the predefined
health contradiction; they do not equate health with lifecycle or calibration
status with confidence. The final live contract rechecks task feasibility
(including changed drift/cost) and the lease immediately before invocation.

The new effect fixture checks only fixed vector input during preparation. It
does not independently reject age/calibration/health telemetry, so the gateway
must prevent the negative cases from reaching its effect-producing invocation.
Post-execution corruptions occur only after the backend records its genuine
commit, with original and exposed results retained separately.

| Ordinary case group | Trials | Starts | Commits | Successful deliveries |
| --- | --- | --- | --- | --- |
| Invalid required preconditions | 28 | 0 | 0 | 0 |
| Valid required evidence, optional-drift and fresh-cache controls | 6 | 6 | 6 | 6 |
| Invalid confidence or post-execution telemetry | 12 | 12 | 12 | 0 |
| Total ordinary cases | 46 | 18 | 18 | 6 |

The four detector trials comprise two deliberately injected bypass commits
and two deny-all cases. The verifier detects all four intended violations,
while still requiring clean leases, workers, audit chains and backend state.
They are excluded from the ordinary forbidden-effect denominator. Across all
50 trials, **120 MCP calls** bind to **240 audit events**. Offline verification
recomputes effect counts, exact perturbations, policy/record/result identities
and timestamp status at the archived request time.

Protocol: [AP1 validation](ap1-validation-protocol.md). Raw archive:
`.cp2n2/ap1-required-evidence-confirmatory-20261014-01`.

This is controlled E0 software evidence. The expired-cache case violates both
expiry and maximum observation age; it does not isolate either branch. No
cryptographic replay protection, sensor-truth guarantee or generic sensor-fusion
claim follows. Bindings must actually supply original metadata to preserve it.

## AP2 provider failure and recovery

Known transport, bounded-read timeout and malformed-payload failures are
reported per resource. Healthy alternatives remain available. Failed resources
remain quarantined after the provider recovers until explicit reconciliation.
All concurrent timed-out read workers are retained, and reconciliation cannot
clear quarantine while a read remains pending or another failure intervenes.
Unexpected planning/precondition programming errors remain visible; an acquired
lease is cleaned up before an unexpected precondition error is re-raised.

An uncertain invocation result prevents automatic retry and fallback execution.
A repeated idempotency key retains that uncertain historical result even after
recovery. Reconciliation checks current provider state; it does not recover a
lost result or retroactively prove that an invocation did not commit.

| Condition | Verified trials | Measured behavior |
| --- | --- | --- |
| Baseline | 3/3 | One commit, then cached same-key replay |
| Planning partition | 3/3 | Structured transport error; no primary effect before explicit recovery |
| Stopped provider | 3/3 | Structured bounded-read timeout; no primary effect before explicit recovery |
| Invalid telemetry object | 3/3 | Structured invalid-telemetry error; no primary effect before explicit recovery |
| Healthy alternative | 3/3 | Secondary executes while primary stays quarantined |
| Lost invocation reply | 3/3 | Primary commits once; no retry/secondary effect; distinct new task only after explicit recovery |

All **96 controller responses** use HTTP 200 with structured action/result
objects, including semantic failures; no generic HTTP 500 occurred. The complete
ledger contains 21 primary and three secondary commits. That total includes
new, explicitly authorized tasks after reconciliation. In each lost-reply
trial, the second final primary commit belongs to that distinct recovery task,
not an automatic retry of the uncertain operation. All owned processes stopped.

During development, the initial classifier expected a transport error for a
stopped provider, while Windows reached the bounded read timeout first. The
negative v1 development report is preserved. Prospective v2 permits either
classification, without changing effect/recovery expectations; it was frozen
before the scored run. The scored stopped-provider trials all report timeout.

Protocol: [AP2 provider errors](revision-ap2-provider-errors-protocol.md). Raw
archive: `.cp2n2/ap2-provider-errors-confirmatory-20261014-01`.

These are actual loopback TCP exchanges between separate local processes, not
physical substrates or multiple hosts. Controller state remains in memory.
The old restart-duplicate negative controls are not fixed by this package;
durable ownership and coordination between controllers remain separate work.

## AP3 timing and CPU context

The [AP3 results](ap3-overhead-results.md) report every direct/controlled path,
median and median-of-trial-p95 interval, actual CPU endpoints, worker cleanup,
and the original R4 intervals extracted offline without new measurements.
The new campaign retains 32,000 measured calls plus 3,200 warmups, with no
failures, monitoring errors or forced worker stops.

Controlled execution medians are 3.43–4.12 ms without intentionally added load
and 4.00–4.56 ms with the owned worker. MCP discovery medians are 14.45 and
14.56 ms. Execution is directed to `bench-0`; varying registered resource count
is not a full automatic-selection scaling study. Several intervals overlap,
so these results do not establish a universal slowdown or a monotonic scaling
trend. The worker achieves roughly 29–37% of one core, not whole-host saturation.

Confidence intervals resample ten fresh-registry trial summaries per condition,
not pooled dependent calls. The p95 interval describes the median of trial p95
values, not a population p95/p99 guarantee. All observations come from one
Windows host and synthetic backends; physical PNN latency is not measured.

## Next revision steps

1. **Complete locally:** preserve the unchanged Gemini output and issued prompt,
   record author-reported model/effort and isolated-chat approval, review and
   freeze expectations before scoring. The [results](gemini-selector-results.md)
   report 72/72 matching cells without functional or expectation tuning.
   Describe twelve externally model-authored synthetic cases, not independent
   software reproduction, 72 independent workloads or guaranteed ground truth.
2. **Complete locally:** integrate the evidence into both manuscript views and
   the cumulative marked journal variant; retain historical source identities
   and narrow telemetry, replay, scaling and recovery wording.
3. **Complete locally:** revise all relevant entries in the 22-comment response,
   explain unaddressed limitations, retain planner deviations and correct the
   historical decisive-selection case descriptions.
4. **Artifacts regenerated:** official response/checklist and manuscript packages
   are rebuilt and checked. Co-author review, independent reproduction and
   separately authorized new raw-evidence publication remain open.

The existing Zenodo DOI `10.5281/zenodo.23281161` covers the previous R5 archive,
not these new local AP archives. No commit, push, release, upload or submission
was performed for this checkpoint.

## Verification commands

Run these commands from the repository root with the existing venv active.
For a fresh environment, install `requirements-evaluation.txt` first; the new
measurement runner directly uses NumPy and psutil. This convenience dependency
manifest was added after the measurement freeze and changes no runtime source
or measured environment. The archived environment versions remain authoritative.

```powershell
python -B scripts/run_revision_ap1_evidence.py --verify .cp2n2/ap1-required-evidence-confirmatory-20261014-01
python -B scripts/run_revision_ap2_provider_errors.py --directory .cp2n2/ap2-provider-errors-confirmatory-20261014-01 --verify-only
python -B scripts/run_revision_ap3_overhead.py --verify .cp2n2/ap3-overhead-confirmatory-20261014-01
python -B -m pytest -q
```

New execution runs require fresh output directories; the frozen archives must
not be overwritten. AP3 timing must run alone, without other tests/campaigns.
