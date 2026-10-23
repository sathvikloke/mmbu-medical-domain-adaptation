# Competition-first immutable manifest specification

**Date:** October 18, 2026  
**Evidence class:** design only  
**Purpose:** make the B0/B1/B2 experiment executable without allowing hidden defaults or public-set selection

## State machine

The manifest has exactly these forward states:

```text
draft
  -> authority_blocked | data_blocked | native_preflight_ready | retired
authority_blocked | data_blocked
  -> retired
native_preflight_ready
  -> native_preflight_failed | experiment_freeze_ready
experiment_freeze_ready
  -> frozen
frozen
  -> execution_failed | executed | retired
executed
  -> confirmation_opened
confirmation_opened
  -> promoted | no_eligible_candidate | retired
```

Unknown authority, data, model, hardware, or evaluator fields prevent the relevant forward transition. Validation never
returns to development. Any post-opening change retires the manifest and requires a new independent confirmation
population; it may not overwrite the old record.

## Required top-level fields

```yaml
manifest_version: string
manifest_id: string
schema_id: string
schema_version: integer
created_at_utc: string
evidence_class: design_only | synthetic_only | native_preflight | biomedical_experiment
state: enum_above
authority_snapshot_id: string
artifact_registry_digest: sha256
scientific_decision_receipt_id: sha256_or_unknown
protocol_contract_id: string
protocol_equivalence: synthetic | proxy | official
public_firewall_policy_id: string
base_selection_receipt_id: sha256_or_unknown
selected_base_digest: sha256_or_unknown
model_pin: object
data_plan: object
candidate_universe: list
training_contract: object
evaluation_contract: object
promotion_contract: object
research_comparison_registry: object
release_contract: object
unknowns: list
canonical_digest: sha256
```

Canonical bytes are RFC 8785 JSON produced from a closed, versioned typed schema; the YAML above is explanatory only.
Scientific rationals use reduced integer numerator/positive-denominator objects. Lists remain ordered unless the schema
declares a sorted-set field. Compute `canonical_digest` as lowercase SHA-256 over the canonical object with that field
omitted. Every referenced ID resolves through an artifact registry to path, SHA-256, and media type. A normative
cross-field decision table and negative fixtures accompany the schema; prose cannot broaden what the schema accepts.

`official` protocol equivalence is structurally forbidden until the raw prompt/schema bytes, context pass, evaluator,
generation/runtime settings, malformed-output precedence, and multi-label behavior are authoritative and hash-bound.
`experiment_freeze_ready` additionally requires a valid upstream base-selection receipt under
[BASE_SELECTION_FRONTIER.md](BASE_SELECTION_FRONTIER.md), unless a reviewed authority decision fixes a single eligible
base before comparative results and records why no selection was performed.

## Model pin

Required fields:

- repository/model identifier, immutable revision, local cache digest, license, and source receipt;
- processor/tokenizer identifiers and immutable revisions;
- image resize, pad, crop, normalization, and original-to-model coordinate transform;
- dtype, quantization, attention backend, thinking mode, generation settings, token limits, and dependency lock;
- allowed loader and `trust_remote_code` policy;
- observed native module names/shapes with source spans; and
- every unobserved item explicitly `unknown`.

No undeclared runtime module or tensor shape may appear. Adapter/projector modules absent from the base tree require an
explicit candidate schema, complete state-dict inventory, synthetic save/load coverage, and an organizer-compatible
loader/package receipt before promotion; base-tree absence alone neither authorizes nor categorically forbids them.

## Data plan

