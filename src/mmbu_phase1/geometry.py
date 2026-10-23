"""Original-pixel ``[x, y, width, height]`` geometry with exact rational IoU.

Boxes are never clipped, rounded, swapped, reordered, normalized, or repaired.
Matching is deterministic: ``single`` compares one pair, ``any_one`` records the
best target (lowest index on ties), and ``all_targets`` requires a perfect
one-to-one matching over threshold-qualified edges that maximizes exact total
IoU, breaking ties by the lexicographically smallest (prediction, target)
vector.  Geometry is a projection of the raw, parsed, and validated layers; the
judge layer has no input here.
"""

from __future__ import annotations

from fractions import Fraction
import math
from typing import Any

from mmbu_phase1 import canonical, fields as f, rational

POLICIES = ("single", "all_targets", "any_one", "not_applicable")
REASON_CODES = (
    "passed",
    "below_threshold",
    "runtime_failure",
    "parse_failure",
    "validation_failure",
    "invalid_prediction_box",
    "prediction_count_mismatch",
)
SYNTHETIC_THRESHOLD = Fraction(1, 2)


def _is_number(value: Any) -> bool:
    return type(value) in (int, float) and (type(value) is int or math.isfinite(value))


def exact_box_array(value: Any) -> bool:
    """An exact ordered array whose members are each exactly four JSON numbers."""
    return type(value) is list and all(type(b) is list and len(b) == 4 and all(_is_number(c) for c in b) for b in value)


def _exact(box: list) -> tuple[Fraction, Fraction, Fraction, Fraction]:
    return tuple(canonical.exact(c) for c in box)  # type: ignore[return-value]


def box_is_valid(box: list, width: int, height: int) -> bool:
    x, y, w, h = _exact(box)
    return x >= 0 and y >= 0 and w > 0 and h > 0 and x + w <= width and y + h <= height


def iou(a: list, b: list) -> Fraction:
    ax, ay, aw, ah = _exact(a)
    bx, by, bw, bh = _exact(b)
    iw = max(Fraction(0), min(ax + aw, bx + bw) - max(ax, bx))
    ih = max(Fraction(0), min(ay + ah, by + bh) - max(ay, by))
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    if union <= 0:
        f.fail("geometry", "valid boxes must have positive union area")
    return inter / union


def cardinality_ok(policy: str, predictions: int, targets: int) -> bool:
    if policy == "single":
        return predictions == 1
    if policy == "any_one":
        return predictions == 1
    if policy == "all_targets":
        return predictions == targets and predictions > 0
    return False


def check_targets(policy: str, width: Any, height: Any, targets: Any, path: str = "targets") -> list:
    """Structural manifest validity: an invalid target array cannot be scored."""
    f.one_of(policy, f"{path}.box_policy", POLICIES[:3])
    f.integer(width, f"{path}.image_width", minimum=1)
    f.integer(height, f"{path}.image_height", minimum=1)
    f.require(exact_box_array(targets) and len(targets) > 0, path, "targets must be a nonempty exact box array")
    for index, box in enumerate(targets):
        f.require(box_is_valid(box, width, height), f"{path}[{index}]", "target box is invalid in the original frame")
    if policy == "single":
        f.require(len(targets) == 1, path, "a single-box row has exactly one target")
    return targets


def detection_validation(policy: str, width: int, height: int, targets: list, boxes: Any,
                         other_failure: str | None) -> tuple[str, str]:
    """(validation_status, geometry_status) under the fixed precedence.

    Precedence: missing/wrong-type array, invalid coordinate, non-geometry
    schema/value failure (``other_failure``), policy cardinality, valid.
    """
    if not exact_box_array(boxes):
        return "invalid_schema", "invalid"
    if not all(box_is_valid(box, width, height) for box in boxes):
        return "invalid_geometry", "invalid"
    if other_failure is not None:
        f.one_of(other_failure, "other_failure", ("invalid_schema", "invalid_value"))
        return other_failure, "valid"
    if not cardinality_ok(policy, len(boxes), len(targets)):
        return "invalid_geometry", "invalid"
    return "valid", "valid"


