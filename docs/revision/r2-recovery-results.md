# R2 SDK recovery results

**Status:** COMPLETE within the local Windows SDK Simulator scope, 9 October 2026.

R2 now connects an admitted MCP assay to a fresh official SDK execution,
independently validates native results, and checks termination before resource
reuse. The frozen [recovery protocol](r2-recovery-protocol.md) passed all
18 case executions: nine conditions, each repeated twice. A separate offline
verification passed without starting another SDK run. These are E3 software
results, not biological performance, LLM behavior or physical-safety evidence.

## Observed outcomes

Counts below are **per execution**, identical in both repetitions. The two
columns headed MCP and audit count calls and events, not successful assays.

| Case | Verified / attempted | MCP | Audit | SDK starts | Observation |
|---|---:|---:|---:|---:|---|
| success | 2 / 2 | 6 | 12 | 1 | Complete native result independently reconstructed and delivered |
| invalid_configuration | 2 / 2 | 4 | 8 | 0 | Extra configuration override rejected before execution |
| launch_failure | 2 / 2 | 6 | 12 | 0 | Missing host executable produces a typed failure, not a result |
| cooperative_abort | 2 / 2 | 7 | 14 | 1 | Owner cancellation retains an aborted native partial recording |
| sdk_crash | 2 / 2 | 6 | 12 | 1 | Parent crash retains unfinalized evidence; owned descendants are forcibly cleaned up |
| validation_failure | 2 / 2 | 6 | 12 | 1 | Altered native spike rejected during VALIDATING; no successful summary |
| lost_reply_duplicate | 2 / 2 | 7 | 14 | 1 | Duplicate terminal run rejected; original stored result retrieved unchanged |
| timeout_confirmed | 2 / 2 | 6 | 12 | 1 | Caller receives EXECUTION_STATUS_UNKNOWN; later confirmed cleanup permits reuse |
| timeout_unconfirmed | 2 / 2 | 7 | 14 | 1 | Active SDK observed in quarantine; reservation denied; real cleanup and explicit reconciliation restore READY |

Totals are **18 / 18 verified conditions, 110 MCP calls, 220 audit events and
14 SDK starts**. Only the success and lost-reply cases deliver successful
assay summaries: four such summaries across the two repetitions. Passing a
negative case means that its specified rejection/recovery occurred, not that
the failed assay succeeded. All 18 final states are READY with no lease; the
unconfirmed-timeout case additionally records the intermediate UNREACHABLE state.

Both ordinary success runs contain 14 trials, 24 native stimulation events
and 60 native spikes. Their deterministic pipeline assertion accuracy is 1.0,
not a biological classification score. In both repetitions, cooperative abort
and both timeout cases retain two decisions, two stimulation events and five
spikes in a cleanly aborted recording. The crash recordings contain those same
partial counts but remain explicitly **unfinalized**; they were not repaired
or relabelled complete. OS accounting confirms zero active owned processes
after all 14 started executions. Forced process-job cleanup occurs in the two
deliberate crash cases, not in the cooperative-abort cases.

## Retained evidence and versions

The complete local campaign is retained in
`.cp2n2/r2-recovery-confirmatory-20261009-01`. Each case contains the exact
protocol, MCP arguments/responses, hash-chained audit, lifecycle history,
attempt configuration and identities, SDK log, native recording where one
exists, termination observation, run record and checksum manifest. The root
contains the pre-run source snapshot, input hashes, empty failure register and
verification report. Development runs under separate `r2-recovery-dev-*` and
`r2-recovery-development-*` paths are excluded from these denominators.

The retained runtime versions are Python 3.14.4 and cl-sdk 1.0.0. The CL
application package is version 0.3.0. The canonical BioPattern Gate core,
technical configuration and decoder remain unchanged.

| Input or report | SHA-256 |
|---|---|
| Exact protocol copy | `c4cdd2965ac442848641143eea3c2bfa7d030fbe7b8199ace0b037884b7c69e5` |
| Source snapshot ZIP | `93b60aedc905c08b1e29cb49e78775d62e357c5ea30d0e130cb603be0477da43` |
| Campaign design JSON | `daeadb67410a05ecf2c4a61c425b14ed83be787c0e0c689a2341b2301a02407e` |
| Verification JSON | `e500d7c5e34bb0a8db4fef439051fd3eb0cbb62a9d55b2564ce3a6cf9b7fc8f5` |
| Canonical application core | `fca1d699d09a57816ce7fefe073170c4a09e146155379bec0339d4119a26bbf7` |
| SDK application shell and bundled core | `28c64820a3e72cea207f0014b4daa08ab4f440c2e7fb95eac2c92e3458790688` |
| CL application package ZIP | `ffb9ef96a9cbbc3883ccd0c7e98eed4d83ff885cd0932efa33b7199fe1f28339` |

The software, protocol and result summary are versioned. Native campaign
files remain in the ignored local evidence directory; public, sanitized
artifact publication and manuscript/reviewer-response integration belong to
R5. The original submission, released baseline and legacy traces are unchanged.

## Reproduce and verify

On Windows, with the repository's Python environment active:

```powershell
python scripts\run_r2_sdk_recovery.py --output .cp2n2\r2-recovery-new-run
python scripts\run_r2_sdk_recovery.py --verify .cp2n2\r2-recovery-new-run
```

The first command requires a new directory and runs all 18 conditions. The
second reads existing evidence only. It checks inventories and hashes, audit
request pairs, principal/task/lease/attempt identities, exact configuration,
source bindings against the archived snapshot, lifecycle versions, native
complete/partial status, result consistency, start counts and quarantine.
It recomputes complete decisions from native events and requires the altered
native negative control to fail validation. This is not provider attestation;
a compromised controller can forge its own unsigned archive.

The full regression suite passed **179 tests**, with two external dependency
deprecation warnings. CL application structure/import/configuration validation
and packaging also passed. Concurrent-finalizer tests confirm that the shared
adapter lock prevents a second abort and that a late old finalizer leaves a
newer lease untouched.

## Limits and next step

The deterministic client calls the real constrained MCP control surface
in process; this is not a network-loss experiment. The lost-reply condition
disregards a returned response in the harness. Faults are deliberate local
software injections, including the temporary unconfirmed-abort test double.
Two repetitions establish bounded conformance, not failure probabilities,
latency-tail estimates or durable coordination across controller restart.

The termination guarantee currently uses Windows-owned process jobs. The new
bridge refuses SDK launch when containment is unsupported or cannot be
established; it does not imply portable cancellation or a CL1 emergency stop.
The legacy application core and runners remain unchanged. Cortical Cloud and
physical CL1 execution remain gated separately.

**Next package: R3.** Build independently observed permitted/forbidden backend
effects and a bounded executing-agent campaign. R5 will later integrate R2–R4
into both manuscript views and the comprehensive reviewer response, preserving
the cumulative yellow change marks. Neither paper source changed in R2.