```yaml
source_ledger_digest: sha256_or_unknown
admitted_source_ids: []
independent_unit_key: string_or_unknown
split_group_keys: []
duplicate_policy_id: string
frontier_train_role_ids: []
frontier_tuning_role_ids: []
frontier_decision_role_ids: []
recipe_train_role_ids: []
recipe_development_role_ids: []
recipe_confirmation_role_ids: []
visual_probe_construction_role_ids: []
visual_probe_audit_role_ids: []
role_disjointness_matrix_digest: sha256_or_unknown
held_out_source_ids: []
prompt_lineage_groups: []
task_view_manifest_digest: sha256_or_unknown
context_field_schema_id: string_or_unknown
context_availability_mask_schema_id: string_or_unknown
independent_unit_loss_policy_id: string_or_unknown
human_review_receipt: sha256_or_unknown
rights_receipts: []
```

The validator implements the [independent-unit exposure audit](UNIT_EXPOSURE_AUDIT_SPEC.md) and rejects view generation before grouping/splitting, any duplicate/patient/study/specimen/source-parent
crossing, public MMBU inputs, unreviewed label invention, counts from incomplete instance sets, context inferred from
source/path/prompt correlations, or a view-weight plan whose total mass deviates by more than 1% across independent
units before prospective source/task/context balancing.

## Frozen candidate universe

Every candidate includes:

```yaml
candidate_id: unique_string
architecture_id: recipe_arch::B0 | recipe_arch::B1-L | recipe_arch::B2-P | recipe_arch::B2-F
objective_profile_id: null_for_B0_or_registered_profile_id
enabled: bool
enablement_rule: string
base_revision: string
adapter_type: none | lora
target_modules: []
rank: integer_or_unknown
alpha: number_or_unknown
dropout: number_or_unknown
trainable_parameter_formula: string
expected_trainable_parameters: integer_or_unknown
active_flop_formula: string
optimizer_condition_id: string
artifact_layout_id: string
```

`candidate_id` names one architecture/objective-profile pair; two loss allocations are two candidates, not an
unrecorded hyperparameter inside one candidate. `recipe_arch::B0` has no training objective profile.
`recipe_arch::B2-F` is disabled unless the exact pre-output F0 synthetic workload, memory-headroom, wall-time, repeat,
and zero-OOM predicates in the scientific-decision receipt pass. Its Boolean and profile digest are committed before
any biomedical output. Confirmation results can never enable it. New candidates or profiles cannot be created after
`frozen`.

## Training contract

- fixed optimizer name and exact hyperparameters;
- scheduler, warmup, clipping, precision, accumulation, per-source/task sampling weights, and maximum updates;
- immutable seeds and deterministic/nondeterministic receipt policy;
- target construction and loss masking, including rationale policy and terminal JSON object;
- separate byte-level `training_target_format_id` and `inference_output_format_id`, including rationale-prefix,
  terminal-object extraction, duplicate-object, whitespace, trailing-text, and failure-precedence rules;
- separate answer-task and authoritative-context objectives, per-field availability masks, frozen aggregation, and
  per-independent-unit total loss-mass normalization;
- static/forward/reverse/shuffled schedule IDs with exposure equivalence when curriculum order is evaluated;
- effective-step weighted numerator/denominator aggregation plus accumulation/distributed/resume receipts from the
  [unit-exposure audit](UNIT_EXPOSURE_AUDIT_SPEC.md);
- base-preservation population, coefficient, and negative-flip metric;
- checkpoint frequency, early-stop statistic, tie rule, and maximum retained checkpoints;
- public-firewall assertion; and
- optional A1 numeric-distance and A2 text-prior weighting conditions disabled by default with prospective enablement
  rules.

An `unknown` value blocks `frozen`; it is never filled from confirmation or public-set behavior.

`rationale_policy` is one of `answer_only_training` or `source_supported_rationale`. The latter requires immutable
source-text, derivation-authority, rights, and answer-consistency receipts for every applicable record. Model-generated
rationales, label-to-template rationales, and rationales inferred from metadata are structurally forbidden. An
answer-only training condition may be evaluated for output-format robustness, but it cannot claim rationale supervision
or official prompt equivalence.

## Dual-objective profile

Every non-B0 `objective_profile_id` resolves to one closed object:

```yaml
profile_id: string
task_target_contract_id: string
context_target_contract_id: string
context_protocol_status: design_only | context_proxy_executable | context_official_equivalent
organizer_confirmed_applicability_mask_rule: bool
requested_field_registry_digest: sha256
zero_applicable_training_policy: reallocate_context_share_to_task | organizer_bound_policy
zero_applicable_evaluation_policy: exclude_and_report | organizer_bound_policy
unit_total_mass: canonical_positive_rational
task_unit_share: canonical_nonnegative_rational
context_unit_share: canonical_nonnegative_rational
task_view_normalization: equal_within_unit | registered_fixed_map
context_field_normalization: equal_available_fields | registered_fixed_map
source_balance_policy_id: string
task_balance_policy_id: string
context_balance_policy_id: string
schedule_id: static | forward | reverse | shuffled
token_normalization_id: string
exposure_audit_tolerance: canonical_rational_at_most_1_over_100
```

The task and context shares sum exactly to one in canonical rational arithmetic. The applicability flag records only
the October 14 confirmation that prompts request applicable fields; it does not upgrade the proxy prompt, registry,
key schema, unknown/zero-field behavior, parser, or scoring. `context_unit_share > 0` for the
dual-objective flagship; a task-only profile is a named control, not the flagship. Under the local proxy, a
zero-applicable-field unit receives no context target, reallocates that share to task, and is excluded-and-reported for
context evaluation. Missing-field count, answer length, view count, and annotation density cannot change total unit
mass. An organizer-bound successor may replace both policies explicitly.

The validator rejects a profile that copies `0.8/0.2` from the score without a registered loss-scale rationale, uses a
floating-point value where a canonical rational is required, invents an official field registry, changes field weights
after results, or compares schedules with unequal units, target tokens, optimizer updates, seeds, templates, or total
mass. A small closed allocation set is allowed only when every architecture/profile pair and comparator is declared
before any result opens.

## Geometry and serializer invariants

For every geometry-bearing view bind:

- original image hash and dimensions;
- source coordinate convention;
- processor transform chain and inverse;
- final original-pixel `xywh` target;
- parse/serialize/inverse-round-trip tolerance; and
- golden fixture suite digest.

For every output profile bind system/user prompt bytes, rationale policy, terminal JSON schema, parser, failure policy,
generation settings, and digest chain. Malformed committed JSON is locally incorrect and never repaired.

## Visual-dependence probes

Each candidate/checkpoint uses identical independent units for:

```yaml
normal_image
blank_or_interface_supported_no_image
answer_preserving_visual_intervention
answer_changing_paired_image_intervention
answer_preserving_overlay_jitter
answer_changing_source_annotated_region_pair
```

The contract freezes task/source applicability, source-authoritative target rule for both sides of each pair,
construction seed, compatibility stratum, statistic, resampling groups, practical tolerance, and failure rule. Blank
or no-image behavior is descriptive and cannot be maximized. Promotion conjunctively requires normal competence,
answer-preserving invariance, and answer-changing target tracking to meet their simultaneous bounds. Inapplicable probes
remain missing-by-design and cannot be imputed. Accuracy or prompt consistency cannot override failure.

## Evaluation and promotion

The evaluation contract freezes:

- primary metric vector and scalar contrast;
- macro-source, macro-task, held-out-source, held-out-template, and held-out-combination slices;
- malformed-output, negative-flip, visual-dependence, cost, and packaging outcomes;
- independent-unit/source-group bootstrap hierarchy, shared resample seeds, confidence level, simultaneous max-stat
  family, and zero/nonfinite behavior;
- practical margins versus B0 and the simpler candidate, plus an explicit exposure-matched primary comparison and
  measured-compute sensitivity comparison;
- an immutable candidate-specific comparator map keyed by `candidate_id`; every enabled non-B0 candidate compares with
  B0, the simpler enabled architecture under the same objective profile where one exists, and any task-only/static
  control required to isolate its objective/schedule claim;
