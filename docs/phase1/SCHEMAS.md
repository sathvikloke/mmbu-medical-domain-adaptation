# Phase 1 schema contract

**Status:** binding field-level design contract; executable validators remain unimplemented  
**Frozen:** 2026-10-14  
**Scope:** governance and evidence records only; official task/context output keys remain behind a versioned prompt/schema adapter

## Common rules

Every JSON object below is UTF-8 without BOM, rejects duplicate keys and nonfinite numbers, and rejects unknown keys unless a field explicitly contains an open metadata object. Schema IDs use the exact `mmbu.phase1.<name>` strings below and `schema_version` is integer `1`. Timestamps are RFC 3339 UTC strings ending in `Z`; chronology compares parsed instants, never lexical local time. Digests are lowercase 64-character SHA-256 hex over the named canonical domain.

Canonical JSON is RFC 8785. A `record_digest` is SHA-256 of the canonical object with only its top-level `record_digest` field omitted. No other field is omitted. File digests cover raw bytes. IDs are opaque nonempty strings and never substitute for digests.

Normalized repository and evidence paths are nonempty relative POSIX paths: no leading slash, backslash, empty component, `.`, `..`, NUL, Unicode-normalization alias, case-fold collision, symlink, hard-link alias, or directory entry. Arrays are ordered unless stated otherwise. Set-like arrays are unique and sorted by UTF-8 bytes before canonicalization.

The canonical enums are:

- purpose: `engineering`, `quarantine_inspection`, `train`, `adaptive_dev`, `confirmation`, `official_audit`, `release`;
- origin: `mmbu_official`, `mmbu_derivative`, `official_rule_summary`, `external_reviewed`, `external_quarantine`, `synthetic_engineering`, `unknown`;
- claim status: `verified`, `failed`, `untested`, `blocked_external`;
- contract status: `synthetic`, `brief_snapshot`, `organizer_confirmed`;
- edge role: `governance`, `data`, `model`, `prompt`, `processor`, `judge`, `decision`;
- phase decision: `accepted`, `returned_blocked`, `rejected`.

`null` is allowed only where explicitly named. Missing and null are not interchangeable.

## `mmbu.phase1.lineage_receipt`

Required fields:

| Field | Type | Rule |
|---|---|---|
| `schema_id`, `schema_version` | string, integer | Exact common values. |
| `lineage_id` | string | Unique opaque ID. |
| `artifact_digest` | digest | Child artifact raw-byte or canonical-record digest. |
| `origin_class` | origin enum | `unknown` fails promotable purposes. |
| `allowed_purposes` | array of purpose enum | Unique sorted array; empty is legal and denies use. |
| `parents` | array of object | Each object has exactly `parent_digest` and `edge_role`; unique pair, sorted by digest then role. |
| `source_version`, `rights_receipt_digest`, `grouping_receipt_digest`, `qa_receipt_digest` | digest or null | Non-null for `external_reviewed` in real model-use purposes. |
| `created_at` | UTC timestamp | Receipt creation. |
| `record_digest` | digest | Canonical record digest. |

The effective allowed-purpose set is the intersection of the child declaration and every content-bearing ancestor reached through `data`, `model`, `prompt`, `processor`, `judge`, or `decision` edges. A pure `governance` edge is excluded only when its target validates as `official_rule_summary`; relabeling content or decisions as governance fails. Cycles, missing parents, an `unknown` ancestor, public/derivative ancestry in a promotable purpose, or an empty intersection reject use.

## `mmbu.phase1.source`

Required fields: `schema_id`, `schema_version`, `source_id`, `source_version`, `source_family`, `origin_class`, `status`, `artifact_manifest_digest`, `rights_receipt_digest`, `grouping_receipt_digest`, `qa_receipt_digest`, `allowed_purposes`, `reviewer_id`, `created_at`, `reviewed_at`, `supersedes_digest`, and `record_digest`.

`status` is `candidate`, `quarantined`, `approved`, or `rejected`. `candidate` has empty `allowed_purposes`. `quarantined` may allow only `quarantine_inspection` and may leave receipt digests, reviewer, and review time null. `approved` requires all three receipt digests plus reviewer/review time and at least one allowed purpose. `rejected` has no allowed purposes. A transition creates a new record that binds the previous record in `supersedes_digest`; the first record uses null. Source identity/version/family and artifact manifest cannot mutate across a transition—changed bytes or upstream version create a new source lineage. Official/derivative origins can never gain a promotable purpose.

## `mmbu.phase1.split`

Required fields: `schema_id`, `schema_version`, `split_id`, `source_digest`, `source_artifact_manifest_digest`, `role`, `record_manifest_digest`, `parent_namespace`, `parent_ids_digest`, `record_ids_digest`, `construction_rule_digest`, `created_at`, and `record_digest`.

`role` is `engineering`, `train`, `adaptive_dev`, `confirmation`, `official_audit`, or `quarantine`. The record and parent-ID manifests are immutable sorted sets; one biomedical parent cannot cross `train`, `adaptive_dev`, or `confirmation` in a source family. A split references one validated source record and exact source artifact manifest. Any record membership, parent mapping, or construction-rule change creates a new split digest. `official_audit` and `quarantine` cannot be consumed by a promotable purpose.

