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

Required fields: `schema_id`, `schema_version`, `lock_id`, `scope`, `source_state_digest`, `input_artifact_digests`, `excluded_result_digests`, `candidate_ids`, `seed_ids`, `thresholds`, `groups`, `evaluator_digest`, `multiplicity_rule`, `compute_plan_digest`, `decision_function_digest`, `claim_boundary`, `planned_opening_event`, `created_at`, `supersedes_digest`, `amendment_reason`, and `record_digest`.

`thresholds` and `groups` are closed-schema arrays whose members include stable ID, value/definition, estimand, unit, direction, and underpowered disposition. `supersedes_digest` and `amendment_reason` are both null for the first lock and both non-null for a successor. A successor created before any opening may govern only if it records the old digest and changed fields. After any governed opening, a successor creates exploratory lineage and cannot preserve the old confirmation claim.

## `mmbu.phase1.opening_receipt`

Required fields: `schema_id`, `schema_version`, `opening_id`, `lock_digest`, `source_state_digest`, `manifest_digests`, `command_digest`, `environment_digest`, `operator_id`, `opening_kind`, `first_access_at`, `expected_run_ids`, `observed_failure_ids`, `retry_ids`, and `record_digest`.

`opening_kind` is `first_output` or `protected_access`. `first_access_at` must be strictly later than the governing lock's `created_at`. Expected, failure, and retry arrays are unique and sorted. Every retry names a prospectively allowed retry policy in the lock; otherwise the governed result is exploratory. A result-selected seed, comparator, threshold, group, or analysis digest not bound before `first_access_at` invalidates confirmation.

## `mmbu.phase1.reproducibility`

Required fields: `schema_id`, `schema_version`, `reproducibility_id`, `declared_level`, `source_state_digest`, `contract_manifest_digest`, `experiment_digest`, `prospective_lock_digest`, `opening_receipt_digest`, `operator_id`, `started_at`, `ended_at`, `terminal_status`, `command`, `command_digest`, `working_directory`, `locale`, `timezone`, `filesystem`, `environment_variables`, `environment_artifact_digests`, `os_kernel`, `python`, `container_digest`, `hardware`, `frameworks`, `effective_numeric_settings`, `distributed_settings`, `seed_namespaces`, `rng_state_artifact_digests`, `worker_sampler_order`, `cache_network_policy`, `input_digests`, `output_digests`, `log_digests`, `exit_code`, `tolerances`, `compared_run_digest`, `observed_differences`, `reproduction_status`, `reproduction_limitation`, `created_at`, and `record_digest`.

`declared_level` is `R-I`, `R-B`, `R-N`, or `R-S`; `terminal_status` uses the finalized run enum; `ended_at >= started_at`, `operator_id` is nonempty, and `exit_code` is integer or null only for a bound external cancellation/preemption. `prospective_lock_digest` and `opening_receipt_digest` may be null only when that purpose requires neither a lock nor an opening receipt. The reproducibility record is execution evidence created from an already immutable experiment: it binds that `experiment_digest`, exact contract manifest, and any applicable lock/opening receipt, while the experiment never points back to the reproducibility record. Its `output_digests` cover execution payloads and never include a run, claims, trace, phase-decision, evidence-manifest, or other record whose digest transitively binds this reproducibility record. `container_digest` may be null only when the complete transitive environment artifacts are otherwise closed.

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
