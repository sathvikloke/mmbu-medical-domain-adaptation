"""Package F representation-only research registry and H1 validator."""

from __future__ import annotations

from typing import Any

from mmbu_phase1 import rational
from mmbu_phase1.fields import (
    ContractViolation, array, boolean, closed, digest, fail, literal, require,
    sorted_unique, string_set, text, utf8_key,
)


ARMS = ("SYS-A0", "SYS-A1", "SYS-A2", "SYS-A3")
RESEARCH_IDS = frozenset((*ARMS, "FRONTIER-U", "FRONTIER-R"))
H1_GATES = (
    "answer_changing_target_tracking", "answer_preserving_visual_invariance", "cost", "invalid_output_rate",
    "negative_flips", "normal_image", "positive_flips", "preservation_nonregression",
)
REGISTRY_KEYS = ("entries", "schema_id", "schema_version")
H1_KEYS = (
    "answer_target_contract_id", "arm_contract_ids", "arm_exposure_contract_ids", "base_digest", "budget_estimand",
    "claim_id", "common_gate_contract_ids", "compute_match_contract_id", "confirmation_opening_receipt_id",
    "confirmation_opening_rule_id", "confirmation_role_ids", "context_target_contract_ids",
    "cross_lane_role_disjointness_digest", "decision_function_id", "development_role_ids",
    "duplication_perturbation_contract_id", "enabled", "equalized_exposure_contract_id", "independent_unit_id",
    "kill_function_id", "minimum_effect_ids", "multiplicity_rule_id", "natural_exposure_contract_id",
    "optimizer_update_match_contract_id", "primary_estimand_ids", "replication_parent_rows", "replication_plan_id",
    "resampling_hierarchy_id", "role_disjointness_matrix_digest", "scientific_decision_receipt_id",
    "source_parent_ids", "source_parent_role_map_id", "status", "supervised_token_match_contract_id",
    "train_role_ids",
)
ARM_KEYS = (
    "answer_target_contract_id", "arm_id", "base_digest", "candidate_digest", "checkpoint_policy_id",
    "checkpoint_slot_id", "context_training", "evaluation_prompt_contract_id", "normalization_policy",
    "objective_profile_id", "optimizer_id", "seed_set_id", "serializer_id", "unit_set_id",
)
EXPOSURE_KEYS = (
    "active_flops", "answer_tokens", "arm_id", "budget_estimand", "compute_units", "context_tokens",
    "displaced_repeated_answer_schedule_id", "global_objective_loss_mass", "optimizer_updates",
    "per_unit_allocation", "unit_allocation_policy",
)
ROLE_MEMBERSHIP_KEYS = ("duplicate_group_ids", "independent_unit_ids", "prompt_lineage_ids", "source_parent_ids")
REPLICATION_KEYS = (
    "confirmation_role_ids", "context_interaction_estimand_id", "governance_authority_id",
    "interaction_decision_receipt_id", "source_parent_id", "task_interaction_estimand_id",
)
COMPOSITE_KEYS = (
    "claim_id", "complete_system_comparator_map_id", "decision_function_id", "eligibility_function_id", "enabled",
    "full_system_artifact_contract_id", "h1_claim_id", "h2_claim_id", "minimum_effect_id",
    "multiplicity_rule_id", "primary_superiority_estimand_id", "resampling_hierarchy_id",
    "scientific_decision_receipt_id", "status", "system_binding_contract_id",
)


def _disabled(entry: dict, path: str) -> None:
    literal(entry["status"], f"{path}.status", "design_only_disabled")
    literal(entry["enabled"], f"{path}.enabled", False)


def _exact_map(value: Any, path: str, keys: tuple[str, ...]) -> dict:
    closed(value, path, keys)
    for key in keys:
        text(value[key], f"{path}.{key}")
    return value


