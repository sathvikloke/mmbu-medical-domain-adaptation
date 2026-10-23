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


if __name__ == "__main__":
    unittest.main()
