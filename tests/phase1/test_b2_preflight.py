"""CPU-only contract tests for the synthetic B2-P projector preflight."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation

try:
    from mmbu_phase1 import b2_preflight
except ImportError:
    b2_preflight = None


NATIVE_PATH = Path(__file__).resolve().parents[2] / "tools/b2_native_preflight.py"
native_spec = importlib.util.spec_from_file_location("b2_native_preflight", NATIVE_PATH)
if NATIVE_PATH.exists() and native_spec and native_spec.loader:
    b2_native = importlib.util.module_from_spec(native_spec)
    native_spec.loader.exec_module(b2_native)
else:
    b2_native = None

RELOAD_PATH = Path(__file__).resolve().parents[2] / "tools/b2_offline_reload.py"
reload_spec = importlib.util.spec_from_file_location("b2_offline_reload", RELOAD_PATH)
if RELOAD_PATH.exists() and reload_spec and reload_spec.loader:
    b2_reload = importlib.util.module_from_spec(reload_spec)
    reload_spec.loader.exec_module(b2_reload)
else:
    b2_reload = None

FINALIZE_PATH = Path(__file__).resolve().parents[2] / "tools/b2_finalize.py"
finalize_spec = importlib.util.spec_from_file_location("b2_finalize", FINALIZE_PATH)
if FINALIZE_PATH.exists() and finalize_spec and finalize_spec.loader:
    b2_finalize = importlib.util.module_from_spec(finalize_spec)
    finalize_spec.loader.exec_module(b2_finalize)
else:
    b2_finalize = None


class B2PreflightTests(unittest.TestCase):
    def valid_config(self) -> dict:
        record = {
            "schema_id": "mmbu.phase1.b2_mocs_preflight",
            "schema_version": 1,
            "attempt": 2,
            "authorization": {
                "authorized_by": "Aditya Raut",
                "authorized_at_utc": "2026-10-23T18:00:00Z",
                "authorized_actions": [
                    "fresh_network_denied_reload",
                    "one_minimal_optimizer_step",
                    "one_single_gpu_synthetic_b2_projector_preflight",
                    "reuse_verified_pinned_b1_model_and_runtime",
                    "standard_peft_adapter_export",
                ],
                "prohibited_actions": [
                    "biomedical_data_acquisition_or_use",
                    "full_training",
                    "mmbu_public_or_private_evaluation",
                    "submission",
                    "upload_or_public_release",
                ],
            },
            "architecture": {
                "recipe_id": "B2-P",
                "projector_module": "model.visual.merger",
                "projector_parameters": [
                    "model.visual.merger.ln_q.weight",
                    "model.visual.merger.mlp.0.bias",
                    "model.visual.merger.mlp.0.weight",
                    "model.visual.merger.mlp.2.bias",
                    "model.visual.merger.mlp.2.weight",
                ],
                "language_target_regex": "^model\\.language_model\\.layers\\.\\d+\\.self_attn\\.(?:q_proj|v_proj)$",
                "learning_rate": 0.01,
                "lora_alpha": 4,
                "lora_dropout": 0,
                "lora_rank": 2,
                "modules_to_save": ["visual.merger"],
            },
            "execution": {
                "allowed_input_classes": ["synthetic_engineering"],
                "biomedical_inputs_allowed": False,
                "dtype": "bfloat16",
                "gradient_accumulation_steps": 1,
                "mmbu_inputs_allowed": False,
                "network_policy": "denied",
                "optimizer_steps": 1,
                "world_size": 1,
            },
            "model": {
                "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
                "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
            },
            "paths": {
                "b1_evidence_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run9/evidence",
                "evidence_root": "/storage/home/npl015/mmbu-b2-preflight/2026-10-23-run2/evidence",
                "model_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/model",
                "remote_root": "/storage/home/npl015/mmbu-b2-preflight/2026-10-23-run2",
                "venv_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/venv",
            },
            "runtime": {
                "accelerate": "1.15.0",
                "attention_implementation": "sdpa",
                "numpy": "2.5.4",
                "peft": "0.21.2",
                "pillow": "13.0.0",
                "python": "3.12.12",
                "safetensors": "0.8.0",
                "torch": "2.11.0+cu128",
                "torchvision": "0.26.0+cu128",
                "transformers": "5.19.0",
                "trust_remote_code": False,
            },
            "scheduler": {
                "account": "allusers",
                "cluster": "mocshpc",
                "cpus_per_task": 4,
                "gpu_count": 1,
                "gpu_type": "tesla_a100_80gb",
                "max_jobs": 1,
                "max_retries": 0,
                "memory_gib": 96,
                "partition": "epyc-gpu",
                "qos": "u-default",
                "wall_seconds": 7200,
            },
            "record_digest": "",
        }
        return canonical.seal(record)

    def test_config_is_closed_and_fails_on_scope_widening(self):
        self.assertIsNotNone(b2_preflight, "B2 validator is missing")
        base = self.valid_config()
        self.assertEqual(b2_preflight.validate_preflight_config(base), base)
        mutations = []
        extra_step = deepcopy(base); extra_step["execution"]["optimizer_steps"] = 2; mutations.append(extra_step)
        data = deepcopy(base); data["execution"]["biomedical_inputs_allowed"] = True; mutations.append(data)
        public = deepcopy(base); public["execution"]["mmbu_inputs_allowed"] = True; mutations.append(public)
        gpu = deepcopy(base); gpu["scheduler"]["gpu_count"] = 2; mutations.append(gpu)
        retry = deepcopy(base); retry["scheduler"]["max_retries"] = 1; mutations.append(retry)
        projector = deepcopy(base); projector["architecture"]["projector_module"] = "model.visual"; mutations.append(projector)
        module = deepcopy(base); module["architecture"]["modules_to_save"] = ["visual"]; mutations.append(module)
        floating = deepcopy(base); floating["model"]["revision"] = "main"; mutations.append(floating)
        for record in mutations:
            record["record_digest"] = canonical.record_digest(record)
            with self.subTest(record=record), self.assertRaises(ContractViolation):
                b2_preflight.validate_preflight_config(record)

    def test_checked_in_config_is_canonical_and_sealed(self):
        path = Path(__file__).resolve().parents[2] / "config/phase1/b2-mocs-preflight.json"
        record = b2_preflight.load_preflight_config(path)
        self.assertEqual(path.read_bytes(), canonical.dumps(record) + b"\n")

    def test_full_b1_pin_is_projected_to_verifier_shape(self):
        pin_path = Path(__file__).resolve().parents[2] / "docs/phase1/b1-pin.json"
        full = canonical.loads(pin_path.read_bytes())
        projected = b2_native.project_b1_pin(full)
        self.assertEqual(set(projected), {
            "model_id", "model_revision", "processor_id", "processor_revision",
            "upstream_metadata", "weight_manifest",
        })
        self.assertEqual(set(projected["weight_manifest"]), {
            "index_path", "index_bytes", "index_sha256", "shards",
        })
        self.assertEqual(projected["model_revision"], full["model_revision"])

    def test_trainable_scope_accepts_only_language_lora_and_projector_copy(self):
        self.assertIsNotNone(b2_native, "B2 native runner is missing")
        targets = [
            "model.language_model.layers.0.self_attn.q_proj",
            "model.language_model.layers.0.self_attn.v_proj",
        ]
        projector = [
            "model.visual.merger.ln_q.weight",
            "model.visual.merger.mlp.0.bias",
        ]
        names = sorted([
            *(f"base_model.model.{name}.lora_{side}.default.weight" for name in targets for side in ("A", "B")),
            *(f"base_model.model.{name.replace('model.visual.merger.', 'model.visual.merger.modules_to_save.default.')}" for name in projector),
        ])
        summary = b2_native.validate_trainable_scope(names, targets, projector)
        self.assertEqual(summary["all"], names)
        self.assertEqual(len(summary["language_lora"]), 4)
        self.assertEqual(len(summary["projector"]), 2)
        for bad in (
            names + ["base_model.model.model.visual.blocks.31.attn.qkv.weight"],
            names[:-1],
            names + [names[0]],
        ):
            with self.subTest(bad=bad), self.assertRaises(ContractViolation):
                b2_native.validate_trainable_scope(bad, targets, projector)

    def test_export_scope_is_exact_and_excludes_vision_tower(self):
        self.assertIsNotNone(b2_native, "B2 native runner is missing")
        targets = [
            "model.language_model.layers.0.self_attn.q_proj",
            "model.language_model.layers.0.self_attn.v_proj",
        ]
        projector = [
            "model.visual.merger.ln_q.weight",
            "model.visual.merger.mlp.0.bias",
        ]
        keys = sorted([
            *(f"base_model.model.{name}.lora_{side}.weight" for name in targets for side in ("A", "B")),
            *(f"base_model.model.{name}" for name in projector),
        ])
        self.assertEqual(b2_native.validate_adapter_state_keys(keys, targets, projector), keys)
        with self.assertRaises(ContractViolation):
            b2_native.validate_adapter_state_keys(keys + ["base_model.model.model.visual.blocks.31.norm1.weight"], targets, projector)

    def test_first_step_update_inventory_requires_projector_and_lora_b_only(self):
        language = sorted([
            "base_model.model.model.language_model.layers.0.self_attn.q_proj.lora_A.default.weight",
            "base_model.model.model.language_model.layers.0.self_attn.q_proj.lora_B.default.weight",
        ])
        projector = ["base_model.model.model.visual.merger.modules_to_save.default.ln_q.weight"]
        declared = sorted(language + projector)
        expected = sorted([language[1], *projector])
        result = b2_native.validate_update_inventory(
            declared, declared, expected, language, projector,
        )
        self.assertEqual(result["updated"], expected)
        for bad in (language, projector, declared):
            with self.subTest(bad=bad), self.assertRaises(ContractViolation):
                b2_native.validate_update_inventory(declared, declared, sorted(bad), language, projector)

    def test_reload_comparison_binds_inputs_pixels_and_logits(self):
        self.assertIsNotNone(b2_reload, "B2 offline reload tool is missing")
        reference = {
            "fixture_id": "small-rgb", "prompt": "prompt", "input_ids": [1, 2],
            "attention_mask": [1, 1], "logits_first_32": [0.0, 1.0],
            "logit_atol": 0.5, "pixel_values_sha256": "a" * 64,
        }
        observed = {
            "fixture_id": "small-rgb", "input_ids": [1, 2], "attention_mask": [1, 1],
            "logits_first_32": [0.25, 0.75], "pixel_values_sha256": "a" * 64,
        }
        self.assertEqual(b2_reload.validate_reload(reference, observed), 0.25)
        for key, value in (("input_ids", [2, 1]), ("pixel_values_sha256", "b" * 64),
                           ("logits_first_32", [0.0, 2.0])):
            bad = deepcopy(observed); bad[key] = value
            with self.subTest(key=key), self.assertRaises(ContractViolation):
                b2_reload.validate_reload(reference, bad)

    def test_network_guard_and_slurm_envelope_are_one_job_offline(self):
        import socket
        original_create = socket.create_connection
        original_socket = socket.socket
        try:
            b2_reload.install_network_guard()
            with self.assertRaises(PermissionError):
                socket.create_connection(("127.0.0.1", 9))
            with socket.socket() as guarded:
                with self.assertRaises(PermissionError):
                    guarded.connect(("127.0.0.1", 9))
        finally:
            socket.create_connection = original_create
            socket.socket = original_socket
        script = (Path(__file__).resolve().parents[2] / "tools/b2_native_preflight.sbatch").read_text()
        for directive in ("#SBATCH --partition=epyc-gpu", "#SBATCH --account=allusers",
                          "#SBATCH --qos=u-default", "#SBATCH --gres=gpu:tesla_a100_80gb:1",
                          "#SBATCH --cpus-per-task=4", "#SBATCH --mem=96G", "#SBATCH --time=02:00:00"):
            self.assertIn(directive, script)
        self.assertNotIn("sbatch ", script)
        self.assertEqual(script.count("b2_native_preflight.py"), 1)
        self.assertEqual(script.count("b2_offline_reload.py"), 1)
        self.assertIn("/tmp/npl015-mmbu-b2-run2-${SLURM_JOB_ID}", script)
        self.assertNotIn("/scratch/", script)
        self.assertNotIn("export CUDA_VISIBLE_DEVICES=", script)
        self.assertIn('test -n "${CUDA_VISIBLE_DEVICES:-}"', script)

    def test_terminal_record_requires_both_success_artifacts(self):
        self.assertIsNotNone(b2_finalize, "B2 finalizer is missing")
        source = [{"path": "tools/a.py", "bytes": 1, "sha256": "a" * 64}]
        complete = [
            {"path": "native-preflight.json", "bytes": 1, "sha256": "b" * 64},
            {"path": "offline-reload.json", "bytes": 1, "sha256": "c" * 64},
        ]
        passed = b2_finalize.build_terminal_record(
            0, "123", "node", "2026-10-23T00:00:00Z", "2026-10-23T00:01:00Z", source, complete,
        )
        self.assertEqual(passed["status"], "passed")
        self.assertEqual(passed["attempt"], 2)
        with self.assertRaises(ContractViolation):
            b2_finalize.build_terminal_record(
                0, "123", "node", "2026-10-23T00:00:00Z", "2026-10-23T00:01:00Z", source, complete[:1],
            )
        failed = b2_finalize.build_terminal_record(
            2, "123", "node", "2026-10-23T00:00:00Z", "2026-10-23T00:01:00Z", source, [],
        )
        self.assertEqual(failed["status"], "failed")


if __name__ == "__main__":
    unittest.main()
