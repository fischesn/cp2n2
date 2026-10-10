# IEEE Access response to reviewers

Manuscript: Access-2026-43996

Title: CP²N²: A Control Plane for Heterogeneous Physical Neural Networks

Date: 10 October 2026

Status: Complete technical response draft. Author approval, independent co-author reproduction, public revision-archive release and the editorial scope decision remain open. Nothing has been submitted. Concern summaries below are not verbatim quotations and require final author comparison with the decision.

## Letter to the editor and reviewers

Dear Editor and Reviewers,

Thank you for the detailed assessment. We revised implementation evidence and claim boundaries. The contribution is a PNN-specific operational contract and reference integration, not a new coordination algorithm or demonstrated physical-safety mechanism.

The revision adds continuous MCP-to-SDK execution, effect-observed direct enforcement, bounded transition exploration, an executing hosted-model campaign, larger selector tests, repeated timings and TCP/container faults. It retains negative findings: planner deviations, restart duplicates and early HTTP errors. No physical substrate is evaluated; durable replicated coordination and production scheduling remain outside the prototype.

The executing campaign replaces the original non-executing study in the main agent results. We preserve its protocol and scores unchanged and address its physical-execution refusal failure below. Different models, prompts and execution availability preclude a controlled comparison of the two scores.

Clean and yellow-highlighted manuscripts share one scientific source; changes are cumulative against the confirmed original submission. Every numbered concern receives a response and an actual action or explicit scope limitation. The author list is unchanged.

Best regards,

Stefan Fischer, Maliheh Hariri and Sebastian Otte

## Evidence key

New experiments use software checkpoint f5802a3d1c2695637a5840ab5ed94d46ce64063c, not historical v5.1.1. Frozen archives have protocols, hash inventories and machine verification. Their identifiers are:

- R2: r2-recovery-confirmatory-20261009-01
- R3-direct: r3-direct-confirmatory-20261010-01
- R3-state: r3-state-confirmatory-20261010-01
- R3-reference: r3-agent-reference-20261010-01
- R3-live: r3-agent-live-qwen-20261010-01
- R4-selection: r4-selection-confirmatory-20261010-01
- R4-contention: r4-contention-confirmatory-20261010-01
- R4-overhead: r4-overhead-confirmatory-20261010-01
- R4-transport: r4-transport-confirmatory-20261010-01
- R4-container: r4-container-confirmatory-20261010-01
- R5-reproduction: r5-reproduction-20261010-01

R1 contract/comparison documents live in docs/revision/ in the software repository. The revision evidence is prepared locally for author-approved publication; it is not yet in the historical release DOI.

## Reviewer 1

### R1.1

**Concern:** Clarify the novelty of CP²N² relative to orchestration frameworks, middleware, and physical-system interfaces.

**Author response:** MCP transport, leases, state machines, idempotency and hash chains are established mechanisms. Our contribution is their reference integration with a PNN-specific operational contract: assay authority, signal units/timing, current-state admission, uncertain completion and identity-bound result validity. The comparison now describes documented responsibilities and remaining domain bindings rather than binary feature scores. It acknowledges PhysMCP/MHS overlap and does not infer that general middleware cannot express the contract. No measured cross-framework superiority is claimed.

**Author action:** Rewrote novelty and comparison; distinguished reused mechanisms from demonstrated integration.

**Location:** Introduction; Physical Neural Resource Contract; Related Work; Table `tab:coverage-comparison`.

**Evidence:** R1 comparison/citation log; R2; R3-direct.

### R1.2

**Concern:** Explain how the absence of real physical-PNN validation limits the scope and generalizability of the conclusions.

**Author response:** Agreed. Evaluation uses mocks, twins, same-host services and the official SDK Simulator. These provenance categories are not cumulative evidence of physical validity. Continuous SDK execution strengthens interface integration, but supplies no biological results, device attestation or physical-safety evidence. We have not obtained physical access and do not substitute simulation for it. Real-substrate applicability remains a separate provider-approved study. Acceptance of this narrowed systems scope is an editorial judgment, not an experimental result.

