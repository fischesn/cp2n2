# AP3: paired overhead and measured CPU context

This is a new predeclared synthetic, single-host campaign. Frozen R4 sources,
raw timings, manifests and verification receipts are immutable. No physical PNN,
external LLM/provider, second physical host, distributed network path or p99
guarantee is implied.

## Before scored measurement

The functional changes from AP1/AP2 and evaluation code must be frozen by the
coordinating task after focused and full regression tests. No concurrent scored
campaign runs on this host. The freeze saves the complete source snapshot,
per-file SHA-256 inventory, working-tree status, base Git commit, protocol,
specification, dependency versions, CPU counts and memory. A dirty base commit
is not presented as the identity of uncommitted new sources: the saved source
bytes and hashes are authoritative.

## Fixed experiment

- Four configurations: direct versus controlled EdgeAdapter execution with
  1, 3 and 12 registered resources; direct control-surface versus official MCP
  in-memory discovery with 3 resources.
- Two conditions: `idle_baseline` (no intentionally added load, not a claim of
  an otherwise idle laptop) and `bounded_cpu_load` (one owned Python worker,
  a declared 60% duty fraction in 20 ms periods, no CPU affinity).
- Ten fresh-registry trials per configuration per condition; 20 warmup and
  200 measured calls per path per trial. Total: 80 fresh-registry trials,
  32,000 measured calls, 3,200 warmup calls.
- Trials alternate idle/load versus load/idle order; both path orders also
  alternate by trial index. Conditions remain adjacent within each trial.
- One outstanding synchronous operation. Execution receives the same fixed
  payload and reset/recalibration policy; these housekeeping operations are
  outside each operation timer but included in measured block throughput.
- Worker readiness is bound to its owned PID; the worker settles for 0.5 s
  before operations start. No load worker exists in idle-baseline conditions.

## Timing and CPU observation

Operation wall time uses `perf_counter_ns`. The benchmark process CPU time,
actual system utilization and owned worker utilization use already-installed
`psutil`. Raw process/system CPU endpoints are captured outside timed calls.
The same asynchronous 20 ms sampler is present under both conditions; its
monitoring overhead is therefore part of the environment, not claimed absent.

System utilization is percentage across logical CPUs. Process utilization is
percentage of one logical CPU and may exceed 100% for a multithreaded process.
Short blocks can produce CPU-clock-resolution artifacts or an unavailable
system percentage; raw CPU times and intervals are retained. Declared worker
duty fraction is not substituted for measured utilization and does not imply
60% utilization of the whole machine. No achieved load threshold is used to
select or discard runs.

Warmup and measurement failures are retained with their reasons and no retry.
All measured wall times, including failed operations, enter timing summaries;
success counts accompany them. Invoke/non-invoke decomposition uses only
successful operations with recorded invocation time and explicitly discloses
that narrower scope. Discovery retains tool responses and paired audit events.

## Safe cleanup

Worker stop is cooperative first. A timeout may terminate/kill only the actual
worker process object created by this trial, never a process discovered by
name or PID enumeration. Every owned PID, readiness signal, stop method and
exit code is archived. Forced stops remain visible and cause overall campaign
verification to fail; monitoring errors are retained and do the same.

## Analysis, integrity and interpretation

Each block contributes a median and p95. Summaries report the median of trial
medians and the median of trial p95 values, with 2,000 bootstrap resamples of
fresh-registry trial summaries (fixed seed 73401), never pooled dependent calls.
The median-of-trial-p95 CI is not a population p95 or p99 guarantee. Paired path
differences compare trial medians collected under the same load condition.

All artifacts have a SHA-256 manifest. Offline verification checks input
binding, source inventory, trial/configuration/order/denominators, raw timings,
CPU endpoint-derived values, cleanup, MCP audit binding and complete report
recomputation. A cryptographic match demonstrates archive consistency, not an
independent execution or physical truth. Generated `report.md` and
`verification.json` report the entire declared experiment; negative observations
are not removed.

The separate offline R4 report verifies the original immutable archive and
copies its already-existing median and median-of-trial-p95 intervals into a
new directory, with source manifest/freeze/report hashes. It performs no new
measurement and never writes into the source archive.

## Commands

Activate the existing venv or invoke `.venv\Scripts\python.exe` explicitly.

```powershell
python -B scripts/run_revision_ap3_overhead.py --report-r4 .cp2n2/r4-overhead-confirmatory-20261010-01 --output .cp2n2/ap3-r4-offline-20261014-01
python -B scripts/run_revision_ap3_overhead.py --development --output .cp2n2/ap3-overhead-development-20261014-01
# Only after functional freeze and all other tests/campaigns have stopped:
python -B scripts/run_revision_ap3_overhead.py --output .cp2n2/ap3-overhead-confirmatory-20261014-01
python -B scripts/run_revision_ap3_overhead.py --verify .cp2n2/ap3-overhead-confirmatory-20261014-01
```

Development mode is explicitly labeled, uses 2 trials/4 observations/2 warmups,
and never serves as the scored experiment. Existing output directories are not
overwritten.
