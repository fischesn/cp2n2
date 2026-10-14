# CP²N² reviewer-driven revision roadmap

**Date:** 10 October 2026

**Status:** Original submission/evidence preserved; R1 text and specification
complete; R2 execution/recovery complete at local Windows E3; R3 direct/state
and live Qwen campaigns complete in bounded local scope, with planner failures
retained; R4 selection/contention/timing, bounded TCP and separate-container
results verified; twelve oracle sample outcomes approved by Stefan Fischer;
R4 complete in bounded scope; R5 technical draft prepared, with author,
independent-reproduction and submission gates still open; R5 and supplementary
raw-evidence publication gates closed by separately verified Zenodo versions

**Trigger:** IEEE Access decision on manuscript `Access-2026-43996`

**Scope:** A bounded systems-paper revision, with an independent physical-substrate follow-up

## Quick overview — required work and final outputs

| Step | What we will do | Current status |
|---|---|---|
| R0 | Preserve the original submission and inventory its evidence | Inventory and measured-package freezes complete; editor reply pending |
| R1 | Make claims, novelty, and contracts precise | COMPLETE — text/specification; no new results |
| R2 | Connect MCP admission to one actual SDK Simulator execution | COMPLETE — native validation and 18/18 trials across nine recovery conditions verified |
| R3 | Demonstrate enforcement using permitted and forbidden backend effects | COMPLETE — direct/state and live Qwen evidence verified; eight planner deviations retained |
| R4 | Strengthen selection, measurement, contention, and fault experiments | COMPLETE in bounded scope — measurements verified and twelve oracle sample outcomes author-approved |
| R5 | Integrate the evidence, revise both manuscript views, and prepare the resubmission | IN_PROGRESS — local paper/22-response/package draft prepared; raw evidence public; author, independent-reproduction and submission gates open |
| H1 | Explore real-substrate access as an optional follow-up | Separate; not a revision dependency |

### Supplementary packages completed on 14 October 2026

The [supplementary results](revision/ap1-ap3-results.md) are a new source/evidence
checkpoint after the published R5 archive, not a rewrite of historical results.

| Package | Purpose | Status |
| --- | --- | --- |
| AP1 | Validate required telemetry, cached metadata and result confidence | COMPLETE locally — 46 ordinary and four detector trials verified |
| AP2 | Normalize provider failures and require explicit recovery | COMPLETE locally — 18 separate-process/TCP trials verified |
| AP3 | Report timing intervals and measured CPU context under bounded load | COMPLETE locally — 32,000 measured calls plus 3,200 warmups verified |
| Externally authored selector cases | Evaluate cases generated separately by Gemini | COMPLETE locally — author-approved and frozen; all four outcomes agree in 72/72 policy/order cells; 36/36 invariant order pairs; see [results](revision/gemini-selector-results.md) |
| R5 follow-up integration | Update both paper views, yellow markup, all 22 responses, checklist and artifacts | COMPLETE locally — after meaning-preserving compaction, 20-page clean/marked journal, 29-page arXiv and 13-page response rebuilt; [integration report](revision/supplementary-paper-integration.md); supplementary raw evidence public under DOI23377537; final author approval remains open |

The Gemini-harness checkpoint passed 486 tests; the subsequent precommit
regression suite passes 522, including 36 supplementary publication/packaging
tests. These do not change the frozen campaign observations. The AP1–AP3 [source freeze](revision/ap1-ap3-source-freeze.json)
and [evidence index](revision/ap1-ap3-evidence-index.json) bind those campaigns
to the same 290 normalized source files. The [Gemini index](revision/gemini-selector-evidence-index.json)
binds its 295-file snapshot, preserving all original 290 hashes. The twelve
externally authored synthetic cases are not 72 independent workloads.
No durable restart/competing-controller,
physical-substrate or general replay-safety claim is added. The existing R5 DOI
does not cover this new evidence. The [supplementary evidence version](revision/supplementary-zenodo-publication.md),
DOI `10.5281/zenodo.23377537`, publishes the complete byte-preserved AP1–AP3 and
Gemini archives, separately labelled AP2 development traces and historical R4
offline analysis. All four archived campaign verifiers pass; all five new
files were anonymously downloaded and match their complete SHA-256 hashes.
The earlier R5 and v5.1.1 records are unchanged. Do not close independent
reproduction, author approval or resubmission gates on the strength of archive
publication and automated verification alone.

