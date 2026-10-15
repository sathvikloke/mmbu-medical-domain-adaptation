# Phase 1 evaluator mechanics

**Revision:** 2026-10-15-cycle-46a  
**Status:** binding synthetic/engineering evaluator contract; not an official harness  
**Scope:** closed evaluation populations, execution-output closure, task-change arithmetic, and original-pixel box geometry

This file is the manifest-covered mechanics companion to `SCHEMAS.md`. It fixes the parts of the Phase 1 evaluator that must be independently recomputable before the final organizer harness exists. It does not freeze unknown official JSON property names, prompts, context fields, judge rubrics, or missing-field policy. Those remain versioned by `mmbu.phase1.prompt_schema_contract` and cannot be labeled `organizer_confirmed` without new authority.

## Population and layer closure

The governing `mmbu.phase1.example_manifest` is frozen before execution. Its row order is authoritative and every row is an independent evaluation unit. A candidate cannot change the population, row order, task weight, requested context fields, geometry policy, dimensions, or target digests. Base and adapted conditions use the same manifest digest.

For each condition, the `mmbu.phase1.execution_output_manifest` contains exactly one raw, parsed, validated, and judged record for every example ID in the example manifest. Failed rows still have all four records: downstream records use the required `not_run` statuses and retain the terminal outcome fixed by `SCHEMAS.md`. No missing row is converted to a zero-length output, silently retried, replaced, or removed. Extra example IDs, duplicate layer roles, a layer record bound to another example/contract/manifest, or a layer set that is not exactly equal to the example-manifest population invalidates the condition.

The output manifest is computed after all execution payloads but before the reproducibility and run records. Its entry `sha256` values equal the reproducibility record's `output_digests` exactly. The finalized run's `output_manifest_digest` resolves to that manifest, and its `input_manifest_digests` contains the governing example-manifest digest. Claims, requirement trace, phase decision, reproducibility, run, evidence manifest, and the execution-output manifest itself are never execution-payload entries.

## Exact task-grade and task-change rules

For example `i`, let `b_i` be the base task grade and `a_i` the adapted task grade. A successfully judged row uses its recorded finite `task_grade` in `[0,1]`. Every other terminal outcome contributes grade zero. A missing layer record or missing example-manifest row is structural invalidity, not a zero grade.

Let `w_i` be the positive finite `task_weight` frozen in the example manifest, and let `W = sum_i w_i`. The population must be nonempty, so `W > 0`. Arithmetic interprets each RFC 8785 canonical JSON number lexeme as an exact decimal rational; implementations may not use a binary-floating tolerance to change a sign, tie, threshold comparison, or conformance result.

The mandatory quantities are:

```text
B = (sum_i w_i b_i) / W
T = (sum_i w_i a_i) / W
d_i = a_i - b_i
positive_mass = (sum_i w_i max(d_i, 0)) / W
negative_mass = (sum_i w_i max(-d_i, 0)) / W
net_task_change = T - B = positive_mass - negative_mass
```

Each row state is `positive` when `d_i > 0`, `zero` when `d_i = 0` exactly, and `negative` when `d_i < 0`. The summary contains every example exactly once in manifest order and recomputes all totals; a supplied total never overrides the rows.

Binary flips are secondary and may be emitted only when the bound judge policy prospectively defines an exact boolean correctness predicate. Then `N` is the full example count, including failures; `PF` counts false-to-true rows, `NF` counts true-to-false rows, and `binary_net_flip_rate = (PF - NF) / N`. The other `N - PF - NF` rows remain in the denominator. If no predicate was frozen, the entire binary summary is null. Fractional grades do not silently imply a threshold or `grade == 1` predicate.

`mmbu.phase1.task_change_summary` is a closed record with exactly `schema_id`, `schema_version`, `summary_id`, `example_manifest_digest`, `base_output_manifest_digest`, `adapted_output_manifest_digest`, `judge_policy_digest`, `rows`, `totals`, `binary_summary`, `created_at`, and `record_digest`.

- `rows` is in example-manifest order and contains exactly `example_id`, `independent_unit_id`, `task_weight`, `base_terminal_outcome`, `adapted_terminal_outcome`, `base_grade`, `adapted_grade`, `delta`, and `state`. IDs and weights equal the manifest; outcomes and grades equal the two judged layers; delta and state recompute exactly.
- `totals` contains exactly `example_count`, `weight_sum`, `base_mean`, `adapted_mean`, `positive_mass`, `negative_mass`, and `net_task_change`. All values recompute from `rows` using the equations above.
- `binary_summary` is null when no prospective correctness predicate exists. Otherwise it contains exactly `correctness_rule_digest`, `N`, `PF`, `NF`, `other`, and `binary_net_flip_rate`; `N = PF + NF + other` and all values recompute from the same rows.

No result-dependent reweighting, denominator change, tolerance, imputation, or aggregation-unit switch is permitted. A different population, weight, correctness predicate, or failure policy is a different prospectively bound condition.

## Original-pixel `xywh` geometry

A box is the four-number array `[x, y, width, height]` in the original decoded image frame. Image width `W` and height `H` are positive integers. Coordinates are finite exact decimal rationals. A valid box satisfies all of:

```text
x >= 0
y >= 0
width > 0
height > 0
x + width <= W
y + height <= H
```

The evaluator never clips, rounds, swaps, reorders, normalizes, or otherwise repairs a box. A normalized-looking box is still interpreted as original-pixel coordinates. An invalid predicted or target box makes geometry invalid for that row.

