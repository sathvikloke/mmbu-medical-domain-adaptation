"""Package F synthetic manifest and disabled-registry conformance tests."""

from copy import deepcopy
from fractions import Fraction
import unittest

try:
    from mmbu_phase1 import competition_manifest, research_registry, track2_score
except ImportError:
    competition_manifest = research_registry = track2_score = None
from mmbu_phase1 import canonical, rational
from mmbu_phase1.fields import ContractViolation


D = "a" * 64
E = "b" * 64
F = "c" * 64
G = "d" * 64
H = "e" * 64


def profile(profile_id, task=(1, 1), context=(0, 1)):
    return {
        "context_balance_policy_id": "unknown",
        "context_field_normalization": "equal_available_fields",
        "context_protocol_status": "design_only",
        "context_target_contract_id": "unknown",
        "context_unit_share": {"denominator": context[1], "numerator": context[0]},
        "exposure_audit_tolerance": {"denominator": 100, "numerator": 1},
        "organizer_confirmed_applicability_mask_rule": True,
        "profile_id": profile_id,
        "requested_field_registry_digest": D,
        "schedule_id": "static",
        "source_balance_policy_id": "unknown",
        "task_balance_policy_id": "unknown",
        "task_target_contract_id": "unknown",
        "task_unit_share": {"denominator": task[1], "numerator": task[0]},
        "task_view_normalization": "equal_within_unit",
        "token_normalization_id": "unknown",
        "unit_total_mass": {"denominator": 1, "numerator": 1},
        "zero_applicable_evaluation_policy": "exclude_and_report",
        "zero_applicable_training_policy": "reallocate_context_share_to_task",
    }


def candidate(architecture, profile_id, enabled=True):
    return {
        "active_flop_formula": "unknown",
        "adapter_type": "none" if architecture == "recipe_arch::B0" else "lora",
        "alpha": "unknown",
        "architecture_id": architecture,
        "artifact_layout_id": "unknown",
        "base_revision": "unknown",
        "candidate_id": architecture + ("::base" if profile_id is None else "::" + profile_id),
        "dropout": "unknown",
        "enabled": enabled,
        "enablement_rule": "always" if architecture != "recipe_arch::B2-F" else "pre_output_f0_gate",
        "expected_trainable_parameters": "unknown",
        "objective_profile_id": profile_id,
        "optimizer_condition_id": "unknown",
        "rank": "unknown",
        "target_modules": [],
        "trainable_parameter_formula": "unknown",
    }