- deterministic tie/failure rule; and
- one `recipe_confirmation` opening receipt, the promotion-candidate checkpoint digest, and the frozen checkpoint
  digest for every comparator in its closure.

A candidate/checkpoint is selected on development before confirmation opens. It is promoted only if every primary,
non-regression, visual-dependence, packaging, and resource predicate is true. If it fails, the result is
`no_eligible_candidate`; the evaluator cannot relax a margin, select the least bad failure, or try the runner-up on the
same confirmation population. Only the named promotion candidate can be promoted from that opening.

For dual-objective candidates, the metric vector includes task `T`, context `C`, every sufficiently supported requested
context field, local-proxy requested-key-set validity, zero-applicable-field count, malformed rate, and the prospective
score proxy. Requested-key-set validity is not organizer-confirmed scoring behavior until the final context contract is
bound.
Neither the scalar proxy nor a task gain may conceal a failed context minimum. While the official context protocol is
unavailable, report the registered partial-identification/sensitivity result and do not relabel a proxy winner an
official winner.

## Disabled research-comparison registry

The primary B0/B1/B2 manifest requires one closed `research_comparison_registry`. It may be empty. Schema version 1 is
permanently representation-only: every entry has literal `status: design_only_disabled` and `enabled: false`. It cannot
add a competition candidate, open a population, authorize a model/data/GPU action, delay Lane 1, or change the primary
promotion rule. It has no transition to an executable state. Any future execution requires a separately versioned
research-execution schema and manifest, independent authority/run receipts, fresh custody and opening controls, and a new
review; it may not mutate or reinterpret this competition-manifest registry. Claude may implement only the v1 schema,
cross-field validators, and synthetic negative fixtures.

`entries` is a unique, UTF-8 `claim_id`-sorted set with at most one H1, one H2, and one composite object. A composite
resolves the exact H1 and H2 IDs in the same registry or rejects. No generic `mmbu.phase1.experiment`, prospective lock,
or decision receipt may name `SYS-A*` or `FRONTIER-*` as an executable candidate through this v1 object. A future
research-execution schema must transitively bind the competition-manifest digest, registry digest, immutable arm
contracts, independent execution-authority receipt, candidate enablement, custody/role manifests, and opening registry;
candidate IDs and decision receipts must cross-validate through those bindings. Until that separately implemented and
reviewed schema exists, the absence of a typed binding is an execution blocker, not permission to use the generic Phase 1
experiment path.

The registry contains exactly:

```yaml
schema_id: mmbu.competition.research_comparison_registry
schema_version: 1
entries: []
```

Each entry is one of the following closed objects. Every map shown below has exactly the displayed keys; arrays cannot
substitute for keyed scientific assignments.

### H1 training-interaction object

