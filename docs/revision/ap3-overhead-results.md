# AP3 overhead and CPU measurements

14 October 2026. The [predeclared protocol](ap3-overhead-protocol.md) was frozen
before this new confirmatory run. All 32,000 measured operations and 3,200
warmups succeeded across 80 fresh-registry trials. The offline verifier passed;
no monitoring errors or forced worker stops occurred.

The [coordinated source freeze](ap1-ap3-source-freeze.json) identifies the
uncommitted evaluated source by normalized per-file SHA-256 hashes. All three
AP archives contain the same 290 source files without mismatches or duplicates;
see the [evidence index](ap1-ap3-evidence-index.json). The base Git commit is not
the identity of these new sources.

Execution targets `bench-0` explicitly. The 1/3/12 configurations vary registered
resources, not a full automatic selector search over all providers. These
measurements therefore do not establish general selector scaling. Discovery
covers three resources through both the direct control surface and official
in-memory MCP sessions. Neither path is a physical PNN or distributed deployment.

The Windows host exposes eight logical CPUs, with Python 3.14.4, psutil 7.2.2,
NumPy 2.5.1, MCP 1.28.1 and Pydantic 2.13.4. The extra load is one duty-cycled
worker; its measured whole-condition utilization is about 29–37% of one core,
not the declared 60% duty setting and not whole-machine saturation. Short direct
blocks are smaller than CPU-clock increments in several trials: their 0% or
above-100% process readings are resolution artifacts, not reliable per-block
utilization estimates. Raw CPU endpoints and asynchronous samples are retained.

Local raw archive: `.cp2n2/ap3-overhead-confirmatory-20261014-01`.

## New confirmatory observations

Synthetic execution and in-memory MCP discovery on one physical host.

Confidence intervals resample fresh-registry trial summaries. The p95 interval is for the median of trial p95 values; it is not a population tail guarantee.

| Group | Condition | Path | Median-of-trial-medians [95% CI], ms | Median-of-trial-p95 [95% CI], ms | Successes / measured |
| --- | --- | --- | --- | --- | --- |
| execution-1 | idle_baseline | direct | 0.0241 [0.0231, 0.0269] | 0.0306 [0.0277, 0.0652] | 2000 / 2000 |
| execution-1 | idle_baseline | controlled | 4.1249 [3.4466, 5.1604] | 8.6729 [6.7082, 12.2216] | 2000 / 2000 |
| execution-1 | bounded_cpu_load | direct | 0.0272 [0.0256, 0.0385] | 0.0655 [0.0419, 0.1099] | 2000 / 2000 |
| execution-1 | bounded_cpu_load | controlled | 4.5573 [3.9135, 5.2202] | 10.6144 [7.7562, 25.7200] | 2000 / 2000 |
| execution-3 | idle_baseline | direct | 0.0253 [0.0232, 0.0264] | 0.0302 [0.0257, 0.0405] | 2000 / 2000 |
| execution-3 | idle_baseline | controlled | 4.1201 [3.7664, 4.4097] | 6.5574 [6.0567, 8.1416] | 2000 / 2000 |
| execution-3 | bounded_cpu_load | direct | 0.0255 [0.0235, 0.0268] | 0.0349 [0.0290, 0.0512] | 2000 / 2000 |
| execution-3 | bounded_cpu_load | controlled | 4.0816 [3.9223, 4.2163] | 6.8353 [6.3490, 7.1970] | 2000 / 2000 |
| execution-12 | idle_baseline | direct | 0.0232 [0.0223, 0.0259] | 0.0355 [0.0322, 0.0405] | 2000 / 2000 |
| execution-12 | idle_baseline | controlled | 3.4311 [3.0903, 3.8280] | 6.8597 [6.1034, 7.8575] | 2000 / 2000 |
| execution-12 | bounded_cpu_load | direct | 0.0248 [0.0231, 0.0273] | 0.0326 [0.0285, 0.0414] | 2000 / 2000 |
| execution-12 | bounded_cpu_load | controlled | 3.9976 [3.8660, 4.6422] | 7.3959 [6.6907, 15.1519] | 2000 / 2000 |
| discovery-3 | idle_baseline | direct_surface | 3.9678 [3.8979, 5.2965] | 6.2396 [5.3519, 12.7103] | 2000 / 2000 |
| discovery-3 | idle_baseline | mcp_memory | 14.4516 [13.6333, 16.5716] | 19.3690 [16.5218, 29.9824] | 2000 / 2000 |
| discovery-3 | bounded_cpu_load | direct_surface | 4.2036 [4.0178, 5.1574] | 6.4166 [5.6101, 17.8203] | 2000 / 2000 |
| discovery-3 | bounded_cpu_load | mcp_memory | 14.5564 [13.9245, 16.3034] | 18.1398 [17.2531, 34.3055] | 2000 / 2000 |