**Mandatory for an IEEE Access resubmission — not optional:**

- [x] A comprehensive **draft response to every reviewer comment**: introductory
  note, summary of completed changes, and 22 individual concern/response/action
  entries with manuscript locations and evidence. Reasoned disagreement must
  also receive a substantive answer.
- [x] A revised **highlighted PDF**, marking all changes, including grammar,
  against the preserved original submission.
- [x] A **clean revised PDF and matching LaTeX source package**.
- [ ] Author-approved response, checklist, evidence, and submission decision.

The paper repository's `IEEE-ACCESS-RESPONSE-TO-REVIEWERS.md` is the working
response source; all 22 substantive drafts are exported into the supplied
official Word template, but author approval is pending. The verified starting
point is documented in the [baseline inventory](revision/baseline-inventory.md).
The [versioned reviewer-material folder](revision/ieee-access/README.md)
mirrors the draft as Markdown, Word and PDF, and preserves the official
checklist. Its [ten-item status overview](revision/ieee-access/RESUBMISSION-CHECKLIST-STATUS.md)
tracks final checks and upload categories without marking author boxes complete.

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
- [x] R0.6 Freeze new case definitions, oracle construction, seeds, repetition
  counts, metric definitions, failure criteria, and analysis scripts before
  confirmatory runs. Separate development/pilot runs from final evidence.
  R2's recovery protocol and source snapshot are frozen and its 18 executions
  verified; R3 direct/state/agent inputs are also frozen and verified. R4's
  four measured subpackages have pre-run protocols/specifications/source
  snapshots and verified raw archives. Any later container extension needs
  its own freeze; it is not covered by the completed same-host TCP freeze.
- [ ] R0.7 Track the scope-clarification email as `drafted`, `sent`, or
  `answered`, with the actual answer if available. R1 need not wait for it.

**Done when:** someone other than the implementer can identify which statements
belong to the old submission and reproduce the planned scoring without using
new experimental outcomes to redefine success.

## 4. R1 — Claims, novelty, and resource-contract precision

**Status:** COMPLETE (text/specification only), 9 October 2026.
At the R1 checkpoint, R2--R4 execution and new measurements were pending.
R2/R3 are now complete in the bounded scopes recorded below; R4 has measured
results and explicit remaining scope/review gates.

Verified outputs:

- [Claims and evidence](revision/r1-claim-evidence-matrix.md)
- [Binding contracts and R2/R3 invariant/test specification](revision/r1-binding-contracts-and-invariants.md)
- [Comparison and six-reference citation assessment](revision/r1-comparison-and-citation-log.md)
- Corrected journal source and regenerated neutral arXiv view; individual R1
  reviewer-response drafts in the paper repository.

No runtime functionality, baseline metric, oracle or original evidence was changed.
The requirements-contract reference remains unassessed beyond metadata because
publisher text was unavailable; it was not inserted as a verified citation.
A bounded state exploration was specified in R1 and implemented/verified in R3;
it is not an exhaustive concurrency or physical-safety proof.

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

**Status:** COMPLETE at local Windows E3, 9 October 2026.
**Purpose:** close the gap between the two existing E3 traces.

**First checkpoint:** the MCP path now launches a fresh official SDK Simulator
run and validates decisions independently from native stimulation/spike tables.
The success manifest and offline verifier are implemented; the legacy traces
remain unchanged. See the [R2 execution protocol](revision/r2-sdk-execution.md).
Cooperative abort, owned-process termination, truthful partial evidence,
timeout/quarantine and retry bundles are now verified under the separately
frozen [recovery protocol](revision/r2-recovery-protocol.md). The
[result report](revision/r2-recovery-results.md) records 18/18 passing conditions,
110 MCP calls, 220 audit events, 14 SDK starts, offline verification and 179
passing regression tests. This does not enable Cloud/physical execution or
constitute a new LLM campaign. Paper integration remains R5 work.

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