def _validate_arm_contracts(entry: dict, refs: dict, path: str) -> None:
    ids = _exact_map(entry["arm_contract_ids"], f"{path}.arm_contract_ids", ARMS)
    contracts = refs.get("arm_contracts")
    if type(contracts) is not dict: fail("references.arm_contracts", "must resolve every H1 arm")
    shared = {"base_digest": entry["base_digest"]}
    shared_values = {key: None for key in ("answer_target_contract_id", "checkpoint_policy_id",
                                            "evaluation_prompt_contract_id", "optimizer_id", "seed_set_id",
                                            "serializer_id", "unit_set_id")}
    checkpoint_slots = set()
    for arm_id in ARMS:
        ref_id = ids[arm_id]
        if ref_id not in contracts: fail(f"{path}.arm_contract_ids.{arm_id}", "unresolved arm contract")
        contract = contracts[ref_id]
        closed(contract, f"references.arm_contracts.{ref_id}", ARM_KEYS)
        literal(contract["arm_id"], f"references.arm_contracts.{ref_id}.arm_id", arm_id)
        literal(contract["base_digest"], f"references.arm_contracts.{ref_id}.base_digest", shared["base_digest"])
        digest(contract["candidate_digest"], f"references.arm_contracts.{ref_id}.candidate_digest")
        expected_context = arm_id in ("SYS-A1", "SYS-A3")
        expected_normalization = "equal_independent_unit" if arm_id in ("SYS-A2", "SYS-A3") else "row_uniform"
        literal(contract["context_training"], f"references.arm_contracts.{ref_id}.context_training", expected_context)
        literal(contract["normalization_policy"], f"references.arm_contracts.{ref_id}.normalization_policy",
                expected_normalization)
        literal(contract["objective_profile_id"], f"references.arm_contracts.{ref_id}.objective_profile_id",
                "objective::context" if expected_context else "objective::answer")
        for key in shared_values:
            value = text(contract[key], f"references.arm_contracts.{ref_id}.{key}")
            if shared_values[key] is None: shared_values[key] = value
            else: literal(value, f"references.arm_contracts.{ref_id}.{key}", shared_values[key])
        slot = text(contract["checkpoint_slot_id"], f"references.arm_contracts.{ref_id}.checkpoint_slot_id")
        require(slot not in checkpoint_slots, f"references.arm_contracts.{ref_id}.checkpoint_slot_id", "must be unique")
        checkpoint_slots.add(slot)
    literal(shared_values["answer_target_contract_id"], f"{path}.answer_target_contract_id",
            entry["answer_target_contract_id"])
    _exact_map(entry["context_target_contract_ids"], f"{path}.context_target_contract_ids", ("SYS-A1", "SYS-A3"))


