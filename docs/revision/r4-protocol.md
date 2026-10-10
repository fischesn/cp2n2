# R4 evaluation protocol v1 — 10 October 2026

This protocol is fixed before the confirmatory runs. Development smoke tests
under `r4-development-*` and regression-test temporary directories are not
confirmatory observations. The old seven-plus-four selector suite, short
timing measurements, and application-layer A6 campaigns remain historical.
Every new run copies this protocol, specifications, environment metadata and
a source snapshot before measurement. New output directories must not exist.
No LLM API requests, physical substrates, Docker repair, firewall changes or
production services are involved.

## R4.1 Selection

The frozen suite contains 64 authored synthetic cases (16 families of four),
not 64 independent real-world workloads. Cases cover zero, one and multiple
admissible resources, exact identifier ties, modality, health and lifecycle,
missing telemetry, supervision, freshness capability, stochasticity/reset
preferences, conflicting constraints, and inclusive/exclusive boundaries.
All resource measurements are synthetic. Calibration timestamp validity is
tested at the execution contract in R3, not incorrectly attributed to the
descriptor selector here.

A present nonnumeric drift string is intentionally included. The descriptor
selector currently checks presence for a required metric and thresholds only
numeric drift; it can admit this ambiguous value and rank it with the missing-
drift penalty. Conformance to that rule must not be advertised as numeric
telemetry validity or physical safety. R3's executing contract checks are a
separate boundary.

`evaluation/r4_selection.py` defines a flat, specification-derived oracle;
only its separate production bridge imports BackendMatcher. Hard limits use
latency <= budget, age <= maximum age, cost <= budget, and drift < 0.95.
The independently authored review fixture records 12 analytical boundary/tie
checks with reasons. The authoring agent performed these checks before scoring;
human author approval or second-author validation was pending at freeze. Expected
outcomes are not adapted to observed production results. The original frozen
protocol copies used the imprecise label "single-researcher review". This
post-run wording clarification does not change any case, expectation, count,
policy, measurement or archived input. The subsequent post-run
[author approval of twelve sample outcomes](r4-oracle-approval.md) is recorded
separately; archived protocol copies remain unchanged.

Five policies receive the identical descriptors, task and runtime information:
lexicographic, latency-first, locality/cost-first, static priority [b,a], and
seeded random-admissible (SHA-256 of seed:task:resource). Baselines execute
production hard filters; they do not consume the oracle's admissible set.
Report admissible-set, ranking and rejection-reason conformance, empty-set
behavior and principal-policy choice agreement. Choice agreement is not a
universal quality/superiority score. Repeat all comparisons with reversed
descriptor order, without calling these deterministic repeats independent
experiments.

Sensitivity has 19 specified conditions: 0.99/1.00/1.01 times each active
latency, freshness, cost and drift boundary; three active priority orders; four
identifier/input-order tie variants. Tie resolution itself is the documented
identifier rule, not an undocumented runtime setting. No unused score-weight
perturbation is used as evidence for lexicographic robustness.

## R4.2 Contention

One fresh controller/shared in-memory registry controls three separately
identified effect-observed E1 edge twins. Two descriptors request exclusive
access; the third declares nonexclusive access but the implementation still
enforces capacity one. This tests current semantics, not shared-capacity
scheduling. Lease TTLs are 5/10/20 seconds respectively.

Client levels are 3, 6, 12 and 24, five fresh trials each. A barrier releases
clients, direct targets alternate across resources, and each request has a
distinct task, owner and idempotency key. No fallback or queue is enabled.
The first effect on each resource waits on a diagnostic gate until the three
starts and all losing requests are observed (10-second guard). The gate is
released before completion. This deliberately overlapping burst is not a
natural throughput benchmark. Archive all requests, latency/error results,
independent hash-chained starts/commits/finishes, live lease snapshots at each
start, final lifecycle and worker cleanup. Auto-acquired lease IDs are not
inserted into the original task by production code; the observer therefore
records the live registry lease separately.

An idle-expiry probe per resource acquires a 60 ms lease, waits at least 100
ms, attempts acquisition before reconciliation, reconciles and reacquires.
Expiry must remove the lease but does not itself reset RESERVED lifecycle.
This is not active-operation preemption or distributed crash recovery.

## R4.3 Overhead