## `mmbu.phase1.purpose_authorization`

Required fields: `schema_id`, `schema_version`, `authorization_id`, `purpose`, `source_digest`, `split_digests`, `lineage_root_digests`, `decision`, `decision_basis_digests`, `reviewer_id`, `decided_at`, `expires_at`, `supersedes_digest`, and `record_digest`.

`decision` is `allowed`, `denied`, or `blocked_external`; `expires_at` is a UTC timestamp or null. Only `allowed` authorizes use, and it must be a subset of the source record's `allowed_purposes`, satisfy the closed purpose/split table below, and survive lineage intersection. `reviewer_id` and nonempty basis digests are mandatory. A changed purpose, source, split, lineage, decision, or expiry creates a successor; revocation/expiry never edits the earlier record. `blocked_external` and `denied` fail closed.

Purpose and split remain distinct fields. Their only legal combinations are:

| Purpose | Permitted split roles |
|---|---|
| `engineering` | `engineering` |
| `quarantine_inspection` | `quarantine` |
| `train` | `train` |
| `adaptive_dev` | `adaptive_dev` |
| `confirmation` | `confirmation` |
| `official_audit` | `official_audit` |
| `release` | `train`, `adaptive_dev`, or `confirmation` already present in the released model's validated lineage; no new data access is authorized |

Every authorization and source record must be an active leaf at run `started_at`: its expiry is null or later than `started_at`, and no valid successor effective at or before `started_at` points to it. Authorization successor time is `decided_at`; source successor time is its non-null `reviewed_at`, otherwise `created_at`. A stale, expired, superseded, mismatched, or non-leaf record rejects execution.

## `mmbu.phase1.authorization_registry`

The sole authority is `config/phase1/authorization-registry.json`. Required fields: `schema_id`, `schema_version`, `registry_id`, `generation`, `source_record_digests`, `purpose_authorization_digests`, `source_heads`, `authorization_heads`, `revoked_digests`, `as_of`, and `record_digest`.

`generation` is a monotonically increasing nonnegative integer. Record arrays are exhaustive unique sorted arrays for every valid source and authorization record known through `as_of`, including superseded/revoked records. `source_heads` is a closed UTF-8-key-sorted map from every `source_id` to its one active leaf digest. `authorization_heads` is a closed sorted map from canonical `source_id|purpose` to its one active leaf digest. Every listed record must form a complete predecessor chain to its head; every predecessor/successor reference resolves inside the registry; a digest cannot be both a head and revoked. Missing chains, two heads, or an unregistered referenced record invalidates the registry. A valid registry may retain a rejected source or denied/blocked authorization as its current head, but execution cannot bind it; a bound source head must permit the requested purpose and its bound authorization head must have decision `allowed`.

The registry file and all referenced record bytes are covered by `source_state`. Each experiment binds `authorization_registry_digest`. Immediately before execution, the runner verifies that the on-disk registry digest and generation still match the experiment and that every bound source/authorization is the corresponding head and unexpired at `started_at`. Any registry drift aborts before data/model access and requires a new experiment or explicit reauthorization; selected-record omission cannot establish leaf status.

## `mmbu.phase1.current_status`

This is the sole schema for `config/phase1/current-status.json`. Required fields: `schema_id`, `schema_version`, `contract_revision`, `contract_manifest_digest`, `official_source_hashes`, `phase`, `facts`, `updated_at`, and `record_digest`.

`phase` is `design_only`, `phase1_running`, `phase1_returned_blocked`, `phase1_rejected`, or `phase1_accepted`. `official_source_hashes` is a closed object keyed only by the official source IDs declared in the contract manifest, each with a raw-byte digest. `facts` is a unique UTF-8-sorted array of closed objects containing exactly `fact_id`, `status`, `value`, `unit`, `evidence_digests`, and `limitation`; status is `measured`, `unknown`, or `blocked_external`. `value` and `unit` may be null only when status is not `measured`; measured facts require nonempty evidence, while unknown/blocked facts require a nonempty limitation. Evidence copies must be byte-identical to this file. Updating a fact creates a new whole-file digest; a public cluster specification cannot support an account-allocation fact.

## `mmbu.phase1.legacy_migration`

Required fields: `schema_id`, `schema_version`, `migration_id`, `input_digest`, `input_schema_id`, `input_schema_version`, `legacy_values`, `mapping_rule_digest`, `output_digest`, `output_schema_id`, `disposition`, `limitations`, `created_at`, and `record_digest`.

`disposition` is `migrated` or `rejected`; `output_digest` and `output_schema_id` are both non-null only for `migrated`. `legacy_values` is a nonempty unique sorted array containing the exact encountered values. The mapping rule is versioned and cannot infer purpose from a split name. Ambiguous `development`, `dev`, `external-development`, `official_dev`, or split-as-purpose values require an explicit row and either one exact canonical result or rejection. Migration never rewrites the legacy bytes, and changed rules create a new migration record.

## `mmbu.phase1.prompt_schema_contract`

Required fields: `schema_id`, `schema_version`, `contract_id`, `contract_status`, `task_prompt_digest`, `context_prompt_digest`, `task_output_schema_digest`, `context_output_schema_digest`, `requested_context_field_registry_digest`, `parser_digest`, `validator_digest`, `judge_policy_digest`, `inference_settings_digest`, `official_source_digests`, `supersedes_digest`, `created_at`, and `record_digest`.

