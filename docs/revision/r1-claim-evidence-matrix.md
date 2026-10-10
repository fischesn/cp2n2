# R1 claims and evidence

**Date:** 9 October 2026. **Scope:** manuscript and contract corrections only;
no new campaign or physical execution. The preserved submission and evidence
remain the baseline described in [baseline-inventory.md](baseline-inventory.md).

The revised paper separates four questions. Planner conformity measures whether
a model selects the specified disposition. Admission/enforcement concerns what
the server permits. Execution integrity concerns the causal link between an
admitted task, backend effects and a validated result. Physical validity concerns
whether those observations describe the real substrate correctly. Evidence for
one question does not automatically answer the others.

## Claim audit

| Claim and manuscript location | Existing evidence | Supported interpretation and R1 action | Remaining package |
|---|---|---|---|
| Abstract: agent safety | Confirmatory fixture v1.2; 160 decisions; execution disabled | Removed the assertion that 100% of executed actions were strictly safe. All 160 trials meet the archived non-commitment criterion; there was no substrate execution. | R3: direct invalid requests and executing positive controls |
| Abstract: planner quality | 141/160 conformant; physical-execution class 1 refusal, 19 clarifications | Preserve 141/160 and 1/20 together, not only the aggregate. No oracle change. | R3: independently frozen executing campaign |
| Abstract: orchestration overhead | 25 local runs per twin, separate from A6's 945 requests | State mean local overhead below 1 ms; do not attribute that measurement to the concurrency campaign. | R4: larger measurements and uncertainty |
| Introduction/contributions: novelty | PNRC, matcher, leases, lifecycle, audit, assay catalog | Domain contract and reference integration, not a new transport, lease, state-machine, or cryptographic algorithm. Remove universal claims that no other framework can express it. | R5: final contribution audit |
| Architecture captions: twin validity | Software state/proxies and declared confidence | Architecture responsibilities are distinguished from validated physical estimation; evaluated paths are software only. | H1: optional physical validation |
| PNRC: operational bounds | `resource_contract.py`; adapter declarations | Schema validity does not mean every limit has an executable validator. Enumerate generic checks versus binding-specific obligations. | R2/R3: semantic validators |
| PNRC: units and ranges | Chemical/wetware/edge adapters and twin runtimes | Table of actual units, preparation predicates and absent upper/physical bounds; no automatic unit conversion. | R3: malformed/NaN/unit/range cases |
| Calibration and drift | Declared confidence 0.90/0.84/0.95; synthetic runtime metrics | These are not measured calibration errors. Optional calibration does not automatically gate generic admission. | R3: required/unsupported/stale calibration cases; H1 for physical accuracy |
| Atomic exclusive leases | `InMemoryLeaseStore`, shared `TwinRegistry`, existing concurrent-client tests | Atomic acquisition within one controller process/registry, not replicated or durable coordination. | R3: observable overlap; expanded architecture is separately authorised |
| Timeout and expiry | Phase timeouts, unreachable state, explicit reconciliation tests | Timeout stops waiting, not the worker; lease expiry is not cancellation. No automatic reuse while completion remains unresolved. | R2/R3: late completion, lost reply, quarantine |
| Idempotency | Completed-result replay and key-conflict tests | Client-scoped in-memory guarantee; no promise across controller restart. | R2/R3: observable duplicate-effect tests |
| Telemetry provenance | Value/unit/source/time/uncertainty/validity fields | Identity/origin, freshness, physical truth and calibration are distinct. A fresh report may be wrong. | R3: stale/replayed/missing/conflicting observations |
| Telemetry freshness | Base adapter validity 30 s; task age bounds | `valid_until=None` is not automatically stale. Generic non-physical health may be `unknown`; stricter requirements need explicit binding/task gates. | R3: enforce and demonstrate the declared requirements |
| Claim matrix and evaluation headings | Existing E0--E3 artifacts | No cumulative maturity ladder or upgrade from software to physical evidence. | R5: final evidence labels |
| Selector suite | Seven curated tasks, four holdouts, 32 weighted perturbations | Conformance on curated cases, not optimal placement. Perturbing unused weights is not robustness evidence for the lexicographic policy. | R4: independent cases and meaningful boundary perturbations |
| A6 distributed campaign | Four same-host processes, 30 cells, 945 requests | Application-layer fault/contention behavior; no WAN, packet-level or replicated-controller result. | R4: bounded network experiments |
| Contention and throughput | Immediate busy outcomes, exclusive resource | Not a queueing, scheduler fairness or scalability benchmark. | R4: separate offered load, completion, rejection and fairness metrics |
| Two E3 traces | Eight MCP requests/16 events; separate official SDK recording | MCP trace did not start the official SDK run, locally or remotely. Shared application hashes do not establish one causal execution. | R2: continuous task-to-native-recording manifest |
| Native recording consistency | 14 trials, 24 stimulations, 60 spikes; exact reconstruction | API/recording/decoder consistency for deterministic software data, not learning or biological performance. | R2: identity-bound validation; H1 physical study |
| Agent aggregate table | Archived `safe_action` field and Wilson intervals | Display as non-commitment criterion; interval is not probability of physical safety. Preserve raw field in baseline. | R3: effect-based enforcement metrics |
| Agent failure and reproducibility | Parsed decisions/audits retained; raw responses absent | 19 errors belong to one 20-trial class. Parsed artifacts cannot reconstruct all model-serving details. | R3: retain redacted raw responses and model metadata |
| General result validation | `_validate_postconditions` | Checks supplied confidence, required field presence, requested age and offline state; no generic full payload, identity or native recording verifier. | R2/R3: independent result/identity/completeness checks |
| Related-work table | Primary specifications and preview announcement | Replace binary yes/no score with documented responsibility and remaining domain binding. No conformance or superiority claim. | R5: final reviewer response |
| Conclusion/future work | Same existing results | Continuous E3 and active-effect tests come before optional E5. No hardware or broad security claim. | R2--R5; H1 separately |

