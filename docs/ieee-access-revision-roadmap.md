# CP²N² reviewer-driven revision roadmap

**Date:** 9 October 2026

**Status:** Original submission/evidence preserved; R1 text and specification
complete; R2 execution bridge validated in development; R2 recovery and R3–R5 pending

**Trigger:** IEEE Access decision on manuscript `Access-2026-43996`

**Scope:** A bounded systems-paper revision, with an independent physical-substrate follow-up

## Quick overview — required work and final outputs

| Step | What we will do | Current status |
|---|---|---|
| R0 | Preserve the original submission and inventory its evidence | Inventory complete; protocol freezes/editor reply pending |
| R1 | Make claims, novelty, and contracts precise | COMPLETE — text/specification; no new results |
| R2 | Connect MCP admission to one actual SDK Simulator execution | IN PROGRESS — bridge/native checks work; recovery experiments pending |
| R3 | Demonstrate enforcement using permitted and forbidden backend effects | TODO |
| R4 | Strengthen selection, measurement, contention, and fault experiments | TODO |
| R5 | Integrate the evidence, revise both manuscript views, and prepare the resubmission | TODO |
| H1 | Explore real-substrate access as an optional follow-up | Separate; not a revision dependency |

**Mandatory for an IEEE Access resubmission — not optional:**

- [ ] A comprehensive **response to every reviewer comment**: introductory
  note, summary of completed changes, and 22 individual concern/response/action
  entries with manuscript locations and evidence. Reasoned disagreement must
  also receive a substantive answer.
- [ ] A revised **highlighted PDF**, marking all changes, including grammar,
  against the preserved original submission.
- [ ] A **clean revised PDF and matching LaTeX source package**.
- [ ] Author-approved response, checklist, evidence, and submission decision.

The paper repository's `IEEE-ACCESS-RESPONSE-TO-REVIEWERS.md` is the working
response source/matrix; it is not yet a finished rebuttal. The verified starting
point is documented in the [baseline inventory](revision/baseline-inventory.md).

## 1. Decision and evidence boundary

The immediate objective is to strengthen the evidence for the CP²N² control
plane, not to benchmark the computational superiority of a PNN or start a new
biological-learning study. We will work through four revision packages:

1. **R1 — Claims, novelty, and resource contracts.** Make the contribution and
   its limits precise, including what is reused from existing middleware.
2. **R2 — One continuous executing E3 trace.** Connect an MCP-started task to
   an actual local CL SDK Simulator run and its independently validated output.
3. **R3 — Active enforcement during execution.** Test permitted and forbidden
   actions against an observable, state-changing test backend, separately from
   the quality of the LLM's plan.
4. **R4 — Stronger selection and systems methodology.** Expand independently
   specified cases, meaningful sensitivity tests, measurement quality, and
   bounded network/recovery experiments.

R0 establishes the baseline and protocol; R5 integrates and packages the results.
H1 is a separate, optional hardware-feasibility track. No current-paper package
depends on Cortical Cloud becoming available.

E3 is SDK-simulator execution, not physical or biological evidence. A
state-changing mock is still a mock, even when it exposes meaningful forbidden
side effects. Policy enforcement is not a proof of physical safety. Hash-bound
traces establish consistency between artifacts; they do not establish that a
compromised provider reports the physical world truthfully.

A scope-clarification email has been drafted. Sending it and receiving an
answer are separate steps; neither is assumed here. In particular, whether
physical hardware and persistent,
multi-controller coordination are prerequisites for an Access resubmission
remains an editorial question. The bounded revision is useful regardless of
the answer; expensive architectural expansion is not silently included.

## 2. Work order and scope controls

