"""Fail-closed controls for the synthetic B2 dual-objective native preflight."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


_REMOTE_ROOT = "/storage/home/npl015/mmbu-b2-objective/2026-10-23-run3"
_MODEL_ROOT = "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/model"
_VENV_ROOT = "/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/venv"


def _exact(value: Any, path: str, expected: dict[str, Any]) -> dict:
    record = f.closed(value, path, expected)
    for key, wanted in expected.items():
        f.literal(record[key], f"{path}.{key}", wanted)
    return record


def validate_preflight_config(record: Any) -> dict:
    record = f.record(
        record,
        "b2_dual_objective_preflight",
        ("schema_id", "schema_version", "attempt", "authorization", "execution", "model",
         "objective", "paths", "runtime", "scheduler", "record_digest"),
        "b2_dual_preflight",
    )
    f.literal(record["attempt"], "b2_dual_preflight.attempt", 3)
    _exact(record["authorization"], "b2_dual_preflight.authorization", {
        "authorized_by": "Aditya Raut",
        "authorized_at_utc": "2026-10-23T22:00:00Z",
        "authorized_actions": [
            "one_minimal_optimizer_step",
            "one_single_gpu_fixed_singleton_accumulation_preflight",
            "reuse_verified_pinned_b1_model_and_runtime",
            "reuse_verified_b2_projector_architecture",
        ],
        "prohibited_actions": [
            "biomedical_data_acquisition_or_use", "full_training",
            "mmbu_public_or_private_evaluation", "submission", "upload_or_public_release",
        ],
    })
    _exact(record["execution"], "b2_dual_preflight.execution", {
        "allowed_input_classes": ["synthetic_engineering"],
        "biomedical_inputs_allowed": False,
        "dtype": "bfloat16",
        "mmbu_inputs_allowed": False,
        "network_policy": "denied",
        "optimizer_steps": 1,
        "world_size": 1,
    })
    _exact(record["model"], "b2_dual_preflight.model", {
        "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
    })
    _exact(record["objective"], "b2_dual_preflight.objective", {
        "context_unit_share": {"denominator": 4, "numerator": 1},
        "gradient_cosine_minimum": 0.99875,
        "gradient_max_abs_tolerance": 0.03125,
        "gradient_relative_l2_tolerance": 0.05,
        "loss_abs_tolerance": 0.00390625,
        "comparison_orders": [
            ["u1-task", "u1-context", "u2-task"],
            ["u2-task", "u1-context", "u1-task"],
        ],
        "microbatch_size": 1,
        "objective_id": "synthetic_answer_context_unit_mass_v1",
        "reduction": "global_weighted_numerator_over_denominator",
        "task_unit_share": {"denominator": 4, "numerator": 3},
        "token_normalization": "uniform_within_view_v1",
        "zero_applicable_training_policy": "reallocate_context_share_to_task",
    })
    paths = _exact(record["paths"], "b2_dual_preflight.paths", {
        "evidence_root": f"{_REMOTE_ROOT}/evidence",
        "model_root": _MODEL_ROOT,
        "remote_root": _REMOTE_ROOT,
        "venv_root": _VENV_ROOT,
    })
    for key, value in paths.items():
        path = PurePosixPath(value)
        f.require(path.is_absolute() and str(path) == value, f"b2_dual_preflight.paths.{key}",
                  "must be an absolute normalized POSIX path")
    _exact(record["runtime"], "b2_dual_preflight.runtime", {
        "attention_implementation": "sdpa", "peft": "0.21.2", "python": "3.12.12",
        "torch": "2.11.0+cu128", "transformers": "5.19.0", "trust_remote_code": False,
    })
    _exact(record["scheduler"], "b2_dual_preflight.scheduler", {
        "account": "allusers", "cluster": "mocshpc", "cpus_per_task": 4,
        "gpu_count": 1, "gpu_type": "tesla_a100_80gb", "max_jobs": 1, "max_retries": 0,
        "memory_gib": 96, "partition": "epyc-gpu", "qos": "u-default", "wall_seconds": 7200,
    })
    return record


def load_preflight_config(path: str | os.PathLike[str]) -> dict:
    raw = Path(path).read_bytes()
    f.require(raw.endswith(b"\n") and not raw.endswith(b"\n\n"), "b2_dual_preflight.file",
              "must end in exactly one newline")
    try:
        record = canonical.loads_canonical(raw[:-1])
    except canonical.CanonicalJSONError as exc:
        f.fail("b2_dual_preflight.file", f"must contain canonical JSON: {exc}")
    return validate_preflight_config(record)
