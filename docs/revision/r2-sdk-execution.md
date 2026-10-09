# R2 continuous MCP and official SDK execution

R2 connects an admitted BioPattern Gate MCP task to a new official Cortical
Labs SDK Simulator execution. The first implementation checkpoint covers the
execution bridge and native result validation. It does not enable Cortical
Cloud or physical CL1 execution, and it does not replace the frozen legacy
E3 traces or the earlier dry-run agent campaign.

## First checkpoint protocol

The server accepts only the existing `pattern_gate_v1` preset, its exact task
metadata, and the frozen configuration, decoder, and application-core hashes.
The bridge starts `python -m cl.app.run` in a new controller-assigned attempt
directory. Its SDK run identifier is also controller-assigned; neither
identifier is provider attestation. The application package must contain the
same frozen core as the repository. The SDK and application both retain the
simulator-only guard. No physical parameters become MCP inputs.

During `VALIDATING`, a separate verifier reads native HDF5 stimulation and
spike tables. It derives observation windows from native trial markers,
acknowledged stimulation times, and the frozen timing configuration; checks
the channel mapping and sham trials; recomputes features, decoder decisions,
and decision commitments; and compares them with the online JSON and recorded
feature/decision streams. All expected trials and a complete terminal state
are required. A sanitized successful summary is published only after these
checks. A partial recording cannot pass as a complete result.

The success bundle binds the authenticated principal, MCP request, task,
resource, lease, attempt, SDK run, source/configuration/decoder hashes,
recording checksum, native validation report, sanitized result, lifecycle,
and hash-chained audit. Counts are measured from the new transcript and audit,
not copied from the old eight-call trace. Checksums provide integrity, not
hardware attestation or protection against a compromised evidence producer.

## Development checks

Before using a run as confirmatory paper evidence, exercise a fresh positive
control through the constrained MCP surface and check at least:

- invalid task/configuration binding rejected before launch;
- a failed SDK process launch and a nonzero SDK exit;
- a wrong run identifier, partial recording, altered native spike data, or
  changed checksum rejected by validation;
- no extra start when a terminal `run_assay` is repeated, with the existing
  status/result tools used to recover a lost reply;
- an active or unresolved subprocess never reported as ready, and reset
  refused until termination is observed.

These are development checks for this checkpoint, not an LLM campaign or
measurements of biological performance. The final R2 recovery experiment
protocol must be frozen separately before confirmatory runs.

## Remaining R2 work

Cooperative cancellation through the official SDK application, dedicated
abort/timeout/lost-reply experiment bundles, and independent cross-case
recovery analysis remain required before R2 is complete. Until a cooperative
abort is implemented, an active subprocess has no confirmed provider abort:
timeouts fail closed and quarantine the resource. The local lease may be
released by the controller, but the lifecycle stays unavailable while the
process is active. A successful SDK exit establishes completion for this
local simulator path. A nonzero exit does not establish child-process cleanup
and remains quarantined until a provider reconciliation path is implemented.
Failure to launch any child can be finalized immediately. This is process-local
coordination, not durable distributed cancellation.

The paper and cumulative yellow markup will receive new results through R5;
starting this bridge does not itself justify changing manuscript result claims.

## Verified development checkpoint

The 9 October 2026 development bundle
`.cp2n2/r2-sdk-development-20261009-02` contains a fresh execution attempt
`f9fd35a1-ea4d-4c4f-a9d6-25cbbd767bf9`. A separate offline verification
recomputed all 14 trials from 24 native stimulation events and 60 native spikes.
The measured transcript contains eight MCP surface calls and 16 valid audit
events. The lifecycle ends in `READY` with no lease. The deterministic pipeline
assertion accuracy is 1.0; it is not a biological classification result.

The deterministic non-LLM client invokes the constrained MCP control surface
in process. This checkpoint does not test network transport or a hosted MCP
endpoint. Its source, tests and protocol are versioned; the generated bundle
is retained locally under the ignored `.cp2n2` directory pending R5 packaging.
The 18 new development tests cover the success path, artifact/identity
substitution, independent native-spike manipulation, simulator guard, launch
failure, nonzero exit quarantine, validation failure, lost-reply retrieval,
duplicate rejection and active-process timeout quarantine.

With the Python virtual environment active, create a new run and then verify it:

```powershell
python scripts\run_biopattern_gate_sdk_e3.py --output .cp2n2\r2-sdk-my-run
python scripts\run_biopattern_gate_sdk_e3.py --verify .cp2n2\r2-sdk-my-run
```

The first command requires an unused output directory. The second command
reads the bundle and does not start another SDK execution.