def _validate_exposures(entry: dict, refs: dict, path: str) -> None:
    ids = _exact_map(entry["arm_exposure_contract_ids"], f"{path}.arm_exposure_contract_ids", ARMS)
    exposures = refs.get("arm_exposures")
    if type(exposures) is not dict: fail("references.arm_exposures", "must resolve every H1 arm")
    comparable = {}
    policy_allocations = {}
    displaced_schedule = None
    for arm_id in ARMS:
        ref_id = ids[arm_id]
        if ref_id not in exposures: fail(f"{path}.arm_exposure_contract_ids.{arm_id}", "unresolved exposure contract")
        item = exposures[ref_id]
        closed(item, f"references.arm_exposures.{ref_id}", EXPOSURE_KEYS)
        literal(item["arm_id"], f"references.arm_exposures.{ref_id}.arm_id", arm_id)
        literal(item["budget_estimand"], f"references.arm_exposures.{ref_id}.budget_estimand",
                "fixed_total_supervised_tokens")
        expected_context = arm_id in ("SYS-A1", "SYS-A3")
        expected_policy = "equal_independent_unit" if arm_id in ("SYS-A2", "SYS-A3") else "row_uniform"
        literal(item["unit_allocation_policy"], f"references.arm_exposures.{ref_id}.unit_allocation_policy",
                expected_policy)
        for key in ("answer_tokens", "context_tokens", "optimizer_updates", "active_flops", "compute_units"):
            value = item[key]
            if type(value) is not int or value < 0: fail(f"references.arm_exposures.{ref_id}.{key}", "must be nonnegative integer")
        if expected_context:
            require(item["context_tokens"] > 0, f"references.arm_exposures.{ref_id}.context_tokens", "must be positive")
            text(item["displaced_repeated_answer_schedule_id"],
                 f"references.arm_exposures.{ref_id}.displaced_repeated_answer_schedule_id")
        else:
            literal(item["context_tokens"], f"references.arm_exposures.{ref_id}.context_tokens", 0)
        total_tokens = item["answer_tokens"] + item["context_tokens"]
        allocation = item["per_unit_allocation"]
        if type(allocation) is not dict or not allocation:
            fail(f"references.arm_exposures.{ref_id}.per_unit_allocation", "must be a nonempty keyed vector")
        unit_ids = list(allocation)
        require(unit_ids == sorted(set(unit_ids), key=lambda value: value.encode("utf-8")),
                f"references.arm_exposures.{ref_id}.per_unit_allocation", "unit IDs must be unique and UTF-8 sorted")
        weights = [rational.from_wire(allocation[unit_id],
                                     f"references.arm_exposures.{ref_id}.per_unit_allocation.{unit_id}")
                   for unit_id in unit_ids]
        require(all(weight >= 0 for weight in weights) and sum(weights) == 1,
                f"references.arm_exposures.{ref_id}.per_unit_allocation",
                "weights must be nonnegative and sum exactly to one")
        if expected_policy == "equal_independent_unit":
            require(len(set(weights)) == 1, f"references.arm_exposures.{ref_id}.per_unit_allocation",
                    "independent-unit normalization requires equal unit mass")
        allocation_wire = tuple((unit_id, weights[index]) for index, unit_id in enumerate(unit_ids))
        if expected_policy in policy_allocations:
            require(allocation_wire == policy_allocations[expected_policy],
                    f"references.arm_exposures.{ref_id}.per_unit_allocation",
                    "arms with the same allocation policy must bind the same vector")
        else:
            policy_allocations[expected_policy] = allocation_wire
        schedule_id = text(item["displaced_repeated_answer_schedule_id"],
                           f"references.arm_exposures.{ref_id}.displaced_repeated_answer_schedule_id")
        if displaced_schedule is None: displaced_schedule = schedule_id
        else: literal(schedule_id, f"references.arm_exposures.{ref_id}.displaced_repeated_answer_schedule_id",
                      displaced_schedule)
        comparable[arm_id] = (total_tokens, rational.from_wire(item["global_objective_loss_mass"],
                                                               f"references.arm_exposures.{ref_id}.global_objective_loss_mass"),
                              item["optimizer_updates"], item["active_flops"], item["compute_units"])
    require(len(set(comparable.values())) == 1, f"{path}.arm_exposure_contract_ids",
            "all H1 arms must match total tokens, global loss mass, updates, active FLOPs, and compute")


def _validate_mechanism(entry: dict, refs: dict, path: str) -> None:
    equalization_id = text(entry["equalized_exposure_contract_id"], f"{path}.equalized_exposure_contract_id")
    contracts = refs.get("equalization_contracts")
    if type(contracts) is not dict or equalization_id not in contracts:
        fail(f"{path}.equalized_exposure_contract_id", "unresolved equalization contract")
    item = contracts[equalization_id]
    closed(item, f"references.equalization_contracts.{equalization_id}", ("pairs", "prediction", "quantities"))
    literal(item["pairs"], f"references.equalization_contracts.{equalization_id}.pairs",
            [["SYS-A0", "SYS-A2"], ["SYS-A1", "SYS-A3"]])
    literal(item["prediction"], f"references.equalization_contracts.{equalization_id}.prediction",
            "pairwise_equivalence_null")
    string_set(item["quantities"], f"references.equalization_contracts.{equalization_id}.quantities")
    require(set(item["quantities"]) == {"active_flops", "compute_units", "objective_fields", "optimizer_updates",
                                        "sampling_probability", "supervised_tokens", "views"},
            f"references.equalization_contracts.{equalization_id}.quantities", "must cover every optimizer exposure")
    duplication_id = text(entry["duplication_perturbation_contract_id"], f"{path}.duplication_perturbation_contract_id")
    duplicates = refs.get("duplication_contracts")
    if type(duplicates) is not dict or duplication_id not in duplicates:
        fail(f"{path}.duplication_perturbation_contract_id", "unresolved duplication contract")
    duplicate = duplicates[duplication_id]
    closed(duplicate, f"references.duplication_contracts.{duplication_id}",
           ("adds_independent_unit", "adds_semantic_target", "matched_exposure"))
    literal(duplicate["adds_independent_unit"], f"references.duplication_contracts.{duplication_id}.adds_independent_unit", False)
    literal(duplicate["adds_semantic_target"], f"references.duplication_contracts.{duplication_id}.adds_semantic_target", False)
    literal(duplicate["matched_exposure"], f"references.duplication_contracts.{duplication_id}.matched_exposure", True)


