"""Synthetic-only deterministic annotation-lattice transformations for Package B."""

from __future__ import annotations

import hashlib
from typing import Any

from mmbu_phase1 import fields as f, geometry


_ORIGIN = "synthetic_engineering"
_CONVENTIONS = ("xywh_half_open", "xyxy_half_open")


def _binary_mask(mask: Any, width: int, height: int, path: str = "mask") -> list[list[int]]:
    f.integer(width, "image_width", minimum=1)
    f.integer(height, "image_height", minimum=1)
    f.require(type(mask) is list and len(mask) == height, path, "must have exactly image_height rows")
    for y, row in enumerate(mask):
        f.require(type(row) is list and len(row) == width, f"{path}[{y}]", "must have exactly image_width cells")
        for x, value in enumerate(row):
            f.require(type(value) is int and value in (0, 1), f"{path}[{y}][{x}]", "must be binary integer 0 or 1")
    return mask


def mask_to_tight_xywh(mask: Any, width: int, height: int) -> list[int]:
    """Return the positive support's half-open tight box in original pixels."""
    rows = _binary_mask(mask, width, height)
    positive = [(x, y) for y, row in enumerate(rows) for x, value in enumerate(row) if value == 1]
    f.require(bool(positive), "mask", "positive support must be nonempty")
    xs, ys = zip(*positive)
    left, top, right, bottom = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    return [left, top, right - left, bottom - top]


def parse_source_box(box: Any, convention: str, width: int, height: int) -> list:
    f.one_of(convention, "source_box_convention", _CONVENTIONS)
    f.require(type(box) is list and len(box) == 4, "source_box", "must contain exactly four coordinates")
    f.require(all(type(value) is int for value in box), "source_box", "source coordinates must be integer pixels")
    if convention == "xywh_half_open":
        xywh = list(box)
    else:
        x1, y1, x2, y2 = box
        xywh = [x1, y1, x2 - x1, y2 - y1]
    f.require(geometry.box_is_valid(xywh, width, height), "source_box", "invalid original-pixel box")
    return xywh


def serialize_source_box(xywh: Any, convention: str, width: int, height: int) -> list:
    parsed = parse_source_box(xywh, "xywh_half_open", width, height)
    f.one_of(convention, "source_box_convention", _CONVENTIONS)
    if convention == "xywh_half_open":
        return parsed
    x, y, w, h = parsed
    return [x, y, x + w, y + h]


def _base(unit: dict, task: str, target: Any, atom_ids: list[str]) -> dict:
    uid = unit["independent_unit_id"]
    return {
        "atom_ids": list(atom_ids),
        "independent_unit_id": uid,
        "source_id": unit["source_id"],
        "split": unit["split"],
        "split_group_id": unit["split_group_id"],
        "target": target,
        "task_form": task,
        "view_id": f"{uid}::{task}",
    }


