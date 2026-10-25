"""Fail-closed BUSI-WHU held-out confirmation mechanics.

This module is CPU-only and performs validation and exact arithmetic. It has
no data acquisition, model, scheduler, network, or accelerator integration.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import random

from mmbu_phase1 import canonical, rational
from mmbu_phase1.fields import (
    ContractViolation, boolean, closed, fail, integer, literal, require, text, timestamp,
)


SPEC_DIGEST = "a7a074d0acac95da79a6505bc791faf30e48f879218ad0b30027f2b56916c703"
SPEC_KEYS = (
    "authorization", "candidate", "confirmation_id", "gates", "prompts", "resources",
    "schema_id", "schema_version", "source", "statistics", "training",
)


def validate_spec(value: object) -> dict:
    """Validate the one prospectively frozen confirmation protocol exactly."""
    record = closed(value, "heldout_confirmation.spec", SPEC_KEYS)
    try:
        digest = canonical.value_digest(record)
    except (canonical.CanonicalJSONError, TypeError, ValueError) as exc:
        fail("heldout_confirmation.spec", f"is not canonicalizable: {exc}")
    if digest != SPEC_DIGEST:
        fail("heldout_confirmation.spec", "does not match the frozen protocol digest")
    return record


def load_spec(path: Path) -> dict:
    try:
        value = canonical.loads(path.read_bytes())
    except (OSError, canonical.CanonicalJSONError) as exc:
        raise ContractViolation("heldout_confirmation.spec", f"cannot load: {exc}") from None
    return validate_spec(value)


LINEAGE_KEYS = (
    "base_model_id", "base_revision", "expected_parameter_count", "legacy_exploratory_adapter_used",
    "lora_alpha", "lora_dropout", "lora_rank", "lora_target_suffixes", "mmbu_public_content_used",
    "optimizer_updates", "post_admission_retraining", "profile", "runtime_gate_id", "runtime_gate_passed",
    "source_purposes", "training_seed",
)


def validate_checkpoint_lineage(value: object, path: str = "heldout_confirmation.lineage") -> dict:
    """Accept only a newly retrained, fully authorized member of the fixed family."""
    row = closed(value, path, LINEAGE_KEYS)
    expected = {
        "base_model_id": "Qwen/Qwen3.5-9B",
        "base_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "expected_parameter_count": 9409813744,
        "legacy_exploratory_adapter_used": False,
        "lora_alpha": 16,
        "lora_dropout": 0,
        "lora_rank": 8,
        "lora_target_suffixes": ["q_proj", "v_proj"],
        "mmbu_public_content_used": False,
        "optimizer_updates": 1024,
        "post_admission_retraining": True,
        "profile": "dual",
        "runtime_gate_id": "qwen3.5-9b-successor-native-runtime",
        "runtime_gate_passed": True,
        "source_purposes": {"busbra": "train", "pathmnist": "train"},
    }
    for key, expected_value in expected.items():
        literal(row[key], f"{path}.{key}", expected_value)
    require(type(row["training_seed"]) is int and row["training_seed"] in (20261025, 20261026, 20261027),
            f"{path}.training_seed", "must be one of the three frozen non-boolean integer seeds")
    return row


ARTIFACT_KEYS = (
    "created_at", "index_matrix", "index_matrix_digest", "patient_ids", "population_digest",
    "sign_matrix", "sign_matrix_digest",
)
RESULT_ROW_KEYS = (
    "condition_id", "context_field_grades", "output_failed", "patient_id", "record_id", "task_grade",
    "target_label",
)
CONDITIONS = ("base", "seed-20261025", "seed-20261026", "seed-20261027")
SEED_CONDITIONS = CONDITIONS[1:]


def _validate_patient_ids(value: object, path: str = "heldout_confirmation.patient_ids") -> list[str]:
    if type(value) is not list:
        fail(path, "must be an array")
    if len(value) < 60:
        fail(path, "must contain at least 60 independent patients")
    for index, patient_id in enumerate(value):
        text(patient_id, f"{path}[{index}]")
    expected = sorted(set(value), key=lambda item: item.encode("utf-8"))
    require(value == expected, path, "must be unique and sorted by ascending UTF-8 bytes")
    return value


def build_randomization_artifacts(patient_ids: list[str], *, created_at: str) -> dict:
    """Build the frozen patient bootstrap and sign matrices before outputs exist."""
    patient_ids = list(_validate_patient_ids(patient_ids))
    timestamp(created_at, "heldout_confirmation.artifacts.created_at")
    count = len(patient_ids)
    bootstrap = random.Random(20261025)
    signs = random.Random(20261026)
    index_matrix = [[bootstrap.randrange(count) for _ in range(count)] for _ in range(10000)]
    sign_matrix = [[1 if signs.getrandbits(1) else -1 for _ in range(count)] for _ in range(10000)]
    return {
        "created_at": created_at,
        "index_matrix": index_matrix,
        "index_matrix_digest": canonical.value_digest(index_matrix),
        "patient_ids": patient_ids,
        "population_digest": canonical.value_digest(patient_ids),
        "sign_matrix": sign_matrix,
        "sign_matrix_digest": canonical.value_digest(sign_matrix),
    }


def _validate_artifacts(value: object, *, first_output_at: str) -> dict:
    artifact = closed(value, "heldout_confirmation.artifacts", ARTIFACT_KEYS)
    patient_ids = _validate_patient_ids(artifact["patient_ids"], "heldout_confirmation.artifacts.patient_ids")
    created = timestamp(artifact["created_at"], "heldout_confirmation.artifacts.created_at")
    first_output = timestamp(first_output_at, "heldout_confirmation.first_output_at")
    require(created < first_output, "heldout_confirmation.artifacts.created_at",
            "must precede the first model output")
    literal(artifact["population_digest"], "heldout_confirmation.artifacts.population_digest",
            canonical.value_digest(patient_ids))
    count = len(patient_ids)
    index_matrix = artifact["index_matrix"]
    sign_matrix = artifact["sign_matrix"]
    require(type(index_matrix) is list and len(index_matrix) == 10000,
            "heldout_confirmation.artifacts.index_matrix", "must contain exactly 10,000 draws")
    require(type(sign_matrix) is list and len(sign_matrix) == 10000,
            "heldout_confirmation.artifacts.sign_matrix", "must contain exactly 10,000 draws")
    for draw_index, draw in enumerate(index_matrix):
        require(type(draw) is list and len(draw) == count,
                f"heldout_confirmation.artifacts.index_matrix[{draw_index}]", "has the wrong patient count")
        require(all(type(position) is int and 0 <= position < count for position in draw),
                f"heldout_confirmation.artifacts.index_matrix[{draw_index}]", "contains an invalid position")
    for draw_index, draw in enumerate(sign_matrix):
        require(type(draw) is list and len(draw) == count,
                f"heldout_confirmation.artifacts.sign_matrix[{draw_index}]", "has the wrong patient count")
        require(all(type(sign) is int and sign in (-1, 1) for sign in draw),
                f"heldout_confirmation.artifacts.sign_matrix[{draw_index}]", "contains an invalid sign")
    literal(artifact["index_matrix_digest"], "heldout_confirmation.artifacts.index_matrix_digest",
            canonical.value_digest(index_matrix))
    literal(artifact["sign_matrix_digest"], "heldout_confirmation.artifacts.sign_matrix_digest",
            canonical.value_digest(sign_matrix))
    return artifact


def _mean(values: list[Fraction], path: str) -> Fraction:
    require(bool(values), path, "must be nonempty")
    return sum(values, Fraction(0)) / len(values)


def _validate_result_row(value: object, index: int) -> dict:
    path = f"heldout_confirmation.rows[{index}]"
    row = closed(value, path, RESULT_ROW_KEYS)
    literal(row["condition_id"], f"{path}.condition_id", row["condition_id"])
    require(type(row["condition_id"]) is str and row["condition_id"] in CONDITIONS,
            f"{path}.condition_id", "must be one frozen condition")
    text(row["patient_id"], f"{path}.patient_id")
    text(row["record_id"], f"{path}.record_id")
    require(type(row["target_label"]) is str and row["target_label"] in ("benign", "malignant"),
            f"{path}.target_label", "must be benign or malignant")
    failed = boolean(row["output_failed"], f"{path}.output_failed")
    task = rational.from_wire(row["task_grade"], f"{path}.task_grade")
    require(task in (Fraction(0), Fraction(1)), f"{path}.task_grade", "must be exactly 0 or 1")
    grades = closed(row["context_field_grades"], f"{path}.context_field_grades",
                    ("body_part", "medical_domain", "modality"))
    for key in ("body_part", "medical_domain", "modality"):
        grade = integer(grades[key], f"{path}.context_field_grades.{key}", minimum=0, maximum=1)
        require(grade in (0, 1), f"{path}.context_field_grades.{key}", "must be binary")
    if failed:
        require(task == 0 and all(value == 0 for value in grades.values()), path,
                "an output failure must remain in the denominator as all-zero grades")
    return row


def analyze_patient_results(rows: list[dict], artifacts: dict, *, first_output_at: str) -> dict:
    """Compute the frozen exact paired patient analysis from complete condition rows."""
    artifact = _validate_artifacts(artifacts, first_output_at=first_output_at)
    patient_ids = artifact["patient_ids"]
    patient_set = set(patient_ids)
    if type(rows) is not list:
        fail("heldout_confirmation.rows", "must be an array")
    by_condition: dict[str, dict[str, dict[str, dict]]] = {condition: {} for condition in CONDITIONS}
    output_failures = 0
    for index, raw in enumerate(rows):
        row = _validate_result_row(raw, index)
        require(row["patient_id"] in patient_set, f"heldout_confirmation.rows[{index}].patient_id",
                "is not in the locked population")
        condition_records = by_condition[row["condition_id"]].setdefault(row["patient_id"], {})
        require(row["record_id"] not in condition_records, f"heldout_confirmation.rows[{index}].record_id",
                "duplicates a condition record")
        condition_records[row["record_id"]] = row
        output_failures += int(row["output_failed"])

    reference: dict[str, set[str]] = {}
    for patient_id in patient_ids:
        reference[patient_id] = set(by_condition["base"].get(patient_id, {}))
        require(bool(reference[patient_id]), f"heldout_confirmation.population.{patient_id}",
                "has no base records")
        for condition in SEED_CONDITIONS:
            require(set(by_condition[condition].get(patient_id, {})) == reference[patient_id],
                    f"heldout_confirmation.population.{patient_id}.{condition}",
                    "must contain exactly the same record IDs as base")
            for record_id in reference[patient_id]:
                base_label = by_condition["base"][patient_id][record_id]["target_label"]
                literal(by_condition[condition][patient_id][record_id]["target_label"],
                        f"heldout_confirmation.population.{patient_id}.{condition}.{record_id}.target_label",
                        base_label)

    task_patient: dict[str, dict[str, Fraction]] = {condition: {} for condition in CONDITIONS}
    context_patient: dict[str, dict[str, Fraction]] = {condition: {} for condition in CONDITIONS}
    for condition in CONDITIONS:
        for patient_id in patient_ids:
            patient_rows = list(by_condition[condition][patient_id].values())
            task_patient[condition][patient_id] = _mean(
                [rational.from_wire(row["task_grade"]) for row in patient_rows], "task_patient"
            )
            context_patient[condition][patient_id] = _mean([
                Fraction(sum(row["context_field_grades"].values()), 3) for row in patient_rows
            ], "context_patient")

    seed_deltas = {
        condition: _mean([
            task_patient[condition][patient_id] - task_patient["base"][patient_id]
            for patient_id in patient_ids
        ], f"seed_delta.{condition}")
        for condition in SEED_CONDITIONS
    }
    patient_deltas = [
        _mean([task_patient[condition][patient_id] - task_patient["base"][patient_id]
               for condition in SEED_CONDITIONS], f"patient_delta.{patient_id}")
        for patient_id in patient_ids
    ]
    point = _mean(patient_deltas, "point_delta")
    draw_values = [
        _mean([patient_deltas[position] for position in draw], "bootstrap_draw")
        for draw in artifact["index_matrix"]
    ]
    lower = sorted(enumerate(draw_values), key=lambda item: (item[1], item[0]))[999][1]
    null_values = [
        _mean([patient_deltas[index] * sign for index, sign in enumerate(signs)], "sign_draw")
        for signs in artifact["sign_matrix"]
    ]
    sign_p = Fraction(1 + sum(value >= point for value in null_values), 10001)
    condition_task = {
        condition: _mean(list(task_patient[condition].values()), f"condition_task.{condition}")
        for condition in CONDITIONS
    }
    condition_context = {
        condition: _mean(list(context_patient[condition].values()), f"condition_context.{condition}")
        for condition in CONDITIONS
    }
    return {
        "base": {
            "context": rational.to_wire(condition_context["base"]),
            "task": rational.to_wire(condition_task["base"]),
        },
        "lower_bound": rational.to_wire(lower),
        "output_failure_count": output_failures,
        "patient_count": len(patient_ids),
        "point_delta": rational.to_wire(point),
        "seed_deltas": {key: rational.to_wire(value) for key, value in seed_deltas.items()},
        "seed_mean": {
            "context": rational.to_wire(_mean([condition_context[key] for key in SEED_CONDITIONS], "seed_context")),
            "task": rational.to_wire(_mean([condition_task[key] for key in SEED_CONDITIONS], "seed_task")),
        },
        "sign_randomization_p": rational.to_wire(sign_p),
    }


__all__ = [
    "SPEC_DIGEST", "analyze_patient_results", "build_randomization_artifacts", "load_spec",
    "validate_checkpoint_lineage", "validate_spec",
]

