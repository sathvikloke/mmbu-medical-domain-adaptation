"""Frozen Phase 1A implementation-slice scope used by orchestration and claims."""

# Every scoped CPU test module; ``tools/team.py test`` fails closed if one is missing.
REQUIRED_PHASE1_TEST_MODULES = (
    "test_admission.py",
    "test_authority.py",
    "test_b1_preflight.py",
    "test_b2_dual_preflight.py",
    "test_b2_preflight.py",
    "test_biomedical_sources.py",
    "test_bundle.py",
    "test_busbra_review.py",
    "test_canonical.py",
    "test_condition.py",
    "test_condition_matrix.py",
    "test_contract_manifest.py",
    "test_dual_objective.py",
    "test_environment.py",
    "test_evidence.py",
    "test_firewall.py",
    "test_geometry.py",
    "test_locks.py",
    "test_lane1_trainer.py",
    "test_package_b.py",
    "test_package_f.py",
    "test_package_f_manifest_v2.py",
    "test_pipeline.py",
    "test_primitives.py",
    "test_root_orchestration.py",
    "test_task_change.py",
)

# Rows the handoff permits to become ``verified`` in Phase 1A (only with complete evidence).
ELIGIBLE_ROWS = ("P1-00", "P1-01", "P1-06", "P1-07", "P1-08", "P1-09", "P1-10", "P1-12", "P1-19", "P1-20")
# Exercised by validators and synthetic canaries but never ``verified`` in Phase 1A.
VALIDATION_ONLY_ROWS = ("P1-02", "P1-03")
# Forced deferrals with the exact status their original row permits.
DEFERRED_ROWS = {
    "P1-04": "untested", "P1-05": "untested", "P1-11": "untested", "P1-13": "untested", "P1-14": "untested",
    "P1-15": "untested", "P1-16": "untested", "P1-17a": "untested", "P1-17b": "blocked_external", "P1-18": "untested",
}

_CODE = "src/mmbu_phase1/"
COMMON_EVIDENCE = ("source-state.json", "commands/phase1-focused-tests.json", "tests/phase1-test-inventory.json")
RUN_EVIDENCE = ("records/execution-condition.json", "records/example-manifest.json", "records/experiment-base.json",
                "records/experiment-adapted.json", "runs/base/output-manifest.json", "runs/adapted/output-manifest.json",
                "runs/base/run.json", "runs/adapted/run.json", "runs/base/reproducibility.json",
                "runs/adapted/reproducibility.json", "runs/launch/environment-launch-receipt.json")