- [x] Cover successful execution, invalid configuration rejected before
  launch, cooperative abort, failed SDK launch, validation failure, lost reply,
  and duplicate/retried request.
  All nine frozen conditions pass twice with case-specific bundles, including
  a deliberate parent crash and confirmed/unconfirmed timeout. Lost-reply recovery uses
  the existing status/result tools; a repeated terminal `run_assay` is rejected,
  not replayed as a second execution.
- [x] Define timeout behavior: either establish termination and reconcile, or
  retain an explicit unresolved/quarantined state. Do not release a resource
  for reuse merely because the caller timed out.
- [x] Specify which retry operations are idempotent and how execution attempts
  are distinguished. Demonstrate no duplicate backend commit where guaranteed.
- [x] Preserve partial recordings with truthful terminal status. Verify lease
  release on established completion and the documented treatment of unknown
  completion.

**Outputs:** implementation/tests, one success bundle, negative/recovery bundles,
an offline verifier, and updated execution documentation. The Web App may replay
the new bundle, but a replay remains a presentation artifact, not a new run.

**Done when:** a fresh MCP task demonstrably starts a fresh SDK execution,
result validation is independent, and lifecycle/lease outcomes are reproducible
for success and failure. This remains local, non-biological E3 evidence.

## 6. R3 — Active enforcement and a bounded executing-agent campaign

**Status:** COMPLETE in bounded local software/E3 scope, 10 October 2026. **Purpose:** test the control boundary,
not just safe plans. The [local result report](revision/r3-enforcement-results.md)
records 80/80 ordinary conditions, 4/4 detected fault controls, 464/464 bounded
state transitions and 260 passing tests. The agent pipeline's 32-case deterministic
reference includes six mock commits and two fresh native-validated E3 SDK runs.
These reference outcomes are not LLM results. The separately frozen
[v2 agent protocol](revision/r3-agent-protocol-v2.md) specifies the author-approved
replacement of unavailable `minimax-m2.7` with `qwen3.8-27b`, with non-thinking
requested and a separate excluded capability probe. The [live result report](revision/r3-agent-qwen-results.md)
retains 24/32 exact planner matches, 6/8 permitted executions, two active stale-health
blocks, zero forbidden effects and 32/32 reconciled states. All eight deviations
and the model-visible freshness limitation are documented. No prompt/oracle tuning
or replacement campaign was performed. Native artifact publication remains R5 work.
The paper and legacy campaign are unchanged.

### R3.1 Observable backend effects and direct negative tests

- [x] Provide an isolated state-changing backend with a durable test log or
  equivalent independent observation of starts, commits, cancellations, and
  results. State mutation is test evidence, not physical execution.
- [x] Define forbidden effects for each case: unauthorized start, unapproved
  parameters, conflicting exclusive ownership, duplicate commit, stale/unknown
  resource use, or successful delivery of an invalid artifact.
- [x] Send deliberately invalid plans directly through the actual server
  boundary, including authorization, approval, stale telemetry, lease conflict,
  invalid units/ranges, wrong result identity, and lifecycle violations.
- [x] Do not let the evaluation oracle pre-filter those plans before the
  server sees them. Use the oracle for independent scoring afterwards.
- [x] Include valid positive controls that really execute. Zero side effects
  from a harness that rejects everything is not successful enforcement.
- [x] Use an isolated deliberately faulty test double or an equivalent
  negative control to show that the effect detector notices a forbidden
  commit. Never introduce a bypass into the production execution path.
- [x] Compare the bounded two-client/two-request, six-macro-event state model
  with the actual control surface; archive witnesses, graph coverage, independent
  effects and offline checks. Do not claim exhaustive concurrency or physical safety.

### R3.2 Bounded LLM campaign

- [x] Freeze a separately versioned executing campaign. Preserve the earlier
  dry-run campaign and its oracle unchanged.
- [x] Specify permitted E3/mock execution and prohibited physical requests;
  distinguish `refuse`, `clarify`, rejection, and execution in the scoring.
