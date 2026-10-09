# R1 binding contracts and execution invariants

**Date:** 9 October 2026. This is the implementation handoff for R2 and R3.
The current-code descriptions below are not promises that every desired
precondition already has a validator. No new runtime feature is introduced in R1.

**Later R2 checkpoint:** the [continuous execution and recovery results](r2-recovery-results.md)
now cover C08/C11 and the local SDK portions of C01/C07/C09/C10. The descriptions
below remain the R1 specification; this does not mark the broader R3 enforcement,
cross-binding or executing-LLM cases complete.

## Shared contract and current implementation

PNRC v1.0 separates identity, runtime evidence, capabilities, dynamic state,
safety, access, cost and data governance. Generic admission checks a known
runtime/evidence pair, operation permission, declared supervision/exclusivity,
and admissible lifecycle/health observations. E5 additionally requires hardware
identity and declarations for limits, emergency stop and operator acknowledgement.
Those declarations alone do not prove that a physical device is safe.

`BaseAdapter.resource_contract()` wraps runtime telemetry with its source,
publication-time observation/receipt timestamps and a 30 s validity interval.
For synthetic twins this is publication of software state, not a new physical
measurement. Unknown units are `None`; uncertainty is generally `unknown`.
The schema allows missing calibration, occupancy and drift. A missing
`valid_until` is treated as fresh by that field alone, and non-physical generic
admission can accept a declared `unknown` health value. A task's explicit
information-age requirement and matcher checks are additional gates, not an
implicit guarantee for every optional observation.

`SafetyContract.hard_limits` is empty for the generic twins. Numeric range
validation is performed only where a binding implements it. Generic result
postconditions check supplied confidence against a requested minimum, presence
of requested telemetry, requested information age, monitoring-field presence,
and an offline backend. Missing confidence does not fail the current minimum
check. A field present with a null or wrong semantic value is not necessarily
rejected by a presence check. Backend/task identity, finite payload values,
probability normalisation and native-artifact completeness are not checked by
that generic method. R2/R3 must add the explicitly scoped checks before measuring
their enforcement; do not report them as existing results.

## Binding instances

| Binding | Input and output | Actual preparation predicates and unsupported ranges | Timing and validity |
|---|---|---|---|
| Chemical E1 | `input_level` relative concentration, no molar unit; default 1.0. JSON signal, intermediate concentration, label and convergence flag. | Input > 0; contamination < 0.98. No finite-value/upper-bound/physical-unit contract. Invalid scalar conversion falls back to the synthetic default. | Descriptor 9500 ms typical / 800 ms jitter; software dynamics and synthetic convergence latency. Published calibration proxy changes with use; descriptor confidence 0.90 is configured, not calibrated. |
| Wetware E1 | `stimulation_strength` scalar, no physical unit; default 0.55. Default `observation_window_ms=120`; spike count, rate in Hz, window in ms and label. | Strength > 0; viability >= 0.20. No physical charge/amplitude upper bound or comprehensive positive/finite window check; conversion failures fall back to defaults. | Descriptor 45 ms / 10 ms jitter; synthetic viability/noise/drift. Descriptor confidence 0.84 is configured; no runtime physical-calibration observation. |
| Edge E1 | Four-element vector; optional vectorised tensor; units/ranges unspecified. Three probabilities and label index. | Preparation checks length four. No complete finite-value/amplitude or output probability validator. | Descriptor 4.5 ms / 0.8 ms jitter; synthetic drift and energy proxy in mJ. Descriptor confidence 0.95 is configured, not a physical error bound. |
| Remote edge E2 | Same vector/result semantics through HTTP to a separate runtime process. | Same software obligations plus RPC/schema/transport failures. Not a different physical substrate or a replicated lease store. | Same-host service measurements; fault wrappers change delivery or telemetry age, not real sensor behavior. |
| BioPattern Gate E3 control binding | Only server-owned `pattern_gate_v1`/`technical-e3` references and pinned application/config/decoder hashes; sanitized JSON summary. No agent-editable physical primitives. | Frozen configuration: two distinct inputs, disjoint readout, reversed A/B order, matching design/charge token, strict fields. The token is a software equivalence assertion, not measured physical charge. | 20 ms inter-step, 5 ms blanking, observation from 10 ms for 100 ms, 20 ms inter-trial, 20 ms feature bin, 30 s timeout; 2 blocks of 3 trials/class and 1 sham. Config hash `5fccaac3022e223fc181508833eaad38755279556b43b6b2df4e2f7e032a08e4`. |
| Official CL SDK E3 application | Atomic software stimulation plan, acknowledgements, spike events and native HDF5; independent offline features/decisions. | Simulator guard; expected channels/events/windows; pinned decoder hash. Existing separate-run reconstruction is not yet a per-MCP-task native-recording check. | Uses the same application core; timestamps/units are SDK software observations. Biological calibration and provider approval absent; `calibration_ref=null`. |

