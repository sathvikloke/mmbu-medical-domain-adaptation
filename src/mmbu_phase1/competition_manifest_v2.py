"""Additive Package F competition-manifest schema version 2.

Version 2 permits multiple objective profiles per architecture.  It validates
design records only and grants no authority to execute an experiment.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from mmbu_phase1 import competition_manifest as v1
from mmbu_phase1 import rational, research_registry
from mmbu_phase1.fields import (
    array,
    boolean,
    closed,
    digest,
    fail,
    literal,
    one_of,
    require,
    string_set,
    text,
    timestamp,
)


PROFILE_KEYS = tuple(sorted((*v1.PROFILE_KEYS, "matched_objective_family_id")))
ARCHITECTURE_RANK = {name: index for index, name in enumerate(v1.ARCHITECTURES)}


def manifest_digest(record: dict[str, Any]) -> str:
    """Return the canonical v2 digest, omitting only its own digest field."""
    return v1.manifest_digest(record)


def _validate_profile(value: Any, path: str) -> dict[str, str]:
    closed(value, path, PROFILE_KEYS)
    profile_id = text(value["profile_id"], f"{path}.profile_id")
    family_id = text(value["matched_objective_family_id"], f"{path}.matched_objective_family_id")
    task = rational.from_wire(value["task_unit_share"], f"{path}.task_unit_share")
    context = rational.from_wire(value["context_unit_share"], f"{path}.context_unit_share")
    unit = rational.from_wire(value["unit_total_mass"], f"{path}.unit_total_mass")
    tolerance = rational.from_wire(value["exposure_audit_tolerance"], f"{path}.exposure_audit_tolerance")
    require(task >= 0 and context >= 0 and task + context == 1, path,
            "task/context shares must be nonnegative and sum exactly to one")
    if context > 0:
        require(task > 0, path, "dual profiles require positive task and context shares")
    require(unit > 0, f"{path}.unit_total_mass", "must be positive")
    require(0 <= tolerance <= Fraction(1, 100), f"{path}.exposure_audit_tolerance",
            "must be at most 1/100")
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
    return {"family_id": family_id, "mode": "task" if context == 0 else "dual", "profile_id": profile_id}


def _validate_training(value: Any) -> dict[str, dict[str, str]]:
    closed(value, "manifest.training_contract", v1.TRAINING_KEYS)
    literal(value["optimizer_name"], "manifest.training_contract.optimizer_name", "AdamW")
    literal(value["public_firewall_assertion"], "manifest.training_contract.public_firewall_assertion", True)
    literal(value["preservation_policy"], "manifest.training_contract.preservation_policy", "no_kl_primary")
    one_of(value["rationale_policy"], "manifest.training_contract.rationale_policy",
           ("answer_only_training", "source_supported_rationale"))
    if value["rationale_policy"] == "source_supported_rationale":
        fail("manifest.training_contract.rationale_policy",
             "source receipts are absent from the Package F schema fixture")
    string_set(value["seed_ids"], "manifest.training_contract.seed_ids")
    closed(value["optional_ablations"], "manifest.training_contract.optional_ablations", ("A1", "A2"))
    literal(value["optional_ablations"]["A1"], "manifest.training_contract.optional_ablations.A1", False)
    literal(value["optional_ablations"]["A2"], "manifest.training_contract.optional_ablations.A2", False)

    geometry = closed(value["geometry"], "manifest.training_contract.geometry",
                      ("box_format", "coordinate_frame", "inverse_transform_receipt", "origin", "repair_policy",
                       "source_edges"))
    literal(geometry["box_format"], "manifest.training_contract.geometry.box_format", "xywh")
    literal(geometry["coordinate_frame"], "manifest.training_contract.geometry.coordinate_frame", "original_pixel")
    literal(geometry["origin"], "manifest.training_contract.geometry.origin", "zero_based")
    literal(geometry["source_edges"], "manifest.training_contract.geometry.source_edges", "half_open")
    literal(geometry["repair_policy"], "manifest.training_contract.geometry.repair_policy", "reject")
    v1._unknown(geometry["inverse_transform_receipt"],
                "manifest.training_contract.geometry.inverse_transform_receipt")

    serializer = closed(value["serializer"], "manifest.training_contract.serializer",
                        ("inference_output_format_id", "malformed_json_policy", "terminal_json_required",
                         "training_target_format_id"))
    literal(serializer["terminal_json_required"], "manifest.training_contract.serializer.terminal_json_required", True)
    literal(serializer["malformed_json_policy"], "manifest.training_contract.serializer.malformed_json_policy",
            "incorrect_no_repair")
    text(serializer["training_target_format_id"], "manifest.training_contract.serializer.training_target_format_id")
    text(serializer["inference_output_format_id"], "manifest.training_contract.serializer.inference_output_format_id")

    profiles = array(value["objective_profiles"], "manifest.training_contract.objective_profiles", nonempty=True)
    metadata = [_validate_profile(item, f"manifest.training_contract.objective_profiles[{index}]")
                for index, item in enumerate(profiles)]
    profile_ids = [item["profile_id"] for item in metadata]
    require(profile_ids == sorted(set(profile_ids), key=lambda item: item.encode("utf-8")),
            "manifest.training_contract.objective_profiles", "profile IDs must be unique and UTF-8 sorted")
    family_modes = [(item["family_id"], item["mode"]) for item in metadata]
    require(len(family_modes) == len(set(family_modes)), "manifest.training_contract.objective_profiles",
            "each objective family may contain at most one profile per mode")
    available = set(family_modes)
    for item in metadata:
        if item["mode"] == "dual":
            require((item["family_id"], "task") in available,
                    "manifest.training_contract.objective_profiles",
                    "every dual profile requires a task-only profile in the same family")
    return {item["profile_id"]: item for item in metadata}


def _candidate_sort_key(candidate: dict[str, Any], profiles: dict[str, dict[str, str]]) -> tuple[int, int, bytes]:
    architecture = candidate["architecture_id"]
    if architecture == "recipe_arch::B0":
        return (0, 0, b"")
    profile_id = candidate["objective_profile_id"]
    mode = profiles[profile_id]["mode"]
    return (ARCHITECTURE_RANK[architecture], 0 if mode == "task" else 1, profile_id.encode("utf-8"))


def expected_comparator_map(record: dict[str, Any]) -> dict[str, list[str]]:
    """Derive the exact enabled-candidate comparator closure."""
    profiles = _validate_training(record["training_contract"])
    candidates = array(record["candidate_universe"], "manifest.candidate_universe", nonempty=True)
    for index, item in enumerate(candidates):
        v1._validate_candidate(item, f"manifest.candidate_universe[{index}]", set(profiles))
    enabled = [item for item in candidates if item["enabled"]]
    base_rows = [item for item in enabled if item["architecture_id"] == "recipe_arch::B0"]
    require(len(base_rows) == 1, "manifest.candidate_universe", "must contain exactly one enabled B0 candidate")
    base_id = base_rows[0]["candidate_id"]
    by_pair = {(item["architecture_id"], item["objective_profile_id"]): item for item in enabled}
    task_profile_by_family = {
        item["family_id"]: profile_id
        for profile_id, item in profiles.items()
        if item["mode"] == "task"
    }
    result: dict[str, list[str]] = {}
    for item in enabled:
        architecture = item["architecture_id"]
        if architecture == "recipe_arch::B0":
            continue
        profile_id = item["objective_profile_id"]
        metadata = profiles[profile_id]
        comparators = {base_id}
        if metadata["mode"] == "dual":
            task_profile_id = task_profile_by_family[metadata["family_id"]]
            task_control = by_pair.get((architecture, task_profile_id))
            require(task_control is not None, "manifest.candidate_universe",
                    f"dual candidate {item['candidate_id']!r} requires an enabled same-family task control")
            comparators.add(task_control["candidate_id"])
        architecture_index = ARCHITECTURE_RANK[architecture]
        if architecture_index > ARCHITECTURE_RANK["recipe_arch::B1-L"]:
            simpler_architecture = v1.ARCHITECTURES[architecture_index - 1]
            simpler = by_pair.get((simpler_architecture, profile_id))
            require(simpler is not None, "manifest.candidate_universe",
                    f"candidate {item['candidate_id']!r} requires an enabled immediate architecture control")
            comparators.add(simpler["candidate_id"])
        result[item["candidate_id"]] = sorted(comparators, key=lambda candidate_id: candidate_id.encode("utf-8"))
    return {candidate_id: result[candidate_id]
            for candidate_id in sorted(result, key=lambda item: item.encode("utf-8"))}


def validate_manifest(value: Any) -> dict:
    """Validate one closed version-2 design manifest without authorizing execution."""
    closed(value, "manifest", v1.TOP_KEYS)
    literal(value["schema_id"], "manifest.schema_id", "mmbu.competition.manifest")
    literal(value["schema_version"], "manifest.schema_version", 2)
    text(value["manifest_version"], "manifest.manifest_version")
    text(value["manifest_id"], "manifest.manifest_id")
    timestamp(value["created_at_utc"], "manifest.created_at_utc")
    one_of(value["evidence_class"], "manifest.evidence_class",
           ("design_only", "synthetic_only", "native_preflight", "biomedical_experiment"))
    state = one_of(value["state"], "manifest.state", v1.STATES)
    digest(value["artifact_registry_digest"], "manifest.artifact_registry_digest")
    literal(value["protocol_equivalence"], "manifest.protocol_equivalence", "synthetic")
    literal(value["public_firewall_policy_id"], "manifest.public_firewall_policy_id",
            "no_mmbu_public_or_derivatives_v1")
    for key in ("authority_snapshot_id", "protocol_contract_id"):
        text(value[key], f"manifest.{key}")
    for key in ("scientific_decision_receipt_id", "base_selection_receipt_id", "selected_base_digest"):
        v1._unknown(value[key], f"manifest.{key}")

    v1._validate_model_pin(value["model_pin"])
    v1._validate_data_plan(value["data_plan"])
    profiles = _validate_training(value["training_contract"])
    candidates = array(value["candidate_universe"], "manifest.candidate_universe", nonempty=True)
    for index, item in enumerate(candidates):
        v1._validate_candidate(item, f"manifest.candidate_universe[{index}]", set(profiles))
    base_rows = [item for item in candidates if item["architecture_id"] == "recipe_arch::B0"]
    require(len(base_rows) == 1, "manifest.candidate_universe", "must contain exactly one B0 candidate")
    pairs = [(item["architecture_id"], item["objective_profile_id"]) for item in candidates]
    require(len(pairs) == len(set(pairs)), "manifest.candidate_universe",
            "architecture/objective-profile pairs must be unique")
    candidate_ids = [item["candidate_id"] for item in candidates]
    require(len(candidate_ids) == len(set(candidate_ids)), "manifest.candidate_universe",
            "candidate IDs must be unique")
    expected_order = sorted(candidates, key=lambda item: _candidate_sort_key(item, profiles))
    require(candidate_ids == [item["candidate_id"] for item in expected_order], "manifest.candidate_universe",
            "candidate rows must use canonical architecture/profile order")

    v1._validate_evaluation(value["evaluation_contract"], set(candidate_ids))
    expected_comparators = expected_comparator_map(value)
    require(value["evaluation_contract"]["candidate_comparator_map"] == expected_comparators,
            "manifest.evaluation_contract.candidate_comparator_map",
            "must equal the mechanically derived enabled-candidate comparator closure")
    v1._validate_promotion(value["promotion_contract"])
    research_registry.validate_registry(
        value["research_comparison_registry"],
        {"execution_candidate_ids": [], "lane1_candidate_ids": candidate_ids, "public_ancestry": []},
    )
    v1._validate_release(value["release_contract"])
    string_set(value["unknowns"], "manifest.unknowns")
    require(value["canonical_digest"] == manifest_digest(value), "manifest.canonical_digest",
            "does not equal the canonical manifest digest")
    if state in {"experiment_freeze_ready", "frozen", "execution_failed", "executed", "confirmation_opened",
                 "promoted", "no_eligible_candidate"}:
        require(not value["unknowns"] and not v1._contains_unknown(
            {key: item for key, item in value.items() if key != "canonical_digest"}
        ), "manifest.state", "freeze or later state cannot contain unknown scientific or authority values")
    return value