`contract_status` uses the common contract-status enum. Prompt and output-schema digests are distinct and non-null; task and context may not share conversation/cache state. The requested-field registry defines allowed context fields and each run binds the ordered requested subset per record; no global four- or six-field assumption is legal. `official_source_digests` is a unique sorted array of closed objects with `source_id`, `source_role`, `sha256`, and `span`, where role is `brief`, `rules`, `site`, `dataset_card`, `organizer_answer`, or `other_official`, and `span` is a nonempty exact location string. `synthetic` has an empty source array and no official-equivalence claim. `brief_snapshot` binds at least one exact published-source object but remains provisional. `organizer_confirmed` additionally requires an `organizer_answer` object. Any prompt, schema, parser, validator, judge, inference, source, or status change creates a successor and cannot silently migrate existing outputs.

## `mmbu.phase1.experiment`

Required fields: `schema_id`, `schema_version`, `experiment_id`, `purpose`, `authorization_registry_digest`, `source_record_digests`, `purpose_authorization_digests`, `source_manifest_digests`, `split_manifest_digests`, `lineage_root_digests`, `model_digest`, `processor_digest`, `prompt_schema_contract_digest`, `evaluator_digest`, `prospective_lock_digest`, `seed_namespace`, `candidate_ids`, `decision_function_digest`, `created_at`, and `record_digest`.

All digest arrays are unique and sorted. There is exactly one source-record digest and one matching purpose-authorization digest for every consumed source; unrelated extra authorizations reject. `prospective_lock_digest` may be null only for `engineering` or `quarantine_inspection`. `candidate_ids` is a nonempty unique sorted array. `decision_function_digest` may be null only when the purpose cannot select, promote, confirm, or release. At run start, the runner resolves the bound exhaustive registry and every source, authorization, split, and lineage digest; proves registry digest/generation have not drifted; proves the source and authorization are its active, unexpired heads; checks the exact purpose/split table; and requires the experiment purpose to survive full lineage intersection. Changing any bound input requires a new experiment.

## `mmbu.phase1.run`

Required fields: `schema_id`, `schema_version`, `run_id`, `experiment_digest`, `reproducibility_record_digest`, `source_state_digest`, `command_digest`, `input_manifest_digests`, `output_manifest_digest`, `started_at`, `ended_at`, `exit_code`, `terminal_status`, `consumed_experiment_digest`, and `record_digest`.

`terminal_status` is one of `succeeded`, `failed`, `cancelled`, or `preempted`; this schema is a finalized immutable run record, not mutable scheduler state. `ended_at >= started_at`; `exit_code` is an integer or null only for an externally cancelled/preempted job with a bound scheduler receipt. `consumed_experiment_digest` must byte-equal `experiment_digest`. The run record is finalized after its reproducibility record and binds that record; execution cannot claim to have consumed its own later provenance record. Live progress, if needed, is an append-only log outside this record family and cannot support a verified claim. `output_manifest_digest` covers execution payloads only and excludes the run, reproducibility, claims, trace, phase-decision, and evidence-manifest records that bind it. Outputs from a failed/nonzero run remain evidence but cannot be labeled successful.

## `mmbu.phase1.prospective_lock`

Required fields: `schema_id`, `schema_version`, `lock_id`, `scope`, `source_state_digest`, `input_artifact_digests`, `excluded_result_digests`, `candidate_ids`, `seed_ids`, `thresholds`, `groups`, `evaluator_digest`, `multiplicity_rule`, `compute_plan_digest`, `decision_function_digest`, `claim_boundary`, `planned_opening_event`, `retry_policies`, `created_at`, `supersedes_digest`, `amendment_reason`, and `record_digest`.

The following values are closed:

| Field | Exact member shape and rule |
|---|---|
| `scope` | Object with exactly `scope_id`, `purpose`, `phase`, `primary_estimand_id`, `comparison_ids`, and `analysis_population_digest`. Purpose uses the common enum; phase is `engineering`, `discovery`, `confirmation`, or `release`; comparison IDs are a nonempty unique sorted array. |
| `thresholds` | Unique `threshold_id`-sorted array of objects with exactly `threshold_id`, `metric_id`, `estimand_id`, `value`, `unit`, `direction`, and `underpowered_disposition`. Value is finite; direction is `at_least`, `at_most`, or `within`; disposition is `block`, `narrow_claim`, or `exploratory_only`. Every metric/estimand resolves inside the bound evaluator or decision-function artifact. |
| `groups` | Unique `group_id`-sorted array of objects with exactly `group_id`, `definition_digest`, `parent_unit`, `minimum_parents`, `role`, and `underpowered_disposition`. Minimum parents is a positive integer; role is `primary`, `multiplicity_family`, `diagnostic`, or `excluded`; diagnostic groups cannot decide the primary claim. |
| `multiplicity_rule` | Object with exactly `family_id`, `alpha`, `method`, `hypothesis_ids`, and `rule_digest`. Alpha is finite in `(0,1)`; method is `bonferroni`, `holm`, `fixed_sequence`, or `none`; hypothesis IDs are unique and sorted. `none` is legal only for one hypothesis. |
| `claim_boundary` | Object with exactly `primary_claim_id`, `allowed_claim_ids`, `prohibited_claim_ids`, and `failure_claim_id`; arrays are disjoint, unique, sorted, and the primary ID is in the allowed set. |
| `planned_opening_event` | Object with exactly `opening_kind`, `trigger`, `not_before`, `operator_role`, `protected_artifact_digests`, and `command_template_digest`. Opening kind uses the opening-receipt enum; `not_before` is UTC; protected digests are nonempty, unique, and sorted. |
| `retry_policies` | Unique `retry_policy_id`-sorted array of objects with exactly `retry_policy_id`, `failure_classes`, `maximum_attempts`, `mutable_fields`, `invariant_digests`, and `decision`. Failure classes and mutable fields are nonempty unique sorted strings; maximum attempts is a positive integer; invariant digests are nonempty; decision is `retry_same_condition`, `new_exploratory_lineage`, or `stop`. A retry may change only named mutable fields and never a candidate, seed, threshold, group, evaluator, multiplicity rule, estimand, or claim boundary under `retry_same_condition`. `stop` permits no retry. `new_exploratory_lineage` requires a new lock and cannot preserve confirmation status or the old confirmation claim. |