def _assignment(weights: list[list[Fraction | None]]) -> tuple[list[int], Fraction] | None:
    """Maximum-total perfect matching over allowed (non-None) edges; None if none exists."""
    n = len(weights)
    big = Fraction(n + 2)
    cost = [[(-w if w is not None else big) for w in row] for row in weights]
    u = [Fraction(0)] * (n + 1)
    v = [Fraction(0)] * (n + 1)
    owner = [0] * (n + 1)
    way = [0] * (n + 1)
    infinity = Fraction(10 ** 6) * (n + 2)
    for i in range(1, n + 1):
        owner[0] = i
        column = 0
        minimum = [infinity] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[column] = True
            row = owner[column]
            delta = infinity
            next_column = 0
            for j in range(1, n + 1):
                if not used[j]:
                    current = cost[row - 1][j - 1] - u[row] - v[j]
                    if current < minimum[j]:
                        minimum[j] = current
                        way[j] = column
                    if minimum[j] < delta:
                        delta = minimum[j]
                        next_column = j
            for j in range(n + 1):
                if used[j]:
                    u[owner[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            column = next_column
            if owner[column] == 0:
                break
        while column:
            previous = way[column]
            owner[column] = owner[previous]
            column = previous
    assignment = [0] * n
    for j in range(1, n + 1):
        assignment[owner[j] - 1] = j - 1
    if any(weights[i][assignment[i]] is None for i in range(n)):
        return None
    return assignment, sum((weights[i][assignment[i]] for i in range(n)), Fraction(0))


def _all_targets(predictions: list, targets: list, threshold: Fraction) -> list[tuple[int, int, Fraction]] | None:
    n = len(predictions)
    scores = [[iou(p, t) for t in targets] for p in predictions]
    weights = [[s if s >= threshold else None for s in row] for row in scores]
    best = _assignment(weights)
    if best is None:
        return None
    optimum = best[1]
    chosen: list[tuple[int, int, Fraction]] = []
    used: set[int] = set()
    fixed = Fraction(0)
    for p in range(n):
        for t in range(n):
            if t in used or weights[p][t] is None:
                continue
            rows = list(range(p + 1, n))
            cols = [c for c in range(n) if c not in used and c != t]
            rest = Fraction(0)
            if rows:
                sub = _assignment([[weights[r][c] for c in cols] for r in rows])
                if sub is None:
                    continue
                rest = sub[1]
            if fixed + weights[p][t] + rest == optimum:
                chosen.append((p, t, scores[p][t]))
                used.add(t)
                fixed += weights[p][t]
                break
        else:  # pragma: no cover - an optimum always admits a lexicographic completion
            f.fail("geometry", "lexicographic matching failed to complete")
    return chosen


def _pairs(items: list[tuple[int, int, Fraction]]) -> list[dict]:
    return [{"iou": rational.to_wire(score), "prediction_index": p, "target_index": t} for p, t, score in items]


def match(policy: str, predictions: list, targets: list, threshold: Fraction) -> dict:
    """Score a cardinality-legal valid row: matched pairs, row IoU, and pass state."""
    if policy in {"single", "any_one"}:
        scores = [iou(predictions[0], target) for target in targets]
        best = max(scores)
        index = scores.index(best)
        return {"matched_pairs": _pairs([(0, index, best)]), "row_iou": rational.to_wire(best), "passed": best >= threshold}
    chosen = _all_targets(predictions, targets, threshold)
    if chosen is None:
        return {"matched_pairs": [], "row_iou": None, "passed": False}
    mean = sum((score for _, _, score in chosen), Fraction(0)) / len(chosen)
    return {"matched_pairs": _pairs(chosen), "row_iou": rational.to_wire(mean), "passed": True}


def _nulls(reason: str) -> dict:
    return {"boxes_valid": None, "matched_pairs": None, "passed": False, "predicted_boxes_digest": None,
            "prediction_count": None, "reason_code": reason, "row_iou": None}


def project(*, policy: str, width: int, height: int, targets: list, runtime_status: str, parse_status: str,
            task_value: Any, validation_status: str, threshold: Fraction) -> dict:
    """Closed geometry projection fields for one detection row."""
    check_targets(policy, width, height, targets)
    if runtime_status != "succeeded":
        return _nulls("runtime_failure")
    if parse_status != "parsed":
        return _nulls("parse_failure")
    f.require(type(task_value) is dict, "geometry", "parsed task value must be an object")
    boxes = task_value.get("boxes")
    exact_array = exact_box_array(boxes)
    if validation_status != "valid":
        if not exact_array:
            f.require(validation_status == "invalid_schema", "geometry", "a missing/wrong-type box array is invalid_schema")
            return _nulls("validation_failure")
        evidence = {"predicted_boxes_digest": canonical.value_digest(boxes), "prediction_count": len(boxes),
                    "matched_pairs": None, "row_iou": None, "passed": False}
        if not all(box_is_valid(box, width, height) for box in boxes):
            f.require(validation_status == "invalid_geometry", "geometry", "invalid coordinates are invalid_geometry")
            return {**evidence, "boxes_valid": False, "reason_code": "invalid_prediction_box"}
        if validation_status in {"invalid_schema", "invalid_value"}:
            return {**evidence, "boxes_valid": True, "reason_code": "validation_failure"}
        f.require(validation_status == "invalid_geometry" and not cardinality_ok(policy, len(boxes), len(targets)),
                  "geometry", "validated geometry status disagrees with the parsed prediction array")
        return {**evidence, "boxes_valid": True, "reason_code": "prediction_count_mismatch"}
    f.require(exact_array and all(box_is_valid(b, width, height) for b in boxes)
              and cardinality_ok(policy, len(boxes), len(targets)), "geometry",
              "a valid validation layer requires an exact, valid, cardinality-legal box array")
    scored = match(policy, boxes, targets, threshold)
    return {"boxes_valid": True, "matched_pairs": scored["matched_pairs"], "passed": scored["passed"],
            "predicted_boxes_digest": canonical.value_digest(boxes), "prediction_count": len(boxes),
            "reason_code": "passed" if scored["passed"] else "below_threshold", "row_iou": scored["row_iou"]}
