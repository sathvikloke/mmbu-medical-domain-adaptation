"""Offline input boundaries and diagnostics, not an official MMBU harness.

No function runs a model, repairs predictions, or assigns semantic correctness.
The output profiles are local conventions pending organizer confirmation.
"""

from collections.abc import Mapping, Sequence
from copy import deepcopy
from fractions import Fraction
import json
import math


CONTEXT_FIELDS = frozenset({
    "modality", "submodality", "specimen", "body_part", "stain", "medical_domain",
})
OUTPUT_PROFILES = frozenset({"brief_json", "public_card"})


def _record(record: Mapping) -> Mapping:
    if not isinstance(record, Mapping):
        raise ValueError("record must be a mapping")
    return record


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def build_task_input(record: Mapping, system_prompt: str) -> dict:
    """Select only the image path, current question, and caller's prompt.

    This is a generic data structure, not a model-specific messages template.
    Input provenance and image access must be validated separately.
    """
    record = _record(record)
    return {
        "system_prompt": _text(system_prompt, "system_prompt"),
        "image_path": _text(record.get("image_path"), "image_path"),
        "question": _text(record.get("question"), "question"),
    }


def build_context_input(record: Mapping, requested_fields: Sequence, system_prompt: str) -> dict:
    """Build an independent context request without consulting task/reference data.

    Field names use the package's internal underscore convention. The caller
    supplies the requested fields; they are never inferred from reference values.
    """
    record = _record(record)
    if isinstance(requested_fields, (str, bytes)) or not isinstance(requested_fields, Sequence):
        raise ValueError("requested_fields must be a nonempty sequence of field names")
    fields = list(requested_fields)
    if not fields or any(not isinstance(field, str) or field not in CONTEXT_FIELDS for field in fields):
        raise ValueError("requested_fields must contain only supported internal context fields")
    if len(set(fields)) != len(fields):
        raise ValueError("requested_fields must not contain duplicates")
    return {
        "system_prompt": _text(system_prompt, "system_prompt"),
        "image_path": _text(record.get("image_path"), "image_path"),
        "requested_fields": fields,
    }


def build_judge_input(record: Mapping, raw_prediction: str) -> dict:
    """Copy adjudication-only data; never pass this dictionary to the model.

    No judge is called, no option labels are rewritten, and raw text (including
    an empty response) is retained. Nested reference values are copied.
    """
    record = _record(record)
    if not isinstance(raw_prediction, str):
        raise ValueError("raw_prediction must be a string")
    if "answer" not in record:
        raise ValueError("record must contain a reference answer")
    options = record.get("options", [])
    context = record.get("context", {})
    if not isinstance(options, list):
        raise ValueError("options must be a list")
    if not isinstance(context, Mapping):
        raise ValueError("context must be a mapping")
    return {
        "question": _text(record.get("question"), "question"),
        "options": deepcopy(options),
        "reference_answer": deepcopy(record["answer"]),
        "reference_context": deepcopy(dict(context)),
        "raw_prediction": raw_prediction,
    }


