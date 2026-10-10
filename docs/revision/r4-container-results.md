# R4 container transport results

The separate-container extension is complete in its single-host scope.
Seven conditions with three fresh trials each produced 57 execute attempts
and 18 durable provider commits. All 21 predeclared effect patterns occurred,
including duplicate execution in every controller-restart negative control.
An expectation match is not a safety pass.

## Observed effects

| Condition | Commits in each of three trials | Observed behavior |
| --- | ---: | --- |
| Baseline | 1 | Execution succeeds; same-key retry replays without another effect |
| 50 ms invoke delay | 1 | Execution and replay succeed; measured forwarding delays are 50.143, 50.298 and 50.362 ms |
| Provider stream partition | 0 | Three attempts per trial receive HTTP 500 before invocation |
| Lost provider reply | 1 | UNREACHABLE state; same-key failed-result replay adds no effect; new key receives POLICY_DENIED |
| Lost client reply | 1 | Same-controller retry retrieves the completed result without a new effect |
| Provider container stopped before request | 0 | Three attempts per trial receive HTTP 500 before invocation |
| Controller container restarted after lost provider reply | 2 | State is lost; retry with the original key executes again |

There are 18 verified starts/commits, no overlaps or unfinished effects, and
no effect attributed to a new-key probe. Effect identities match the frozen
task, client, key and backend. The six partition/interruption trials contain
18 HTTP 500 responses. Their actual response bodies are retained; they must
not be described as structured CP²N² quarantine denials. Lost-provider-reply
cases, by contrast, retain explicit POLICY_DENIED responses to the new key.

All three controller restarts preserve the container ID but change its process
PID and start timestamp. The provider remains the same running instance.
The second commit is therefore not a new trial or replacement provider: it
demonstrates the existing in-memory idempotency/lifecycle limitation. Trace
files survive, but do not reconstruct those stores. No durable recovery
implementation was added.

## Deployment and environment

Each trial creates four separate containers and one user-defined bridge
network. Only the client proxy publishes a port, restricted to Windows
loopback. Provider and controller traffic crosses container network endpoints
through the two byte-stream proxies. Delay, withheld replies and connection
closure act on actual HTTP/TCP traffic; no proxy fabricates an HTTP 503.
The partition rule closes streams rather than disconnecting the Docker network.

The experiment uses Docker Desktop 4.94.0, Engine 29.8.2, Linux kernel
5.15.167.4-microsoft-standard-WSL2, Python 3.12.11, NumPy 2.5.1, SciPy 1.18.0
and Pydantic 2.13.4. The Windows runner uses the existing project environment.
All containers run on the same Linux VM and physical Windows computer. This
is neither a second independently deployed host nor packet-level impairment,
MCP-over-network timing, CL SDK execution or a physical-substrate experiment.
The provider is an effect-observed E1 edge twin.

Trial containers are nonprivileged, drop additional capabilities, use a
read-only root filesystem and mount only their new evidence directories.
The source is copied into the image; the checkout and Docker socket are not
mounted. The network permits external egress, but experiment service requests
target the trial services. No LLM, provider cloud or physical-device call is
made. Cleanup removed all 84 confirmatory containers and 21 trial networks by
exact ID and ownership label. No user container, image or volume was removed.
The evaluation images and evidence remain available.

## Frozen archive and verification

The [protocol](r4-container-protocol.md) was frozen before confirmatory
requests. The [artifact index](../../evaluation/fixtures/r4-container-confirmatory-20261010.json)
binds the exact local archive, inputs, image and final inventory:

`.cp2n2/r4-container-confirmatory-20261010-01`

Its 275-file source ZIP includes remote services, twins, demos and testbed
configuration in addition to the existing source folders. Every image source
file was compared with that ZIP before measurement. The archive retains the
112,099,328-byte image TAR, installation report with package distribution
hashes, host/container metadata, requests and responses, effect ledgers and
counter, proxy events, controller spans, inspect records, logs and cleanup.
The final 793-file inventory and all frozen bindings verify offline.

With the project virtual environment active:

```powershell
python scripts/run_r4_container_evaluation.py --verify .cp2n2/r4-container-confirmatory-20261010-01
python scripts/run_r4_container_evaluation.py --output .cp2n2/r4-container-new
```

Verification does not need a running Docker engine. New measurement requires
Docker and a locally installed `python:3.12-slim` base image; its actual immutable
repository digest is captured and used for the build. Use a new output name.
Exact clean-checkout reproduction must use the archived source, environment
and image, rather than assume the current checkout or base tag is identical.
The raw archive remains ignored and local, not a public release asset.

Three development archives remain separate. The first exposed a missing
SciPy dependency; the second showed that the internal-network setting did not
allocate the requested host port; the third exercised all seven conditions
successfully. These observations were not counted among the 21 trials.

## Packaging correction

The initial archive exporter excluded every file named manifest.json, rather
than only the root inventory. This omitted four unchanged source manifests
inside the extracted build context, and the strict inventory check rejected
the package. The exporter now excludes only the root inventory.

The archive's packaging-repair directory retains the original inventory,
the corrected r4_common.py and a repair record. Before repackaging, every
previously listed file and frozen input was hash-checked; the four omissions
were checked against the source ZIP. No measured file, frozen input or runtime
image changed. The recomputed analysis report remains byte-identical. No
measurement was rerun. Reproducing the original export step requires this
recorded inventory correction; the original frozen runtime/source bytes remain
available for inspection.

## Remaining work

The complete software suite passes 286 tests, with the two previously known
dependency deprecation warnings. R4's container deployment gate is satisfied.
Human approval of the twelve selector-oracle sample cases still remains open.
Independent clean-checkout reproduction, public raw-archive release, manuscript
integration and the full reviewer response are R5 work. The journal and arXiv
sources are unchanged. No commit, push or release was made for this extension.
