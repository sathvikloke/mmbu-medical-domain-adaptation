"""CPU-only contract tests for the authorized B1 native preflight control plane."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation

try:
    from mmbu_phase1 import b1_preflight
except ImportError:
    b1_preflight = None

ACQUIRE_PATH = Path(__file__).resolve().parents[2] / "tools/b1_acquire.py"
acquire_spec = importlib.util.spec_from_file_location("b1_acquire", ACQUIRE_PATH)
if ACQUIRE_PATH.exists() and acquire_spec and acquire_spec.loader:
    b1_acquire = importlib.util.module_from_spec(acquire_spec)
    acquire_spec.loader.exec_module(b1_acquire)
else:
    b1_acquire = None

NATIVE_PATH = Path(__file__).resolve().parents[2] / "tools/b1_native_preflight.py"
native_spec = importlib.util.spec_from_file_location("b1_native_preflight", NATIVE_PATH)
if NATIVE_PATH.exists() and native_spec and native_spec.loader:
    b1_native = importlib.util.module_from_spec(native_spec)
    native_spec.loader.exec_module(b1_native)
else:
    b1_native = None

RELOAD_PATH = Path(__file__).resolve().parents[2] / "tools/b1_offline_reload.py"
reload_spec = importlib.util.spec_from_file_location("b1_offline_reload", RELOAD_PATH)
if RELOAD_PATH.exists() and reload_spec and reload_spec.loader:
    b1_reload = importlib.util.module_from_spec(reload_spec)
    reload_spec.loader.exec_module(b1_reload)
else:
    b1_reload = None


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class B1PreflightTests(unittest.TestCase):
    def valid_config(self) -> dict:
        record = {
            "schema_id": "mmbu.phase1.b1_mocs_preflight",
            "schema_version": 1,
            "authorization": {
                "authorized_by": "Aditya Raut",
                "authorized_at_utc": "2026-10-23T07:20:00Z",
                "authorized_actions": [
                    "acquire_pinned_model_and_runtime",
                    "export_minimal_adapter",
                    "fresh_network_denied_reload",
                    "one_minimal_optimizer_step",
                    "one_single_gpu_synthetic_preflight",
                ],
                "prohibited_actions": [
                    "biomedical_data_acquisition_or_use",
                    "full_training",
                    "mmbu_public_or_private_evaluation",
                    "submission",
                    "upload_or_public_release",
                ],
            },
            "scheduler": {
                "account": "allusers",
                "cluster": "mocshpc",
                "cpus_per_task": 8,
                "gpu_count": 1,
                "gpu_type": "tesla_a100_80gb",
                "max_jobs": 1,
                "max_retries": 0,
                "memory_gib": 96,
                "partition": "epyc-gpu",
                "qos": "u-default",
                "wall_seconds": 7200,
            },
            "paths": {
                "cache_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/cache",
                "evidence_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/evidence",
                "model_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/model",
                "remote_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1",
                "venv_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/venv",
                "wheelhouse_root": "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/wheelhouse",
            },
            "model": {
                "allowed_files": [
                    "chat_template.json",
                    "config.json",
                    "generation_config.json",
                    "merges.txt",
                    "model-00001-of-00005.safetensors",
                    "model-00002-of-00005.safetensors",
                    "model-00003-of-00005.safetensors",
                    "model-00004-of-00005.safetensors",
                    "model-00005-of-00005.safetensors",
                    "model.safetensors.index.json",
                    "preprocessor_config.json",
                    "tokenizer.json",
                    "tokenizer_config.json",
                    "vocab.json",
                ],
                "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
                "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
            },
            "runtime": {
                "accelerate": "1.15.0",
                "attention_implementation": "sdpa",
                "cuda_wheel_index": "https://download.pytorch.org/whl/cu128",
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
            "execution": {
                "allowed_input_classes": ["synthetic_engineering"],
                "biomedical_inputs_allowed": False,
                "dtype": "bfloat16",
                "gradient_accumulation_steps": 1,
                "mmbu_inputs_allowed": False,
                "network_policy": "acquisition_only_then_denied",
                "optimizer_steps": 1,
                "world_size": 1,
            },
            "record_digest": "",
        }
        return canonical.seal(record)

    def pin_and_files(self) -> tuple[dict, dict[str, bytes]]:
        files = {
            "config.json": b"config",
            "preprocessor_config.json": b"processor",
            "generation_config.json": b"generation",
            "tokenizer_config.json": b"tokenizer-config",
            "chat_template.json": b"template",
            "model.safetensors.index.json": b"index",
            "model-00001-of-00005.safetensors": b"one",
            "model-00002-of-00005.safetensors": b"two",
            "model-00003-of-00005.safetensors": b"three",
            "model-00004-of-00005.safetensors": b"four",
            "model-00005-of-00005.safetensors": b"five",
            "merges.txt": b"merges",
            "tokenizer.json": b"tokenizer",
            "vocab.json": b"vocab",
        }
        pin = {
            "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
            "model_revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
            "processor_id": "Qwen/Qwen2.5-VL-7B-Instruct",
            "processor_revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
            "upstream_metadata": {
                "config_sha256": sha(files["config.json"]),
                "preprocessor_config_sha256": sha(files["preprocessor_config.json"]),
                "generation_config_sha256": sha(files["generation_config.json"]),
                "tokenizer_config_sha256": sha(files["tokenizer_config.json"]),
                "chat_template_sha256": sha(files["chat_template.json"]),
            },
            "weight_manifest": {
                "index_path": "model.safetensors.index.json",
                "index_bytes": len(files["model.safetensors.index.json"]),
                "index_sha256": sha(files["model.safetensors.index.json"]),
                "shards": [
                    {"path": name, "bytes": len(files[name]), "sha256": sha(files[name])}
                    for name in sorted(files)
                    if name.startswith("model-")
                ],
            },
        }
        return pin, files

    def test_module_exists_and_valid_config_is_canonical(self):
        self.assertIsNotNone(b1_preflight, "B1 preflight module is missing")
        record = self.valid_config()
        self.assertEqual(b1_preflight.validate_preflight_config(record), record)
        self.assertEqual(b1_preflight.canonical_json_bytes(record), canonical.dumps(record))

    def test_checked_in_config_loads_as_exact_canonical_bytes(self):
        config_path = Path(__file__).resolve().parents[2] / "config/phase1/b1-mocs-preflight.json"
        record = b1_preflight.load_preflight_config(config_path)
        self.assertEqual(record, self.valid_config())
        self.assertEqual(config_path.read_bytes(), canonical.dumps(record) + b"\n")

    def test_config_is_closed_and_scope_and_resource_caps_fail_closed(self):
        base = self.valid_config()
        mutations = []
        extra = deepcopy(base); extra["surprise"] = True; mutations.append(extra)
        jobs = deepcopy(base); jobs["scheduler"]["max_jobs"] = 2; mutations.append(jobs)
        retries = deepcopy(base); retries["scheduler"]["max_retries"] = 1; mutations.append(retries)
        gpu = deepcopy(base); gpu["scheduler"]["gpu_count"] = 2; mutations.append(gpu)
        steps = deepcopy(base); steps["execution"]["optimizer_steps"] = 2; mutations.append(steps)
        biomedical = deepcopy(base); biomedical["execution"]["biomedical_inputs_allowed"] = True; mutations.append(biomedical)
        public = deepcopy(base); public["execution"]["mmbu_inputs_allowed"] = True; mutations.append(public)
        floating = deepcopy(base); floating["model"]["revision"] = "main"; mutations.append(floating)
        for record in mutations:
            record["record_digest"] = canonical.record_digest(record)
            with self.subTest(record=record), self.assertRaises(ContractViolation):
                b1_preflight.validate_preflight_config(record)

    def test_pinned_artifacts_reject_missing_extra_size_and_hash_drift(self):
        config = self.valid_config()
        pin, files = self.pin_and_files()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, raw in files.items():
                (root / name).write_bytes(raw)
            manifest = b1_preflight.verify_pinned_artifacts(config, pin, root)
            self.assertEqual([row["path"] for row in manifest], config["model"]["allowed_files"])
            for mutation, expected_path in (("missing", "model-00005-of-00005.safetensors"),
                                             ("extra", "unexpected.bin"),
                                             ("drift", "model-00001-of-00005.safetensors")):
                with self.subTest(mutation=mutation):
                    if mutation == "missing":
                        (root / expected_path).unlink()
                    elif mutation == "extra":
                        (root / expected_path).write_bytes(b"extra")
                    else:
                        (root / expected_path).write_bytes(b"same-size-drift")
                    with self.assertRaises(ContractViolation):
                        b1_preflight.verify_pinned_artifacts(config, pin, root)
                    for path in root.iterdir():
                        path.unlink()
                    for name, raw in files.items():
                        (root / name).write_bytes(raw)

    def test_acquisition_plan_is_immutable_and_floating_free(self):
        self.assertIsNotNone(b1_acquire, "B1 acquisition tool is missing")
        config = self.valid_config()
        plan = b1_acquire.build_plan(config)
        self.assertEqual([row["path"] for row in plan["model_files"]], config["model"]["allowed_files"])
        for row in plan["model_files"]:
            self.assertIn(config["model"]["revision"], row["url"])
            self.assertNotIn("/main/", row["url"])
        self.assertEqual(plan["requirements"], [
            "accelerate==1.15.0", "numpy==2.5.4", "peft==0.21.2", "pillow==13.0.0",
            "safetensors==0.8.0", "torch==2.11.0+cu128", "torchvision==0.26.0+cu128",
            "transformers==5.19.0",
        ])

    def test_resolver_report_rejects_vcs_editable_missing_and_version_drift(self):
        config = self.valid_config()
        installs = []
        for requirement in b1_acquire.build_plan(config)["requirements"]:
            name, version = requirement.split("==")
            installs.append({
                "metadata": {"name": name, "version": version},
                "download_info": {
                    "url": f"https://packages.example/{name}-{version}.whl",
                    "archive_info": {"hash": "sha256=" + "a" * 64},
                },
                "requested": True,
            })
        report = {"version": "1", "install": installs}
        self.assertEqual(b1_acquire.validate_resolver_report(report, config), report)
        mutations = []
        missing = deepcopy(report); missing["install"].pop(); mutations.append(missing)
        drift = deepcopy(report); drift["install"][0]["metadata"]["version"] = "0"; mutations.append(drift)
        vcs = deepcopy(report); vcs["install"][0]["download_info"]["vcs_info"] = {"vcs": "git"}; mutations.append(vcs)
        editable = deepcopy(report); editable["install"][0]["download_info"]["dir_info"] = {"editable": True}; mutations.append(editable)
        unhashed = deepcopy(report); unhashed["install"][0]["download_info"]["archive_info"] = {}; mutations.append(unhashed)
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ContractViolation):
                b1_acquire.validate_resolver_report(mutation, config)
        inventory = []
        for item in installs:
            name = item["metadata"]["name"]
            version = item["metadata"]["version"]
            digest = item["download_info"]["archive_info"]["hash"][7:]
            inventory.append({"path": f"{name}-{version}-py3-none-any.whl", "bytes": 1, "sha256": digest})
        inventory.sort(key=lambda row: row["path"].encode("utf-8"))
        self.assertEqual(b1_acquire.validate_resolver_report(unhashed, config, inventory), unhashed)
        inventory.pop(0)
        with self.assertRaises(ContractViolation):
            b1_acquire.validate_resolver_report(unhashed, config, inventory)

    def test_download_inventory_rejects_missing_extra_and_hash_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "one.whl").write_bytes(b"one")
            (root / "two.whl").write_bytes(b"two")
            inventory = b1_acquire.inventory_directory(root, ".whl")
            self.assertEqual(b1_acquire.verify_inventory(root, inventory, ".whl"), inventory)
            (root / "one.whl").write_bytes(b"ONE")
            with self.assertRaises(ContractViolation):
                b1_acquire.verify_inventory(root, inventory, ".whl")

    def test_synthetic_fixture_inventory_is_closed_and_deterministic(self):
        self.assertIsNotNone(b1_native, "B1 native runner is missing")
        specs = b1_native.fixture_specs()
        self.assertEqual([row["id"] for row in specs], [
            "small-rgb", "large-rgb", "nonsquare-rgb", "extreme-aspect-rgb",
            "grayscale-conversion", "rgba-conversion", "exif-orientation",
            "boundary-27", "boundary-28", "boundary-29",
        ])
        self.assertEqual(specs, b1_native.fixture_specs())
        for row in specs:
            self.assertEqual(set(row), {"id", "raw_mode", "raw_size", "seed", "transform"})
            self.assertGreater(row["raw_size"][0], 0)
            self.assertGreater(row["raw_size"][1], 0)

    def test_target_only_labels_mask_padding_prompt_and_image_tokens(self):
        input_ids = [[0, 0, 10, 11, 12, 13], [0, 20, 21, 22, 23, 24]]
        attention = [[0, 0, 1, 1, 1, 1], [0, 1, 1, 1, 1, 1]]
        labels = b1_native.build_target_only_labels(input_ids, attention, [3, 3])
        self.assertEqual(labels, [[-100, -100, -100, -100, -100, 13], [-100, -100, -100, -100, 23, 24]])
        with self.assertRaises(ContractViolation):
            b1_native.build_target_only_labels(input_ids, attention, [4, 5])

    def test_exact_lora_targets_exclude_vision_and_fail_closed(self):
        names = [
            "model.language_model.layers.0.self_attn.q_proj",
            "model.language_model.layers.0.self_attn.v_proj",
            "model.language_model.layers.0.self_attn.k_proj",
            "model.visual.blocks.0.attn.q_proj",
        ]
        self.assertEqual(b1_native.exact_lora_targets(names), names[:2])
        with self.assertRaises(ContractViolation):
            b1_native.exact_lora_targets(["model.visual.blocks.0.attn.q_proj"])

    def test_trainable_gradient_and_update_inventory_closes(self):
        declared = ["adapter.a", "adapter.b"]
        self.assertEqual(
            b1_native.validate_update_inventory(declared, declared, declared, declared),
            {"declared": declared, "finite_gradients": declared, "updated": declared},
        )
        for trainable, gradients, updated in ((declared + ["base.x"], declared, declared),
                                               (declared, ["adapter.a"], declared),
                                               (declared, declared, ["adapter.a"])):
            with self.assertRaises(ContractViolation):
                b1_native.validate_update_inventory(declared, trainable, gradients, updated)

    def test_mrope_summary_and_numeric_comparison_fail_closed(self):
        summary = {
            "position_shape": [3, 2, 10], "position_dtype": "torch.int64",
            "rope_deltas_shape": [2, 1], "rope_deltas_dtype": "torch.int64",
            "image_temporal_unique_counts": [1, 1], "image_grid_temporal_counts": [1, 1],
            "position_sha256": "a" * 64, "rope_deltas_sha256": "b" * 64,
        }
        self.assertEqual(b1_native.validate_mrope_summary(summary, 2, 10), summary)
        for key, value in (("position_shape", [3, 1, 10]),
                           ("position_dtype", "torch.float32"),
                           ("image_temporal_unique_counts", [2, 1])):
            mutation = deepcopy(summary); mutation[key] = value
            with self.subTest(key=key), self.assertRaises(ContractViolation):
                b1_native.validate_mrope_summary(mutation, 2, 10)
        self.assertAlmostEqual(b1_native.compare_logits([0.0, 1.0], [0.1, 1.1], 0.5, "x"), 0.1)
        with self.assertRaises(ContractViolation):
            b1_native.compare_logits([0.0], [1.0], 0.5, "x")

    def test_offline_reload_reference_rejects_identity_and_numeric_drift(self):
        self.assertIsNotNone(b1_reload, "B1 offline reload tool is missing")
        reference = {
            "fixture_id": "small-rgb", "prompt": "prompt", "input_ids": [1, 2],
            "attention_mask": [1, 1], "logits_first_32": [0.0, 1.0],
            "logit_atol": 0.5, "pixel_values_sha256": "a" * 64,
        }
        observed = {"fixture_id": "small-rgb", "input_ids": [1, 2],
                    "attention_mask": [1, 1], "logits_first_32": [0.1, 1.1],
                    "pixel_values_sha256": "a" * 64}
        self.assertLessEqual(b1_reload.validate_reload(reference, observed), 0.5)
        for key, value in (("fixture_id", "other"), ("input_ids", [2, 1]),
                           ("pixel_values_sha256", "b" * 64), ("logits_first_32", [1.0, 2.0])):
            mutation = deepcopy(observed); mutation[key] = value
            with self.subTest(key=key), self.assertRaises(ContractViolation):
                b1_reload.validate_reload(reference, mutation)

    def test_network_guard_denies_socket_and_slurm_is_exactly_one_job(self):
        import socket
        original_create = socket.create_connection
        original_socket = socket.socket
        try:
            b1_reload.install_network_guard()
            with self.assertRaises(PermissionError):
                socket.create_connection(("127.0.0.1", 9))
            with socket.socket() as guarded:
                with self.assertRaises(PermissionError):
                    guarded.connect(("127.0.0.1", 9))
        finally:
            socket.create_connection = original_create
            socket.socket = original_socket
        script = (Path(__file__).resolve().parents[2] / "tools/b1_native_preflight.sbatch").read_text()
        for directive in ("#SBATCH --partition=epyc-gpu", "#SBATCH --account=allusers",
                          "#SBATCH --qos=u-default", "#SBATCH --gres=gpu:tesla_a100_80gb:1",
                          "#SBATCH --cpus-per-task=8", "#SBATCH --mem=96G", "#SBATCH --time=02:00:00"):
            self.assertIn(directive, script)
        self.assertNotIn("sbatch ", script)
        self.assertEqual(script.count("b1_native_preflight.py"), 1)
        self.assertEqual(script.count("b1_offline_reload.py"), 1)
        self.assertIn("/tmp/npl015-mmbu-b1-${SLURM_JOB_ID}", script)
        self.assertNotIn("/scratch/", script)
        native_source = NATIVE_PATH.read_text()
        reload_source = RELOAD_PATH.read_text()
        self.assertIn('backend="pil"', native_source)
        self.assertIn("native.load_pil_processor(model_root)", reload_source)
        self.assertNotIn("use_fast=True", native_source + reload_source)
        self.assertNotIn("AutoProcessor", native_source + reload_source)


if __name__ == "__main__":
    unittest.main()