```yaml
claim_id: system::H1_context_x_unit_mass
status: design_only_disabled
enabled: false
arm_contract_ids:
  SYS-A0: sha256_or_unknown
  SYS-A1: sha256_or_unknown
  SYS-A2: sha256_or_unknown
  SYS-A3: sha256_or_unknown
base_digest: sha256_or_unknown
source_parent_ids: []
source_parent_role_map_id: string_or_unknown
train_role_ids: []
development_role_ids: []
confirmation_role_ids: []
role_disjointness_matrix_digest: sha256_or_unknown
cross_lane_role_disjointness_digest: sha256_or_unknown
confirmation_opening_rule_id: string_or_unknown
confirmation_opening_receipt_id: sha256_or_unknown
budget_estimand: fixed_total_supervised_tokens
arm_exposure_contract_ids:
  SYS-A0: string_or_unknown
  SYS-A1: string_or_unknown
  SYS-A2: string_or_unknown
  SYS-A3: string_or_unknown
answer_target_contract_id: string_or_unknown
context_target_contract_ids:
  SYS-A1: string_or_unknown
  SYS-A3: string_or_unknown
primary_estimand_ids:
  task: string_or_unknown
  context: string_or_unknown
minimum_effect_ids:
  task: string_or_unknown
  context: string_or_unknown
common_gate_contract_ids:
  positive_flips: string_or_unknown
  negative_flips: string_or_unknown
  normal_image: string_or_unknown
  answer_preserving_visual_invariance: string_or_unknown
  answer_changing_target_tracking: string_or_unknown
  preservation_nonregression: string_or_unknown
  invalid_output_rate: string_or_unknown
  cost: string_or_unknown
independent_unit_id: string_or_unknown
resampling_hierarchy_id: string_or_unknown
multiplicity_rule_id: string_or_unknown
replication_plan_id: string_or_unknown
replication_parent_rows: []
natural_exposure_contract_id: string_or_unknown
equalized_exposure_contract_id: string_or_unknown
duplication_perturbation_contract_id: string_or_unknown
supervised_token_match_contract_id: string_or_unknown
optimizer_update_match_contract_id: string_or_unknown
compute_match_contract_id: string_or_unknown
decision_function_id: string_or_unknown
kill_function_id: string_or_unknown
scientific_decision_receipt_id: sha256_or_unknown
```

Each arm contract binds its arm ID to one immutable objective profile, unit-normalization policy, base/candidate digest,
serializer, optimizer, seeds, checkpoint policy, and eventual checkpoint-artifact slot. The validator requires exactly
the factorial mapping in [SYSTEM_INTERACTION_HYPOTHESIS.md](SYSTEM_INTERACTION_HYPOTHESIS.md); labels alone are not
authority. All arms use the same units, base answer prompt/target bytes, evaluation prompts, and global summed objective-
loss/optimizer budget. They intentionally do not use the same per-unit allocation vector: `SYS-A0`/`SYS-A1` assign unit
mass in proportion to authorized row/view exposure, whereas `SYS-A2`/`SYS-A3` assign equal mass per independent unit.
`budget_estimand` is intentionally one estimand: context receives a prospectively frozen portion of a fixed total
supervised-token budget in `SYS-A1`/`SYS-A3`, displacing the same amount of a frozen repeated-answer-loss schedule used
by `SYS-A0`/`SYS-A2`. The keyed exposure contracts bind per-arm answer tokens, context tokens, global summed objective-
loss mass, the complete per-unit allocation vector, updates, active FLOPs, and compute. This estimates context allocation
under a fixed total budget; it does not claim fixed answer exposure plus free additional context. Any other estimand
requires a future separately reviewed schema.

Context prompt/target bytes are bound only for `SYS-A1` and `SYS-A3`; all arms are evaluated on identical task and
context endpoints. Total supervised tokens, optimizer updates, active FLOPs, and compute must match prospectively or H1
is `nonidentified`. Task and context estimands and minimum effects remain separate. Every common gate above is mandatory
and the decision/kill functions must resolve and bind all eight; a generic function ID cannot omit one. The answer-
preserving visual-invariance gate is distinct from ordinary normal-image competence, and preservation nonregression is
not implied merely by a negative-flip count. No scalar composite
can substitute for either primary interaction decision or any common gate.

The equalized-exposure check applies pairwise within context level: `SYS-A0` versus `SYS-A2`, and `SYS-A1` versus
`SYS-A3`. Within each pair it equalizes views, supervised tokens, objective-bearing fields, sampling probability, and
update opportunity. It does not remove the context factor across pairs. Its frozen predictions are pairwise equivalence
and interaction compatible with zero inside a pre-output margin. The duplication check adds no independent unit or
semantic target, mechanically receipts row-uniform weight perturbation, and requires unit-normalized invariance under
matched tokens, updates, and compute. Row-uniform endpoint direction is only a hypothesis unless independently derived
before outputs.

