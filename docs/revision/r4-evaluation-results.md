# R4 evaluation results

R4 now has larger selection, contention and timing evidence, plus bounded
TCP connection/reply experiments. The experiments retain three limitations:
the selector can admit present nonnumeric drift, pre-invocation provider
failure can escape as HTTP 500, and restarting the controller can repeat a
committed operation. None is a new physical-substrate result.

The [separate-container extension](r4-container-results.md) now adds 21 trials
and 57 execute attempts on the same physical host, after the authorized Docker
repair/update. It confirms three restart duplicates and 18 generic early HTTP
500 responses. Stefan Fischer subsequently
[approved the twelve oracle sample outcomes](r4-oracle-approval.md);
independent clean-checkout reproduction remains pending. The journal and arXiv
manuscripts have not changed; integration and the full reviewer response are
R5 work. The R3/R4 checkpoint was subsequently committed and pushed as
`f5802a3`; no release was made.

## Frozen evidence and reproduction

The [protocol](r4-protocol.md) specifies counts, comparisons and analysis before
measurement. Each archive contains its original protocol copy, flat inputs,
environment, frozen source ZIP, raw observations, a hash inventory and an
offline-recomputed report. The four source snapshots contain the same 238
files; ZIP hashes differ because their packaging timestamps differ. The
versioned [artifact index](../../evaluation/fixtures/r4-confirmatory-20261010.json)
binds the exact manifests, specifications and source snapshots.
The later container campaign has its own protocol/source/image freeze and
[index](../../evaluation/fixtures/r4-container-confirmatory-20261010.json);
it does not replace the four original snapshots.

| Subpackage | Local archive | Result |
| --- | --- | --- |
| Selection | `.cp2n2/r4-selection-confirmatory-20261010-01` | 640 policy/order comparisons and 38 sensitivity comparisons conform |
| Contention | `.cp2n2/r4-contention-confirmatory-20261010-01` | 20 trials, 225 requests, 60 completions, 165 immediate rejections, no overlaps |
| Overhead | `.cp2n2/r4-overhead-confirmatory-20261010-01` | 40 fresh-registry trial blocks, 16,000 measured and 1,600 warm-up operations |
| TCP extension | `.cp2n2/r4-transport-confirmatory-20261010-01` | 21 expected effect patterns observed, including three restart failures |
| Container extension | `.cp2n2/r4-container-confirmatory-20261010-01` | 21 trials/57 attempts, including three restart duplicates and 18 early HTTP 500 responses |

The raw directories are ignored and local, not yet public release assets.
From the repository root, with the project virtual environment active:

```powershell
python scripts/run_r4_evaluation.py --kind selection --output .cp2n2/r4-selection-new
python scripts/run_r4_evaluation.py --kind contention --output .cp2n2/r4-contention-new
python scripts/run_r4_evaluation.py --kind overhead --output .cp2n2/r4-overhead-new
python scripts/run_r4_evaluation.py --kind transport --output .cp2n2/r4-transport-new
python scripts/run_r4_evaluation.py --verify .cp2n2/r4-selection-confirmatory-20261010-01
```

Use a new output name for each measurement; no archive is overwritten. Replace
the verification path to verify another subpackage. Reproduction uses the
archived source snapshot and its recorded dependencies, not an assumed current
checkout. R5 will perform that independent check and publish the selected raw
archives. Run the timing campaign without other experiment/test campaigns.

## Selection

The 64 authored synthetic cases span 16 families. There are 28 empty, 22
singleton and 14 multiple-resource admissible sets. Every policy receives the
same task, descriptors and telemetry. Each uses the production hard filters;
the independent flat oracle computes expectations separately. All five policies
match their specified admissible sets, rankings and rejection reasons, in both
forward and reversed descriptor order.

Principal-policy choice agreements over the 36 nonempty cases are 36/36 for
lexicographic, 29/36 for latency-first, 33/36 for locality/cost-first, 29/36 for
static priority and 27/36 for seeded random-admissible. The other 28 cases
agree trivially because every policy returns no candidate. These agreements
measure preference conformity, not a universal quality advantage. For example,
lexicographic chooses lower drift before latency, while latency-first chooses
the faster admissible option; the study does not establish which application
utility is superior.

