"""Claims, requirement trace, and the non-self-referential phase decision (P1-21).

Inputs are exactly the 22 rows P1-00..P1-16, P1-17a, P1-17b, P1-18..P1-20.
P1-21 is the validated decision record itself and is never an input.

* ``rejected`` if any row is ``failed`` or any automatic-rejection predicate
  fires (including verified-without-evidence and an invalid root/trace);
* ``accepted`` if every row except P1-17b is ``verified`` and P1-17b is
  ``verified`` or ``blocked_external``;
* ``returned_blocked`` otherwise.
"""

from __future__ import annotations

from typing import Any, Mapping

from mmbu_phase1 import fields as f, paths
from mmbu_phase1.vocab import CLAIM_STATUSES, PHASE_DECISIONS

INPUT_IDS = tuple([f"P1-{i:02d}" for i in range(17)] + ["P1-17a", "P1-17b"] + [f"P1-{i}" for i in (18, 19, 20)])
STABLE_BEHAVIORS = (
    "firewall_rejects_public_source_for_promotion",
    "firewall_rejects_public_derivative_for_promotion",
    "historical_bundle_remains_byte_immutable",
    "purpose_and_split_are_independent",
    "lineage_receipt_is_required_for_promotion",
    "governance_reference_does_not_enter_data_purpose_intersection",
    "content_artifact_cannot_claim_governance_role",
    "official_rule_summary_requires_two_reviewed_span_receipt",
    "decision_plan_precedes_protected_input_opening",
    "decision_runner_rejects_unallowlisted_mount_read_and_network",
    "decision_lineage_covers_every_mounted_content_input",
    "copied_rationale_and_manual_decision_payload_are_ineligible",
    "decision_operator_cannot_self_review",
    "promotable_experiment_binds_complete_decision_receipts",
    "runner_rejects_record_digest_mismatch",
    "runner_rejects_inherited_generation_defaults",
    "runner_rejects_effective_decoding_drift",
    "task_context_calls_are_stateless",
    "raw_output_is_immutable",
    "parsed_validated_and_judged_layers_bind_parent_hash",
    "runtime_failure_layer_state_is_legal",
    "failure_stages_remain_orthogonal",
    "failures_remain_in_denominator",
    "paired_condition_rejects_each_non_model_field_drift",
    "paired_condition_allows_only_closed_model_identity_difference",
    "execution_condition_rejects_each_leaf_mutation",
    "execution_condition_matches_raw_run_and_reproducibility",
    "continuous_task_change_identity_holds",
    "exact_rational_wire_rejects_float_unreduced_negative_denominator_and_alt_zero",
    "binary_flip_rate_identity_holds_when_applicable",
    "visual_benefit_transition_table_is_complete",
    "boxes_are_not_silently_repaired",
    "geometry_failure_uses_nulls_without_fabricated_prediction",
    "geometry_validation_failure_distinguishes_missing_and_present_array",
    "geometry_judge_failure_preserves_validated_result",
    "geometry_match_pairs_are_zero_based_sorted_and_exact",
    "geometry_exact_tie_uses_lexicographic_matching",
    "native_collator_masks_only_declared_targets",
    "real_backward_reaches_declared_modules",
    "fresh_process_reload_matches",
    "interrupted_resume_preserves_state_order_and_exposure",
    "reproducibility_record_binds_effective_environment_and_command",
    "environment_launch_starts_empty_and_matches_policy_receipt_condition_and_reproducibility",
    "environment_launch_rejects_inheritance_unknown_change_and_parent_canary",
    "prompt_geometry_threshold_matches_condition_evaluator_validator_and_summary",
    "seed_namespaces_and_sampler_order_are_stable",
    "clean_cache_replay_rejects_hidden_network_fetch",
    "result_chosen_or_wrong_object_tolerance_is_rejected",
    "prompt_schema_contract_is_digest_bound",
    "context_schema_uses_requested_field_subset",
    "unconfirmed_contract_is_not_official_equivalent",
    "evidence_bundle_root_detects_deletion_and_replacement",
    "evidence_manifest_rejects_alias_traversal_symlink_and_collision",
    "source_state_detects_dirty_or_post_evidence_drift",
    "fresh_clone_contains_governing_contract",
    "phase_decision_is_derived_without_self_reference",
    "release_manifest_detects_missing_or_changed_file",
    "release_scan_detects_secret_and_private_path",
)
REJECTION_PREDICATES = (
    "deferred_row_verified",
    "evidence_root_or_trace_invalid",
    "external_upload_without_user_step",
    "failed_mandatory_row",
    "failed_rows_left_denominator",
    "historical_bundle_changed",
    "local_preflight_called_external_r0",
    "native_backward_missed_declared_modules",
    "promotable_decision_missing_controls",
    "public_content_in_development_or_decision",
    "raw_output_missing_or_repaired",
    "reload_not_fresh_offline",
    "resource_facts_estimated",
    "rule_summary_without_two_reviewer_extraction",
    "run_not_bound_to_declarations",
    "self_reference",
    "synthetic_called_medical_or_model_evidence",
    "task_context_state_shared",
    "unconfirmed_contract_called_official_equivalent",
    "verified_row_lacks_bound_evidence",
)
SELF_REFERENTIAL_PATHS = frozenset({"claims.json", "requirement-trace.json", "phase-decision.json", "evidence-manifest.json"})
CLAIMS_KEYS = ("schema_id", "schema_version", "source_state_digest", "claims", "created_at", "record_digest")
ROW_KEYS = ("requirement_id", "status", "code_paths", "test_ids", "evidence_paths", "evidence_digests", "limitations")
TRACE_KEYS = ("schema_id", "schema_version", "source_state_digest", "claims_digest", "rows", "created_at", "record_digest")
TRACE_ROW_KEYS = ("requirement_id", "behaviors", "test_ids", "evidence_paths")
DECISION_KEYS = ("schema_id", "schema_version", "claims_digest", "trace_digest", "decision", "rejection_predicates",
                 "derived_at", "record_digest")