Every `replication_parent_rows` element is a closed row containing exactly `source_parent_id`,
`governance_authority_id`, `confirmation_role_ids`, `task_interaction_estimand_id`,
`context_interaction_estimand_id`, and `interaction_decision_receipt_id`; rows are unique and sorted by source-parent ID.
A valid H1 object requires at least two such rows with different source-parent and governance-authority IDs. Each row must
contribute its own confirmatory task and context interaction estimate. Those confirmation roles are disjoint from all
training, tuning, and development roles; development evidence never counts toward the two-parent replication minimum.

The role matrix and source-parent map reject independent-unit, duplicate-group, source-parent, and prompt-lineage overlap
across H1 roles and between H1 confirmation, H2 cohorts, and Lane 1 `recipe_confirmation`. A future execution manifest
could not be authorized without the two independently governed confirmatory parents, a separately bound one-opening
receipt, and complete custody. Modalities, strata, or subsets from one parent do not count as replication.

### H2 selection-protocol object

```yaml
claim_id: system::H2_adaptation_response_selection
status: design_only_disabled
enabled: false
arm_contract_ids:
  FRONTIER-U: sha256_or_unknown
  FRONTIER-R: sha256_or_unknown
eligible_base_universe_id: string_or_unknown
micro_adaptation_screen_id: string_or_unknown
frontier_train_role_ids: []
frontier_tuning_role_ids: []
first_decision_role_ids: []
second_untouched_role_ids: []
source_parent_role_map_id: string_or_unknown
role_disjointness_matrix_digest: sha256_or_unknown
cross_lane_role_disjointness_digest: sha256_or_unknown
untouched_selection_function_id: string_or_unknown
response_selection_function_id: string_or_unknown
selected_base_rows:
  FRONTIER-U:
    selected_base_digest: sha256_or_unknown
    selection_receipt_id: sha256_or_unknown
  FRONTIER-R:
    selected_base_digest: sha256_or_unknown
    selection_receipt_id: sha256_or_unknown
second_cohort_opening_rule_id: string_or_unknown
second_cohort_opening_receipt_id: sha256_or_unknown
second_cohort_opening_registry_digest: sha256_or_unknown
second_cohort_population_manifest_digest: sha256_or_unknown
primary_base_selection_separation_rule_id: string_or_unknown
primary_estimand_id: string_or_unknown
minimum_effect_id: string_or_unknown
resampling_hierarchy_id: string_or_unknown
multiplicity_rule_id: string_or_unknown
decision_function_id: string_or_unknown
kill_function_id: string_or_unknown
scientific_decision_receipt_id: sha256_or_unknown
```

The two arm contracts bind immutable selection functions, candidate universes, screen contracts, selected-base receipt
slots, and cohort rules. H2 is eligible only when `FRONTIER-U` and `FRONTIER-R` select different immutable bases before
the one-opening second untouched cohort, and `FRONTIER-R` then wins under the frozen H2 decision function. H1 success
cannot rescue H2 failure and H2 success cannot rescue H1 failure. The role matrices reject any independent-unit,
duplicate-group, source-parent decision group, or prompt-lineage overlap with selection populations, H1 confirmation, or
Lane 1 `recipe_confirmation`. Neither keyed H2 selection receipt nor selected-base digest may equal, satisfy, supersede,
or flow into the top-level competition `base_selection_receipt_id` or `selected_base_digest`; the separation-rule ID and
validator enforce that H2 is research-only rather than a back door into the competition base choice.

### Optional composite-protocol object

```yaml
claim_id: system::COMPOSITE_PROTOCOL
status: design_only_disabled
enabled: false
h1_claim_id: system::H1_context_x_unit_mass
h2_claim_id: system::H2_adaptation_response_selection
full_system_artifact_contract_id: string_or_unknown
system_binding_contract_id: string_or_unknown
complete_system_comparator_map_id: string_or_unknown
primary_superiority_estimand_id: string_or_unknown
minimum_effect_id: string_or_unknown
resampling_hierarchy_id: string_or_unknown
multiplicity_rule_id: string_or_unknown
decision_function_id: string_or_unknown
eligibility_function_id: string_or_unknown
scientific_decision_receipt_id: sha256_or_unknown
```