| Stage | Dependency | Main output | Completion gate |
|---|---|---|---|
| R0 | None | Baseline inventory and frozen evaluation protocols | Old and new evidence remain distinguishable |
| R1 | R0 inventory | Claims, contracts, comparison, response skeleton | Every intended claim has evidence or an explicit limitation |
| R2 | R1 execution contract | Executing MCP-to-SDK E3 bundle | A new SDK run is causally linked to the admitted MCP task |
| R3 | R1 invariants; R2 valid execution path | Active-enforcement campaign | Permitted actions execute; rejected actions cause no forbidden effect |
| R4 | R0 protocols; R1 claim scope | Selection, overhead, contention, and fault bundles | Conclusions match the tested configurations and uncertainty |
| R5 | R1–R4 acceptance gates | Revised paper, response, and submission artifacts | Independent reproduction and claim audit pass |
| H1 | Separate feasibility decision | Physical-access matrix and optional pilot protocol | Hardware mode, permissions, provenance, and costs are established |

R4's protocol design can proceed while R2/R3 are implemented, but experiments
must not be redesigned after inspecting confirmatory results. Each package is
reviewed with the authors before starting the next substantial package.

**Not included by default:** a replicated control plane, consensus protocol,
production scheduler, persistent cross-controller lease service, large LLM
leaderboard, new biological training algorithm, or a paid hardware booking.
If any becomes necessary, record a separate decision, effort estimate, and
claim change before implementation.

Do not promise a new release number or calendar submission date yet. Estimate
effort after R0/R1 and reassess after the executing E3 path works.

## 3. R0 — Preserve the submission and freeze the revision protocol

**Status:** IN_PROGRESS. Baseline inventory complete on 9 October 2026;
new protocol freezes and editor-scope follow-up remain pending. See the
[baseline inventory](revision/baseline-inventory.md). This is preparation,
not a rewrite of the old results.

- [x] R0.1 Identify and archive the exact as-submitted PDF, source, bibliography,
  figures, submission package, and editorial decision. Do not assume the
  current local manuscript is identical to the submitted version.
- [x] R0.2 Record the published software baseline: v5.1.1, commit
  `36fbae002b0a9e066416ea9cafbb966a33fe53bb`, version DOI
  `10.5281/zenodo.21887895`. Preserve the released artifacts and their hashes.
- [x] R0.3 Inspect current branches and local changes before creating a
  revision branch. Preserve unrelated changes and temporary files. No
  automatic merge, release replacement, or history rewrite.
- [x] R0.4 Build an evidence inventory distinguishing the legacy control-plane
  trace, separate CL SDK trace, dry-run agent campaign, selector suite, and
  same-host distributed campaign. Record what each does and does not show.
- [x] R0.5 Create a response matrix for all reviewer points, with the requested
  change, our interpretation, planned action, evidence location, and status.
  Explicitly justify declined or narrowed requests rather than ignoring them.
- [ ] R0.6 Freeze new case definitions, oracle construction, seeds, repetition
  counts, metric definitions, failure criteria, and analysis scripts before
  confirmatory runs. Separate development/pilot runs from final evidence.
- [ ] R0.7 Track the scope-clarification email as `drafted`, `sent`, or
  `answered`, with the actual answer if available. R1 need not wait for it.

**Done when:** someone other than the implementer can identify which statements
belong to the old submission and reproduce the planned scoring without using
new experimental outcomes to redefine success.

## 4. R1 — Claims, novelty, and resource-contract precision

**Status:** COMPLETE (text/specification only), 9 October 2026.
R2--R4 execution and new measurements remain pending.

Verified outputs:

- [Claims and evidence](revision/r1-claim-evidence-matrix.md)
- [Binding contracts and R2/R3 invariant/test specification](revision/r1-binding-contracts-and-invariants.md)
- [Comparison and six-reference citation assessment](revision/r1-comparison-and-citation-log.md)
- Corrected journal source and regenerated neutral arXiv view; individual R1
  reviewer-response drafts in the paper repository.

No runtime functionality, baseline metric, oracle or original evidence was changed.
The requirements-contract reference remains unassessed beyond metadata because
publisher text was unavailable; it was not inserted as a verified citation.
A bounded property test is specified for R3, not reported as implemented.

### R1.1 Claim and terminology audit

- [x] Create a claim-to-evidence matrix covering the abstract, introduction,
  contributions, evaluation, conclusion, tables, captions, and artifact docs.