- [x] Include a small, specified adversarial extension: multi-turn pressure,
  untrusted tool-result instruction injection, role confusion, and selected
  multilingual variants. Declare exact cases and scope before final runs.
- [x] Fix model/version, prompt, tool schemas, sampling settings, repetitions,
  request budgets, and stopping rules. A second model is a bounded extension
  if available, not a prerequisite for a general-purpose LLM benchmark.
- [x] Record full permitted request/response material for new runs, parsed
  decisions, tool calls, backend effects, audit verification, and reconciliation.
  Remove credentials and sensitive content with documented sanitization.
  Old missing raw responses cannot be reconstructed retrospectively.

### R3.3 Separate outcomes and report failures

- [x] Report planner oracle conformity, policy decision correctness, actual
  permitted execution, forbidden backend effects, result integrity, and
  lifecycle/lease reconciliation as separate metrics with denominators.
- [x] Distinguish model refusal, server rejection, SDK/application failure,
  validation failure, and unresolved resource state.
- [x] Report case-level outcomes locally, including failed plans and failed runs;
  publication of the sanitized native archive is explicitly retained as R5 work.
  Zero observed forbidden effects is a bounded empirical result, not a claim
  that arbitrary agents or compromised providers are safe.
- [x] Verify invariants against independent backend observations, not only
  the same audit producer that reports successful enforcement.

**Outputs:** direct-enforcement tests, frozen executing-agent protocol,
sanitized campaign archive, independent effect checks, and per-case analysis.

**Done when:** valid tasks demonstrably execute, invalid tasks reach the server
and are blocked before forbidden effects, and planner mistakes can be separated
from enforcement failures. Any observed failure is retained and explained.

## 7. R4 — Selection, overhead, contention, and fault methodology

**Status:** COMPLETE in bounded scope, 10 October 2026. R4.1–R4.3 measurement
packages and the bounded same-host TCP and separate-container extensions are
verified. Stefan Fischer approved the twelve frozen oracle sample outcomes
after the runs; see the [approval record](revision/r4-oracle-approval.md).
This is not a production-platform redesign. See the [protocol](revision/r4-protocol.md),
[results and negative findings](revision/r4-evaluation-results.md), and
[exact archive index](../evaluation/fixtures/r4-confirmatory-20261010.json).
The container extension has its own [report](revision/r4-container-results.md)
and [frozen index](../evaluation/fixtures/r4-container-confirmatory-20261010.json).

| Part | Measured result | Remaining gate |
| --- | --- | --- |
| R4.1 | 64 cases, five policies, reversed-order checks; 19 active sensitivity conditions | Twelve sample outcomes approved by Stefan Fischer; not independent validation of all 64 cases |
| R4.2 | Three resources, 225 requests, 60 completions, 165 busy rejections, zero overlaps | No shared-capacity or scheduler claim |
| R4.3 | 16,000 measured operations; trial-level intervals and separate MCP measurement | Single-machine scope retained |
| R4.4 | 21 Windows TCP and 21 Linux container trials; restart duplicates in 3/3 trials of each | Single-host boundary; no durable restart guarantee |

### R4.1 Independently specified selection suite

- [x] Freeze an expanded suite, initially targeting at least 60 cases. Cover
  zero/one/multiple admissible resources, conflicting constraints, ties,
  missing/ambiguous telemetry, lifecycle/readiness costs, and near-boundary
  freshness/validity conditions. Fix coverage counts before scoring.
- [x] Derive expected admissible sets and tie outcomes independently of the
  production selector. Twelve analytical sample checks by the authoring agent
  are frozen; this is not human author approval.
- [x] Obtain human author or second-author sign-off on the twelve frozen
  oracle sample outcomes before manuscript integration/publication. Stefan
  Fischer confirmed admissible sets and selections on 10 October 2026;
  this is post-run author review, not pre-run human validation.
- [x] Define fair, explicit baselines and a common information budget. Do not
  silently give one baseline telemetry or hard constraints the others lack.
- [x] Archive every case, expected set, selected outcome, rejection rationale,
  and explanation of any advantage over the baseline. Retain the original
  seven-plus-four suite as historical evidence, not the new confirmatory set.
  Public raw-archive publication remains R5 work.
