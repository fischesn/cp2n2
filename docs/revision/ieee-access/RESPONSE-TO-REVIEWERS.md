# IEEE Access response to reviewers

Manuscript: Access-2026-43996

Title: CP²N²: A Control Plane for Heterogeneous Physical Neural Networks

Date: 14 October 2026

Status: Technical response draft incorporating R2–R5 and the supplementary AP1–AP3/Gemini results. Both the earlier R5 evidence and the separately authorized supplementary raw archives are public under distinct version DOIs. Final co-author approval, independent co-author reproduction and the editorial scope decision remain open. Nothing has been submitted. Concern summaries below are not verbatim quotations and require final author comparison with the decision.

## Letter to the editor and reviewers

Dear Editor and Reviewers,

Thank you for the detailed assessment. Your comments helped us distinguish the operational properties that can be tested in this prototype from the physical and distributed guarantees that require a different study. We revised the implementation, experimental evidence and claim boundaries. The contribution is a PNN-specific operational contract and reference integration, not a new coordination algorithm or demonstrated physical-safety mechanism.

The revision adds continuous MCP-to-SDK execution, effect-observed direct enforcement, bounded transition exploration, an executing hosted-model campaign, larger selector tests, repeated timings and TCP/container faults. Supplementary work adds task-required numeric/result validation, original-age preservation for cached observations, structured provider errors with explicit recovery, measured CPU/load context, and twelve externally Gemini-authored selector cases tested without changing the functional source or expectations. It retains historical negative findings: planner deviations, restart duplicates and early HTTP errors. No physical substrate is evaluated; durable replicated coordination and production scheduling remain outside the prototype.

The executing campaign replaces the original non-executing study in the main agent results. The manuscript now also states the original 141/160 aggregate and the physical-execution class's one refusal and nineteen clarifications (1/20 conformity). We preserve that protocol and those scores unchanged. Different models, prompts and execution availability preclude a controlled comparison of the two campaigns.

Clean and yellow-highlighted manuscripts share one scientific source; changes are cumulative against the confirmed original submission. Repeated background, architecture and discussion passages were condensed for readability without changing results, methods, figures, tables or scientific qualifications. Every numbered concern receives a response and an actual action or explicit scope limitation. The author list is unchanged.

Best regards,

Stefan Fischer, Maliheh Hariri and Sebastian Otte

## Evidence key

The R2–R5 experiments use software checkpoint f5802a3d1c2695637a5840ab5ed94d46ce64063c, not historical v5.1.1. Frozen archives have protocols, hash inventories and machine verification. Their identifiers are:

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

R1 contract/comparison documents live in docs/revision/ in the software repository. The public revision evidence is archived as version R5-2026-10-10 at https://doi.org/10.5281/zenodo.23281161. It includes the exact evaluated source snapshot and package/campaign verification receipts. The historical v5.1.1 DOI, 10.5281/zenodo.21887895, remains unchanged and does not cover the new experiments.

The R5 public copy omits two budget-only JSON logs and structured provider-account budget objects, with original/public hashes and transformations disclosed. Already-public textual budget summaries in historical documentation/source snapshots remain. All other 12,427 evidence payloads are byte-identical to the private frozen candidate, including prompts, oracles, measurements, failures and audit chains. All ten campaign verifiers passed on the public copy; complete unauthenticated downloads of the five new deposit files matched local SHA-256 values and sizes. This publication adds no new LLM, container, timing or physical observations and does not establish independent co-author reproduction.

The supplementary campaigns were prospectively frozen on 14 October 2026 and use modified, uncommitted source bytes. Their base Git commit, bba19db333011aa5c59bc6fa56f29eede536a723, is not the identity of those bytes. The coordinated AP1–AP3 source freeze contains 290 normalized per-file hashes; the Gemini snapshot contains the same unchanged 290 files plus five campaign/packaging files. The supplementary identifiers are:

- AP1: ap1-required-evidence-confirmatory-20261014-01
- AP2: ap2-provider-errors-confirmatory-20261014-01
- AP3: ap3-overhead-confirmatory-20261014-01
- Gemini: gemini-selector-confirmatory-20261014-01

Their byte-preserved raw archives are published as version SUPPLEMENTARY-2026-10-14 at https://doi.org/10.5281/zenodo.23377537. The supplementary ZIP contains specifications, protocols, source snapshots, environment, first-run observations and offline verification reports; retained development reports are separate from scored campaigns. All four archived campaign verifiers passed on the public copy. Complete unauthenticated downloads of its five new deposit files matched local SHA-256 values and sizes. Tracked results and SHA-256 evidence indexes are in docs/revision/ap1-ap3-results.md, ap3-overhead-results.md, ap1-ap3-evidence-index.json, gemini-selector-results.md and gemini-selector-evidence-index.json. The final regression checkpoint passes 486 tests. The earlier R5 DOI, 10.5281/zenodo.23281161, does not cover these new archives. Publication adds no new scored observations and does not establish independent co-author reproduction. No old source, oracle, observation or negative result has been overwritten; the new code's intentional rejection of a historical nonnumeric required-drift fixture is documented rather than presented as reproduction of the old output.

