# Package F schema and negative-test matrix

**Prepared:** October 22, 2026
**Evidence class:** design-only schema review
**Scope:** Package F CPU-only synthetic manifest, decision function, and disabled H1 registry

This matrix freezes the bounded implementation surface before production code. It selects no scientific value, admits
no data, loads no model, and authorizes no execution. Synthetic literals exist only to prove validator behavior.

| Contract surface | Production interface | Positive fixture | Required rejection fixtures |
|---|---|---|---|
| Canonical manifest identity | `competition_manifest.manifest_digest`, `validate_manifest` | Closed draft with the four immutable architecture IDs and explicit unknowns | Extra/missing field, bad digest, duplicate/wrong candidate, unqualified identifier |
| State machine | `competition_manifest.validate_transition` | Every declared forward edge | Backward, skipped, or reopening transition |
| Objective/exposure closure | `competition_manifest.validate_manifest` | Reduced task/context shares summing to one; one unit mass; B2-F disabled | Float/unreduced share, wrong sum, copied score weights without rationale, enabled B2-F without pre-output gate |
| Geometry/serializer/public firewall | `competition_manifest.validate_manifest` | Original-pixel half-open `xywh`, inverse receipt, fail-closed JSON, answer-only rationale policy | Normalized/ambiguous frame, repair policy, public input/derivative/choice, invented rationale |
| Freeze blocker | `competition_manifest.validate_manifest` | Unknown-bearing draft validates as non-runnable | Any `frozen` manifest with unknown scientific or authority values |
| Exact score proxy | `track2_score.score_proxy` | Hand-derived rational vectors | Out-of-range input and nonpositive task gain eligibility |
| Promotion decision | `competition_manifest.evaluate_promotion` | Named candidate clears every comparator and conjunctive gate | Missing/false gate, tie, failed task floor, runner-up rescue, nonfinite/unknown result |
| Disabled registry envelope | `research_registry.validate_registry` | Empty registry and one closed H1 object | Unsorted/duplicate/extra entry; changed status/enabled literal; public ancestry; primary-lane mutation |
| H1 arm identity | `research_registry.validate_registry` | Exact `SYS-A0`–`SYS-A3` arm bindings | Missing/renamed/fifth arm; wrong objective, normalization, base, serializer, optimizer, seed, or checkpoint slot |
| H1 fixed-budget exposure | `research_registry.validate_registry` | Matched tokens/loss/update/FLOP/compute totals with declared row/uniform policies | Missing displaced schedule, unequal totals, wrong per-unit policy, cross-context equalization |
| H1 estimands and gates | `research_registry.validate_registry` | Separate task/context estimands and all eight common gates | Scalar collapse, swapped/missing endpoint, missing minimum effect, missing gate |
| H1 mechanism and replication | `research_registry.validate_registry` | Pairwise equalization, no-new-unit duplication, two governed confirmation parents | Unmatched perturbation, role overlap, reused parent/governance, development parent counted as confirmation |
| No execution bridge | `research_registry.validate_registry` | Representation-only references | Generic experiment/lock/decision receipt names a research arm |

The focused suite must be added to the fail-closed Phase 1 test inventory. Package F is `schema_ready` only after every
fixture passes; that status is not `experiment_freeze_ready` or `execution_authorized`.