def valid_manifest(state="draft"):
    value = {
        "artifact_registry_digest": D,
        "authority_snapshot_id": "authority::synthetic",
        "base_selection_receipt_id": "unknown",
        "candidate_universe": [
            candidate("recipe_arch::B0", None),
            candidate("recipe_arch::B1-L", "profile::task_only"),
            candidate("recipe_arch::B2-P", "profile::dual"),
            candidate("recipe_arch::B2-F", "profile::dual", False),
        ],
        "canonical_digest": "",
        "created_at_utc": "2026-10-22T00:00:00Z",
        "data_plan": {
            "admitted_source_ids": [], "context_availability_mask_schema_id": "unknown",
            "context_field_schema_id": "unknown", "duplicate_policy_id": "synthetic_no_duplicates",
            "frontier_decision_role_ids": [], "frontier_train_role_ids": [], "frontier_tuning_role_ids": [],
            "held_out_source_ids": [], "human_review_receipt": "unknown", "independent_unit_key": "unknown",
            "independent_unit_loss_policy_id": "equal_unit_mass_v1", "prompt_lineage_groups": [],
            "recipe_confirmation_role_ids": [], "recipe_development_role_ids": [], "recipe_train_role_ids": [],
            "rights_receipts": [], "role_disjointness_matrix_digest": "unknown", "source_ledger_digest": "unknown",
            "split_group_keys": [], "task_view_manifest_digest": "unknown",
            "visual_probe_audit_role_ids": [], "visual_probe_construction_role_ids": [],
        },
        "evaluation_contract": {
            "bootstrap_seed_ids": ["seed::synthetic"], "candidate_comparator_map": {
                "recipe_arch::B1-L::profile::task_only": ["recipe_arch::B0::base"],
                "recipe_arch::B2-F::profile::dual": ["recipe_arch::B0::base", "recipe_arch::B2-P::profile::dual"],
                "recipe_arch::B2-P::profile::dual": ["recipe_arch::B0::base"],
            }, "context_status": "design_only", "metric_ids": ["context", "score_proxy", "task"],
            "one_confirmation_opening": True, "paired_group_bootstrap": True,
        },
        "evidence_class": "synthetic_only",
        "manifest_id": "manifest::package-f-synthetic",
        "manifest_version": "1",
        "model_pin": {
            "attention_backend": "unknown", "dependency_lock_digest": "unknown", "dtype": "unknown",
            "generation_settings_digest": "unknown", "image_transform_receipt": "unknown",
            "license": "unknown", "local_cache_digest": "unknown", "model_identifier": "unknown",
            "model_revision": "unknown", "module_map_digest": "unknown", "processor_identifier": "unknown",
            "processor_revision": "unknown", "quantization": "unknown", "source_receipt": "unknown",
            "thinking_mode": "unknown", "token_limits_digest": "unknown", "trust_remote_code": "forbidden",
        },
        "promotion_contract": {
            "decision_function_id": "decision::synthetic", "one_named_candidate_only": True,
            "required_gate_ids": ["answer_changing_target_tracking", "answer_preserving_visual_invariance", "cost",
                                  "invalid_output_rate", "negative_flips", "normal_image", "packaging",
                                  "positive_flips", "preservation_nonregression", "resource"],
            "runner_up_rescue": False,
        },
        "protocol_contract_id": "protocol::synthetic",
        "protocol_equivalence": "synthetic",
        "public_firewall_policy_id": "no_mmbu_public_or_derivatives_v1",
        "release_contract": {
            "allowed_loader_id": "unknown", "artifact_inventory_digest": "unknown",
            "human_approval_receipt": "unknown", "network_denied_reload_required": True,
            "rollback_identity": "unknown", "upload_verification_receipt": "unknown",
        },
        "research_comparison_registry": {"entries": [], "schema_id": "mmbu.competition.research_comparison_registry",
                                         "schema_version": 1},
        "schema_id": "mmbu.competition.manifest",
        "schema_version": 1,
        "scientific_decision_receipt_id": "unknown",
        "selected_base_digest": "unknown",
        "state": state,
        "training_contract": {
            "early_stop_rule_id": "unknown", "geometry": {
                "box_format": "xywh", "coordinate_frame": "original_pixel", "inverse_transform_receipt": "unknown",
                "origin": "zero_based", "repair_policy": "reject", "source_edges": "half_open",
            }, "maximum_updates": "unknown", "objective_profiles": [
                profile("profile::dual", (3, 4), (1, 4)), profile("profile::task_only")
            ], "optimizer_name": "AdamW", "optional_ablations": {"A1": False, "A2": False},
            "preservation_policy": "no_kl_primary", "public_firewall_assertion": True,
            "rationale_policy": "answer_only_training", "seed_ids": [], "serializer": {
                "inference_output_format_id": "unknown", "malformed_json_policy": "incorrect_no_repair",
                "terminal_json_required": True, "training_target_format_id": "unknown",
            },
        },
        "unknowns": ["base", "data", "decision_literals", "model", "release"],
    }
    value["canonical_digest"] = canonical.value_digest({k: v for k, v in value.items() if k != "canonical_digest"})
    return value


REQUIRED_GATES = ["answer_changing_target_tracking", "answer_preserving_visual_invariance", "cost",
                  "invalid_output_rate", "negative_flips", "normal_image", "packaging", "positive_flips",
                  "preservation_nonregression", "resource"]
H1_GATES = ["answer_changing_target_tracking", "answer_preserving_visual_invariance", "cost",
            "invalid_output_rate", "negative_flips", "normal_image", "positive_flips",
            "preservation_nonregression"]


def arm(arm_id, context, normalized):
    return {
        "answer_target_contract_id": "answer::same", "arm_id": arm_id, "base_digest": D,
        "candidate_digest": {"SYS-A0": D, "SYS-A1": E, "SYS-A2": F, "SYS-A3": G}[arm_id],
        "checkpoint_policy_id": "checkpoint::same", "checkpoint_slot_id": "slot::" + arm_id,
        "context_training": context, "normalization_policy": "equal_independent_unit" if normalized else "row_uniform",
        "evaluation_prompt_contract_id": "evaluation::same",
        "objective_profile_id": "objective::context" if context else "objective::answer",
        "optimizer_id": "optimizer::same", "seed_set_id": "seeds::same", "serializer_id": "serializer::same",
        "unit_set_id": "units::same",
    }