All 19 active threshold/priority/tie conditions match their specification in
both input orders. Age, latency and cost use inclusive bounds; drift uses an
exclusive bound. `sensitivity.png` plots the actual boundary outcomes.
`selection.json` retains all observations and full reports; `case-table.md`
lists principal expected/observed sets and choices with exclusion reasons.

The twelve analytical sample checks in the review fixture were performed by
the authoring agent before scoring. They are not human author approval or
second-author validation. The original frozen review text called this
"single-researcher review"; current documentation clarifies that label without
changing the archived expectations or any result. On 10 October 2026, Stefan
Fischer separately [approved those twelve admissible sets and selections](r4-oracle-approval.md).
This post-run human review does not retroactively make the pre-run checks human
validation or independently validate all 64 cases.

`missing_telemetry-2` deliberately contains the string `unknown` as drift.
The selector admits it: required telemetry currently means present/non-null,
and the drift rejection threshold applies to numeric values only. Ranking
assigns the missing-drift penalty. This is specification conformance, not
numeric telemetry validation; do not claim otherwise. Calibration validity
and execution-contract checks are separate R3 evidence. The authored cases
and deterministic reverse-order comparisons are not statistically independent
real-world workloads or evidence of physical predictive accuracy.

## Contention and idle lease expiry

Four burst levels (3, 6, 12 and 24 clients), five fresh trials each, target three
independent effect-observed twins. Each resource completes exactly one request
per trial. All 165 competing rejections have code `RESOURCE_BUSY`. Effect
ledgers and durable counters verify 60 starts/commits, no same-resource overlap,
correct task/owner/live-lease binding, released leases, READY lifecycle and
finished workers. Different resources start before the diagnostic gate opens.

The third descriptor declares nonexclusive access, but the controller still
serializes it. Capacity is one for all three resources. TTLs are 5/10/20
seconds, and there is no queue, fairness or shared-capacity scheduler. Timing
in this deliberately gated burst is descriptive, not natural service
throughput; other same-machine test activity was not excluded from that burst.

All three idle-expiry probes pass. A lease expires after the bounded wait, but
the resource remains RESERVED and cannot be reacquired until reconciliation.
After reconciliation it can be reserved and released normally. This does not
prove active-operation preemption or durable crash recovery.

## Wall time and incremental overhead

Environment: Windows 11 build 26200, Intel Core Ultra 7 258V (8 cores/logical
processors), approximately 32 GiB RAM, Python 3.14.4, MCP 1.28.1, NumPy 2.5.1,
Pydantic 2.13.4 and Matplotlib 3.11.1. Full metadata is archived. CPU affinity,
power mode and background OS work were not controlled. No other evaluation
campaign ran alongside the final timing measurements.

Each path/configuration has ten fresh trials with 20 warm-up and 200 measured
calls, alternating paired block order. All 16,000 measured operations succeed.
The table reports the median of the ten trial medians and the median of the
ten within-trial p95 values, not a pooled p95 or population estimate.

| Path | Median wall time ms | Median trial p95 ms | Incremental paired median ms | 95% trial-bootstrap interval ms for increment |
| --- | ---: | ---: | ---: | --- |
| Direct adapter, 1 resource | 0.022 | 0.026 | — | — |
| Controlled execution, 1 resource | 1.846 | 3.350 | 1.824 | 1.745–2.015 |
| Direct adapter, 3 resources | 0.023 | 0.025 | — | — |
| Controlled execution, 3 resources | 2.471 | 3.851 | 2.448 | 2.197–2.610 |
| Direct adapter, 12 resources | 0.022 | 0.029 | — | — |
| Controlled execution, 12 resources | 3.424 | 5.796 | 3.402 | 3.271–3.592 |
| Audited direct surface discovery | 2.009 | 2.577 | — | — |
| Audited official MCP memory discovery | 9.997 | 12.413 | 7.922 | 7.643–8.603 |

Closed-loop controlled throughput is approximately 441, 366 and 261
operations/s for 1/3/12 resources, using medians of trial block throughput.
The discovery paths yield approximately 470 and 96 operations/s. Execution
block throughput includes reset/recalibration and loop housekeeping; it is
not saturation throughput or a multi-client scheduling result.

