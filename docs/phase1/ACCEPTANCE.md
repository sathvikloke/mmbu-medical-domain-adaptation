# Phase 1 acceptance contract

**Status:** binding, clone-resident, manifest-covered acceptance authority  
**Frozen:** 2026-10-14  
**Scope:** Phase 1 only; this file does not authorize serious training, public-set optimization, or external upload

## Authority and decision vocabulary

`SCHEMAS.md` is the binding field-level companion to this row registry; an implementation cannot replace its types, digest domains, references, or chronology with a self-chosen alternative.

This document is the normative Phase 1 row registry. `CONTRACT.md` defines the engineering boundary, `REPRODUCIBILITY.md` defines replay claims, and `B1_RUNTIME_GATE.md` defines native B1 admission. External audit files may explain these rows but cannot add an implementation requirement or override this registry. Official rules, the official harness, and written organizer answers remain higher authority and require a reviewed contract revision.

Every row has exactly one status: `verified`, `failed`, `untested`, or `blocked_external`. Narrative labels such as `partial`, `mostly`, or `ready` are invalid. Evidence for `verified` must name its code path, test, exact artifact, source-state digest, and limitation. A generic suite pass cannot verify a row.

## Normative row registry

| ID | Mandatory Phase 1 condition | Required proof and adversarial behavior | Automatic row failure |
|---|---|---|---|
| P1-00 | Phase 1 lives at `src/mmbu_phase1`, CPU tests at `tests/phase1`, and status at `config/phase1/current-status.json`; the historical bundle is byte-immutable. | Root orchestration runs historical, root-tool, and nonzero Phase 1 tests; deliberate historical-byte drift fails. | Historical bytes change, Phase 1 is invisible to root tests, or an old bundle claim is reused. |
| P1-01 | One current-status authority records the pinned contract revision and measured-versus-unknown state. | Evidence contains a byte-identical status copy and digest; public hardware cannot become account evidence. | Two overlay authorities, divergent evidence copy, or unmeasured readiness is asserted. |
| P1-02 | Public-origin and derivative ancestry fail closed for every promotable purpose, including the decisions that choose what to run. | Synthetic canary bypasses cover direct path, copy, symlink, manifest, derivative, mixed ancestry, governance relabeling, omitted decision parents, copied rationale, manual payload creation, extra mounts/reads, denied-read attempts, network access, self-review, and human-memory attestation; restricted real-hash checks reveal no content; an admitted engineering positive control passes. | Enforcement is a warning, filename check, ignored flag, content-blind declaration, or exposes official examples to developers. |
| P1-03 | Strict V2 records bind reviewer attestations, revocable pre-download acquisition plus execution, exact source artifacts, proposed purposes, rights, grouping, closed eligible populations, immutable QA sampling plans, QA, two-stage custody summaries, source, split, complete checkpoint/model lineage, purpose and checkpoint-bound release authorization, predecessor-bound exhaustive authorization registry, lineage, sanitized rule extraction, decision plan/payload/execution, environment-launch policy/receipt, execution condition, experiment, run, overlay, migration, paired-condition contract, lock, opening receipt, predecessor-bound exhaustive receipt-head registry, reproducibility, and evaluation layers. | Validators reject unknown keys, unauthorized/unreceipted acquisition, superseded acquisition heads, pre-manifest inspection, container/population chronology inversion, incomplete or opaque populations, QA plans frozen before a population or after QA opening, plan/lock/opening/receipt mismatch, opaque or wrong-schema admission digests, wrong-subject review, illegal source transitions, unbound proposed purposes, pre-artifact source records, unreceipted candidate admission, incomplete or duplicate model lineage, release without one matching authorization per contributor and compatible rights, unsanitized or out-of-window custody content, omitted/superseded authorization, ambiguous legacy values, noncanonical digests, broken references, unrelated records, unreceipted rule summaries, late decision plans/thresholds, result-selected seeds/comparators, missing decision receipts, omitted/rewritten/branched registry generations, retry-chain resets/branches/stale heads, inherited/unknown/changed child environment entries, canary leakage, incomplete/opaque execution conditions, condition drift at any transitive leaf, and discovery reused as confirmation. Execution emits the exact experiment and execution-condition digests consumed; its completed reproducibility record binds both plus the exact environment-launch policy/receipt and authorizing receipt-registry head, and the finalized run binds all three. | An arbitrary non-null digest, prose-only record, incomplete/stale/rewritten registry, optional provenance, manual decision, unrelated declaration, late lock or pairing contract, opaque condition component, self-declared ambient-environment safety, mismatched base/adapted condition, or hand-picked retry receipt can bless acquisition, a source, run, or release. |
| P1-04 | Exact pinned B1 identity and the complete native reference condition pass. | Before load, index, five shards, sizes, hashes, tensor totals, metadata, class, processor/template, geometry, padding, BF16, SDPA, cache, decoding, visual intervention, heterogeneous batch, repeated-call state, MRoPE, cached/uncached, offline, resource, training, and reload checks reproduce under `B1_RUNTIME_GATE.md`. | A mock, one-image or batch-size-1 demo, auto fallback, inherited generation setting, hidden fetch/kernel/utility, or upstream fixture is reported as native proof. |
| P1-05 | Task and context are separate fresh stateless calls. | Serialized requests and cache state prove no shared conversation, cache, answer, label, prediction, or judge data; sentinel leakage fails. | Dictionary separation or coincidental output text is the only evidence. |
| P1-06 | Raw output is immutable and written before parsing. | Content-addressed raw record contains request hash, token IDs, decoded text, finish reason, effective settings, timing, and runtime status; mutation attempts fail. | Only a final answer is retained or downstream fields enter raw. |
| P1-07 | Parsed, validated, and judged layers are distinct and parent-hash bound. | Malformed, duplicate-key, nonfinite, multi-object, unknown-field, truncated, and stale-parent cases fail without rewriting ancestry. | Repair/retry becomes the prediction or judged evidence survives a changed parent. |
| P1-08 | Runtime, parse, validation, and judge states are orthogonal; every frozen example-manifest row remains in each layer population and the denominator. | Legal transition tests include load, timeout, OOM, malformed, unknown-field, geometry, and judge failures; downstream states become `not_run` where required; a judge failure after valid validation preserves the already deterministic geometry result; execution-output layer ID sets equal the example-manifest ID set. | Failure stage disappears, judge state changes validated geometry, impossible states validate, fake empty output is created, an opaque output manifest passes, or denominators differ by candidate. |
| P1-09 | The engineering fixture is synthetic and covers classification, counting, one/many boxes, dynamic context subsets, inapplicable context, malformed output, and stateless sentinels. | Every case has a deliberate negative; task scoring works with no applicable context; its closed example manifest obeys `EVALUATOR_MECHANICS.md`. | Official or unapproved biomedical content enters, empty context blocks task scoring, or fixture population/targets/weights change after opening. |
| P1-10 | Continuous task-change arithmetic is exact under frozen weights and prospectively matched base/adapted conditions; binary flips remain secondary. | The normative conformance vectors plus fractional, weighted, transition, failure, tie, missing-row, wrong-denominator, noncanonical-rational, and every-field condition-drift negatives prove the exact equations and pairing contract in `EVALUATOR_MECHANICS.md`; binary `(PF-NF)/N` is emitted only with a prospectively bound correctness predicate. | Counts/rates, rational wire form, aggregation unit, tie/failure/missing policy, weights, predicate, denominator, or any non-model inference/evaluation condition is inconsistent or result-selected. |
| P1-11 | Visual-benefit states require verified answer-changing pairs and correct generated decisions on both endpoints. | Retained/acquired/lost/never and joint task-change tables reproduce; no-image/shuffle remains diagnostic. | Suppressing an old answer, an undefined target, or a diagnostic pair counts as success. |
| P1-12 | Geometry and serialization preserve original dimensions and the `single`, `all_targets`, `any_one`, and `not_applicable` semantics without repair or fabricated predictions. | The normative `EVALUATOR_MECHANICS.md` vectors plus runtime failure, parse failure, wrong-type/no-array validation failure, valid-array/non-geometry validation failure, valid geometry followed by judge failure, invalid box, count mismatch, exact matching tie, negative, zero, overflow, swapped-frame, normalized-as-pixel, ordering, and border cases trace end to end with canonical-rational original-pixel IoU, zero-based pairs, closed reasons, exact precedence, and exact null/empty rules. | Coordinates are silently clipped, rounded, reordered, normalized, repaired, multiply reused, fabricated, approximately scored, parse/validation failures are relabeled, judging changes validated geometry, or matching/reason codes use an open or result-chosen rule. |
| P1-13 | A real native collator and backward step supervise only declared targets and reach only declared modules. | The closed `mmbu.phase1.forward_backward` record proves `use_cache=false`; non-targets are `-100`; framework loss matches manually shifted CE; forward/backward/update is finite; declared patterns cover the trainable inventory; undeclared modules receive no gradient/update; full-batch versus accumulated-microbatch equivalence is separately labeled under a pre-result rule. | Toy tensors replace the native path, finite loss substitutes for mask/CE correctness, exposure differs, a result-chosen tolerance appears, or undeclared gradients/updates occur. |
| P1-14 | Minimal save, network-denied fresh reload, and interrupted resume preserve identity and execution state. | Adapter/module keys, class/config/backend/targets, pixel hash, first-step logits, generated IDs, adapter/config hashes, optimizer/scheduler/scaler when used, RNG, sampler/cursor, accumulation, and exposure replay under fixed tolerance. | Warm-process-only reload, hidden fetch, repeated/skipped data, state loss, or result-chosen tolerance. |
| P1-15 | Schema-bound reproducibility and resource records capture the closed empty-parent environment launch, exact effective condition, command, logs, allocation, randomness, data order, cache/network state, observed resources, and declared replay level. | The launcher uses the policy's absolute Python and exact platform-specific environment from an empty mapping; its receipt proves passed/child equality and parent-canary exclusion; condition and reproducibility projections match. The closed `mmbu.phase1.resource_measurement` record binds the exact condition, observed counters, synchronization, memory, timing, and recomputable throughput; negative reruns vary environment membership/value, canary, hidden kernel/precision/topology/worker/order/seed/cache/network/measurement state and are detected. | Parent state or a secret enters the child, the child self-classifies ambient state, estimates/public specifications replace measurements, numerator/denominator or synchronization changes are hidden, `pip freeze` claims closure, requested replaces effective settings, or replay levels are conflated. |
| P1-16 | A generation-path fixture schema is prepared but not falsely passed. | External task/source slices and thresholds remain unexecuted until admitted data exists; fake candidate options for open generation fail. | Phase 1 claims G1/O1/O2 passed from synthetic or public examples. |
| P1-17a | Local R0 preflight closes a disposable dummy bundle. | Canonical manifest, safe-serialization allowlist, dependency closure, empty-cache reload, secret/private-path scan, build receipt, and missing blob/shard, template drift, path alias, pickle, remote-code, mutable revision, dependency range, and hidden-network failures reproduce. | Unsafe/unclosed content passes or local work is called external R0. |
| P1-17b | External repository lifecycle is separately statused. | Ownership, visibility, upload, anonymous download, deletion/supersession, and receipt each have evidence or remain `blocked_external`. | External state is inferred locally, an upload occurs without a separate user-directed step, or an unexecuted field is verified. |
| P1-18 | Requirement trace, acyclic source state, separately bound mutable execution-state registries, and content-addressed evidence root bind every claim to exact implementation and execution bytes. | Manifest rejects deletion/replacement/reorder, unsafe paths, case/Unicode aliases, traversal, symlink/hard-link alias, self-entry, dirty-tree lie, missing log/exit code, unrelated reproducibility record, omitted registry, provenance cycle, and post-evidence drift. | A generic suite verifies a row, unsafe members enter, mutable authority is hidden inside source state, or evidence is not source/run bound. |
| P1-19 | Every run binds a versioned prompt/schema contract with status `synthetic`, `brief_snapshot`, or `organizer_confirmed`. | Exact prompt, schema, requested context fields, parser, validator, judge policy, canonical-rational geometry threshold, inference settings, and source hashes are digest-bound; the threshold equals the execution condition, evaluator, validator, and geometry summary; unknown/mismatched versions and hard-coded global field counts fail. | An unconfirmed contract is called official-equivalent, a threshold projection drifts, or outputs silently migrate. |
| P1-20 | The binding clone contract is complete and strict-manifest covered. | Fresh clone works with no parent workspace; manifest verification rejects missing, extra, duplicate-key, mismatched, nonnormalized, or path-escaping members and checks official-source hashes. | Execution depends on chat paths, floating pins, contract drift, or the historical bundle receives new code. |
| P1-21 | Overall phase decision is derived without self-reference. | Standalone validator consumes the exact 22-row input set—P1-00 through P1-16, P1-17a, P1-17b, and P1-18 through P1-20; forged acceptance, an input P1-21 row, and self-reference fail. | A narrative or the decision field itself can justify acceptance. |

