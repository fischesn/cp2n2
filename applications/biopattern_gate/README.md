# BioPattern Gate

BioPattern Gate is the access-independent application core for the Cortical
Labs case study. Two hidden, charge-equivalent logical input patterns differ
only in temporal order. A dynamic reservoir response is converted into a
small, fixed feature vector and passed to a frozen linear readout. The
committed decision routes the result to the `left` or `right` gate before the
expected label is revealed.

The current `technical-e3` path is deliberately a deterministic test double.
It proves orchestration, blinding, provenance, validation, abort behavior, and
replayability. It is not a biological result and its accuracy must not be
reported as PNN performance.

Run the local demonstration from the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\run_biopattern_gate_demo.py
```

Run the same frozen application through the complete constrained CP²N²
lifecycle (including dry run, exclusive lease, prepare, execute, result,
audit references, and automatic release):

```powershell
.\.venv\Scripts\python.exe scripts\run_biopattern_gate_mcp_e3.py
```

The MCP result exposes only a sanitized aggregate and checksum-bearing
artifact references. It binds the server-owned preset to exact application
source, configuration, and decoder hashes. No raw spike events or physical
control parameters cross the agent boundary.

Verify that the checked-in JSON Schema matches the frozen configuration model:

```powershell
.\.venv\Scripts\python.exe scripts\export_biopattern_gate_schema.py --check
```

## Hardware boundary

The core exposes a narrow `BioPatternGatePort`. A future CL1 implementation
must translate provider-approved logical groups and protocol references into
the actual SDK calls. The repository intentionally contains no executable
provider preset. Hardware modes fail validation unless all of the following
are present:

- `provider_approved` preset namespace;
- attested `cl1` runtime and E5 evidence context;
- verified provider API contract;
- exact approval references;
- calibration reference;
- matching frozen decoder and configuration hashes.

The provider-approved namespace remains empty until those facts can be
verified with the granted Cortical Labs environment.