# requirement -> (code paths, test-ID prefixes, {stable behavior: test-ID prefixes}, evidence paths, limitations)
ROW_SPECS = {
    "P1-00": (
        ("tools/team.py", _CODE + "scope.py", _CODE + "authority.py"),
        ("test_root_orchestration.", "test_authority.BootstrapCommandTests.test_repository_authority_files_validate"),
        {"historical_bundle_remains_byte_immutable":
         ("test_root_orchestration.HistoricalImmutabilityTests.test_historical_bundle_remains_byte_immutable",)},
        ("commands/team-test.json", "commands/verify-evidence.json", "authority/current-status.json"),
        ("Root-orchestration evidence comes from this checkout's command logs on one Python version; the CI matrix "
         "(3.11/3.12/3.14 on Linux) was not executed in this attempt.",),
    ),
    "P1-01": (
        (_CODE + "status.py", _CODE + "authority.py"),
        ("test_authority.CurrentStatusTests.", "test_authority.BootstrapCommandTests.",
         "test_authority.GenerationZeroRegistryTests."),
        {},
        ("authority/current-status.json", "authority/status-evidence/predecessor.json",
         "authority/status-evidence/b1.json", "authority/status-evidence/b2-projector.json",
         "authority/status-evidence/b2-dual.json", "commands/authority-verify.json"),
        ("Status is design_only; every account, allocation, GPU, and data-admission fact remains unknown or "
         "blocked_external, while only exact bounded synthetic native-runtime facts are measured.",
         "Account facts cannot be promoted by per-job runtime receipts because no account-wide allocation-evidence "
         "schema or receipt exists.",
         "Unmeasured facts must carry null value and unit (a stricter reading of the status schema)."),
    ),
    "P1-06": (
        (_CODE + "phase1a_child.py", _CODE + "layers.py", _CODE + "evaluator.py"),
        ("test_pipeline.RawOutputTests.",),
        {"raw_output_is_immutable": ("test_pipeline.RawOutputTests.",),
         "runner_rejects_effective_decoding_drift":
         ("test_pipeline.RawOutputTests.test_runner_rejects_effective_decoding_drift",)},
        RUN_EVIDENCE,
        ("Raw records come from a synthetic stateless responder, not a model; token IDs are synthetic UTF-8 byte tokens.",
         "The per-example raw record packs the separate task and context call transcripts losslessly (synthetic adapter).",
         "Read-only file modes and content addressing are filesystem-level; tamper detection is by digest."),
    ),
    "P1-07": (
        (_CODE + "layers.py", _CODE + "evaluator.py", _CODE + "canonical.py"),
        ("test_pipeline.LayerTests.", "test_canonical.ParserStrictnessTests."),
        {"parsed_validated_and_judged_layers_bind_parent_hash": ("test_pipeline.LayerTests.",)},
        RUN_EVIDENCE,
        ("Inexact or unrepresentable JSON numbers and non-object values map to invalid_json under the strict kernel.",
         "Any task- or context-call parse failure fails the whole evaluation row (one per-example layer status).",
         "Synthetic adapter output schemas only; official task/context JSON keys remain unfrozen."),
    ),
    "P1-08": (
        (_CODE + "layers.py", _CODE + "phase1a_child.py", _CODE + "summaries.py"),
        ("test_pipeline.FailureStateTests.", "test_task_change.NegativeArithmeticTests.test_failures_remain_in_denominator"),
        {"runtime_failure_layer_state_is_legal": ("test_pipeline.FailureStateTests.test_runtime_failure_layer_state_is_legal",),
         "failure_stages_remain_orthogonal": ("test_pipeline.FailureStateTests.test_failure_stages_remain_orthogonal",),
         "failures_remain_in_denominator": ("test_pipeline.FailureStateTests.test_failures_remain_in_denominator",
                                            "test_task_change.NegativeArithmeticTests.test_failures_remain_in_denominator"),
         "geometry_judge_failure_preserves_validated_result":
         ("test_pipeline.FailureStateTests.test_geometry_judge_failure_preserves_validated_result",)},
        RUN_EVIDENCE + ("summaries/task-change.json",),
        ("Runtime failures (load, preprocess, timeout, OOM, generation) and judge failures are injected by the synthetic "
         "responder and judge policy; no native runtime failure occurred.",),
    ),
    "P1-09": (
        (_CODE + "synthetic.py", _CODE + "layers.py", _CODE + "condition.py"),
        ("test_pipeline.FixtureTests.",),
        {"task_context_calls_are_stateless": ("test_pipeline.FixtureTests.test_task_context_calls_are_stateless",),
         "context_schema_uses_requested_field_subset":
         ("test_pipeline.FixtureTests.test_context_schema_uses_requested_field_subset",)},
        RUN_EVIDENCE + ("records/prompt-schema-contract.json",),
        ("The fixture is entirely synthetic (36 rows); it is not biomedical, official, or model-performance evidence.",
         "Statelessness is shown for synthetic calls (pure functions of request bytes plus sentinels); native task/context "
         "statelessness is P1-05 and untested."),
    ),
    "P1-10": (
        (_CODE + "task_change.py", _CODE + "rational.py", _CODE + "condition.py", _CODE + "experiment.py",
         _CODE + "summaries.py"),
        ("test_task_change.", "test_condition.PairedConditionTests.", "test_condition_matrix.",
         "test_pipeline.TaskChangeEndToEndTests.", "test_primitives.RationalWireTests."),
        {"continuous_task_change_identity_holds": ("test_task_change.ConformanceVectorTests.test_continuous_task_change_identity_holds",
                                                   "test_pipeline.TaskChangeEndToEndTests.test_continuous_task_change_summary_recomputes"),
         "exact_rational_wire_rejects_float_unreduced_negative_denominator_and_alt_zero":
         ("test_primitives.RationalWireTests.test_exact_rational_wire_rejects_float_unreduced_negative_denominator_and_alt_zero",),
         "binary_flip_rate_identity_holds_when_applicable":
         ("test_task_change.ConformanceVectorTests.test_binary_flip_rate_identity_holds_when_applicable",),
         "paired_condition_rejects_each_non_model_field_drift":
         ("test_condition.PairedConditionTests.test_paired_condition_rejects_each_non_model_field_drift",),
         "paired_condition_allows_only_closed_model_identity_difference":
         ("test_condition.PairedConditionTests.test_paired_condition_allows_only_closed_model_identity_difference",),
         "execution_condition_rejects_each_leaf_mutation":
         ("test_condition_matrix.MutationMatrixTests.test_execution_condition_rejects_each_leaf_mutation",),
         "execution_condition_matches_raw_run_and_reproducibility":
         ("test_condition_matrix.MutationMatrixTests.test_execution_condition_matches_raw_run_and_reproducibility",)},
        RUN_EVIDENCE + ("records/paired-condition-contract.json", "summaries/task-change.json"),
        ("Base and adapted models are synthetic responder tables; the task-change totals are engineering mechanics, "
         "not model improvement or a competition result.",
         "The binary flip table uses the prospectively bound synthetic predicate task_grade == 1."),
    ),
    "P1-12": (
        (_CODE + "geometry.py", _CODE + "summaries.py", _CODE + "evaluator.py"),
        ("test_geometry.", "test_pipeline.GeometryEndToEndTests."),
        {"boxes_are_not_silently_repaired": ("test_geometry.GeometryRuleTests.test_boxes_are_not_silently_repaired",),
         "geometry_failure_uses_nulls_without_fabricated_prediction":
         ("test_geometry.ConformanceVectorTests.test_failure_projections_have_exact_null_rules",
          "test_geometry.GeometryRuleTests.test_empty_parsed_array_is_evidence_not_fabrication"),
         "geometry_validation_failure_distinguishes_missing_and_present_array":
         ("test_geometry.ConformanceVectorTests.test_geometry_validation_failure_distinguishes_missing_and_present_array",),
         "geometry_judge_failure_preserves_validated_result":
         ("test_geometry.ConformanceVectorTests.test_geometry_judge_failure_preserves_validated_result",),
         "geometry_match_pairs_are_zero_based_sorted_and_exact":
         ("test_geometry.ConformanceVectorTests.test_any_one_and_all_targets_vectors",
          "test_pipeline.GeometryEndToEndTests.test_tampered_geometry_summary_rejects"),
         "geometry_exact_tie_uses_lexicographic_matching":
         ("test_geometry.ConformanceVectorTests.test_geometry_exact_tie_uses_lexicographic_matching",),
         "prompt_geometry_threshold_matches_condition_evaluator_validator_and_summary":
         ("test_pipeline.GeometryEndToEndTests.test_prompt_geometry_threshold_matches_condition_evaluator_validator_and_summary",)},
        RUN_EVIDENCE + ("summaries/geometry-base.json", "summaries/geometry-adapted.json"),
        ("Geometry is computed on synthetic boxes in a synthetic 100x80 frame with the synthetic threshold 1/2; the "
         "official threshold and harness behavior are not claimed.",),
    ),
    "P1-19": (
        (_CODE + "prompt_contract.py", _CODE + "condition.py", _CODE + "synthetic.py"),
        ("test_condition.PromptSchemaContractTests.",),
        {"prompt_schema_contract_is_digest_bound":
         ("test_condition.PromptSchemaContractTests.test_prompt_schema_contract_is_digest_bound",),
         "unconfirmed_contract_is_not_official_equivalent":
         ("test_condition.PromptSchemaContractTests.test_unconfirmed_contract_is_not_official_equivalent",),
         "prompt_geometry_threshold_matches_condition_evaluator_validator_and_summary":
         ("test_condition.PromptSchemaContractTests.test_threshold_projection_drift_rejects",)},
        ("records/prompt-schema-contract.json", "records/execution-condition.json", "artifacts/specs/validator.json",
         "artifacts/specs/evaluator.json"),
        ("The only executed contract has status synthetic with no official sources; brief_snapshot and "
         "organizer_confirmed rules are validated on synthetic records only.",),
    ),
    "P1-20": (
        (_CODE + "contract_manifest.py", _CODE + "bundle.py"),
        ("test_contract_manifest.", "test_bundle.FreshCloneTests."),
        {"fresh_clone_contains_governing_contract": ("test_bundle.FreshCloneTests.",)},
        ("commands/verify-contract.json", "source-state.json"),
        ("Fresh-clone proof is the clean-state reproduction in a temporary checkout of the pinned commit with the "
         "canonical patch applied; no parent workspace path is read.",),
    ),
    "P1-02": (
        (_CODE + "lineage.py", _CODE + "decisions.py"),
        ("test_firewall.",),
        {"firewall_rejects_public_source_for_promotion": ("test_firewall.EffectivePurposeTests.test_firewall_rejects_public_source_for_promotion",),
         "firewall_rejects_public_derivative_for_promotion": ("test_firewall.EffectivePurposeTests.test_firewall_rejects_public_derivative_for_promotion",),
         "lineage_receipt_is_required_for_promotion": ("test_firewall.EffectivePurposeTests.test_lineage_receipt_is_required_for_promotion",),
         "governance_reference_does_not_enter_data_purpose_intersection":
         ("test_firewall.EffectivePurposeTests.test_governance_reference_does_not_enter_data_purpose_intersection",),
         "content_artifact_cannot_claim_governance_role": ("test_firewall.EffectivePurposeTests.test_content_artifact_cannot_claim_governance_role",),
         "official_rule_summary_requires_two_reviewed_span_receipt":
         ("test_firewall.RuleSummaryTests.test_official_rule_summary_requires_two_reviewed_span_receipt",),
         "decision_plan_precedes_protected_input_opening": ("test_firewall.DecisionReceiptTests.test_decision_plan_precedes_protected_input_opening",),
         "decision_runner_rejects_unallowlisted_mount_read_and_network":
         ("test_firewall.DecisionReceiptTests.test_decision_runner_rejects_unallowlisted_mount_read_and_network",),
         "decision_lineage_covers_every_mounted_content_input":
         ("test_firewall.DecisionReceiptTests.test_decision_lineage_covers_every_mounted_content_input",),
         "copied_rationale_and_manual_decision_payload_are_ineligible":
         ("test_firewall.DecisionReceiptTests.test_copied_rationale_and_manual_decision_payload_are_ineligible",),
         "decision_operator_cannot_self_review": ("test_firewall.DecisionReceiptTests.test_decision_operator_cannot_self_review",)},
        (),
        ("Validation-only: declared records and synthetic canaries are rejected; no real hermetic decision sandbox, "
         "mount isolation, network-denial proof, or read tracing exists, so P1-02 cannot be verified in Phase 1A.",),
    ),
    "P1-03": (
        (_CODE + "admission.py", _CODE + "registries.py", _CODE + "locks.py", _CODE + "environment.py",
         _CODE + "condition.py", _CODE + "experiment.py"),
        ("test_admission.", "test_locks.", "test_environment.", "test_authority.GenerationZeroRegistryTests.",
         "test_firewall.LineageRecordTests.test_purpose_and_split_are_independent"),
        {"purpose_and_split_are_independent": ("test_firewall.LineageRecordTests.test_purpose_and_split_are_independent",),
         "environment_launch_starts_empty_and_matches_policy_receipt_condition_and_reproducibility":
         ("test_environment.LaunchTests.test_environment_launch_starts_empty_and_matches_policy_receipt",),
         "environment_launch_rejects_inheritance_unknown_change_and_parent_canary":
         ("test_environment.LaunchTests.test_environment_launch_rejects_inheritance_unknown_change_and_parent_canary",)},
        (),
        ("Validation-only subset: legacy_migration, resource_measurement, and forward_backward validators are not "
         "implemented; sampling, conversion, and approval functions are bound by digest and checked by projection, "
         "not re-executed; no real source was acquired or admitted.",),
    ),
}
DEFERRAL_REASONS = {
    "P1-04": "A separate bounded B1 synthetic preflight exists, but no model or weights execute in the Phase 1A bundle and no biomedical task evidence exists.",
    "P1-05": "Native task/context calls were not executed; only synthetic stateless calls exist (see P1-09).",
    "P1-11": "Visual-benefit states require verified answer-changing native pairs; not implemented in Phase 1A.",
    "P1-13": "Separate bounded B1/B2 synthetic native steps exist, but the Phase 1A bundle runs no native collator, model forward/backward, or optimizer step.",
    "P1-14": "Separate bounded B1/B2-P export and offline-reload receipts exist, but Phase 1A has no native adapter save/reload/resume result.",
    "P1-15": "The empty-mapping launch and synthetic reproducibility records exist, but resource_measurement is not "
             "implemented for the Phase 1A run; separate native receipts do not supply its resource record.",
    "P1-16": "No generation-path fixture schema was prepared in Phase 1A.",
    "P1-17a": "Local R0 release preflight was not implemented in Phase 1A.",
    "P1-17b": "External repository lifecycle requires a separate user-directed step and organizer route; nothing was "
              "created, uploaded, or downloaded.",
    "P1-18": "Evidence-manifest and source-state validators exist, but the full evidence-discovery contract (native, "
             "release, resource, and real-source artifacts) cannot be satisfied in Phase 1A.",
}