## Stable behavior names

The requirement trace must map equivalent tests to these stable behaviors:

```text
firewall_rejects_public_source_for_promotion
firewall_rejects_public_derivative_for_promotion
historical_bundle_remains_byte_immutable
purpose_and_split_are_independent
lineage_receipt_is_required_for_promotion
governance_reference_does_not_enter_data_purpose_intersection
content_artifact_cannot_claim_governance_role
official_rule_summary_requires_two_reviewed_span_receipt
decision_plan_precedes_protected_input_opening
decision_runner_rejects_unallowlisted_mount_read_and_network
decision_lineage_covers_every_mounted_content_input
copied_rationale_and_manual_decision_payload_are_ineligible
decision_operator_cannot_self_review
promotable_experiment_binds_complete_decision_receipts
runner_rejects_record_digest_mismatch
runner_rejects_inherited_generation_defaults
runner_rejects_effective_decoding_drift
task_context_calls_are_stateless
raw_output_is_immutable
parsed_validated_and_judged_layers_bind_parent_hash
runtime_failure_layer_state_is_legal
failure_stages_remain_orthogonal
failures_remain_in_denominator
paired_condition_rejects_each_non_model_field_drift
paired_condition_allows_only_closed_model_identity_difference
execution_condition_rejects_each_leaf_mutation
execution_condition_matches_raw_run_and_reproducibility
continuous_task_change_identity_holds
exact_rational_wire_rejects_float_unreduced_negative_denominator_and_alt_zero
binary_flip_rate_identity_holds_when_applicable
visual_benefit_transition_table_is_complete
boxes_are_not_silently_repaired
geometry_failure_uses_nulls_without_fabricated_prediction
geometry_validation_failure_distinguishes_missing_and_present_array
geometry_judge_failure_preserves_validated_result
geometry_match_pairs_are_zero_based_sorted_and_exact
geometry_exact_tie_uses_lexicographic_matching
native_collator_masks_only_declared_targets
real_backward_reaches_declared_modules
fresh_process_reload_matches
interrupted_resume_preserves_state_order_and_exposure
reproducibility_record_binds_effective_environment_and_command
environment_launch_starts_empty_and_matches_policy_receipt_condition_and_reproducibility
environment_launch_rejects_inheritance_unknown_change_and_parent_canary
prompt_geometry_threshold_matches_condition_evaluator_validator_and_summary
seed_namespaces_and_sampler_order_are_stable
clean_cache_replay_rejects_hidden_network_fetch
result_chosen_or_wrong_object_tolerance_is_rejected
prompt_schema_contract_is_digest_bound
context_schema_uses_requested_field_subset
unconfirmed_contract_is_not_official_equivalent
evidence_bundle_root_detects_deletion_and_replacement
evidence_manifest_rejects_alias_traversal_symlink_and_collision
source_state_detects_dirty_or_post_evidence_drift
fresh_clone_contains_governing_contract
phase_decision_is_derived_without_self_reference
release_manifest_detects_missing_or_changed_file
release_scan_detects_secret_and_private_path
```