## Reviewer 1

### R1.1

**Concern:** Clarify the novelty of CP²N² relative to orchestration frameworks, middleware, and physical-system interfaces.

**Author response:** We agree that combining familiar mechanisms alone is not a novelty argument. MCP transport, leases, state machines, idempotency and hash chains are established mechanisms. Our contribution is their reference integration with a PNN-specific operational contract: assay authority, signal units/timing, current-state admission, uncertain completion and identity-bound result validity. The comparison now describes documented responsibilities and remaining domain bindings rather than binary feature scores. It acknowledges PhysMCP/MHS overlap and does not infer that general middleware cannot express the contract. The supplementary implementation makes required-evidence and uncertain-provider-result rules executable, but does not establish measured cross-framework superiority.

**Author action:** Rewrote novelty and comparison; distinguished reused mechanisms from demonstrated integration.

**Location:** Introduction; Physical Neural Resource Contract; Related Work; Table `tab:coverage-comparison`.

**Evidence:** R1 comparison/citation log; R2; R3-direct; AP1; AP2.

### R1.2

**Concern:** Explain how the absence of real physical-PNN validation limits the scope and generalizability of the conclusions.

**Author response:** Agreed. Evaluation uses mocks, twins, same-host services and the official SDK Simulator. These provenance categories are not cumulative evidence of physical validity. Continuous SDK execution strengthens interface integration, but supplies no biological results, device attestation or physical-safety evidence. The supplementary validation, recovery and selector campaigns likewise remain software evidence. We have not obtained physical access and do not substitute simulation for it. Real-substrate applicability remains a separate provider-approved study. This limitation prevents conclusions about calibrated substrate behavior, biological utility and physical safety; acceptance of the narrowed systems scope remains an editorial judgment.

**Author action:** Narrowed claims throughout; retained the separate physical-study gate.

**Location:** Abstract; Evaluation Design and Claim Boundaries; Threats to Validity and Limitations; Conclusion; Tables `tab:evidence-levels` and `tab:claim-matrix`.

**Evidence:** R2; AP1–AP3; Gemini; separate H1 track in the revision roadmap.

### R1.3

**Concern:** Moderate the interpretation of the reported 100% safe result because the Agent-to-PNN campaign performed no substrate execution.

**Author response:** Correct. The original 160/160 field measured withheld execution, not active/physical safety, and is no longer the main agent result. The replacement separates conformity, allowed opportunities, calls, starts, commits and checked deliveries. Six of eight allowed opportunities complete; two stale calls reach admission and are blocked. Direct tests send invalid requests even if a model would refuse them. AP1 additionally uses a fixture whose preparation does not reject invalid telemetry: 28 invalid preconditions produce no starts/commits, six valid controls execute and deliver, and twelve invalid post-execution results retain their legitimate commits but withhold successful delivery. Four separate faulty detector controls are detected. This distinguishes prevention from result withholding and avoids crediting the provider's own checks to the gateway. Zero observed forbidden effects remains bounded software evidence, not a physical-safety probability.

**Author action:** Removed the old safe-action claim/main tables; added executing-agent and effect-observed enforcement results, with separate precondition, commit and delivery denominators.

**Location:** Abstract; Agent-to-PNN Protocol and Results; Discussion; Tables `tab:executing-agent` and `tab:supplementary-enforcement`.

**Evidence:** R3-direct; R3-live; AP1; unchanged historical campaign.

## Reviewer 2

### R2.1

**Concern:** None of the physical-substrate bindings executes its corresponding real substrate. Add physical or hardware-in-the-loop validation, or keep the claims at prototype level.

**Author response:** We agree that a real backend would materially strengthen substrate applicability. We take the explicitly narrowed prototype route offered in the comment: no physical PNN or hardware-in-the-loop experiment was performed. Observations are labelled by actual runtime provenance. The abstract/conclusion reject inference of physical safety, biological validity or universal portability. Continuous MCP-to-SDK execution is software integration, not Cortical Cloud/CL1 execution. Adding more mocks, externally authored cases or loopback failures cannot close that physical-validation gap. A physical study requires provider access, approved presets and attributable device observations; it is not included in this revision.