def _validate_roles_and_replication(entry: dict, refs: dict, path: str) -> None:
    role_keys = ("train_role_ids", "development_role_ids", "confirmation_role_ids")
    role_ids = []
    for key in role_keys:
        role_ids.extend(string_set(entry[key], f"{path}.{key}", nonempty=True))
    memberships = refs.get("role_memberships")
    if type(memberships) is not dict: fail("references.role_memberships", "must map every H1 role to unit IDs")
    seen = {dimension: set() for dimension in ROLE_MEMBERSHIP_KEYS}
    membership_by_role = {}
    for role_id in role_ids:
        if role_id not in memberships: fail(f"references.role_memberships.{role_id}", "missing role membership")
        membership = memberships[role_id]
        closed(membership, f"references.role_memberships.{role_id}", ROLE_MEMBERSHIP_KEYS)
        membership_by_role[role_id] = membership
        for dimension in ROLE_MEMBERSHIP_KEYS:
            values = set(string_set(membership[dimension],
                                    f"references.role_memberships.{role_id}.{dimension}", nonempty=True))
            require(not (seen[dimension] & values), f"references.role_memberships.{role_id}.{dimension}",
                    "H1 roles overlap")
            seen[dimension] |= values
    rows = array(entry["replication_parent_rows"], f"{path}.replication_parent_rows", nonempty=True)
    require(len(rows) >= 2, f"{path}.replication_parent_rows", "at least two confirmatory parents are required")
    parents, authorities = [], []
    for index, row in enumerate(rows):
        row_path = f"{path}.replication_parent_rows[{index}]"
        closed(row, row_path, REPLICATION_KEYS)
        parents.append(text(row["source_parent_id"], f"{row_path}.source_parent_id"))
        authorities.append(text(row["governance_authority_id"], f"{row_path}.governance_authority_id"))
        string_set(row["confirmation_role_ids"], f"{row_path}.confirmation_role_ids", nonempty=True)
        require(set(row["confirmation_role_ids"]) <= set(entry["confirmation_role_ids"]),
                f"{row_path}.confirmation_role_ids", "must use only frozen confirmation roles")
        for key in ("task_interaction_estimand_id", "context_interaction_estimand_id"):
            text(row[key], f"{row_path}.{key}")
        digest(row["interaction_decision_receipt_id"], f"{row_path}.interaction_decision_receipt_id")
    require(parents == sorted(set(parents), key=lambda item: item.encode("utf-8")),
            f"{path}.replication_parent_rows", "parents must be unique and sorted")
    require(len(authorities) == len(set(authorities)), f"{path}.replication_parent_rows",
            "confirmatory parents must have distinct governance authorities")
    require(entry["source_parent_ids"] == parents, f"{path}.source_parent_ids",
            "must exactly match the confirmatory source parents")
    confirm_parent_ids = set()
    for role_id in entry["confirmation_role_ids"]:
        confirm_parent_ids.update(membership_by_role[role_id]["source_parent_ids"])
    require(set(parents) <= confirm_parent_ids, f"{path}.replication_parent_rows",
            "every replication parent must be bound to a confirmation role")
    nonconfirmation_parents = set()
    for role_id in (*entry["train_role_ids"], *entry["development_role_ids"]):
        nonconfirmation_parents.update(membership_by_role[role_id]["source_parent_ids"])
    require(not (set(parents) & nonconfirmation_parents), f"{path}.replication_parent_rows",
            "replication parents cannot be reused for training or development")


