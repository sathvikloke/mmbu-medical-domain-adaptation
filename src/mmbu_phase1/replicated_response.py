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

from mmbu_phase1 import biomedical_lane1, canonical, evidence, rational
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


def grade_task_rows(rows: list[dict], base_predictions: list[dict], adapted_predictions: list[dict]) -> list[dict]:
    """Convert aligned predictions into explicit paired binary task grades."""
    f.require(len(rows) == len(base_predictions) == len(adapted_predictions), "response.aggregate.predictions",
              "rows, base predictions, and adapted predictions must align one-to-one")
    grades = []
    for index, (row, base, adapted) in enumerate(zip(rows, base_predictions, adapted_predictions)):
        path = f"response.aggregate.predictions[{index}]"
        f.require(base.get("row_id") == adapted.get("row_id") == row.get("row_id"), f"{path}.row_id",
                  "does not align")
        grades.append({
            "adapted_correct": int(
                biomedical_lane1.normalize_answer(adapted.get("task"))
                == biomedical_lane1.normalize_answer(row.get("task_target"))
            ),
            "base_correct": int(
                biomedical_lane1.normalize_answer(base.get("task"))
                == biomedical_lane1.normalize_answer(row.get("task_target"))
            ),
            "group_id": row["independent_unit_id"],
            "record_id": row["row_id"],
            "source_id": row["source_id"],
        })
    return grades


def analyze_candidate(
    rows: list[dict], base_predictions: list[dict], profile_predictions: dict[str, dict[str, list[dict]]],
    *, iterations: int, bootstrap_seed: int, confidence: float,
) -> dict:
    """Replay the exploratory paired task intervals for one candidate."""
    f.require(type(profile_predictions) is dict and set(profile_predictions) == {"dual", "task_only"},
              "response.aggregate.profile_predictions", "must contain dual and task_only exactly")
    profiles = {}
    for profile in ("task_only", "dual"):
        predictions_by_seed = profile_predictions[profile]
        f.require(type(predictions_by_seed) is dict and bool(predictions_by_seed),
                  f"response.aggregate.{profile}", "must contain at least one seed")
        seed_rows = {
            seed_id: grade_task_rows(rows, base_predictions, predictions)
            for seed_id, predictions in predictions_by_seed.items()
        }
        profiles[profile] = paired_seed_mean_task_bootstrap(
            seed_rows, iterations=iterations, bootstrap_seed=bootstrap_seed, confidence=confidence,
        )
    return {
        "inference": "post_output_exploratory_fixed_development_population",
        "profiles": profiles,
        "promotion_eligible": False,
    }


def _portable_json(root: Path, relative: str) -> Any:
    return canonical.loads((Path(root) / relative).read_bytes())


def _validate_development_projection(value: Any, screen_id: str) -> list[dict]:
    value = f.closed(value, "portable.population", (
        "mmbu_public_content_used", "rows", "schema_id", "schema_version", "screen_id",
        "source_payloads_included",
    ))
    f.literal(value["schema_id"], "portable.population.schema_id",
              "mmbu.biomedical.replicated_response_development_projection")
    f.literal(value["schema_version"], "portable.population.schema_version", 1)
    f.literal(value["screen_id"], "portable.population.screen_id", screen_id)
    f.literal(value["mmbu_public_content_used"], "portable.population.mmbu_public_content_used", False)
    f.literal(value["source_payloads_included"], "portable.population.source_payloads_included", False)
    rows = f.array(value["rows"], "portable.population.rows", nonempty=True)
    f.literal(len(rows), "portable.population.rows.length", 256)
    row_ids = []
    unit_ids = []
    counts: dict[str, int] = defaultdict(int)
    for index, row in enumerate(rows):
        path = f"portable.population.rows[{index}]"
        f.closed(row, path, (
            "context_target", "independent_unit_id", "requested_context_fields", "row_id", "source_id",
            "task_target",
        ))
        for key in ("independent_unit_id", "row_id", "task_target"):
            f.text(row[key], f"{path}.{key}")
        f.require(row["source_id"] in _CONTEXT, f"{path}.source_id", "unsupported source")
        expected_fields, _ = _CONTEXT[row["source_id"]]
        f.literal(row["requested_context_fields"], f"{path}.requested_context_fields", expected_fields)
        f.require(type(row["context_target"]) is dict, f"{path}.context_target", "must be an object")
        row_ids.append(row["row_id"])
        unit_ids.append(row["independent_unit_id"])
        counts[row["source_id"]] += 1
    f.require(len(set(row_ids)) == len(row_ids), "portable.population.rows", "row ids must be unique")
    f.require(len(set(unit_ids)) == len(unit_ids), "portable.population.rows", "independent units must be unique")
    f.literal(dict(sorted(counts.items())), "portable.population.source_counts",
              {"busbra": 128, "pathmnist": 128})
    return rows


