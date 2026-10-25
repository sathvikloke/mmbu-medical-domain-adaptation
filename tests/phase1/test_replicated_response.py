"""Closed tests for the replicated external-biomedical response screen."""

from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "config/phase1/replicated-response-screen-2026-10-25.json"


class ReplicatedResponseManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = importlib.util.find_spec("mmbu_phase1.replicated_response")
        cls.module = importlib.import_module("mmbu_phase1.replicated_response") if cls.spec else None

    def setUp(self):
        if self.module is None and self._testMethodName != "test_module_and_manifest_exist":
            self.skipTest("replicated_response module is not implemented")
        if self.module is not None:
            self.value = self.module.load_manifest(MANIFEST)

    def test_module_and_manifest_exist(self):
        self.assertIsNotNone(self.spec, "replicated_response module must exist")
        self.assertTrue(MANIFEST.is_file(), "replicated response manifest must exist")

    def test_expands_exact_fourteen_conditions(self):
        conditions = self.module.conditions(self.value)
        self.assertEqual(len(conditions), 14)
        self.assertEqual(
            [(row["candidate_id"], row["profile"], row["training_seed"]) for row in conditions],
            [
                ("rr-qwen35-9b", "base", None),
                ("rr-qwen35-9b", "task_only", 20261025),
                ("rr-qwen35-9b", "task_only", 20261026),
                ("rr-qwen35-9b", "task_only", 20261027),
                ("rr-qwen35-9b", "dual", 20261025),
                ("rr-qwen35-9b", "dual", 20261026),
                ("rr-qwen35-9b", "dual", 20261027),
                ("rr-qwen35-4b", "base", None),
                ("rr-qwen35-4b", "task_only", 20261025),
                ("rr-qwen35-4b", "task_only", 20261026),
                ("rr-qwen35-4b", "task_only", 20261027),
                ("rr-qwen35-4b", "dual", 20261025),
                ("rr-qwen35-4b", "dual", 20261026),
                ("rr-qwen35-4b", "dual", 20261027),
            ],
        )
        self.assertEqual(self.module.condition_by_index(self.value, 13), conditions[13])
        with self.assertRaises(ContractViolation):
            self.module.condition_by_index(self.value, 14)

    def test_identity_population_and_budget_are_frozen(self):
        self.assertEqual(self.value["selection"], {
            "allow_confirmation": False,
            "development_units_per_source": 128,
            "selection_seed": 1729,
            "training_units_per_source": 512,
        })
        self.assertEqual(self.value["training"]["seeds"], [20261025, 20261026, 20261027])
        self.assertEqual(self.value["training"]["profiles"], ["task_only", "dual"])
        self.assertEqual(self.value["resources"], {
            "attempts_per_condition": 1,
            "automatic_rescue_allowed": False,
            "gpu_model": "NVIDIA A100 80GB PCIe",
            "gpu_seconds_per_condition": 14400,
            "gpus_per_condition": 1,
            "max_concurrent_conditions": 5,
        })
        self.assertEqual(
            [(row["model_id"], row["revision"], row["expected_parameter_count"])
             for row in self.value["candidates"]],
            [
                ("Qwen/Qwen3.5-9B", "c202236235762e1c871ad0ccb60c8ee5ba337b9a", 9409813744),
                ("Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", 4539265536),
            ],
        )

    def test_scope_widening_and_unknown_fields_reject(self):
        mutations = (
            lambda value: value.__setitem__("surprise", True),
            lambda value: value["authorization"].__setitem__("mmbu_public_content_allowed", True),
            lambda value: value["selection"].__setitem__("allow_confirmation", True),
            lambda value: value["selection"].__setitem__("training_units_per_source", 513),
            lambda value: value["selection"].__setitem__("development_units_per_source", 129),
            lambda value: value["resources"].__setitem__("attempts_per_condition", 2),
            lambda value: value["resources"].__setitem__("automatic_rescue_allowed", True),
            lambda value: value["training"].__setitem__("seeds", [20261025, 20261026]),
            lambda value: value["training"].__setitem__("profiles", ["dual"]),
            lambda value: value["candidates"][0].__setitem__("revision", "a" * 40),
        )
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(self.value)
            mutate(changed)
            with self.subTest(index=index), self.assertRaises(ContractViolation):
                self.module.validate_manifest(changed)

    def test_official_context_projection_is_source_specific_and_closed(self):
        busbra = self.module.official_context_row({
            "context_prompt": "old",
            "context_target": {"birads": "4"},
            "context_target_text": "old",
            "row_id": "bus_0001-l",
            "source_id": "busbra",
        })
        self.assertEqual(busbra["requested_context_fields"],
                         ["body_part", "medical_domain", "modality"])
        self.assertEqual(busbra["context_target"], {
            "body_part": "breast", "medical_domain": "radiology", "modality": "ultrasound",
        })
        self.assertEqual(busbra["context_target_text"],
                         canonical.dumps(busbra["context_target"]).decode("utf-8"))
        self.assertIn("exactly these keys: body_part, medical_domain, modality", busbra["context_prompt"])

        path = self.module.official_context_row({
            "context_prompt": None,
            "context_target": None,
            "context_target_text": None,
            "row_id": "pathmnist::train::0",
            "source_id": "pathmnist",
        })
        self.assertEqual(path["requested_context_fields"],
                         ["medical_domain", "modality", "specimen", "stain"])
        self.assertEqual(path["context_target"], {
            "medical_domain": "pathology",
            "modality": "histopathology",
            "specimen": "colorectal tissue",
            "stain": "hematoxylin and eosin",
        })
        with self.assertRaises(ContractViolation):
            self.module.official_context_row({"row_id": "x", "source_id": "unknown"})


if __name__ == "__main__":
    unittest.main()
