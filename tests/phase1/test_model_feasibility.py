"""Closed bounded model-feasibility screen tests."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from mmbu_phase1 import model_feasibility
from mmbu_phase1.fields import ContractViolation


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "config/phase1/model-feasibility-screen-2026-10-25.json"


def _load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

    def test_qwen35_counts_match_native_post_tie_models(self):
        counts = {
            row["candidate_id"]: row["expected_parameter_count"]
            for row in self.value["candidates"]
        }
        self.assertEqual(counts["f0-qwen35-9b"], 9409813744)
        self.assertEqual(counts["f0-qwen35-4b"], 4539265536)

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


class NativeF0EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = _load_tool("model_feasibility_f0_for_test", REPO / "tools/model_feasibility_f0.py")

    def test_one_shot_output_root_must_not_exist(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "new"
            self.runner.require_new_output_root(output)
            output.mkdir()
            with self.assertRaises(ContractViolation):
                self.runner.require_new_output_root(output)

    def test_offline_environment_is_required(self):
        valid = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
        self.assertEqual(self.runner.validate_offline_environment(valid), valid)
        for key in valid:
            changed = dict(valid)
            changed[key] = "0"
            with self.subTest(key=key), self.assertRaises(ContractViolation):
                self.runner.validate_offline_environment(changed)

    def test_fresh_reload_command_is_explicit_and_offline(self):
        command = self.runner.reload_command(
            "/python", "/reload.py", "/manifest.json", 2, "/snapshot", "/adapter", "/reload-result.json"
        )
        self.assertEqual(command, [
            "/python", "/reload.py", "--manifest", "/manifest.json", "--candidate-index", "2",
            "--snapshot", "/snapshot", "--adapter", "/adapter", "--output", "/reload-result.json",
        ])

    def test_frozen_target_text_is_not_normalized(self):
        class Mask:
            def sum(self):
                return self

            def item(self):
                return 1

        class Processor:
            def __call__(self, **_kwargs):
                return {"attention_mask": Mask()}

        conversations = []

        def render(_processor, _family, conversation, *, generation):
            conversations.append((conversation, generation))
            return "rendered"

        with mock.patch.object(self.runner, "render_chat", side_effect=render):
            self.runner.encode(Processor(), "qwen3_5", object(), "prompt", " blue")
        self.assertEqual(conversations[1][0][1]["content"][0]["text"], " blue")

    def test_tensor_digest_supports_bfloat16(self):
        try:
            import torch
        except ImportError:
            self.skipTest("torch unavailable")
        value = torch.tensor([1.0, 2.0], dtype=torch.bfloat16)
        digest = self.runner.tensor_digest([("adapter", value)])
        self.assertEqual(len(digest), 64)

    def test_failure_receipt_retains_stage_and_never_claims_later_gates(self):
        candidate = model_feasibility.candidate_by_index(model_feasibility.load_manifest(MANIFEST), 0)
        receipt = self.runner.failure_receipt(
            candidate, "backward", "RuntimeError: synthetic failure", "2026-10-25T01:00:00Z",
            "2026-10-25T01:00:03Z", "/snapshot", "abc123",
        )
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["terminal_stage"], "backward")
        self.assertEqual(receipt["optimizer_updates"], 0)
        self.assertIsNone(receipt["reload_prediction_match"])
        self.assertFalse(receipt["mmbu_public_content_used"])
        self.assertFalse(receipt["biomedical_content_used"])

    def test_late_failure_receipt_retains_observed_update_and_adapter(self):
        candidate = model_feasibility.candidate_by_index(model_feasibility.load_manifest(MANIFEST), 1)
        receipt = self.runner.failure_receipt(
            candidate, "reload", "offline mismatch", "2026-10-25T01:00:00Z", "2026-10-25T01:00:03Z",
            "/snapshot", "abc123", optimizer_updates=1,
            adapter_inventory=[{"bytes": 3, "path": "adapter_model.safetensors", "sha256": "a" * 64}],
            snapshot_tree_sha256="b" * 64,
            resources={"elapsed_seconds": 3},
        )
        self.assertEqual(receipt["optimizer_updates"], 1)
        self.assertEqual(receipt["adapter_inventory"][0]["path"], "adapter_model.safetensors")
        self.assertEqual(receipt["snapshot_tree_sha256"], "b" * 64)
        self.assertEqual(receipt["resources"], {"elapsed_seconds": 3})

    def test_sbatch_enforces_one_hour_one_attempt_offline_array(self):
        text = (REPO / "tools/model_feasibility_f0.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --array=0-4%5", text)
        self.assertIn("#SBATCH --time=01:00:00", text)
        self.assertIn("#SBATCH --gres=gpu:tesla_a100_80gb:1", text)
        self.assertIn("module load python/3.12.12", text)
        self.assertIn("HF_HUB_OFFLINE=1", text)
        self.assertIn("TRANSFORMERS_OFFLINE=1", text)
        self.assertEqual(text.count("model_feasibility_f0.py"), 1)
        self.assertNotIn("sbatch ", text)

    def test_acquisition_job_is_cpu_only_and_revision_bound(self):
        text = (REPO / "tools/acquire_model_feasibility_snapshots.sbatch").read_text(encoding="utf-8")
        self.assertIn("#SBATCH --partition=epyc-cpu", text)
        self.assertIn("#SBATCH --array=0-4%5", text)
        self.assertNotIn("--gres=gpu", text)
        self.assertEqual(text.count("acquire_model_feasibility_snapshots.py"), 1)
        source = (REPO / "tools/acquire_model_feasibility_snapshots.py").read_text(encoding="utf-8")
        self.assertIn("revision=candidate[\"revision\"]", source)
        self.assertIn("f.literal(info.sha", source)
        self.assertNotIn("from_pretrained", source)


if __name__ == "__main__":
    unittest.main()
