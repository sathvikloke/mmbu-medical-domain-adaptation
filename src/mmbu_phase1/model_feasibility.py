"""Closed validator for the one-attempt generated-only F0 model screen."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


_SHA = re.compile(r"[0-9a-f]{40}")
_TOP = (
    "authorization", "candidates", "comparison_rules", "fixture", "lora", "resources", "runtime",
    "schema_id", "schema_version", "screen_id",
)
_CANDIDATE = (
    "candidate_id", "expected_parameter_count", "gated", "license_id", "loader_family", "model_id",
    "revision", "track_roles", "trust_remote_code",
)
_EXPECTED = (
    ("f0-qwen35-9b", "Qwen/Qwen3.5-9B", "c202236235762e1c871ad0ccb60c8ee5ba337b9a", 9409813744,
     "qwen3_5", ["track2"]),
    ("f0-qwen3vl-8b", "Qwen/Qwen3-VL-8B-Instruct", "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
     8767123696, "qwen3_vl", ["track2"]),
    ("f0-qwen35-4b", "Qwen/Qwen3.5-4B", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a", 4539265536,
     "qwen3_5", ["track2", "track3"]),
    ("f0-qwen3vl-2b", "Qwen/Qwen3-VL-2B-Instruct", "89644892e4d85e24eaac8bacfd4f463576704203",
     2127532032, "qwen3_vl", ["track3"]),
    ("f0-internvl35-2b", "OpenGVLab/InternVL3_5-2B-HF", "3f301ffcf3dcbb47893afae6650ea3e78d96fb6d",
     2348347392, "internvl3_5", ["track3"]),
)


def validate_manifest(value: Any) -> dict:
    value = f.closed(value, "f0", _TOP)
    f.literal(value["schema_id"], "f0.schema_id", "mmbu.phase1.model_feasibility_screen")
    f.literal(value["schema_version"], "f0.schema_version", 1)
    f.literal(value["screen_id"], "f0.screen_id", "mmbu-f0-2026-10-25")

    authorization = f.closed(value["authorization"], "f0.authorization", (
        "allowed_actions", "biomedical_content_allowed", "mmbu_public_content_allowed", "prohibited_actions",
    ))
    f.literal(authorization["allowed_actions"], "f0.authorization.allowed_actions",
              ["generated_fixture", "load", "forward", "backward", "one_optimizer_step", "save", "offline_reload"])
    f.literal(authorization["biomedical_content_allowed"], "f0.authorization.biomedical_content_allowed", False)
    f.literal(authorization["mmbu_public_content_allowed"], "f0.authorization.mmbu_public_content_allowed", False)
    f.literal(authorization["prohibited_actions"], "f0.authorization.prohibited_actions",
              ["full_training", "model_selection", "multi_seed_campaign", "submission", "upload"])

    resources = f.closed(value["resources"], "f0.resources", (
        "attempts_per_candidate", "automatic_rescue_allowed", "gpu_model", "gpu_seconds_per_candidate",
        "max_concurrent_candidates", "gpus_per_candidate",
    ))
    f.literal(resources["attempts_per_candidate"], "f0.resources.attempts_per_candidate", 1)
    f.literal(resources["automatic_rescue_allowed"], "f0.resources.automatic_rescue_allowed", False)
    f.literal(resources["gpu_model"], "f0.resources.gpu_model", "NVIDIA A100 80GB PCIe")
    f.literal(resources["gpu_seconds_per_candidate"], "f0.resources.gpu_seconds_per_candidate", 3600)
    f.literal(resources["max_concurrent_candidates"], "f0.resources.max_concurrent_candidates", 5)
    f.literal(resources["gpus_per_candidate"], "f0.resources.gpus_per_candidate", 1)

    fixture = f.closed(value["fixture"], "f0.fixture", (
        "channels", "height", "origin", "prompt", "seed", "target", "width",
    ))
    f.literal(fixture["origin"], "f0.fixture.origin", "synthetic_engineering")
    f.literal(fixture["channels"], "f0.fixture.channels", 3)
    f.literal(fixture["height"], "f0.fixture.height", 64)
    f.literal(fixture["width"], "f0.fixture.width", 64)
    f.literal(fixture["seed"], "f0.fixture.seed", 20261025)
    f.literal(fixture["prompt"], "f0.fixture.prompt", "Name the dominant color in this generated image using one word.")
    f.literal(fixture["target"], "f0.fixture.target", " blue")

    lora = f.closed(value["lora"], "f0.lora", (
        "alpha", "dropout", "learning_rate", "optimizer", "rank", "target_suffixes", "update_steps",
        "weight_decay",
    ))
    f.literal(lora, "f0.lora", {
        "alpha": 4, "dropout": 0, "learning_rate": 0.0001, "optimizer": "AdamW", "rank": 2,
        "target_suffixes": ["q_proj", "v_proj"], "update_steps": 1, "weight_decay": 0,
    })

    runtime = f.closed(value["runtime"], "f0.runtime", (
        "attention_implementation", "deterministic_algorithms", "local_files_only", "network_disabled",
        "seed", "torch_dtype",
    ))
    f.literal(runtime, "f0.runtime", {
        "attention_implementation": "sdpa", "deterministic_algorithms": True, "local_files_only": True,
        "network_disabled": True, "seed": 20261025, "torch_dtype": "bfloat16",
    })

    rules = f.closed(value["comparison_rules"], "f0.comparison_rules", (
        "decision_use", "pass_requirements", "quality_outputs_allowed", "rerun_policy",
    ))
    f.literal(rules["decision_use"], "f0.comparison_rules.decision_use", "feasibility_only_no_ranking")
    f.literal(rules["quality_outputs_allowed"], "f0.comparison_rules.quality_outputs_allowed", False)
    f.literal(rules["rerun_policy"], "f0.comparison_rules.rerun_policy", "none_automatic")
    f.literal(rules["pass_requirements"], "f0.comparison_rules.pass_requirements", [
        "exact_snapshot", "offline_load", "finite_forward_loss", "finite_gradients", "one_parameter_update",
        "adapter_save", "fresh_process_offline_reload", "deterministic_prediction_match", "resource_receipt",
    ])

    candidates = f.array(value["candidates"], "f0.candidates", nonempty=True)
    f.literal(len(candidates), "f0.candidates.length", len(_EXPECTED))
    seen = set()
    for index, (candidate, expected) in enumerate(zip(candidates, _EXPECTED)):
        candidate = f.closed(candidate, f"f0.candidates[{index}]", _CANDIDATE)
        identity, model_id, revision, count, family, roles = expected
        f.literal(candidate["candidate_id"], f"f0.candidates[{index}].candidate_id", identity)
        f.literal(candidate["model_id"], f"f0.candidates[{index}].model_id", model_id)
        f.require(type(candidate["revision"]) is str and bool(_SHA.fullmatch(candidate["revision"])),
                  f"f0.candidates[{index}].revision", "must be an exact 40-character lowercase commit")
        f.literal(candidate["revision"], f"f0.candidates[{index}].revision", revision)
        f.literal(candidate["expected_parameter_count"], f"f0.candidates[{index}].expected_parameter_count", count)
        f.literal(candidate["loader_family"], f"f0.candidates[{index}].loader_family", family)
        f.literal(candidate["track_roles"], f"f0.candidates[{index}].track_roles", roles)
        f.literal(candidate["license_id"], f"f0.candidates[{index}].license_id", "Apache-2.0")
        f.literal(candidate["gated"], f"f0.candidates[{index}].gated", False)
        f.literal(candidate["trust_remote_code"], f"f0.candidates[{index}].trust_remote_code", False)
        f.require(model_id not in seen, "f0.candidates", "model IDs must be unique")
        seen.add(model_id)
    return value


def load_manifest(path: Path) -> dict:
    return validate_manifest(canonical.loads(path.read_bytes()))


def candidate_by_index(manifest: dict, index: int) -> dict:
    validate_manifest(manifest)
    f.integer(index, "f0.candidate_index", minimum=0)
    f.require(index < len(manifest["candidates"]), "f0.candidate_index", "out of range")
    return manifest["candidates"][index]


__all__ = ["candidate_by_index", "load_manifest", "validate_manifest"]
