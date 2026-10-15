# Phase 1 evaluator mechanics

**Revision:** 2026-10-15-cycle-46c
**Status:** binding synthetic/engineering evaluator contract; not an official harness  
**Scope:** closed evaluation populations, execution-output closure, task-change arithmetic, and original-pixel box geometry

This file is the manifest-covered mechanics companion to `SCHEMAS.md`. It fixes the parts of the Phase 1 evaluator that must be independently recomputable before the final organizer harness exists. It does not freeze unknown official JSON property names, prompts, context fields, judge rubrics, or missing-field policy. Those remain versioned by `mmbu.phase1.prompt_schema_contract` and cannot be labeled `organizer_confirmed` without new authority.

## Canonical exact-rational wire type

Every exact value produced by division is encoded as one closed JSON object containing exactly `numerator` and `denominator`. Both are JSON integers and not booleans; `numerator` is signed and `denominator` is strictly positive. The fraction is reduced so `gcd(abs(numerator), denominator)=1`, and zero has the sole representation `{"denominator":1,"numerator":0}`. Negative signs occur only on `numerator`. Implementations parse source JSON number lexemes without first rounding through binary floating point, perform exact rational arithmetic, and reject rather than approximate an unrepresentable or resource-exhausting value. RFC 8785 canonical member ordering makes the exact byte form `{"denominator":D,"numerator":N}`.

This wire type is mandatory for every derived `delta`, `weight_sum`, `base_mean`, `adapted_mean`, `positive_mass`, `negative_mass`, `net_task_change`, `binary_net_flip_rate`, geometry `threshold`, matched-pair `iou`, and non-null `row_iou`. Declared source weights, grades, dimensions, and box coordinates remain the exact JSON numbers in their governing records; derived records never replace an exact fraction with a decimal approximation. Validators compare rationals by cross multiplication after checking canonical reduction, never by a floating tolerance.

## Population and layer closure

The governing `mmbu.phase1.example_manifest` is frozen before execution. Its row order is authoritative and every row is an independent evaluation unit. A candidate cannot change the population, row order, task weight, requested context fields, geometry policy, dimensions, or target digests. Base and adapted conditions use the same manifest digest.

Before either condition emits its first raw output, one immutable `mmbu.phase1.paired_condition_contract` binds the already immutable base and adapted experiments. Its `matched_conditions` object contains exactly `purpose`, `authorization_registry_digest`, `source_record_digests`, `purpose_authorization_digests`, `source_manifest_digests`, `split_manifest_digests`, `non_model_lineage_root_digests`, `non_model_decision_execution_receipt_digests`, `execution_condition_digest`, `prospective_lock_digest`, and `decision_function_digest`. Each value equals the same-named required field in both experiments. Set-like arrays are canonical sorted sets; every other value is byte-identical. `execution_condition_digest` resolves the complete closed `mmbu.phase1.execution_condition` in `SCHEMAS.md`; none of its request, processor, component, seed/RNG, decoding, task/context isolation, failure/retry, runtime/software/device/topology, batching/order, precision/backend, cache, or network state may live in an opaque side artifact. Every condition that is not model identity must be covered by these named projections; omission is invalid.

The contract also contains closed `base_model_identity` and `adapted_model_identity` objects, each with exactly `model_digest`, `candidate_ids`, `model_lineage_root_digests`, `model_selection_receipt_digests`, and `adapted_from_model_digest`. The base value for `adapted_from_model_digest` is null; the adapted value equals the base `model_digest`. `allowed_difference_fields` is exactly the sorted set `adapted_from_model_digest`, `candidate_ids`, `model_digest`, `model_lineage_root_digests`, and `model_selection_receipt_digests`; it cannot be widened. Each experiment projects field-for-field to the shared `matched_conditions` and its respective model identity. A mismatch in any matched field or any execution-condition leaf, an extra differing field, a changed allowlist, or an adapted lineage not rooted at the named base rejects the pair. Both experiments, every raw record, both output manifests, both finalized runs, and both reproducibility records bind the same execution-condition digest; validators resolve it and compare every observed transitive value rather than accepting digest equality alone.

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

