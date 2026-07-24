# Changelog

## v4.0 — 2026-07-24

The first release after the frozen v3.0 baseline. This release completes the
accepted A0-A7 development line.

### Added

- Versioned, substrate-neutral Physical Neural Resource Contract v1.0.
- Runtime evidence, telemetry provenance/freshness, safety, access, cost, and
  data-governance fields with fail-closed admissibility checks.
- Lifecycle and lease protocol with reservations, state-version checks,
  idempotency, phase timeouts, abort, reconciliation, and typed errors.
- Admission, feasibility, and documented backend-selection policies.
- General adapter architecture separating control adapters from substrate
  runtimes.
- Constrained agent-facing MCP surface with plan validation, approvals, audit,
  and server-owned presets.
- Gemini, Ollama, and University of Lübeck AI-Lab agent integrations.
- Distributed four-process testbed, versioned deployment/fault profiles, and
  reproducible RQ2 evaluation artifacts.
- Expanded CL SDK Simulator and attested CL integration path.
- Installation, operation, evaluation, and evidence-boundary documentation.

### Verification

- 91 automated tests pass in the release branch.
- AI-Lab reference evaluation: 2/2 successful dry-run cases.
- AI-Lab evaluation explicitly records `pnn_evidence=false` and
  `substrate_executed=false`.

### Evidence boundary

v4.0 demonstrates a substrate-aware control plane and reproducible simulator,
synthetic-twin, and agent-control workflows. It does not claim that the
prototype has executed a biological PNN. The University AI-Lab integration is
an LLM-agent runtime, not a PNN backend.

## v3.0

Frozen legacy baseline. See the `v3.0` tag for the corresponding source state.
