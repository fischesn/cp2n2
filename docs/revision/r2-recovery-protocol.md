# R2 SDK cancellation and recovery protocol

**Protocol:** `r2-recovery-v1`. **Frozen case definitions:** 9 October 2026.

This bounded conformance experiment tests termination, partial evidence,
retry behavior and resource reuse in the local official CL SDK Simulator
binding. It is not a biological experiment, an LLM campaign, a network
benchmark or a guarantee across controller restart. The paper remains unchanged.

## Execution and termination contract

Each admitted assay gets a fresh attempt directory, controller-assigned SDK
run ID and exact frozen application core/configuration/decoder bindings. A
local launcher waits for the controller to establish process containment
before entering the official `cl.app.run` entry point. On Windows, the owned
job includes ordinary SDK descendants without breakaway permission. SDK
execution is refused if containment cannot be established. Other platforms
must not silently claim the same termination guarantee.

Cancellation is a run-bound local request, not a stimulation instruction or
an agent-editable configuration. The application checks it between trials,
interrupts input channels through the existing port abort, closes the native
recording and emits a partial result. A cancellation acknowledgment alone
does not free the resource. The controller must observe that its owned SDK
process group is empty. Bounded forced cleanup is allowed only for these
owned local simulator processes; it never represents a hardware emergency stop.
An unconfirmed stop retains quarantine. Late cleanup still requires explicit
controller reconciliation before reuse.

Concurrent user abort and the original execution's failure handler must not
finalize the resource twice, overwrite a newer lease or publish late success.
Native partial evidence must distinguish a cleanly aborted recording from a
file left unfinalized or unreadable by a crash. No partial file qualifies as
a successful complete result.

## Cases and repetitions

Run the following nine cases twice, in the order shown. Use fresh surfaces,
leases and output directories for every case. Do not infer latency distributions
or failure probabilities from these two repetitions. Development runs have
separate output paths and are excluded from the frozen final run.

| Case | Controlled condition | Required observation |
|---|---|---|
| success | Ordinary frozen assay | One fresh SDK start; complete native validation; successful summary; READY with no lease |
| invalid_configuration | Extra configuration override sent to the MCP prepare tool | Schema rejection before SDK start; unused reservation released |
| launch_failure | Host executable path deliberately absent | No SDK start; typed failed result; no lease; READY |
| cooperative_abort | SDK paused after two committed decisions; owner calls abort_run | Run-bound cancellation; aborted native file with two committed decisions including a stimulated trial; no successful result; confirmed empty process group; READY |
| sdk_crash | Same checkpoint; kill only the owned parent SDK process | Failure reported; partial/unfinalized evidence retained; descendants cleaned up and termination independently observed before reuse |
| validation_failure | Change one native readout spike channel before VALIDATING checks it | Native verifier rejects the result; no successful summary; recording retained; known terminal resource finalized |
| lost_reply_duplicate | Discard the first successful run response; repeat run_assay and retrieve result | Repeated terminal run rejected; stored result unchanged; exactly one SDK start |
| timeout_confirmed | Host-owned invocation deadline expires at the SDK checkpoint | Typed unknown/timeout caller result, no successful delivery; cooperative cleanup confirmed; no lease; READY |
| timeout_unconfirmed | Isolated provider-abort test double temporarily returns false | Active SDK remains observable; resource UNREACHABLE; reservation rejected; later real cleanup and explicit reconciliation restore READY |

The diagnostic checkpoint is server-owned test instrumentation, not an MCP
parameter or a changed neural protocol. It changes wall-clock waiting only.
The frozen schedule starts with a sham, followed by a stimulated trial; the
checkpoint therefore occurs after two decisions to retain actual native
stimulation/spike data as well as the sham.
The timeout is a host-owned TaskRequest setting in the isolated harness.
Its invocation deadline is 12 seconds; it expires while the diagnostic
checkpoint is waiting. Cooperative cleanup waits at most 2.5 seconds for the
parent, followed by bounded process-job cleanup and a worker-completion check.
The absent executable, parent kill, spike alteration and unconfirmed-abort
test double are deliberate software fault injections, not provider failures
observed in ordinary operation.

## Evidence and independent checks

Retain the exact protocol, source hashes and SDK/Python versions; delivered
MCP arguments/responses and request IDs; paired hash-chained audit events;
task, principal, resource and lease identity; SDK start authorization; process
containment/termination observations; native files and their checksums; partial
or complete result records; lifecycle history, intermediate quarantine and
final state; and per-case checks with observed denominators.

The offline verifier checks file inventories/checksums, audit chains and
request identities, attempt/run/configuration bindings, native completion or
partial status, delivered-result consistency, start counts and reuse outcomes.
The ordinary success case additionally uses independent native spike/decision
reconstruction. The manifest is local integrity evidence, not signed provider
attestation; a malicious controller can forge its own records. Process-group
accounting is an independent OS observation at runtime, but its archived
JSON representation is not cryptographically authenticated by the OS.

R2 can close when all eighteen case executions meet their declared conditions,
the offline checks pass, and regression tests remain green. Unexpected failures
remain visible and must not be removed from the result archive.

Windows containment follows Microsoft's documented
[Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects)
and [active-process accounting](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_basic_accounting_information).