## Contract and test handoff

[Binding contracts and invariants](r1-binding-contracts-and-invariants.md)
specifies the R2/R3 acceptance gates and distinguishes existing checks from
proposed tests. [Comparison and citation decisions](r1-comparison-and-citation-log.md)
records primary-source scope and the six suggested references.

The authoritative manuscript is `cp2n2.tex` in the paper repository. Its neutral
arXiv view must be regenerated with `prepare_arxiv_submission.py`. The
reviewer-response source records actual text changes without claiming that
R2--R4 experiments are complete. R1 does not alter software functionality,
baseline metrics, the oracle, figures, or retained experiment files.

### R2 development handoff

R1's audit above describes the preserved submission and its corrections. The
new [R2 execution checkpoint](r2-sdk-execution.md) adds a continuous MCP-to-SDK
development path with independent native-event reconstruction. It does not
retroactively connect the two historical E3 traces, replace the old agent
campaign, or add a completed R2 result to the manuscript. R2 recovery is now
complete in the local Windows E3 scope: the [result report](r2-recovery-results.md)
records 18/18 verified conditions and 179 passing regression tests. The
comprehensive reviewer response will incorporate the new evidence through R5
after the required packages are complete. This handoff note does not change
the historical R1 verification counts below.

### R4 measurement handoff

The historical claim audit above remains the R1 baseline. The later
[R4 results](r4-evaluation-results.md) and
[container report](r4-container-results.md) add measured evidence for R5:

| Claim boundary | New measured evidence | Required R5 interpretation |
| --- | --- | --- |
| Selector conformance | 64 synthetic cases, five common-information policies and 19 active sensitivity conditions | Twelve sample sets/selections have post-run author approval; not independent validation of all cases, optimal placement or physical calibration |
| Contention and overhead | Three capacity-one resources, 225 requests; 16,000 timed operations and trial-level intervals | No queue/fairness, shared-capacity or multi-environment performance claim |
| Transport faults | 21 Windows process trials plus 21 separate-container trials/57 additional attempts | Actual HTTP/TCP byte-stream faults; same physical host, not packets, WAN or MCP-network latency |
| Idempotency and recovery | Same-process reply/retry protection; duplicates in 3/3 restart trials in each topology | Explicitly exclude durable restart safety; trace persistence is not state restoration |
| Pre-invocation provider failure | 18 HTTP 500 responses in each topology, zero effects | No-effect observation is not structured quarantine; retain the error-handling limitation |