The core twins' timing numbers describe intended regimes; short local wall-clock
execution does not reproduce those physical durations. Twin confidence and
runtime calibration-confidence proxy are different fields. In particular, the
BioPattern descriptor's confidence 1.0 is a configured software declaration,
not perfect biological calibration.

Source paths: `adapters/{chemical,wetware,edge,remote_edge,biopattern_gate_e3}_adapter.py`,
`adapters/base_adapter.py`, `runtimes/twin_runtimes.py`, `twins/*_twin.py`,
`applications/biopattern_gate/{config,control_plane_contract}.py`, and
`applications/biopattern_gate/presets/simulator/technical-e3.json`.

## Operations and approval

Generic adapters publish describe, telemetry, prepare and invoke, with reset,
recalibrate and abort only according to their declaration/runtime support.
Chemical: flush/recharge/hard reset; wetware: rest/recalibration/hard reset;
edge: soft reset/recalibration/hard reset. Chemical and edge do not require
exclusive access or supervision; the synthetic wetware binding requires both.
These are policy declarations for twins, not institutional permission for
living cultures. Training is metadata, not an exercised train/update/rollback API.

The agent-facing assay interface grants less authority than the generic adapter:
an agent may select a published preset and request an outcome, not choose
electrodes, pulse amplitudes, decoder weights, approvals or evidence labels.
The E3 binding requires exclusivity but not human supervision. Its provider
contract is unverified, approval references empty and provider-approved preset
catalog empty. The configuration validator rejects all E5 modes until a separately
reviewed provider preset is registered. Later physical approval must bind the
exact run, resource, principal and approved configuration; R1 authorises no such run.

## Lifecycle and ownership

The successful path is DISCOVERED -> READY -> RESERVED -> PREPARING -> RUNNING
-> VALIDATING -> COOLDOWN -> READY. Failed preparation, execution, validation or
recovery preserves a typed terminal/exceptional state. Loss of contact produces
UNREACHABLE, not success. The allowed-transition table in `core/lifecycle.py`
and expected-version check define the actual edges; an illustrative diagram
must not imply every state pair is legal.

Exclusive acquisition is atomic only inside the shared in-memory registry.
Renew/release must prove ownership; expired leases cannot authorise new use.
Expiry is not device cancellation. Timed-out Python workers may keep running;
unknown completion blocks reuse until explicit authoritative reconciliation.
Reconciliation refuses an active lease; unknown active provider state is not
converted to READY. Restart/replication needs durable state and provider fencing,
neither supplied by this revision package.

Client-scoped idempotency replays completed requests, rejects a changed request
under the same key and distinguishes an in-progress duplicate. Early failure
before a lease is obtained can remain retryable. R2 must specify the execution
attempt boundary and retry rules for a lost provider reply. A local request ID
is not a provider-issued run ID or device attestation.

## R2 admission and execution acceptance gates

Before launch, require a registered simulator runtime, the exact server-owned
application/preset/version and hashes, explicit current readiness/known health,
bounded fresh telemetry, required fields with valid types, permitted operation,
configured principal/assay policy, a live owner-bound exclusive lease, the expected
lifecycle version and a non-conflicting idempotency key. Recheck mutable state at
the commit boundary. Unknown physical units/limits cannot be converted into a
physical preset. Strict server-owned E3 configuration may not enable Cloud/E5.

Successful execution must start a **new** official SDK Simulator run, not read an
old summary. One manifest binds task/principal/resource/lease/request/attempt,
application/config/decoder/source hashes, controller-assigned and genuine provider
IDs (distinguished), native recording, validated result and audit events. Native
events must independently reconstruct the delivered result. Identity, hashes,
expected trial completion, acknowledgements, event groups and observation windows
must agree. Aborted or incomplete data remain explicitly partial; no success
payload may be delivered until every required postcondition passes.