- [x] Separate four questions: planner conformity, admission/enforcement,
  execution/result integrity, and physical-substrate validity.
- [x] Replace broad safety claims with measured policy properties and their
  trust assumptions. The legacy 160/160 result remains a dry-run result, not
  evidence of safe physical execution or of a general security guarantee.
- [x] Keep the physical-execution prompt class visible: one oracle-conformant
  refusal and 19 clarifications in 20 trials. A clarification may avoid an
  unsafe action while still failing the specified planner oracle.
- [x] State the existing lease boundary: atomicity within one logical control
  plane and the documented shared-registry scope, not durable replicated
  coordination. Clarify which recovery states require reconciliation.
- [x] State the telemetry trust model. Authentication proves source identity,
  not semantic correctness. Discuss stale, replayed, missing, and conflicting
  observations; identify compromised sensing/providers as a remaining limit.

### R1.2 Objective contribution and related-work comparison

- [x] Separate reused mechanisms (MCP transport, ordinary authorization,
  leases, state machines, checksums) from the resource-contract integration,
  ordering of admission/selection, evidence labels, and implemented bindings.
- [x] Define comparison criteria before filling the table. Distinguish native
  mechanisms, possible extensions, demonstrated integrations, and features
  outside a system's scope; avoid an all-yes versus all-no superiority table.
- [x] Check primary, versioned sources for PhysMCP, Model Hardware Standard,
  and the relevant general middleware/control-plane approaches. Explain the
  PNN-specific gap without claiming those systems cannot be extended.
- [x] Assess suggested citations individually. Include directly relevant
  work with an explained connection; do not add unrelated intrusion-detection
  or optimization references merely because a reviewer listed them.

### R1.3 Concrete contract and invariants

- [x] Document each backend binding's input/output units, valid ranges, timing
  assumptions, calibration/validity fields, freshness rules, allowed
  operations, approval scope, and result-validation postconditions.
- [x] Identify which fields are observed, provider-declared, synthetic,
  unknown, or unsupported. Missing information must not become a healthy or
  calibrated default. Synthetic thresholds are not physical measurements.
- [x] Document lifecycle transition preconditions, exclusive-lease ownership,
  expiry, duplicate-request/idempotency behavior, terminal outcomes, and
  fail-closed handling when execution status cannot be established.
- [x] Specify cross-binding conformance tests for the implemented mock/twin
  and E3 bindings. A common control contract does not imply identical neural
  dynamics or interchangeable task semantics.
- [x] Define executable invariants for R2/R3: no forbidden commit, no
  overlapping exclusive ownership in the supported scope, no unvalidated
  successful result, and no automatic reuse after an unresolved execution.
- [x] Decide whether a small bounded state-space/property test adds useful
  evidence. If implemented, document its bounds; do not call it an unbounded
  proof of physical safety.

**Outputs:** updated contract documentation, claim matrix, objective comparison,
reviewer-response skeleton, and manuscript corrections that require no new
results. Edit `cp2n2.tex` and regenerate the arXiv view through the existing
workflow; never fill pending results with invented numbers.

**Done when:** every claim is demonstrably supported, explicitly conditional,
or narrowed; all R2/R3 admission and execution postconditions are specified.

## 5. R2 — Continuous MCP-to-CL-SDK execution at E3

**Status:** IN PROGRESS. **Purpose:** close the gap between the two existing E3 traces.

**First checkpoint:** the MCP path now launches a fresh official SDK Simulator
run and validates decisions independently from native stimulation/spike tables.
The success manifest and offline verifier are implemented; the legacy traces
remain unchanged. See the [R2 execution protocol](revision/r2-sdk-execution.md).
Cooperative abort, dedicated recovery bundles and confirmatory recovery analysis
are still pending; R2 is not complete.

### R2.1 Implement the real execution bridge

- [x] Map an admitted high-level BioPattern Gate task to a constrained,
  versioned CL application configuration. An agent must not invent primitive
  stimulation settings or override approved bounds.