**Author action:** Narrowed claims throughout; retained the separate physical-study gate.

**Location:** Abstract; Evaluation Design and Claim Boundaries; Threats to Validity and Limitations; Conclusion; Tables `tab:evidence-levels` and `tab:claim-matrix`.

**Evidence:** R2; separate H1 track in the revision roadmap.

### R1.3

**Concern:** Moderate the interpretation of the reported 100% safe result because the Agent-to-PNN campaign performed no substrate execution.

**Author response:** Correct. The original 160/160 field measured withheld execution, not active/physical safety, and is no longer the main agent result. The replacement separates conformity, allowed opportunities, calls, starts, commits and checked deliveries. Six of eight allowed opportunities complete; two stale calls reach admission and are blocked. Direct tests send invalid requests even if a model would refuse them. Four faulty detector controls establish detection of forbidden effects and suppressed valid execution. Zero observed forbidden effects is bounded evidence, not a safety probability.

**Author action:** Removed the old safe-action claim/main tables; added effect-observed enforcement and executing-agent results.

**Location:** Abstract; Agent-to-PNN Protocol and Results; Discussion; Table `tab:executing-agent`.

**Evidence:** R3-direct; R3-live; unchanged historical campaign.

## Reviewer 2

### R2.1

**Concern:** None of the physical-substrate bindings executes its corresponding real substrate. Add physical or hardware-in-the-loop validation, or keep the claims at prototype level.

**Author response:** We take the explicitly narrowed prototype route. No physical PNN or hardware-in-the-loop experiment was performed. Observations are labelled by actual runtime provenance. The abstract/conclusion reject inference of physical safety, biological validity or universal portability. Continuous MCP-to-SDK execution is software integration, not Cortical Cloud/CL1 execution. A physical study requires provider access, approved presets and attributable device observations; it is not included in this revision.

**Author action:** Restricted claims and kept the physical module disabled.

**Location:** Abstract; Implementation and Adapter Integration; Evaluation Design and Claim Boundaries; Threats to Validity and Limitations; Conclusion.

**Evidence:** R2; R3-live; H1 evidence gate.

### R2.2

**Concern:** Substantiate novelty with objective comparisons, concrete missing semantics or failure cases, and a distinction between new contributions and existing distributed-systems mechanisms.

**Author response:** The comparison separates description, admission, authority/lifecycle and result validity, identifying documented responsibilities and remaining PNN bindings. It distinguishes native mechanisms, possible extensions and demonstrated integrations. Kubernetes, ROS 2 and OPC UA already provide important coordination, lifecycle and information-model mechanisms. PhysMCP overlaps in units, permissions, quality, feasibility and recovery. MHS is a research-preview direction, not a fully specified competitor scored as lacking unannounced features. No cross-framework performance/security experiment is claimed.

**Author action:** Replaced binary comparison and clarified reused/new responsibilities.

**Location:** Introduction; Related Work; Table `tab:coverage-comparison`.

**Evidence:** R1 comparison/citation log, including source versions.

### R2.3

**Concern:** The seven selector tasks and four holdout cases are too curated. Use a larger independently specified workload with conflicts, multiple admissible resources, partial telemetry, lifecycle costs, ties, unavailable resources, and ambiguity.

**Author response:** The frozen synthetic suite has 64 cases in 16 families: 28 empty, 22 singleton and 14 multi-resource admissible sets. Five policies and two registration orders yield 640 conformant outputs. Thirty-eight sensitivity checks exercise active age, latency, cost and drift limits, priorities and ties. The analytical oracle is separate from production selection, but the workload remains authored rather than independently sampled. Stefan Fischer approved twelve frozen sets/selections after the run; this is not pre-run human or complete second-author validation. Nonnumeric drift admission remains a weakness.

**Author action:** Added case-level outputs, baseline agreement and active sensitivity; narrowed independence claims.

