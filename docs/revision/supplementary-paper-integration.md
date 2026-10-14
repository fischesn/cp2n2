# Supplementary paper and reviewer response integration

14 October 2026. AP1–AP3 and the Gemini selector results are integrated into the
authoritative journal manuscript, its generated neutral arXiv view and the
22-comment reviewer response. Clean and cumulative yellow-marked journal
PDFs are **20 pages** each after meaning-preserving compaction; arXiv is
**29 pages**. The response uses the official
IEEE template and is **13 pages**; the three-page checklist retains all ten
unchecked author boxes.

The manuscript integration above is a local revision checkpoint. The subsequent
[supplementary evidence publication](supplementary-zenodo-publication.md) closes
the raw-archive gate: DOI `10.5281/zenodo.23377537`, version
`SUPPLEMENTARY-2026-10-14`. Four archived campaign verifiers pass, and all five
new public files match their complete SHA-256 hashes after anonymous download.
Independent co-author reproduction and final author/submission approval remain
open; public archival is not independent reproduction or a software release.

The final editorial shortening removes repeated/verbose prose without changing
methods, results, scientific qualifications, six figure environments, thirteen
tables or citation order. Font sizes, margins, biographies and photographs are
unchanged. The generated arXiv view stays scientifically synchronized; reviewer
locators use the current clean journal. All 25 paper/workflow tests and the
522-test software suite pass. The fresh final QA record is
`tmp/shortening-20261014/verification.json` in the paper repository; earlier
21/21/30-page publication-stage records below remain historical.

## Results and source boundaries

The supplementary studies retain their separate frozen identities:

| Study | Manuscript evidence | Principal reviewer entries |
| --- | --- | --- |
| AP1 | 46 ordinary cases and four detector controls; 28 invalid preconditions cause no starts/commits, six valid controls deliver, twelve post-invalid cases commit but deliver no success | R1.3, R2.7, R2.10–12, R3.1, R3.3 |
| AP2 | 18 separate-process/TCP trials; 96 structured HTTP responses; uncertain invocation suppresses automatic retry/fallback and requires explicit recovery | R2.5, R2.6, R2.12 |
| AP3 | 80 fresh-registry trials; 32,000 measured calls and 3,200 warm-ups; trial-summary intervals and observed bounded CPU load | R2.13 |
| Gemini | Twelve externally model-authored cases; all four outcomes match in 72 policy/order cells; 36 invariant order pairs | R2.3, R3.4 |

The [AP source freeze](ap1-ap3-source-freeze.json) identifies 290 files.
The [Gemini evidence index](gemini-selector-evidence-index.json) identifies
its 295-file snapshot, preserving all 290 prior hashes. The published R5 source
and outcomes are not reassigned to the modified source. No new functional
change or scored observation was introduced by this paper integration.

Required nonnumeric drift and early generic provider-error handling are
corrected in the supplementary source. Their historical R4 observations and
oracle remain unchanged. AP2 does not fix the restart duplicates caused by
lost in-memory controller state.

## Manuscript and response corrections

Both views report the exact historical 141/160 score and the physical-execution
class's one refusal plus nineteen clarifications (1/20). These decisions are
not rescored or pooled with the executing Qwen study. The historical 7/7 versus
6/7 explanation now identifies the actual locality/placement differences,
rather than attributing them to drift, stale state or missing supervision.

AP1 wording distinguishes precondition effect prevention from post-commit
delivery withholding. Cached metadata checks and duplicate same-property
contradictions do not establish signed replay prevention, sensor fusion or
physical truth. Optional calibration remains optional; required declared
validity is not physical calibration evidence.

AP3 intervals describe median trial summaries, including the median of trial
p95 values, not a population tail guarantee. Actual worker utilization is
about 29–37% of one core, not the declared 60% duty fraction or host saturation.
Directed execution at `bench-0` is not general selector scaling.

Gemini strengthens external case authorship under a written contract, not
independent human reproduction or representative workload sampling. Its
dependent policy/order cells are not independent experiments. Fixed multi-turn
contexts and benign German/Vietnamese prompts likewise are not adaptive or
multilingual red-team evidence.

All 22 responses preserve concern, response, action, location and evidence.
Partial fulfillment is explicit for physical validation, scheduler/shared
capacity, persistent competing controllers, broad adversarial/model coverage,
telemetry truth and cross-environment performance. The six suggested references
receive individual relevance/access explanations; the response no longer
argues that citing detection literature would imply an IDS evaluation.

## Prepared artifacts and checks

The paper repository remains authoritative:

`C:/Users/Stefan Fischer/Documents/Publikationen/papers/PNN-papers/phys-MCP`

- `cp2n2.tex` contains the scientific edits and cumulative revision markers.
- `cp2n2-arxiv.tex` is generated from that source, never edited separately.
- `output/pdf/` contains clean/marked journal, neutral arXiv and response/checklist PDFs.
- `submission-package/` contains matching manuscript source ZIPs and SHA-256 manifests.
- `IEEE-ACCESS-RESPONSE-TO-REVIEWERS.md` is the canonical all-comment text.
- `reviewer-response/` versions the verified official-template documents,
  checklist status and their byte manifest; matching copies are in
  [this repository](ieee-access/README.md).

All three Biber-backed manuscript builds pass. Twenty-two paper/workflow
regression tests pass, covering journal/arXiv synchronization, source/result
boundaries, all-comment coverage, valid locators, cumulative markup and
byte-preserving document synchronization. The integration QA directory in the
paper repository is `tmp/supplementary-integration/`.
All 88 output pages were visually checked. Source ZIPs pass CRC, exact current
source/PDF hash bindings and duplicate-entry checks; document mirrors pass
their SHA-256/size manifests. The QA record is `verification.json` in that
directory. The final source-hash check also confirms that manuscript integration
did not alter the evaluated software or Gemini expectations.

The official templates retain every preserve-only package part and their
section geometry. The bundled DOCX renderer remains unavailable because
LibreOffice is absent; the existing read-only Microsoft Word PDF-export
workflow supplies the reviewed visual output without resaving the DOCX.

## Remaining work

The post-publication refresh cites DOI `10.5281/zenodo.23377537` in both
manuscript views and the reviewer response. Matching 21/21/30-page manuscript
PDF/source packages and 13/3-page official-template reviewer PDFs were rebuilt.
All 88 pages are covered by fresh rendering and individual inspection of every
changed page or pixel equality with previously inspected pages. Twenty-four
paper/workflow tests and 36 supplementary packaging/publication tests pass.
Source/PDF bindings, template fidelity and byte-identical reviewer mirrors pass;
the final QA receipt is `tmp/supplementary-publication-final-qa/verification.json`
in the paper repository. The evaluated software and Gemini expectations remain
unchanged. These technical checks do not constitute final author approval.

1. Review the revised manuscript and every response with the co-authors.
2. Independently reproduce key execution/enforcement results; automated
   same-host verification does not satisfy this gate.
3. Review the technically verified DOI-integrated packages for final author
   approval. The supplementary DOI is `10.5281/zenodo.23377537`; DOI
   `10.5281/zenodo.23281161` covers only the earlier R5 evidence, not AP/Gemini.
4. Approve the submission route, final checklist and upload files.

No commit, push, release, Zenodo upload or journal/arXiv submission was
performed by the initial manuscript integration step. The later Zenodo
publication was separately authorized and is recorded in the linked
supplementary publication receipt; it does not authorize those other actions.

