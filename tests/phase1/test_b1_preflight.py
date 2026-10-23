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


if __name__ == "__main__":
    unittest.main()