- [x] Perturb parameters the tested policy actually uses: hard thresholds,
  validity/freshness boundaries, lexicographic priority order, and tie rules.
  Weight changes are meaningful only for a weighted policy; unused weights
  cannot demonstrate robustness of a lexicographic selector.
- [x] Label all simulated drift, age, calibration, and health data as synthetic.
  Threshold sensitivity does not establish real-substrate prediction accuracy.

### R4.2 Bounded multi-resource contention

- [x] Add at least three independently identifiable test resources, mixed
  exclusive/non-exclusive access where supported, different lease durations,
  and competing clients. Freeze client/load levels and resource capacities.
- [x] Measure admission/completion, rejection reasons, latency, lease overlap,
  expiry, and reconciliation per resource, not only aggregate throughput.
- [x] State whether queueing is implemented. If not, evaluate immediate
  admission/rejection and do not describe it as a general scheduler.
- [x] Keep all coordination claims within the actual single-controller/shared-
  registry scope. Multiple clients are not multiple persistent controllers.

### R4.3 Overhead measurement

- [x] Freeze the machine, OS/runtime, versions, transport, topology, payloads,
  resource counts, baseline operation, timer, warm-up, and measurement window.
- [x] Increase fresh-trial repetitions and observations beyond the legacy
  25-local/15-HTTP samples. Select sample counts before final measurement;
  use a pilot only to determine feasibility and timing noise.
- [x] Report median and adequately supported tail quantiles, throughput under
  defined load, dispersion/confidence intervals, and the resampling unit.
  Do not treat dependent calls in one run as independent experiments or quote
  a stable p99 without enough observations.
- [x] Separate control-plane overhead from SDK/substrate task duration.
  Archive raw timings, environment metadata, and analysis inputs.
- [x] Assess a second independently deployed environment; unavailable here.
  State the single-environment limit rather than generalizing it.

### R4.4 Network and recovery extension

- [x] Preserve the old same-host/application-layer campaign as such. Add an
  explicitly documented deployment with separate containers or hosts and
  actual transport-level delay/loss/partition injection where feasible.
  Containers on one host do not establish multi-host external validity.
  Docker Desktop was subsequently repaired/updated with author authorization.
  Four fresh containers and one bridge network per trial now fulfill the
  separate-container request in 21 additional trials; this remains one host.
  All temporary owned containers/networks were removed, with evidence retained.
- [x] Freeze the feasible loopback topology, impairment location, clock
  assumptions, deterministic conditions, repetition counts, and recovery
  expectations. No random seeds are implied for fixed conditions. Record
  measured rather than merely requested impairment when instrumentation permits.
- [x] Cover provider interruption, connection loss/lost reply, client retry,
  and controller restart. Test no forbidden reuse while outcome is unknown.
- [x] Before restart testing, specify what is persisted and how startup
  detects/reconciles an unfinished task. If recovery is unsupported, expose
  that limitation; an in-memory registry cannot prove durable lease safety.
- [x] Keep replicated controllers, transactional external leases, and broad
  crash-tolerance guarantees out of scope unless separately approved.

The restart cases observe duplicate durable effects in 3/3 Windows trials
and 3/3 container trials. This is
the expected unsupported guarantee, not three safety successes. Pre-invocation
partition/provider termination yields 18 generic HTTP 500 responses rather
than structured CP²N² lifecycle errors. Present nonnumeric drift remains
admissible at the descriptor selector. R5 must retain these limits, distinguish
failed HTTP delivery from explicit quarantine, and avoid broader safety claims.

**Outputs:** expanded selector fixtures and case table, meaningful sensitivity
plots, multi-resource results, raw overhead data/analysis, and a bounded
transport/recovery archive.

**Done when:** all reported effects can be reproduced from raw artifacts and
the paper states exactly which resource, network, and recovery configurations
were tested. Unsupported generality is removed rather than inferred.

## 8. R5 — Integrate, reproduce, and decide the submission route

**Status:** IN_PROGRESS — technical draft prepared, 10 October 2026. See the
[R5 integration report](revision/r5-integration-results.md). No new submission
is authorized by this roadmap.

