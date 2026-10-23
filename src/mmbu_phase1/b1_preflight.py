"""Fail-closed controls for the authorized one-job B1 native preflight."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


_ACTIONS = [
    "acquire_pinned_model_and_runtime",
    "export_minimal_adapter",
    "fresh_network_denied_reload",
    "one_minimal_optimizer_step",
    "one_single_gpu_synthetic_preflight",
]
_PROHIBITED = [
    "biomedical_data_acquisition_or_use",
    "full_training",
    "mmbu_public_or_private_evaluation",
    "submission",
    "upload_or_public_release",
]
_FILES = [
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
]
_MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
_REVISION = "cc594898137f460bfe9f0759e9844b3ce807cfb5"
_REMOTE_ROOT = "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1"


def _exact_object(value: Any, path: str, expected: dict[str, Any]) -> dict:
    record = f.closed(value, path, expected)
    for key, wanted in expected.items():
        f.literal(record[key], f"{path}.{key}", wanted)
    return record


def validate_preflight_config(record: Any) -> dict:
    """Validate the immutable authorization, resource, path, and runtime envelope."""
    record = f.record(
        record,
        "b1_mocs_preflight",
        ("schema_id", "schema_version", "authorization", "scheduler", "paths", "model", "runtime", "execution", "record_digest"),
        "b1_preflight",
    )
    authorization = f.closed(
        record["authorization"],
        "b1_preflight.authorization",
        ("authorized_by", "authorized_at_utc", "authorized_actions", "prohibited_actions"),
    )
    f.literal(authorization["authorized_by"], "b1_preflight.authorization.authorized_by", "Aditya Raut")
    f.timestamp(authorization["authorized_at_utc"], "b1_preflight.authorization.authorized_at_utc")
    f.literal(authorization["authorized_actions"], "b1_preflight.authorization.authorized_actions", _ACTIONS)
    f.literal(authorization["prohibited_actions"], "b1_preflight.authorization.prohibited_actions", _PROHIBITED)

    _exact_object(record["scheduler"], "b1_preflight.scheduler", {
        "account": "allusers", "cluster": "mocshpc", "cpus_per_task": 8,
        "gpu_count": 1, "gpu_type": "tesla_a100_80gb", "max_jobs": 1,
        "max_retries": 0, "memory_gib": 96, "partition": "epyc-gpu",
        "qos": "u-default", "wall_seconds": 7200,
    })

    paths = f.closed(
        record["paths"],
        "b1_preflight.paths",
        ("cache_root", "evidence_root", "model_root", "remote_root", "venv_root", "wheelhouse_root"),
    )
    f.literal(paths["remote_root"], "b1_preflight.paths.remote_root", _REMOTE_ROOT)
    children = {
        "cache_root": "cache", "evidence_root": "evidence", "model_root": "model",
        "venv_root": "venv", "wheelhouse_root": "wheelhouse",
    }
    for key, leaf in children.items():
        expected = f"{_REMOTE_ROOT}/{leaf}"
        f.literal(paths[key], f"b1_preflight.paths.{key}", expected)
        candidate = PurePosixPath(paths[key])
        f.require(candidate.is_absolute() and str(candidate) == paths[key], f"b1_preflight.paths.{key}", "must be an absolute normalized POSIX path")
    f.require(len(set(paths.values())) == len(paths), "b1_preflight.paths", "paths must be distinct")

    model = f.closed(record["model"], "b1_preflight.model", ("allowed_files", "model_id", "revision"))
    f.literal(model["allowed_files"], "b1_preflight.model.allowed_files", _FILES)
    f.literal(model["model_id"], "b1_preflight.model.model_id", _MODEL_ID)
    f.literal(model["revision"], "b1_preflight.model.revision", _REVISION)

    _exact_object(record["runtime"], "b1_preflight.runtime", {
        "accelerate": "1.15.0", "attention_implementation": "sdpa",
        "cuda_wheel_index": "https://download.pytorch.org/whl/cu128",
        "numpy": "2.5.4", "peft": "0.21.2", "pillow": "13.0.0",
        "python": "3.12.12", "safetensors": "0.8.0", "torch": "2.11.0+cu128",
        "torchvision": "0.26.0+cu128", "transformers": "5.19.0",
        "trust_remote_code": False,
    })
    _exact_object(record["execution"], "b1_preflight.execution", {
        "allowed_input_classes": ["synthetic_engineering"],
        "biomedical_inputs_allowed": False, "dtype": "bfloat16",
        "gradient_accumulation_steps": 1, "mmbu_inputs_allowed": False,
        "network_policy": "acquisition_only_then_denied", "optimizer_steps": 1,
        "world_size": 1,
    })
    return record


def canonical_json_bytes(record: Any) -> bytes:
    validate_preflight_config(record)
    return canonical.dumps(record)


def load_preflight_config(path: str | os.PathLike[str]) -> dict:
    """Load one checked-in canonical JSON record with exactly one final newline."""
    raw = Path(path).read_bytes()
    f.require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), "b1_preflight.file", "must end in exactly one newline")
    try:
        record = canonical.loads_canonical(raw[:-1])
    except canonical.CanonicalJSONError as exc:
        f.fail("b1_preflight.file", f"must contain canonical JSON: {exc}")
    return validate_preflight_config(record)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_file(path: Path, label: str, expected_bytes: int | None, expected_sha: str | None) -> dict:
    try:
        stat = path.lstat()
    except FileNotFoundError:
        f.fail(label, "required artifact is missing")
    f.require(path.is_file() and not path.is_symlink(), label, "must be a regular non-symlink file")
    if expected_bytes is not None:
        f.literal(stat.st_size, f"{label}.bytes", expected_bytes)
    observed_sha = _sha256(path)
    if expected_sha is not None:
        f.digest(expected_sha, f"{label}.expected_sha256")
        f.literal(observed_sha, f"{label}.sha256", expected_sha)
    return {"path": path.name, "bytes": stat.st_size, "sha256": observed_sha}


def verify_pinned_artifacts(config: Any, pin: Any, root: str | os.PathLike[str]) -> list[dict]:
    """Verify that ``root`` contains exactly the immutable pinned model payload."""
    config = validate_preflight_config(config)
    root = Path(root)
    f.require(root.is_dir() and not root.is_symlink(), "artifacts.root", "must be a real directory")
    observed = sorted(entry.name for entry in root.iterdir())
    f.literal(observed, "artifacts.files", config["model"]["allowed_files"])

    pin = f.closed(pin, "pin", ("model_id", "model_revision", "processor_id", "processor_revision", "upstream_metadata", "weight_manifest"))
    for key in ("model_id", "processor_id"):
        f.literal(pin[key], f"pin.{key}", _MODEL_ID)
    for key in ("model_revision", "processor_revision"):
        f.literal(pin[key], f"pin.{key}", _REVISION)
    metadata = f.closed(pin["upstream_metadata"], "pin.upstream_metadata", (
        "config_sha256", "preprocessor_config_sha256", "generation_config_sha256",
        "tokenizer_config_sha256", "chat_template_sha256",
    ))
    weights = f.closed(pin["weight_manifest"], "pin.weight_manifest", ("index_path", "index_bytes", "index_sha256", "shards"))
    f.literal(weights["index_path"], "pin.weight_manifest.index_path", "model.safetensors.index.json")
    shards = f.array(weights["shards"], "pin.weight_manifest.shards")
    f.require(len(shards) == 5, "pin.weight_manifest.shards", "must contain exactly five shards")
    shard_by_path: dict[str, dict] = {}
    for index, shard in enumerate(shards):
        shard = f.closed(shard, f"pin.weight_manifest.shards[{index}]", ("path", "bytes", "sha256"))
        f.text(shard["path"], f"pin.weight_manifest.shards[{index}].path")
        f.integer(shard["bytes"], f"pin.weight_manifest.shards[{index}].bytes", minimum=1)
        f.digest(shard["sha256"], f"pin.weight_manifest.shards[{index}].sha256")
        f.require(shard["path"] not in shard_by_path, "pin.weight_manifest.shards", "duplicate shard path")
        shard_by_path[shard["path"]] = shard
    expected_shards = [name for name in _FILES if name.startswith("model-")]
    f.literal(sorted(shard_by_path), "pin.weight_manifest.shards.paths", expected_shards)

    metadata_files = {
        "config.json": "config_sha256", "preprocessor_config.json": "preprocessor_config_sha256",
        "generation_config.json": "generation_config_sha256", "tokenizer_config.json": "tokenizer_config_sha256",
        "chat_template.json": "chat_template_sha256",
    }
    manifest = []
    for name in _FILES:
        size = None
        digest = metadata.get(metadata_files[name]) if name in metadata_files else None
        if name == weights["index_path"]:
            size, digest = weights["index_bytes"], weights["index_sha256"]
            f.integer(size, "pin.weight_manifest.index_bytes", minimum=1)
            f.digest(digest, "pin.weight_manifest.index_sha256")
        elif name in shard_by_path:
            size, digest = shard_by_path[name]["bytes"], shard_by_path[name]["sha256"]
        manifest.append(_verify_file(root / name, f"artifacts.{name}", size, digest))
    return manifest
