"""Closed contracts for the Competition Lane 1 synthetic trainer.

This module accepts engineering-only fixtures. It grants no authority to open
biomedical data, load model weights, or execute a real experiment.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from mmbu_phase1 import canonical, competition_manifest_v2, rational
from mmbu_phase1 import lane1_synthetic
from mmbu_phase1.fields import (
    array,
    boolean,
    closed,
    digest,
    fail,
    integer,
    literal,
    one_of,
    require,
    string_set,
    text,
)


ARM_IDS = (
    "recipe_arch::B0::base",
    "recipe_arch::B1-L::profile::task_only",
    "recipe_arch::B1-L::profile::dual",
    "recipe_arch::B2-P::profile::task_only",
    "recipe_arch::B2-P::profile::dual",
)
ARCHITECTURES = ("recipe_arch::B0", "recipe_arch::B1-L", "recipe_arch::B2-P")
FIXTURE_KEYS = (
    "biomedical_content",
    "evaluation_rows",
    "fixture_id",
    "mmbu_public_content",
    "origin_class",
    "schema_id",
    "schema_version",
    "train_rows",
)
ROW_KEYS = ("context_target", "feature", "independent_unit_id", "row_id", "task_target")
CONFIG_KEYS = (
    "allowed_fixture_digest",
    "checkpoint_after_updates",
    "epochs",
    "learning_rate",
    "schema_id",
    "schema_version",
    "seed",
    "trainable_names_by_architecture",
)


def _binary(value: Any, path: str) -> int:
    return integer(value, path, minimum=0, maximum=1)


def _validate_row(value: Any, path: str, *, training: bool) -> dict:
    row = closed(value, path, ROW_KEYS)
    text(row["row_id"], f"{path}.row_id")
    text(row["independent_unit_id"], f"{path}.independent_unit_id")
    rational.from_wire(row["feature"], f"{path}.feature")
    _binary(row["task_target"], f"{path}.task_target")
    context = row["context_target"]
    if context is None:
        require(not training, f"{path}.context_target", "training context targets must be applicable")
    else:
        _binary(context, f"{path}.context_target")
    return row


def validate_fixture(value: Any) -> dict:
    """Validate one closed synthetic fixture declaration."""
    fixture = closed(value, "fixture", FIXTURE_KEYS)
    literal(fixture["schema_id"], "fixture.schema_id", "mmbu.synthetic.lane1_fixture")
    literal(fixture["schema_version"], "fixture.schema_version", 1)
    text(fixture["fixture_id"], "fixture.fixture_id")
    literal(fixture["origin_class"], "fixture.origin_class", "synthetic_engineering")
    literal(boolean(fixture["biomedical_content"], "fixture.biomedical_content"),
            "fixture.biomedical_content", False)
    literal(boolean(fixture["mmbu_public_content"], "fixture.mmbu_public_content"),
            "fixture.mmbu_public_content", False)
    train = array(fixture["train_rows"], "fixture.train_rows", nonempty=True)
    evaluation = array(fixture["evaluation_rows"], "fixture.evaluation_rows", nonempty=True)
    for index, item in enumerate(train):
        _validate_row(item, f"fixture.train_rows[{index}]", training=True)
    for index, item in enumerate(evaluation):
        _validate_row(item, f"fixture.evaluation_rows[{index}]", training=False)
    require(any(item["context_target"] is not None for item in evaluation),
            "fixture.evaluation_rows", "must contain at least one applicable context target")
    rows = train + evaluation
    for key in ("row_id", "independent_unit_id"):
        identifiers = [item[key] for item in rows]
        require(len(identifiers) == len(set(identifiers)), f"fixture.{key}",
                "must be unique across training and evaluation splits")
    return fixture


def validate_config(value: Any, fixture: Any) -> dict:
    """Validate engineering controls and bind them to exact fixture bytes."""
    fixture = validate_fixture(fixture)
    config = closed(value, "config", CONFIG_KEYS)
    literal(config["schema_id"], "config.schema_id", "mmbu.synthetic.lane1_config")
    literal(config["schema_version"], "config.schema_version", 1)
    integer(config["seed"], "config.seed", minimum=0)
    epochs = integer(config["epochs"], "config.epochs", minimum=1)
    learning_rate = rational.from_wire(config["learning_rate"], "config.learning_rate")
    require(0 < learning_rate <= Fraction(1), "config.learning_rate", "must be in (0, 1]")
    expected_digest = digest(config["allowed_fixture_digest"], "config.allowed_fixture_digest")
    require(expected_digest == canonical.value_digest(fixture), "config.allowed_fixture_digest",
            "does not match the canonical fixture digest")
    checkpoint = integer(config["checkpoint_after_updates"], "config.checkpoint_after_updates", minimum=1)
    total_updates = epochs * len(fixture["train_rows"])
    require(checkpoint < total_updates, "config.checkpoint_after_updates",
            "must be strictly before the final optimizer update")
    scopes = closed(config["trainable_names_by_architecture"],
                    "config.trainable_names_by_architecture", ARCHITECTURES)
    for architecture in ARCHITECTURES:
        string_set(scopes[architecture], f"config.trainable_names_by_architecture.{architecture}")
    require(scopes["recipe_arch::B0"] == [], "config.trainable_names_by_architecture.recipe_arch::B0",
            "B0 must have no trainable parameters")
    b1 = set(scopes["recipe_arch::B1-L"])
    b2 = set(scopes["recipe_arch::B2-P"])
    require(bool(b1), "config.trainable_names_by_architecture.recipe_arch::B1-L", "must be nonempty")
    require(b1 < b2, "config.trainable_names_by_architecture.recipe_arch::B2-P",
            "must be a proper superset of B1-L")
    return config


def _profile_modes(manifest: dict) -> dict[str, str]:
    result = {}
    for index, profile in enumerate(manifest["training_contract"]["objective_profiles"]):
        context = rational.from_wire(
            profile["context_unit_share"],
            f"manifest.training_contract.objective_profiles[{index}].context_unit_share",
        )
        result[profile["profile_id"]] = "task" if context == 0 else "dual"
    return result


def resolve_arms(manifest: Any) -> tuple[dict, ...]:
    """Validate and derive the exact authorized five-arm execution universe."""
    competition_manifest_v2.validate_manifest(manifest)
    profiles = _profile_modes(manifest)
    enabled = [item for item in manifest["candidate_universe"] if item["enabled"]]
    require(tuple(item["candidate_id"] for item in enabled) == ARM_IDS,
            "manifest.candidate_universe", "must equal the exact Lane 1 five-arm universe in canonical order")
    arms = []
    for item in enabled:
        architecture = item["architecture_id"]
        profile_id = item["objective_profile_id"]
        mode = "base" if architecture == "recipe_arch::B0" else profiles[profile_id]
        arms.append({
            "architecture_id": architecture,
            "candidate_id": item["candidate_id"],
            "objective_mode": mode,
            "objective_profile_id": profile_id,
        })
    return tuple(arms)


def _empty_arm_result(arm: dict, status: str) -> dict:
    return {
        "architecture_id": arm["architecture_id"],
        "candidate_id": arm["candidate_id"],
        "context_accuracy": None,
        "failure_message": None,
        "failure_stage": None,
        "objective_profile_id": arm["objective_profile_id"],
        "optimizer_updates": 0,
        "ordered_unit_digest": None,
        "reload_prediction_match": None,
        "resume_prediction_match": None,
        "resume_state_match": None,
        "score_proxy": None,
        "status": status,
        "task_accuracy": None,
        "trainable_parameter_names": None,
    }


def _ordered_training_rows(fixture: dict, config: dict) -> tuple[list[dict], list[str]]:
    rows = []
    units = []
    for _epoch in range(config["epochs"]):
        for row in fixture["train_rows"]:
            rows.append(row)
            units.append(row["independent_unit_id"])
    return rows, units


def _run_matched_arm(arm: dict, fixture: dict, config: dict, backend_factory) -> dict:
    row = _empty_arm_result(arm, "passed")
    backend = backend_factory()
    backend.initialize(base_state=lane1_synthetic.BASE_STATE_BYTES, arm=arm, seed=config["seed"])
    if backend.base_state_bytes() != lane1_synthetic.BASE_STATE_BYTES:
        fail("lane1.backend.base_state", "backend did not preserve the common base bytes")
    actual_scope = tuple(backend.trainable_parameter_names())
    expected_scope = tuple(config["trainable_names_by_architecture"][arm["architecture_id"]])
    if actual_scope != expected_scope:
        fail("lane1.backend.trainable_parameter_names", "backend scope differs from the bound engineering config")
    row["trainable_parameter_names"] = list(actual_scope)
    training_rows, units = _ordered_training_rows(fixture, config)
    row["ordered_unit_digest"] = canonical.value_digest(units)
    if arm["objective_mode"] == "base":
        return row
    learning_rate = rational.from_wire(config["learning_rate"], "config.learning_rate")
    for item in training_rows:
        try:
            backend.step(item, objective_mode=arm["objective_mode"], learning_rate=learning_rate)
        except Exception as exc:
            row["status"] = "failed"
            row["failure_stage"] = "update"
            row["failure_message"] = str(exc)
            return row
        row["optimizer_updates"] += 1
    return row


def run_lane1(manifest: Any, fixture: Any, config: Any, *, backend_factory=lane1_synthetic.SyntheticBackend) -> dict:
    """Run the exact five-arm engineering lane and preserve a closed failure population."""
    arms = resolve_arms(manifest)
    fixture = validate_fixture(fixture)
    config = validate_config(config, fixture)
    arm_results = []
    stopped = False
    for arm in arms:
        if stopped:
            arm_results.append(_empty_arm_result(arm, "not_run"))
            continue
        try:
            result = _run_matched_arm(arm, fixture, config, backend_factory)
        except Exception as exc:
            result = _empty_arm_result(arm, "failed")
            result["failure_stage"] = "pre_update"
            result["failure_message"] = str(exc)
        arm_results.append(result)
        stopped = result["status"] != "passed"
    return {
        "arm_results": arm_results,
        "comparisons": [],
        "config_digest": canonical.value_digest(config),
        "evidence_class": "synthetic_engineering_only",
        "fixture_digest": canonical.value_digest(fixture),
        "limitations": [
            "Synthetic engineering evidence only; no biomedical performance was measured.",
            "No model weights, GPU, HPC, MMBU public examples, upload, or submission were used.",
        ],
        "manifest_digest": manifest["canonical_digest"],
        "schema_id": "mmbu.synthetic.lane1_result",
        "schema_version": 1,
        "scientific_selection_output_observed": False,
    }


__all__ = [
    "ARM_IDS",
    "ContractViolation",
    "resolve_arms",
    "run_lane1",
    "validate_config",
    "validate_fixture",
]