Freeze the actual Windows/Python/package/CPU metadata; do not replace it with
an idealized machine description. One environment, one outstanding request,
ten fresh-registry trials per configuration, 20 warm-up and 200 measured
operations per path/trial. Alternate paired block order between trials.
The fixed payload is `[0.1,0.3,0.5,0.7]`, classification, direct target bench-0,
no fallback, separate but identically initialized EdgeAdapter twins.

Execution configurations contain 1, 3 or 12 registered resources. Baseline is
adapter prepare + invoke + telemetry. Controlled path is full execute_task,
including discovery/selection, admission, lease/lifecycle, validation and
recovery, without MCP audit. Reset/recalibrate before each operation in both
paths occurs outside the per-operation timer. Block throughput includes that
housekeeping (except the reset immediately preceding its first observation)
and loop/task-construction work. It is closed-loop single-client throughput,
not saturation or queue capacity. Timers use perf_counter_ns. Measure adapter
invoke wall time separately; synthetic reported substrate latency is archived
but never substituted for wall time or treated as a real device duration.
The wall-minus-invoke remainder includes prepare, telemetry and other work;
it is not a perfectly isolated service overhead. Paired full-path differences
estimate the incremental cost of this defined control-plane path.

A fourth configuration compares audited direct surface discovery and actual
official MCP in-memory protocol discovery over one persistent session per
trial, with three resources and otherwise identical information/audit work.
Session initialization is outside timed calls. This is not TCP or stdio MCP
latency. Audit fsync is included in both paths; all events are verified.

Report trial medians, trial p95s, dispersion of trial medians, paired median
differences, block throughput and invoke/non-invoke wall measurements.
Bootstrap 2,000 times with seed 73401, resampling the ten trial summaries, not
dependent calls. These 95% intervals describe repeatability on this machine,
not population/multi-deployment uncertainty. No p99 claim. Retain every raw
observation, success/failure and collection order. A failure is not discarded
or replaced with a favorable rerun. A second environment is unavailable.

## R4.4 Bounded transport/recovery extension

Docker CLI is installed, but its Linux engine is unavailable. One Docker
Desktop start attempt failed according to the user; no further starts or
system repair are authorized by this experiment. Separate-container/host and
packet-level impairment remain an explicit unmet deployment extension.

The feasible fallback uses a provider process, production controller process,
two TCP byte-stream proxy processes, and a runner on Windows loopback. It adds
real connection closure, withheld replies and measured stream delay to the
old application-layer 503/sleep fixtures; it is not a container experiment,
packet-loss model, multi-host study or physical substrate execution. The
provider is an independent durable effect counter around an E1 edge twin.
The proxies forward HTTP bytes and can close sockets or delay forwarding;
they do not fabricate an HTTP fault response. Rules are armed only after
startup. Each trial uses new process/registry/effect state and fresh ports.

Seven conditions, three fresh repetitions each, are deterministic: baseline;
50 ms delay before forwarding invoke; all provider connections partitioned
after startup; lost invoke reply after the provider response; lost controller
reply after execution; provider termination before request; controller restart
after a lost provider reply. Each includes a same-key retry. Unknown outcome
cases also include a new-key reuse attempt before reconciliation. No random
loss process or seed-based statistical claim is made; all conditions are
fixed, so a random seed would be misleading. Proxy event logs retain requested
and measured delay, forwarded/withheld bytes and connection closure. Clocks
are UTC for trace correlation, monotonic for within-process durations; there
is no cross-host clock claim. Only processes started by this runner are stopped.

Expected baseline/delay and lost-client-reply effects: one start/commit despite
same-controller same-key retry. Provider interruption/partition: no effect and
failed request; no successful new-key reuse while state is unknown. Lost
provider reply: one effect, failed result, same-key no duplicate, and new-key
blocked while quarantined. The lease/idempotency/lifecycle stores are not
persisted; audit/span files do not restore them. Restart has no unfinished-task
startup reconciliation. The restart case is a negative control: a repeated
request may cause a second durable provider effect after restarting the
controller, which must be reported as an unsupported guarantee, not hidden
by a new architecture or counted as a safety success. Preserve exact outcomes
and distinguish detector/expectation conformance from restart safety.

## Analysis and handoff

Offline verification checks archive inventory/hashes, frozen inputs,
denominators, independently specified selection expectations, effect ledgers,
paired timing summaries and transport observations. Generated figures derive
only from archived observations. Raw directories stay local until the R5
clean-checkout reproduction/release step; an ignored directory is not public
evidence. No manuscript change, commit, push or resubmission is part of R4.
