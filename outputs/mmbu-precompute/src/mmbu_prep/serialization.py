"""Serialize explicit reference targets under provisional local conventions.

This module neither annotates nor grades examples. It does not authorize data
use, choose an official protocol, or put references into inference inputs.
"""

from collections.abc import Mapping, Sequence
import json
import re

from .contracts import CONTEXT_FIELDS, OUTPUT_PROFILES, parse_task_output, validate_xywh
from .data import TASKS


LOCAL_CONTEXT_PROFILE = "local_internal_underscore_json"


def _text(value: object, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonblank string")


def _rationale(value: object) -> None:
    if value is not None and not isinstance(value, str):
        raise ValueError("rationale must be an explicitly supplied string or None")


def _json(value: object) -> str:
    # Escape Unicode line separators too: public_card's terminal object must
    # remain one line under str.splitlines(), while JSON retains string values.
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":"))


def _task_answer(task: str, answer: object, width: object, height: object) -> None:
    if not isinstance(task, str) or task not in TASKS:
        raise ValueError("task must be a supported explicit task name")
    if task in {"global_classification", "box_classification"}:
        _text(answer, "classification answer")
    elif task == "counting":
        if not (type(answer) is int and answer >= 0
                or isinstance(answer, str) and re.fullmatch(r"0|[1-9][0-9]*", answer)):
            raise ValueError("count must be a nonnegative integer or canonical ASCII decimal string")
    elif task == "mask_classification":
        if isinstance(answer, str):
            _text(answer, "mask label")
        else:
            if not isinstance(answer, list) or not answer:
                raise ValueError("mask answer must be a nonblank label or a nonempty list of distinct labels")
            for label in answer:
                _text(label, "mask label")
            if len(set(answer)) != len(answer):
                raise ValueError("mask labels must be distinct; duplicates are not silently removed")
    elif task == "detection":
        if not isinstance(answer, list) or not answer:
            raise ValueError("detection answer must be one xywh box or a nonempty list of boxes")
        boxes = [answer] if len(answer) == 4 and all(not isinstance(v, list) for v in answer) else answer
        for box in boxes:
            if not isinstance(box, list):
                raise ValueError("each detection box must be a JSON array of four pixel xywh coordinates")
            validate_xywh(box, width, height)


def serialize_task_target(task, answer, *, profile, rationale=None,
                          image_width=None, image_height=None) -> str:
    """Return a reference target that round-trips through parse_task_output.

    profile is required: brief_json uses answer plus an optional string
    rationale; public_card uses an optional exact rationale prefix, a newline,
    and a terminal answer-only object. Ambiguous public_card prose is rejected.

    Detection requires explicit image dimensions in the same pixel frame as
    its boxes. Dimensions are used only for detection. Values, list order,
    scalar/list cardinality, and integer/string counts are never normalized.
    None omits a rationale; an explicitly supplied empty string remains empty.
    """
    if not isinstance(profile, str) or profile not in OUTPUT_PROFILES:
        raise ValueError("profile must be explicitly brief_json or public_card")
    _rationale(rationale)
    _task_answer(task, answer, image_width, image_height)
    payload = {"answer": answer}
    if profile == "brief_json" and rationale is not None:
        payload["rationale"] = rationale
    raw = _json(payload)
    if profile == "public_card" and rationale is not None:
        raw = rationale + "\n" + raw
    parsed = parse_task_output(raw, profile)
    if not parsed["ok"] or parsed["parsed"] != payload:
        raise ValueError("target cannot round-trip under the selected profile; rationale may contain ambiguous JSON objects")
    return raw


def serialize_context_target(requested_fields, values, *, profile, rationale=None) -> str:
    """Serialize a LOCAL context wrapper with exact explicitly requested fields.

    The only profile is local_internal_underscore_json. Its wrapper is
    {"context": {requested fields}, "rationale": optional explicit string}.
    This is not an official context format or a statement about field masks,
    unknown values, spacing, missing-field scoring, or independent annotations.
    """
    if not isinstance(profile, str) or profile != LOCAL_CONTEXT_PROFILE:
        raise ValueError(f"profile must be explicitly {LOCAL_CONTEXT_PROFILE}")
    _rationale(rationale)
    if isinstance(requested_fields, (str, bytes)) or not isinstance(requested_fields, Sequence):
        raise ValueError("requested_fields must be a nonempty sequence of supported internal field names")
    fields = list(requested_fields)
    if not fields or any(not isinstance(field, str) or field not in CONTEXT_FIELDS for field in fields):
        raise ValueError("requested_fields must contain only supported internal underscore field names")
    if len(set(fields)) != len(fields):
        raise ValueError("requested_fields must not contain duplicates")
    if not isinstance(values, Mapping) or set(values) != set(fields):
        raise ValueError("context values must have exactly the requested fields, with none missing or extra")
    for field in fields:
        _text(values[field], field)
    payload = {"context": {field: values[field] for field in fields}}
    if rationale is not None:
        payload["rationale"] = rationale
    return _json(payload)