### Observed CPU context

| Group | Condition | Path | Benchmark CPU seconds / block (median) | Benchmark CPU %, one-core basis (median) | System CPU % (median) | Load-worker CPU %, one-core basis (median) |
| --- | --- | --- | --- | --- | --- | --- |
| execution-1 | idle_baseline | direct | 0.0000 | 0.0000 | 33.8889 | unavailable / not applicable |
| execution-1 | idle_baseline | controlled | 0.8672 | 80.1377 | 37.0991 | unavailable / not applicable |
| execution-1 | bounded_cpu_load | direct | 0.0156 | 133.8081 | 50.0000 | 0.0000 |
| execution-1 | bounded_cpu_load | controlled | 0.9062 | 79.7589 | 39.0580 | 27.3534 |
| execution-3 | idle_baseline | direct | 0.0078 | 80.2443 | 33.3333 | unavailable / not applicable |
| execution-3 | idle_baseline | controlled | 0.8359 | 89.5178 | 40.3886 | unavailable / not applicable |
| execution-3 | bounded_cpu_load | direct | 0.0156 | 151.4104 | 28.5714 | 0.0000 |
| execution-3 | bounded_cpu_load | controlled | 0.7969 | 86.1745 | 37.3981 | 36.8988 |
| execution-12 | idle_baseline | direct | 0.0156 | 201.5559 | 46.4286 | unavailable / not applicable |
| execution-12 | idle_baseline | controlled | 0.6562 | 79.6615 | 33.3387 | unavailable / not applicable |
| execution-12 | bounded_cpu_load | direct | 0.0000 | 0.0000 | 20.0000 | 0.0000 |
| execution-12 | bounded_cpu_load | controlled | 0.7578 | 83.9861 | 37.8087 | 30.8403 |
| discovery-3 | idle_baseline | direct_surface | 0.6719 | 69.5945 | 41.4262 | unavailable / not applicable |
| discovery-3 | idle_baseline | mcp_memory | 2.4688 | 80.1989 | 38.0386 | unavailable / not applicable |
| discovery-3 | bounded_cpu_load | direct_surface | 0.6562 | 72.8029 | 45.9793 | 40.4308 |
| discovery-3 | bounded_cpu_load | mcp_memory | 2.5078 | 81.7438 | 41.7956 | 30.8569 |

Condition-level worker utilization (one-core basis, including settle/warmups/measurements):
- execution-1: 28.7774% median across trials.
- execution-3: 36.7079% median across trials.
- execution-12: 31.2447% median across trials.
- discovery-3: 30.2670% median across trials.

Per-block process CPU time and actual system/worker utilization are retained in verification.json and raw trial CPU endpoints. Idle baseline does not assert an otherwise idle host.

Mode: confirmatory. Measured operations: 32000; warmups: 3200.
All operations succeeded: True. Overall verified: True.


## Interpretation and reuse

Controlled execution medians in this run range from 3.43 to 4.12 ms without
intentional load and from 4.00 to 4.56 ms with the owned worker. MCP discovery
medians are 14.45 and 14.56 ms respectively. Several intervals overlap; these
observations do not establish a universal slowdown, a monotonic resource-count
trend or a tail guarantee. Retain both conditions and their actual CPU context.

The original R4 table below is an offline extraction of intervals already
present in the immutable archive, not a new measurement. Do not pool its timings
with the modified-source AP3 observations or attribute old measurements to the
new validation/provider-error implementation.

# Previously archived R4 intervals (offline report)

bootstrap CI for median of fresh-trial p95 values; not population tail guarantee

No new measurements; source archive verified before reading. Source files were not changed.

| Group | Path | Median [95% CI], ms | Median-of-trial-p95 [95% CI], ms |
| --- | --- | --- | --- |
| execution-1 | direct | 0.0219 [0.0217, 0.0233] | 0.0262 [0.0245, 0.0382] |
| execution-1 | controlled | 1.8464 [1.7685, 2.0368] | 3.3496 [3.0630, 3.7171] |
| execution-3 | direct | 0.0226 [0.0216, 0.0233] | 0.0252 [0.0244, 0.0299] |
| execution-3 | controlled | 2.4713 [2.2187, 2.6330] | 3.8507 [3.6612, 4.5301] |
| execution-12 | direct | 0.0222 [0.0214, 0.0234] | 0.0290 [0.0261, 0.0349] |
| execution-12 | controlled | 3.4244 [3.2926, 3.6141] | 5.7961 [5.1822, 5.9568] |
| discovery-3 | direct_surface | 2.0088 [1.9983, 2.1138] | 2.5774 [2.4691, 2.8272] |
| discovery-3 | mcp_memory | 9.9972 [9.6525, 10.6344] | 12.4133 [11.5684, 12.8881] |
