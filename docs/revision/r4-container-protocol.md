# R4 container transport protocol

This extension repeats the seven R4 TCP conditions in separate Linux
containers after Docker Desktop was repaired and updated on 10 October 2026.
It is a new campaign; the earlier Windows loopback archive is unchanged.
The experiment tests the existing HTTP controller and an effect-observed E1
edge twin, not MCP over a network, CL1, or physical-substrate behavior.

## Deployment and frozen inputs

Each trial has four fresh containers: provider, provider proxy, controller,
and client proxy. They share one fresh, private Docker bridge network. The
Windows runner reaches only the client proxy through a dynamically allocated
port published on 127.0.0.1. The other services are reached by container DNS
names on that network. All containers remain on the same Docker Desktop
Linux VM and physical computer. Container separation is not a second host or
independent environment.

The network is a user-defined bridge, not Docker's internal-network mode,
which did not allocate a host port in development. Its network configuration
does not block external egress. Experiment requests target only the trial's
services; no internet service or production endpoint is called during trials.

The image copies a self-contained source snapshot, including remote services,
twins, deployment configuration and testbed modules. No working checkout,
credentials, Docker socket, or private user directory is mounted. The only
bind mounts are newly created trial evidence directories. Containers have no
additional capabilities, use a read-only root filesystem and a bounded /tmp
tmpfs, and are not privileged. They use the production controller unchanged.
Per-container json-file logging retains stdout/stderr without changing Docker's
global logging settings. Proxy environment variables are explicitly cleared.
The E1 effect observer's JSON writer has the same atomic serialization as
before, but no longer imports the CL SDK solely to write files.

Before the first confirmatory request, freeze this protocol, task and condition
specification, source ZIP, Dockerfile and direct dependency pins, host and
Docker metadata, actual Linux/Python/package metadata, pip's installation
report with distribution hashes, the built image ID, its source-content
check, and an exported image TAR. Dependency resolution and development
checks precede that freeze. The image ID, not a mutable tag, identifies every
trial container. Retain build logs. Use a new output directory and never
overwrite or replace failed observations. Development runs are not counted.

## Conditions and requests

Use exactly three fresh trials per condition, in the following order, for
21 trials. The fixed classification task targets remote-edge-backend,
disables fallback and has the same client, task and idempotency key in every
within-trial retry. All provider and controller state is fresh between trials.

| Condition | Impairment | Expected durable provider commits per trial |
| --- | --- | ---: |
| baseline | None | 1 |
| delay | Wait 50 ms before forwarding the invoke request | 1 |
| partition | Close all provider-proxy requests without forwarding after startup | 0 |
| lost_provider_reply | Forward invoke and read its response, then close without delivering that response once | 1 |
| lost_client_reply | Read the completed controller response, then close without delivering it once | 1 |
| provider_interrupt | Stop the provider container before the first execute request | 0 |
| controller_restart | Lose the provider reply, retry and probe a new key, then restart only the controller container and repeat the original key | 2 |

The runner makes first and same-key requests in all conditions. Partition,
lost provider reply, provider interruption and controller restart also probe
a new key before any restart. The restart condition adds one post-restart
same-key request. There are 57 execute attempts in total. There is one
outstanding execute attempt at a time. Readiness probes precede fault arming
and are not execute attempts.

Proxies impose actual TCP byte-stream delay, connection closure and withheld
replies between distinct containers. They never synthesize an HTTP fault
response. This is not packet-level netem, random packet loss or a real WAN
partition. A deterministic partition rule closes the provider-facing stream;
it does not disconnect the Docker network. Record requested and measured
delay, forwarded/received/withheld bytes and closure events. No random seed
or statistical independent-environment claim applies to these fixed cases.

## Recovery expectations and verification

Baseline and delay must succeed; the retry must replay with no second effect.
Lost client reply must replay the completed result in the same controller.
Lost provider reply must leave UNREACHABLE state; same-key replay must not
add an effect and a new key must be explicitly refused. Before-invocation
partition/interruption must cause no effect; retain the actual HTTP status
and body. A generic HTTP 500 is not evidence of explicit quarantine.

Controller lease, lifecycle and idempotency stores remain in memory. A
container restart runs a fresh controller; persisted trace files do not
restore that state. The provider stays running with the same durable counter.
The expected second commit after restart is a negative control demonstrating
an unsupported guarantee, not a safety success. Do not add durable storage or
startup reconciliation as part of this experiment.

Archive each exact request and response, HTTP status or missing response,
provider hash-chained effects and counter, both proxy ledgers, controller
spans, container stdout/stderr, startup/final/restarted inspect records,
network topology, owned-resource cleanup records, and any harness failures.
Manual restart is verified by unchanged container ID, changed process PID and
start timestamp, and a retained provider start timestamp. Docker's archived
RestartCount is not treated as a count of manual restart commands.
UTC correlates traces and monotonic clocks measure within-process durations;
there is no cross-host clock claim. Distinguish observation/expectation
conformance from safety. Confirm distinct container IDs and IPs, the same
frozen image, restart count, retained provider identity, and no overlap or
unfinished effect. Cleanup removes only exact IDs created by the runner and
matching its ownership label; bind-mounted evidence and the evaluation image
are retained. Never prune Docker or remove user containers, images or volumes.

Offline verification must check inventories, hashes, freeze/image/source
bindings, the 21-trial/57-request denominator, effect chains, condition
outcomes, impairment observations, restart evidence and cleanup. No failures
are discarded. The journal/arXiv manuscripts, public artifact release,
human oracle approval and full reviewer response remain later work.
