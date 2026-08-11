# CP²N² v5.1.1 Zenodo record

The published Zenodo record extends the existing CP²N² software concept rather
than creating a second, unrelated deposit.

## Persistent identifiers

- Version-specific DOI: `10.5281/zenodo.21887895`
- Concept DOI for all CP²N² versions: `10.5281/zenodo.19595082`
- GitHub release: `https://github.com/fischesn/cp2n2/releases/tag/v5.1.1`
- Tagged commit: `36fbae002b0a9e066416ea9cafbb966a33fe53bb`

Use the version-specific DOI when citing the exact software and evidence used
by the paper. Use the concept DOI only when referring to CP²N² independently of
a particular release.

## Combined archival bundle

The v5.1.1 record preserves Zenodo's automatically generated GitHub source
snapshot and adds `cp2n2-v5.1.1-zenodo.zip` as the complete archival bundle.
The latter contains:

- the exact tagged source tree exported by `cp2n2-v5.1.1-source.zip`;
- the complete A6/RQ2 archive with 945 request records and 30 aggregate cells;
- the synchronized selector reference run, including four holdout cases and 32
  seeded weight perturbations;
- source, evidence, and per-run SHA-256 manifests; and
- the citation and Zenodo metadata used to describe the record.

Build it from the already verified GitHub release inputs:

```powershell
.\scripts\build_zenodo_bundle.ps1 -Version v5.1.1
```

The generated `ZENODO-SHA256SUMS.txt` records the bundle checksum. The bundle
does not alter the v5.1.1 source tree or any experimental result; it only places
the immutable source and evidence inputs under one archival root.

Frozen bundle SHA-256:

```text
aaeb13a608fa2ae94d61dbce2df19bfbd5a9669d6c61e1b64b1337753ffedaa7
```

## Evidence boundary

A6 is a controlled same-host software experiment. The Cortical Labs paths are
E3 SDK-simulator evidence. The record does not claim physical CL1 execution,
biological performance, provider-approved stimulation parameters, or an
implemented Cortical Cloud authentication and lifecycle contract.
