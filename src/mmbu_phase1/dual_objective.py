"""Synthetic answer/context objective adapter; not a final research loss.

This module translates an already validated independent-unit exposure manifest
into causal target-token weights.  It intentionally contains no biomedical
data, model import, optimizer, or automatic policy choice.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from mmbu_phase1 import exposure
from mmbu_phase1 import fields as f


IGNORE_INDEX = -100


def _labels(value: Any, path: str) -> list[int]:
    f.require(type(value) is list and len(value) >= 2, path,
              "must contain at least two causal-label positions")
    for index, token in enumerate(value):
        f.require(type(token) is int and (token == IGNORE_INDEX or token >= 0),
                  f"{path}[{index}]", "must be -100 or a nonnegative non-boolean token ID")
    return value


def compile_plan(rows: Any, labels_by_view: Any) -> dict:
    """Bind accepted exposure rows to exact shifted causal token weights."""
    report = exposure.audit_rows(rows)
    f.require(type(labels_by_view) is dict, "labels_by_view", "must be an object")
    accepted = [row for row in rows if row["accepted"]]
    accepted_ids = {row["view_id"] for row in accepted}
    f.require(set(labels_by_view) == accepted_ids, "labels_by_view",
              "must contain exactly one label row for every accepted view")

    token_weights: dict[str, list[Fraction]] = {}
    endpoint_mass: dict[tuple[str, str], Fraction] = {}
    view_records: dict[str, dict] = {}
    for index, row in enumerate(accepted):
        view_id = row["view_id"]
        labels = _labels(labels_by_view[view_id], f"labels_by_view.{view_id}")
        shifted = labels[1:]
        target_count = sum(token != IGNORE_INDEX for token in shifted)
        f.require(target_count == row["supervised_token_count"],
                  f"labels_by_view.{view_id}",
                  "shifted target count must equal the frozen supervised-token count")
        f.require(target_count > 0, f"labels_by_view.{view_id}", "empty target is forbidden")
        per_token = row["view_share"] / target_count
        weights = [Fraction(0) if token == IGNORE_INDEX else per_token for token in shifted]
        f.require(sum(weights) == row["view_share"], f"labels_by_view.{view_id}",
                  "token weights must partition the declared view mass")
        token_weights[view_id] = weights
        endpoint_key = (row["independent_unit_id"], row["endpoint_id"])
        endpoint_mass[endpoint_key] = endpoint_mass.get(endpoint_key, Fraction(0)) + sum(weights)
        view_records[view_id] = {
            "endpoint_id": row["endpoint_id"],
            "independent_unit_id": row["independent_unit_id"],
            "manifest_index": index,
            "supervised_token_count": target_count,
            "view_mass": row["view_share"],
        }

    expected_endpoint_mass: dict[tuple[str, str], Fraction] = {}
    for row in accepted:
        key = (row["independent_unit_id"], row["endpoint_id"])
        expected_endpoint_mass.setdefault(key, row["endpoint_share"])
    f.require(endpoint_mass == expected_endpoint_mass, "endpoint_mass",
              "realized token weights must reproduce every declared endpoint share")
    total_mass = sum(report["unit_mass"].values(), Fraction(0))
    f.require(sum(endpoint_mass.values(), Fraction(0)) == total_mass, "total_mass",
              "endpoint token weights must reproduce total accepted unit mass")
    return {
        "endpoint_mass": endpoint_mass,
        "ignored_label": IGNORE_INDEX,
        "token_weights": token_weights,
        "total_mass": total_mass,
        "unit_mass": report["unit_mass"],
        "views": view_records,
    }


def padded_float_weights(plan: Any, view_order: Any, width: int) -> list[list[float]]:
    """Project exact weights into a framework-shaped shifted-token matrix."""
    f.require(type(plan) is dict and type(plan.get("token_weights")) is dict,
              "plan", "must be a compiled objective plan")
    f.integer(width, "width", minimum=1)
    f.require(type(view_order) is list and view_order, "view_order", "must be a nonempty list")
    f.require(len(view_order) == len(set(view_order)), "view_order", "duplicate view ID")
    matrix = []
    for index, view_id in enumerate(view_order):
        f.text(view_id, f"view_order[{index}]")
        f.require(view_id in plan["token_weights"], f"view_order[{index}]", "unknown view ID")
        weights = plan["token_weights"][view_id]
        f.require(len(weights) <= width, f"view_order[{index}]", "weight row exceeds framework width")
        matrix.append([float(weight) for weight in weights] + [0.0] * (width - len(weights)))
    return matrix


def runtime_float_weights(plan: Any, view_order: Any, label_rows: Any) -> list[list[float]]:
    """Reproject frozen view mass after runtime-specific left padding changes."""
    f.require(type(plan) is dict and type(plan.get("views")) is dict,
              "plan", "must be a compiled objective plan")
    f.require(type(view_order) is list and view_order, "view_order", "must be a nonempty list")
    f.require(len(view_order) == len(set(view_order)), "view_order", "duplicate view ID")
    f.require(type(label_rows) is list and len(label_rows) == len(view_order),
              "label_rows", "must align one-to-one with view order")
    widths = set()
    matrix = []
    for index, (view_id, raw_labels) in enumerate(zip(view_order, label_rows, strict=True)):
        f.text(view_id, f"view_order[{index}]")
        f.require(view_id in plan["views"], f"view_order[{index}]", "unknown view ID")
        labels = _labels(raw_labels, f"label_rows[{index}]")
        shifted = labels[1:]
        widths.add(len(shifted))
        target_count = sum(token != IGNORE_INDEX for token in shifted)
        view = plan["views"][view_id]
        f.require(target_count == view["supervised_token_count"], f"label_rows[{index}]",
                  "shifted target count changed from the frozen objective plan")
        per_token = view["view_mass"] / target_count
        weights = [Fraction(0) if token == IGNORE_INDEX else per_token for token in shifted]
        f.require(sum(weights) == view["view_mass"], f"label_rows[{index}]",
                  "runtime token weights must preserve frozen view mass")
        matrix.append([float(weight) for weight in weights])
    f.require(len(widths) == 1, "label_rows", "framework batch rows must have one padded width")
    return matrix


def loss_partial(plan: Any, token_losses_by_view: Any) -> tuple[Fraction, Fraction]:
    """Return a weighted numerator/denominator for one nonempty microbatch."""
    f.require(type(plan) is dict and type(plan.get("token_weights")) is dict,
              "plan", "must be a compiled objective plan")
    f.require(type(token_losses_by_view) is dict and token_losses_by_view,
              "token_losses_by_view", "must be a nonempty object")
    f.require(set(token_losses_by_view) <= set(plan["token_weights"]),
              "token_losses_by_view", "contains an unknown view ID")
    numerator = Fraction(0)
    denominator = Fraction(0)
    for view_id, losses in token_losses_by_view.items():
        weights = plan["token_weights"][view_id]
        f.require(type(losses) is list and len(losses) == len(weights),
                  f"token_losses_by_view.{view_id}", "must match shifted-label width")
        for index, (loss, weight) in enumerate(zip(losses, weights, strict=True)):
            f.require(type(loss) is Fraction and loss >= 0,
                      f"token_losses_by_view.{view_id}[{index}]",
                      "must be a nonnegative exact Fraction")
            numerator += loss * weight
            denominator += weight
    f.require(denominator > 0, "token_losses_by_view", "empty-target microbatch is forbidden")
    return numerator, denominator


def combine_loss_partials(parts: Any) -> Fraction:
    """Combine microbatch/device partials by mass, never by mean-of-means."""
    return exposure.combine_partials(parts)