No journal/arXiv text, historical R1 verification count or physical evidence
label is changed by this handoff. The comprehensive reviewer response must
incorporate these results and limits during R5 rather than report all expected
negative controls as safety successes.

## R5 integration audit — 10 October 2026

The R1 audit and verification below remain historical. The new evidence is
integrated in both manuscript views, and all 22 reviewer-response drafts
distinguish completed work, bounded results and declined/unimplemented requests.
See [R5 integration results](r5-integration-results.md).

| Revised claim | Evidence now reported | Retained limit/negative result |
| --- | --- | --- |
| Continuous MCP-to-SDK execution | 18 trials across nine conditions; 110 MCP calls, 220 audit events, 14 SDK starts | E3 simulator only; independent native consistency, not biological learning |
| Active enforcement | 80 ordinary direct cases and four detector controls; 464 bounded state transitions | Finite cases/bounds, not arbitrary concurrency or physical safety |
| Executing agent integration | Qwen: 24/32 strict matches, 6/8 permitted executions, two SDK runs, two active stale-health blocks | All eight deviations retained; model-visible freshness limitation; no cross-model improvement claim |
| Selection/systems behavior | 64 synthetic cases, five policies, 225 contention requests, 16,000 timed operations, process/container TCP faults | Author-defined cases; one host/performance environment; no fairness/WAN/replicated architecture claim |
| Recovery/idempotency | Reply-loss/duplicate handling in process; observed restart duplicates in both topologies | No durable restart idempotency; early HTTP 500s remain unstructured |
| Reproduction/availability | Clean local source checkpoint, 286 tests and 18 zero-exit reproduction/verification jobs; hash/CRC-checked candidate | Same host/environment; no new LLM/container/timing campaign; independent reproduction and public archive pending |

The old non-executing campaign is unchanged in its archive. Its detailed tables
are removed from the main paper, while the response explicitly retains
141/160 aggregate conformity and 1/20 in the physical-execution prompt class.
The new campaign is the main evaluation because it exercises backend effects,
not because results can be compared as a controlled improvement.

## R1 verification (historical)

- Existing software regression suite: **146 passed**, one external dependency
  deprecation warning. This is not a new evaluation campaign.
- Journal preview: **18 pages**, Biber 2.21; neutral arXiv preview: **26 pages**,
  Biber 2.21. All 44 pages were rendered and visually inspected; after a code-token
  line-break correction, all changed pages were re-inspected and the other page
  images were byte-identical to the reviewed renderings.
- Generated arXiv source exactly matches the current journal-to-arXiv generator.
  Both source archives pass ZIP CRC verification; `git diff --check` passes.
- Original private baseline archive remains unchanged, SHA-256
  `cdd10b6285cda2d89a1ef34caa20c2e3141c2e5b08247403658f06ea97ad026a`.
- Current revision preview PDF SHA-256:
  clean journal `31afd79f136c024032b16881d7b098aa794e111462e42d7ade7f14908986bbc5`;
  yellow-marked journal `8d126ee89ae58fce9461368864a195445bc2541859409fd735dea8401bc9d4a4`;
  arXiv `6ed34efe97be6a770735a9244b3d6d6446109ef58c52a928cfb72ba19580a079`.

The journal hashes above include the later R1 revision-highlighting workflow
added on the same date. Both journal views have 18 pages and the same content;
all pages were visually reviewed. Nine markup/workflow tests pass, including
exact preservation of the generated clean arXiv source. No new experiment or
scientific-text change was introduced by the highlighting step.
  These identify **R1 working copies**, not the original submission or an
  author-approved final resubmission.

The IEEE template still emits font-substitution and output-box warnings, with
some minor paragraph warnings; the previews have no visible clipping/overlap
on the inspected pages. No commit, push, release or external upload was performed.