def verify_portable_evidence_bundle(root: Path, retention: dict) -> dict:
    """Verify a portable response-screen bundle and replay every reported metric.

    The bundle intentionally contains predictions and narrow target metadata only.
    Source images, compiled portfolios, model weights, and adapter payloads are
    forbidden even when a freshly sealed evidence manifest lists them.
    """
    root = Path(root)
    evidence_manifest = evidence.verify_bundle_root(root, retention)
    member_paths = {member["path"] for member in evidence_manifest["members"]}
    forbidden_suffixes = (".bin", ".ckpt", ".npz", ".pt", ".pth", ".safetensors", ".zip")
    for relative in member_paths:
        f.require(not relative.lower().endswith(forbidden_suffixes), "portable.members",
                  f"heavy or source payload {relative!r} is forbidden")

    manifest_path = "config/frozen-manifest.json"
    population_path = "population/development.json"
    f.require({manifest_path, population_path}.issubset(member_paths), "portable.members",
              "frozen manifest and development projection are required")
    manifest_raw = (root / manifest_path).read_bytes()
    manifest = validate_manifest(canonical.loads(manifest_raw))
    manifest_sha256 = canonical.raw_digest(manifest_raw)
    rows = _validate_development_projection(_portable_json(root, population_path), manifest["screen_id"])

    expected_conditions = conditions(manifest)
    portfolio_sha256 = None
    candidate_predictions = {
        candidate["candidate_id"]: {"base": None, "profiles": {"dual": {}, "task_only": {}}}
        for candidate in manifest["candidates"]
    }
    for index, expected_condition in enumerate(expected_conditions):
        result_path = f"results/condition-{index}/result.json"
        reload_path = f"results/condition-{index}/reload-result.json"
        f.require({result_path, reload_path}.issubset(member_paths), "portable.members",
                  f"condition {index} result and reload result are required")
        result = _portable_json(root, result_path)
        reload = _portable_json(root, reload_path)
        expected_candidate = candidate_by_id(manifest, expected_condition["candidate_id"])
        f.literal(result.get("condition"), f"portable.condition[{index}].condition", expected_condition)
        f.literal(result.get("candidate"), f"portable.condition[{index}].candidate", expected_candidate)
        f.literal(result.get("status"), f"portable.condition[{index}].status", "passed")
        f.literal(result.get("terminal_stage"), f"portable.condition[{index}].terminal_stage", "completed")
        f.literal(result.get("manifest_sha256"), f"portable.condition[{index}].manifest_sha256", manifest_sha256)
        f.digest(result.get("portfolio_sha256"), f"portable.condition[{index}].portfolio_sha256")
        if portfolio_sha256 is None:
            portfolio_sha256 = result["portfolio_sha256"]
        else:
            f.literal(result["portfolio_sha256"], f"portable.condition[{index}].portfolio_sha256",
                      portfolio_sha256)
        expected_updates = 0 if expected_condition["profile"] == "base" else 1024
        f.literal(result.get("optimizer_updates"), f"portable.condition[{index}].optimizer_updates",
                  expected_updates)
        inventory = result.get("adapter_inventory")
        f.require(type(inventory) is list, f"portable.condition[{index}].adapter_inventory", "must be an array")
        f.require((not inventory) if expected_updates == 0 else bool(inventory),
                  f"portable.condition[{index}].adapter_inventory", "does not match base/adapted condition")
        for key in ("mmbu_public_content_used", "promotion_eligible", "source_admission_complete"):
            f.literal(result.get(key), f"portable.condition[{index}].{key}", False)
        f.literal(result.get("reload_prediction_match"),
                  f"portable.condition[{index}].reload_prediction_match", True)

        predictions = result.get("development_predictions")
        f.require(type(predictions) is list, f"portable.condition[{index}].development_predictions",
                  "must be an array")
        replayed_metrics = biomedical_lane1.score_predictions(rows, predictions)
        f.literal(result.get("development_metrics"), f"portable.condition[{index}].development_metrics",
                  replayed_metrics)
        f.literal(reload.get("schema_id"), f"portable.condition[{index}].reload.schema_id",
                  "mmbu.biomedical.replicated_response_reload")
        f.literal(reload.get("schema_version"), f"portable.condition[{index}].reload.schema_version", 1)
        f.literal(reload.get("candidate_id"), f"portable.condition[{index}].reload.candidate_id",
                  expected_condition["candidate_id"])
        f.literal(reload.get("condition_id"), f"portable.condition[{index}].reload.condition_id",
                  expected_condition["condition_id"])
        f.literal(reload.get("network_disabled"), f"portable.condition[{index}].reload.network_disabled", True)
        f.literal(reload.get("predictions"), f"portable.condition[{index}].reload.predictions", predictions)
        f.literal(reload.get("metrics"), f"portable.condition[{index}].reload.metrics", replayed_metrics)

        target = candidate_predictions[expected_condition["candidate_id"]]
        if expected_condition["profile"] == "base":
            target["base"] = predictions
        else:
            target["profiles"][expected_condition["profile"]][str(expected_condition["training_seed"])] = predictions

    analysis_path = "analysis/post-output-bootstrap.json"
    f.require(analysis_path in member_paths, "portable.members", "post-output analysis is required")
    analysis = _portable_json(root, analysis_path)
    f.require(type(analysis) is dict, "portable.analysis", "must be an object")
    required_analysis_keys = {"bootstrap", "candidates", "inference", "promotion_eligible"}
    f.require(required_analysis_keys.issubset(analysis), "portable.analysis", "is missing required fields")
    f.require(set(analysis).issubset(required_analysis_keys | {"analysis_commit", "source_result_root"}),
              "portable.analysis", "contains unknown fields")
    f.literal(analysis["inference"], "portable.analysis.inference",
              "post_output_exploratory_fixed_development_population")
    f.literal(analysis["promotion_eligible"], "portable.analysis.promotion_eligible", False)
    bootstrap = f.closed(analysis["bootstrap"], "portable.analysis.bootstrap", ("confidence", "iterations", "seed"))
    f.integer(bootstrap["iterations"], "portable.analysis.bootstrap.iterations", minimum=1)
    f.integer(bootstrap["seed"], "portable.analysis.bootstrap.seed", minimum=0)
    f.require(type(bootstrap["confidence"]) in (int, float) and not isinstance(bootstrap["confidence"], bool)
              and 0 < bootstrap["confidence"] < 1, "portable.analysis.bootstrap.confidence",
              "must be between zero and one")
    f.require(type(analysis["candidates"]) is dict, "portable.analysis.candidates", "must be an object")
    f.literal(set(analysis["candidates"]), "portable.analysis.candidates.keys", set(candidate_predictions))
    for candidate_id, stored in candidate_predictions.items():
        f.require(stored["base"] is not None, f"portable.analysis.{candidate_id}.base", "is required")
        replayed = analyze_candidate(
            rows, stored["base"], stored["profiles"], iterations=bootstrap["iterations"],
            bootstrap_seed=bootstrap["seed"], confidence=bootstrap["confidence"],
        )
        f.literal(analysis["candidates"][candidate_id], f"portable.analysis.candidates.{candidate_id}", replayed)

    return {
        "analysis_replayed": True,
        "all_metrics_replayed": True,
        "evidence_root_sha256": retention["root_sha256"],
        "promotion_eligible": False,
        "verified_conditions": len(expected_conditions),
        "verified_development_rows": len(rows),
    }


__all__ = [
    "analyze_candidate", "candidate_by_id", "condition_by_index", "conditions", "grade_task_rows", "load_manifest",
    "official_context_row", "paired_seed_mean_task_bootstrap", "validate_manifest",
    "verify_portable_evidence_bundle",
]
