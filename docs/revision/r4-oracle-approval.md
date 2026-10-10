# R4 selector oracle sample approval

On 10 October 2026, Stefan Fischer confirmed the admissible resource sets and
expected selections for the twelve frozen R4 sample cases. This closes the
human author approval gate in R4.1. It is a post-run review of those twelve
expectations, not pre-run human validation or independent reproduction.

## Author confirmation

The explicit confirmation in the project chat was:

> Ich habe die zwölf Fälle geprüft und bestätige jeweils die zulässigen Ressourcen und die erwartete Auswahl.

The preceding review explanation presented each case's inputs and expected
outcome, the inclusive latency/age/cost boundaries, the exclusive drift
boundary, supervision requirements, priority policies and identifier tie rule.

## Approved expectations

| Frozen case | Admissible resources | Selected resource |
| --- | --- | --- |
| `singleton-0` | `a` | `a` |
| `empty_inventory-0` | None | None |
| `latency_boundary-0` | None | None |
| `latency_boundary-1` | `a` | `a` |
| `drift_boundary-1` | None | None |
| `freshness_boundary-1` | `a` | `a` |
| `freshness_boundary-2` | None | None |
| `cost_boundary-1` | `a` | `a` |
| `identifier_tie-1` | `a`, `b` | `a` |
| `policy_tradeoff-0` | `a`, `b` | `b` |
| `policy_tradeoff-1` | `a`, `b` | `a` |
| `supervision-0` | `b` | `b` |

The [review fixture](../../evaluation/fixtures/r4-selection-review-v1.json)
contains the same twelve expectations and their reasons. They were checked
against the archived inputs in
`.cp2n2/r4-selection-confirmatory-20261010-01/specification.json` before the
review explanation was presented. The software/evaluation checkpoint is
commit `f5802a3d1c2695637a5840ab5ed94d46ce64063c`.

SHA-256 bindings at approval:

- Review fixture: `a2c636dbd380efd83f3467f4b530bfa82e3da82533ab3e0a5209d096cf271647`.
- Frozen selection specification: `213ee450d0299de1947c8d4e47975bf172695b54669d4b906a23a8befd810ce7`.
- Frozen selection manifest: `bf127e83366b8185f73e8dee3b26dcfcf8079ec03031be77fde8d9e3646667dc`.

## Scope and remaining work

The approval covers these twelve admissible sets and selections under the
declared rules. It does not independently validate all 64 cases, every ranking
or rejection explanation, physical safety thresholds, or deployment behavior.
It is not a second-author review, a signed certification, or evidence that the
synthetic workload represents real substrate measurements.

The pre-run analytical checks remain attributable to the authoring agent.
No case, expected outcome, measurement, frozen protocol, archive or hash
inventory is changed by this approval. R4 is complete in its documented bounded
scope. Clean-checkout reproduction, public raw-archive publication, manuscript
integration and the comprehensive reviewer response remain R5 work.