Measured controlled adapter-invoke wall time is approximately 0.084–0.100 ms;
the remainder is approximately 1.763–3.315 ms and includes preparation,
telemetry and control work. Direct invoke is approximately 0.018–0.019 ms.
Use full paired-path differences for incremental cost, rather than pretending
that wall-minus-invoke perfectly isolates control-plane work. The synthetic
reported device latency is not elapsed wall time and is not a CL1 measurement.

MCP discovery uses one persistent official in-memory session per trial, with
session startup outside the timer. Both discovery paths include the same
durable audit work. There are 4,400 discovery calls including warm-up: 2,200
actual MCP and 2,200 direct surface calls, with 8,800 verified audit events.
This is not MCP over TCP/stdio or an executing-assay MCP latency measurement.
The 2,000 bootstrap samples resample trial summaries, not individual dependent
calls. Their intervals express repeatability on one machine, not ten
deployments or independent environments. No p99 is reported.

## TCP failures and restart limits

Three fresh trials cover each of seven conditions using a provider, production
HTTP controller, two byte-stream proxies and the runner, all on Windows
loopback. Socket closure and withheld replies are actual connection faults;
no HTTP 503 response is fabricated. The 50 ms forwarding delay measures
50.497, 50.177 and 50.325 ms across the three trials. There is no packet-loss,
separate-container, multi-host or physical-substrate claim.

| Condition | Provider commits per trial | Interpretation |
| --- | ---: | --- |
| Baseline / delay | 1 | Successful execution; same-key retry replays without another effect |
| Lost client reply | 1 | Completed controller result survives retry within the same process |
| Lost provider reply | 1 | Failed invocation leaves UNREACHABLE state; same-key retry has no new effect and new-key reuse is refused |
| Provider partition / termination before request | 0 | No effect; early telemetry failure returns generic HTTP 500 |
| Controller restart after lost provider reply | 2 | Prior quarantine is lost; replay causes a duplicate durable effect |

All 21 predeclared effect patterns occur, including all three unsafe restart
negative controls. An expectation match is not a safety pass: the protocol
expects this known unsupported guarantee to fail. There are 18 total provider
starts/commits, no overlapping operations, and all owned processes are stopped.

In the six partition/provider-termination trials, all 18 first/same-key/new-key
attempts receive HTTP 500. The client helper's `delivered: false` includes
HTTPError, not just a lost reply; controller span logs retain the 500 status
and RemoteDisconnected cause. The verification field `new_key_blocked` denotes
a nonsuccessful request, not necessarily an explicit control-plane denial.
These pre-invocation failures do not prove quarantine. The later lost-provider-
reply trials do prove the tested same-process quarantine behavior. Generic
pre-invocation error reporting is a limitation for future improvement, not
silently fixed after scoring.

Lease, idempotency and lifecycle state are in memory. A surviving span/audit
file does not restore them, and there is no startup unfinished-task
reconciliation. The duplicate after restart is consequently a real limit of
the current implementation. R5 must remove durable restart guarantees from
the manuscript and answer that reviewer concern explicitly; a durable store
or replicated controller would be a separately approved architecture change.

## Remaining work and regression status

The complete suite now passes **286 tests**, with two dependency deprecation
warnings. New evaluation code does not change production control-plane
behavior. Figures have been visually checked; the manuscript is unchanged.

- The twelve frozen oracle sample outcomes have human author approval;
  no further sign-off is required for that R4.1 gate.
- Multi-host and packet-level external validity remain unmeasured; the
  separate-container deployment requirement is fulfilled within one host.
- R5 clean-checkout reproduction, raw-archive publication, manuscript/figure
  integration, claim audit and complete response to all 22 reviewer concerns.

Docker Desktop 4.83.0's local log at 07:02:18 UTC on 10 October records startup
failure in its Inference Manager: the local `Docker/run/dockerInference`
endpoint cannot be removed/accessed and the listener reports invalid filename
syntax. The endpoint is a zero-length reparse point. This identifies the
original startup failure, not its deeper cause. At that checkpoint no system
repair was attempted. The subsequently authorized repair preserved the old
socket directories and updated Desktop to 4.94.0 without factory reset,
deinstallation or deleting user images/volumes. The engine and restart smoke
checks succeeded, enabling the separately frozen container campaign. The old
non-container observations and archives remain unchanged.