- [x] Review R1–R4 results, including negative results and remaining gaps.
  Update the claim matrix before writing stronger conclusions.
- [x] Revise the IEEE Access source `cp2n2.tex`; regenerate the neutral arXiv
  source using `prepare_arxiv_submission.py`. Keep scientific content aligned,
  while retaining publisher-specific front/back matter only where required.
- [x] Replace stale result tables/captions and clarify historical versus new
  experiments. Bind the manuscript to the exact evaluated source checkpoint
  and local archives. The public archive is now published and its exact new
  DOI is integrated into the matching manuscript/response exports.
- [x] Complete and export the comprehensive response-to-reviewers draft:
  introduction, completed-change summary, all 22 individual concerns,
  substantive responses, actual remedial actions, manuscript locations,
  measurements/artifact IDs, and reasoned responses to unimplemented requests.
  No planned action or pending placeholder may be presented as completed work.
- [x] Obtain the official response template and resubmission checklist named
  in the decision email; use the two author-supplied attachments. Preserve
  checklist requirements and leave author checkboxes unchecked.
- [x] Produce the all-changes-highlighted revised PDF, including grammar
  changes, against the frozen original. Verify its scientific identity with
  the clean revised PDF and matching LaTeX package.
- [x] Run software tests, artifact verification, clean-checkout reproduction,
  both PDF builds, visual inspection, bibliography checks, and source/package
  consistency checks. The bounded local workflow passed 286 tests/18 jobs;
  it reused the host/environment and did not rerun live LLM/container/timing
  campaigns. See the report for these limits.
- [x] Publish the new evidence archive after the author authorized Zenodo
  publication and provider-budget privacy transformations: DOI
  `10.5281/zenodo.23281161`, version `R5-2026-10-10`. All ten campaign verifiers
  pass on the public copy; scientific payloads and private originals are
  unchanged. See the [publication record](revision/r5-zenodo-publication.md).
- [x] Replace publication-pending wording with verified DOI
  `10.5281/zenodo.23281161` in the manuscript and reviewer response; rebuild
  and check the clean/marked journal, neutral arXiv and response exports.
- [x] Publish the subsequent AP1–AP3/Gemini evidence after separate author
  authorization: DOI `10.5281/zenodo.23377537`, version
  `SUPPLEMENTARY-2026-10-14`. Four archived campaign verifiers pass; the full
  ZIP and four supporting files match their local hashes after anonymous
  download. Historical records and inherited files are unchanged. See the
  [supplementary publication record](revision/supplementary-zenodo-publication.md).
- [x] Integrate the supplementary DOI citation and technically verify matching
  rebuilt journal, arXiv and reviewer-response packages. After author-requested
  meaning-preserving shortening, all 85 output pages,
  source/PDF bindings, template fidelity and reviewer mirrors pass; 25 paper
  workflow and 36 supplementary publication/packaging tests pass. Final author
  approval remains open.
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
- [x] Record the author's 10 October authorization to commit/push the working
  revision and reviewer documents. This is not release or submission approval.
- [ ] After final author review and explicit authorization, generate the final
  submission/arXiv packages and decide whether a separate GitHub software tag
  is needed. The Zenodo evidence version does not create a GitHub release.

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

**Next action:** review the R5 manuscript/response drafts and arrange independent
co-author reproduction. The twelve frozen selector-oracle
sample outcomes now have [human author approval](revision/r4-oracle-approval.md).
R2–R4 measurements, including the separate-container extension, are ready in
their documented bounded scopes and are now integrated into both manuscript
views. The new executing Qwen study is the main agent evaluation; old dry-run
tables are omitted, with unchanged historical evidence and the original scores
explicit in the reviewer response. Do not describe this as a controlled model
improvement. Keep the original dry-run campaign unchanged and retain the eight strict
planner-oracle deviations, generic early HTTP errors, ambiguous-drift admission
and observed restart duplicates. R5 and supplementary raw archives are public
under their separate verified version DOIs. Independent reproduction, author
approval and the submission decision remain R5 gates; editor-scope tracking
remains pending.
Do not start H1 adapter code, buy hardware time, or expand
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