**Location:** RQ1: Contract, Safe Admission, and Portability; Threats to Validity and Limitations.

**Evidence:** R4-selection; r4-oracle-approval.md.

### R2.4

**Concern:** Contention for one exclusive resource demonstrates exclusion more than scheduling scalability. Add multiple resources, queueing, heterogeneous lease durations, and mixed access modes.

**Author response:** Three resources with 5/10/20-second leases and bursts of 3/6/12/24 requests, repeated in five fresh controllers, yield 225 requests: 60 complete, 165 busy, no overlap. The resource declared nonexclusive is still serialized by the capacity-one implementation. Three idle-expiry probes require explicit reconciliation, not preemption. These are exclusion semantics, not shared-capacity scheduling. Queueing, fairness, utilization optimization and production scalability are not implemented or claimed.

**Author action:** Added multi-resource contention/expiry tests and bounded scheduler/access-mode interpretations.

**Location:** RQ2: Concurrency, Faults, and Recovery; Discussion; Threats to Validity and Limitations.

**Evidence:** R4-contention.

### R2.5

**Concern:** Same-host application-layer faults, one topology/seed, and three repetitions provide limited distributed-systems realism. Include network-level faults and crash/restart cases.

**Author response:** Seven real HTTP/TCP conditions, three times each, use proxies that delay, close and drop replies rather than fabricate status codes. A Linux-container extension separates provider, provider proxy, controller and client proxy into four fresh containers on one bridge network in each of 21 trials: 57 attempts, 18 commits, no overlaps. Restart duplicates occur in all three probes, and 18 early failures return generic HTTP 500 errors. Both failures are retained. These are byte-stream faults on one physical host, not packet-level netem, WAN, clock-skew or replicated-database tests.

**Author action:** Added transport/container experiments, frozen topology/source inventories and explicit negative findings.

**Location:** RQ2: Concurrency, Faults, and Recovery; Threats to Validity and Limitations.

**Evidence:** R4-transport; R4-container.

### R2.6

**Concern:** In-process state does not establish atomic leases with replicated controllers, crashes, persistence races, or partitions. Distinguish current semantics and test persistent competing controllers.

**Author response:** Correct. Lease/lifecycle state is in memory within one controller. Same-controller retries use retained request state, but restart probes cause repeated provider commits after that state is lost. All three restart controls detect duplication. Persistence, controller consensus and device-side fencing require additional architecture and are not implemented. We report failure instead of inferring durability from a mutex or token.

**Author action:** Clarified the in-process boundary; added restart negative controls; removed durable/replicated guarantees.

**Location:** Lifecycle Protocol, Leases, Recovery, and Error Semantics; RQ2: Concurrency, Faults, and Recovery; Threats to Validity and Limitations.

**Evidence:** R4-transport; R4-container.

### R2.7

**Concern:** With execution disabled and decisions withheld by the harness, the 160/160 result does not demonstrate prevention of dangerous effects during execution. Use a state-changing emulated backend.

**Author response:** Actual MCP sessions now log starts, durable mock commits and checked results independently. Forty ordinary conditions, twice each, yield 80 expected outcomes, 24 starts, 22 commits and 14 checked deliveries, without unauthorized/duplicate commits or overlaps. Four extra controls bypass enforcement or deny valid execution; all are detected and excluded from the zero-forbidden-effects denominator. The live campaign allows mock/SDK effects. This evaluates software policy and result integrity, not danger or safety in a physical substrate.

**Author action:** Added direct effect-observed enforcement and separate planner metrics.

**Location:** Agent-to-PNN Protocol and Results; Discussion; Table `tab:executing-agent`.

**Evidence:** R3-direct; R3-live.

### R2.8

**Concern:** The physical-hardware execution class passes only 1/20 because 19 decisions clarify rather than refuse. Give this class greater emphasis instead of relying on aggregate conformity.