`mmbu.phase1.task_change_summary` is a closed record with exactly `schema_id`, `schema_version`, `summary_id`, `pairing_contract_digest`, `example_manifest_digest`, `base_run_digest`, `adapted_run_digest`, `base_output_manifest_digest`, `adapted_output_manifest_digest`, `judge_policy_digest`, `rows`, `totals`, `binary_summary`, `created_at`, and `record_digest`. The pairing contract predates every raw record. Each run resolves to its named output manifest and experiment, both experiments equal the pairing contract, both reproducibility records prove the bound matched condition, `judge_policy_digest` equals the execution-condition component, and no condition field outside the fixed model-identity allowlist differs.

- `rows` is in example-manifest order and contains exactly `example_id`, `independent_unit_id`, `task_weight`, `base_terminal_outcome`, `adapted_terminal_outcome`, `base_grade`, `adapted_grade`, `delta`, and `state`. IDs and weights equal the manifest; outcomes and grades equal the two judged layers. Successful grades remain their source JSON numbers and non-success grades remain null; arithmetic substitutes exact zero only while deriving `delta` and totals. `delta` uses the canonical rational wire type and state recomputes exactly.
- `totals` contains exactly `example_count`, `weight_sum`, `base_mean`, `adapted_mean`, `positive_mass`, `negative_mass`, and `net_task_change`. Every numeric value except integer `example_count` uses the canonical rational wire type and recomputes from `rows` using the equations above.
- `binary_summary` is null when no prospective correctness predicate exists. Otherwise it contains exactly `correctness_rule_digest`, `N`, `PF`, `NF`, `other`, and `binary_net_flip_rate`; counts are nonnegative integers, the rate is a canonical rational, `N = PF + NF + other`, and all values recompute from the same rows.

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

`mmbu.phase1.geometry_summary` is a closed record with exactly `schema_id`, `schema_version`, `summary_id`, `example_manifest_digest`, `output_manifest_digest`, `validator_digest`, `threshold`, `rows`, `created_at`, and `record_digest`. `threshold` is a canonical rational and equals the value prospectively bound by the execution condition, validator, and prompt/schema contract; for the synthetic Phase 1 suite it is exactly `{"denominator":2,"numerator":1}`. `rows` contains every detection example exactly once in example-manifest order. Each row has exactly `example_id`, `box_policy`, `image_width`, `image_height`, `target_boxes_digest`, `predicted_boxes_digest`, `target_count`, `prediction_count`, `boxes_valid`, `matched_pairs`, `row_iou`, `passed`, and `reason_code`.

Target boxes always resolve to the manifest's valid immutable ordered array and `target_count` is its positive integer length. Prediction evidence and failure handling are closed:

- A raw terminal `runtime_failure` sets `predicted_boxes_digest`, `prediction_count`, `boxes_valid`, `matched_pairs`, and `row_iou` all null, `passed=false`, and `reason_code=runtime_failure`.
- A terminal `parse_failure` sets the same five fields null, `passed=false`, and `reason_code=parse_failure`, regardless of decoded text or a partial non-object parse. No prediction artifact or empty array is fabricated.
- For terminal `validation_failure`, `matched_pairs` and `row_iou` are null and `passed=false`. If parsed evidence contains no exact ordered prediction-box array—missing, null, scalar, object, or wrong-type member—then `predicted_boxes_digest`, `prediction_count`, and `boxes_valid` are null. If the exact array exists, its digest and nonnegative count are retained. Invalid coordinates take the more specific `invalid_prediction_box` branch below; otherwise `boxes_valid=true` and `reason_code=validation_failure` records a non-geometry schema/value failure. An empty array is evidence only when it was actually parsed; it is never fabricated.
- If a parsed prediction array exists, `predicted_boxes_digest` resolves to that exact immutable ordered parsed array before validation and `prediction_count` is its nonnegative integer length. Invalid coordinates set `boxes_valid=false`, `matched_pairs=null`, `row_iou=null`, `passed=false`, and `reason_code=invalid_prediction_box`. Valid boxes set `boxes_valid=true`. An invalid target array is structural manifest invalidity and cannot be represented as a scored row.
- Valid boxes with illegal policy cardinality set `matched_pairs=null`, `row_iou=null`, `passed=false`, and `reason_code=prediction_count_mismatch`.
- Otherwise `matched_pairs` is an array sorted by `prediction_index`, then `target_index`; each closed member has exactly zero-based integer `prediction_index`, zero-based integer `target_index`, and canonical-rational `iou`. For `single` and `any_one` it contains the one deterministic compared/best pair even below threshold, and `row_iou` equals that pair's IoU. For `all_targets`, a selected perfect matching contains every prediction and target once and `row_iou` is its canonical-rational mean. If no threshold-qualified perfect matching exists, `matched_pairs=[]`, `row_iou=null`, `passed=false`, and `reason_code=below_threshold`.
- A scored row uses only `passed` or `below_threshold`: `passed=true` iff the policy rule meets the inclusive threshold, with `reason_code=passed`; otherwise `passed=false` and `reason_code=below_threshold`.

