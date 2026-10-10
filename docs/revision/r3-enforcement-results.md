# R3 local enforcement and agent-pipeline results

Status: R3 complete in the bounded local software/E3 scope, 10 October 2026.
The author-approved replacement `qwen3.8-27b` passed a separate capability check
and completed the frozen [v2 live campaign](r3-agent-qwen-results.md): 24/32 exact
planner matches, 6/8 permitted executions, two active stale-health blocks,
zero forbidden effects and 32/32 reconciled states. Planner failures are retained,
not hidden or repaired. Journal
and arXiv sources have not been changed. Paper integration and the comprehensive
reviewer response remain mandatory R5 outputs.

## Direct enforcement

The separately frozen [direct protocol](r3-enforcement-protocol.md) and JSON oracle
define 42 cases, repeated twice. All **80 ordinary case instances** matched their
expected effects and delivery outcomes. All **four detector-control instances**
identified their deliberately introduced faults. An offline re-verification also
passed without invoking a backend.

| Measurement | Ordinary cases only |
|---|---:|
| Verified case instances | 80 / 80 |
| Independently logged backend starts | 24 |
| Durable backend commits | 22 |
| Successful, checked deliveries | 14 |
| Unauthorized/duplicate commits or overlapping effects | 0 |

The complete campaign, including detector controls, used **218 actual MCP calls
and 436 verified audit events**. The transport is official MCP memory sessions,
not a network service or a production authentication deployment.

Valid E0 work, scoped approval-authority tests, duplicate suppression, and chemical,
edge and wetware E1 positive controls actually executed. Input/state violations
were blocked before effects. Four invalid-result conditions legitimately executed
but delivered no successful result. The unconfirmed-timeout condition started
without committing, refused reuse while the worker remained active, and restored
READY only after owned-worker termination and explicit reconciliation.

The fault-control findings are intentionally excluded from the zero-forbidden-
effects statement: two isolated direct backend bypasses each committed once and
were flagged `unauthorized_commit`; two deny-all controls failed the expected
permitted-delivery count. Neither fault was introduced into production code.
These controls show that the checker detects both forbidden execution and absence
of required valid execution.

Approval-authority requirements and bad server-owned preset values are injected
only into isolated fixtures, as declared in the protocol. They do not establish
physical-device approval or physical amplitude-limit enforcement. The common
production adapter validator now checks task/backend identity and finite numeric
results; fixture-specific probability rules are not imposed on unrelated bindings.

## Bounded state exploration

The independent abstract model matched **464 / 464 transitions** across **78
deduplicated states**, with one exclusive E0 resource, two principals, two
single-shot request slots, and traces of at most six macro-events. Its 18-symbol
alphabet includes acquisition, preparation, execution, duplicates, invalid results,
timeout, abort, finish/status, expiry and reconciliation. Offline verification
reconstructed the expected graph and checked its coverage and backend effects.

Replaying canonical witnesses and outgoing transitions made **1,975 direct
control-surface calls**, producing **3,950 verified audit events**. These are not
additional MCP protocol-transport calls. Synchronous execution/validation/finish
is one macro-event; this does not exhaust concurrent intermediate interleavings.
The logical-timeout fixture is not a timing measurement. Real-time SDK recovery
and in-progress duplicates remain covered separately by R2 and direct tests.

## Executing-agent reference, not LLM results

The new [agent protocol](r3-agent-protocol.md) fixes 16 cases, two repetitions,
one configured model, at most 32 completions, and separate planner/effect scores.
The local deterministic reference processed **32 / 32 cases** and completed
**8 / 8 permitted execution opportunities**: six durable mock commits and two
fresh official SDK Simulator runs with independent native-event reconstruction.
It produced **78 MCP calls and 156 audit events**, no forbidden effects or invalid
deliveries, and 32 known reconciled final states. **No AI-Lab request was sent.**

The reference consumes the oracle by design and verifies the harness, not agent
intelligence. Additional tests submit an unsafe model-like request unchanged to
MCP, retain malformed replies/provider errors, redact an unexpected secret echo,
and demonstrate semantic misrouting: a valid authorized mock request can still
violate a user's request for physical hardware. The latter is a planner/intent
failure, not falsely counted as a server authorization bypass.