**Author action:** Restricted claims and kept the physical module disabled.

**Location:** Abstract; Implementation and Adapter Integration; Evaluation Design and Claim Boundaries; Threats to Validity and Limitations; Conclusion.

**Evidence:** R2; R3-live; H1 evidence gate.

### R2.2

**Concern:** Substantiate novelty with objective comparisons, concrete missing semantics or failure cases, and a distinction between new contributions and existing distributed-systems mechanisms.

**Author response:** The concern identifies a weakness in the original all-yes/all-no table. We replaced it with declared criteria for description, admission, authority/lifecycle and result validity, distinguishing native mechanisms, possible extensions and demonstrated integrations. Kubernetes, ROS 2 and OPC UA already provide important coordination, lifecycle and information-model mechanisms. PhysMCP overlaps in units, permissions, quality, feasibility and recovery. MHS is a research-preview direction, not a fully specified competitor scored as lacking unannounced features. Concrete CP²N² failure cases now show missing required evidence, uncertain invocation completion and restart duplication, but they are not tests of those other frameworks. The comparison therefore establishes positioning and domain-binding obligations, not measured cross-framework superiority or a proof that another framework cannot express them.

**Author action:** Replaced binary comparison and clarified reused/new responsibilities.

**Location:** Introduction; Related Work; Table `tab:coverage-comparison`.

**Evidence:** R1 comparison/citation log, including source versions.

### R2.3

**Concern:** The seven selector tasks and four holdout cases are too curated. Use a larger independently specified workload with conflicts, multiple admissible resources, partial telemetry, lifecycle costs, ties, unavailable resources, and ambiguity.

**Author response:** We agree that the original seven curated tasks did not establish general matching accuracy. The first revision adds 64 synthetic cases in 16 families: 28 empty, 22 singleton and 14 multi-resource admissible sets, with 640 policy/order outputs and 38 active sensitivity comparisons. Because that suite remained implementation-team-authored, we then obtained twelve cases from an unchanged first response in an isolated Gemini chat without the paper, repository or previous results. The author-reported generator was Gemini Flash 3.8 with high effort; Stefan Fischer approved the cases and documented interpretations before scoring. Their 47 candidates cover conflicting constraints, partial telemetry, fatal lifecycle/unavailability, multiple eligible resources, reset/stochasticity preferences, ties and policy trade-offs. Three policies and original/reversed order yield 72/72 matches for eligible sets, full rankings, selected resources and normalized rejection annotations; all 36 order pairs are invariant. All 290 functional/source hashes were frozen before receipt and remained unchanged. One overlapping missing-drift rule interpretation is disclosed and was approved before execution; it changes neither exclusion nor ranking. This strengthens external case authorship, not independent human reproduction, representative workload sampling or guaranteed ground truth. Ambiguous natural-language intent is tested separately in the agent campaign; these selector cases use an explicit restricted contract. AP1 fixes malformed required numeric evidence separately, without changing or rescoring the historical R4 oracle.

**Author action:** Added the external case-authorship protocol, untouched response/prompt, pre-run approval, input-only bridge, frozen source/input hashes and first-run case-level outcomes; retained authored-suite sensitivity and narrowed independence/generalization claims.

**Location:** RQ1: Contract, Safe Admission, and Portability, including Externally Authored Selector Cases; Threats to Validity and Limitations; Data Availability.

**Evidence:** R4-selection; r4-oracle-approval.md; Gemini protocol, immutable intake, author approval, first-run outputs and evidence index; AP1. The supplementary raw archives are public under DOI 10.5281/zenodo.23377537, distinct from the earlier R5 DOI.

### R2.4

**Concern:** Contention for one exclusive resource demonstrates exclusion more than scheduling scalability. Add multiple resources, queueing, heterogeneous lease durations, and mixed access modes.

**Author response:** Agreed: immediate busy rejection primarily tests exclusion, not scheduling quality. Three resources with 5/10/20-second leases and bursts of 3/6/12/24 requests, repeated in five fresh controllers, yield 225 requests: 60 complete, 165 busy, no overlap. The resource declared nonexclusive is still serialized by the capacity-one implementation. Three idle-expiry probes require explicit reconciliation, not preemption. Thus the revision supplies heterogeneous leases and simultaneous resources, but only partially fulfills the requested scheduling study. Queueing, fairness and shared-capacity scheduling need a scheduler and capacity model not present in this reference controller; their evaluation cannot be inferred from rejection counts or AP3's directed microbenchmarks. We have removed scalability/utilization interpretations rather than claim those unimplemented guarantees.

**Author action:** Added multi-resource contention/expiry tests and bounded scheduler/access-mode interpretations.

