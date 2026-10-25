"""Closed contracts for the Competition Lane 1 synthetic trainer.

This module accepts engineering-only fixtures. It grants no authority to open
biomedical data, load model weights, or execute a real experiment.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from mmbu_phase1 import canonical, competition_manifest_v2, rational, track2_score
from mmbu_phase1 import lane1_synthetic
from mmbu_phase1.fields import (
    ContractViolation,
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
TRUSTED_FIXTURE_DIGESTS = {
    "lane1-fixture-v1": "0a669da9edbfae0c047b326ceead8f70ae1b5ed906f6732c8877b46b7eb37eb2",
    "lane1-runtime-failure-v1": "235d2af7d2b343df0dc42482c6f6159adefa2667b761485e119834818e240c29",
}
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
    trusted_digest = TRUSTED_FIXTURE_DIGESTS.get(fixture["fixture_id"])
    require(trusted_digest == expected_digest, "config.allowed_fixture_digest",
            "fixture is not present in the repository-reviewed synthetic allowlist")
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


def _profile_contracts(manifest: dict) -> dict[str, dict]:
    result = {}
    for index, profile in enumerate(manifest["training_contract"]["objective_profiles"]):
        task = rational.from_wire(
            profile["task_unit_share"],
            f"manifest.training_contract.objective_profiles[{index}].task_unit_share",
        )
        context = rational.from_wire(
            profile["context_unit_share"],
            f"manifest.training_contract.objective_profiles[{index}].context_unit_share",
        )
        unit = rational.from_wire(
            profile["unit_total_mass"],
            f"manifest.training_contract.objective_profiles[{index}].unit_total_mass",
        )
        result[profile["profile_id"]] = {
            "context_unit_share": rational.to_wire(context),
            "objective_mode": "task" if context == 0 else "dual",
            "task_unit_share": rational.to_wire(task),
            "unit_total_mass": rational.to_wire(unit),
        }
    return result


def resolve_arms(manifest: Any) -> tuple[dict, ...]:
    """Validate and derive the exact authorized five-arm execution universe."""
    competition_manifest_v2.validate_manifest(manifest)
    profiles = _profile_contracts(manifest)
    enabled = [item for item in manifest["candidate_universe"] if item["enabled"]]
    require(tuple(item["candidate_id"] for item in enabled) == ARM_IDS,
            "manifest.candidate_universe", "must equal the exact Lane 1 five-arm universe in canonical order")
    arms = []
    for item in enabled:
        architecture = item["architecture_id"]
        profile_id = item["objective_profile_id"]
        profile = ({
            "context_unit_share": rational.to_wire(0),
            "objective_mode": "base",
            "task_unit_share": rational.to_wire(1),
            "unit_total_mass": rational.to_wire(1),
        } if architecture == "recipe_arch::B0" else profiles[profile_id])
        arms.append({
            "architecture_id": architecture,
            "candidate_id": item["candidate_id"],
            "context_unit_share": profile["context_unit_share"],
            "objective_mode": profile["objective_mode"],
            "objective_profile_id": profile_id,
            "task_unit_share": profile["task_unit_share"],
            "unit_total_mass": profile["unit_total_mass"],
        })
    return tuple(arms)


def _empty_arm_result(arm: dict, status: str) -> dict:
    return {
        "architecture_id": arm["architecture_id"],
        "candidate_id": arm["candidate_id"],
        "context_accuracy": None,
        "failure_message": None,
        "failure_stage": None,
        "final_state_digest": None,
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


class _RuntimeStageError(RuntimeError):
    def __init__(self, stage: str, cause: Exception):
        super().__init__(str(cause))
        self.stage = stage


def _at(stage: str, operation):
    try:
        return operation()
    except Exception as exc:
        raise _RuntimeStageError(stage, exc) from exc


def _initialize_backend(backend_factory, arm: dict, config: dict):
    backend = backend_factory()
    _at("initialize", lambda: backend.initialize(
        base_state=lane1_synthetic.BASE_STATE_BYTES, arm=arm, seed=config["seed"]
    ))
    preserved = _at("base_state", backend.base_state_bytes)
    if preserved != lane1_synthetic.BASE_STATE_BYTES:
        raise _RuntimeStageError("base_state", ValueError("backend did not preserve the common base bytes"))
    actual_scope = tuple(_at("scope", backend.trainable_parameter_names))
    expected_scope = tuple(config["trainable_names_by_architecture"][arm["architecture_id"]])
    if actual_scope != expected_scope:
        raise _RuntimeStageError("scope", ValueError("backend scope differs from the bound engineering config"))
    return backend, actual_scope


def _predictions(backend, fixture: dict) -> tuple[tuple[int, int | None], ...]:
    return tuple(backend.predict(item) for item in fixture["evaluation_rows"])


def _metrics(predictions: tuple[tuple[int, int | None], ...], fixture: dict) -> tuple[Fraction, Fraction]:
    evaluation = fixture["evaluation_rows"]
    task_correct = sum(prediction[0] == item["task_target"] for prediction, item in zip(predictions, evaluation))
    applicable = [(prediction, item) for prediction, item in zip(predictions, evaluation)
                  if item["context_target"] is not None]
    context_correct = sum(prediction[1] == item["context_target"] for prediction, item in applicable)
    return Fraction(task_correct, len(evaluation)), Fraction(context_correct, len(applicable))


def _apply_updates(backend, rows: list[dict], mode: str, learning_rate: Fraction, *, stage: str) -> None:
    for item in rows:
        _at(stage, lambda item=item: backend.step(
            item, objective_mode=mode, learning_rate=learning_rate
        ))


def _run_matched_arm(arm: dict, fixture: dict, config: dict, backend_factory) -> dict:
    row = _empty_arm_result(arm, "passed")
    training_rows, units = _ordered_training_rows(fixture, config)
    row["ordered_unit_digest"] = canonical.value_digest(units)
    learning_rate = rational.from_wire(config["learning_rate"], "config.learning_rate")
    try:
        backend, actual_scope = _initialize_backend(backend_factory, arm, config)
        row["trainable_parameter_names"] = list(actual_scope)
        if arm["objective_mode"] != "base":
            _apply_updates(backend, training_rows, arm["objective_mode"], learning_rate, stage="update")
            row["optimizer_updates"] = len(training_rows)

            boundary = config["checkpoint_after_updates"]
            prefix_backend, _ = _initialize_backend(backend_factory, arm, config)
            _apply_updates(prefix_backend, training_rows[:boundary], arm["objective_mode"], learning_rate,
                           stage="checkpoint_prefix_update")
            checkpoint = _at("checkpoint_dump", prefix_backend.dump_state)
            resumed_backend, _ = _initialize_backend(backend_factory, arm, config)
            _at("checkpoint_reload", lambda: resumed_backend.load_state(checkpoint))
            _apply_updates(resumed_backend, training_rows[boundary:], arm["objective_mode"], learning_rate,
                           stage="checkpoint_suffix_update")
            full_state = _at("final_state_dump", backend.dump_state)
            resumed_state = _at("resumed_state_dump", resumed_backend.dump_state)
            row["resume_state_match"] = full_state == resumed_state
            if not row["resume_state_match"]:
                raise _RuntimeStageError("resume_state", ValueError("resumed state differs from uninterrupted state"))
            full_predictions = _at("evaluation", lambda: _predictions(backend, fixture))
            resumed_predictions = _at("resume_prediction", lambda: _predictions(resumed_backend, fixture))
            row["resume_prediction_match"] = full_predictions == resumed_predictions
            if not row["resume_prediction_match"]:
                raise _RuntimeStageError(
                    "resume_prediction", ValueError("resumed predictions differ from uninterrupted predictions")
                )
        else:
            full_predictions = _at("evaluation", lambda: _predictions(backend, fixture))
            full_state = _at("final_state_dump", backend.dump_state)

        row["final_state_digest"] = canonical.raw_digest(full_state)

        exported = _at("export", backend.export)
        reload_backend, _ = _initialize_backend(backend_factory, arm, config)
        _at("export_reload", lambda: reload_backend.load_export(exported))
        reload_predictions = _at("export_reload_prediction", lambda: _predictions(reload_backend, fixture))
        row["reload_prediction_match"] = full_predictions == reload_predictions
        if not row["reload_prediction_match"]:
            raise _RuntimeStageError(
                "export_reload_prediction", ValueError("reloaded predictions differ from final predictions")
            )
        task, context = _metrics(full_predictions, fixture)
        row["task_accuracy"] = rational.to_wire(task)
        row["context_accuracy"] = rational.to_wire(context)
    except _RuntimeStageError as exc:
        row["status"] = "failed"
        row["failure_stage"] = exc.stage
        row["failure_message"] = str(exc)
    return row


def _add_scores_and_comparisons(result: dict, manifest: dict) -> None:
    by_id = {item["candidate_id"]: item for item in result["arm_results"]}
    base = by_id[ARM_IDS[0]]
    if base["status"] == "passed":
        base_task = rational.from_wire(base["task_accuracy"], "result.arm_results.B0.task_accuracy")
        for item in result["arm_results"]:
            if item["status"] == "passed":
                task = rational.from_wire(item["task_accuracy"], "result.arm_results.task_accuracy")
                context = rational.from_wire(item["context_accuracy"], "result.arm_results.context_accuracy")
                item["score_proxy"] = rational.to_wire(track2_score.score_proxy(task, context, base_task))
    comparisons = []
    for candidate_id, comparator_ids in competition_manifest_v2.expected_comparator_map(manifest).items():
        for comparator_id in comparator_ids:
            candidate = by_id[candidate_id]
            comparator = by_id[comparator_id]
            comparison = {
                "candidate_id": candidate_id,
                "comparator_id": comparator_id,
                "context_delta": None,
                "score_proxy_delta": None,
                "status": "unavailable",
                "task_delta": None,
            }
            if candidate["status"] == comparator["status"] == "passed":
                comparison["status"] = "available"
                for result_key, metric_key in (
                    ("task_delta", "task_accuracy"),
                    ("context_delta", "context_accuracy"),
                    ("score_proxy_delta", "score_proxy"),
                ):
                    left = rational.from_wire(candidate[metric_key], f"result.{candidate_id}.{metric_key}")
                    right = rational.from_wire(comparator[metric_key], f"result.{comparator_id}.{metric_key}")
                    comparison[result_key] = rational.to_wire(left - right)
            comparisons.append(comparison)
    result["comparisons"] = comparisons


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
            result["failure_stage"] = "runtime_internal"
            result["failure_message"] = str(exc)
        arm_results.append(result)
        stopped = result["status"] != "passed"
    result = {
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
    _add_scores_and_comparisons(result, manifest)
    return result


__all__ = [
    "ARM_IDS",
    "ContractViolation",
    "resolve_arms",
    "run_lane1",
    "validate_config",
    "validate_fixture",
]