def exposure(arm_id, context, normalized):
    return {
        "active_flops": 100, "answer_tokens": 75 if context else 100, "arm_id": arm_id,
        "budget_estimand": "fixed_total_supervised_tokens", "compute_units": 100,
        "context_tokens": 25 if context else 0, "displaced_repeated_answer_schedule_id": "repeat::25",
        "global_objective_loss_mass": {"denominator": 1, "numerator": 100},
        "optimizer_updates": 10,
        "per_unit_allocation": ({"unit::one": rational.to_wire(Fraction(1, 2)),
                                  "unit::two": rational.to_wire(Fraction(1, 2))} if normalized else
                                 {"unit::one": rational.to_wire(Fraction(3, 4)),
                                  "unit::two": rational.to_wire(Fraction(1, 4))}),
        "unit_allocation_policy": "equal_independent_unit" if normalized else "row_uniform",
    }


def valid_h1_bundle():
    contracts = {name: arm(name, name in ("SYS-A1", "SYS-A3"), name in ("SYS-A2", "SYS-A3"))
                 for name in ("SYS-A0", "SYS-A1", "SYS-A2", "SYS-A3")}
    exposures = {name: exposure(name, name in ("SYS-A1", "SYS-A3"), name in ("SYS-A2", "SYS-A3"))
                 for name in contracts}
    entry = {
        "answer_target_contract_id": "answer::same", "arm_contract_ids": {name: name for name in contracts},
        "arm_exposure_contract_ids": {name: name for name in exposures}, "base_digest": D,
        "budget_estimand": "fixed_total_supervised_tokens", "claim_id": "system::H1_context_x_unit_mass",
        "common_gate_contract_ids": {name: "gate::" + name for name in H1_GATES},
        "compute_match_contract_id": "match::compute", "confirmation_opening_receipt_id": "unknown",
        "confirmation_opening_rule_id": "unknown", "confirmation_role_ids": ["confirm::p1", "confirm::p2"],
        "context_target_contract_ids": {"SYS-A1": "context::same", "SYS-A3": "context::same"},
        "cross_lane_role_disjointness_digest": E, "decision_function_id": "decision::h1",
        "development_role_ids": ["development::one"], "duplication_perturbation_contract_id": "dup::no_new_unit",
        "enabled": False, "equalized_exposure_contract_id": "equalize::within_context",
        "independent_unit_id": "unit::synthetic", "kill_function_id": "kill::h1",
        "minimum_effect_ids": {"context": "margin::context", "task": "margin::task"},
        "multiplicity_rule_id": "multiplicity::simultaneous", "natural_exposure_contract_id": "natural::frozen",
        "optimizer_update_match_contract_id": "match::updates",
        "primary_estimand_ids": {"context": "estimand::context", "task": "estimand::task"},
        "replication_parent_rows": [
            {"confirmation_role_ids": ["confirm::p1"], "context_interaction_estimand_id": "ctx::p1",
             "governance_authority_id": "authority::p1", "interaction_decision_receipt_id": F,
             "source_parent_id": "parent::p1", "task_interaction_estimand_id": "task::p1"},
            {"confirmation_role_ids": ["confirm::p2"], "context_interaction_estimand_id": "ctx::p2",
             "governance_authority_id": "authority::p2", "interaction_decision_receipt_id": G,
             "source_parent_id": "parent::p2", "task_interaction_estimand_id": "task::p2"},
        ],
        "replication_plan_id": "replication::two_parents", "resampling_hierarchy_id": "resample::parents",
        "role_disjointness_matrix_digest": H, "scientific_decision_receipt_id": "unknown",
        "source_parent_ids": ["parent::p1", "parent::p2"], "source_parent_role_map_id": "roles::parents",
        "status": "design_only_disabled", "supervised_token_match_contract_id": "match::tokens",
        "train_role_ids": ["train::one"],
    }
    registry = {"entries": [entry], "schema_id": "mmbu.competition.research_comparison_registry", "schema_version": 1}
    refs = {
        "arm_contracts": contracts, "arm_exposures": exposures,
        "duplication_contracts": {"dup::no_new_unit": {"adds_independent_unit": False, "adds_semantic_target": False,
                                                        "matched_exposure": True}},
        "equalization_contracts": {"equalize::within_context": {"pairs": [["SYS-A0", "SYS-A2"],
                                                                             ["SYS-A1", "SYS-A3"]],
                                                              "prediction": "pairwise_equivalence_null",
                                                              "quantities": ["active_flops", "compute_units",
                                                                             "objective_fields", "optimizer_updates",
                                                                             "sampling_probability", "supervised_tokens",
                                                                             "views"]}},
        "execution_candidate_ids": [], "lane1_candidate_ids": [], "public_ancestry": [],
        "role_memberships": {
            role: {"duplicate_group_ids": ["dup::" + suffix], "independent_unit_ids": ["unit::" + suffix],
                   "prompt_lineage_ids": ["prompt::" + suffix],
                   "source_parent_ids": (["parent::p1"] if suffix == "c1" else
                                         ["parent::p2"] if suffix == "c2" else ["source::" + suffix])}
            for role, suffix in (("confirm::p1", "c1"), ("confirm::p2", "c2"),
                                 ("development::one", "d"), ("train::one", "t"))
        },
    }
    return registry, refs