`supersedes_digest` and `amendment_reason` are both null for the first lock and both non-null for a successor. A successor created before any opening may govern only if it records the old digest and changed fields. After any governed opening, a successor creates exploratory lineage and cannot preserve the old confirmation claim.

## `mmbu.phase1.opening_receipt`

Required fields: `schema_id`, `schema_version`, `opening_id`, `lock_digest`, `source_state_digest`, `manifest_digests`, `command_digest`, `environment_digest`, `operator_id`, `opening_kind`, `first_access_at`, `receipt_generation`, `supersedes_receipt_digest`, `expected_run_ids`, `observed_failure_ids`, `retries`, and `record_digest`.

`opening_kind` is `first_output` or `protected_access`. `first_access_at` must be strictly later than the governing lock's `created_at`. The initial immutable receipt has generation zero and null predecessor. A successor uses the same opening/lock identity, increments generation by exactly one, binds the prior receipt in `supersedes_receipt_digest`, preserves every prior scalar and retry object byte-for-byte, and may only add expected runs, newly finalized failures, or one newly authorized retry. Expected and failure arrays are unique and sorted; successors contain supersets. Every member of `observed_failure_ids` is the record digest of a finalized `mmbu.phase1.run` whose terminal status is `failed`, `cancelled`, or `preempted`; successful or unresolved runs reject.

`retries` is a unique `retry_id`-sorted array of closed objects with exactly `retry_id`, `retry_chain_id`, `retry_policy_id`, `root_failed_run_id`, `failed_run_id`, `retry_run_id`, `failure_class`, `attempt`, `changed_fields`, `command_digest`, and `started_at`. `retry_chain_id` is the canonical digest of `(lock_digest, retry_policy_id, root_failed_run_id)`; `retry_run_id` is unique across the lock and appears in `expected_run_ids`. Attempt one requires `failed_run_id = root_failed_run_id`; each later attempt requires `failed_run_id` to equal the immediately preceding attempt's `retry_run_id`. Every referenced failed run resolves in `observed_failure_ids`, matches the authorized failure class, and ended strictly before the next attempt starts. For each `(lock_digest, retry_policy_id, retry_chain_id)`, attempts across the complete predecessor chain are exactly `1..n`, start times strictly increase, and `n <= maximum_attempts`; changed fields remain a subset of the frozen policy. Every retry resolves one prospectively allowed policy in the lock and obeys its invariant digests and decision; a `stop` policy cannot appear, and `new_exploratory_lineage` cannot preserve confirmation status or the old confirmation claim. Otherwise the governed result is exploratory. A result-selected seed, comparator, threshold, group, or analysis digest not bound before `first_access_at` invalidates confirmation.

## `mmbu.phase1.opening_receipt_registry`

This is the sole schema for `config/phase1/opening-receipt-registry.json`. Required fields: `schema_id`, `schema_version`, `registry_id`, `generation`, `heads`, `created_at`, and `record_digest`. `generation` is a nonnegative integer. `heads` is a unique `lock_digest`-sorted array of closed objects with exactly `lock_digest`, `opening_id`, `head_receipt_digest`, and `receipt_generation`. Each head resolves one complete, unbranched predecessor chain; its generation equals the resolved head receipt. Registry generation zero may have empty heads. Every successor registry increments generation by one and may only add a lock or replace exactly one head with its direct receipt successor; removing a lock, skipping a generation, branching, or moving a head backward rejects.

Before protected access or a retry starts, the runner verifies the on-disk registry digest/generation, proves the governing receipt is the registered head, writes the immutable successor receipt that authorizes the action, then atomically advances the registry head. Every governed reproducibility record binds that exact pre-run registry digest and head receipt. Final claim validation uses the final registry head and walks the whole predecessor chain; an omitted, alternate, or stale receipt cannot establish an exhaustive retry history.

## `mmbu.phase1.reproducibility`