- [x] Have the MCP execution path start a **new** official SDK Simulator run
  through the provider-facing application path. Importing an old result or
  replaying a Web Demo bundle is not execution.
- [x] Run discovery/selection, admission, lease acquisition, lifecycle start,
  SDK execution, native HDF5 validation, sanitized result delivery, and
  finalization under the documented contract.
- [x] Keep the simulator guard and E3 label. The bridge must not enable Cloud
  or physical execution by accident.

### R2.2 Bind and verify the complete trace

- [x] Bind the principal, MCP request/task, resource, lease, execution attempt,
  SDK run, configuration/decoder/source hashes, native recording, validated
  result, and audit events in one manifest.
- [x] Use provider identifiers where actually supplied; label controller-
  assigned local identifiers as such. An ID or file hash is not provider
  attestation of biological execution.
- [x] Reconstruct the result independently from native HDF5 and compare it
  with the delivered sanitized result. Reject mismatched configuration,
  substituted artifacts, partial data disguised as success, and bad checksums.
- [x] Record observed MCP-call and audit-event counts. Do not force the new
  run to retain the legacy eight-call/16-event counts.

### R2.3 Execution and recovery cases

- [ ] Cover successful execution, invalid configuration rejected before
  launch, cooperative abort, failed SDK launch, validation failure, lost reply,
  and duplicate/retried request.
  Development tests cover all listed cases except cooperative abort; full
  case-specific experiment bundles remain pending. Lost-reply recovery uses
  the existing status/result tools; a repeated terminal `run_assay` is rejected,
  not replayed as a second execution.
- [x] Define timeout behavior: either establish termination and reconcile, or
  retain an explicit unresolved/quarantined state. Do not release a resource
  for reuse merely because the caller timed out.
- [ ] Specify which retry operations are idempotent and how execution attempts
  are distinguished. Demonstrate no duplicate backend commit where guaranteed.
- [ ] Preserve partial recordings with truthful terminal status. Verify lease
  release on established completion and the documented treatment of unknown
  completion.

**Outputs:** implementation/tests, one success bundle, negative/recovery bundles,
an offline verifier, and updated execution documentation. The Web App may replay
the new bundle, but a replay remains a presentation artifact, not a new run.

**Done when:** a fresh MCP task demonstrably starts a fresh SDK execution,
result validation is independent, and lifecycle/lease outcomes are reproducible
for success and failure. This remains local, non-biological E3 evidence.

## 6. R3 — Active enforcement and a bounded executing-agent campaign

**Status:** TODO. **Purpose:** test the control boundary, not just safe plans.

### R3.1 Observable backend effects and direct negative tests

- [ ] Provide an isolated state-changing backend with a durable test log or
  equivalent independent observation of starts, commits, cancellations, and
  results. State mutation is test evidence, not physical execution.
- [ ] Define forbidden effects for each case: unauthorized start, unapproved
  parameters, conflicting exclusive ownership, duplicate commit, stale/unknown
  resource use, or successful delivery of an invalid artifact.
- [ ] Send deliberately invalid plans directly through the actual server
  boundary, including authorization, approval, stale telemetry, lease conflict,
  invalid units/ranges, wrong result identity, and lifecycle violations.
- [ ] Do not let the evaluation oracle pre-filter those plans before the
  server sees them. Use the oracle for independent scoring afterwards.
- [ ] Include valid positive controls that really execute. Zero side effects
  from a harness that rejects everything is not successful enforcement.
- [ ] Use an isolated deliberately faulty test double or an equivalent
  negative control to show that the effect detector notices a forbidden
  commit. Never introduce a bypass into the production execution path.

### R3.2 Bounded LLM campaign

- [ ] Freeze a separately versioned executing campaign. Preserve the earlier
  dry-run campaign and its oracle unchanged.
- [ ] Specify permitted E3/mock execution and prohibited physical requests;
  distinguish `refuse`, `clarify`, rejection, and execution in the scoring.