class PackageModuleTests(unittest.TestCase):
    def test_package_f_modules_exist(self):
        self.assertIsNotNone(competition_manifest)
        self.assertIsNotNone(research_registry)
        self.assertIsNotNone(track2_score)


@unittest.skipIf(competition_manifest is None, "Package F modules not implemented")
class ManifestTests(unittest.TestCase):
    def test_closed_draft_and_digest_validate(self):
        value = valid_manifest()
        self.assertEqual(competition_manifest.validate_manifest(value)["state"], "draft")
        bad = {**value, "hidden_default": True}
        with self.assertRaises(ContractViolation):
            competition_manifest.validate_manifest(bad)
        bad = deepcopy(value); bad["canonical_digest"] = E
        with self.assertRaises(ContractViolation):
            competition_manifest.validate_manifest(bad)

    def test_state_machine_is_forward_only(self):
        for old, new in (("draft", "native_preflight_ready"), ("native_preflight_ready", "experiment_freeze_ready"),
                         ("experiment_freeze_ready", "frozen"), ("frozen", "executed"),
                         ("executed", "confirmation_opened"), ("confirmation_opened", "promoted")):
            competition_manifest.validate_transition(old, new)
        for old, new in (("frozen", "draft"), ("draft", "frozen"), ("promoted", "executed")):
            with self.subTest(old=old, new=new), self.assertRaises(ContractViolation):
                competition_manifest.validate_transition(old, new)

    def test_candidate_universe_and_profiles_are_closed(self):
        for mutate in ("missing", "duplicate", "unqualified", "profile_sum"):
            value = valid_manifest()
            if mutate == "missing": value["candidate_universe"].pop()
            elif mutate == "duplicate": value["candidate_universe"][3] = deepcopy(value["candidate_universe"][2])
            elif mutate == "unqualified": value["candidate_universe"][1]["architecture_id"] = "B1-L"
            else: value["training_contract"]["objective_profiles"][0]["context_unit_share"] = rational.to_wire(Fraction(1, 2))
            value["canonical_digest"] = competition_manifest.manifest_digest(value)
            with self.subTest(mutate=mutate), self.assertRaises(ContractViolation):
                competition_manifest.validate_manifest(value)

    def test_public_geometry_serializer_and_rationale_fail_closed(self):
        for path, replacement in (("public_firewall_policy_id", "allow_public"),
                                  ("coordinate_frame", "normalized"), ("repair_policy", "clip"),
                                  ("malformed_json_policy", "repair"), ("rationale_policy", "label_template")):
            value = valid_manifest()
            target = value
            if path in ("coordinate_frame", "repair_policy"): target = value["training_contract"]["geometry"]
            elif path == "malformed_json_policy": target = value["training_contract"]["serializer"]
            elif path == "rationale_policy": target = value["training_contract"]
            target[path] = replacement
            value["canonical_digest"] = competition_manifest.manifest_digest(value)
            with self.subTest(path=path), self.assertRaises(ContractViolation):
                competition_manifest.validate_manifest(value)

    def test_unknowns_block_freeze_and_optional_branches_stay_disabled(self):
        value = valid_manifest("frozen")
        with self.assertRaises(ContractViolation): competition_manifest.validate_manifest(value)
        value = valid_manifest(); value["training_contract"]["optional_ablations"]["A1"] = True
        value["canonical_digest"] = competition_manifest.manifest_digest(value)
        with self.assertRaises(ContractViolation): competition_manifest.validate_manifest(value)
        value = valid_manifest(); value["candidate_universe"][3]["enabled"] = True
        value["canonical_digest"] = competition_manifest.manifest_digest(value)
        with self.assertRaises(ContractViolation): competition_manifest.validate_manifest(value)