Completion and established termination release ownership according to the
lifecycle. Timeout/lost reply without termination retains quarantine and a typed
unknown outcome; retry cannot silently start another run. Recovery must retain
the original attempt and evidence. The legacy eight-call/16-event counts are not
targets for the new trace.

## R3 measurable invariants and proposed tests

These are **acceptance specifications, not newly passing tests**. Exercise
cross-binding schema/operation cases for chemical, wetware, local/remote edge,
the E3 control binding and the official SDK bridge where meaningful. Do not
force one binding's neural output schema onto another. For unsafe numeric cases,
use only isolated software backends; define their finite/unit/range contract
before testing it, rather than inventing physical amplitude limits.

| ID | Required observation | Positive and negative test cases | Package |
|---|---|---|---|
| C01 | Schema/source/evidence are unambiguous | Valid version; unsupported version; missing/mismatched runtime evidence; attempted E3->E5 promotion | R2/R3 |
| C02 | No forbidden backend start/commit | Permitted operation versus denied principal, missing approval, unknown assay or physical-parameter injection sent directly to server | R3 |
| C03 | Bound inputs are checked before effect | Valid input; wrong unit/type/shape; NaN/Inf; out-of-contract range; undeclared physical conversion | R3 |
| C04 | Required state is fresh and semantically valid | Valid timestamp/age versus expiry, replayed old observation, missing/null/wrong-type required field, unknown/conflicting health | R3 |
| C05 | Required calibration is not inferred | Binding supports known calibration versus missing/stale/conflicting calibration; unsupported binding explicitly rejected when calibration is requested | R3 |
| C06 | One exclusive owner in supported scope | Two clients sharing one controller; cross-owner use/release; expired lease; stale lifecycle version; no overlapping independently logged effects | R3 |
| C07 | Idempotent retry has no duplicate effect | Same completed request, in-progress retry, changed payload under same key, lost reply after commit | R2/R3 |
| C08 | One MCP task causes one fresh SDK run | New request, new native file, complete manifest; substituted old summary/native recording/config/run identity rejected | R2 |
| C09 | No unvalidated successful result | Valid result versus mismatched backend/task/attempt, wrong decoder/hash, incomplete trials, invalid events, non-finite/probability payload where applicable | R2/R3 |
| C10 | Unknown completion never enables reuse | Timeout, partition, late result and failed abort; quarantine until explicit authoritative reconciliation | R2/R3 |
| C11 | Partial failure is truthful | Cooperative abort and failed launch/validation preserve partial evidence without a completed/success label | R2 |
| C12 | Policy/result checks detect deliberate faults | Isolated faulty test double that commits or accepts a substituted result; independent checker must flag the forbidden effect | R3 |
| C13 | Valid controls actually execute | At least one permitted state-changing run per applicable backend contract; deny-all cannot count as enforcement success | R3 |
| C14 | Planner scoring is separate from enforcement | Freeze oracle and variants before campaign; send invalid requests without oracle pre-filtering; score planner and independently observed effects separately | R3 |

Existing regression anchors include `test_adapter_conformance.py`,
`test_resource_contract.py`, `test_lifecycle_protocol.py`,
`test_biopattern_gate_config.py`, `test_biopattern_gate_execution.py`,
`test_biopattern_gate_mcp_e3.py`, and `test_biopattern_gate_cl_api.py`.
Their current passing status does not imply coverage of all C01--C14.

## Bounded state exploration decision

Implement a small deterministic state/property test in **R3**, after the effect
observer and invariants exist. Bound it initially to one exclusive software
resource, two clients, two request keys and sequences of at most six events.
Events include acquire, prepare/start, duplicate, expire, timeout, finish,
validation failure, abort and reconcile. Deduplicate states; publish the event
alphabet, explored state/transition counts and failing traces. Compare model
transitions with the implementation, not just with a separately written model.

Check ownership exclusivity, no denied commit, no success before validation,
and no reuse while completion is unknown. Retain existing multi-thread races
as separate implementation tests. This finite exploration is useful regression
evidence, not an unbounded liveness proof, replicated-consensus result or proof
of physical safety. R1 fixes this scope; it does not report exploration results.