A different test name is permitted only when the trace maps it to the same behavior and evidence.

## Required evidence discovery contract

The trace must locate, by exact normalized bundle-relative path and digest, at least: claims, phase decision, evidence manifest, source state, requirement trace, environment-launch policy and receipt, execution condition, experiment and receipt, reproducibility record, prompt/schema contract, paired-condition contract, run manifest, example manifest, execution-output manifest, environment, allocation, current-status overlay, migration, reviewer attestations, acquisition authorizations and execution receipts, source artifact manifests, rights/grouping receipts, eligible-population manifests, QA sampling plans and receipts, two-stage custody summaries, source, checkpoint/model-lineage, and purpose/release authorization records, lineage receipts, sanitized-rule receipts, decision plans, decision payloads, decision rationales, decision-execution receipts and sandbox logs, raw/parsed/validated/judged layers, failures, task-change and visual-benefit summaries, geometry, native forward/backward, save/reload/resume, resources, tests, local-R0 manifest/output/failure/scan artifacts, and limitations. Names may differ only through the trace. The externally retained root is not a bundle member and has no bundle-relative path. The validator receives a separate external retention receipt containing a locator ID, bundle ID, and root SHA-256; that receipt must not appear in the manifest it authenticates.

`evidence-manifest.json` is computed after every other member. It never lists itself. Its RFC 8785 canonical bytes cover every other member exactly once and its SHA-256 root is retained outside the bundle before review. `source-state.json` is inside that root and binds all Phase 1 source, tests, immutable implementation configuration, contract, and lock bytes plus clean/dirty state and a canonical patch digest when dirty. Current status, authorization heads, and opening-receipt heads are mutable execution-state authorities excluded from source state; their exact files remain manifest members and their digests are bound by the governing status, experiment, and reproducibility records.

