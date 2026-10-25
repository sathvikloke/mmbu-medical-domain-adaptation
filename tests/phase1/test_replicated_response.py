"""Closed tests for the replicated external-biomedical response screen."""

from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "config/phase1/replicated-response-screen-2026-10-25.json"


def _load_tool(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


class ReplicatedResponseNativeEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = REPO / "tools/replicated_response_screen.py"
        cls.runner = _load_tool("replicated_response_screen_for_test", cls.path) if cls.path.is_file() else None
        cls.manifest = importlib.import_module("mmbu_phase1.replicated_response").load_manifest(MANIFEST)

    def setUp(self):
        if self.runner is None and self._testMethodName != "test_native_runner_exists":
            self.skipTest("replicated response native runner is not implemented")

    def test_native_runner_exists(self):
        self.assertTrue(self.path.is_file(), "native response runner must exist")

    def test_output_root_is_one_shot(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "new"
            self.runner.require_new_output_root(path)
            path.mkdir()
            with self.assertRaises(ContractViolation):
                self.runner.require_new_output_root(path)

    def test_population_selection_is_independent_of_training_seed(self):
        rows = []
        for source in ("busbra", "pathmnist"):
            for split, count in (("train", 520), ("development", 130)):
                for index in range(count):
                    rows.append({
                        "independent_unit_id": f"{source}::{split}::{index}",
                        "row_id": f"{source}::{split}::{index}",
                        "source_id": source,
                        "split": split,
                    })
        portfolio = {"rows": rows}
        left = self.runner.select_populations(portfolio, self.manifest,
                                              self.runner.response.condition_by_index(self.manifest, 1))
        right = self.runner.select_populations(portfolio, self.manifest,
                                               self.runner.response.condition_by_index(self.manifest, 3))
        self.assertEqual(left, right)
        self.assertEqual(len(left["train"]), 1024)
        self.assertEqual(len(left["development"]), 256)

    def test_generic_loader_and_exact_language_lora_scope(self):
        source = self.path.read_text(encoding="utf-8")
        self.assertIn("AutoModelForImageTextToText", source)
        self.assertNotIn("Qwen2_5_VLForConditionalGeneration", source)

        class Fake:
            def named_modules(self):
                return iter((
                    ("model.language_model.layers.0.self_attn.q_proj", object()),
                    ("model.language_model.layers.0.self_attn.v_proj", object()),
                    ("model.visual.q_proj", object()),
                    ("model.language_model.layers.0.mlp.down_proj", object()),
                ))

        self.assertEqual(self.runner.exact_lora_targets(Fake(), ["q_proj", "v_proj"]), [
            "model.language_model.layers.0.self_attn.q_proj",
            "model.language_model.layers.0.self_attn.v_proj",
        ])

    def test_expected_updates_are_zero_for_base_and_exact_for_adapted(self):
        base = self.runner.response.condition_by_index(self.manifest, 0)
        adapted = self.runner.response.condition_by_index(self.manifest, 1)
        self.assertEqual(self.runner.expected_optimizer_updates(self.manifest, base), 0)
        self.assertEqual(self.runner.expected_optimizer_updates(self.manifest, adapted), 1024)

    def test_failure_receipt_is_closed_and_never_claims_reload(self):
        condition = self.runner.response.condition_by_index(self.manifest, 1)
        candidate = self.runner.response.candidate_by_id(self.manifest, condition["candidate_id"])
        receipt = self.runner.failure_receipt(
            candidate, condition, "training", "RuntimeError: synthetic", "start", "end", "manifest", "portfolio",
        )
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["terminal_stage"], "training")
        self.assertEqual(receipt["optimizer_updates"], 0)
        self.assertIsNone(receipt["reload_prediction_match"])
        self.assertFalse(receipt["mmbu_public_content_used"])
        self.assertFalse(receipt["promotion_eligible"])

    def test_reload_command_is_explicit_and_offline_capable(self):
        command = self.runner.reload_command(
            "/python", "/reload.py", "/manifest.json", 2, "/portfolio.json", "/snapshots",
            "/sources", "/adapter", "/output.json",
        )
        self.assertEqual(command[:6], [
            "/python", "/reload.py", "--manifest", "/manifest.json", "--condition-index", "2",
        ])
        self.assertIn("--adapter", command)
        self.assertEqual(command[-1], "/output.json")


class ReplicatedResponseSchedulerEnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepare_path = REPO / "tools/prepare_replicated_response_portfolio.py"
        cls.prepare_sbatch = REPO / "tools/prepare_replicated_response_portfolio.sbatch"
        cls.screen_sbatch = REPO / "tools/replicated_response_screen.sbatch"

    def test_launch_files_exist(self):
        self.assertTrue(self.prepare_path.is_file())
        self.assertTrue(self.prepare_sbatch.is_file())
        self.assertTrue(self.screen_sbatch.is_file())

    def test_preparation_is_new_output_only(self):
        if not self.prepare_path.is_file():
            self.skipTest("portfolio preparation tool is not implemented")
        module = _load_tool("prepare_replicated_response_for_test", self.prepare_path)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / "portfolio.json"
            module.publish(output, b"first\n")
            self.assertEqual(output.read_bytes(), b"first\n")
            with self.assertRaises(FileExistsError):
                module.publish(output, b"second\n")

    def test_scheduler_is_exactly_bounded_and_offline(self):
        if not self.screen_sbatch.is_file():
            self.skipTest("response screen Slurm envelope is not implemented")
        source = self.screen_sbatch.read_text(encoding="utf-8")
        self.assertIn("#SBATCH --array=0-13%5", source)
        self.assertIn("#SBATCH --gres=gpu:tesla_a100_80gb:1", source)
        self.assertIn("#SBATCH --time=04:00:00", source)
        self.assertIn("export HF_HUB_OFFLINE=1", source)
        self.assertIn("export TRANSFORMERS_OFFLINE=1", source)
        self.assertIn('--condition-index "${SLURM_ARRAY_TASK_ID}"', source)
        self.assertNotIn("sbatch ", source)

    def test_source_and_snapshot_paths_are_explicit(self):
        if not self.screen_sbatch.is_file() or not self.prepare_sbatch.is_file():
            self.skipTest("response screen Slurm envelopes are not implemented")
        screen = self.screen_sbatch.read_text(encoding="utf-8")
        prepare = self.prepare_sbatch.read_text(encoding="utf-8")
        for name in ("MMBU_SOURCE_ROOT", "MMBU_RESPONSE_ROOT"):
            self.assertIn(name, screen)
            self.assertIn(name, prepare)
        self.assertIn("MMBU_SNAPSHOT_ROOT", screen)
        self.assertIn('BUSBRA.zip', prepare)
        self.assertIn('pathmnist_224.npz', prepare)

    def test_preparation_scheduler_is_cpu_only_and_does_not_download(self):
        if not self.prepare_sbatch.is_file():
            self.skipTest("portfolio preparation Slurm envelope is not implemented")
        source = self.prepare_sbatch.read_text(encoding="utf-8")
        self.assertIn("#SBATCH --partition=epyc-cpu", source)
        self.assertNotIn("--gres=gpu", source)
        self.assertNotIn("curl ", source)
        self.assertNotIn("wget ", source)
        self.assertNotIn("sbatch ", source)


if __name__ == "__main__":
    unittest.main()