Required fields: `schema_id`, `schema_version`, `reproducibility_id`, `declared_level`, `source_state_digest`, `contract_manifest_digest`, `experiment_digest`, `prospective_lock_digest`, `opening_receipt_digest`, `opening_receipt_registry_digest`, `operator_id`, `started_at`, `ended_at`, `terminal_status`, `command`, `command_digest`, `working_directory`, `locale`, `timezone`, `filesystem`, `environment_variables`, `environment_artifact_digests`, `os_kernel`, `python`, `container_digest`, `hardware`, `frameworks`, `effective_numeric_settings`, `distributed_settings`, `seed_namespaces`, `rng_state_artifact_digests`, `worker_sampler_order`, `cache_network_policy`, `input_digests`, `output_digests`, `log_digests`, `exit_code`, `tolerances`, `compared_run_digest`, `observed_differences`, `reproduction_status`, `reproduction_limitation`, `created_at`, and `record_digest`.

`declared_level` is `R-I`, `R-B`, `R-N`, or `R-S`; `terminal_status` uses the finalized run enum; `ended_at >= started_at`, `operator_id` is nonempty, and `exit_code` is integer or null only for a bound external cancellation/preemption. `prospective_lock_digest`, `opening_receipt_digest`, and `opening_receipt_registry_digest` are all null only when that purpose requires neither a lock nor an opening receipt; otherwise all are non-null and the registry resolves the receipt as the active head that authorized this run at `started_at`. The reproducibility record is execution evidence created from an already immutable experiment: it binds that `experiment_digest`, exact contract manifest, and any applicable lock/opening-receipt registry/head, while the experiment never points back to the reproducibility record. Its `output_digests` cover execution payloads and never include a run, claims, trace, phase-decision, evidence-manifest, or other record whose digest transitively binds this reproducibility record. `container_digest` may be null only when the complete transitive environment artifacts are otherwise closed.

The following nested objects are closed; listed scalar strings are nonempty, integer counts/bytes/ranks are nonnegative, boolean fields are literal booleans, and nullable fields are marked:

| Object | Exact fields |
|---|---|
| `hardware` | `host_id`, `architecture`, `cpu_model`, `cpu_count`, `ram_bytes`, `gpu_driver`, `gpus`, `scheduler`; `gpu_driver` is null exactly when `gpus` is empty. `scheduler` is null or the closed object `job_id`, `account`, `partition`, `qos`, `requested_resources`, `allocated_resources`; unknown scheduler scalars are explicit null. Each GPU has `uuid`, `model`, `memory_bytes`, `compute_capability`, `node_rank`, `local_rank`, `topology` and may not use a public spec in place of allocation evidence. |
| `frameworks` | `python_executable_digest`, `python_version`, `torch`, `transformers`, `accelerate`, `deepspeed`, `fsdp`, `cuda_runtime`, `cuda_toolkit`, `cudnn`, `nccl`, `compiler`, `attention_library`, `quantization_library`, `image_decoder`, `dependency_lock_digest`, `resolver_report_digest`, `package_artifact_digests`, `install_command_digest`, `package_source_digests`; unused optional framework/version strings are null. |
| `effective_numeric_settings` | `parameter_dtype`, `compute_dtype`, `autocast_dtype`, `tf32`, `deterministic_algorithms`, `cudnn_benchmark`, `cublas_workspace_config`, `attention_backend`, `cache_backend`, `kernel_ids`, `fused_optimizer`, `compile_mode`, `gradient_checkpointing`, `fallbacks`; `fallbacks` and `kernel_ids` are ordered string arrays. |
| `distributed_settings` | `world_size`, `node_count`, `rank_topology`, `launcher`, `rendezvous_digest`, `visible_device_order`, `gradient_reduction`, `sharding_policy`, `microbatch_size`, `accumulation_steps`, `effective_batch_size`, `remainder_policy`; `rendezvous_digest` is null only at world size one. |
| `worker_sampler_order` | `worker_count`, `persistent_workers`, `prefetch_factor`, `multiprocessing_start_method`, `worker_seed_rule_digest`, `sampler_type`, `sampler_epoch`, `ordered_parent_ids_digest`, `ordered_record_ids_digest`, `batch_membership_digest`, `rejected_skipped_digest`, `padding_truncation_digest`, `exposure_digest`, `resume_cursor_digest`; fields unused by a zero-worker/no-resume run are explicit null. |
| `cache_network_policy` | `cache_root_digest`, `snapshot_digests`, `offline_requested`, `network_denied`, `network_probe_digest`, `remote_request_log_digest`, `hidden_fetch_count`; request log may be null only when network denial is proven and hidden-fetch count is zero. |

`seed_namespaces` is a sorted array of closed objects with `name`, integer `seed`, `derivation_rule_digest`, and `rng_state_digest`. `tolerances` is a sorted array of closed objects with `object_id`, `metric`, numeric `absolute`, numeric `relative`, `aggregation`, `rationale`, and `pre_result_source_digest`; both tolerances cannot be negative and text-answer/parser/box changes cannot be excused by numeric tolerance.

`locale`, `timezone`, and `filesystem` are nonempty effective values. `environment_variables` is a UTF-8-name-sorted array of closed objects with `name`, `present`, `secret`, and `value_digest`; `value_digest` is required for a present nonsecret value and null for an absent or secret value. Secret values are never hashed into portable evidence; their name and presence are retained. The registry includes every variable class named in `REPRODUCIBILITY.md`, not only variables the command author remembers setting.