- [ ] Include a small, specified adversarial extension: multi-turn pressure,
  untrusted tool-result instruction injection, role confusion, and selected
  multilingual variants. Declare exact cases and scope before final runs.
- [ ] Fix model/version, prompt, tool schemas, sampling settings, repetitions,
  request budgets, and stopping rules. A second model is a bounded extension
  if available, not a prerequisite for a general-purpose LLM benchmark.
- [ ] Record full permitted request/response material for new runs, parsed
  decisions, tool calls, backend effects, audit verification, and reconciliation.
  Remove credentials and sensitive content with documented sanitization.
  Old missing raw responses cannot be reconstructed retrospectively.

### R3.3 Separate outcomes and report failures

- [ ] Report planner oracle conformity, policy decision correctness, actual
  permitted execution, forbidden backend effects, result integrity, and
  lifecycle/lease reconciliation as separate metrics with denominators.
- [ ] Distinguish model refusal, server rejection, SDK/application failure,
  validation failure, and unresolved resource state.
- [ ] Publish case-level outcomes, including failed plans and failed runs.
  Zero observed forbidden effects is a bounded empirical result, not a claim
  that arbitrary agents or compromised providers are safe.
- [ ] Verify invariants against independent backend observations, not only
  the same audit producer that reports successful enforcement.

**Outputs:** direct-enforcement tests, frozen executing-agent protocol,
sanitized campaign archive, independent effect checks, and per-case analysis.

**Done when:** valid tasks demonstrably execute, invalid tasks reach the server
and are blocked before forbidden effects, and planner mistakes can be separated
from enforcement failures. Any observed failure is retained and explained.

## 7. R4 — Selection, overhead, contention, and fault methodology

**Status:** TODO. Four bounded subpackages, not a production-platform redesign.

### R4.1 Independently specified selection suite

- [ ] Freeze an expanded suite, initially targeting at least 60 cases. Cover
  zero/one/multiple admissible resources, conflicting constraints, ties,
  missing/ambiguous telemetry, lifecycle/readiness costs, and near-boundary
  freshness/validity conditions. Fix coverage counts before scoring.
- [ ] Derive expected admissible sets and tie outcomes independently of the
  production selector. Review a sample manually or with a second author.
- [ ] Define fair, explicit baselines and a common information budget. Do not
  silently give one baseline telemetry or hard constraints the others lack.
- [ ] Publish every case, expected set, selected outcome, rejection rationale,
  and explanation of any advantage over the baseline. Retain the original
  seven-plus-four suite as historical evidence, not the new confirmatory set.
- [ ] Perturb parameters the tested policy actually uses: hard thresholds,
  validity/freshness boundaries, lexicographic priority order, and tie rules.
  Weight changes are meaningful only for a weighted policy; unused weights
  cannot demonstrate robustness of a lexicographic selector.
- [ ] Label all simulated drift, age, calibration, and health data as synthetic.
  Threshold sensitivity does not establish real-substrate prediction accuracy.

### R4.2 Bounded multi-resource contention

- [ ] Add at least three independently identifiable test resources, mixed
  exclusive/non-exclusive access where supported, different lease durations,
  and competing clients. Freeze client/load levels and resource capacities.
- [ ] Measure admission/completion, rejection reasons, latency, lease overlap,
  expiry, and reconciliation per resource, not only aggregate throughput.
- [ ] State whether queueing is implemented. If not, evaluate immediate
  admission/rejection and do not describe it as a general scheduler.
- [ ] Keep all coordination claims within the actual single-controller/shared-
  registry scope. Multiple clients are not multiple persistent controllers.

### R4.3 Overhead measurement

- [ ] Freeze the machine, OS/runtime, versions, transport, topology, payloads,
  resource counts, baseline operation, timer, warm-up, and measurement window.
- [ ] Increase independent repetitions and observations beyond the legacy
  25-local/15-HTTP samples. Select sample counts before final measurement;
  use a pilot only to determine feasibility and timing noise.