class _DiagnosticError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _unique_object(pairs: list) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise _DiagnosticError("duplicate_key", f"Duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _nonfinite_constant(literal: str):
    raise _DiagnosticError("nonfinite_number", f"Nonfinite JSON number: {literal}")


def _finite_float(literal: str) -> float:
    value = float(literal)
    if not math.isfinite(value):
        raise _DiagnosticError("nonfinite_number", "JSON number overflows the finite float range")
    return value


def _contains_json_object(text: str) -> bool:
    """Detect an additional object conservatively; never use it as an answer.

    This deliberately uses the permissive default decoder only for ambiguity
    detection, so an earlier object with duplicate keys/NaN is not overlooked.
    """
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character == "{":
            try:
                value, _ = decoder.raw_decode(text, index)
            except (ValueError, RecursionError):
                continue
            if isinstance(value, dict):
                return True
    return False


def parse_task_output(raw: str, profile: str) -> dict:
    """Return raw text and strict local syntax/schema diagnostics without grading.

    brief_json: whole response is one object; required answer and optional
    string rationale. These keys are an engineering convention, not a confirmed
    final-harness schema. public_card: an optional prose prefix followed by one
    terminal single-line object with only answer. No fallback answer is inferred.

    Invalid predictions return ok=False and parsed=None. Caller configuration
    errors (unknown profile or non-string raw input) raise ValueError.
    """
    if not isinstance(raw, str):
        raise ValueError("raw must be a string")
    if not isinstance(profile, str) or profile not in OUTPUT_PROFILES:
        raise ValueError("profile must be brief_json or public_card")
    result = {"profile": profile, "raw": raw, "ok": False, "parsed": None, "diagnostics": []}
    candidate = raw
    try:
        if profile == "public_card":
            lines = raw.strip().splitlines()
            if not lines:
                raise _DiagnosticError("invalid_json", "The response is empty")
            candidate = lines[-1].strip()
            prefix = "\n".join(lines[:-1])
            if _contains_json_object(prefix):
                raise _DiagnosticError("ambiguous_objects", "Another JSON object precedes the final object")
        parsed = json.loads(candidate, object_pairs_hook=_unique_object,
                            parse_constant=_nonfinite_constant, parse_float=_finite_float)
        if not isinstance(parsed, dict):
            raise _DiagnosticError("not_object", "The selected profile requires a JSON object")
        allowed = {"answer", "rationale"} if profile == "brief_json" else {"answer"}
        unknown = set(parsed) - allowed
        if unknown:
            raise _DiagnosticError("unexpected_keys", f"Unexpected keys: {', '.join(sorted(unknown))}")
        if "answer" not in parsed:
            raise _DiagnosticError("missing_answer", "The answer key is required")
        answer = parsed["answer"]
        if (answer is None or isinstance(answer, bool) or isinstance(answer, dict)
                or isinstance(answer, str) and not answer.strip()
                or isinstance(answer, list) and not answer):
            raise _DiagnosticError("invalid_answer", "Answer must be a nonempty string/list or a finite number")
        if "rationale" in parsed and not isinstance(parsed["rationale"], str):
            raise _DiagnosticError("invalid_rationale", "Rationale must be a string when present")
    except _DiagnosticError as error:
        result["diagnostics"].append({"code": error.code, "message": str(error)})
    except (ValueError, RecursionError) as error:
        result["diagnostics"].append({"code": "invalid_json", "message": str(error)})
    else:
        result["ok"] = True
        result["parsed"] = parsed
    return result


def _finite_number(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite int or float, not a boolean")
    # Python integers are exact and finite regardless of their magnitude.
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


def _box(box: Sequence) -> tuple:
    if isinstance(box, (str, bytes)) or not isinstance(box, Sequence) or len(box) != 4:
        raise ValueError("box must be a sequence of four pixel xywh coordinates")
    values = tuple(box)
    for name, value in zip(("x", "y", "width", "height"), values):
        _finite_number(value, name)
    x, y, width, height = values
    if x < 0 or y < 0 or width <= 0 or height <= 0:
        raise ValueError("box requires nonnegative x/y and strictly positive width/height")
    return values


def validate_xywh(box: Sequence, width: int | float, height: int | float) -> tuple:
    """Validate an in-bounds pixel xywh box without clamping, scaling or rounding.

    Coordinates may be fractional. Dimensions and extents must be positive.
    No tolerance is applied at image boundaries. This function cannot determine
    whether otherwise legal fractional values were intended as normalized units.
    """
    _finite_number(width, "image width")
    _finite_number(height, "image height")
    if width <= 0 or height <= 0:
        raise ValueError("image dimensions must be strictly positive")
    values = _box(box)
    x, y, box_width, box_height = map(Fraction, values)
    if x + box_width > Fraction(width) or y + box_height > Fraction(height):
        raise ValueError("box extends outside the image")
    return values


def box_iou(a: Sequence, b: Sequence) -> float:
    """Compute geometric IoU for two positive-area pixel xywh boxes.

    Image bounds are unavailable here; validate them separately. Exact rational
    intermediates avoid area overflow for large finite coordinates. No threshold,
    matching policy, box repair, or semantic grade is applied.
    """
    ax, ay, aw, ah = map(Fraction, _box(a))
    bx, by, bw, bh = map(Fraction, _box(b))
    overlap_width = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    overlap_height = max(0, min(ay + ah, by + bh) - max(ay, by))
    intersection = overlap_width * overlap_height
    union = aw * ah + bw * bh - intersection
    return float(intersection / union)