**Location:** RQ2: Concurrency, Faults, and Recovery; Discussion; Threats to Validity and Limitations.

**Evidence:** R4-contention.

### R2.5

**Concern:** Same-host application-layer faults, one topology/seed, and three repetitions provide limited distributed-systems realism. Include network-level faults and crash/restart cases.

**Author response:** We agree that application-layer synthetic responses alone were insufficient. Seven actual HTTP/TCP conditions, three times each, use proxies that delay, close and drop replies rather than fabricate status codes. A Linux-container extension separates provider, provider proxy, controller and client proxy into four fresh containers on one bridge network in each of 21 trials: 57 attempts, 18 commits, no overlaps. All three restart probes duplicate commits and 18 early attempts return generic HTTP 500; those historical observations remain unchanged. We then implemented structured per-resource provider failures, quarantine, bounded reads and explicit reconciliation. AP2 runs six conditions three times using separate production controller/provider/TCP-proxy processes: all 18 effect/recovery patterns verify, with 96 HTTP 200 responses carrying structured semantic results and no generic HTTP 500. A healthy alternative remains usable; after a lost invocation reply the primary commits once, with no automatic retry or secondary invocation, and same-key replay remains uncertain. A distinct new task is permitted only after explicit recovery. This addresses the identified error-reporting/recovery weakness, not restart durability. It remains one-host byte-stream evidence; multi-host partitions, packet-level netem, clock skew, database inconsistency and replicated control-plane failures are not tested.

**Author action:** Added transport/container experiments and a separately frozen provider-error/recovery implementation study; distinguished historical failures, corrected behavior and untested distributed guarantees.

**Location:** RQ2: Concurrency, Faults, and Recovery; Threats to Validity and Limitations.

**Evidence:** R4-transport; R4-container; AP2 protocol v2, process/HTTP/TCP records, provider effect ledgers and verification. The retained v1 development report records a pre-scoring timeout-classification correction; effect/recovery expectations did not change.

### R2.6

**Concern:** In-process state does not establish atomic leases with replicated controllers, crashes, persistence races, or partitions. Distinguish current semantics and test persistent competing controllers.

**Author response:** Correct. Lease/lifecycle state is in memory within one controller. Same-controller retries use retained request state, but all three restart probes repeat provider commits after that state is lost. AP2 improves single-controller quarantine and explicit recovery; it does not restore lost ownership, provide device-side fencing or fix restart duplicates. Persistent competing controllers would require a transactional state/ownership design and a different failure model, not a stronger interpretation of the current mutex or token. We have not implemented that architecture or claimed distributed atomicity. The revised paper reports the negative controls and confines atomic acquisition to the single-controller critical section.

**Author action:** Clarified the in-process boundary; added restart negative controls; removed durable/replicated guarantees.

**Location:** Lifecycle Protocol, Leases, Recovery, and Error Semantics; RQ2: Concurrency, Faults, and Recovery; Threats to Validity and Limitations.

**Evidence:** R4-transport; R4-container; AP2's recovery boundary within one controller lifetime.

### R2.7

**Concern:** With execution disabled and decisions withheld by the harness, the 160/160 result does not demonstrate prevention of dangerous effects during execution. Use a state-changing emulated backend.

**Author response:** Agreed. Actual MCP sessions now log starts, persisted mock commits and checked results independently. R3-direct's forty conditions, twice each, yield 80 expected outcomes, 24 starts, 22 commits and 14 checked deliveries; four extra bypass/deny-all detector controls are detected and excluded from the ordinary forbidden-effect denominator. The live campaign allows mock/SDK effects. To isolate the gateway from provider-side telemetry checks, AP1 adds a fixture whose preparation checks only fixed vector input: 28 invalid required preconditions yield zero starts/commits, six valid controls yield six successful executions/deliveries, and twelve invalid post-execution results follow twelve legitimate commits but yield no successful delivery. Four extra detector controls all fail the intended invariant. Across AP1's 50 trials, 120 MCP calls bind to 240 audit events. This directly tests effect prevention and result withholding, but does not validate physical danger thresholds or safety-policy completeness.

**Author action:** Added direct effect-observed enforcement, a provider-preparation-independent required-evidence fixture, post-commit result-corruption cases and separate planner/effect/delivery metrics.

**Location:** Agent-to-PNN Protocol and Results; Discussion; Tables `tab:executing-agent` and `tab:supplementary-enforcement`.

**Evidence:** R3-direct; R3-live; AP1 effect ledgers, MCP/audit bindings and detector verification.

### R2.8

**Concern:** The physical-hardware execution class passes only 1/20 because 19 decisions clarify rather than refuse. Give this class greater emphasis instead of relying on aggregate conformity.