**Author response:** We preserve the original scores: one refusal and 19 clarifications give 1/20 under the original refusal oracle; the aggregate remains 141/160. Non-commitment does not make those 19 decisions conformant. We do not rescore or delete them. The main paper now reports executing cases because effects address the revised question, not because the score is higher: conformity is 24/32, with all eight deviations described. The old failure remains in the unchanged archive and this response. Different models, prompts and harnesses prevent a controlled improvement claim.

**Author action:** Replaced old main tables; retained a design-history note and unchanged archive; reported every new deviation.

**Location:** Agent-to-PNN Protocol and Results; Discussion; Table `tab:executing-agent`.

**Evidence:** Historical campaign; R3-live per-case records.

### R2.9

**Concern:** The single-model, eight-class campaign has limited adversarial coverage. Strengthen red-team tests, preferably with multiple model families and independently designed prompts.

**Author response:** Sixteen frozen cases, twice each, include multi-turn pressure, role confusion, untrusted resource-description injection, German/Vietnamese requests, scope/lease conflicts and stale-health execution. The author approved Qwen3.8-27b after a separate capability probe because the original model was unavailable; settings changed before scoring. All eight deviations remain. Coverage is authored and bounded, not independent red teaming or model/language superiority. Adaptive/encoded attacks and compromised hosts/providers are untested. Descriptor injection is untrusted content, not compromise of the descriptor authority.

**Author action:** Added adversarial/multilingual executing cases, provenance and explicit coverage limits.

**Location:** Agent-to-PNN Protocol and Results; Threats to Validity and Limitations.

**Evidence:** R3-live; excluded capability probe; protocol-change record.

### R2.10

**Concern:** Authenticated telemetry need not be physically true. Discuss compromised adapters/providers, attestation, redundant sensing, signed telemetry, replay prevention, and conflicting observations.

**Author response:** Provenance/freshness is distinct from physical truth. Direct tests exercise required missing, stale/replayed/conflicting observations and result checks, establishing specified software rejection, not sensor truth. A trusted host/provider can forge unsigned observations. No hardware attestation, independent redundant sensing or generic contradiction resolver is provided. Optional calibration is not automatically verified; nonnumeric drift can be admitted. These limits are explicit rather than treating field presence or audit hashes as physical assurance.

**Author action:** Expanded the trust boundary/counterexamples and reported unresolved telemetry limits.

**Location:** Threat Model and Trust Boundaries; Physical Neural Resource Contract; Threats to Validity and Limitations.

**Evidence:** R3-direct; R4-selection; R1 binding-contract/invariant document.

### R2.11

**Concern:** Twin validity, confidence, freshness, and drift are largely declared fields rather than calibrated estimates. Show threshold sensitivity and acknowledge missing physical validation.

**Author response:** Agreed. Confidence declarations and synthetic thresholds are contract inputs, not calibrated physical error bounds. Active sensitivity varies age, latency, cost, drift, priorities and ties and verifies rule semantics only. Age/latency/cost limits are inclusive; drift exclusion is strict. Deterministic reconstruction establishes neither predictive fidelity nor a physically safe stimulation envelope or biological generalization. These require independent physical observations and calibration/error studies.

**Author action:** Added rule sensitivity and removed implicit physical-validity interpretations.

**Location:** Physical Neural Resource Contract; RQ1: Contract, Safe Admission, and Portability; Threats to Validity and Limitations.

**Evidence:** R4-selection; R2 native reconstruction; H1 physical gate.

### R2.12

**Concern:** Rule conformance is not validation that the policies are sufficient for physical safety. Distinguish enforcement correctness and specify lifecycle, lease, idempotency, and fail-closed invariants.

**Author response:** Fourteen contract/invariant cases specify authority, ownership, final-state knowledge, identity and delivery. An independent abstract model matches 464 transitions across 78 states for one exclusive E0 resource, two principals, two single-shot request slots and traces of at most six macro-events. Witness replay uses 1,975 direct control-surface calls, not MCP transport. Execute/validate/finalize is one synchronous macro-event: this is bounded conformance, not proof over arbitrary concurrent interleavings. Restart duplication is measured separately. No physical-safety theorem is asserted.

