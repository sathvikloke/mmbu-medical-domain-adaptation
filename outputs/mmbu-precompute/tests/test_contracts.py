"""Behavioral tests for offline inference boundaries and diagnostic parsing."""

import copy
import importlib
import json
import math
import unittest

try:
    contracts = importlib.import_module("mmbu_prep.contracts")
except ModuleNotFoundError as error:
    if error.name not in {"mmbu_prep", "mmbu_prep.contracts"}:
        raise
    contracts = None


class ContractTestCase(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(contracts, "The input/geometry contract module is not implemented yet")
        self.record = {
            "image_path": "images/synthetic.png",
            "question": "How many blue shapes are visible?",
            "task": "counting",
            "options": ["A) 2", "B) 3"],
            "answer": "2",
            "context": {"modality": "synthetic", "body_part": "none"},
            "history": [{"role": "assistant", "content": "previous answer"}],
            "messages": [{"role": "user", "content": "previous task"}],
            "previous_prediction": {"answer": "3"},
            "predicted_metadata": {"modality": "leaked"},
            "system_prompt": "untrusted record prompt",
        }


class InputContractTests(ContractTestCase):
    def test_task_contains_only_current_question_image_and_caller_prompt(self):
        result = contracts.build_task_input(self.record, "Caller task prompt")
        self.assertEqual(result, {
            "system_prompt": "Caller task prompt",
            "image_path": "images/synthetic.png",
            "question": "How many blue shapes are visible?",
        })

    def test_context_is_invariant_to_question_answer_options_and_previous_state(self):
        before = contracts.build_context_input(self.record, ["modality", "body_part"], "Context prompt")
        changed = copy.deepcopy(self.record)
        changed.update({"question": "another question", "answer": "secret", "options": ["secret"],
                        "context": {"modality": "secret"}, "history": ["secret"],
                        "previous_prediction": "secret", "task": "detection"})
        after = contracts.build_context_input(changed, ["modality", "body_part"], "Context prompt")
        self.assertEqual(before, after)
        self.assertEqual(before, {"system_prompt": "Context prompt", "image_path": "images/synthetic.png",
                                  "requested_fields": ["modality", "body_part"]})

    def test_context_does_not_require_task_question_or_reference_metadata(self):
        result = contracts.build_context_input({"image_path": "same.png"}, ["stain"], "Context prompt")
        self.assertEqual(result["requested_fields"], ["stain"])

    def test_context_rejects_duplicate_unknown_and_empty_fields(self):
        for fields in (["modality", "modality"], ["answer"], ["body part"], [], "modality", [None]):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                contracts.build_context_input(self.record, fields, "Context prompt")

    def test_context_requested_fields_are_fresh_and_keep_caller_order(self):
        fields = ["stain", "modality"]
        result = contracts.build_context_input(self.record, fields, "Context prompt")
        fields.reverse()
        self.assertEqual(result["requested_fields"], ["stain", "modality"])
        result["requested_fields"].append("specimen")
        self.assertEqual(fields, ["modality", "stain"])

    def test_model_builders_reject_missing_or_empty_caller_prompt(self):
        for prompt in (None, "", " \n ", 7):
            for builder in (lambda p: contracts.build_task_input(self.record, p),
                            lambda p: contracts.build_context_input(self.record, ["stain"], p)):
                with self.subTest(prompt=prompt), self.assertRaises(ValueError):
                    builder(prompt)

    def test_model_builders_validate_only_their_required_input_fields(self):
        for bad_image in (None, "", "  ", {"path": "a.png"}):
            row = dict(self.record, image_path=bad_image)
            for builder in (lambda r: contracts.build_task_input(r, "Prompt"),
                            lambda r: contracts.build_context_input(r, ["stain"], "Prompt")):
                with self.subTest(image=bad_image), self.assertRaises(ValueError):
                    builder(row)
        for question in (None, "", 5):
            with self.subTest(question=question), self.assertRaises(ValueError):
                contracts.build_task_input(dict(self.record, question=question), "Prompt")

    def test_builders_do_not_mutate_record_or_reuse_output_dict(self):
        original = copy.deepcopy(self.record)
        first = contracts.build_task_input(self.record, "Prompt")
        first["question"] = "mutated output"
        self.assertEqual(contracts.build_task_input(self.record, "Prompt")["question"], original["question"])
        self.assertEqual(self.record, original)

    def test_judge_receives_reference_data_but_no_history_or_model_prompt(self):
        raw = 'Rationale.\n{"answer":"2"}'
        result = contracts.build_judge_input(self.record, raw)
        self.assertEqual(result, {
            "question": "How many blue shapes are visible?", "options": ["A) 2", "B) 3"],
            "reference_answer": "2", "reference_context": {"modality": "synthetic", "body_part": "none"},
            "raw_prediction": raw,
        })

    def test_judge_deep_copies_nested_references(self):
        row = dict(self.record, answer=[[1, 2, 3, 4]], context={"modality": {"label": "synthetic"}})
        result = contracts.build_judge_input(row, "")
        result["options"].append("C) 4")
        result["reference_answer"][0][0] = 99
        result["reference_context"]["modality"]["label"] = "changed"
        self.assertEqual(row["options"], ["A) 2", "B) 3"])
        self.assertEqual(row["answer"], [[1, 2, 3, 4]])
        self.assertEqual(row["context"], {"modality": {"label": "synthetic"}})

    def test_judge_handles_optional_options_context_but_requires_answer_and_raw_text(self):
        minimal = {"question": "Locate shape", "answer": [1, 2, 3, 4]}
        result = contracts.build_judge_input(minimal, "")
        self.assertEqual(result["options"], [])
        self.assertEqual(result["reference_context"], {})
        with self.assertRaises(ValueError):
            contracts.build_judge_input({"question": "Locate shape"}, "raw")
        with self.assertRaises(ValueError):
            contracts.build_judge_input(minimal, {"answer": "not raw text"})


class ParserTests(ContractTestCase):
    def assert_invalid(self, raw, profile, code=None):
        result = contracts.parse_task_output(raw, profile)
        self.assertFalse(result["ok"])
        self.assertEqual(result["raw"], raw)
        self.assertEqual(result["profile"], profile)
        self.assertIsNone(result["parsed"])
        self.assertTrue(result["diagnostics"])
        if code:
            self.assertIn(code, [item["code"] for item in result["diagnostics"]])
        return result

    def test_brief_preserves_answer_rationale_and_raw_without_semantic_grading(self):
        raw = ' \n{"answer": "2", "rationale": "Two circles are visible."} \n'
        result = contracts.parse_task_output(raw, "brief_json")
        self.assertEqual(result, {"profile": "brief_json", "raw": raw, "ok": True,
                                  "parsed": {"answer": "2", "rationale": "Two circles are visible."},
                                  "diagnostics": []})

    def test_brief_rationale_is_optional_in_engineering_convention(self):
        result = contracts.parse_task_output('{"answer": 2}', "brief_json")
        self.assertTrue(result["ok"])
        self.assertEqual(result["parsed"]["answer"], 2)

    def test_public_card_allows_rationale_prefix_and_preserves_boxes(self):
        raw = 'A blue rectangle appears on the left.\n{"answer": [[1, 2, 3, 4], [5, 6, 7, 8]]}\n'
        result = contracts.parse_task_output(raw, "public_card")
        self.assertTrue(result["ok"])
        self.assertEqual(result["parsed"], {"answer": [[1, 2, 3, 4], [5, 6, 7, 8]]})
        self.assertEqual(result["raw"], raw)

    def test_public_card_accepts_json_only(self):
        self.assertTrue(contracts.parse_task_output('{"answer":"effusion, cardiomegaly"}', "public_card")["ok"])

    def test_brief_does_not_extract_or_repair_json(self):
        for raw in ('Here it is: {"answer":"x"}', '```json\n{"answer":"x"}\n```',
                    '{"answer":"x",}', "{'answer': 'x'}", '{"answer":"x"} trailing', "", "   "):
            with self.subTest(raw=raw):
                self.assert_invalid(raw, "brief_json")

    def test_missing_empty_or_null_answer_is_invalid(self):
        for data in ({}, {"rationale": "visible"}, {"answer": None}, {"answer": "  "}, {"answer": []}):
            for profile in ("brief_json", "public_card"):
                with self.subTest(data=data, profile=profile):
                    self.assert_invalid(json.dumps(data), profile)

    def test_unknown_keys_and_nonstring_rationale_are_invalid(self):
        self.assert_invalid('{"answer":"x","explanation":"y"}', "brief_json", "unexpected_keys")
        self.assert_invalid('{"answer":"x","rationale":2}', "brief_json", "invalid_rationale")
        self.assert_invalid('{"answer":"x","rationale":"y"}', "public_card", "unexpected_keys")

    def test_duplicate_json_keys_are_rejected_including_nested_keys(self):
        for raw in ('{"answer":"a","answer":"b"}', '{"answer":[{"x":1,"x":2}]}'):
            for profile in ("brief_json", "public_card"):
                with self.subTest(raw=raw, profile=profile):
                    self.assert_invalid(raw, profile, "duplicate_key")

    def test_nonfinite_constants_and_overflowing_json_numbers_are_rejected(self):
        for literal in ("NaN", "Infinity", "-Infinity", "1e999", "[1, 2, NaN, 4]"):
            for profile in ("brief_json", "public_card"):
                with self.subTest(literal=literal, profile=profile):
                    self.assert_invalid('{"answer":' + literal + '}', profile, "nonfinite_number")

    def test_multiple_json_objects_are_rejected_in_both_profiles(self):
        for raw in ('{"answer":"a"}\n{"answer":"b"}',
                    'First {"answer":"a"}.\n{"answer":"b"}',
                    '{"answer":"a"} {"answer":"b"}'):
            for profile in ("brief_json", "public_card"):
                with self.subTest(raw=raw, profile=profile):
                    self.assert_invalid(raw, profile)

    def test_public_card_does_not_accept_prose_after_or_multiline_final_object(self):
        for raw in ('{"answer":"a"}\nExtra explanation', 'Rationale.\n{\n"answer": "a"\n}',
                    '```json\n{"answer":"a"}\n```', 'Rationale. {"answer":"a"}'):
            with self.subTest(raw=raw):
                self.assert_invalid(raw, "public_card")

    def test_nonobject_top_level_boolean_or_object_answer_rejected(self):
        for raw in ('[1,2,3,4]', '"answer"', '{"answer":true}', '{"answer":{"label":"x"}}'):
            for profile in ("brief_json", "public_card"):
                with self.subTest(raw=raw, profile=profile):
                    self.assert_invalid(raw, profile)

    def test_configuration_errors_raise_instead_of_becoming_model_failures(self):
        with self.assertRaises(ValueError):
            contracts.parse_task_output('{"answer":"a"}', "unknown_profile")
        with self.assertRaises(ValueError):
            contracts.parse_task_output({"answer": "a"}, "brief_json")


class GeometryTests(ContractTestCase):
    def test_valid_pixel_boxes_are_preserved_without_rounding(self):
        self.assertEqual(contracts.validate_xywh([1.25, 2, 3.5, 4], 10, 10), (1.25, 2, 3.5, 4))
        self.assertEqual(contracts.validate_xywh((0, 0, 10, 10), 10, 10), (0, 0, 10, 10))

    def test_invalid_boxes_are_rejected_without_clamping(self):
        bad = ([-1, 0, 2, 2], [0, -1, 2, 2], [0, 0, 0, 2], [0, 0, 2, -1],
               [9, 0, 2, 2], [0, 9, 2, 2], [0, 0, math.nan, 2], [0, 0, math.inf, 2],
               [True, 0, 2, 2], ["1", 0, 2, 2], [0, 0, 2], "0,0,2,2")
        for box in bad:
            with self.subTest(box=box), self.assertRaises(ValueError):
                contracts.validate_xywh(box, 10, 10)

    def test_dimensions_must_be_positive_finite_numbers_not_booleans(self):
        for dimension in (0, -1, math.nan, math.inf, True, "10", None):
            for width, height in ((dimension, 10), (10, dimension)):
                with self.subTest(width=width, height=height), self.assertRaises(ValueError):
                    contracts.validate_xywh([0, 0, 1, 1], width, height)

    def test_iou_uses_xywh_and_hand_derived_half_threshold(self):
        # Each box area is 6; intersection is 2 * 2 = 4; union is 8.
        first, second = (0, 0, 3, 2), (1, 0, 3, 2)
        self.assertEqual(contracts.box_iou(first, second), 0.5)
        self.assertEqual(contracts.box_iou(second, first), 0.5)
        self.assertLess(contracts.box_iou(first, (1.01, 0, 3, 2)), 0.5)
        self.assertGreater(contracts.box_iou(first, (0.99, 0, 3, 2)), 0.5)

    def test_iou_identity_touching_and_disjoint_boxes(self):
        self.assertEqual(contracts.box_iou([0, 0, 2, 2], [0, 0, 2, 2]), 1.0)
        self.assertEqual(contracts.box_iou([0, 0, 2, 2], [2, 0, 2, 2]), 0.0)
        self.assertEqual(contracts.box_iou([0, 0, 2, 2], [3, 3, 2, 2]), 0.0)

    def test_iou_rejects_invalid_boxes_even_when_they_would_not_overlap(self):
        for box in ([0, 0, -1, 2], [-1, 0, 1, 2], [0, 0, math.inf, 2], [0, 0, True, 2]):
            with self.subTest(box=box), self.assertRaises(ValueError):
                contracts.box_iou([10, 10, 1, 1], box)

    def test_iou_of_large_finite_boxes_avoids_area_overflow(self):
        box = [0, 0, 1e200, 1e200]
        self.assertEqual(contracts.box_iou(box, box), 1.0)


if __name__ == "__main__":
    unittest.main()