**Author response:** We agree that the aggregate obscured an important semantic failure. The manuscript now states explicitly that the original aggregate was 141/160 and the physical-execution class produced one refusal and nineteen clarifications, giving 1/20 under the original refusal oracle. Non-commitment does not make those nineteen decisions conformant; neither the oracle nor the scores are changed. The discussion uses this class to motivate an execution-authority boundary independent of planner wording. Executing cases become the main agent results because observed effects address the revised question, not because the score is higher: conformity is 24/32, with all eight deviations described. Different models, prompts and harnesses prevent a controlled improvement claim.

**Author action:** Added the exact historical aggregate, refusal/clarification counts and class-specific interpretation to the manuscript; retained the unchanged archive and reported every new deviation separately.

**Location:** Agent-to-PNN Protocol and Results; Discussion; Table `tab:executing-agent`.

**Evidence:** Historical campaign; R3-live per-case records.

### R2.9

**Concern:** The single-model, eight-class campaign has limited adversarial coverage. Strengthen red-team tests, preferably with multiple model families and independently designed prompts.

**Author response:** We agree that repeated single-turn calls were not a substantial red-team study. Sixteen frozen cases, twice each, now include fixed multi-turn pressure/context, role confusion, injection in untrusted resource-description content, scope/lease conflicts and stale-health execution. German/Vietnamese cases are benign multilingual task requests, not multilingual attacks. The fixed multi-turn cases are prewritten contexts, not an adversary adapting to live answers. The author approved Qwen3.8-27b after a separate capability probe because the original model was unavailable; settings changed before scoring, and all eight deviations remain. Gemini separately supplies external selector cases, not an independent red-team campaign or another executing model family. Encoded/adaptive attacks, compromised authoritative descriptors/hosts/providers and a multi-model adversarial comparison remain untested. We therefore strengthen bounded coverage and describe the remaining gap rather than label the campaign comprehensive red teaming.

**Author action:** Added fixed pressure/injection and benign multilingual executing cases with provenance; corrected the distinction between fixed context, adaptive dialogue and compromised descriptor authority.

**Location:** Agent-to-PNN Protocol and Results; Threats to Validity and Limitations.

**Evidence:** R3-live; excluded capability probe; protocol-change record.

### R2.10

**Concern:** Authenticated telemetry need not be physically true. Discuss compromised adapters/providers, attestation, redundant sensing, signed telemetry, replay prevention, and conflicting observations.

**Author response:** We agree that authenticated communication cannot make a provider's report physically true. AP1 now rejects task-required missing/malformed numeric evidence and invalid declared calibration, preserves supplied original observation/receipt/expiry times when cached observations are republished, and rejects future/expired/over-age required observations. Its conflict case compares two representations of the same health property; it is not a generic contradiction resolver or sensor-fusion study. The expired-cache case violates expiry and maximum age together and does not isolate those branches. These changes close the earlier present-but-nonnumeric required-drift weakness in the new implementation, without editing historical results. They do not provide signed anti-replay sequences, hardware attestation, redundant independent sensing, physical calibration or confidence degradation under arbitrary contradictions. A trusted compromised provider can still submit a fresh, consistent but physically false report. Bindings must supply original metadata for age preservation to work, and optional calibration is not automatically validated. The manuscript separates these implemented checks from future attestation/provenance/sensing mechanisms rather than treating audit hashes as physical assurance.

**Author action:** Implemented task-required semantic validation and original-age preservation; added same-property conflict and cached-expiry tests; narrowed replay/physical-truth wording and retained compromised-provider counterexamples.

**Location:** Threat Model and Trust Boundaries; Physical Neural Resource Contract; Agent-to-PNN Protocol and Results; Threats to Validity and Limitations; Table `tab:supplementary-enforcement`.

**Evidence:** AP1; historical R3-direct/R4-selection; R1 binding-contract/invariant document.

### R2.11

**Concern:** Twin validity, confidence, freshness, and drift are largely declared fields rather than calibrated estimates. Show threshold sensitivity and acknowledge missing physical validation.

**Author response:** Agreed. Confidence declarations and synthetic thresholds are contract inputs, not calibrated physical error bounds. Active sensitivity varies age, latency, cost, drift, priorities and ties and verifies rule semantics only; age/latency/cost limits are inclusive and drift exclusion is strict. AP1 additionally makes task-required result confidence fail closed: missing values, booleans, numeric strings, nonfinite/out-of-range values or insufficient confidence withhold successful delivery, and valid controls deliver. That shows interpretation/enforcement of a declared threshold, not that the threshold predicts real substrate error. Deterministic SDK reconstruction likewise establishes neither predictive fidelity nor a physically safe stimulation envelope or biological generalization. Mapping twin mismatch/confidence to safe operating limits still requires independent physical observations and calibration/error studies, which are not available here.