**Author action:** Added explicit contracts and bounded transition exploration with abstraction limits.

**Location:** Physical Neural Resource Contract; Lifecycle Protocol, Leases, Recovery, and Error Semantics; Agent-to-PNN Protocol and Results; Threats to Validity and Limitations.

**Evidence:** R3-state; R3-direct; R1 binding-contract/invariant document.

### R2.13

**Concern:** Overhead estimates based on 25 local and 15 HTTP calls need stronger statistics, warm-up/environment details, supported tail quantiles, load characterization, and ideally a second environment.

**Author response:** Four paired comparisons use ten trials, 20 warm-ups and 200 measurements per path: 1,600 warm-ups and 16,000 measurements. Statistics are median of trial medians, median of within-trial p95 values and paired increments with trial-bootstrap intervals (2,000 resamples, fixed seed). Controlled edge-twin execution adds 1.824–3.402 ms at 1–12 resources; MCP memory discovery is a different operation. Host/library versions are retained. Affinity, power mode and background load were not controlled. Containers are another software boundary, not a second physical performance environment. No p99 or cross-host generalization is claimed.

**Author action:** Replaced short headline timings with repeated, uncertainty-qualified results and deployment limits.

**Location:** RQ2: Control-Plane Overhead; Discussion; Threats to Validity and Limitations; Table `tab:revision-overhead`.

**Evidence:** R4-overhead method/environment records.

### R2.14

**Concern:** Broaden related work with relevant software-contract, edge-security, observability, insider-threat, and IoT studies; the reviewer supplies six candidate references.

**Author response:** We assessed all six suggestions individually. The requirements-contract paper may be conceptually relevant, but primary text was unavailable; detailed claims cannot be assessed. The cloud-log anomaly paper concerns learned log classification; the insider-threat paper behaviour classification/optimization; the edge-security/GAN paper intrusion detection/augmentation; the metaverse-IoT paper intrusion classification; and the CNN/XGBoost IoT paper network classification/tuning. These are valuable adjacent problems, but the five available abstracts do not establish the assay authority, execution ownership or result-validity obligations evaluated here. Adding them would imply an intrusion-detection evaluation we do not conduct.

**Author action:** Expanded directly related interfaces/middleware instead; recorded each title, DOI, access limit and omission reason.

**Location:** Related Work; Table `tab:coverage-comparison`.

**Evidence:** R1 comparison/citation log, six-reference assessment table.

### R2.15

**Concern:** Improve LLM reproducibility by archiving prompts, system instructions, schemas, oracle, raw responses, request IDs, model/version metadata, and machine-verifiable pilot/confirmatory separation.

**Author response:** The new live archive retains exact instructions/prompts, schemas, oracle, completions, parsed decisions, provider IDs, requested/returned model IDs, settings and audit/effect/native records. One capability probe is separate; no scored call was retried/replaced. Historical missing responses are not reconstructed. Provider weights, routing and reasoning-token counts are unavailable. A clean checkout passed 286 tests and eighteen verification/reproduction jobs without new LLM/physical calls. It reuses the same host/environment, not independent co-author reproduction. Container/hosted-model archives are verified, not rerun; overhead is recomputed, not remeasured. Public revision-evidence release requires author approval.

**Author action:** Added provenance, archive verification and clean-checkout reproduction; separated historical/current/public evidence.

**Location:** Agent-to-PNN Protocol and Results; Threats to Validity and Limitations; Data Availability.

**Evidence:** R3-live; R5-reproduction; revision baseline record.

## Reviewer 3

### R3.1

**Concern:** The harness withheld simulator execution and physical execution was unavailable, so the 160/160 results do not show protection through an active lifecycle.