@unittest.skipIf(track2_score is None, "Package F score module not implemented")
class ScoreAndPromotionTests(unittest.TestCase):
    def test_exact_score_proxy_uses_hand_derived_rational(self):
        self.assertEqual(track2_score.score_proxy(Fraction(3, 4), Fraction(1, 2), Fraction(1, 2)), Fraction(7, 40))
        with self.assertRaises(ContractViolation): track2_score.score_proxy(Fraction(5, 4), Fraction(1, 2), Fraction(1, 2))

    def test_promotion_is_named_conjunctive_and_has_no_runner_up(self):
        contract = {"candidate_order": ["cand-a", "cand-b"], "context_bounds": [rational.to_wire(0), rational.to_wire(1)],
                    "positive_task_gain_floor": rational.to_wire(0), "practical_margin": rational.to_wire(0),
                    "promotion_candidate_id": "cand-a", "required_gate_ids": REQUIRED_GATES}
        def result(name, task, context):
            return {"base_task": rational.to_wire(Fraction(1, 2)), "candidate_id": name,
                    "context": rational.to_wire(context), "gates": {gate: True for gate in REQUIRED_GATES},
                    "task": rational.to_wire(task)}
        results = {"base": result("base", Fraction(1, 2), Fraction(1, 2)),
                   "cand-a": result("cand-a", Fraction(3, 4), Fraction(1, 2)),
                   "cand-b": result("cand-b", Fraction(4, 5), Fraction(1, 2))}
        self.assertEqual(competition_manifest.evaluate_promotion(contract, results, "base", ["base"]), "cand-a")
        results["cand-a"]["gates"]["normal_image"] = False
        self.assertEqual(competition_manifest.evaluate_promotion(contract, results, "base", ["base"]),
                         "no_eligible_candidate")
        results["cand-a"]["gates"]["normal_image"] = True
        results["cand-a"]["candidate_id"] = "cand-b"
        with self.assertRaises(ContractViolation):
            competition_manifest.evaluate_promotion(contract, results, "base", ["base"])


