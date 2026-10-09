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

## Verification

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
