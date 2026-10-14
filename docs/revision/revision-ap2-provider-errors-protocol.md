# AP2 provider failure and explicit recovery protocol

Status: prospective protocol, authored before scored runs. Version `revision-ap2-provider-errors-v2`.

This package measures the production orchestrator/HTTP controller with separate
effect-producing provider and actual TCP proxy processes on one loopback host.
It does not use physical substrates, multiple hosts, packet-loss emulation,
durable controller state or competing controllers. No historical R4 observation
or oracle is overwritten. This is a new post-review implementation study.

## Frozen conditions

Run three repetitions of each condition in separate directories:

| Condition | Intervention after controller registration | Required behavior |
| --- | --- | --- |
| baseline | None | Successful directed execution and cached replay, exactly one commit |
| planning_partition | TCP proxy closes telemetry connection before forwarding | Structured planning transport error; no start; resource unreachable; healthy provider recovery alone cannot permit reuse; explicit reconciliation then permits one new task |
| provider_stop | Stop the registered provider process | Structured planning transport error **or bounded-read timeout**, no effects and explicit reconciliation; restarting the provider is not controller recovery |
| invalid_telemetry | Provider publishes a JSON array instead of a telemetry object | Structured invalid-telemetry error; no start; explicit reconciliation required after corrected payload |
| healthy_alternative | Primary telemetry partition, secondary provider healthy | Secondary succeeds; primary has zero effects and structured provider error; reconciliation can recover primary |
| lost_invoke_reply | Proxy forwards invocation then discards entire provider response; secondary is healthy | Primary commits exactly once; returned invocation status uncertain; no automatic invocation retry or secondary invocation; repeated key remains same uncertain result; new directed primary task blocked until explicit reconciliation |

Planning reads wait at most the task preparation timeout. A timed-out Python
worker is not cancelled; unit tests separately require that reuse/reconciliation
is refused while a timed-out read remains pending. Known provider I/O and payload
schema errors are normalized; arbitrary programming errors are not reclassified
as successful or silently ignored resources.

For pre-invoke failure conditions retain the first response, retry while fault
persists, failure of reconciliation while fault persists, corrected provider,
blocked task before reconciliation, explicit reconciliation and successful new
task. Every checkpoint records independent provider ledger/state summaries.
For lost replies retain unknown response, same-key replay, blocked new directed
request, explicit reconciliation and a distinct task after operator-directed
recovery. Reconciliation observes readiness only: it cannot recover the missing
result or prove that an uncertain historical operation did not commit.

## Freeze and verification

Before any scored provider starts, retain this protocol, full specification,
environment, source snapshot and SHA-256 freeze receipt. Exact functional files
must match the parent-approved freeze. Preserve all first-run trials, failures,
process logs and complete requests/results. Do not adjust expected values to
observations. Any correction requires a new campaign identifier/freeze.

Offline verification recomputes all archive hashes and effect-ledger hash chains;
checks state/ledger agreement, unique request-to-commit identities, no overlap,
all owned processes stopped, expected error code/reason/phase, blocked reuse,
explicit recovery, and observed TCP forwarding/withholding evidence. Counter
expectations are independently computed from persisted provider files, never
from control-plane success flags alone.

Provider loss occurs only after descriptor discovery/registration. Startup
failure is a deployment error, not a scored fault trial. Automatic retries of
state-changing calls are prohibited. All resources remain capacity-one,
controller state is in memory, and no restart-safety claim follows.

## Development-only correction before confirmatory freeze

The first complete development campaign (`revision-ap2-development-20261014-b`)
used v1 and retained 15/18 matching trials. Its three provider-stop trials met
the no-effect, quarantine and recovery requirements, but returned a bounded
planning timeout rather than the overly specific expected transport exception.
The Windows connection-refusal/backoff can outlast the one-second planning
deadline. V2 accepts these two legitimate failure classifications for this
condition only; other expected reasons and all effect/recovery requirements are
unchanged. The development raw files, v1 source snapshot and negative receipt
remain unmodified. No scored v1 experiment was conducted.