`reproduction_status` is `not_requested`, `matched`, `within_tolerance`, `mismatch`, or `unavailable`. `compared_run_digest` is null only for `not_requested` or `unavailable`; otherwise it resolves to a finalized run. `observed_differences` is a sorted array of closed objects with `object_id`, `comparison_kind`, `metric`, `observed`, `allowed`, and `pass`; `comparison_kind` is `byte_equal` or `numeric`. For byte equality, `observed` and `allowed` are null and the compared artifact digests establish the result. For numeric comparison they are finite numbers. The array is empty only for `not_requested` or `unavailable`; a comparison status requires at least one row. `reproduction_limitation` is nonempty only for `unavailable`, otherwise null. Status must agree with all difference rows and the declared R-I/R-B/R-N/R-S level; a mismatch cannot be relabeled within tolerance.

## `mmbu.phase1.resource_measurement`

Required fields: `schema_id`, `schema_version`, `measurement_id`, `source_state_digest`, `experiment_digest`, `command_digest`, `condition_digest`, `measurement_scope`, `device_ids`, `memory`, `timing`, `throughput`, `terminal_status`, `evidence_digests`, `limitations`, `created_at`, and `record_digest`.

This is an observed execution-payload record created before the reproducibility record that later binds it through `output_digests`; it never contains a reproducibility or run digest. `condition_digest` covers the exact model, processor, inputs, batch/sequence/image geometry, numeric settings, and warmup/measurement policy. `device_ids` is a unique ordered array of allocated GPU UUIDs or the singleton string `cpu`; public hardware specifications and scheduler requests cannot substitute for observed allocation.

The nested objects are closed:

| Object | Exact fields and rules |
|---|---|
| `measurement_scope` | `stage`, `warmup_iterations`, `measured_iterations`, `independent_units`, `records`, `input_tokens`, `target_tokens`, `generated_tokens`; stage is `load`, `inference`, `forward_backward`, `save_reload`, or `resume`; counts are nonnegative integers, inapplicable token counts are null, and measured iterations must be positive for a successful record. |
| `memory` | `method`, `reset_receipt_digest`, `baseline_bytes`, `peak_allocated_bytes`, `peak_reserved_bytes`, `process_peak_bytes`, `system_peak_bytes`; method is a nonempty observed-counter description, reset receipt is required for a GPU peak, byte values are nonnegative integers or null only when the named counter is unavailable. At least one peak counter is non-null on success. |
| `timing` | `clock`, `synchronization_policy`, `started_at`, `ended_at`, `wall_time_seconds`; clock and policy are nonempty, timestamps are UTC, wall time is finite and nonnegative, and it agrees with the timestamp interval within a prospectively declared clock-resolution tolerance. |

`throughput` is a unique UTF-8-ID-sorted array of closed objects containing exactly `metric_id`, `numerator_value`, `numerator_unit`, `wall_time_seconds`, and `rate_per_second`. Values are finite and nonnegative; the rate must equal numerator divided by the same recorded positive wall time within a predeclared machine-precision tolerance. Permitted numerator units are `independent_units`, `records`, `input_tokens`, `target_tokens`, and `generated_tokens`, and the numerator must equal the corresponding non-null scope count. Empty throughput is legal only for a failed, cancelled, or preempted measurement.

`terminal_status` uses the finalized run enum. A successful record requires positive measured iterations, a non-null observed peak, positive wall time, at least one throughput row, and nonempty raw counter/log `evidence_digests`. Failed/cancelled/preempted records retain partial measurements and a nonempty limitation. Estimated or extrapolated memory, timing, and throughput are invalid; a changed warmup, geometry, batch, precision, kernel, device, or synchronization policy creates a different `condition_digest` and cannot be compared as the same condition.

## `mmbu.phase1.forward_backward`

Required fields: `schema_id`, `schema_version`, `probe_id`, `source_state_digest`, `experiment_digest`, `command_digest`, `model_digest`, `processor_digest`, `batch_digest`, `label_mask_digest`, `declared_trainable_patterns`, `parameter_inventory_digest`, `effective_settings_digest`, `loss`, `gradient_modules`, `optimizer_step`, `accumulation_comparison`, `output_digests`, `terminal_status`, `terminal_stage`, `started_at`, `ended_at`, `limitations`, `record_digest`.

This is also an execution payload and therefore never points to the later reproducibility or finalized run records. `declared_trainable_patterns` is a nonempty unique UTF-8-sorted array. `terminal_stage` is one of `initialization`, `preprocess`, `forward`, `loss`, `backward`, `optimizer`, or `completed` in that order; success requires `completed`, while a non-success records the last stage begun. `parameter_inventory_digest`, `batch_digest`, and `label_mask_digest` are strings on success. On non-success each may be null iff that artifact was not yet created, but any observed digest is retained; reaching `forward` or later requires both batch and label-mask digests, and reaching `backward` or later requires the parameter-inventory digest. `gradient_modules` is a UTF-8-module-name-sorted array of closed objects containing exactly `module_name`, `declared_trainable`, `parameter_count`, `gradient_parameter_count`, `finite_gradient_count`, `nonfinite_gradient_count`, `gradient_norm`, and `updated_parameter_count`; counts are nonnegative integers, the norm is finite or null exactly when no gradient exists, undeclared modules require zero gradient and update counts, and every declared trainable pattern must match at least one inventoried module when the inventory exists.