**Author action:** Added rule sensitivity and strict task-required result-confidence validation; distinguished declared calibration validity from empirical physical calibration.

**Location:** Physical Neural Resource Contract; RQ1: Contract, Safe Admission, and Portability; Agent-to-PNN Protocol and Results; Threats to Validity and Limitations; Table `tab:supplementary-enforcement`.

**Evidence:** R4-selection; AP1; R2 native reconstruction; H1 physical gate.

### R2.12

**Concern:** Rule conformance is not validation that the policies are sufficient for physical safety. Distinguish enforcement correctness and specify lifecycle, lease, idempotency, and fail-closed invariants.

**Author response:** We agree that conformance to the selected rules cannot establish that those rules are sufficient for a physical substrate. Fourteen contract/invariant cases specify authority, ownership, final-state knowledge, identity and delivery. A separately implemented abstract model matches 464 transitions across 78 states for one exclusive E0 resource, two principals, two single-shot request slots and traces of at most six macro-events. Witness replay uses 1,975 direct control-surface calls, not MCP transport. Execute/validate/finalize is one synchronous macro-event: this is bounded transition exploration, not proof over arbitrary concurrent interleavings. AP1 supplies further effect/delivery witnesses for required evidence; AP2 tests uncertain completion and explicit recovery within one controller lifetime. Neither expands the model into persistent or replicated execution, and restart duplication is retained separately. We state the invariants, abstraction and measured counterexamples without asserting a physical-safety theorem.

**Author action:** Added explicit contracts and bounded transition exploration with abstraction limits.

**Location:** Physical Neural Resource Contract; Lifecycle Protocol, Leases, Recovery, and Error Semantics; Agent-to-PNN Protocol and Results; Threats to Validity and Limitations.

**Evidence:** R3-state; R3-direct; AP1; AP2; R1 binding-contract/invariant document.

### R2.13

**Concern:** Overhead estimates based on 25 local and 15 HTTP calls need stronger statistics, warm-up/environment details, supported tail quantiles, load characterization, and ideally a second environment.

**Author response:** We agree that the original short runs did not support tail-latency conclusions. R4 adds ten fresh-registry trials, 20 warm-ups and 200 measurements per paired path, totaling 16,000 measured operations and 1,600 warm-ups. After the AP1/AP2 changes, AP3 measures the updated source separately under no intentionally added load and one owned duty-cycled CPU worker: 80 fresh-registry trials, 32,000 measured operations and 3,200 warm-ups, all successful. Each condition/configuration again has ten trials; statistics report the median of trial medians and median of trial p95 values with 2,000 bootstrap resamples of trial summaries, not pooled dependent calls. Updated controlled-execution medians are 3.43–4.12 ms without intentionally added load and 4.00–4.56 ms with the worker; MCP memory-discovery medians are 14.45 and 14.56 ms. Measured worker utilization is approximately 29–37% of one core, not its declared 60% duty setting or whole-host saturation. Raw process/system CPU endpoints, library/host versions and cleanup are retained; several short direct blocks have CPU-clock-resolution artifacts. Intervals overlap, and execution targets bench-0 explicitly: varying registered resource count is not general selector scaling. The p95 interval describes the median of trial p95 values, not a population tail guarantee. No p99, second physical environment or cross-host generalization is claimed; affinity/power/background OS work remain uncontrolled. New and historical timings are kept distinct rather than pooled or attributed to the wrong source.

**Author action:** Replaced short headline timings with repeated trials and uncertainty-qualified statistics; added updated-source load/CPU measurements, both conditions' intervals, archived raw endpoints and explicit tail/scaling/environment limits.

**Location:** RQ2: Control-Plane Overhead; Discussion; Threats to Validity and Limitations; Tables `tab:revision-overhead` and `tab:supplementary-overhead`.

**Evidence:** R4-overhead method/environment records and immutable intervals; AP3 protocol, raw timing/CPU endpoints, full condition tables and offline verification.

### R2.14

**Concern:** Broaden related work with relevant software-contract, edge-security, observability, insider-threat, and IoT studies; the reviewer supplies six candidate references.