The complete `reason_code` enum is `passed`, `below_threshold`, `runtime_failure`, `parse_failure`, `validation_failure`, `invalid_prediction_box`, and `prediction_count_mismatch`. Precedence is raw runtime failure, parse failure, missing/wrong-type array validation failure, invalid coordinate, non-geometry validation failure, policy cardinality, then scoring. These branches agree exactly with the layer statuses and judged terminal outcome in `SCHEMAS.md`; any other code, null placement, fabricated prediction array, one-based index, unsorted match vector, noncanonical rational, or transitive mismatch rejects the summary.

## Conformance vectors

These vectors are normative. Every shown rational object is already in RFC 8785 member order. `0` has only `{"denominator":1,"numerator":0}`; `1/3` has only `{"denominator":3,"numerator":1}`; and `17/24` has only `{"denominator":24,"numerator":17}`. The values `0`, `0.3333333333333333`, `"1/3"`, `{"denominator":6,"numerator":2}`, `{"denominator":-3,"numerator":-1}`, `{"denominator":2,"numerator":0}`, and either field set to a boolean must reject wherever an exact rational is required.

### Task change

| ID | Weight | Base grade/outcome | Adapted grade/outcome | Delta | State |
|---|---:|---|---|---:|---|
| `a` | 1 | 0.25 / success | 0.75 / success | 0.50 | positive |
| `b` | 2 | 0.80 / success | 0.50 / success | -0.30 | negative |
| `c` | 1 | 0.40 / success | 0.40 / success | 0 | zero |
| `d` | 2 | 1 / success | null / runtime_failure | -1 | negative |

The row deltas are respectively `{"denominator":2,"numerator":1}`, `{"denominator":10,"numerator":-3}`, `{"denominator":1,"numerator":0}`, and `{"denominator":1,"numerator":-1}`. The required totals are `example_count=4`, `weight_sum={"denominator":1,"numerator":6}`, `base_mean={"denominator":24,"numerator":17}`, `adapted_mean={"denominator":120,"numerator":43}`, `positive_mass={"denominator":12,"numerator":1}`, `negative_mass={"denominator":30,"numerator":13}`, and `net_task_change={"denominator":20,"numerator":-7}`. With a prospectively bound predicate of exact grade 1, `N=4`, `PF=0`, `NF=1`, `other=3`, and `binary_net_flip_rate={"denominator":4,"numerator":-1}`. Without that bound predicate, `binary_summary` is null. Omitting row `d`, changing its arithmetic contribution from zero, encoding its stored null grade as a fabricated zero, or using four as the weighted denominator is invalid.

### Paired conditions