The nested objects are closed:

| Object | Exact fields and rules |
|---|---|
| `loss` | `framework_loss`, `manual_shifted_ce`, `absolute_difference`, `allowed_difference`, `target_token_count`, `ignored_token_count`, `finite`; on success numeric values are finite, target count is positive, ignored count is nonnegative, `finite` is literal true, and the observed difference cannot exceed a nonnegative tolerance fixed in `effective_settings_digest` before execution. If execution fails before a named value or count exists, that field is null and `finite` is false; any value already observed is retained rather than erased. |
| `optimizer_step` | `optimizer_id`, `learning_rate`, `pre_step_parameter_digest`, `post_step_parameter_digest`, `changed_parameter_count`, `step_succeeded`; on an attempted successful step, optimizer ID and pre-step digest are nonempty, learning rate is finite and positive, pre/post digests differ, at least one declared-trainable parameter changes, and `step_succeeded` is true while undeclared parameters remain byte-identical. On non-success, optimizer ID, learning rate, and either digest/count may be null iff that value was not yet created or observed; every observed value is retained and `step_succeeded` is false. Reaching `optimizer` requires non-null optimizer ID, learning rate, and pre-step digest. A failed attempted step records every observed pre/post value and keeps `step_succeeded` false. |
| `accumulation_comparison` | `status`, `full_batch_digest`, `microbatch_digest`, `exposure_digest`, `metric`, `observed_difference`, `allowed_difference`, `pre_result_rule_digest`; status is `not_requested`, `matched`, `within_tolerance`, `mismatch`, or `unavailable`; all comparison fields are null only for `not_requested` or `unavailable`, whose reason appears in `limitations`; otherwise exposure must be identical and tolerance must be nonnegative and prospectively bound. |

`effective_settings_digest` binds `use_cache=false`, microbatch size, accumulation steps, precision, loss reduction, optimizer, clipping, and deterministic settings. `output_digests` is a nonempty unique UTF-8-sorted array that binds raw logs and any minimal checkpoint payload, not later provenance records. `terminal_status` uses the finalized run enum, timestamps are UTC, and `ended_at` is not earlier than `started_at`. Success requires target-only masking, agreement with manually shifted cross entropy, finite loss and gradients, coverage of all declared trainable patterns, no undeclared gradient/update, and a successful optimizer step. Failed, cancelled, or preempted records preserve every observed partial value; `gradient_modules` may be empty only if backward never began, and `limitations` must be nonempty and state the terminal stage. A toy tensor path, model output detached from the native processor, finite scalar without mask/shift proof, or result-chosen tolerance invalidates the record.

## Evaluation layers

All layer records require `schema_id`, `schema_version`, `record_id`, `example_manifest_digest`, `contract_digest`, `created_at`, and `record_digest`.

- `mmbu.phase1.raw_output` additionally requires `request_digest`, `input_digest`, `token_ids`, `decoded_text`, `finish_reason`, `effective_generation_settings`, `timing`, and `runtime_status`. `runtime_status` is `succeeded`, `load_failed`, `preprocess_failed`, `timeout`, `oom`, or `generation_failed`. `token_ids` is a nonnegative-integer array and `decoded_text` a string on success. On failure each is either the exact partial value produced before failure or null iff no such value exists; neither may be fabricated. `finish_reason` is a string on success and a string or null on failure. Generation settings is a closed object with `decoding_method`, `max_new_tokens`, `temperature`, `top_p`, `top_k`, `do_sample`, `num_beams`, `stop_token_ids`, `seed`, and `cache_enabled`; inapplicable sampling scalars are explicit null. Timing is a closed object with `started_at`, `ended_at`, and nonnegative `latency_ms`.
- `mmbu.phase1.parsed_output` additionally requires `raw_digest`, `parser_digest`, `parse_status`, and `parsed_value`. `parse_status` is `parsed`, `invalid_json`, `duplicate_key`, `nonfinite`, `multiple_objects`, `unknown_key`, `missing_required`, or `not_run`; `parsed_value` is a closed contract-governed object only for `parsed`, otherwise null.
- `mmbu.phase1.validated_output` additionally requires `raw_digest`, `parsed_digest`, `validator_digest`, `validation_status`, `requested_context_fields`, `geometry_status`, and `validated_value`. `validation_status` is `valid`, `invalid_schema`, `invalid_value`, `invalid_geometry`, or `not_run`; `geometry_status` is `valid`, `invalid`, `not_applicable`, or `not_run`; requested fields are a unique ordered subset allowed by the bound contract; `validated_value` is non-null only for `valid`.
- `mmbu.phase1.judged_output` additionally requires `raw_digest`, `parsed_digest`, `validated_digest`, `judge_digest`, `judge_status`, `task_grade`, `context_grades`, and `terminal_outcome`. `judge_status` is `judged`, `judge_failed`, or `not_run`; `terminal_outcome` is `success`, `runtime_failure`, `parse_failure`, `validation_failure`, or `judge_failure`. `task_grade` is a finite number in `[0,1]` and `context_grades` a closed map over the requested fields only when judged; otherwise both are null.