The system-binding contract transitively requires the full-system artifact to use the immutable base selected by the H2
`FRONTIER-R` row, implement the exact H1 `SYS-A3` objective and unit-normalization contracts, and use the same serializer,
evaluation contract, and budgeted system definition evaluated against the complete-system comparators. Any digest or
contract mismatch rejects composite eligibility even when H1 and H2 pass separately. The comparator map includes the
ordinary shared answer-only system, a faithful matched FLARE-style system, a matched
Two-Stage Mixture-of-LoRA system, and MedQwen only when implementable from available evidence. An unavailable published
comparator is `not_implementable_from_available_evidence`, never silently replaced. Composite eligibility requires H1
and H2 to pass separately and the full system's frozen superiority contrast and simultaneous decision to beat the
strongest faithfully matched complete-system comparator. Comparator failure does not erase an isolated H1 result. The
composite creates no pooled H1/H2 statistic and no novelty bonus merely because both pass.

### Required negative fixtures

Schema review is incomplete unless deterministic synthetic fixtures reject each of the following. `[F]` fixtures belong
to package F's shared registry/H1 schema module; `[G]` fixtures belong to package G's H2 module; and `[I]` fixtures belong
to a post-F/G integration module that consumes both implementations read-only. Every negative fixture starts from a
fully valid synthetic registry and mutates exactly one field or relationship, so an earlier unrelated rejection cannot
masquerade as the intended test. The frozen specification is read-only during implementation; package-specific code and
tests must not mix purposes.

1. `[F]` any v1 entry whose status or `enabled` literal changes, or any attempt to treat v1 as execution authority;
2. `[F]` missing, duplicate, renamed, or fifth H1 arm;
3. `[F]` an arm label whose contract binds the wrong objective, normalization policy, base, serializer, optimizer, seed, or
   checkpoint slot;
4. `[F]` a context-training target in `SYS-A0` or `SYS-A2`, or a missing/swapped `SYS-A1`/`SYS-A3` context contract;
5. `[F]` an exposure map not using the fixed-total-supervised-token estimand, not binding every arm, or not explicitly
   recording the displaced repeated-answer schedule;
6. `[F]` unequal total supervised tokens, global summed objective-loss/optimizer budget, optimizer updates, active FLOPs,
   or compute across H1 arms, or an arm whose per-unit allocation vector does not match its row-uniform versus
   independent-unit-normalized contract;
7. `[F]` one scalar replacing the separate task and context interactions or a missing minimum-effect assignment;
8. `[F]` any missing positive-flip, negative-flip, normal-image, answer-preserving visual-invariance, answer-changing,
   preservation-nonregression, invalid-output, or cost gate;
9. `[F]` an equalized-exposure check that compares across context levels, omits an optimizer-relevant exposure, or predicts
   continued H1 advantage rather than pairwise equivalence/null;
10. `[F]` a duplication check that adds an independent unit, semantic target, or unmatched exposure;
11. `[F]` any H1 role overlap by unit, duplicate group, source parent, or prompt lineage, including reuse of Lane 1 confirmation;
12. `[F]` fewer than two independently governed confirmatory replication parents, any replication parent reused for
    training/tuning/development, or two replication strata derived from one governed source parent;
13. `[F]` an unkeyed, incomplete, reordered, or swapped H1 arm/endpoint assignment;
14. `[I]` a missing complete-system comparator silently replaced by an easier method;
15. `[I]` a composite superiority decision missing its full-system artifact, estimand, minimum effect, resampling, multiplicity,
   or decision function;