**Author response:** Thank you for identifying adjacent contract, observability and security literature. We assessed all six suggestions individually rather than reject them as a group. The requirements-contract paper may offer a useful conceptual connection, but primary text was unavailable in the recorded source check; we cannot fairly make detailed claims about it. The available publisher abstracts describe cloud-log anomaly classification, insider-behavior classification/optimization, edge-security intrusion detection/augmentation, metaverse-IoT intrusion classification, and CNN/XGBoost network classification/tuning. Those studies address valuable complementary detection questions. Our focused related-work comparison concerns executable assay authority, operation ownership, current-state admission and identity-bound result validity, and the accessible material did not establish a direct comparison on those obligations. We therefore expanded the directly related physical-interface/general-middleware discussion and retained individual access/scope assessments instead of adding tangential citations without a substantive connection. This is a relevance decision, not an assertion that citing detection work would require us to evaluate an IDS or that the suggested work lacks merit. We would reconsider the requirements-contract paper if its primary text becomes available before final submission.

**Author action:** Expanded directly related interfaces/middleware; recorded each suggested title, DOI, access limit and individual relevance decision, with the unavailable contract paper left open for reassessment if primary text is supplied.

**Location:** Related Work; Table `tab:coverage-comparison`.

**Evidence:** R1 comparison/citation log, six-reference assessment table.

### R2.15

**Concern:** Improve LLM reproducibility by archiving prompts, system instructions, schemas, oracle, raw responses, request IDs, model/version metadata, and machine-verifiable pilot/confirmatory separation.

**Author response:** The executing live archive retains exact instructions/prompts, schemas, oracle, completions, parsed decisions, provider IDs, requested/returned model IDs, settings and audit/effect/native records. One capability probe is separate; no scored call was retried/replaced. Historical missing responses are not reconstructed, so the old 141/160 and 1/20 scores remain auditable from their retained decisions but do not acquire nonexistent raw completions. Provider weights, routing and reasoning-token counts are unavailable. R5's clean checkout passed 286 tests and eighteen verification/reproduction jobs without new LLM/physical calls; it reuses the same host/environment and does not establish independent co-author reproduction. Container/hosted-model archives were verified, not rerun, and overhead recomputed, not remeasured. DOI 10.5281/zenodo.23281161 covers that R5 evidence, with disclosed budget-object/log redaction leaving scientific trial payloads unchanged. The supplementary AP/Gemini freezes retain their own new source snapshots, protocols, first-run observations and offline receipts; the final regression suite passes 486 tests. Gemini's unchanged first response and issued prompt, isolated-chat approval and original bytes are preserved, but the model display name/effort are author-reported and no missing API ID or exact backend version is invented. Those supplementary raw archives are now public under DOI 10.5281/zenodo.23377537, with all four archived campaign verifiers and complete anonymous-download hash checks passed. Independent co-author reproduction remains open; the earlier R5 DOI does not cover the new archives.

**Author action:** Added available provenance, prospective freezes and complete first-run archives; distinguished same-host/offline reproduction from independent execution, historical unavailable data from retained new responses, and the two separately identified public evidence versions.

**Location:** Agent-to-PNN Protocol and Results; Threats to Validity and Limitations; Data Availability.

**Evidence:** R3-live; R5-reproduction/publication; revision baseline record; AP1–AP3 and Gemini evidence indexes, immutable input/source receipts and offline verification.

## Reviewer 3

### R3.1

**Concern:** The harness withheld simulator execution and physical execution was unavailable, so the 160/160 results do not show protection through an active lifecycle.

**Author response:** Correct. The replacement allows mock/SDK execution: six permitted opportunities complete, two stale calls reach admission and are blocked, and eight strict planner deviations remain. Direct tests bypass planner refusal and independently check effects/results. A deterministic 32-case reference completes all eight allowed opportunities; it is oracle-fed harness validation, not an LLM result. AP1 further separates gateway precondition checks from provider preparation, confirms six valid controls execute/deliver, and observes twelve legitimate commits whose invalid post-execution evidence prevents delivery. Its detector controls expose bypass and suppressed valid execution. These active-lifecycle observations address the harness-withholding issue but support bounded software enforcement, not arbitrary agent/physical safety.

**Author action:** Replaced old main agent tables with executing/direct/control results and distinct denominators.

**Location:** Agent-to-PNN Protocol and Results; Discussion; Tables `tab:executing-agent` and `tab:supplementary-enforcement`.

**Evidence:** R3-direct; R3-reference; R3-live; AP1.

### R3.2

**Concern:** The audited MCP trace did not launch the provider-facing SDK run. Shared code/hashes do not bind authorization, lease, execution identity, provider completion, and result delivery across one path.