Legal status flow is deterministic: any raw `runtime_status` other than `succeeded` forces parse, validation, and judge statuses `not_run` and terminal outcome `runtime_failure`. A successful raw record requires a parse attempt; `parsed` requires a non-`not_run` validation attempt, while every other parse status forces validation/judge `not_run` and `parse_failure`. Validation `valid` requires judge `judged` or `judge_failed`; any other non-`not_run` validation status forces judge `not_run` and `validation_failure`. Judge `judged` maps to `success`; `judge_failed` maps to `judge_failure`. No layer rewrites its parent. A changed parent creates a new descendant digest.

Official task/context field names are not frozen here. They live in the bound prompt/schema contract and requested-field subset for the relevant `contract_status`.

## `mmbu.phase1.evidence_manifest`

Required fields: `schema_id`, `schema_version`, `bundle_id`, `members`, and `created_at`. It has no `record_digest` field and never contains itself.

Each member has exactly `path`, `bytes`, `sha256`, `media_type`, `schema_id`, and `schema_version`; the last two are both null for raw logs/prose or both non-null. Members are sorted by UTF-8 path bytes and cover every other bundle member exactly once. Only regular files are allowed. The externally retained bundle-root digest is SHA-256 of the RFC 8785 canonical manifest bytes.

## `mmbu.phase1.source_state`

Required fields: `schema_id`, `schema_version`, `commit_sha`, `dirty`, `patch_sha256`, `inventory`, `created_at`, and `record_digest`.

`patch_sha256` is null exactly when `dirty=false`; otherwise it covers a canonical binary patch that includes staged and unstaged tracked changes plus an explicit untracked-file inventory/content digest. Inventory members have exact path, bytes, SHA-256, and class (`source`, `test`, `config`, `contract`, or `lock`), sorted by path. It must cover every Phase 1 source, test, configuration, binding contract, and lock file.

## Claims, trace, and decision

`mmbu.phase1.claims` requires `schema_id`, `schema_version`, `source_state_digest`, `claims`, `created_at`, and `record_digest`. The input claim set has exactly 22 members: P1-00 through P1-16, P1-17a, P1-17b, and P1-18 through P1-20. P1-21 is excluded because it is the derived decision output. Each input ID appears exactly once with `requirement_id`, claim `status`, `code_paths`, `test_ids`, `evidence_paths`, `evidence_digests`, and `limitations`. A `verified` row requires nonempty code/test/evidence references unless the binding row is document-only and explicitly names its document verifier.

`mmbu.phase1.requirement_trace` requires `schema_id`, `schema_version`, `source_state_digest`, `claims_digest`, `rows`, `created_at`, and `record_digest`. It has exactly one row for each of the same 22 input IDs, mapping stable behavior names to exact tests and evidence. Missing, duplicate, unknown, extra, or P1-21 input rows fail.

`mmbu.phase1.phase_decision` requires `schema_id`, `schema_version`, `claims_digest`, `trace_digest`, `decision`, `rejection_predicates`, `derived_at`, and `record_digest`. It must not contain P1-21 as an input. The standalone validator derives the decision exactly as `ACCEPTANCE.md` specifies and compares it with `decision`; this validated decision record is the evidence/output for P1-21. Claims, trace, and decision contain no bundle-root field. The manifest is computed last, covers all three records, and its root is retained outside the bundle, eliminating self-reference. A mismatch, self-reference, unknown status, invalid completed evidence manifest/root, or verified row with missing bound evidence rejects.

## Minimal chronology examples

Valid: lock `L` at `10:00Z`; opening receipt at `10:01Z`; execution consumes the immutable experiment bound to `L`; its reproducibility record binds that experiment, `L`, the receipt, and payloads; the finalized run then binds both experiment and reproducibility digests; decision code and thresholds match `L`.

Invalid: output exists at `09:59Z`; lock is created at `10:00Z`; an opening receipt later points to the lock. The result remains exploratory. Also invalid: a pre-opening amendment changes the seed but omits `supersedes_digest`, or a post-opening amendment claims to preserve confirmation.

## Minimal cross-record examples

Valid: a quarantined source with empty purposes receives immutable rights, grouping, and QA receipts; a successor source record becomes `approved` for `engineering`; an engineering split references that successor; a purpose authorization allows only `engineering`; lineage intersection remains `engineering`; and the experiment consumes those exact digests.

Invalid: a source is `candidate` but lists `train`; a split calls itself `train` while its source permits only `engineering`; a purpose authorization infers `adaptive_dev` from legacy `development`; or a migration omits the legacy input digest. Each fails before execution.

Valid: `current-status.json` records the public MOCS specification as one measured public fact while the account allocation is a separate `unknown` fact with null value and a limitation. Invalid: copying the public GPU count into the account-allocation value.

Valid: a `brief_snapshot` prompt contract binds exact published-source, prompt, output-schema, parser, validator, judge, and inference digests, while preserving the provisional status. Invalid: changing a requested context field, parser, or inference setting without a successor contract, or relabeling the same bytes `organizer_confirmed` without a written-answer digest.

Executable JSON Schemas or equivalently strict typed validators must implement this contract and its cross-record graph/chronology rules. Self-authored fixtures alone are insufficient: every invariant above needs a positive and adversarial negative test.