16. `[G]` `FRONTIER-U` and `FRONTIER-R` selecting the same base while H2 passes;
17. `[G]` opening the second H2 cohort before both keyed `selected_base_rows` and the opening registry are immutable;
18. `[I]` H1 evidence used to rescue H2, H2 evidence used to rescue H1, or either result pooled post hoc;
19. `[F]` any public MMBU example, label, output, derivative, or public-driven choice entering any research object;
20. `[F]` any research object changing the primary competition candidate universe, promotion result, or schedule;
21. `[G]` any H2 cohort overlap with H1 confirmation or Lane 1 `recipe_confirmation`;
22. `[I]` duplicate claim IDs, noncanonical entry order, more than one object of a claim type, or a composite reference
    not resolved in the same registry;
23. `[G]` an incomplete/swapped arm-to-base-to-receipt row, or any H2 receipt/digest satisfying the primary competition
    base-selection fields; and
24. `[F]` a generic Phase 1 experiment, lock, or decision receipt attempting to execute a v1 research arm without the
    separately versioned transitive research-execution binding and authority receipt; and
25. `[I]` a composite whose full-system artifact does not transitively bind the H2 `FRONTIER-R` selected base, the H1
    `SYS-A3` objective/normalization contracts, and the comparator-matched serializer/evaluation/budget definition.

A passing synthetic registry proves only that the hypotheses are representable without hidden defaults. It does not
freeze scientific values, establish source support, authorize execution, or provide evidence that either hypothesis is
true.

## Release contract

Bind the immutable artifact inventory, state-dict closure, dependency lock, allowed loader, offline-load command,
network-denied environment, two independent clean processes using the same frozen generation seed, exact deterministic
token/raw-byte equivalence or a prospectively named field-level tolerance for permitted nondeterminism, runtime/memory/artifact ceilings,
disclosures, human approval receipt, upload verification, and rollback identity. Unknown official limits block release
but do not rewrite the experiment.

## Transition-specific blockers

Do not collapse every unknown into one global stop. Each transition has its own authority boundary:

- `native_preflight_ready` requires a verified MOCS connection/allocation plus the pinned model, processor, dependency,
  cache, module-tree, synthetic input, load/forward/export/reload, memory, and timing contract. It does **not** require
  biomedical data, a final context prompt, or an official evaluator.
- `experiment_freeze_ready` additionally requires admitted training and independently grouped held-out source families
  sufficient for every claimed source-level estimand, immutable views/splits, a named task-protocol proxy, exact
  rationale policy, candidate modules, budgets, margins, and resource plan. Candidate choice may use context only at
  `context_proxy_executable` or `context_official_equivalent`. At proxy status, the complete local proxy and its
  prospective sensitivity/robust-dominance rule must be hash-bound; selection may use registered proxy components and
  the score interval over the frozen admissible official-context range, but never an unbound official-context point
  estimate or an official-equivalence claim. At `design_only`, context is non-binding and no candidate choice may use
  it.
- `confirmation_opened` requires the frozen comparator map, promotion candidate plus every comparator checkpoint,
  untouched population,
  opening receipt, and every binding development predicate. A later official-protocol change cannot be evaluated on
  this population and then fed back into development.
- release or any `official`-equivalence claim additionally requires authoritative task and context bytes, malformed-
  output and segmentation/multi-label precedence, official loader, hardware/runtime/dependency/token/image/artifact
  limits, exact form and cutoff, and a successful fresh-load rehearsal.

The exact [experiment-freeze contract](EXPERIMENT_FREEZE_CONTRACT.md) additionally governs canonical identity,
scientific-decision ownership, role partitions, exposure, decision functions, resource caps, output/geometry closure,
and package/workflow ordering.

The project currently fails the first transition because MOCS connectivity/allocation and the native pinned-model
receipt are absent. The unresolved official context and evaluator contract block `context_official_equivalent` and
release, not a fully bound `context_proxy_executable` experiment or the mechanically independent native preflight.
Unknowns remain unknown; no transition may borrow authority from a later stage or fill a field with a common default.
