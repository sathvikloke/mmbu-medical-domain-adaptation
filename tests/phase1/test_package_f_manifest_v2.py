"""Version-2 multi-profile competition-manifest conformance tests."""

from copy import deepcopy
import unittest

from mmbu_phase1 import canonical, competition_manifest, competition_manifest_v2
from mmbu_phase1.fields import ContractViolation
from test_package_f import candidate, valid_manifest


FAMILY = "objective_family::task_context_v1"
B0 = "recipe_arch::B0::base"
B1_TASK = "recipe_arch::B1-L::profile::task_only"
B1_DUAL = "recipe_arch::B1-L::profile::dual"
B2_TASK = "recipe_arch::B2-P::profile::task_only"
B2_DUAL = "recipe_arch::B2-P::profile::dual"


def reseal(value):
    value["canonical_digest"] = competition_manifest_v2.manifest_digest(value)
    return value


def valid_v2_manifest():
    value = valid_manifest()
    value["schema_version"] = 2
    value["manifest_version"] = "2"
    profiles = value["training_contract"]["objective_profiles"]
    for item in profiles:
        item["matched_objective_family_id"] = FAMILY
    value["candidate_universe"] = [
        candidate("recipe_arch::B0", None),
        candidate("recipe_arch::B1-L", "profile::task_only"),
        candidate("recipe_arch::B1-L", "profile::dual"),
        candidate("recipe_arch::B2-P", "profile::task_only"),
        candidate("recipe_arch::B2-P", "profile::dual"),
    ]
    value["evaluation_contract"]["candidate_comparator_map"] = {
        B1_DUAL: [B0, B1_TASK],
        B1_TASK: [B0],
        B2_DUAL: [B0, B1_DUAL, B2_TASK],
        B2_TASK: [B0, B1_TASK],
    }
    return reseal(value)


class ManifestV2UniverseTests(unittest.TestCase):
    def test_five_arm_manifest_is_valid_and_digest_bound(self):
        value = valid_v2_manifest()
        self.assertEqual(competition_manifest_v2.validate_manifest(value), value)
        self.assertNotEqual(value["canonical_digest"], valid_manifest()["canonical_digest"])
        value["manifest_id"] = "manifest::tampered"
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_schema_versions_are_mutually_exclusive(self):
        with self.assertRaises(ContractViolation):
            competition_manifest.validate_manifest(valid_v2_manifest())
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(valid_manifest())

    def test_exactly_one_base_is_required(self):
        for mutation in ("missing", "duplicate"):
            value = valid_v2_manifest()
            if mutation == "missing":
                value["candidate_universe"].pop(0)
            else:
                value["candidate_universe"].insert(1, deepcopy(value["candidate_universe"][0]))
            reseal(value)
            with self.subTest(mutation=mutation), self.assertRaises(ContractViolation):
                competition_manifest_v2.validate_manifest(value)

    def test_architecture_profile_pairs_are_unique(self):
        value = valid_v2_manifest()
        duplicate = deepcopy(value["candidate_universe"][1])
        duplicate["candidate_id"] = duplicate["candidate_id"] + "::alias"
        value["candidate_universe"].insert(2, duplicate)
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_candidate_order_is_canonical(self):
        value = valid_v2_manifest()
        value["candidate_universe"][1], value["candidate_universe"][2] = (
            value["candidate_universe"][2], value["candidate_universe"][1]
        )
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_dual_profile_requires_positive_task_and_context_shares(self):
        value = valid_v2_manifest()
        dual = next(item for item in value["training_contract"]["objective_profiles"]
                    if item["profile_id"] == "profile::dual")
        dual["task_unit_share"] = {"denominator": 1, "numerator": 0}
        dual["context_unit_share"] = {"denominator": 1, "numerator": 1}
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)


