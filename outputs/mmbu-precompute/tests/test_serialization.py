"""Synthetic reference targets only: serialization is not annotation or grading."""

import copy
import importlib
import json
import unittest

from mmbu_prep.contracts import build_context_input, build_task_input, parse_task_output

try:
    serialization = importlib.import_module("mmbu_prep.serialization")
except ModuleNotFoundError as error:
    if error.name != "mmbu_prep.serialization":
        raise
    serialization = None


class TaskSerializationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(serialization, "The explicit target serializer is not implemented")

    def roundtrip(self, task, answer, **kwargs):
        for profile in ("brief_json", "public_card"):
            with self.subTest(task=task, answer=answer, profile=profile):
                raw = serialization.serialize_task_target(task, answer, profile=profile, **kwargs)
                parsed = parse_task_output(raw, profile)
                self.assertTrue(parsed["ok"], parsed)
                self.assertEqual(parsed["raw"], raw)
                self.assertEqual(parsed["parsed"]["answer"], answer)
                self.assertIs(type(parsed["parsed"]["answer"]), type(answer))
                self.assertEqual(json.dumps(parsed["parsed"]["answer"]), json.dumps(answer))
        return raw

    def test_profile_is_required_and_unknown_profiles_or_tasks_are_rejected(self):
        with self.assertRaises(TypeError):
            serialization.serialize_task_target("counting", 1)
        for profile in (None, "auto", "official", [], 2):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                serialization.serialize_task_target("counting", 1, profile=profile)
        for task in (None, "classification", "context", [], 2):
            with self.subTest(task=task), self.assertRaises(ValueError):
                serialization.serialize_task_target(task, "x", profile="brief_json")

    def test_classification_preserves_labels_without_rewriting_options_or_whitespace(self):
        for task in ("global_classification", "box_classification"):
            for answer in ("A) synthetic", "  exact label  ", "β-cell\nlabel", "a\u0085b\u2028c\u2029d"):
                self.roundtrip(task, answer)

    def test_classification_rejects_nontext_and_blank_labels(self):
        for task in ("global_classification", "box_classification"):
            for answer in (None, True, 1, 1.5, [], ["x"], {}, "", " \n\t"):
                with self.subTest(task=task, answer=answer), self.assertRaises(ValueError):
                    serialization.serialize_task_target(task, answer, profile="brief_json")

    def test_counting_preserves_nonnegative_integers_and_canonical_ascii_strings(self):
        for answer in (0, 17, 10**100, "0", "17", "12345678901234567890"):
            self.roundtrip("counting", answer)

    def test_counting_rejects_boolean_negative_float_and_noncanonical_text(self):
        for answer in (True, False, -1, 1.0, float("nan"), None, [], "00", "01", "+1", "-0",
                       "1.0", "1e2", " 1", "1 ", "1\n", "١", "１", "", "many"):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                serialization.serialize_task_target("counting", answer, profile="brief_json")

    def test_mask_preserves_scalar_vs_one_label_vs_multi_label_and_order(self):
        for answer in ("synthetic label", ["synthetic label"], ["B", "A"], ["A", "a"], ["x", " x "]):
            self.roundtrip("mask_classification", answer)

    def test_mask_rejects_empty_duplicate_or_nonstring_lists(self):
        for answer in ("", "  ", [], [""], ["A", "A"], ["A", None], ["A", 2], [True], [["A"]],
                       ("A",), {"A"}, {}, 1):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                serialization.serialize_task_target("mask_classification", answer, profile="public_card")

    def test_detection_preserves_one_box_multi_box_and_numeric_types_without_clamping(self):
        for answer in ([1, 2.5, 3, 4.0], [[1, 2.5, 3, 4.0]], [[4, 5, 6, 7], [0, 0, 10, 10]],
                       [[0, 0, 1, 1], [0, 0, 1, 1]]):
            before = copy.deepcopy(answer)
            self.roundtrip("detection", answer, image_width=10, image_height=12)
            self.assertEqual(answer, before)

    def test_detection_requires_explicit_positive_finite_image_dimensions(self):
        for dims in ({}, {"image_width": 10}, {"image_height": 10},
                     {"image_width": 0, "image_height": 10}, {"image_width": True, "image_height": 10},
                     {"image_width": float("inf"), "image_height": 10},
                     {"image_width": 10, "image_height": "10"}):
            with self.subTest(dims=dims), self.assertRaises(ValueError):
                serialization.serialize_task_target("detection", [0, 0, 1, 1], profile="brief_json", **dims)

    def test_detection_rejects_empty_negative_out_of_bounds_nonfinite_and_ambiguous_shapes(self):
        for answer in ([], None, "none", [0, 0, 0, 1], [-1, 0, 1, 1], [9, 0, 2, 1], [0, 0, 1, 11],
                       [0, 0, True, 1], [0, 0, float("inf"), 1], [0, 0, float("nan"), 1],
                       [0, 0, "1", 1], [0, 0, 1], [0, 0, 1, 1, 2], [[0, 0, 1, 1], []],
                       [[0, 0, 1, 1], 2], (0, 0, 1, 1), [(0, 0, 1, 1)]):
            with self.subTest(answer=answer), self.assertRaises(ValueError):
                serialization.serialize_task_target("detection", answer, profile="brief_json",
                                                    image_width=10, image_height=10)

    def test_brief_rationale_is_optional_explicit_and_exact_even_with_json_text(self):
        without = serialization.serialize_task_target("counting", 0, profile="brief_json")
        self.assertEqual(json.loads(without), {"answer": 0})
        for rationale in ("", "  Provided prose.\nSecond line.  ", 'Literal {"answer": "other"}.'):
            raw = serialization.serialize_task_target("counting", 0, profile="brief_json", rationale=rationale)
            self.assertEqual(parse_task_output(raw, "brief_json")["parsed"], {"answer": 0, "rationale": rationale})

    def test_public_rationale_is_exact_prefix_and_never_inserted_into_answer_object(self):
        for rationale in ("", "  Provided prose.\nSecond line.  "):
            raw = serialization.serialize_task_target("counting", "0", profile="public_card", rationale=rationale)
            self.assertTrue(raw.startswith(rationale + "\n"))
            self.assertEqual(parse_task_output(raw, "public_card")["parsed"], {"answer": "0"})
        raw = serialization.serialize_task_target("counting", "0", profile="public_card")
        self.assertEqual(json.loads(raw), {"answer": "0"})

    def test_public_rationale_rejects_ambiguous_objects_without_repairing_them(self):
        for rationale in ('Earlier {"answer":"x"}', "Discuss {} in prose.",
                          '{"duplicate": 1, "duplicate": 2}', '{"a": NaN}', '"{}"',
                          'Line one\n{"a":1}\nLine three'):
            with self.subTest(rationale=rationale), self.assertRaisesRegex(ValueError, "round.trip|ambig"):
                serialization.serialize_task_target("counting", 1, profile="public_card", rationale=rationale)

    def test_nonstring_rationale_is_rejected_without_fabrication(self):
        for profile in ("brief_json", "public_card"):
            for rationale in (False, 0, [], {}, ["explanation"]):
                with self.subTest(profile=profile, rationale=rationale), self.assertRaises(ValueError):
                    serialization.serialize_task_target("counting", 1, profile=profile, rationale=rationale)


class ContextSerializationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(serialization, "The explicit target serializer is not implemented")
        self.profile = "local_internal_underscore_json"

    def test_context_profile_is_required_explicitly_local_and_never_auto_inferred(self):
        with self.assertRaises(TypeError):
            serialization.serialize_context_target(["modality"], {"modality": "synthetic"})
        for profile in (None, "public_card", "brief_json", "official_context", []):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                serialization.serialize_context_target(["modality"], {"modality": "synthetic"}, profile=profile)

    def test_context_matches_requested_keys_preserves_values_and_request_order(self):
        fields = ["stain", "body_part", "modality"]
        values = {"modality": " synthetic ", "body_part": "user-declared unknown", "stain": "β label"}
        before = copy.deepcopy(values)
        raw = serialization.serialize_context_target(fields, values, profile=self.profile)
        result = json.loads(raw)
        self.assertEqual(result, {"context": values})
        self.assertEqual(list(result["context"]), fields)
        self.assertEqual(values, before)
        self.assertEqual(fields, ["stain", "body_part", "modality"])

    def test_context_rejects_missing_extra_blank_or_nonstrings_without_guessing(self):
        for values in ({}, {"modality": "x", "stain": "y"}, {"modality": None}, {"modality": ""},
                       {"modality": "  "}, {"modality": 0}, {"modality": ["x"]},
                       {"modality": {"answer": "x"}}, ["x"], "x"):
            with self.subTest(values=values), self.assertRaises(ValueError):
                serialization.serialize_context_target(["modality"], values, profile=self.profile)

    def test_context_rejects_spaced_unknown_duplicate_and_invalid_requested_fields(self):
        for fields in ([], ["body part"], ["medical domain"], ["answer"], ["rationale"],
                       ["modality", "modality"], [None], "modality", {"modality"}, None):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                serialization.serialize_context_target(fields, {"modality": "synthetic"}, profile=self.profile)

    def test_all_six_explicit_context_fields_and_optional_rationale_are_supported(self):
        fields = ["modality", "submodality", "specimen", "body_part", "stain", "medical_domain"]
        values = {field: "explicit " + field for field in fields}
        for rationale in ("", 'Caller supplied {"text":"only"}.\nNo fabrication.'):
            raw = serialization.serialize_context_target(fields, values, profile=self.profile, rationale=rationale)
            self.assertEqual(json.loads(raw), {"context": values, "rationale": rationale})
        for rationale in (False, 0, [], {}):
            with self.subTest(rationale=rationale), self.assertRaises(ValueError):
                serialization.serialize_context_target(fields, values, profile=self.profile, rationale=rationale)

    def test_serialized_references_do_not_enter_independent_model_inputs(self):
        row = {"image_path": "synthetic.png", "question": "Classify shape", "task": "global_classification",
               "answer": "secret-reference", "context": {"modality": "secret-context"}}
        task_before = build_task_input(row, "Caller prompt")
        context_before = build_context_input(row, ["modality"], "Context prompt")
        row["serialized_task_target"] = serialization.serialize_task_target(row["task"], row["answer"], profile="brief_json")
        row["serialized_context_target"] = serialization.serialize_context_target(["modality"], row["context"], profile=self.profile)
        self.assertEqual(build_task_input(row, "Caller prompt"), task_before)
        self.assertEqual(build_context_input(row, ["modality"], "Context prompt"), context_before)
        self.assertNotIn("secret", json.dumps(task_before))
        self.assertNotIn("secret", json.dumps(context_before))


if __name__ == "__main__":
    unittest.main()