## Deterministic decision function

Inputs are exactly 22 validated statuses and their evidence: P1-00 through P1-16, P1-17a, P1-17b, and P1-18 through P1-20. P1-21 is the validated phase-decision record itself and is never a claim or trace input.

- `rejected` if any mandatory row is `failed`, any automatic rejection below fires, any row marked `verified` lacks valid bound evidence, or the evidence root/trace is invalid.
- `accepted` if P1-00 through P1-16 and P1-18 through P1-20 are `verified`, P1-17a is `verified`, P1-17b is `verified` or `blocked_external`, and no automatic rejection fires.
- `returned_blocked` otherwise, provided no rejection condition fires. Missing native model, GPU, clean reload, resource, organizer, rights, human-review, credential, or cluster authority remains explicit; it never becomes acceptance.

Real-source positive controls for `train`, `adaptive_dev`, `confirmation`, and `release` may be `blocked_external` in Phase 1 only when their schema-logic controls verify. They become mandatory before that purpose is used.

## Automatic rejection

Reject the phase if public MMBU content or derivatives enter a development/promotable run or any decision selecting that run; a rule summary lacks exact-span two-reviewer extraction; a promotable decision lacks a pre-opening plan, hermetic receipt, complete input lineage, operator attestation, or independent review; the historical bundle changes; a run is not bound to its exact declarations; raw output is unavailable or repaired before preservation; task/context share state; failed rows leave the denominator; native backward misses declared modules; reload is not fresh and offline; resource facts are estimated; synthetic work is called medical/model-performance evidence; an external upload occurs without a separate user-directed step; local preflight is called external R0; any missing row is verified; or an unconfirmed contract is called official-equivalent.

This contract can define acceptance. Only implementation and reproduced evidence can earn it.