def _rows(value: Any, path: str, keys: tuple[str, ...]) -> list[dict]:
    rows = f.array(value, path)
    for index, row in enumerate(rows):
        f.closed(row, f"{path}[{index}]", keys)
    ids = [row["requirement_id"] for row in rows]
    f.require("P1-21" not in ids, path, "P1-21 is the derived decision and never an input row")
    f.require(ids == list(INPUT_IDS), path, "must contain exactly the 22 input rows once each, in canonical order")
    return rows


def validate_claims(record: Any, path: str = "claims") -> dict:
    f.record(record, "claims", CLAIMS_KEYS, path)
    f.digest(record["source_state_digest"], f"{path}.source_state_digest")
    for index, row in enumerate(_rows(record["claims"], f"{path}.claims", ROW_KEYS)):
        label = f"{path}.claims[{row['requirement_id']}]"
        status = f.one_of(row["status"], f"{label}.status", CLAIM_STATUSES)
        code = f.string_set(row["code_paths"], f"{label}.code_paths")
        tests = f.string_set(row["test_ids"], f"{label}.test_ids")
        evidence = f.string_set(row["evidence_paths"], f"{label}.evidence_paths")
        for item in code + evidence:
            paths.relative_path(item, label)
        digests = f.array(row["evidence_digests"], f"{label}.evidence_digests")
        f.require(len(digests) == len(evidence), f"{label}.evidence_digests", "one digest per evidence path, in order")
        for item in digests:
            f.digest(item, f"{label}.evidence_digests")
        limitations = f.array(row["limitations"], f"{label}.limitations", nonempty=True)
        for item in limitations:
            f.text(item, f"{label}.limitations")
        if status == "verified":
            f.require(bool(code) and bool(tests) and bool(evidence), label,
                      "a verified row names its code paths, tests, and exact evidence")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def validate_requirement_trace(record: Any, claims: dict, path: str = "requirement_trace") -> dict:
    f.record(record, "requirement_trace", TRACE_KEYS, path)
    f.require(record["source_state_digest"] == claims["source_state_digest"], f"{path}.source_state_digest",
              "trace and claims bind different source states")
    f.require(record["claims_digest"] == claims["record_digest"], f"{path}.claims_digest", "does not bind these claims")
    claim_rows = {row["requirement_id"]: row for row in claims["claims"]}
    for row in _rows(record["rows"], f"{path}.rows", TRACE_ROW_KEYS):
        label = f"{path}.rows[{row['requirement_id']}]"
        behaviors = f.array(row["behaviors"], f"{label}.behaviors")
        mapped = set()
        for item in behaviors:
            f.closed(item, f"{label}.behaviors", ("behavior", "test_ids"))
            f.one_of(item["behavior"], f"{label}.behaviors.behavior", STABLE_BEHAVIORS)
            mapped.update(f.string_set(item["test_ids"], f"{label}.behaviors.test_ids", nonempty=True))
        f.sorted_unique(behaviors, f"{label}.behaviors", lambda item: item["behavior"].encode())
        tests = f.string_set(row["test_ids"], f"{label}.test_ids")
        f.require(mapped <= set(tests), f"{label}.behaviors", "behavior tests must be listed row tests")
        f.require(tests == claim_rows[row["requirement_id"]]["test_ids"], f"{label}.test_ids", "differs from the claim row")
        f.require(f.string_set(row["evidence_paths"], f"{label}.evidence_paths")
                  == claim_rows[row["requirement_id"]]["evidence_paths"], f"{label}.evidence_paths",
                  "differs from the claim row")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def validate_phase_decision(record: Any, path: str = "phase_decision") -> dict:
    f.record(record, "phase_decision", DECISION_KEYS, path)
    f.digest(record["claims_digest"], f"{path}.claims_digest")
    f.digest(record["trace_digest"], f"{path}.trace_digest")
    f.one_of(record["decision"], f"{path}.decision", PHASE_DECISIONS)
    predicates = f.array(record["rejection_predicates"], f"{path}.rejection_predicates")
    for item in predicates:
        f.closed(item, f"{path}.rejection_predicates", ("predicate_id", "fired"))
        f.one_of(item["predicate_id"], f"{path}.rejection_predicates.predicate_id", REJECTION_PREDICATES)
        f.boolean(item["fired"], f"{path}.rejection_predicates.fired")
    f.require([item["predicate_id"] for item in predicates] == list(REJECTION_PREDICATES), f"{path}.rejection_predicates",
              "must evaluate exactly the closed sorted predicate set")
    f.timestamp(record["derived_at"], f"{path}.derived_at")
    return record