- [ ] Report median and adequately supported tail quantiles, throughput under
  defined load, dispersion/confidence intervals, and the resampling unit.
  Do not treat dependent calls in one run as independent experiments or quote
  a stable p99 without enough observations.
- [ ] Separate control-plane overhead from SDK/substrate task duration.
  Archive raw timings, environment metadata, and analysis inputs.
- [ ] Repeat on a second independently deployed environment if practical;
  otherwise state the single-environment limit rather than generalizing it.

### R4.4 Network and recovery extension

- [ ] Preserve the old same-host/application-layer campaign as such. Add an
  explicitly documented deployment with separate containers or hosts and
  actual transport-level delay/loss/partition injection where feasible.
  Containers on one host do not establish multi-host external validity.
- [ ] Freeze topology, impairment location, clock assumptions, independent
  seeds, repetition counts, and recovery expectations. Record measured rather
  than merely requested impairment when instrumentation permits.
- [ ] Cover provider interruption, connection loss/lost reply, client retry,
  and controller restart. Test no forbidden reuse while outcome is unknown.
- [ ] Before restart testing, specify what is persisted and how startup
  detects/reconciles an unfinished task. If recovery is unsupported, expose
  that limitation; an in-memory registry cannot prove durable lease safety.
- [ ] Keep replicated controllers, transactional external leases, and broad
  crash-tolerance guarantees out of scope unless separately approved.

**Outputs:** expanded selector fixtures and case table, meaningful sensitivity
plots, multi-resource results, raw overhead data/analysis, and a bounded
transport/recovery archive.

**Done when:** all reported effects can be reproduced from raw artifacts and
the paper states exactly which resource, network, and recovery configurations
were tested. Unsupported generality is removed rather than inferred.

## 8. R5 — Integrate, reproduce, and decide the submission route

**Status:** TODO. No new submission is authorized by this roadmap.

- [ ] Review R1–R4 results, including negative results and remaining gaps.
  Update the claim matrix before writing stronger conclusions.
- [ ] Revise the IEEE Access source `cp2n2.tex`; regenerate the neutral arXiv
  source using `prepare_arxiv_submission.py`. Keep scientific content aligned,
  while retaining publisher-specific front/back matter only where required.
- [ ] Replace stale result tables/captions and clarify historical versus new
  experiments. Bind the manuscript to the exact revision commit and archive.
- [ ] Complete and export the comprehensive response-to-reviewers document:
  introduction, completed-change summary, all 22 individual concerns,
  substantive responses, actual remedial actions, manuscript locations,
  measurements/artifact IDs, and reasoned responses to unimplemented requests.
  No planned action or pending placeholder may be presented as completed work.
- [ ] Obtain the official response template and resubmission checklist named
  in the decision email; their attachments have not yet been located locally.
- [ ] Produce the all-changes-highlighted revised PDF, including grammar
  changes, against the frozen original. Verify its scientific identity with
  the clean revised PDF and matching LaTeX package.
- [ ] Run software tests, artifact verification, clean-checkout reproduction,
  both PDF builds, visual inspection, bibliography checks, and source/package
  consistency checks. No credentials or private provider/proposal documents
  may enter public artifacts.
- [ ] Have a co-author reproduce the key execution and enforcement results
  without relying on undocumented local state and review every response for
  accuracy, completeness, and appropriate tone.
- [ ] Decide the venue after checking the editor's scope response and the
  evidence actually obtained. If a physical study or replicated durable
  architecture is required, decide explicitly whether to extend or move the
  bounded systems paper rather than repeatedly expanding it by default.
- [ ] Reassess current scopes and submission requirements for a different
  venue if needed. Previous fallback candidates were *Computer Standards &
  Interfaces*, *SN Computer Science*, *Future Internet*, and *Computers*;
  this is a decision list, not a commitment or acceptance prediction.
- [ ] Only after author review and explicit authorization: commit/push,
  publish a new immutable software/evidence release, update archival records,
  and generate the final submission/arXiv packages.

**Done when:** the revised manuscript, response, source, release, evidence,
and submission packages agree, and the authors approve the submission route.

