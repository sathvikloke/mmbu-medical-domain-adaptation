"""Closed Package F competition manifest and synthetic promotion mechanics."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from mmbu_phase1 import canonical, rational, research_registry, track2_score
from mmbu_phase1.fields import (
    ContractViolation, array, boolean, closed, digest, fail, integer, literal,
    one_of, require, string_set, text, timestamp,
)


STATES = (
    "draft", "authority_blocked", "data_blocked", "native_preflight_ready", "retired",
    "native_preflight_failed", "experiment_freeze_ready", "frozen", "execution_failed",
    "executed", "confirmation_opened", "promoted", "no_eligible_candidate",
)
TRANSITIONS = {
    "draft": {"authority_blocked", "data_blocked", "native_preflight_ready", "retired"},
    "authority_blocked": {"retired"}, "data_blocked": {"retired"},
    "native_preflight_ready": {"native_preflight_failed", "experiment_freeze_ready"},
    "native_preflight_failed": set(), "experiment_freeze_ready": {"frozen"},
    "frozen": {"execution_failed", "executed", "retired"}, "execution_failed": set(),
    "executed": {"confirmation_opened"},
    "confirmation_opened": {"promoted", "no_eligible_candidate", "retired"},
    "promoted": set(), "no_eligible_candidate": set(), "retired": set(),
}
ARCHITECTURES = ("recipe_arch::B0", "recipe_arch::B1-L", "recipe_arch::B2-P", "recipe_arch::B2-F")
TOP_KEYS = (
    "artifact_registry_digest", "authority_snapshot_id", "base_selection_receipt_id", "candidate_universe",
    "canonical_digest", "created_at_utc", "data_plan", "evaluation_contract", "evidence_class", "manifest_id",
    "manifest_version", "model_pin", "promotion_contract", "protocol_contract_id", "protocol_equivalence",
    "public_firewall_policy_id", "release_contract", "research_comparison_registry", "schema_id", "schema_version",
    "scientific_decision_receipt_id", "selected_base_digest", "state", "training_contract", "unknowns",
)
DATA_KEYS = (
    "admitted_source_ids", "context_availability_mask_schema_id", "context_field_schema_id", "duplicate_policy_id",
    "frontier_decision_role_ids", "frontier_train_role_ids", "frontier_tuning_role_ids", "held_out_source_ids",
    "human_review_receipt", "independent_unit_key", "independent_unit_loss_policy_id", "prompt_lineage_groups",
    "recipe_confirmation_role_ids", "recipe_development_role_ids", "recipe_train_role_ids", "rights_receipts",
    "role_disjointness_matrix_digest", "source_ledger_digest", "split_group_keys", "task_view_manifest_digest",
    "visual_probe_audit_role_ids", "visual_probe_construction_role_ids",
)
MODEL_KEYS = (
    "attention_backend", "dependency_lock_digest", "dtype", "generation_settings_digest", "image_transform_receipt",
    "license", "local_cache_digest", "model_identifier", "model_revision", "module_map_digest",
    "processor_identifier", "processor_revision", "quantization", "source_receipt", "thinking_mode",
    "token_limits_digest", "trust_remote_code",
)
CANDIDATE_KEYS = (
    "active_flop_formula", "adapter_type", "alpha", "architecture_id", "artifact_layout_id", "base_revision",
    "candidate_id", "dropout", "enabled", "enablement_rule", "expected_trainable_parameters",
    "objective_profile_id", "optimizer_condition_id", "rank", "target_modules", "trainable_parameter_formula",
)
PROFILE_KEYS = (
    "context_balance_policy_id", "context_field_normalization", "context_protocol_status",
    "context_target_contract_id", "context_unit_share", "exposure_audit_tolerance",
    "organizer_confirmed_applicability_mask_rule", "profile_id", "requested_field_registry_digest", "schedule_id",
    "source_balance_policy_id", "task_balance_policy_id", "task_target_contract_id", "task_unit_share",
    "task_view_normalization", "token_normalization_id", "unit_total_mass", "zero_applicable_evaluation_policy",
    "zero_applicable_training_policy",
)
TRAINING_KEYS = (
    "early_stop_rule_id", "geometry", "maximum_updates", "objective_profiles", "optimizer_name",
    "optional_ablations", "preservation_policy", "public_firewall_assertion", "rationale_policy", "seed_ids",
    "serializer",
)


def manifest_digest(record: dict[str, Any]) -> str:
    """Digest a manifest while omitting only its own canonical digest."""
    if type(record) is not dict:
        fail("manifest", "must be an object")
    return canonical.value_digest({key: value for key, value in record.items() if key != "canonical_digest"})


def validate_transition(old: str, new: str) -> None:
    one_of(old, "transition.old", STATES)
    one_of(new, "transition.new", STATES)
    require(new in TRANSITIONS[old], "transition", f"illegal forward transition {old!r} -> {new!r}")


def _unknown(value: Any, path: str) -> None:
    if value == "unknown":
        return
    if path.endswith("_digest") or path.endswith("_receipt"):
        digest(value, path)
    else:
        text(value, path)


def _validate_data_plan(value: Any) -> None:
    closed(value, "manifest.data_plan", DATA_KEYS)
    for key in ("admitted_source_ids", "frontier_decision_role_ids", "frontier_train_role_ids",
                "frontier_tuning_role_ids", "held_out_source_ids", "prompt_lineage_groups",
                "recipe_confirmation_role_ids", "recipe_development_role_ids", "recipe_train_role_ids",
                "rights_receipts", "split_group_keys", "visual_probe_audit_role_ids",
                "visual_probe_construction_role_ids"):
        string_set(value[key], f"manifest.data_plan.{key}")
    for key in set(DATA_KEYS) - {"admitted_source_ids", "frontier_decision_role_ids", "frontier_train_role_ids",
                                     "frontier_tuning_role_ids", "held_out_source_ids", "prompt_lineage_groups",
                                     "recipe_confirmation_role_ids", "recipe_development_role_ids", "recipe_train_role_ids",
                                     "rights_receipts", "split_group_keys", "visual_probe_audit_role_ids",
                                     "visual_probe_construction_role_ids"}:
        _unknown(value[key], f"manifest.data_plan.{key}")
    public_terms = ("mmbu", "public")
    for key in ("admitted_source_ids", "held_out_source_ids"):
        for item in value[key]:
            require(not all(term in item.lower() for term in public_terms), f"manifest.data_plan.{key}",
                    "MMBU public content cannot enter the data plan")


def _validate_model_pin(value: Any) -> None:
    closed(value, "manifest.model_pin", MODEL_KEYS)
    for key in MODEL_KEYS:
        _unknown(value[key], f"manifest.model_pin.{key}")
    literal(value["trust_remote_code"], "manifest.model_pin.trust_remote_code", "forbidden")


def _validate_profile(value: Any, path: str) -> str:
    closed(value, path, PROFILE_KEYS)
    profile_id = text(value["profile_id"], f"{path}.profile_id")
    task = rational.from_wire(value["task_unit_share"], f"{path}.task_unit_share")
    context = rational.from_wire(value["context_unit_share"], f"{path}.context_unit_share")
    unit = rational.from_wire(value["unit_total_mass"], f"{path}.unit_total_mass")
    tolerance = rational.from_wire(value["exposure_audit_tolerance"], f"{path}.exposure_audit_tolerance")
    require(task >= 0 and context >= 0 and task + context == 1, path,
            "task/context shares must be nonnegative and sum exactly to one")
    require(unit > 0, f"{path}.unit_total_mass", "must be positive")
    require(0 <= tolerance <= Fraction(1, 100), f"{path}.exposure_audit_tolerance", "must be at most 1/100")
    one_of(value["context_protocol_status"], f"{path}.context_protocol_status",
           ("design_only", "context_proxy_executable", "context_official_equivalent"))
    one_of(value["task_view_normalization"], f"{path}.task_view_normalization",
           ("equal_within_unit", "registered_fixed_map"))
    one_of(value["context_field_normalization"], f"{path}.context_field_normalization",
           ("equal_available_fields", "registered_fixed_map"))
    one_of(value["schedule_id"], f"{path}.schedule_id", ("static", "forward", "reverse", "shuffled"))
    literal(value["zero_applicable_training_policy"], f"{path}.zero_applicable_training_policy",
            "reallocate_context_share_to_task")
    literal(value["zero_applicable_evaluation_policy"], f"{path}.zero_applicable_evaluation_policy",
            "exclude_and_report")
    boolean(value["organizer_confirmed_applicability_mask_rule"],
            f"{path}.organizer_confirmed_applicability_mask_rule")
    for key in ("task_target_contract_id", "context_target_contract_id", "source_balance_policy_id",
                "task_balance_policy_id", "context_balance_policy_id", "token_normalization_id"):
        text(value[key], f"{path}.{key}")
    digest(value["requested_field_registry_digest"], f"{path}.requested_field_registry_digest")
    return profile_id


def _validate_candidate(value: Any, path: str, profiles: set[str]) -> str:
    closed(value, path, CANDIDATE_KEYS)
    candidate_id = text(value["candidate_id"], f"{path}.candidate_id")
    architecture = one_of(value["architecture_id"], f"{path}.architecture_id", ARCHITECTURES)
    require(candidate_id.startswith(architecture + "::"), f"{path}.candidate_id",
            "must be qualified by its architecture ID")
    boolean(value["enabled"], f"{path}.enabled")
    one_of(value["adapter_type"], f"{path}.adapter_type", ("none", "lora"))
    array(value["target_modules"], f"{path}.target_modules")
    if architecture == "recipe_arch::B0":
        literal(value["objective_profile_id"], f"{path}.objective_profile_id", None)
        literal(value["adapter_type"], f"{path}.adapter_type", "none")
    else:
        require(value["objective_profile_id"] in profiles, f"{path}.objective_profile_id",
                "must resolve a declared objective profile")
        literal(value["adapter_type"], f"{path}.adapter_type", "lora")
    if architecture == "recipe_arch::B2-F":
        literal(value["enabled"], f"{path}.enabled", False)
        literal(value["enablement_rule"], f"{path}.enablement_rule", "pre_output_f0_gate")
    for key in ("base_revision", "active_flop_formula", "artifact_layout_id", "optimizer_condition_id",
                "trainable_parameter_formula"):
        text(value[key], f"{path}.{key}")
    for key in ("alpha", "dropout", "expected_trainable_parameters", "rank"):
        item = value[key]
        if item != "unknown": integer(item, f"{path}.{key}", minimum=0)
    return architecture


def _validate_training(value: Any) -> None:
    closed(value, "manifest.training_contract", TRAINING_KEYS)
    literal(value["optimizer_name"], "manifest.training_contract.optimizer_name", "AdamW")
    literal(value["public_firewall_assertion"], "manifest.training_contract.public_firewall_assertion", True)
    literal(value["preservation_policy"], "manifest.training_contract.preservation_policy", "no_kl_primary")
    one_of(value["rationale_policy"], "manifest.training_contract.rationale_policy",
           ("answer_only_training", "source_supported_rationale"))
    if value["rationale_policy"] == "source_supported_rationale":
        fail("manifest.training_contract.rationale_policy", "source receipts are absent from the Package F schema fixture")
    string_set(value["seed_ids"], "manifest.training_contract.seed_ids")
    closed(value["optional_ablations"], "manifest.training_contract.optional_ablations", ("A1", "A2"))
    literal(value["optional_ablations"]["A1"], "manifest.training_contract.optional_ablations.A1", False)
    literal(value["optional_ablations"]["A2"], "manifest.training_contract.optional_ablations.A2", False)
    geometry = closed(value["geometry"], "manifest.training_contract.geometry",
                      ("box_format", "coordinate_frame", "inverse_transform_receipt", "origin", "repair_policy", "source_edges"))
    literal(geometry["box_format"], "manifest.training_contract.geometry.box_format", "xywh")
    literal(geometry["coordinate_frame"], "manifest.training_contract.geometry.coordinate_frame", "original_pixel")
    literal(geometry["origin"], "manifest.training_contract.geometry.origin", "zero_based")
    literal(geometry["source_edges"], "manifest.training_contract.geometry.source_edges", "half_open")
    literal(geometry["repair_policy"], "manifest.training_contract.geometry.repair_policy", "reject")
    _unknown(geometry["inverse_transform_receipt"], "manifest.training_contract.geometry.inverse_transform_receipt")
    serializer = closed(value["serializer"], "manifest.training_contract.serializer",
                        ("inference_output_format_id", "malformed_json_policy", "terminal_json_required",
                         "training_target_format_id"))
    literal(serializer["terminal_json_required"], "manifest.training_contract.serializer.terminal_json_required", True)
    literal(serializer["malformed_json_policy"], "manifest.training_contract.serializer.malformed_json_policy",
            "incorrect_no_repair")
    text(serializer["training_target_format_id"], "manifest.training_contract.serializer.training_target_format_id")
    text(serializer["inference_output_format_id"], "manifest.training_contract.serializer.inference_output_format_id")
    profiles = array(value["objective_profiles"], "manifest.training_contract.objective_profiles", nonempty=True)
    profile_ids = [_validate_profile(item, f"manifest.training_contract.objective_profiles[{index}]")
                   for index, item in enumerate(profiles)]
    require(profile_ids == sorted(set(profile_ids), key=lambda item: item.encode("utf-8")),
            "manifest.training_contract.objective_profiles", "profile IDs must be unique and UTF-8 sorted")


def _profiles(value: dict) -> set[str]:
    return {item["profile_id"] for item in value["training_contract"]["objective_profiles"]}


def _validate_evaluation(value: Any, candidate_ids: set[str]) -> None:
    closed(value, "manifest.evaluation_contract", ("bootstrap_seed_ids", "candidate_comparator_map", "context_status",
                                                     "metric_ids", "one_confirmation_opening", "paired_group_bootstrap"))
    string_set(value["bootstrap_seed_ids"], "manifest.evaluation_contract.bootstrap_seed_ids", nonempty=True)
    string_set(value["metric_ids"], "manifest.evaluation_contract.metric_ids", nonempty=True)
    literal(value["one_confirmation_opening"], "manifest.evaluation_contract.one_confirmation_opening", True)
    literal(value["paired_group_bootstrap"], "manifest.evaluation_contract.paired_group_bootstrap", True)
    one_of(value["context_status"], "manifest.evaluation_contract.context_status",
           ("design_only", "context_proxy_executable", "context_official_equivalent"))
    mapping = value["candidate_comparator_map"]
    if type(mapping) is not dict: fail("manifest.evaluation_contract.candidate_comparator_map", "must be an object")
    for candidate_id, comparators in mapping.items():
        require(candidate_id in candidate_ids, "manifest.evaluation_contract.candidate_comparator_map",
                "unknown candidate key")
        string_set(comparators, f"manifest.evaluation_contract.candidate_comparator_map.{candidate_id}", nonempty=True)
        require(set(comparators) <= candidate_ids, f"manifest.evaluation_contract.candidate_comparator_map.{candidate_id}",
                "comparator must resolve a candidate")


def _validate_promotion(value: Any) -> None:
    closed(value, "manifest.promotion_contract", ("decision_function_id", "one_named_candidate_only",
                                                    "required_gate_ids", "runner_up_rescue"))
    text(value["decision_function_id"], "manifest.promotion_contract.decision_function_id")
    literal(value["one_named_candidate_only"], "manifest.promotion_contract.one_named_candidate_only", True)
    literal(value["runner_up_rescue"], "manifest.promotion_contract.runner_up_rescue", False)
    string_set(value["required_gate_ids"], "manifest.promotion_contract.required_gate_ids", nonempty=True)


def _validate_release(value: Any) -> None:
    closed(value, "manifest.release_contract", ("allowed_loader_id", "artifact_inventory_digest", "human_approval_receipt",
                                                  "network_denied_reload_required", "rollback_identity",
                                                  "upload_verification_receipt"))
    literal(value["network_denied_reload_required"], "manifest.release_contract.network_denied_reload_required", True)
    for key in set(value) - {"network_denied_reload_required"}:
        _unknown(value[key], f"manifest.release_contract.{key}")


def _contains_unknown(value: Any) -> bool:
    if value == "unknown": return True
    if type(value) is list: return any(_contains_unknown(item) for item in value)
    if type(value) is dict: return any(_contains_unknown(item) for item in value.values())
    return False


def validate_manifest(value: Any) -> dict:
    """Validate one closed Package F manifest without granting execution."""
    closed(value, "manifest", TOP_KEYS)
    literal(value["schema_id"], "manifest.schema_id", "mmbu.competition.manifest")
    literal(value["schema_version"], "manifest.schema_version", 1)
    text(value["manifest_version"], "manifest.manifest_version")
    text(value["manifest_id"], "manifest.manifest_id")
    timestamp(value["created_at_utc"], "manifest.created_at_utc")
    one_of(value["evidence_class"], "manifest.evidence_class",
           ("design_only", "synthetic_only", "native_preflight", "biomedical_experiment"))
    state = one_of(value["state"], "manifest.state", STATES)
    digest(value["artifact_registry_digest"], "manifest.artifact_registry_digest")
    literal(value["protocol_equivalence"], "manifest.protocol_equivalence", "synthetic")
    literal(value["public_firewall_policy_id"], "manifest.public_firewall_policy_id",
            "no_mmbu_public_or_derivatives_v1")
    for key in ("authority_snapshot_id", "protocol_contract_id"): text(value[key], f"manifest.{key}")
    for key in ("scientific_decision_receipt_id", "base_selection_receipt_id", "selected_base_digest"):
        _unknown(value[key], f"manifest.{key}")
    _validate_model_pin(value["model_pin"])
    _validate_data_plan(value["data_plan"])
    _validate_training(value["training_contract"])
    candidates = array(value["candidate_universe"], "manifest.candidate_universe", nonempty=True)
    profiles = _profiles(value)
    architecture_ids = [_validate_candidate(item, f"manifest.candidate_universe[{index}]", profiles)
                        for index, item in enumerate(candidates)]
    require(tuple(architecture_ids) == ARCHITECTURES, "manifest.candidate_universe",
            "must contain exactly B0, B1-L, B2-P, B2-F in frozen order")
    candidate_ids = [item["candidate_id"] for item in candidates]
    require(len(candidate_ids) == len(set(candidate_ids)), "manifest.candidate_universe", "candidate IDs must be unique")
    _validate_evaluation(value["evaluation_contract"], set(candidate_ids))
    _validate_promotion(value["promotion_contract"])
    research_registry.validate_registry(value["research_comparison_registry"],
                                        {"execution_candidate_ids": [], "lane1_candidate_ids": candidate_ids,
                                         "public_ancestry": []})
    _validate_release(value["release_contract"])
    string_set(value["unknowns"], "manifest.unknowns")
    require(value["canonical_digest"] == manifest_digest(value), "manifest.canonical_digest",
            "does not equal the canonical manifest digest")
    if state in {"experiment_freeze_ready", "frozen", "execution_failed", "executed", "confirmation_opened",
                 "promoted", "no_eligible_candidate"}:
        require(not value["unknowns"] and not _contains_unknown({k: v for k, v in value.items()
                                                                  if k != "canonical_digest"}),
                "manifest.state", "freeze or later state cannot contain unknown scientific or authority values")
    return value


def _decision_contract(value: Any) -> dict:
    closed(value, "decision", ("candidate_order", "context_bounds", "positive_task_gain_floor", "practical_margin",
                               "promotion_candidate_id", "required_gate_ids"))
    order = string_set(value["candidate_order"], "decision.candidate_order", nonempty=True)
    require(value["promotion_candidate_id"] in order, "decision.promotion_candidate_id", "must be in candidate order")
    bounds = array(value["context_bounds"], "decision.context_bounds")
    require(len(bounds) == 2, "decision.context_bounds", "must contain lower and upper bounds")
    lower, upper = (rational.from_wire(item, f"decision.context_bounds[{index}]") for index, item in enumerate(bounds))
    require(0 <= lower <= upper <= 1, "decision.context_bounds", "must be ordered inside [0, 1]")
    floor = rational.from_wire(value["positive_task_gain_floor"], "decision.positive_task_gain_floor")
    margin = rational.from_wire(value["practical_margin"], "decision.practical_margin")
    require(floor >= 0 and margin >= 0, "decision", "floor and margin must be nonnegative")
    string_set(value["required_gate_ids"], "decision.required_gate_ids", nonempty=True)
    return {"lower": lower, "upper": upper, "floor": floor, "margin": margin}


def _result(value: Any, path: str) -> dict:
    closed(value, path, ("base_task", "candidate_id", "context", "gates", "task"))
    text(value["candidate_id"], f"{path}.candidate_id")
    task = rational.from_wire(value["task"], f"{path}.task")
    context = rational.from_wire(value["context"], f"{path}.context")
    base_task = rational.from_wire(value["base_task"], f"{path}.base_task")
    for name, score in (("task", task), ("context", context), ("base_task", base_task)):
        require(0 <= score <= 1, f"{path}.{name}", "must be in [0, 1]")
    if type(value["gates"]) is not dict: fail(f"{path}.gates", "must be an object")
    for gate, passed in value["gates"].items():
        text(gate, f"{path}.gates.key"); boolean(passed, f"{path}.gates.{gate}")
    return {"task": task, "context": context, "base_task": base_task, "gates": value["gates"]}


def evaluate_promotion(contract: Any, results: Any, base_id: str, comparator_ids: list[str]) -> str:
    """Apply the frozen synthetic decision; failure never promotes a runner-up."""
    decision = _decision_contract(contract)
    if type(results) is not dict: fail("results", "must be an object keyed by candidate ID")
    promotion_id = contract["promotion_candidate_id"]
    required_ids = [base_id, promotion_id, *comparator_ids]
    if any(item not in results for item in required_ids): return "no_eligible_candidate"
    parsed = {item: _result(results[item], f"results.{item}") for item in set(required_ids)}
    for result_id in set(required_ids):
        literal(results[result_id]["candidate_id"], f"results.{result_id}.candidate_id", result_id)
    promoted = parsed[promotion_id]
    if promoted["task"] - promoted["base_task"] <= decision["floor"]: return "no_eligible_candidate"
    if set(promoted["gates"]) != set(contract["required_gate_ids"]): return "no_eligible_candidate"
    if not all(promoted["gates"].values()): return "no_eligible_candidate"
    for comparator_id in set([base_id, *comparator_ids]):
        comparator = parsed[comparator_id]
        for context_bound in (decision["lower"], decision["upper"]):
            candidate_score = track2_score.score_proxy(promoted["task"], context_bound, promoted["base_task"])
            comparator_score = track2_score.score_proxy(comparator["task"], context_bound, comparator["base_task"])
            if candidate_score - comparator_score <= decision["margin"]: return "no_eligible_candidate"
    return promotion_id


__all__ = ["ContractViolation", "evaluate_promotion", "manifest_digest", "validate_manifest", "validate_transition"]
