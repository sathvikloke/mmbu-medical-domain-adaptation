"""Closed CPU-only tests for the BUSI-WHU held-out confirmation mechanics."""

from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import unittest

from mmbu_phase1 import rational
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


class HeldoutConfirmationLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def valid_lineage(self):
        return {
            "base_model_id": "Qwen/Qwen3.5-9B",
            "base_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
            "expected_parameter_count": 9409813744,
            "legacy_exploratory_adapter_used": False,
            "lora_alpha": 16,
            "lora_dropout": 0,
            "lora_rank": 8,
            "lora_target_suffixes": ["q_proj", "v_proj"],
            "mmbu_public_content_used": False,
            "optimizer_updates": 1024,
            "post_admission_retraining": True,
            "profile": "dual",
            "runtime_gate_id": "qwen3.5-9b-successor-native-runtime",
            "runtime_gate_passed": True,
            "source_purposes": {"busbra": "train", "pathmnist": "train"},
            "training_seed": 20261025,
        }

    def test_complete_post_admission_lineage_passes(self):
        self.assertEqual(self.module.validate_checkpoint_lineage(self.valid_lineage())["training_seed"], 20261025)

    def test_ineligible_or_incomplete_lineage_rejects(self):
        mutations = (
            lambda row: row.__setitem__("unknown", True),
            lambda row: row.__setitem__("legacy_exploratory_adapter_used", True),
            lambda row: row.__setitem__("post_admission_retraining", False),
            lambda row: row.__setitem__("runtime_gate_passed", False),
            lambda row: row.__setitem__("runtime_gate_id", "qwen2.5-vl-b1"),
            lambda row: row.__setitem__("source_purposes", {"busbra": "train"}),
            lambda row: row.__setitem__("source_purposes", {"busbra": "train", "pathmnist": "eval"}),
            lambda row: row.__setitem__("lora_dropout", 0.05),
            lambda row: row.__setitem__("optimizer_updates", 1023),
            lambda row: row.__setitem__("training_seed", 7),
            lambda row: row.__setitem__("mmbu_public_content_used", True),
        )
        for index, mutate in enumerate(mutations):
            changed = self.valid_lineage()
            mutate(changed)
            with self.subTest(index=index), self.assertRaises(ContractViolation):
                self.module.validate_checkpoint_lineage(changed)


class HeldoutConfirmationStatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def patients(self):
        return [f"patient-{index:03d}" for index in range(60)]

    def rows(self):
        rows = []
        for patient_id in self.patients():
            for condition in ("base", "seed-20261025", "seed-20261026", "seed-20261027"):
                adapted = condition != "base"
                rows.append({
                    "condition_id": condition,
                    "context_field_grades": {
                        "body_part": 1 if adapted else 0,
                        "medical_domain": 1 if adapted else 0,
                        "modality": 1 if adapted else 0,
                    },
                    "output_failed": False,
                    "patient_id": patient_id,
                    "record_id": patient_id + "::image-0",
                    "task_grade": rational.to_wire(1 if adapted else 0),
                    "target_label": "benign" if int(patient_id[-3:]) % 2 == 0 else "malignant",
                })
        return rows

    def artifacts(self):
        return self.module.build_randomization_artifacts(
            self.patients(), created_at="2026-10-25T12:00:00Z"
        )

    def test_exact_patient_analysis_uses_locked_matrices(self):
        result = self.module.analyze_patient_results(
            self.rows(), self.artifacts(), first_output_at="2026-10-25T12:00:01Z"
        )
        self.assertEqual(result["patient_count"], 60)
        self.assertEqual(result["point_delta"], rational.to_wire(1))
        self.assertEqual(result["lower_bound"], rational.to_wire(1))
        self.assertEqual(result["seed_deltas"], {
            "seed-20261025": rational.to_wire(1),
            "seed-20261026": rational.to_wire(1),
            "seed-20261027": rational.to_wire(1),
        })
        self.assertEqual(result["base"]["task"], rational.to_wire(0))
        self.assertEqual(result["seed_mean"]["context"], rational.to_wire(1))

    def test_population_and_chronology_drift_reject(self):
        with self.assertRaises(ContractViolation):
            self.module.build_randomization_artifacts(self.patients()[:-1], created_at="2026-10-25T12:00:00Z")
        with self.assertRaises(ContractViolation):
            self.module.build_randomization_artifacts(list(reversed(self.patients())), created_at="2026-10-25T12:00:00Z")
        with self.assertRaises(ContractViolation):
            self.module.analyze_patient_results(
                self.rows(), self.artifacts(), first_output_at="2026-10-25T11:59:59Z"
            )

    def test_missing_duplicate_and_matrix_drift_reject(self):
        rows = self.rows()
        for changed in (rows[:-1], rows + [copy.deepcopy(rows[0])]):
            with self.assertRaises(ContractViolation):
                self.module.analyze_patient_results(
                    changed, self.artifacts(), first_output_at="2026-10-25T12:00:01Z"
                )
        artifact = self.artifacts()
        artifact["index_matrix"][0][0] = 59
        with self.assertRaises(ContractViolation):
            self.module.analyze_patient_results(
                rows, artifact, first_output_at="2026-10-25T12:00:01Z"
            )

    def test_failures_stay_as_exact_zero_and_floats_reject(self):
        rows = self.rows()
        rows[0]["output_failed"] = True
        rows[0]["task_grade"] = rational.to_wire(0)
        result = self.module.analyze_patient_results(
            rows, self.artifacts(), first_output_at="2026-10-25T12:00:01Z"
        )
        self.assertEqual(result["output_failure_count"], 1)

        rows = self.rows()
        rows[0]["task_grade"] = 0.0
        with self.assertRaises(ContractViolation):
            self.module.analyze_patient_results(
                rows, self.artifacts(), first_output_at="2026-10-25T12:00:01Z"
            )


class HeldoutConfirmationDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def analysis(self):
        return {
            "base": {"context": rational.to_wire(1), "q": rational.to_wire(1), "task": rational.to_wire(1)},
            "class_diagnostics": {},
            "lower_bound": rational.to_wire(rational.Fraction(1, 10)),
            "output_failure_count": 0,
            "patient_count": 60,
            "point_delta": rational.to_wire(rational.Fraction(1, 10)),
            "seed_deltas": {
                "seed-20261025": rational.to_wire(rational.Fraction(1, 10)),
                "seed-20261026": rational.to_wire(rational.Fraction(1, 10)),
                "seed-20261027": rational.to_wire(rational.Fraction(1, 10)),
            },
            "seed_mean": {"context": rational.to_wire(0), "q": rational.to_wire(0), "task": rational.to_wire(1)},
            "sign_randomization_p": rational.to_wire(1),
        }

    def execution(self):
        return {
            "adapted_attempts": {"seed-20261025": 1, "seed-20261026": 1, "seed-20261027": 1},
            "adapted_reload_match": {"seed-20261025": True, "seed-20261026": True, "seed-20261027": True},
            "base_attempts": 1,
            "base_reload_match": True,
            "identity_drift": False,
            "mmbu_public_content_used": False,
            "source_id": "busi-whu-v3",
            "source_role": "confirmation",
        }

    def test_primary_pass_ignores_bad_secondary_and_sign_diagnostic(self):
        result = self.module.confirmation_decision(self.analysis(), self.execution())
        self.assertEqual(result, {"reasons": [], "status": "confirmation_passed"})

    def test_exact_margin_nonpositive_seed_and_lower_bound_fail(self):
        changes = (
            ("point_delta", rational.to_wire(rational.Fraction(1, 20)), "point_delta_not_above_margin"),
            ("lower_bound", rational.to_wire(rational.Fraction(1, 20)), "lower_bound_not_above_margin"),
        )
        for key, value, reason in changes:
            analysis = self.analysis()
            analysis[key] = value
            result = self.module.confirmation_decision(analysis, self.execution())
            self.assertEqual(result["status"], "confirmation_failed")
            self.assertIn(reason, result["reasons"])
        analysis = self.analysis()
        analysis["seed_deltas"]["seed-20261026"] = rational.to_wire(0)
        result = self.module.confirmation_decision(analysis, self.execution())
        self.assertIn("nonpositive_seed_delta:seed-20261026", result["reasons"])

    def test_execution_failures_cannot_be_rescued(self):
        mutations = (
            (lambda row: row.__setitem__("base_attempts", 2), "base_attempt_count"),
            (lambda row: row.__setitem__("base_reload_match", False), "base_reload_mismatch"),
            (lambda row: row["adapted_attempts"].__setitem__("seed-20261027", 2), "adapted_attempt_count:seed-20261027"),
            (lambda row: row.__setitem__("identity_drift", True), "identity_drift"),
        )
        for mutate, reason in mutations:
            execution = self.execution()
            mutate(execution)
            result = self.module.confirmation_decision(self.analysis(), execution)
            self.assertEqual(result["status"], "confirmation_failed")
            self.assertIn(reason, result["reasons"])

    def test_underpowered_and_source_substitution_are_terminal(self):
        analysis = self.analysis()
        analysis["patient_count"] = 59
        self.assertEqual(
            self.module.confirmation_decision(analysis, self.execution())["status"], "underpowered"
        )
        execution = self.execution()
        execution["source_id"] = "bus-uclm"
        result = self.module.confirmation_decision(self.analysis(), execution)
        self.assertEqual(result, {"reasons": ["source_identity_or_role"], "status": "blocked"})


if __name__ == "__main__":
    unittest.main()