def derive_views(unit: Any) -> list[dict]:
    """Emit only the closed deterministic synthetic slice required by Package B."""
    required = {
        "atom_ids", "image_height", "image_width", "independent_unit_id", "instance_ids",
        "instance_set_complete", "mask", "ontology", "origin_class", "source_box", "source_box_convention",
        "source_id", "source_label_id", "source_term", "split", "split_group_id",
    }
    f.closed(unit, "unit", required)
    for key in ("independent_unit_id", "source_id", "source_label_id", "source_term", "split", "split_group_id"):
        f.text(unit[key], f"unit.{key}")
    f.literal(unit["origin_class"], "unit.origin_class", _ORIGIN)
    f.require(normalize_term(unit["source_term"], unit["ontology"]) == unit["source_label_id"],
              "unit.source_term", "source term does not round-trip to its admitted source label ID")
    f.require(type(unit["atom_ids"]) is list and unit["atom_ids"]
              and all(type(item) is str and item for item in unit["atom_ids"]), "unit.atom_ids", "lineage is required")
    f.require(type(unit["instance_ids"]) is list and unit["instance_ids"]
              and len(unit["instance_ids"]) == len(set(unit["instance_ids"]))
              and all(type(item) is str and item for item in unit["instance_ids"]),
              "unit.instance_ids", "complete unique instance IDs are required")
    f.literal(unit["instance_set_complete"], "unit.instance_set_complete", True)
    width = f.integer(unit["image_width"], "unit.image_width", minimum=1)
    height = f.integer(unit["image_height"], "unit.image_height", minimum=1)
    mask_box = mask_to_tight_xywh(unit["mask"], width, height)
    source_box = parse_source_box(unit["source_box"], unit["source_box_convention"], width, height)
    atoms = unit["atom_ids"]
    term = unit["source_term"]
    views = [
        _base(unit, "ungrounded_classification", term, atoms),
        _base(unit, "box_grounded_classification", term, atoms),
        _base(unit, "mask_grounded_classification", term, atoms),
        _base(unit, "mask_localization", mask_box, atoms),
        _base(unit, "box_localization", source_box, atoms),
        _base(unit, "counting", len(unit["instance_ids"]), atoms),
    ]
    views[1]["grounding"] = {"kind": "box", "xywh": list(source_box)}
    views[2]["grounding"] = {"kind": "mask", "mask": [list(row) for row in unit["mask"]]}
    for view in views:
        if "classification" in view["task_form"]:
            view["target_source_id"] = unit["source_label_id"]
    validate_split_isolation(views)
    return views


def _normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def _ontology_index(ontology: Any) -> dict[str, str]:
    f.require(type(ontology) is dict and len(ontology) >= 2, "ontology", "at least two concepts are required")
    index: dict[str, str] = {}
    for concept, terms in ontology.items():
        f.text(concept, "ontology.concept")
        f.require(type(terms) is list and terms, f"ontology.{concept}", "nonempty terms are required")
        for term in terms:
            f.text(term, f"ontology.{concept}.term")
            normalized = _normalized(term)
            f.require(normalized not in index, "ontology", "normalized synonym collision")
            index[normalized] = concept
    return index


def normalize_term(term: str, ontology: Any) -> str:
    f.text(term, "term")
    index = _ontology_index(ontology)
    normalized = _normalized(term)
    f.require(normalized in index, "term", "term is absent from the admitted ontology")
    return index[normalized]


def closed_options(correct_id: str, ontology: Any, view_id: str) -> dict:
    index = _ontology_index(ontology)
    del index
    f.require(correct_id in ontology, "correct_id", "correct concept is absent")
    f.text(view_id, "view_id")
    option_ids = sorted(ontology, key=lambda item: hashlib.sha256(f"{view_id}\0{item}".encode()).digest())
    return {"correct_index": option_ids.index(correct_id), "option_ids": option_ids,
            "options": [ontology[item][0] for item in option_ids]}


def validate_split_isolation(views: Any) -> None:
    f.require(type(views) is list and views, "views", "nonempty view list required")
    unit_split: dict[str, str] = {}
    group_split: dict[str, str] = {}
    seen_views: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()
    for index, view in enumerate(views):
        path = f"views[{index}]"
        for key in ("view_id", "independent_unit_id", "split_group_id", "split", "task_form"):
            f.require(key in view, path, f"missing {key}")
            f.text(view[key], f"{path}.{key}")
        f.require(type(view.get("atom_ids")) is list and view["atom_ids"]
                  and all(type(item) is str and item for item in view["atom_ids"]),
                  f"{path}.atom_ids", "lineage is required")
        f.require(view["view_id"] not in seen_views, f"{path}.view_id", "duplicate view ID")
        edge = (view["independent_unit_id"], view["task_form"])
        f.require(edge not in seen_edges, path, "duplicate derived edge")
        seen_views.add(view["view_id"])
        seen_edges.add(edge)
        for mapping, key in ((unit_split, "independent_unit_id"), (group_split, "split_group_id")):
            identity = view[key]
            prior = mapping.setdefault(identity, view["split"])
            f.require(prior == view["split"], path, f"{key} crosses splits")
