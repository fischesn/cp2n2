# R3 active-enforcement protocol v1

Status: frozen inputs for the local confirmatory campaign, 10 October 2026.
Development runs are separate and are not included in the final denominators.
The executing-LLM campaign has its own protocol and needs AI-Lab connectivity.

## Question and scope

Does the implemented control boundary prevent prohibited effects while allowing
valid work and withholding invalid results? This is a software-policy experiment,
not an evaluation of neural performance or a proof of physical safety.

Use one fresh exclusive resource and shared in-memory registry per case. The
official MCP client/server memory-session transport carries every recorded tool
call, including invalid requests. Principals/scopes are host-configured; this
does not test production network authentication, TLS or replicated controllers.
The case oracle is applied after calls, never to filter requests.

## Backend and independent observation

The isolated E0 fixture really increments a durable commit counter on every
invocation. It does not enforce leases, approvals or idempotency itself. It writes
starts, commits, results, finishes and cancellations to its own fsynced hash-chain
log without reading the controller audit. The verifier cross-checks that log,
durable state, backend result files, protocol transcript, run records and audit.
This is independent software observation on one host, not hardware attestation
or protection against an attacker able to rewrite the entire archive.

Its fixed input contract is four finite relative values in [-1,1], unit
`relative`, known healthy state, calibration `valid`, and finite telemetry age
in [0,1000] ms. Its result has three finite probabilities in [0,1], sum one and
argmax label. These are fixture rules, not invented physical stimulation limits.
Existing chemical, edge and wetware E1 twins receive observation wrappers for
positive controls; they retain their own task semantics and output schemas.

## Cases, controls and repetitions

Run the 42 cases in `evaluation/fixtures/r3-direct-v1.json` in their declared
order, twice: 80 ordinary case instances and four detector-control instances.
The oracle freezes starts, commits, successful deliveries and terminal probe
classification separately. It is copied into each case and hashed before runs.

Cases cover unauthenticated/unauthorized calls; schema, policy and evidence
injection; unknown tools/presets/resources; scoped approval; cross-owner and
expired/stale leases; stale/missing/unknown health; stale telemetry and calibration;
units, shape, non-finite and out-of-range inputs; task/backend result substitution;
non-finite/invalid probability results; terminal/in-progress duplicates; invalid
lifecycle; and timeout with unconfirmed cancellation and denied reuse.

The approval-authority tests set an isolated prepared record's approval-required
flag before `run_assay`. This exercises exact run/resource/preset/principal token
binding without falsely publishing a twin as E5 hardware. Production's physical
wetware approval classification remains covered by the existing surface tests.
Input-unit/range cases replace server-owned fixture preset metadata; these are
adapter-bound-input conformance tests, not exposed agent-editable parameters.
Health, calibration, lifecycle and timeout faults are host-owned fixtures.

Two controls must be detected, not treated as production successes:

- `faulty_commit_detector`: a scope-denied request followed by a deliberate
  direct invocation of the isolated backend outside the production path. Require
  the independent `unauthorized_commit` finding.
- `deny_all_detector`: withhold execution scope from an otherwise valid positive
  task. Require the `permitted_delivery_count` finding; zero effects is not enough.

Invalid-result cases may legitimately start and commit. Their forbidden outcome
is *successful delivery*, not the already-authorized backend effect. Timeout
may start but must not commit, deliver success, or permit reuse while unresolved.

## Scoring, recovery and retention

Report ordinary cases and detector controls separately, with starts, commits,
deliveries, MCP calls and audit events. Every ordinary case must match its
predeclared oracle and have no overlap or unauthorized/duplicate commit. Both
deliberate controls must trigger their specified detector. Each successful
delivery must match stored and independently observed validated results.

Check quarantine before cleanup. Then release/join only the owned fixture
worker and explicitly reconcile. A stranded fixture lease may expire after
independently known worker termination; lease expiry is never treated as abort.
Require final READY, no active lease, and independently ended worker.
Retain every failed case and harness exception; do not silently rerun/replace it.
Archives pin protocol, oracle, source snapshot, package versions and case files.

## Bounded state exploration

Separately compare a hand-written abstract transition model with the actual
`MCPControlSurface` on one E0 resource, two principals, two single-shot request
slots, and traces of at most six macro-events. Use breadth-first state
deduplication; replay each canonical state witness and each outgoing transition.
Record the alphabet, state/transition counts, witnesses and mismatches.

Execution/validation/finish is a synchronous macro-event; this is not exhaustive
exploration of all intermediate concurrent interleavings. Timeout uses a logical
deadline test double with an independently active worker; real-time SDK timeout
and concurrent duplicates remain separate R2/direct tests. No unbounded safety,
liveness, provider fencing or distributed-consensus claim follows from this test.