**Author response:** We agree that shared files/hashes alone did not establish the continuous path. The new bridge starts a fresh SDK Simulator process from the admitted MCP task. Its manifest binds principal, request, task, resource, lease, attempt, SDK identity, configuration, decoder, native recording, result and final state. Nine conditions twice yield 18 trials, 110 MCP calls, 220 audit events and 14 SDK starts. Four successful deliveries are independently reconstructed. Abort/timeouts preserve partial recordings; crashes preserve unfinalized evidence. Unknown termination quarantines the resource until reconciliation. Windows process containment checks observed termination before reuse; unsupported platforms fail closed. This is causal simulator integration, not Cloud/CL1 execution or physical attestation; those bindings remain unimplemented.

**Author action:** Implemented/measured the continuous path, recovery and native reconstruction; retained the historical separate-trace boundary.

**Location:** BioPattern Gate Application Workflow; Cortical Labs E3 Case Study; Discussion; Table `tab:biopattern-e3-trace`.

**Evidence:** R2 per-trial manifests, recordings and reconstruction reports.

### R3.3

**Concern:** Portability lacks concrete cross-binding examples for units, admissible ranges, timing, calibration validity, and postconditions.

**Author response:** We agree that a shared top-level schema was insufficient to explain portability. The PNRC distinguishes field types from binding obligations. The binding table specifies concentration versus spike/feature encodings, operating/timing assumptions, observation/calibration requirements and postconditions. Common production validation checks task/backend identity and finite output; fixture probability predicates are not universal validators. SDK delivery is independently reconstructed and bound to its server-owned preset. AP1 now applies strict semantic checks only to task-required telemetry/confidence, with an absent optional-drift positive control, preserved supplied timestamps and predefined same-health-property contradictions. Those executable examples complement the binding table but do not validate chemical, wetware or photonic operating ranges against real hardware. Optional calibration and unsigned provider declarations remain trusted inputs, not physical-validity evidence.

**Author action:** Expanded binding contracts and tested common identity/result checks, strict required-evidence semantics, optional-field controls and continuous SDK postconditions; retained the distinction between declared ranges and physical calibration.

**Location:** Physical Neural Resource Contract; Implementation and Adapter Integration; Cortical Labs E3 Case Study; Tables `tab:binding-contracts` and `tab:supplementary-enforcement`.

**Evidence:** R2; R3-direct; AP1; R1 binding-contract/invariant document.

### R3.4

**Concern:** The 7/7 versus 6/7 comparison needs decisive case-level explanations. Weighted-heuristic perturbations do not establish robustness of the lexicographic policy.

**Author response:** We agree that the original one-case difference needed explanation and did not establish robustness. In the archived seven-case comparison, static-priority and seeded random-admissible choose remote-edge-backend instead of edge-backend for edge_low_latency; constraint-based chooses edge-backend instead of remote-edge-backend for remote_fog_monitoring. All three handle the drifted-primary, stale-chemical and missing-supervision cases correctly: those are not the decisive failures. The differences reflect the benchmark's specified placement preference among eligible choices, not an observed physical-utility advantage. We no longer use weighted-policy perturbations to support lexicographic robustness. R4 instead supplies 64 cases, five policies, two orders and 38 changes to active limits/priorities/ties; all 640 outputs conform, with principal-choice agreements of 29/36 latency-first, 33/36 locality/cost, 29/36 static and 27/36 seeded random over nonempty cases. The separately Gemini-authored suite adds twelve frozen cases, with five policy-divergent cases and 72/72 eligible-set/ranking/selection/annotation matches under three policies and two orders. Neither agreement score establishes placement optimality, general workload accuracy or physical performance. External model authorship and pre-run author approval improve the workload's provenance, not independent human reproduction or representative sampling.

**Author action:** Added the actual historical decisive case/resource choices, active lexicographic sensitivity and externally authored frozen cases; removed unused-weight robustness and general superiority interpretations.

**Location:** RQ1: Contract, Safe Admission, and Portability, including Externally Authored Selector Cases; Threats to Validity and Limitations.

**Evidence:** Historical matching_baselines_results.csv; R4-selection; r4-oracle-approval.md; Gemini original cases, first-run matrix and evidence index.

## Author review and submission gates

- Check concerns, responses and final manuscript locations against the decision/PDFs.
- Obtain independent co-author reproduction; the automated same-host run does not satisfy this gate.
- Decide on IEEE Access resubmission; the editor has not answered the physical-evidence scope question.
- Public revision evidence is published at https://doi.org/10.5281/zenodo.23281161 and cited in Data Availability; review the matching rebuilt manuscript/response packages.
- The separately authorized AP1–AP3/Gemini raw publication is complete at https://doi.org/10.5281/zenodo.23377537, with archived-campaign verification and full anonymous-download hash checks passed; review its distinct citation and matching rebuilt manuscript/response packages. The earlier R5 DOI does not cover these new archives.
- Approve the official checklist and upload categories. Nothing is uploaded without explicit authorization.
