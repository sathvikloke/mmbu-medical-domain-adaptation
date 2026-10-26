"""Closed prospective contract for the replicated biomedical response screen."""

from __future__ import annotations

from copy import deepcopy
from collections import defaultdict
from fractions import Fraction
from math import floor
from pathlib import Path
import random
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


def paired_seed_mean_task_bootstrap(
    seed_rows: dict[str, list[dict]], *, iterations: int, bootstrap_seed: int, confidence: float,
) -> dict:
    """Estimate a source-balanced seed-mean paired task delta over shared group draws."""
    f.require(type(seed_rows) is dict and bool(seed_rows), "response.bootstrap.seed_rows",
              "must be a nonempty object")
    f.integer(iterations, "response.bootstrap.iterations", minimum=1)
    f.integer(bootstrap_seed, "response.bootstrap.bootstrap_seed", minimum=0)
    f.require(type(confidence) in (int, float) and not isinstance(confidence, bool)
              and 0 < confidence < 1, "response.bootstrap.confidence", "must be between zero and one")

    seed_ids = sorted(seed_rows, key=lambda value: value.encode("utf-8"))
    for seed_id in seed_ids:
        f.text(seed_id, "response.bootstrap.seed_id")
        f.array(seed_rows[seed_id], f"response.bootstrap.seed_rows[{seed_id}]", nonempty=True)

    aligned: dict[str, dict[str, dict]] = {}
    reference: dict[str, tuple[str, str, int]] | None = None
    for seed_id in seed_ids:
        rows: dict[str, dict] = {}
        for index, row in enumerate(seed_rows[seed_id]):
            path = f"response.bootstrap.seed_rows[{seed_id}][{index}]"
            f.closed(row, path, ("adapted_correct", "base_correct", "group_id", "record_id", "source_id"))
            for name in ("group_id", "record_id", "source_id"):
                f.text(row[name], f"{path}.{name}")
            for name in ("adapted_correct", "base_correct"):
                f.require(type(row[name]) is int and row[name] in (0, 1), f"{path}.{name}",
                          "must be integer zero or one")
            f.require(row["record_id"] not in rows, f"{path}.record_id", "must be unique")
            rows[row["record_id"]] = row
        projection = {
            record_id: (row["source_id"], row["group_id"], row["base_correct"])
            for record_id, row in rows.items()
        }
        if reference is None:
            reference = projection
        else:
            f.require(projection == reference, f"response.bootstrap.seed_rows[{seed_id}]",
                      "record, source, group, and base grades must align across seeds")
        aligned[seed_id] = rows

    assert reference is not None
    grouped: dict[str, dict[str, str]] = defaultdict(dict)
    for record_id, (source_id, group_id, _) in reference.items():
        f.require(group_id not in grouped[source_id], "response.bootstrap.group_id",
                  "the response screen requires one row per independent group")
        grouped[source_id][group_id] = record_id
    for source_id, groups in grouped.items():
        f.require(len(groups) >= 2, f"response.bootstrap.groups[{source_id}]",
                  "requires at least two independent groups")

    sources = sorted(grouped, key=lambda value: value.encode("utf-8"))

    def estimate(sampled: dict[str, list[str]]) -> Fraction:
        seed_estimates = []
        for seed_id in seed_ids:
            source_estimates = []
            for source_id in sources:
                identifiers = sampled[source_id]
                delta = sum(
                    aligned[seed_id][record_id]["adapted_correct"]
                    - aligned[seed_id][record_id]["base_correct"]
                    for record_id in identifiers
                )
                source_estimates.append(Fraction(delta, len(identifiers)))
            seed_estimates.append(sum(source_estimates, Fraction(0)) / len(source_estimates))
        return sum(seed_estimates, Fraction(0)) / len(seed_estimates)

    observed = {
        source_id: [grouped[source_id][group_id] for group_id in sorted(grouped[source_id])]
        for source_id in sources
    }
    point = estimate(observed)
    rng = random.Random(bootstrap_seed)
    samples = []
    for _ in range(iterations):
        sampled = {}
        for source_id in sources:
            groups = sorted(grouped[source_id])
            sampled[source_id] = [grouped[source_id][rng.choice(groups)] for _ in groups]
        samples.append(float(estimate(sampled)))
    samples.sort()

    def quantile(probability: float) -> float:
        position = (len(samples) - 1) * probability
        low = floor(position)
        high = min(low + 1, len(samples) - 1)
        return samples[low] + (samples[high] - samples[low]) * (position - low)

    tail = (1 - confidence) / 2
    return {
        "bootstrap_seed": bootstrap_seed,
        "confidence": confidence,
        "estimand": "source_balanced_seed_mean_paired_task_delta_on_fixed_development_population",
        "groups_per_source": {source_id: len(grouped[source_id]) for source_id in sources},
        "interval": [quantile(tail), quantile(1 - tail)],
        "iterations": iterations,
        "point_delta": rational.to_wire(point),
        "seed_ids": seed_ids,
        "warning": "Post-output exploratory interval unless every bootstrap literal was frozen before model output.",
    }


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
    "paired_seed_mean_task_bootstrap", "validate_manifest",
]