The completed live run records model availability, actual requested/response identifiers,
raw completion content, concrete messages, parsed decisions and every case outcome.
Refusal, clarification, server rejection, invalid output, failed execution and
unknown state must remain distinct. A model refusal does not test active server
enforcement; the direct campaign supplies that evidence.

The VPN preflight on 10 October reached `/v1/models` but found no `minimax-m2.7`
or MiniMax alias. Available text-model IDs included `gpt-oss-120b`,
`deepseek-v4-flash`, `glm-5.3`, `glm-5.3-flash`, `gemma-4-26b-a4b-it` and
`qwen3.8-27b`. Zero completion requests were sent. The sanitized catalog check is
retained in `.cp2n2/r3-ai-lab-preflight-20261010-01.json`. The original v1 fixture,
reference archive and scoring oracle have not been changed to disguise this
availability failure.

After the approved replacement and separate v2 freeze, the real Qwen campaign
completed 32 requests plus one excluded capability probe. It produced four mock
commits and two native-validated SDK deliveries, 80 MCP calls and 160 verified
audit events. Two stale-health attempts failed execution-time admission before
backend effects, despite successful MCP tool envelopes. The detailed
[Qwen result report](r3-agent-qwen-results.md) retains all eight planner-oracle
deviations and the model-visible freshness limitation. This is not a 32/32
perfect-agent result, a biological result or a proof of arbitrary-agent safety.

## Evidence locations and provenance

Local archives (ignored native evidence; publication is R5 work):

- `.cp2n2/r3-direct-confirmatory-20261010-01`
- `.cp2n2/r3-state-confirmatory-20261010-01`
- `.cp2n2/r3-agent-reference-20261010-01`
- `.cp2n2/r3-agent-live-qwen-20261010-01`
- `.cp2n2/r3-qwen-capability-20261010-01` (excluded from measured denominators)

Each archive retains protocol/oracle or design, source snapshot, exact calls,
audit, backend observations, final states and verification. Development evidence
under `r3-dev-*` and pytest temporary paths is excluded from these denominators.
The local runtime is Python 3.14.4, mcp 1.28.1, pydantic 2.13.4, cl-sdk 1.0.0,
tables 3.11.1. All **260 regression tests pass**, with two dependency deprecation
warnings. The frozen BioPattern Gate core, configuration and decoder are unchanged.

| Archive | Design/manifest SHA-256 | Source ZIP SHA-256 |
|---|---|---|
| Direct | `3c960bfe9f53698d91709a228aaf70372a9cf218355bba0db4e01de5ca2334f5` | `6b52b7a08a86759296123b5b4ad4629305ab3496b4322e1fc94de1210e6d87a9` |
| State | `c30e6da0dc87eafe58382db9280f4268477a0e32640ff09a7c6c237e43da9caa` | `f8f991e1d1521ef0f87674c2075702a5fa0d8f3ba0408ab3d45a2940746e8d55` |
| Reference | `8eccad48f46a8bb808c4c1f666ebad898072d1fcc781d7f3355e1047c3760d08` | `24db341299aacefca18c23f43b1c6bf17f946cc7092740e39b2baadf40acd6d6` |

The checker observes independent software files on the same host. It does not
defend against a compromised host able to forge all files, prove biological
performance, or establish replicated ownership or unbounded physical safety.

## Reproduce and continue

With the repository's Python environment active, offline verification requires
neither VPN nor new simulator runs:

```powershell
python scripts/run_r3_enforcement.py --verify .cp2n2/r3-direct-confirmatory-20261010-01
python scripts/run_r3_state_exploration.py --verify .cp2n2/r3-state-confirmatory-20261010-01
python scripts/run_r3_agent_campaign.py --verify .cp2n2/r3-agent-reference-20261010-01
python scripts/run_r3_agent_campaign.py --verify .cp2n2/r3-agent-live-qwen-20261010-01
python -m pytest -q
```

Omitting `--verify` creates a fresh local archive; the agent runner defaults to a
deterministic reference and makes no network requests. V2 selects the approved
Qwen settings; `--protocol-version v1` reproduces the original local reference.
`--preflight` inspects availability/budget without completions. A new, separately
authorized live campaign requires a passed `--capability-probe`, an explicit
budget and a fresh `--output` directory. Do not rerun live merely to inspect these
results, drop failed cases or relabel reference evidence as LLM observations.
R3's bounded work is complete; R4 is next, with public artifact/paper integration
and the comprehensive reviewer response still required in R5.