@unittest.skipIf(research_registry is None, "Package F registry module not implemented")
class ResearchRegistryTests(unittest.TestCase):
    def test_empty_and_complete_h1_registry_validate(self):
        empty = {"entries": [], "schema_id": "mmbu.competition.research_comparison_registry", "schema_version": 1}
        research_registry.validate_registry(empty, {"execution_candidate_ids": [], "lane1_candidate_ids": [],
                                                    "public_ancestry": []})
        registry, refs = valid_h1_bundle()
        self.assertEqual(research_registry.validate_registry(registry, refs)["entries"][0]["enabled"], False)

    def test_status_enablement_arms_and_context_assignment_reject(self):
        for mutate in ("status", "enabled", "missing_arm", "fifth_arm", "context_on_a0", "missing_context_binding",
                       "wrong_objective", "wrong_normalization", "wrong_base", "wrong_serializer", "wrong_optimizer",
                       "wrong_seed", "duplicate_checkpoint"):
            registry, refs = valid_h1_bundle(); entry = registry["entries"][0]
            if mutate == "status": entry["status"] = "ready"
            elif mutate == "enabled": entry["enabled"] = True
            elif mutate == "missing_arm": del entry["arm_contract_ids"]["SYS-A3"]
            elif mutate == "fifth_arm": entry["arm_contract_ids"]["SYS-A4"] = "SYS-A4"
            elif mutate == "context_on_a0": refs["arm_contracts"]["SYS-A0"]["context_training"] = True
            elif mutate == "missing_context_binding": del entry["context_target_contract_ids"]["SYS-A3"]
            elif mutate == "wrong_objective": refs["arm_contracts"]["SYS-A3"]["objective_profile_id"] = "objective::answer"
            elif mutate == "wrong_normalization": refs["arm_contracts"]["SYS-A3"]["normalization_policy"] = "row_uniform"
            elif mutate == "wrong_base": refs["arm_contracts"]["SYS-A3"]["base_digest"] = H
            elif mutate == "wrong_serializer": refs["arm_contracts"]["SYS-A3"]["serializer_id"] = "serializer::drift"
            elif mutate == "wrong_optimizer": refs["arm_contracts"]["SYS-A3"]["optimizer_id"] = "optimizer::drift"
            elif mutate == "wrong_seed": refs["arm_contracts"]["SYS-A3"]["seed_set_id"] = "seeds::drift"
            else: refs["arm_contracts"]["SYS-A3"]["checkpoint_slot_id"] = "slot::SYS-A2"
            with self.subTest(mutate=mutate), self.assertRaises(ContractViolation):
                research_registry.validate_registry(registry, refs)

    def test_budget_estimands_totals_and_per_unit_policy_reject(self):
        for mutate in ("estimand", "tokens", "loss", "updates", "flops", "compute", "policy", "allocation",
                       "displaced"):
            registry, refs = valid_h1_bundle(); ex = refs["arm_exposures"]["SYS-A3"]
            if mutate == "estimand": ex["budget_estimand"] = "free_context"
            elif mutate == "tokens": ex["answer_tokens"] += 1
            elif mutate == "loss": ex["global_objective_loss_mass"] = rational.to_wire(101)
            elif mutate == "updates": ex["optimizer_updates"] += 1
            elif mutate == "flops": ex["active_flops"] += 1
            elif mutate == "compute": ex["compute_units"] += 1
            elif mutate == "policy": ex["unit_allocation_policy"] = "row_uniform"
            elif mutate == "allocation": ex["per_unit_allocation"]["unit::one"] = rational.to_wire(Fraction(3, 4))
            else: ex["displaced_repeated_answer_schedule_id"] = ""
            with self.subTest(mutate=mutate), self.assertRaises(ContractViolation):
                research_registry.validate_registry(registry, refs)

    def test_separate_estimands_all_gates_and_mechanism_contracts_reject(self):
        for mutate in ("same_estimand", "missing_effect", "missing_gate", "cross_context_equalization",
                       "missing_quantity", "continued_advantage", "dup_adds_unit", "dup_adds_target", "dup_unmatched"):
            registry, refs = valid_h1_bundle(); entry = registry["entries"][0]
            if mutate == "same_estimand": entry["primary_estimand_ids"]["context"] = entry["primary_estimand_ids"]["task"]
            elif mutate == "missing_effect": del entry["minimum_effect_ids"]["context"]
            elif mutate == "missing_gate": del entry["common_gate_contract_ids"]["negative_flips"]
            elif mutate == "cross_context_equalization": refs["equalization_contracts"]["equalize::within_context"]["pairs"] = [["SYS-A0", "SYS-A3"], ["SYS-A1", "SYS-A2"]]
            elif mutate == "missing_quantity": refs["equalization_contracts"]["equalize::within_context"]["quantities"].pop()
            elif mutate == "continued_advantage": refs["equalization_contracts"]["equalize::within_context"]["prediction"] = "continued_h1_advantage"
            elif mutate == "dup_adds_unit": refs["duplication_contracts"]["dup::no_new_unit"]["adds_independent_unit"] = True
            elif mutate == "dup_adds_target": refs["duplication_contracts"]["dup::no_new_unit"]["adds_semantic_target"] = True
            else: refs["duplication_contracts"]["dup::no_new_unit"]["matched_exposure"] = False
            with self.subTest(mutate=mutate), self.assertRaises(ContractViolation):
                research_registry.validate_registry(registry, refs)

    def test_roles_replication_public_ancestry_and_execution_bridge_reject(self):
        for mutate in ("unit_overlap", "duplicate_overlap", "source_overlap", "prompt_overlap", "one_parent",
                       "same_governance", "parent_reused_for_training", "public", "execution", "lane1"):
            registry, refs = valid_h1_bundle(); entry = registry["entries"][0]
            if mutate.endswith("overlap"):
                dimension = {"unit_overlap": "independent_unit_ids", "duplicate_overlap": "duplicate_group_ids",
                             "source_overlap": "source_parent_ids", "prompt_overlap": "prompt_lineage_ids"}[mutate]
                refs["role_memberships"]["confirm::p1"][dimension] = refs["role_memberships"]["train::one"][dimension]
            elif mutate == "one_parent": entry["replication_parent_rows"].pop()
            elif mutate == "same_governance": entry["replication_parent_rows"][1]["governance_authority_id"] = "authority::p1"
            elif mutate == "parent_reused_for_training": refs["role_memberships"]["train::one"]["source_parent_ids"] = ["parent::p1"]
            elif mutate == "public": refs["public_ancestry"] = ["mmbu_official"]
            elif mutate == "execution": refs["execution_candidate_ids"] = ["SYS-A3"]
            else: refs["lane1_candidate_ids"] = ["SYS-A0"]
            with self.subTest(mutate=mutate), self.assertRaises(ContractViolation):
                research_registry.validate_registry(registry, refs)


if __name__ == "__main__":
    unittest.main()