class ManifestV2ComparatorTests(unittest.TestCase):
    def test_five_arm_comparator_closure_is_exact(self):
        expected = {
            B1_DUAL: [B0, B1_TASK],
            B1_TASK: [B0],
            B2_DUAL: [B0, B1_DUAL, B2_TASK],
            B2_TASK: [B0, B1_TASK],
        }
        value = valid_v2_manifest()
        self.assertEqual(competition_manifest_v2.expected_comparator_map(value), expected)
        self.assertEqual(competition_manifest_v2.validate_manifest(value), value)

    def test_expected_comparator_map_rejects_malformed_candidate_as_contract_violation(self):
        value = valid_v2_manifest()
        del value["candidate_universe"][1]["enabled"]
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.expected_comparator_map(value)

    def test_dual_candidate_requires_same_architecture_task_control(self):
        value = valid_v2_manifest()
        value["candidate_universe"] = value["candidate_universe"][:1] + [value["candidate_universe"][2]]
        value["evaluation_contract"]["candidate_comparator_map"] = {B1_DUAL: [B0]}
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_dual_candidate_rejects_cross_family_task_control(self):
        value = valid_v2_manifest()
        task_profile = next(item for item in value["training_contract"]["objective_profiles"]
                            if item["profile_id"] == "profile::task_only")
        task_profile["matched_objective_family_id"] = "objective_family::different"
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_higher_task_candidate_requires_simpler_task_control(self):
        value = valid_v2_manifest()
        value["candidate_universe"] = [value["candidate_universe"][0], value["candidate_universe"][3]]
        value["evaluation_contract"]["candidate_comparator_map"] = {B2_TASK: [B0]}
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_higher_dual_candidate_requires_simpler_dual_control(self):
        value = valid_v2_manifest()
        value["candidate_universe"] = [
            value["candidate_universe"][0], value["candidate_universe"][1],
            value["candidate_universe"][3], value["candidate_universe"][4],
        ]
        value["evaluation_contract"]["candidate_comparator_map"].pop(B1_DUAL)
        value["evaluation_contract"]["candidate_comparator_map"][B2_DUAL] = [B0, B2_TASK]
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_comparator_map_rejects_missing_edges(self):
        value = valid_v2_manifest()
        value["evaluation_contract"]["candidate_comparator_map"][B2_DUAL] = [B0, B1_DUAL]
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_comparator_map_rejects_extra_edges(self):
        value = valid_v2_manifest()
        value["evaluation_contract"]["candidate_comparator_map"][B2_DUAL] = [
            B0, B1_DUAL, B1_TASK, B2_TASK,
        ]
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)

    def test_disabled_candidates_cannot_enter_comparator_map(self):
        disabled = candidate("recipe_arch::B2-F", "profile::task_only", False)
        disabled_id = disabled["candidate_id"]
        for placement in ("key", "value"):
            value = valid_v2_manifest()
            value["candidate_universe"].append(deepcopy(disabled))
            if placement == "key":
                value["evaluation_contract"]["candidate_comparator_map"][disabled_id] = [B0]
            else:
                value["evaluation_contract"]["candidate_comparator_map"][B2_DUAL] = sorted(
                    [B0, B1_DUAL, B2_TASK, disabled_id], key=lambda item: item.encode("utf-8")
                )
            reseal(value)
            with self.subTest(placement=placement), self.assertRaises(ContractViolation):
                competition_manifest_v2.validate_manifest(value)

    def test_hierarchy_rejects_missing_immediate_control(self):
        value = valid_v2_manifest()
        value["candidate_universe"] = [
            value["candidate_universe"][0], value["candidate_universe"][3], value["candidate_universe"][4],
        ]
        value["evaluation_contract"]["candidate_comparator_map"] = {
            B2_DUAL: [B0, B2_TASK], B2_TASK: [B0],
        }
        reseal(value)
        with self.assertRaises(ContractViolation):
            competition_manifest_v2.validate_manifest(value)


if __name__ == "__main__":
    unittest.main()
