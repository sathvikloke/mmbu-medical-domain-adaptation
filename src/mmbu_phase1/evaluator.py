"""Synthetic Phase 1A parser, validator, and judge (no extraction, repair, or retry).

Parsing applies the strict canonical kernel to each call's exact decoded text;
it never extracts a JSON substring, repairs syntax, coerces types, clamps
coordinates, drops fields, or retries.  A non-object top-level value or an
inexact/unrepresentable number is ``invalid_json`` under the strict kernel.
"""

from __future__ import annotations

from typing import Any

from mmbu_phase1 import canonical, fields as f, geometry, synthetic

CALL_KEYS = ("decoded_text", "finish_reason", "runtime_status", "token_count")
_PARSE_CODES = {"duplicate_key": "duplicate_key", "nonfinite": "nonfinite", "multiple_values": "multiple_objects"}


def transcript(task: synthetic.Call, context: synthetic.Call | None) -> dict:
    """Pack two separate call outcomes losslessly into the per-example raw fields."""
    calls = [("task", task)] + ([("context", context)] if context is not None else [])
    tokens: list[int] = []
    produced = False
    entries: dict[str, Any] = {"context": None, "task": None}
    for name, call in calls:
        data = call.text.encode("utf-8") if call.text is not None else b""
        tokens.extend(data)
        produced |= call.text is not None
        entries[name] = {"decoded_text": call.text, "finish_reason": call.finish_reason,
                         "runtime_status": call.runtime_status, "token_count": len(data)}
    status = next((call.runtime_status for _, call in calls if call.runtime_status != "succeeded"), "succeeded")
    finish = ";".join(f"{name}={call.finish_reason or 'none'}" for name, call in calls)
    any_finish = any(call.finish_reason is not None for _, call in calls)
    if status == "succeeded":
        return {"token_ids": tokens, "decoded_text": canonical.dumps(entries).decode("utf-8"),
                "finish_reason": finish, "runtime_status": status}
    return {"token_ids": tokens if produced else None,
            "decoded_text": canonical.dumps(entries).decode("utf-8") if produced else None,
            "finish_reason": finish if any_finish else None, "runtime_status": status}


def decode_transcript(raw: dict, has_context: bool, path: str = "raw_output") -> dict:
    """Recover the exact call transcripts; any inconsistency invalidates the raw record."""
    entries = canonical.loads_canonical(raw["decoded_text"].encode("utf-8"))
    f.closed(entries, f"{path}.decoded_text", ("context", "task"))
    tokens: list[int] = []
    for name in ("task", "context"):
        call = entries[name]
        if name == "context" and not has_context:
            f.require(call is None, f"{path}.decoded_text", "a context call exists without requested fields")
            continue
        f.closed(call, f"{path}.decoded_text.{name}", CALL_KEYS)
        data = call["decoded_text"].encode("utf-8") if call["decoded_text"] is not None else b""
        f.require(call["token_count"] == len(data), f"{path}.decoded_text.{name}", "token count differs from the text")
        tokens.extend(data)
    f.require(raw["token_ids"] == tokens, f"{path}.token_ids", "token IDs differ from the call transcripts")
    return entries


def _parse_object(text: str | None, keys: list[str]) -> tuple[str, Any]:
    if text is None:
        return "invalid_json", None
    try:
        value = canonical.loads(text.encode("utf-8"))
    except canonical.CanonicalJSONError as exc:
        return _PARSE_CODES.get(exc.code, "invalid_json"), None
    if type(value) is not dict:
        return "invalid_json", None
    if set(value) - set(keys):
        return "unknown_key", None
    if set(keys) - set(value):
        return "missing_required", None
    return "parsed", value


def parse(raw: dict, row: dict) -> tuple[str, Any]:
    if raw["runtime_status"] != "succeeded":
        return "not_run", None
    entries = decode_transcript(raw, bool(row["requested_context_fields"]))
    status, task = _parse_object(entries["task"]["decoded_text"], list(synthetic.TASK_KEYS[row["task_family"]]))
    if status != "parsed":
        return status, None
    context = None
    if row["requested_context_fields"]:
        status, context = _parse_object(entries["context"]["decoded_text"], row["requested_context_fields"])
        if status != "parsed":
            return status, None
    return "parsed", {"context": context, "task": task}


def _text_failure(value: Any) -> str | None:
    if type(value) is not str:
        return "invalid_schema"
    return None if value else "invalid_value"


def validate(parse_status: str, parsed_value: Any, row: dict, targets: list | None) -> tuple[str, str, Any]:
    if parse_status != "parsed":
        return "not_run", "not_run", None
    task = parsed_value["task"]
    context_failure = next((failure for failure in (_text_failure(v) for v in (parsed_value["context"] or {}).values())
                            if failure), None)
    family = row["task_family"]
    if family == "detection":
        other = _text_failure(task["required_field"]) or context_failure
        status, geometry_status = geometry.detection_validation(row["box_policy"], row["image_width"], row["image_height"],
                                                                targets, task["boxes"], other)
    else:
        geometry_status = "not_applicable"
        if family == "classification":
            label = task["label"]
            failure = "invalid_schema" if type(label) is not str else (None if label in synthetic.LABELS else "invalid_value")
        else:
            count = task["count"]
            failure = "invalid_schema" if type(count) is not int else (None if count >= 0 else "invalid_value")
        status = failure or context_failure or "valid"
    return status, geometry_status, parsed_value if status == "valid" else None


def judge(validation_status: str, validated_value: Any, row: dict, policy: dict, task_target: Any,
          context_target: dict | None, targets: list | None, threshold: Any) -> tuple[str, Any, Any]:
    if validation_status != "valid":
        return "not_run", None, None
    if row["example_id"] in policy["simulated_judge_failures"]:
        return "judge_failed", None, None
    task = validated_value["task"]
    family = row["task_family"]
    if family == "classification":
        grade = policy["classification_grades"].get(row["example_id"], {}).get(task["label"], 0)
    elif family == "counting":
        grade = policy["counting_grades"].get(row["example_id"], {}).get(str(task["count"]), 0)
    else:
        scored = geometry.project(policy=row["box_policy"], width=row["image_width"], height=row["image_height"],
                                  targets=targets, runtime_status="succeeded", parse_status="parsed", task_value=task,
                                  validation_status="valid", threshold=threshold)
        grade = 1 if scored["passed"] else 0
    context = validated_value["context"] or {}
    grades = {name: 1 if context_target is not None and context.get(name) == context_target.get(name) else 0
              for name in sorted(row["requested_context_fields"], key=str.encode)}
    return "judged", grade, grades