**Author response:** Correct. The replacement allows mock/SDK execution: six permitted opportunities complete, two stale calls reach admission and are blocked, and eight strict planner deviations remain. Direct tests bypass planner refusal and independently check effects/results. A deterministic 32-case reference completes all eight allowed opportunities; it is oracle-fed harness validation, not an LLM result. Detector controls expose bypass and suppressed valid execution. These support bounded software enforcement, not arbitrary agent/physical safety.

**Author action:** Replaced old main agent tables with executing/direct/control results and distinct denominators.

**Location:** Agent-to-PNN Protocol and Results; Discussion; Table `tab:executing-agent`.

**Evidence:** R3-direct; R3-reference; R3-live.

### R3.2

**Concern:** The audited MCP trace did not launch the provider-facing SDK run. Shared code/hashes do not bind authorization, lease, execution identity, provider completion, and result delivery across one path.

**Author response:** The new bridge starts a fresh SDK Simulator process from the admitted MCP task. Its manifest binds principal, request, task, resource, lease, attempt, SDK identity, configuration, decoder, native recording, result and final state. Nine conditions twice yield 18 trials, 110 MCP calls, 220 audit events and 14 SDK starts. Four successful deliveries are independently reconstructed. Abort/timeouts preserve partial recordings; crashes preserve unfinalized evidence. Unknown termination quarantines the resource until reconciliation. Windows process containment checks observed termination before reuse; unsupported platforms fail closed. Cloud lifecycle and physical attestation remain unimplemented.

**Author action:** Implemented/measured the continuous path, recovery and native reconstruction; retained the historical separate-trace boundary.

**Location:** BioPattern Gate Application Workflow; Cortical Labs E3 Case Study; Discussion; Table `tab:biopattern-e3-trace`.

**Evidence:** R2 per-trial manifests, recordings and reconstruction reports.

### R3.3

**Concern:** Portability lacks concrete cross-binding examples for units, admissible ranges, timing, calibration validity, and postconditions.

**Author response:** The PNRC distinguishes field types from binding obligations. The binding table specifies concentration versus spike/feature encodings, operating/timing assumptions, observation/calibration requirements and postconditions. Common production validation checks task/backend identity and finite output; fixture probability predicates are not universal validators. SDK delivery is independently reconstructed and bound to its server-owned preset. Direct cases cover required calibration, missing/stale/conflicting observations, identity errors and invalid results. Optional calibration and unsigned telemetry still do not establish physical validity.

**Author action:** Expanded binding contracts and tested common result validation/continuous SDK postconditions.

**Location:** Physical Neural Resource Contract; Implementation and Adapter Integration; Cortical Labs E3 Case Study; Table `tab:binding-contracts`.

**Evidence:** R2; R3-direct; R1 binding-contract/invariant document.

### R3.4

**Concern:** The 7/7 versus 6/7 comparison needs decisive case-level explanations. Weighted-heuristic perturbations do not establish robustness of the lexicographic policy.

**Author response:** The new suite has 64 cases, five policies, two orders and 38 active sensitivity checks. All 640 outputs conform. Across 36 nonempty principal choices, latency-first agrees in 29, locality/cost in 33, static in 29 and seeded random in 27; lexicographic agreement is 36 by construction. These are policy-choice agreements, not physical utility/accuracy improvements. Sensitivity changes active limits, priorities and ties, not unused weights. Authored synthetic workloads and partial post-run human review remain limitations.

**Author action:** Added case-level agreement and active sensitivity without superiority claims.

**Location:** RQ1: Contract, Safe Admission, and Portability; Threats to Validity and Limitations.

**Evidence:** R4-selection; r4-oracle-approval.md.

## Author review and submission gates

- Check concerns, responses and final manuscript locations against the decision/PDFs.
- Obtain independent co-author reproduction; the automated same-host run does not satisfy this gate.
- Decide on IEEE Access resubmission; the editor has not answered the physical-evidence scope question.
- Approve/publish the revision archive and update Data Availability to its actual public location.
- Approve the official checklist and upload categories. Nothing is uploaded without explicit authorization.