Start from a valid pair whose matched-condition fields all resolve and whose adapted identity names the base model as `adapted_from_model_digest`. Mutate each matched-condition field named under **Population and layer closure**, one at a time, in either experiment or its transitive raw/run/reproducibility evidence. Every mutation must reject. Mutate each fixed `allowed_difference_fields` member name, add a sixth member, place condition data in a model-identity object, omit the adapted-to-base edge, or bind either output manifest to a third experiment; every case must reject. Changing only one or more of the five closed model-identity fields while retaining the adapted-to-base edge is the sole permitted base/adapted difference.

The one-field mutation matrix is normative. For every path below, start with one valid canonical condition; mutate exactly one leaf in only one side or its observed evidence by deletion, unknown-field insertion, wrong JSON type, illegal null, invalid enum/range, alternate array order, duplicate set member, or unequal valid value whenever that mutation applies. Each mutation must fail. Recompute all local record digests in the negative fixture so rejection proves semantic equality/completeness rather than stale hashing.

| Condition path | Leaves exercised one at a time |
|---|---|
| top level | `schema_id`, `schema_version`, `condition_id`, `created_at`, `record_digest`, plus unknown/missing top-level member and late creation |
| `request_set` | `example_manifest_digest`; every row's `example_id`, `input_digest`, `task_request_digest`, `context_request_digest`, `requested_context_fields`; row omission/addition/order |
| `components` | `prompt_schema_contract_digest`, `evaluator_digest`, `parser_digest`, `validator_digest`, `judge_policy_digest`, `geometry_threshold` and each parent/child disagreement |
| `processor` | `processor_digest`, `preprocessor_config_digest`, `template_digest`, `image_decoder_digest` including each legal-null boundary |
| `randomness` | `seed_namespace`; every stream's `name`, `seed`, `algorithm`, `version`, `derivation`, `parent_name`; derivation value/parent/formula/acyclicity; missing generation stream, duplicate, addition, order |
| `decoding` | `decoding_method`, `max_new_tokens`, `temperature`, `top_p`, `top_k`, `do_sample`, `num_beams`, `num_return_sequences`, `repetition_penalty`, each `stop_token_ids` member/order, `cache_enabled`, and every cross-field legality rule |
| `call_isolation` | `mode`, `fresh_state_per_call`, `conversation_reuse`, `kv_cache_reuse`, `task_receives_context_output`, `context_receives_task_output`, `cross_call_allowed_fields` |
| `failure_retry` | every terminal row's `terminal_outcome`, `retain_row`, rational numerator/denominator; row set/order; `retry_mode`, `maximum_attempts`, `retryable_outcomes` |
| `runtime` scalar/software/env | `os`, `architecture`, `python_executable_digest`, `python_version`, `locale`, `timezone`, `filesystem`; every software `name`/`version`/`artifact_digest`; every environment-variable `name`/`present`/`secret`/`value_digest`; set completeness/order |
| `runtime.devices/topology` | every device `device_id`/`device_type`/`model`/`ordinal`/`memory_bytes`; `world_size`, `node_count`, `process_count`, `launcher`, every visible-device member/order; device/topology consistency |
| `runtime.cache_network` | every cache/snapshot digest and order; `offline_requested`, `network_denied`, `remote_request_count`, `hidden_fetch_count`, `request_log_digest`; null/count consistency |
| `batching` | `batch_size`, `shuffle`, `drop_last`, `worker_count`, every `row_order` ID/order, every `batches` membership/boundary/order, `padding_side`, `padding_policy`, `truncation`, `max_input_tokens`, `remainder_policy`, `image_order`; request-set partition consistency |
| `precision_backend` | `parameter_dtype`, `compute_dtype`, `autocast_dtype`, `tf32`, `deterministic_algorithms`, `cudnn_benchmark`, `attention_backend`, every kernel/fallback member and order, `compile_mode`, `cache_backend`; device/decoding consistency |
| transitive bindings | experiment, pair, raw request/components/decoding, output manifest, run, and reproducibility condition digests plus every observed runtime/reproducibility projection |

### Geometry

For an image `W=100`, `H=80` and threshold `1/2`:

| Case | Target(s) | Prediction(s) | Policy | Required result |
|---|---|---|---|---|
| exact | `[10,10,20,20]` | `[10,10,20,20]` | single | pair `(0,0,1/1)`; row IoU `1/1`; `passed` |
| partial | `[10,10,20,20]` | `[20,10,20,20]` | single | pair `(0,0,1/3)`; row IoU `1/3`; `below_threshold` |
| touching | `[0,0,10,10]` | `[10,0,10,10]` | single | pair `(0,0,0/1)`; row IoU `0/1`; `below_threshold` |
| border-valid | `[0,0,100,80]` | `[0,0,100,80]` | single | pair `(0,0,1/1)`; row IoU `1/1`; `passed` |
| runtime failure | `[10,10,20,20]` | no produced value | single | prediction digest/count, validity, matches, and IoU null; `runtime_failure` |
| parse failure | `[10,10,20,20]` | no parsed value | single | prediction digest/count, validity, matches, and IoU null; `parse_failure` |
| wrong-type boxes | `[10,10,20,20]` | parsed `{"boxes":"not-an-array"}` | single | prediction digest/count, validity, matches, and IoU null; `validation_failure` |
| valid array, other invalid field | `[10,10,20,20]` | parsed `{"boxes":[[10,10,20,20]],"required_field":null}` where `required_field` must be non-null | single | exact digest of `[[10,10,20,20]]` and count one retained; validity true; matches and IoU null; `validation_failure` |
| overflow | `[90,70,10,10]` | `[90,70,11,10]` | single | exact prediction digest/count retained; matches and IoU null; `invalid_prediction_box` |
| any-one | `[0,0,10,10]`, `[20,20,10,10]` | `[20,20,10,10]` | any_one | pair `(0,1,1/1)`; row IoU `1/1`; `passed` |
| any-one-extra | same | two predictions | any_one | matches and IoU null; `prediction_count_mismatch` |
| all-reordered | `[0,0,10,10]`, `[20,20,10,10]` | `[20,20,10,10]`, `[0,0,10,10]` | all_targets | pairs `(0,1,1/1)`, `(1,0,1/1)`; row IoU `1/1`; `passed` |
| all-extra | `[0,0,10,10]`, `[20,20,10,10]` | same two plus `[40,40,10,10]` | all_targets | matches and IoU null; `prediction_count_mismatch` |
| exact tie | two targets both `[0,0,10,10]` | two predictions both `[0,0,10,10]` | all_targets | choose lexicographic pairs `(0,0,1/1)`, `(1,1,1/1)`; row IoU `1/1`; `passed` |

In the table, `N/D` denotes the exact JSON object `{"denominator":D,"numerator":N}` and each tuple denotes `{"iou":N/D,"prediction_index":p,"target_index":t}` after canonical member ordering.

The exact tie's `matched_pairs` bytes are `[{"iou":{"denominator":1,"numerator":1},"prediction_index":0,"target_index":0},{"iou":{"denominator":1,"numerator":1},"prediction_index":1,"target_index":1}]`. A runtime-failure projection is `{"boxes_valid":null,"matched_pairs":null,"passed":false,"predicted_boxes_digest":null,"prediction_count":null,"reason_code":"runtime_failure","row_iou":null}`; the parse-failure and wrong-type validation projections differ only by their respective `reason_code`. For a parsed valid-coordinate array with another invalid field, the projection instead retains its exact prediction digest/count and sets `boxes_valid=true`. An invalid-box or count-mismatch row retains a non-null exact prediction digest and count but has `matched_pairs=null` and `row_iou=null`; substituting an empty match array in any validation, invalid-box, or count-mismatch case rejects.

Negative width/height, nonfinite coordinates, swapped frame dimensions, normalized-coordinate reinterpretation, target reuse, and a threshold chosen after outputs are all invalid.

## Claim boundary

Passing these mechanics proves only that synthetic or duly authorized evaluation records obey this contract. It is not evidence of official-harness equivalence, biomedical validity, model performance, or private-set generalization. Unknown official behavior remains `brief_snapshot` or unresolved, never silently upgraded.
