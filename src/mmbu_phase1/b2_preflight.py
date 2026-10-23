"""Fail-closed controls for the synthetic-only B2-P projector preflight."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


_ACTIONS = [
    "fresh_network_denied_reload",
    "one_minimal_optimizer_step",
    "one_single_gpu_synthetic_b2_projector_preflight",
    "reuse_verified_pinned_b1_model_and_runtime",
    "standard_peft_adapter_export",
]
_PROHIBITED = [
    "biomedical_data_acquisition_or_use",
    "full_training",
    "mmbu_public_or_private_evaluation",
    "submission",
    "upload_or_public_release",
]
_PROJECTOR_PARAMETERS = [
    "model.visual.merger.ln_q.weight",
    "model.visual.merger.mlp.0.bias",
    "model.visual.merger.mlp.0.weight",
    "model.visual.merger.mlp.2.bias",
    "model.visual.merger.mlp.2.weight",
]
_LANGUAGE_TARGET_REGEX = r"^model\.language_model\.layers\.\d+\.self_attn\.(?:q_proj|v_proj)$"
_MODEL_ID = "Qwen/Qwen2.5-VL-7B-Instruct"
_REVISION = "cc594898137f460bfe9f0759e9844b3ce807cfb5"
_B1_ROOT = "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1"
_B1_EVIDENCE_ROOT = "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run9/evidence"
_REMOTE_ROOT = "/storage/home/npl015/mmbu-b2-preflight/2026-10-23-run2"


def _exact_object(value: Any, path: str, expected: dict[str, Any]) -> dict:
    record = f.closed(value, path, expected)
    for key, wanted in expected.items():
        f.literal(record[key], f"{path}.{key}", wanted)
    return record


def validate_preflight_config(record: Any) -> dict:
    """Validate the immutable authorization, architecture, and runtime envelope."""
    record = f.record(
        record,
        "b2_mocs_preflight",
        (
            "schema_id", "schema_version", "attempt", "authorization", "architecture",
            "execution", "model", "paths", "runtime", "scheduler", "record_digest",
        ),
        "b2_preflight",
    )
    f.literal(record["attempt"], "b2_preflight.attempt", 2)
    authorization = f.closed(
        record["authorization"],
        "b2_preflight.authorization",
        ("authorized_by", "authorized_at_utc", "authorized_actions", "prohibited_actions"),
    )
    f.literal(authorization["authorized_by"], "b2_preflight.authorization.authorized_by", "Aditya Raut")
    f.timestamp(authorization["authorized_at_utc"], "b2_preflight.authorization.authorized_at_utc")
    f.literal(authorization["authorized_actions"], "b2_preflight.authorization.authorized_actions", _ACTIONS)
    f.literal(authorization["prohibited_actions"], "b2_preflight.authorization.prohibited_actions", _PROHIBITED)

    _exact_object(record["architecture"], "b2_preflight.architecture", {
        "recipe_id": "B2-P",
        "projector_module": "model.visual.merger",
        "projector_parameters": _PROJECTOR_PARAMETERS,
        "language_target_regex": _LANGUAGE_TARGET_REGEX,
        "learning_rate": 0.01,
        "lora_alpha": 4,
        "lora_dropout": 0,
        "lora_rank": 2,
        "modules_to_save": ["visual.merger"],
    })
    _exact_object(record["execution"], "b2_preflight.execution", {
        "allowed_input_classes": ["synthetic_engineering"],
        "biomedical_inputs_allowed": False,
        "dtype": "bfloat16",
        "gradient_accumulation_steps": 1,
        "mmbu_inputs_allowed": False,
        "network_policy": "denied",
        "optimizer_steps": 1,
        "world_size": 1,
    })
    _exact_object(record["model"], "b2_preflight.model", {
        "model_id": _MODEL_ID,
        "revision": _REVISION,
    })

    paths = _exact_object(record["paths"], "b2_preflight.paths", {
        "b1_evidence_root": _B1_EVIDENCE_ROOT,
        "evidence_root": f"{_REMOTE_ROOT}/evidence",
        "model_root": f"{_B1_ROOT}/model",
        "remote_root": _REMOTE_ROOT,
        "venv_root": f"{_B1_ROOT}/venv",
    })
    for key, value in paths.items():
        candidate = PurePosixPath(value)
        f.require(candidate.is_absolute() and str(candidate) == value, f"b2_preflight.paths.{key}",
                  "must be an absolute normalized POSIX path")
    f.require(len(set(paths.values())) == len(paths), "b2_preflight.paths", "paths must be distinct")

    _exact_object(record["runtime"], "b2_preflight.runtime", {
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
    })
    _exact_object(record["scheduler"], "b2_preflight.scheduler", {
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
    })
    return record


def canonical_json_bytes(record: Any) -> bytes:
    validate_preflight_config(record)
    return canonical.dumps(record)


def load_preflight_config(path: str | os.PathLike[str]) -> dict:
    raw = Path(path).read_bytes()
    f.require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), "b2_preflight.file",
              "must end in exactly one newline")
    try:
        record = canonical.loads_canonical(raw[:-1])
    except canonical.CanonicalJSONError as exc:
        f.fail("b2_preflight.file", f"must contain canonical JSON: {exc}")
    return validate_preflight_config(record)
