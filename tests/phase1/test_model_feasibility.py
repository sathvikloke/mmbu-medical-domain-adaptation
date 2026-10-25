"""Closed bounded model-feasibility screen tests."""

from __future__ import annotations

import copy
from pathlib import Path
import unittest

from mmbu_phase1 import model_feasibility
from mmbu_phase1.fields import ContractViolation


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "config/phase1/model-feasibility-screen-2026-10-25.json"


class ModelFeasibilityManifestTests(unittest.TestCase):
    def setUp(self):
        self.value = model_feasibility.load_manifest(MANIFEST)

    def test_frozen_candidate_ids_and_revisions_are_exact(self):
        self.assertEqual(
            [(row["model_id"], row["revision"]) for row in self.value["candidates"]],
            [
                ("Qwen/Qwen3.5-9B", "c202236235762e1c871ad0ccb60c8ee5ba337b9a"),
                ("Qwen/Qwen3-VL-8B-Instruct", "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b"),
                ("Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a"),
                ("Qwen/Qwen3-VL-2B-Instruct", "89644892e4d85e24eaac8bacfd4f463576704203"),
                ("OpenGVLab/InternVL3_5-2B-HF", "3f301ffcf3dcbb47893afae6650ea3e78d96fb6d"),
            ],
        )
        self.assertEqual(model_feasibility.candidate_by_index(self.value, 0)["model_id"], "Qwen/Qwen3.5-9B")
        self.assertEqual(model_feasibility.candidate_by_index(self.value, 4)["loader_family"], "internvl3_5")
        with self.assertRaises(ContractViolation):
            model_feasibility.candidate_by_index(self.value, 5)

    def test_manifest_freezes_generated_input_and_matched_update(self):
        self.assertEqual(self.value["fixture"]["origin"], "synthetic_engineering")
        self.assertFalse(self.value["authorization"]["mmbu_public_content_allowed"])
        self.assertEqual(self.value["resources"]["gpu_seconds_per_candidate"], 3600)
        self.assertEqual(self.value["resources"]["attempts_per_candidate"], 1)
        self.assertFalse(self.value["resources"]["automatic_rescue_allowed"])
        self.assertEqual(self.value["lora"]["target_suffixes"], ["q_proj", "v_proj"])
        self.assertEqual(self.value["comparison_rules"]["decision_use"], "feasibility_only_no_ranking")

    def test_closed_manifest_rejects_unknown_key_and_floating_revision(self):
        for label, mutate in (
            ("unknown", lambda value: value.__setitem__("surprise", True)),
            ("floating", lambda value: value["candidates"][0].__setitem__("revision", "main")),
            ("short", lambda value: value["candidates"][0].__setitem__("revision", "a" * 39)),
        ):
            value = copy.deepcopy(self.value)
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                model_feasibility.validate_manifest(value)

    def test_rejects_duplicates_and_candidate_specific_scientific_settings(self):
        duplicate = copy.deepcopy(self.value)
        duplicate["candidates"][1]["model_id"] = duplicate["candidates"][0]["model_id"]
        with self.assertRaises(ContractViolation):
            model_feasibility.validate_manifest(duplicate)
        extra = copy.deepcopy(self.value)
        extra["candidates"][0]["learning_rate"] = 2e-4
        with self.assertRaises(ContractViolation):
            model_feasibility.validate_manifest(extra)

    def test_rejects_expanded_gpu_or_retry_budget(self):
        for key, value in (
            ("gpu_seconds_per_candidate", 3601),
            ("attempts_per_candidate", 2),
            ("automatic_rescue_allowed", True),
        ):
            changed = copy.deepcopy(self.value)
            changed["resources"][key] = value
            with self.subTest(key=key), self.assertRaises(ContractViolation):
                model_feasibility.validate_manifest(changed)

    def test_rejects_any_public_content_or_quality_ranking(self):
        public = copy.deepcopy(self.value)
        public["authorization"]["mmbu_public_content_allowed"] = True
        with self.assertRaises(ContractViolation):
            model_feasibility.validate_manifest(public)
        ranking = copy.deepcopy(self.value)
        ranking["comparison_rules"]["decision_use"] = "select_winner"
        with self.assertRaises(ContractViolation):
            model_feasibility.validate_manifest(ranking)


if __name__ == "__main__":
    unittest.main()