Boxes denote continuous half-open rectangles `[x, x + width) x [y, y + height)`. For boxes `A` and `B`:

```text
intersection_width  = max(0, min(A.right, B.right) - max(A.x, B.x))
intersection_height = max(0, min(A.bottom, B.bottom) - max(A.y, B.y))
intersection_area   = intersection_width * intersection_height
union_area          = area(A) + area(B) - intersection_area
IoU                 = intersection_area / union_area
```

Valid boxes have positive union area. Merely touching edges yields IoU zero. Threshold comparison is inclusive: `IoU >= threshold` passes. The synthetic Phase 1 threshold is exactly `1/2`; a later official threshold must be bound by the prompt/schema contract rather than inferred.

Each detection row freezes exactly one `box_policy` in the example manifest:

- `single`: exactly one target and exactly one prediction are required; that pair must meet threshold.
- `all_targets`: target and prediction counts must be equal and nonzero. Passing requires a perfect one-to-one bipartite matching using only edges at or above threshold. For the recorded matching, maximize exact total IoU; ties choose the lexicographically smallest vector of `(prediction_index, target_index)` pairs after sorting by prediction index. Extra, missing, or duplicate-use boxes fail.
- `any_one`: one or more targets and exactly one prediction are required. The row passes when the maximum IoU against any target meets threshold. If multiple targets tie, record the lowest target index. Two predictions are invalid even if one would pass.
- `not_applicable`: targets and predictions are empty and no geometry score is emitted.

Prediction and target array order is preserved as evidence. Only the matching search may pair indices; it never reorders stored boxes. Detection rows use manifest-bound original dimensions and target-box artifact digests. Non-detection rows use `not_applicable` and null dimensions/target digest.

`mmbu.phase1.geometry_summary` is a closed record with exactly `schema_id`, `schema_version`, `summary_id`, `example_manifest_digest`, `output_manifest_digest`, `validator_digest`, `threshold`, `rows`, `created_at`, and `record_digest`. `rows` contains every detection example exactly once in example-manifest order. Each row has exactly `example_id`, `box_policy`, `image_width`, `image_height`, `target_boxes_digest`, `predicted_boxes_digest`, `target_count`, `prediction_count`, `boxes_valid`, `matched_pairs`, `row_iou`, `passed`, and `reason_code`. Digests resolve to immutable ordered arrays of raw boxes. `matched_pairs` is the deterministic index/IoU result above; `row_iou` is the single/max pair IoU for `single`/`any_one`, the exact mean over the selected perfect matching for `all_targets`, and null when no valid score exists. Counts, validity, matching, IoU, disposition, and reason code are recomputed rather than trusted.

## Conformance vectors

These vectors are normative. Equivalent exact-rational encodings are allowed only when their RFC 8785 canonical values are equal.

### Task change

| ID | Weight | Base grade/outcome | Adapted grade/outcome | Delta | State |
|---|---:|---|---|---:|---|
| `a` | 1 | 0.25 / success | 0.75 / success | 0.50 | positive |
| `b` | 2 | 0.80 / success | 0.50 / success | -0.30 | negative |
| `c` | 1 | 0.40 / success | 0.40 / success | 0 | zero |
| `d` | 2 | 1 / success | null / runtime_failure | -1 | negative |

The required totals are `example_count=4`, `weight_sum=6`, `B=17/24`, `T=43/120`, `positive_mass=1/12`, `negative_mass=13/30`, and `net_task_change=-7/20`. With a prospectively bound predicate of exact grade 1, `N=4`, `PF=0`, `NF=1`, `other=3`, and `binary_net_flip_rate=-1/4`. Without that bound predicate, `binary_summary` is null. Omitting row `d`, changing its failure grade from zero, or using four as the weighted denominator is invalid.

### Geometry

For an image `W=100`, `H=80` and threshold `1/2`:

| Case | Target(s) | Prediction(s) | Policy | Required result |
|---|---|---|---|---|
| exact | `[10,10,20,20]` | `[10,10,20,20]` | single | IoU 1; pass |
| partial | `[10,10,20,20]` | `[20,10,20,20]` | single | IoU 1/3; fail |
| touching | `[0,0,10,10]` | `[10,0,10,10]` | single | IoU 0; fail |
| border-valid | `[0,0,100,80]` | `[0,0,100,80]` | single | valid; IoU 1; pass |
| overflow | `[90,70,10,10]` | `[90,70,11,10]` | single | invalid prediction; fail without clipping |
| any-one | `[0,0,10,10]`, `[20,20,10,10]` | `[20,20,10,10]` | any_one | match target index 1; pass |
| any-one-extra | same | two predictions | any_one | invalid prediction count; fail |
| all-reordered | two disjoint 10x10 targets | the same boxes in reverse order | all_targets | deterministic perfect matching; pass |
| all-extra | two targets | the same two plus one extra | all_targets | count mismatch; fail |

Negative width/height, nonfinite coordinates, swapped frame dimensions, normalized-coordinate reinterpretation, target reuse, and a threshold chosen after outputs are all invalid.

## Claim boundary

Passing these mechanics proves only that synthetic or duly authorized evaluation records obey this contract. It is not evidence of official-harness equivalence, biomedical validity, model performance, or private-set generalization. Unknown official behavior remains `brief_snapshot` or unresolved, never silently upgraded.