def derive_decision(claim_rows: list[dict], predicates: Mapping[str, bool]) -> str:
    """The deterministic three-way decision function from ACCEPTANCE.md."""
    statuses = {row["requirement_id"]: row["status"] for row in claim_rows}
    f.require(list(statuses) == list(INPUT_IDS), "phase_decision", "inputs are exactly the 22 non-decision rows")
    f.require(set(predicates) == set(REJECTION_PREDICATES), "phase_decision", "every rejection predicate must be evaluated")
    if any(status == "failed" for status in statuses.values()) or any(predicates.values()):
        return "rejected"
    required = [rid for rid in INPUT_IDS if rid != "P1-17b"]
    if all(statuses[rid] == "verified" for rid in required) and statuses["P1-17b"] in {"verified", "blocked_external"}:
        return "accepted"
    return "returned_blocked"


def predicate_rows(predicates: Mapping[str, bool]) -> list[dict]:
    return [{"fired": bool(predicates[name]), "predicate_id": name} for name in REJECTION_PREDICATES]


def check_decision(decision: dict, claims: dict, trace: dict, predicates: Mapping[str, bool]) -> str:
    """Recompute the decision; a forged or stale decision record rejects."""
    validate_phase_decision(decision)
    f.require(decision["claims_digest"] == claims["record_digest"] and decision["trace_digest"] == trace["record_digest"],
              "phase_decision", "decision binds other claims or trace")
    for row in claims["claims"] + trace["rows"]:
        f.require(not set(row["evidence_paths"]) & SELF_REFERENTIAL_PATHS, "phase_decision",
                  "claims and trace cannot cite the decision, manifest, or themselves (self-reference)")
    f.require(f.same(decision["rejection_predicates"], predicate_rows(predicates)), "phase_decision.rejection_predicates",
              "recorded predicate evaluations differ from the recomputation")
    derived = derive_decision(claims["claims"], predicates)
    f.require(decision["decision"] == derived, "phase_decision.decision", f"forged decision; the contract derives {derived}")
    return derived
