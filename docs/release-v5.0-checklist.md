# CP²N² v5.0 release checklist

This checklist prepares the software and evidence release that accompanies the
journal manuscript. It does not authorize publication before the manuscript
and artifact revision is frozen.

## Release identity

The following identifiers must refer to one immutable revision:

- Git commit on `main`;
- annotated Git tag `v5.0`;
- GitHub release and source archive;
- `cp2n2-v5.0-source.zip` and `SHA256SUMS.txt`;
- Zenodo deposit and DOI;
- non-anonymous manuscript software/data citation;
- paper metrics and cited evaluation artifacts.

Do not build the candidate from uncommitted files, a local-only commit, or a
branch that has not been merged and pushed.

## Included scope

v5.0 contains the merged post-v4.0 work:

- the CP²N² naming migration and compatibility aliases;
- the BioPattern Gate E3 control-plane integration;
- the audited replay/web demo and user guide;
- platform-independent canonical audit-fixture hashing;
- the Agent-to-PNN v1.2 campaign package;
- the frozen University of Lübeck AI-Lab campaign results.

The release does not claim physical CL1 execution, biological performance, or
provider-approved Cortical Cloud deployment. Those require separately attested
E5 evidence.

## Freeze gate

- [ ] The authoritative manuscript and software wording use the same evidence
  boundary and release identity.
- [ ] The paper revision is frozen for release preparation.
- [ ] `main` contains all intended changes and is synchronized with
  `origin/main`.
- [ ] `git status --short` is empty.
- [ ] No secrets, local `.env` files, provider credentials, or unredacted
  prompts are tracked.
- [ ] The complete automated test suite passes from a fresh environment.
- [ ] The E3 BioPattern fixture and audit chain verify.
- [ ] The frozen Agent-to-PNN campaign manifest, trial count, metrics, and
  audit verification match the manuscript.
- [ ] `CHANGELOG.md`, `README.md`, and the project master plan reflect the
  frozen state.

## Build the candidate

From a clean `main` worktree:

```powershell
.\scripts\build_release_candidate.ps1 -Version v5.0
```

The script refuses a dirty or non-`main` worktree and creates an untracked
release directory containing the source ZIP, SHA-256 manifest, and
machine-readable release manifest. Review those files before tagging.

Record the final values here only after the gate passes:

| Field | Frozen value |
|---|---|
| Commit | |
| Test result | |
| BioPattern E3 fixture verification | |
| Agent campaign manifest | |
| Source ZIP SHA-256 | |
| GitHub release URL | |
| Zenodo DOI | |

## Publish and bind

- [ ] Create an annotated `v5.0` tag at the recorded commit.
- [ ] Push the tag and publish the GitHub release with the generated archive
  and checksum files.
- [ ] Archive that exact release on Zenodo and verify its files and checksum.
- [ ] Add the Zenodo DOI and Git commit to the non-anonymous manuscript.
- [ ] Rebuild the final PDF and verify that the cited release, code, data,
  metrics, and evidence statements all resolve to the frozen revision.

If any published identifier or artifact differs, stop and issue a corrected
release rather than silently replacing files.
