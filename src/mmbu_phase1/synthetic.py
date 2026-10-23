"""Synthetic engineering fixture and adapter specifications for Phase 1A.

Every input, target, field name, label, and model response here is synthetic.
No official MMBU example, public result, label, statistic, or biomedical record
enters this module.  The fixture deliberately covers classification, counting,
one box, multiple boxes, dynamic context subsets, inapplicable context,
malformed output, every runtime-failure state, judge failure, and stateless
sentinels; each covered case has a deliberate negative.

Synthetic adapter contract (``contract_status=synthetic``; not official):

* a task request and, when context fields are requested, a separate context
  request are serialized independently from the manifest row and input only;
* each call is answered by a fresh stateless responder that is a pure function
  of its own request bytes (a frozen table keyed by request digest);
* the per-example raw record packs the two call transcripts losslessly:
  ``decoded_text`` is RFC 8785 JSON ``{"context": call|null, "task": call}``,
  ``token_ids`` concatenates the task then context tokens (one token per UTF-8
  byte), and any call failure makes the whole evaluation row fail;
* parsed values are ``{"context": object|null, "task": object}``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import hashlib
from pathlib import Path
from typing import Any

from mmbu_phase1 import canonical

LABELS = ("alpha", "beta", "gamma")
CONTEXT_FIELDS = ("syn_magnification", "syn_modality", "syn_region", "syn_stain", "syn_view")
WIDTH, HEIGHT = 100, 80
THRESHOLD = Fraction(1, 2)
TASK_KEYS = {"classification": ("label",), "counting": ("count",), "detection": ("boxes", "required_field")}
SIMULATED_JUDGE_FAILURES = ("det-09",)
CORRECTNESS_RULE = {"rule": "task_grade_equals_one", "version": 1}
TASK_SENTINEL = "TASK-SENTINEL"
CONTEXT_SENTINEL = "CTX-SENTINEL"
MAX_NEW_TOKENS = 256


@dataclass(frozen=True)
class Call:
    """One synthetic responder outcome for one request."""

    runtime_status: str
    text: str | None
    finish_reason: str | None


def ok(value: Any) -> Call:
    text = value if isinstance(value, str) else canonical.dumps(value).decode("utf-8")
    return Call("succeeded", text, "stop")


def failed(status: str, partial: str | None = None) -> Call:
    return Call(status, partial, None)


@dataclass(frozen=True)
class Case:
    example_id: str
    family: str
    weight: int | float
    fields: tuple[str, ...]
    base: Call
    adapted: Call
    target: Any = None
    boxes: tuple = ()
    policy: str = "not_applicable"
    grades: dict = field(default_factory=dict)
    context_base: dict = field(default_factory=dict)
    context_adapted: dict = field(default_factory=dict)
    covers: tuple[str, ...] = ()
    context_failure: dict = field(default_factory=dict)


def ctx_value(example_id: str, name: str) -> str:
    return f"{CONTEXT_SENTINEL}-{example_id}-{name}"


def det(boxes: Any, example_id: str, required: Any = "fill") -> dict:
    return {"boxes": boxes, "required_field": f"{TASK_SENTINEL}-{example_id}" if required == "fill" else required}


def _cases() -> list[Case]:
    T1 = [[10, 10, 20, 20]]
    TWO = [[0, 0, 10, 10], [20, 20, 10, 10]]
    return [
        Case("cls-01", "classification", 1, ("syn_modality", "syn_stain"), ok({"label": "beta"}), ok({"label": "alpha"}),
             target="alpha", grades={"alpha": 1, "beta": 0.25}, context_adapted={"syn_stain": "wrong"},
             covers=("classification", "fractional_grade", "dynamic_context_subset")),
        Case("cls-02", "classification", 2, (), ok({"label": "beta"}), ok({"label": "gamma"}), target="beta",
             grades={"beta": 1}, covers=("classification", "inapplicable_context", "weighted_row")),
        Case("cls-03", "classification", 1, ("syn_view",), ok('{"label": "gamma"'), ok({"label": "gamma"}),
             target="gamma", grades={"gamma": 1}, covers=("malformed_output", "truncated", "parse_failure")),
        Case("cls-04", "classification", 1, (), ok('{"label":"alpha","label":"alpha"}'), ok({"label": "alpha"}),
             target="alpha", grades={"alpha": 1}, covers=("malformed_output", "duplicate_key")),
        Case("cls-05", "classification", 1, ("syn_region",), ok('{"label":"alpha","note":"extra"}'),
             ok({"label": "alpha"}), target="alpha", grades={"alpha": 1}, covers=("malformed_output", "unknown_field")),
        Case("cls-06", "classification", 1, (), ok('{"label":"alpha"}{"label":"beta"}'), ok({"label": "alpha"}),
             target="alpha", grades={"alpha": 1}, covers=("malformed_output", "multiple_objects")),
        Case("cls-07", "classification", 1, (), ok("{}"), ok({"label": "alpha"}), target="alpha",
             grades={"alpha": 1}, covers=("malformed_output", "missing_required")),
        Case("cls-08", "classification", 1, (), ok({"label": "delta"}), ok({"label": "alpha"}), target="alpha",
             grades={"alpha": 1}, covers=("validation_failure", "invalid_value")),
        Case("cls-09", "classification", 1, ("syn_magnification", "syn_modality", "syn_region"), failed("load_failed"),
             ok({"label": "alpha"}), target="alpha", grades={"alpha": 1}, covers=("runtime_failure", "load_failed"),
             context_failure={"base": "load_failed"}),
        Case("cls-10", "classification", 0.5, (), ok({"label": "alpha"}), failed("generation_failed", '{"lab'),
             target="alpha", grades={"alpha": 1}, covers=("runtime_failure", "generation_failed", "partial_output",
                                                          "fractional_weight")),
        Case("cls-11", "classification", 1, ("syn_stain", "syn_view"), ok({"label": "alpha"}), ok({"label": "alpha"}),
             target="alpha", grades={"alpha": 1}, covers=("zero_state_tie",)),
        Case("cnt-01", "counting", 1.5, ("syn_region", "syn_modality"), ok({"count": 3}), ok({"count": 4}), target=4,
             grades={"4": 1, "3": 0.75}, covers=("counting", "fractional_grade", "ordered_context_subset")),
        Case("cnt-02", "counting", 1, (), ok('{"count": NaN}'), ok({"count": 4}), target=4, grades={"4": 1},
             covers=("malformed_output", "nonfinite")),
        Case("cnt-03", "counting", 1, (), ok({"count": "three"}), ok({"count": 3}), target=3, grades={"3": 1},
             covers=("validation_failure", "invalid_schema")),
        Case("cnt-04", "counting", 1, ("syn_stain",), failed("timeout", '{"count":'), failed("oom"), target=2,
             grades={"2": 1}, covers=("runtime_failure", "timeout", "oom", "partial_output")),
        Case("cnt-05", "counting", 1, (), failed("preprocess_failed"), ok({"count": 2}), target=2, grades={"2": 1},
             covers=("runtime_failure", "preprocess_failed")),
        Case("det-01", "detection", 1, ("syn_modality",), ok(det(T1, "det-01")), ok(det(T1, "det-01")), boxes=T1,
             policy="single", covers=("one_box", "geometry_exact")),
        Case("det-02", "detection", 2, (), ok(det([[20, 10, 20, 20]], "det-02")), ok(det(T1, "det-02")), boxes=T1,
             policy="single", covers=("one_box", "geometry_partial")),
        Case("det-03", "detection", 1, (), ok(det([[10, 0, 10, 10]], "det-03")), ok(det([[0, 0, 10, 10]], "det-03")),
             boxes=[[0, 0, 10, 10]], policy="single", covers=("geometry_touching",)),
        Case("det-04", "detection", 1, (), ok(det([[0, 0, 100, 80]], "det-04")), ok(det([[0, 0, 100, 80]], "det-04")),
             boxes=[[0, 0, 100, 80]], policy="single", covers=("geometry_border_valid",)),
        Case("det-05", "detection", 1, (), failed("oom"), ok(det(T1, "det-05")), boxes=T1, policy="single",
             covers=("geometry_runtime_failure", "oom")),
        Case("det-06", "detection", 1, (), ok('{"boxes":[[10,10,20,20]]'), ok(det(T1, "det-06")), boxes=T1,
             policy="single", covers=("geometry_parse_failure", "truncated")),
        Case("det-07", "detection", 1, (), ok(det("not-an-array", "det-07")), ok(det(T1, "det-07")), boxes=T1,
             policy="single", covers=("geometry_wrong_type",)),
        Case("det-08", "detection", 1, (), ok(det(T1, "det-08", required=None)), ok(det(T1, "det-08")), boxes=T1,
             policy="single", covers=("geometry_other_invalid_field",)),
        Case("det-09", "detection", 1, ("syn_view",), ok(det(T1, "det-09")), ok(det(T1, "det-09")), boxes=T1,
             policy="single", covers=("geometry_judge_failure", "judge_failure")),
        Case("det-10", "detection", 1, (), ok(det([[90, 70, 11, 10]], "det-10")), ok(det([[90, 70, 10, 10]], "det-10")),
             boxes=[[90, 70, 10, 10]], policy="single", covers=("geometry_overflow", "invalid_box")),
        Case("det-11", "detection", 1, (), ok(det([[20, 20, 10, 10]], "det-11")), ok(det([[0, 0, 10, 10]], "det-11")),
             boxes=TWO, policy="any_one", covers=("multiple_boxes", "geometry_any_one")),
        Case("det-12", "detection", 1, (), ok(det([[20, 20, 10, 10], [0, 0, 10, 10]], "det-12")),
             ok(det([[20, 20, 10, 10]], "det-12")), boxes=TWO, policy="any_one",
             covers=("multiple_boxes", "geometry_any_one_extra", "count_mismatch")),
        Case("det-13", "detection", 1, ("syn_region", "syn_view"), ok(det([[20, 20, 10, 10], [0, 0, 10, 10]], "det-13")),
             ok(det([[20, 20, 10, 10], [0, 0, 10, 10]], "det-13")), boxes=TWO, policy="all_targets",
             covers=("multiple_boxes", "geometry_all_reordered", "ordering")),
        Case("det-14", "detection", 1, (), ok(det(TWO + [[40, 40, 10, 10]], "det-14")), ok(det(TWO, "det-14")),
             boxes=TWO, policy="all_targets", covers=("multiple_boxes", "geometry_all_extra", "count_mismatch")),
        Case("det-15", "detection", 1, (), ok(det([[0, 0, 10, 10], [0, 0, 10, 10]], "det-15")),
             ok(det([[0, 0, 10, 10], [0, 0, 10, 10]], "det-15")), boxes=[[0, 0, 10, 10], [0, 0, 10, 10]],
             policy="all_targets", covers=("multiple_boxes", "geometry_exact_tie")),
        Case("det-16", "detection", 1, (), ok(det([[-1, 0, 10, 10]], "det-16")), ok(det([[0, 0, 10, 10]], "det-16")),
             boxes=[[0, 0, 10, 10]], policy="single", covers=("geometry_negative", "invalid_box")),
        Case("det-17", "detection", 1, (), ok(det([[0, 0, 0, 10]], "det-17")), ok(det([[0, 0, 10, 10]], "det-17")),
             boxes=[[0, 0, 10, 10]], policy="single", covers=("geometry_zero", "invalid_box")),
        Case("det-18", "detection", 1, (), ok(det([[0, 0, 80, 100]], "det-18")), ok(det([[0, 0, 100, 80]], "det-18")),
             boxes=[[0, 0, 100, 80]], policy="single", covers=("geometry_swapped_frame", "invalid_box")),
        Case("det-19", "detection", 1, (), ok(det([[0.1, 0.1, 0.2, 0.2]], "det-19")), ok(det(T1, "det-19")),
             boxes=T1, policy="single", covers=("geometry_normalized_as_pixel",)),
        Case("det-20", "detection", 1, (), ok(det([], "det-20")), ok(det(T1, "det-20")), boxes=T1, policy="single",
             covers=("geometry_empty_parsed_array", "count_mismatch")),
    ]


CASES = _cases()


def _impl_digest(module: str) -> str:
    path = Path(__file__).resolve().parent / f"{module}.py"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def spec_artifacts() -> dict[str, bytes]:
    """Every immutable adapter/specification artifact as exact canonical bytes."""
    threshold = {"denominator": THRESHOLD.denominator, "numerator": THRESHOLD.numerator}
    specs = {
        "task_prompt": {"kind": "mmbu.phase1a.synthetic_task_prompt", "version": 1, "template_required": True,
                        "instructions": {"classification": "Return a JSON object with exactly the key label.",
                                         "counting": "Return a JSON object with exactly the key count.",
                                         "detection": "Return a JSON object with exactly the keys boxes and required_field;"
                                                      " boxes are original-pixel [x, y, width, height] arrays."}},
        "context_prompt": {"kind": "mmbu.phase1a.synthetic_context_prompt", "version": 1, "template_required": True,
                           "instructions": "Return a JSON object with exactly the requested context fields as string values."},
        "task_output_schema": {"kind": "mmbu.phase1a.synthetic_task_output_schema", "version": 1,
                               "families": {k: list(v) for k, v in TASK_KEYS.items()}, "labels": list(LABELS)},
        "context_output_schema": {"kind": "mmbu.phase1a.synthetic_context_output_schema", "version": 1,
                                  "value_type": "nonempty_string", "keys": "exactly_the_requested_fields"},
        "field_registry": {"kind": "mmbu.phase1a.synthetic_context_field_registry", "version": 1,
                           "fields": list(CONTEXT_FIELDS)},
        "parser": {"kind": "mmbu.phase1a.synthetic_parser", "version": 1, "implementation_sha256": _impl_digest("evaluator"),
                   "kernel_sha256": _impl_digest("canonical"), "raw_transcript": "rfc8785_context_task_calls",
                   "no_extraction_or_repair": True},
        "validator": {"kind": "mmbu.phase1a.synthetic_validator", "version": 1,
                      "implementation_sha256": _impl_digest("evaluator"), "geometry_sha256": _impl_digest("geometry"),
                      "geometry_threshold": threshold, "frame": "original_pixel_xywh"},
        "judge_policy": {"kind": "mmbu.phase1a.synthetic_judge_policy", "version": 1,
                         "implementation_sha256": _impl_digest("evaluator"),
                         "classification_grades": {c.example_id: c.grades for c in CASES if c.family == "classification"},
                         "counting_grades": {c.example_id: c.grades for c in CASES if c.family == "counting"},
                         "detection_grade": "one_if_validated_geometry_passes_else_zero",
                         "context_grade": "one_if_exact_target_string_else_zero",
                         "binary_correctness": CORRECTNESS_RULE,
                         "simulated_judge_failures": list(SIMULATED_JUDGE_FAILURES)},
        "evaluator": {"kind": "mmbu.phase1a.synthetic_evaluator", "version": 1,
                      "implementation_sha256": _impl_digest("task_change"), "geometry_sha256": _impl_digest("geometry"),
                      "geometry_threshold": threshold, "failure_grade": {"denominator": 1, "numerator": 0}},
        "processor": {"kind": "mmbu.phase1a.synthetic_text_processor", "version": 1, "tokenizer": "utf8_bytes"},
        "preprocessor_config": {"kind": "mmbu.phase1a.synthetic_preprocessor_config", "version": 1,
                                "image_geometry": "identity_original_pixel"},
        "template": {"kind": "mmbu.phase1a.synthetic_template", "version": 1, "format": "request_json_only"},
        "image_decoder": {"kind": "mmbu.phase1a.synthetic_descriptor_decoder", "version": 1,
                          "accepts": "mmbu.phase1a.synthetic_image_descriptor"},
    }
    return {name: canonical.dumps(value) for name, value in specs.items()}


def input_descriptor(case: Case) -> dict:
    return {"kind": "mmbu.phase1a.synthetic_image_descriptor", "version": 1, "pattern": f"pattern-{case.example_id}",
            "width": WIDTH, "height": HEIGHT, "synthetic": True}


def task_request(case: Case, specs: dict[str, str]) -> dict:
    return {"call": "task", "input": input_descriptor(case), "input_digest": canonical.value_digest(input_descriptor(case)),
            "prompt_digest": specs["task_prompt"], "output_schema_digest": specs["task_output_schema"],
            "task_family": case.family, "box_policy": case.policy}


def context_request(case: Case, specs: dict[str, str]) -> dict | None:
    if not case.fields:
        return None
    return {"call": "context", "input": input_descriptor(case), "input_digest": canonical.value_digest(input_descriptor(case)),
            "prompt_digest": specs["context_prompt"], "output_schema_digest": specs["context_output_schema"],
            "requested_context_fields": list(case.fields)}


def context_answers(case: Case, side: str) -> Call | None:
    if not case.fields:
        return None
    if side in case.context_failure:
        return failed(case.context_failure[side])
    wrong = case.context_adapted if side == "adapted" else case.context_base
    return ok({name: wrong.get(name, ctx_value(case.example_id, name)) for name in case.fields})


def task_target(case: Case) -> Any:
    if case.family == "detection":
        return {"boxes": [list(b) for b in case.boxes]}
    return {"label": case.target} if case.family == "classification" else {"count": case.target}


def context_target(case: Case) -> dict | None:
    return {name: ctx_value(case.example_id, name) for name in case.fields} if case.fields else None


def responder_table(side: str, specs: dict[str, str]) -> dict:
    """A synthetic model: a frozen map from request digest to one call outcome."""
    responses = {}
    for case in CASES:
        call = case.base if side == "base" else case.adapted
        responses[canonical.value_digest(task_request(case, specs))] = {
            "runtime_status": call.runtime_status, "text": call.text, "finish_reason": call.finish_reason}
        request = context_request(case, specs)
        if request is not None:
            answer = context_answers(case, side)
            responses[canonical.value_digest(request)] = {
                "runtime_status": answer.runtime_status, "text": answer.text, "finish_reason": answer.finish_reason}
    return {"kind": "mmbu.phase1a.synthetic_responder", "version": 1, "model": f"synthetic-{side}", "responses": responses}


def respond(table: dict, request_bytes: bytes) -> Call:
    """A fresh stateless call: output depends only on the exact request bytes."""
    entry = table["responses"].get(canonical.raw_digest(request_bytes))
    if entry is None:
        return Call("generation_failed", None, None)
    return Call(entry["runtime_status"], entry["text"], entry["finish_reason"])
