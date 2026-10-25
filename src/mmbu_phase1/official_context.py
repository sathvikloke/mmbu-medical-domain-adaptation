"""Strict published-brief biomedical-context parsing and scoring.

This module implements a ``brief_snapshot`` contract only.  It does not
claim equivalence with the unpublished official evaluator.
"""

from __future__ import annotations

from fractions import Fraction
import json
from typing import Any

from mmbu_phase1 import rational
from mmbu_phase1.fields import fail, require


FIELD_REGISTRY = (
    "body_part",
    "medical_domain",
    "modality",
    "specimen",
    "stain",
    "submodality",
)


class _DuplicateKey(ValueError):
    pass


def _requested_fields(value: Any) -> list[str]:
    require(type(value) is list and bool(value), "context.requested_fields", "must be a nonempty list")
    require(all(type(item) is str for item in value), "context.requested_fields", "members must be strings")
    require(value == sorted(set(value), key=str.encode), "context.requested_fields",
            "must be unique and sorted by UTF-8 bytes")
    require(set(value) <= set(FIELD_REGISTRY), "context.requested_fields", "contains an unsupported field")
    return value


def _pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKey(key)
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"nonfinite JSON constant {value}")


def parse_context_output(raw: str, requested_fields: list[str]) -> dict:
    """Parse one strict raw JSON object for the prospectively requested fields."""
    fields = _requested_fields(requested_fields)
    if type(raw) is not str:
        return {"reason": "invalid_json", "valid": False, "value": None}
    try:
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject_constant)
    except _DuplicateKey:
        return {"reason": "duplicate_key", "valid": False, "value": None}
    except (json.JSONDecodeError, TypeError, ValueError):
        return {"reason": "invalid_json", "valid": False, "value": None}
    if type(value) is not dict:
        return {"reason": "invalid_object", "valid": False, "value": None}
    if set(value) != set(fields) or len(value) != len(fields):
        return {"reason": "field_set_mismatch", "valid": False, "value": None}
    if any(type(value[field]) is not str or not value[field].strip() for field in fields):
        return {"reason": "invalid_value", "valid": False, "value": None}
    return {"reason": "valid", "valid": True, "value": value}


def _normalized(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def score_context_output(raw: str, target: dict, requested_fields: list[str]) -> dict:
    """Return strict validity and exact mean field credit for one context pass."""
    fields = _requested_fields(requested_fields)
    require(type(target) is dict and set(target) == set(fields) and len(target) == len(fields),
            "context.target", "must contain exactly the requested fields")
    for field in fields:
        if type(target[field]) is not str or not target[field].strip():
            fail(f"context.target.{field}", "must be a nonempty string")
    parsed = parse_context_output(raw, fields)
    if not parsed["valid"]:
        return {
            "field_grades": {}, "reason": parsed["reason"],
            "score": rational.to_wire(Fraction(0)), "valid": False,
        }
    grades = {
        field: int(_normalized(parsed["value"][field]) == _normalized(target[field]))
        for field in fields
    }
    return {
        "field_grades": grades,
        "reason": "valid",
        "score": rational.to_wire(Fraction(sum(grades.values()), len(fields))),
        "valid": True,
    }


__all__ = ["FIELD_REGISTRY", "parse_context_output", "score_context_output"]