## 9. H1 — Optional physical-substrate feasibility and follow-up paper

**Status:** OPTIONAL / TODO. No access, booking, outreach, or execution is assumed.

The DECIPHER access worksheet identifies **CL1 plus BrainScaleS-2** as its
preferred contrasting pair, with **FinalSpark Neuroplatform** and **IBM Analog
AI as a Service** as alternatives. Therefore, “the two other platforms” does
not yet define a unique pair for CP²N². Select the intended alternatives before
committing to two new adapters.

| Candidate | Why investigate | Boundary to establish |
|---|---|---|
| BrainScaleS-2 / EBRAINS | Electronic analogue/mixed-signal contrast to CL1; documented research-access route in DECIPHER | Physical hardware mode versus mock mode; actual allocation, identifiers, calibration, queueing, and available controls |
| FinalSpark Neuroplatform | Alternative biological access if CL1 remains delayed | Actual live stimulation/readout rights versus recorded data; availability, permitted experiment, provenance, and institutional requirements |
| IBM Analog AI as a Service | Conditional analogue/in-memory-computing alternative | Current service availability; actual hardware versus simulation; authentication, export, and supported tasks |

These are proposal-derived candidates, not freshly verified CP²N² access
commitments. BrainScaleS-2's term “physical neural emulation” can refer to real
analogue hardware; software mock mode cannot. FinalSpark recordings alone do
not demonstrate an intervention performed by CP²N². IBM simulation is not
hardware evidence. Check the actual execution mode and provenance in every run.

- [ ] H1.1 Select which candidates to investigate first. BrainScaleS-2 is the
  natural first contrasting route in the existing DECIPHER plan; do not assume
  a second alternative is already selected or available.
- [ ] H1.2 Verify current official access documentation and record auth,
  quotas, costs, publication/export rights, permitted operations, and relevant
  institutional/provider approvals. Do not copy private proposal attachments
  or commercial correspondence into the public repository.
- [ ] H1.3 Build a feasibility matrix for task submission, stable resource/run
  identity, status, timing, calibration, cancellation, result retrieval,
  reconciliation, and concurrent use. Unknown interfaces remain unknown.
- [ ] H1.4 Define the smallest provider-approved physical task that exercises
  the control plane: admission, reservation/access, bounded execution,
  validated readout, and finalization. It need not reproduce BioPattern Gate
  literally or claim PNN learning superiority.
- [ ] H1.5 Estimate adapter effort and dependencies. Decide whether the
  available provider semantics support CP²N²'s required guarantees or require
  a narrower binding. No placeholder adapter may claim E5 conformance.
- [ ] H1.6 Obtain explicit authorization before contacting providers,
  creating accounts, booking paid time, or running physical interventions.
  Freeze a pilot protocol before execution and retain failure evidence.
- [ ] H1.7 Treat integration into the current revision as optional and
  time-bounded. If access is late or the scientific scope grows, keep it out of
  R1–R5 and develop a separate follow-up paper.

**Possible follow-up contribution:** how one control contract maps to real,
heterogeneous substrates; which resource-state, calibration, timing, lease,
cancellation, and recovery assumptions survive actual provider constraints;
and which adaptations measured runs require. Two genuinely different physical
platforms would support stronger heterogeneity claims than one. One physical
pilot supports only its demonstrated binding, not universal portability.

This would be a distinct empirical systems contribution, not the current
paper with hardware screenshots added. A new learning/biology study is a
separate decision. Cortical Labs remains a valid later route, not the only one.

## 10. Reviewer coverage and response ownership

The identifiers below refer to the supplied decision, not new requirements
invented by this roadmap. Final responses must quote or summarize each point
accurately and state what we changed or deliberately bounded.

