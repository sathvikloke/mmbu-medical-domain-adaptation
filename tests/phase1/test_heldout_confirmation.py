"""Closed CPU-only tests for the BUSI-WHU held-out confirmation mechanics."""

from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import unittest

from mmbu_phase1.scope import REQUIRED_PHASE1_TEST_MODULES
from mmbu_phase1.fields import ContractViolation


REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "config/phase1/busi-whu-confirmation-spec-2026-10-25.json"


class HeldoutConfirmationRegistrationTests(unittest.TestCase):
    def test_module_spec_and_suite_registration_exist(self):
        self.assertIsNotNone(importlib.util.find_spec("mmbu_phase1.heldout_confirmation"))
        self.assertTrue(SPEC.is_file())
        self.assertIn("test_heldout_confirmation.py", REQUIRED_PHASE1_TEST_MODULES)


class HeldoutConfirmationSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")
        cls.value = cls.module.load_spec(SPEC)

    def test_exact_frozen_protocol(self):
        value = self.value
        self.assertEqual(value["candidate"], {
            "expected_parameter_count": 9409813744,
            "model_id": "Qwen/Qwen3.5-9B",
            "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
            "runtime_gate": "qwen3.5-9b-successor-native-runtime",
            "track": "track2",
        })
        self.assertEqual(value["training"]["seeds"], [20261025, 20261026, 20261027])
        self.assertEqual(value["training"]["optimizer_updates"], 1024)
        self.assertEqual(value["training"]["lora_dropout"], 0)
        self.assertEqual(value["source"]["minimum_independent_patients"], 60)
        self.assertEqual(value["statistics"]["bootstrap_draws"], 10000)
        self.assertEqual(value["statistics"]["lower_bound_index_zero_based"], 999)
        self.assertEqual(value["statistics"]["decision_margin"], {"denominator": 20, "numerator": 1})
        self.assertFalse(value["authorization"]["mmbu_public_content_allowed"])

    def test_scope_widening_and_protocol_drift_reject(self):
        mutations = (
            lambda value: value.__setitem__("unknown", True),
            lambda value: value["candidate"].__setitem__("model_id", "other/model"),
            lambda value: value["candidate"].__setitem__("revision", "a" * 40),
            lambda value: value["training"].__setitem__("lora_dropout", 0.05),
            lambda value: value["training"].__setitem__("seeds", [20261025]),
            lambda value: value["training"].__setitem__("optimizer_updates", 1025),
            lambda value: value["prompts"].__setitem__("parser", "repair-json"),
            lambda value: value["statistics"].__setitem__("decision_margin", {"denominator": 10, "numerator": 1}),
            lambda value: value["resources"].__setitem__("attempts_per_condition", 2),
            lambda value: value["resources"].__setitem__("automatic_rescue_allowed", True),
            lambda value: value["source"].__setitem__("source_id", "bus-uclm"),
            lambda value: value["authorization"].__setitem__("mmbu_public_content_allowed", True),
        )
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(self.value)
            mutate(changed)
            with self.subTest(index=index), self.assertRaises(ContractViolation):
                self.module.validate_spec(changed)


if __name__ == "__main__":
    unittest.main()
