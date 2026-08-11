# CP²N² v5.1.1 evidence-publication checklist

This patch release publishes the complete A6/RQ2 reference run and synchronizes
the selector artifacts with the current implementation. It changes no
control-plane behaviour and preserves the v5.1.0 E3 evidence boundary.

## Release identity

The annotated `v5.1.1` tag, source archive, evidence archive, checksum file,
GitHub release, and manuscript data-availability statement must identify the
same immutable release.

## Included evidence

- A6 reference run: 945 requests over five network profiles, six client counts,
  and three repetitions, with 30 aggregate cells.
- A6 raw JSONL/CSV, configuration, logs, traces, figures, summary, and verified
  47-entry internal SHA-256 manifest.
- Selector conformance outputs for five policies, four holdout cases, and 32
  seeded weighted-heuristic perturbations.
- A release-level evidence manifest and SHA-256 checksum set.

## Evidence boundary

The A6 archive is a controlled same-host software experiment. The Cortical Labs
integration remains E3 SDK-simulator evidence. This release does not claim
physical CL1 execution, biological performance, or an implemented Cortical
Cloud authentication and lifecycle contract.

## Freeze gate

- [x] The A6 internal manifest verifies all listed files.
- [x] The current selector scripts generated the frozen reference directory.
- [x] Selector names and values are synchronized across code, artifacts, and
  manuscript text.
- [x] The complete headless test suite passes with 146 tests.
- [x] The source and evidence archives verify against release checksums.
- [x] The annotated tag and GitHub release are published.
- [x] The manuscript points to the published v5.1.1 release.

## Immutable publication values

| Field | Frozen value |
|---|---|
| Tag commit | `36fbae002b0a9e066416ea9cafbb966a33fe53bb` |
| Test result | 146 passed |
| Source ZIP SHA-256 | `552943e9b3d51f8201cf7b46d58e4d1d09de53e762770cd7daf017246d1f6b22` |
| Evidence ZIP SHA-256 | `6b55c66a956d3c2c58971bc531da0d9421e0a3f4ac1d018212b8d0823ce27916` |
| GitHub release URL | `https://github.com/fischesn/cp2n2/releases/tag/v5.1.1` |

If any published identifier or artifact differs, issue a corrected release
rather than silently replacing files.
