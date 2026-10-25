"""Closed prospective contract for the replicated biomedical response screen."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import re
from typing import Any

from mmbu_phase1 import canonical, rational
from mmbu_phase1 import fields as f


_SHA = re.compile(r"[0-9a-f]{40}")
_TOP = (
    "authorization", "candidates", "interpretation", "resources", "schema_id", "schema_version",
    "screen_id", "selection", "training",
)
_CANDIDATE_KEYS = (
    "candidate_id", "expected_parameter_count", "loader_family", "model_id", "revision", "snapshot_name",
    "track_roles",
)
_CANDIDATES = (
    {
        "candidate_id": "rr-qwen35-9b",
        "expected_parameter_count": 9409813744,
        "loader_family": "qwen3_5",
        "model_id": "Qwen/Qwen3.5-9B",
        "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "snapshot_name": "f0-qwen35-9b",
        "track_roles": ["track2"],
    },
    {
        "candidate_id": "rr-qwen35-4b",
        "expected_parameter_count": 4539265536,
        "loader_family": "qwen3_5",
        "model_id": "Qwen/Qwen3.5-4B",
        "revision": "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        "snapshot_name": "f0-qwen35-4b",
        "track_roles": ["track2", "track3"],
    },
)
_SEEDS = [20261025, 20261026, 20261027]
_PROFILES = ["task_only", "dual"]
_CONTEXT = {
    "busbra": (
        ["body_part", "medical_domain", "modality"],
        {"body_part": "breast", "medical_domain": "radiology", "modality": "ultrasound"},
    ),
    "pathmnist": (
        ["medical_domain", "modality", "specimen", "stain"],
        {
            "medical_domain": "pathology",
            "modality": "histopathology",
            "specimen": "colorectal tissue",
            "stain": "hematoxylin and eosin",
        },
    ),
}


def validate_manifest(value: Any) -> dict:
    value = f.closed(value, "response", _TOP)
    f.literal(value["schema_id"], "response.schema_id", "mmbu.biomedical.replicated_response_screen")
    f.literal(value["schema_version"], "response.schema_version", 1)
    f.literal(value["screen_id"], "response.screen_id", "mmbu-replicated-response-2026-10-25")

    authorization = f.closed(
        value["authorization"], "response.authorization",
        ("biomedical_content_allowed", "mmbu_public_content_allowed", "prohibited_actions"),
    )
    f.literal(authorization["biomedical_content_allowed"],
              "response.authorization.biomedical_content_allowed", True)
    f.literal(authorization["mmbu_public_content_allowed"],
              "response.authorization.mmbu_public_content_allowed", False)
    f.literal(authorization["prohibited_actions"], "response.authorization.prohibited_actions",
              ["automatic_retry", "confirmation_opening", "model_promotion", "submission", "upload"])

    candidates = f.array(value["candidates"], "response.candidates", nonempty=True)
    f.literal(len(candidates), "response.candidates.length", len(_CANDIDATES))
    for index, (candidate, expected) in enumerate(zip(candidates, _CANDIDATES)):
        candidate = f.closed(candidate, f"response.candidates[{index}]", _CANDIDATE_KEYS)
        f.require(type(candidate["revision"]) is str and bool(_SHA.fullmatch(candidate["revision"])),
                  f"response.candidates[{index}].revision", "must be an exact lowercase commit")
        f.literal(candidate, f"response.candidates[{index}]", expected)

    selection = f.closed(value["selection"], "response.selection", (
        "allow_confirmation", "development_units_per_source", "selection_seed", "training_units_per_source",
    ))
    f.literal(selection, "response.selection", {
        "allow_confirmation": False,
        "development_units_per_source": 128,
        "selection_seed": 1729,
        "training_units_per_source": 512,
    })

    training = f.closed(value["training"], "response.training", (
        "attention_implementation", "dtype", "epochs", "gradient_clip_norm", "learning_rate", "lora_alpha",
        "lora_dropout", "lora_rank", "lora_target_suffixes", "max_context_new_tokens", "max_task_new_tokens",
        "profiles", "seeds", "weight_decay",
    ))
    f.literal(training["attention_implementation"], "response.training.attention_implementation", "sdpa")
    f.literal(training["dtype"], "response.training.dtype", "bfloat16")
    f.literal(training["epochs"], "response.training.epochs", 1)
    f.literal(training["gradient_clip_norm"], "response.training.gradient_clip_norm", 1)
    f.literal(training["learning_rate"], "response.training.learning_rate",
              {"denominator": 10000, "numerator": 1})
    rational.from_wire(training["learning_rate"], "response.training.learning_rate")
    f.literal(training["lora_alpha"], "response.training.lora_alpha", 16)
    f.literal(training["lora_dropout"], "response.training.lora_dropout", 0)
    f.literal(training["lora_rank"], "response.training.lora_rank", 8)
    f.literal(training["lora_target_suffixes"], "response.training.lora_target_suffixes", ["q_proj", "v_proj"])
    f.literal(training["max_context_new_tokens"], "response.training.max_context_new_tokens", 48)
    f.literal(training["max_task_new_tokens"], "response.training.max_task_new_tokens", 24)
    f.literal(training["profiles"], "response.training.profiles", _PROFILES)
    f.literal(training["seeds"], "response.training.seeds", _SEEDS)
    f.literal(training["weight_decay"], "response.training.weight_decay", 0)

    resources = f.closed(value["resources"], "response.resources", (
        "attempts_per_condition", "automatic_rescue_allowed", "gpu_model", "gpu_seconds_per_condition",
        "gpus_per_condition", "max_concurrent_conditions",
    ))
    f.literal(resources, "response.resources", {
        "attempts_per_condition": 1,
        "automatic_rescue_allowed": False,
        "gpu_model": "NVIDIA A100 80GB PCIe",
        "gpu_seconds_per_condition": 14400,
        "gpus_per_condition": 1,
        "max_concurrent_conditions": 5,
    })

    interpretation = f.closed(value["interpretation"], "response.interpretation", (
        "dual_q_minimum_gain", "maximum_dual_task_drop", "minimum_supporting_seeds", "promotion_allowed",
        "small_route_q_margin", "track3_multiplier_allowed",
    ))
    f.literal(interpretation, "response.interpretation", {
        "dual_q_minimum_gain": {"denominator": 100, "numerator": 1},
        "maximum_dual_task_drop": {"denominator": 100, "numerator": 1},
        "minimum_supporting_seeds": 2,
        "promotion_allowed": False,
        "small_route_q_margin": {"denominator": 100, "numerator": 3},
        "track3_multiplier_allowed": False,
    })
    for key in ("dual_q_minimum_gain", "maximum_dual_task_drop", "small_route_q_margin"):
        rational.from_wire(interpretation[key], f"response.interpretation.{key}")
    return value


def load_manifest(path: Path) -> dict:
    return validate_manifest(canonical.loads(path.read_bytes()))


def conditions(manifest: dict) -> list[dict]:
    validate_manifest(manifest)
    result = []
    for candidate in manifest["candidates"]:
        result.append({
            "candidate_id": candidate["candidate_id"],
            "condition_id": f"{candidate['candidate_id']}::base",
            "profile": "base",
            "training_seed": None,
        })
        for profile in manifest["training"]["profiles"]:
            for seed in manifest["training"]["seeds"]:
                result.append({
                    "candidate_id": candidate["candidate_id"],
                    "condition_id": f"{candidate['candidate_id']}::{profile}::{seed}",
                    "profile": profile,
                    "training_seed": seed,
                })
    return result


def condition_by_index(manifest: dict, index: int) -> dict:
    rows = conditions(manifest)
    f.integer(index, "response.condition_index", minimum=0)
    f.require(index < len(rows), "response.condition_index", "out of range")
    return rows[index]


def candidate_by_id(manifest: dict, candidate_id: str) -> dict:
    validate_manifest(manifest)
    matches = [row for row in manifest["candidates"] if row["candidate_id"] == candidate_id]
    f.require(len(matches) == 1, "response.candidate_id", "must resolve exactly one candidate")
    return matches[0]


def official_context_row(row: dict) -> dict:
    f.require(type(row) is dict, "response.row", "must be an object")
    source = row.get("source_id")
    f.require(source in _CONTEXT, "response.row.source_id", "unsupported source")
    fields, target = _CONTEXT[source]
    result = deepcopy(row)
    result["requested_context_fields"] = list(fields)
    result["context_target"] = deepcopy(target)
    result["context_target_text"] = canonical.dumps(target).decode("utf-8")
    result["context_prompt"] = (
        "Using only the medical image, return exactly one raw JSON object with exactly these keys: "
        + ", ".join(fields) + ". Every value must be a nonempty string. Return no Markdown or extra text."
    )
    return result


__all__ = [
    "candidate_by_id", "condition_by_index", "conditions", "load_manifest", "official_context_row",
    "validate_manifest",
]