def _validate_h1(entry: Any, refs: dict, path: str) -> None:
    closed(entry, path, H1_KEYS)
    _disabled(entry, path)
    literal(entry["claim_id"], f"{path}.claim_id", "system::H1_context_x_unit_mass")
    literal(entry["budget_estimand"], f"{path}.budget_estimand", "fixed_total_supervised_tokens")
    digest(entry["base_digest"], f"{path}.base_digest")
    _exact_map(entry["primary_estimand_ids"], f"{path}.primary_estimand_ids", ("context", "task"))
    _exact_map(entry["minimum_effect_ids"], f"{path}.minimum_effect_ids", ("context", "task"))
    require(entry["primary_estimand_ids"]["context"] != entry["primary_estimand_ids"]["task"],
            f"{path}.primary_estimand_ids", "task and context estimands must remain separate")
    _exact_map(entry["common_gate_contract_ids"], f"{path}.common_gate_contract_ids", H1_GATES)
    for key in ("role_disjointness_matrix_digest", "cross_lane_role_disjointness_digest"):
        digest(entry[key], f"{path}.{key}")
    for key in ("answer_target_contract_id", "source_parent_role_map_id", "confirmation_opening_rule_id",
                "natural_exposure_contract_id", "supervised_token_match_contract_id",
                "optimizer_update_match_contract_id", "compute_match_contract_id", "independent_unit_id",
                "resampling_hierarchy_id", "multiplicity_rule_id", "replication_plan_id", "decision_function_id",
                "kill_function_id"):
        text(entry[key], f"{path}.{key}")
    _validate_arm_contracts(entry, refs, path)
    _validate_exposures(entry, refs, path)
    _validate_mechanism(entry, refs, path)
    _validate_roles_and_replication(entry, refs, path)


def _validate_composite(entry: Any, path: str) -> None:
    closed(entry, path, COMPOSITE_KEYS)
    _disabled(entry, path)
    literal(entry["claim_id"], f"{path}.claim_id", "system::COMPOSITE_PROTOCOL")
    literal(entry["h1_claim_id"], f"{path}.h1_claim_id", "system::H1_context_x_unit_mass")
    literal(entry["h2_claim_id"], f"{path}.h2_claim_id", "system::H2_adaptation_response_selection")
    for key in set(COMPOSITE_KEYS) - {"claim_id", "h1_claim_id", "h2_claim_id", "status", "enabled"}:
        text(entry[key], f"{path}.{key}")


def validate_registry(value: Any, references: Any) -> dict:
    """Validate the v1 disabled envelope and every Package F-owned H1 object."""
    closed(value, "research_registry", REGISTRY_KEYS)
    literal(value["schema_id"], "research_registry.schema_id", "mmbu.competition.research_comparison_registry")
    literal(value["schema_version"], "research_registry.schema_version", 1)
    if type(references) is not dict: fail("references", "must be an object")
    public = references.get("public_ancestry", [])
    require(type(public) is list and not public, "references.public_ancestry",
            "public MMBU content, derivatives, outputs, or choices are forbidden")
    for key in ("execution_candidate_ids", "lane1_candidate_ids"):
        values = references.get(key, [])
        if type(values) is not list: fail(f"references.{key}", "must be an array")
        require(not (set(values) & RESEARCH_IDS), f"references.{key}",
                "research v1 arms cannot become executable or enter Lane 1")
    entries = array(value["entries"], "research_registry.entries")
    claim_ids = []
    for index, entry in enumerate(entries):
        if type(entry) is not dict: fail(f"research_registry.entries[{index}]", "must be an object")
        claim_id = entry.get("claim_id")
        text(claim_id, f"research_registry.entries[{index}].claim_id")
        claim_ids.append(claim_id)
        if claim_id == "system::H1_context_x_unit_mass":
            _validate_h1(entry, references, f"research_registry.entries[{index}]")
        elif claim_id == "system::H2_adaptation_response_selection":
            validator = references.get("h2_validator")
            if not callable(validator): fail(f"research_registry.entries[{index}]", "Package G H2 validator is required")
            validator(entry, references)
        elif claim_id == "system::COMPOSITE_PROTOCOL":
            _validate_composite(entry, f"research_registry.entries[{index}]")
        else:
            fail(f"research_registry.entries[{index}].claim_id", "unsupported claim type")
    require(claim_ids == sorted(set(claim_ids), key=utf8_key), "research_registry.entries",
            "claim IDs must be unique and UTF-8 sorted")
    require(len(entries) <= 3, "research_registry.entries", "at most H1, H2, and composite may appear")
    return value


__all__ = ["ContractViolation", "validate_registry"]
