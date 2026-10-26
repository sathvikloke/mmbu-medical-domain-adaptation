"""Pure planning and scoring primitives for the external biomedical Lane 1 run."""

from __future__ import annotations

from fractions import Fraction
import hashlib
import json
import re
from typing import Any

from mmbu_phase1 import official_context, rational
from mmbu_phase1.fields import ContractViolation, require


_SOURCES = ("busbra", "pathmnist")
_SPLITS = ("train", "development", "confirmation")
_ANSWER_EDGE = re.compile(r"^[\s\"'`*_:#-]+|[\s\"'`*_.:;!?,#-]+$")


def _row_key(row: dict) -> bytes:
    return row["row_id"].encode("utf-8")


def select_rows(
    rows: list[dict], *, split: str, per_source: int, seed: int, allow_confirmation: bool = False,
) -> list[dict]:
    """Select one deterministic record per independent unit, balanced by source."""
    require(split in _SPLITS, "selection.split", "unsupported split")
    require(split != "confirmation" or allow_confirmation,
            "selection.split", "confirmation is sealed until explicitly opened")
    require(type(per_source) is int and per_source > 0, "selection.per_source", "must be a positive integer")
    require(type(seed) is int and seed >= 0, "selection.seed", "must be a nonnegative integer")
    selected = []
    for source in _SOURCES:
        candidates = [row for row in rows if row.get("source_id") == source and row.get("split") == split]
        by_unit: dict[str, dict] = {}
        for row in sorted(candidates, key=_row_key):
            unit = row.get("independent_unit_id")
            require(type(unit) is str and bool(unit), f"selection.{source}.independent_unit_id", "must be nonempty")
            by_unit.setdefault(unit, row)
        require(len(by_unit) >= per_source, f"selection.{source}", "does not contain enough independent units")
        ranked = sorted(
            by_unit.values(),
            key=lambda row: (
                hashlib.sha256(f"{seed}:{row['independent_unit_id']}".encode("utf-8")).digest(),
                _row_key(row),
            ),
        )
        selected.extend(ranked[:per_source])
    return sorted(selected, key=lambda row: (
        hashlib.sha256(f"{seed}:{row['independent_unit_id']}".encode("utf-8")).digest(),
        _row_key(row),
    ))


def training_views(row: dict, mode: str) -> tuple[tuple[str, str, str, dict], ...]:
    """Return endpoint, prompt, target, and exact unit mass for one optimizer unit."""
    require(mode in {"task", "dual"}, "training.mode", "must be task or dual")
    task = ("task", row["task_prompt"], row["task_target"], rational.to_wire(Fraction(1)))
    if mode == "task" or row.get("context_target") is None:
        return (task,)
    require(type(row.get("context_prompt")) is str and bool(row["context_prompt"]),
            "training.context_prompt", "applicable context requires a prompt")
    require(type(row.get("context_target_text")) is str and bool(row["context_target_text"]),
            "training.context_target_text", "applicable context requires serialized target")
    return (
        ("task", row["task_prompt"], row["task_target"], rational.to_wire(Fraction(3, 4))),
        ("context", row["context_prompt"], row["context_target_text"], rational.to_wire(Fraction(1, 4))),
    )


def normalize_answer(value: Any) -> str:
    if type(value) is not str:
        return ""
    result = value.strip().lower()
    if result.startswith("answer:"):
        result = result[len("answer:"):].strip()
    previous = None
    while result != previous:
        previous = result
        result = _ANSWER_EDGE.sub("", result)
    return " ".join(result.split())


def _box(value: Any) -> tuple[int, int, int, int] | None:
    if type(value) is not list or len(value) != 4 or any(type(item) is not int for item in value):
        return None
    x, y, width, height = value
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        return None
    return x, y, width, height


def _iou(left: tuple[int, int, int, int], right: tuple[int, int, int, int]) -> Fraction:
    lx, ly, lw, lh = left
    rx, ry, rw, rh = right
    intersection_width = max(0, min(lx + lw, rx + rw) - max(lx, rx))
    intersection_height = max(0, min(ly + lh, ry + rh) - max(ly, ry))
    intersection = intersection_width * intersection_height
    union = lw * lh + rw * rh - intersection
    return Fraction(intersection, union) if union else Fraction(0)


def _context_score(raw: Any, target: dict) -> Fraction:
    if type(raw) is not str:
        return Fraction(0)
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return Fraction(0)
    if type(value) is not dict or set(value) != {"bbox_xywh", "birads", "image_size", "side"}:
        return Fraction(0)
    predicted_box = _box(value["bbox_xywh"])
    target_box = _box(target["bbox_xywh"])
    if predicted_box is None or target_box is None or value["image_size"] != target["image_size"]:
        return Fraction(0)
    return (
        Fraction(value["birads"] == target["birads"])
        + Fraction(value["side"] == target["side"])
        + _iou(predicted_box, target_box)
    ) / 3


def score_predictions(rows: list[dict], predictions: list[dict]) -> dict:
    """Score strict answer and source-supported context endpoints without silent repair."""
    require(len(rows) == len(predictions), "predictions", "must align one-to-one with rows")
    answer_by_source: dict[str, Fraction] = {}
    context_by_source: dict[str, Fraction] = {}
    context_counts: dict[str, int] = {}
    for index, (row, prediction) in enumerate(zip(rows, predictions)):
        require(prediction.get("row_id") == row.get("row_id"), f"predictions[{index}].row_id", "does not align")
        source = row["source_id"]
        require(source in _SOURCES, f"rows[{index}].source_id", "unsupported source")
        answer_by_source.setdefault(source, Fraction(0))
        answer_by_source[source] += Fraction(normalize_answer(prediction.get("task")) ==
                                             normalize_answer(row["task_target"]))
        if row.get("context_target") is not None:
            context_by_source.setdefault(source, Fraction(0))
            context_counts[source] = context_counts.get(source, 0) + 1
            if "requested_context_fields" in row:
                result = official_context.score_context_output(
                    prediction.get("context"), row["context_target"], row["requested_context_fields"]
                )
                context_by_source[source] += rational.from_wire(result["score"])
            else:
                context_by_source[source] += _context_score(prediction.get("context"), row["context_target"])
    answer_counts = {source: sum(row["source_id"] == source for row in rows) for source in answer_by_source}
    answer_accuracies = {source: answer_by_source[source] / answer_counts[source] for source in answer_by_source}
    context_scores = {source: context_by_source[source] / context_counts[source] for source in context_by_source}
    answer_macro = sum(answer_accuracies.values(), Fraction(0)) / len(answer_accuracies)
    context_macro = (sum(context_scores.values(), Fraction(0)) / len(context_scores)
                     if context_scores else Fraction(0))
    return {
        "answer_by_source": {key: rational.to_wire(value) for key, value in sorted(answer_accuracies.items())},
        "answer_macro_accuracy": rational.to_wire(answer_macro),
        "context_by_source": {key: rational.to_wire(value) for key, value in sorted(context_scores.items())},
        "context_macro_score": rational.to_wire(context_macro),
        "invalid_or_incomplete_context_is_zero": True,
    }


__all__ = [
    "ContractViolation",
    "normalize_answer",
    "score_predictions",
    "select_rows",
    "training_views",
]
