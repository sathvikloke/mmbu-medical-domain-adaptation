"""Competition Lane 1 CPU-only synthetic trainer conformance tests."""

from copy import deepcopy
import unittest

from mmbu_phase1 import canonical, lane1_trainer
from mmbu_phase1.fields import ContractViolation
from test_package_f_manifest_v2 import (
    B0,
    B1_DUAL,
    B1_TASK,
    B2_DUAL,
    B2_TASK,
    valid_v2_manifest,
)


ARM_IDS = (B0, B1_TASK, B1_DUAL, B2_TASK, B2_DUAL)


def q(numerator, denominator=1):
    return {"denominator": denominator, "numerator": numerator}


def row(row_id, unit_id, feature, task, context):
    return {
        "context_target": context,
        "feature": feature,
        "independent_unit_id": unit_id,
        "row_id": row_id,
        "task_target": task,
    }


def valid_fixture():
    return {
        "biomedical_content": False,
        "evaluation_rows": [
            row("eval-1", "eval-unit-1", q(-1), 0, 0),
            row("eval-2", "eval-unit-2", q(1), 1, 1),
            row("eval-3", "eval-unit-3", q(0), 1, None),
        ],
        "fixture_id": "lane1-fixture-v1",
        "mmbu_public_content": False,
        "origin_class": "synthetic_engineering",
        "schema_id": "mmbu.synthetic.lane1_fixture",
        "schema_version": 1,
        "train_rows": [
            row("train-1", "train-unit-1", q(-1), 0, 0),
            row("train-2", "train-unit-2", q(1), 1, 1),
        ],
    }


def valid_config(fixture=None):
    fixture = valid_fixture() if fixture is None else fixture
    return {
        "allowed_fixture_digest": canonical.value_digest(fixture),
        "checkpoint_after_updates": 1,
        "epochs": 1,
        "learning_rate": q(1, 4),
        "schema_id": "mmbu.synthetic.lane1_config",
        "schema_version": 1,
        "seed": 17,
        "trainable_names_by_architecture": {
            "recipe_arch::B0": [],
            "recipe_arch::B1-L": ["language_adapter"],
            "recipe_arch::B2-P": ["language_adapter", "projector_adapter"],
        },
    }


class FixtureContractTests(unittest.TestCase):
    def test_valid_fixture_and_config_are_closed(self):
        fixture = valid_fixture()
        self.assertEqual(lane1_trainer.validate_fixture(fixture), fixture)
        self.assertEqual(lane1_trainer.validate_config(valid_config(fixture), fixture), valid_config(fixture))

    def test_fixture_rejects_origin_flags_unknowns_and_bad_rationals(self):
        mutations = (
            ("origin", lambda value: value.__setitem__("origin_class", "biomedical")),
            ("biomedical", lambda value: value.__setitem__("biomedical_content", True)),
            ("public", lambda value: value.__setitem__("mmbu_public_content", True)),
            ("unknown", lambda value: value.__setitem__("surprise", False)),
            ("bad-rational", lambda value: value["train_rows"][0].__setitem__("feature", q(2, 2))),
            ("missing-train-context", lambda value: value["train_rows"][0].__setitem__("context_target", None)),
            ("zero-eval-context", lambda value: [item.__setitem__("context_target", None)
                                                   for item in value["evaluation_rows"]]),
        )
        for label, mutate in mutations:
            value = valid_fixture()
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                lane1_trainer.validate_fixture(value)

    def test_fixture_rejects_duplicate_or_overlapping_ids(self):
        for field in ("row_id", "independent_unit_id"):
            for placement in ("within-train", "across-splits"):
                value = valid_fixture()
                if placement == "within-train":
                    value["train_rows"][1][field] = value["train_rows"][0][field]
                else:
                    value["evaluation_rows"][0][field] = value["train_rows"][0][field]
                with self.subTest(field=field, placement=placement), self.assertRaises(ContractViolation):
                    lane1_trainer.validate_fixture(value)

    def test_config_rejects_digest_budget_and_scope_drift(self):
        fixture = valid_fixture()
        mutations = (
            ("digest", lambda value: value.__setitem__("allowed_fixture_digest", "0" * 64)),
            ("checkpoint-zero", lambda value: value.__setitem__("checkpoint_after_updates", 0)),
            ("checkpoint-final", lambda value: value.__setitem__("checkpoint_after_updates", 2)),
            ("base-trainable", lambda value: value["trainable_names_by_architecture"]
             ["recipe_arch::B0"].append("bad")),
            ("b1-empty", lambda value: value["trainable_names_by_architecture"]
             .__setitem__("recipe_arch::B1-L", [])),
            ("b2-not-superset", lambda value: value["trainable_names_by_architecture"]
             .__setitem__("recipe_arch::B2-P", ["other"])),
            ("scope-order", lambda value: value["trainable_names_by_architecture"]
             .__setitem__("recipe_arch::B2-P", ["projector_adapter", "language_adapter"])),
        )
        for label, mutate in mutations:
            value = valid_config(fixture)
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                lane1_trainer.validate_config(value, fixture)


class ArmContractTests(unittest.TestCase):
    def test_manifest_resolves_exact_five_arm_order_and_modes(self):
        arms = lane1_trainer.resolve_arms(valid_v2_manifest())
        self.assertEqual(tuple(arm["candidate_id"] for arm in arms), ARM_IDS)
        self.assertEqual(tuple(arm["objective_mode"] for arm in arms), ("base", "task", "dual", "task", "dual"))

    def test_missing_extra_disabled_or_reordered_arm_rejects(self):
        for label, mutate in (
            ("missing", lambda value: value["candidate_universe"].pop()),
            ("extra", lambda value: value["candidate_universe"].append(deepcopy(value["candidate_universe"][-1]))),
            ("disabled", lambda value: value["candidate_universe"][-1].__setitem__("enabled", False)),
            ("reordered", lambda value: value["candidate_universe"].__setitem__(
                slice(1, 3), list(reversed(value["candidate_universe"][1:3])))),
        ):
            value = valid_v2_manifest()
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                lane1_trainer.resolve_arms(value)


if __name__ == "__main__":
    unittest.main()