| Reviewer point | Revision route | Required evidence or explicit boundary |
|---|---|---|
| R1.1 — Novelty over middleware | R1.2 | Objective comparison and reused/new mechanisms |
| R1.2 — Physical validation and generality | R1.1, H1, R5 | Simulator/prototype scope; optional physical pilot; editorial scope decision |
| R1.3 — Safety wording without execution | R1.1, R2, R3 | Bounded policy language and active execution/effect observations |
| R2.1 — Missing real PNN backend | R1.1, H1, R5 | No E3-to-E5 substitution; narrow claims or separately approved E5 study |
| R2.2 — Novelty/comparison criteria | R1.2 | Criteria fixed independently of the completed comparison |
| R2.3 — Curated selection workload | R4.1 | Larger independently specified suite and case-level results |
| R2.4 — Contention versus scheduling | R4.2 | Multi-resource experiment; no unsupported scheduler claim |
| R2.5 — Topology/fault methodology | R4.4 | Transport faults, independent repetitions, explicit deployment limits |
| R2.6 — In-process lease atomicity | R1.1, R4.4 | Scope and restart behavior; no replicated durable guarantee |
| R2.7 — Dry-run safety versus protection | R3.1–R3.3 | Invalid plans at the server boundary and observable forbidden effects |
| R2.8 — Explicit physical-execution prompt class | R1.1, R3.2–R3.3 | Per-class refusal/clarification/planner/enforcement distinction |
| R2.9 — Narrow agent/adversarial campaign | R3.2 | Frozen bounded adversarial extension; model coverage stated |
| R2.10 — Trust in provider telemetry | R1.1, R1.3 | Source authenticity versus truth, replay/conflicts, compromised-provider limit |
| R2.11 — Twin validity/calibration | R1.3, R4.1 | Synthetic threshold sensitivity without physical predictive claims |
| R2.12 — Policy versus physical safety | R1.1, R1.3, R3.3 | Explicit invariants, trust assumptions, optional bounded property checks |
| R2.13 — Overhead sample size/tails | R4.3 | Warm-up, repetitions, uncertainty, adequately supported quantiles |
| R2.14 — Suggested literature | R1.2 | Relevance assessment rather than indiscriminate citation |
| R2.15 — Artifact reproducibility | R0, R3.2, R5 | Exact baseline, new sanitized raw records, independent reproduction |
| R3.1 — No active execution protection | R2, R3 | Positive executions and negative effects checked independently |
| R3.2 — MCP trace does not launch SDK run | R2 | Continuous execution identity and native recording validation |
| R3.3 — Cross-binding contract | R1.3, R2 | Concrete units, ranges, timing, validity, and postconditions |
| R3.4 — Curated selector/weight sensitivity | R4.1 | Per-case oracle results and perturbations that affect the policy |

Before closing a package, identify the responsible implementer, analysis
reviewer, and manuscript reviewer. Author assignments are pending; this plan
does not allocate work to co-authors without agreement.

## 11. Checkpoint protocol and immediate next action

At every checkpoint:

1. run the package-specific tests and artifact checks;
2. record completed task IDs, changed files, evidence IDs, and limitations;
3. update the response and claim matrices, including failed cases;
4. synchronize scientific manuscript changes through the established arXiv
   generator when relevant;
5. ask for the next implementation package and, separately, any commit/push
   or external action the authors want.

**Next action:** finish R2 recovery: cooperative SDK cancellation, independently
checked timeout/abort/lost-reply bundles and a frozen confirmatory protocol.
Freeze each new experiment's protocol before its confirmatory runs; editor-scope tracking
remains pending. Do not start H1 adapter code, buy hardware time, or expand
the software into a replicated scheduler as an implicit consequence of this
roadmap.

## 12. Related project documents

- [Full master plan](project-masterplan.md) — retains the completed A–D history.
- [Lifecycle, leases, and errors](lifecycle-leases-and-errors.md).
- [Admission, feasibility, and selection](admission-feasibility-selection.md).
- [Provider-facing BioPattern Gate execution](cl-api-biopattern-gate-execution.md).
- [Existing Agent-to-PNN campaign](agent-to-pnn-evaluation-campaign.md).

This document is the current source of truth for reviewer-driven next work.
Earlier submission checklists remain historical and must not override the
scope and evidence gates above.
