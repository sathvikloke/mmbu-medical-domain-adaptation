"""Normative original-pixel xywh geometry vectors from EVALUATOR_MECHANICS.md."""

from fractions import Fraction
import unittest

from mmbu_phase1 import canonical, geometry
from mmbu_phase1.fields import ContractViolation

W, H = 100, 80
HALF = Fraction(1, 2)


def r(n, d=1):
    return {"denominator": d, "numerator": n}


def pair(p, t, n, d=1):
    return {"iou": r(n, d), "prediction_index": p, "target_index": t}


def scored(policy, targets, boxes, threshold=HALF):
    status, _ = geometry.detection_validation(policy, W, H, targets, boxes, None)
    return geometry.project(policy=policy, width=W, height=H, targets=targets, runtime_status="succeeded",
                            parse_status="parsed", task_value={"boxes": boxes, "required_field": "x"},
                            validation_status=status, threshold=threshold)


class ConformanceVectorTests(unittest.TestCase):
    def check(self, projection, pairs, row_iou, reason):
        self.assertEqual(projection["matched_pairs"], pairs)
        self.assertEqual(projection["row_iou"], row_iou)
        self.assertEqual(projection["reason_code"], reason)
        self.assertEqual(projection["passed"], reason == "passed")

    def test_scored_single_box_vectors(self):
        self.check(scored("single", [[10, 10, 20, 20]], [[10, 10, 20, 20]]), [pair(0, 0, 1)], r(1), "passed")
        self.check(scored("single", [[10, 10, 20, 20]], [[20, 10, 20, 20]]), [pair(0, 0, 1, 3)], r(1, 3), "below_threshold")
        self.check(scored("single", [[0, 0, 10, 10]], [[10, 0, 10, 10]]), [pair(0, 0, 0)], r(0), "below_threshold")
        self.check(scored("single", [[0, 0, 100, 80]], [[0, 0, 100, 80]]), [pair(0, 0, 1)], r(1), "passed")

    def test_failure_projections_have_exact_null_rules(self):
        runtime = geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]], runtime_status="oom",
                                   parse_status="not_run", task_value=None, validation_status="not_run", threshold=HALF)
        self.assertEqual(canonical.dumps(runtime),
                         b'{"boxes_valid":null,"matched_pairs":null,"passed":false,"predicted_boxes_digest":null,'
                         b'"prediction_count":null,"reason_code":"runtime_failure","row_iou":null}')
        parse = geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]], runtime_status="succeeded",
                                 parse_status="invalid_json", task_value=None, validation_status="not_run", threshold=HALF)
        self.assertEqual(parse, {**runtime, "reason_code": "parse_failure"})
        wrong_type = geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]],
                                      runtime_status="succeeded", parse_status="parsed",
                                      task_value={"boxes": "not-an-array", "required_field": "x"},
                                      validation_status="invalid_schema", threshold=HALF)
        self.assertEqual(wrong_type, {**runtime, "reason_code": "validation_failure"})

    def test_geometry_validation_failure_distinguishes_missing_and_present_array(self):
        for member in (None, 7, {"x": 1}, "boxes", [[1, 2, 3]], [["a", 1, 2, 3]], [[True, 0, 1, 1]]):
            with self.subTest(member=member):
                projection = geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]],
                                              runtime_status="succeeded", parse_status="parsed",
                                              task_value={"boxes": member, "required_field": "x"},
                                              validation_status="invalid_schema", threshold=HALF)
                self.assertIsNone(projection["predicted_boxes_digest"])
                self.assertIsNone(projection["prediction_count"])
                self.assertIsNone(projection["boxes_valid"])
                self.assertEqual(projection["reason_code"], "validation_failure")
        present = geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]],
                                   runtime_status="succeeded", parse_status="parsed",
                                   task_value={"boxes": [[10, 10, 20, 20]], "required_field": None},
                                   validation_status="invalid_schema", threshold=HALF)
        self.assertEqual(present["predicted_boxes_digest"], canonical.value_digest([[10, 10, 20, 20]]))
        self.assertEqual(present["prediction_count"], 1)
        self.assertIs(present["boxes_valid"], True)
        self.assertIsNone(present["matched_pairs"])
        self.assertIsNone(present["row_iou"])
        self.assertEqual(present["reason_code"], "validation_failure")

    def test_geometry_judge_failure_preserves_validated_result(self):
        valid = scored("single", [[10, 10, 20, 20]], [[10, 10, 20, 20]])
        self.assertEqual(valid["reason_code"], "passed")
        self.assertNotIn("judge", geometry.project.__code__.co_varnames)

    def test_invalid_box_and_count_mismatch_retain_prediction_evidence(self):
        overflow = scored("single", [[90, 70, 10, 10]], [[90, 70, 11, 10]])
        self.assertEqual(overflow["reason_code"], "invalid_prediction_box")
        self.assertIs(overflow["boxes_valid"], False)
        self.assertEqual(overflow["prediction_count"], 1)
        self.assertEqual(overflow["predicted_boxes_digest"], canonical.value_digest([[90, 70, 11, 10]]))
        self.assertIsNone(overflow["matched_pairs"])
        two = [[0, 0, 10, 10], [20, 20, 10, 10]]
        extra = scored("any_one", two, [[20, 20, 10, 10], [0, 0, 10, 10]])
        self.assertEqual(extra["reason_code"], "prediction_count_mismatch")
        self.assertIs(extra["boxes_valid"], True)
        self.assertIsNone(extra["matched_pairs"])
        self.assertIsNone(extra["row_iou"])
        all_extra = scored("all_targets", two, two + [[40, 40, 10, 10]])
        self.assertEqual(all_extra["reason_code"], "prediction_count_mismatch")
        self.assertEqual(all_extra["prediction_count"], 3)

    def test_any_one_and_all_targets_vectors(self):
        two = [[0, 0, 10, 10], [20, 20, 10, 10]]
        self.check(scored("any_one", two, [[20, 20, 10, 10]]), [pair(0, 1, 1)], r(1), "passed")
        self.check(scored("all_targets", two, [[20, 20, 10, 10], [0, 0, 10, 10]]),
                   [pair(0, 1, 1), pair(1, 0, 1)], r(1), "passed")

    def test_geometry_exact_tie_uses_lexicographic_matching(self):
        same = [[0, 0, 10, 10], [0, 0, 10, 10]]
        projection = scored("all_targets", same, same)
        self.assertEqual(canonical.dumps(projection["matched_pairs"]),
                         b'[{"iou":{"denominator":1,"numerator":1},"prediction_index":0,"target_index":0},'
                         b'{"iou":{"denominator":1,"numerator":1},"prediction_index":1,"target_index":1}]')
        self.assertEqual(projection["row_iou"], r(1))
        self.assertEqual(projection["reason_code"], "passed")

    def test_any_one_tie_records_lowest_target_index(self):
        projection = scored("any_one", [[0, 0, 10, 10], [0, 0, 10, 10]], [[0, 0, 10, 10]])
        self.assertEqual(projection["matched_pairs"], [pair(0, 0, 1)])


class GeometryRuleTests(unittest.TestCase):
    def test_detection_validation_precedence(self):
        target = [[10, 10, 20, 20]]
        self.assertEqual(geometry.detection_validation("single", W, H, target, "bad", "invalid_schema"),
                         ("invalid_schema", "invalid"))
        self.assertEqual(geometry.detection_validation("single", W, H, target, [[95, 0, 10, 10]], "invalid_value"),
                         ("invalid_geometry", "invalid"))
        self.assertEqual(geometry.detection_validation("single", W, H, target, [[0, 0, 1, 1], [0, 0, 2, 2]], "invalid_value"),
                         ("invalid_value", "valid"))
        self.assertEqual(geometry.detection_validation("single", W, H, target, [[0, 0, 1, 1], [0, 0, 2, 2]], None),
                         ("invalid_geometry", "invalid"))
        self.assertEqual(geometry.detection_validation("single", W, H, target, [[0, 0, 1, 1]], None), ("valid", "valid"))

    def test_boxes_are_not_silently_repaired(self):
        cases = {
            "negative": [-1, 0, 10, 10],
            "zero_width": [0, 0, 0, 10],
            "negative_height": [0, 0, 10, -5],
            "overflow_x": [95, 0, 10, 10],
            "overflow_fraction": [0, 0, 100.5, 10],
            "swapped_frame": [0, 0, 80, 100],
        }
        for name, box in cases.items():
            with self.subTest(case=name):
                self.assertFalse(geometry.box_is_valid(box, W, H))
                projection = scored("single", [[10, 10, 20, 20]], [box])
                self.assertEqual(projection["reason_code"], "invalid_prediction_box")
                self.assertEqual(projection["predicted_boxes_digest"], canonical.value_digest([box]))
        self.assertTrue(geometry.box_is_valid([0, 0, 100, 80], W, H))
        self.assertFalse(geometry.box_is_valid([0, 0, 100, 80], 80, 100))

    def test_normalized_looking_boxes_are_still_original_pixels(self):
        projection = scored("single", [[10, 10, 20, 20]], [[0.1, 0.1, 0.2, 0.2]])
        self.assertEqual(projection["reason_code"], "below_threshold")
        self.assertEqual(projection["row_iou"], r(0))
        self.assertTrue(geometry.box_is_valid([0.1, 0.1, 0.2, 0.2], W, H))

    def test_exact_rational_iou_uses_decimal_lexemes(self):
        self.assertEqual(geometry.iou([0, 0, 0.3, 1], [0, 0, 0.1, 1]), Fraction(1, 3))
        self.assertEqual(geometry.iou([0, 0, 10, 10], [5, 0, 10, 10]), Fraction(1, 3))

    def test_inclusive_threshold(self):
        projection = scored("single", [[0, 0, 10, 10]], [[0, 0, 10, 5]])
        self.assertEqual(projection["row_iou"], r(1, 2))
        self.assertEqual(projection["reason_code"], "passed")

    def test_target_cannot_be_reused_and_matching_is_deterministic(self):
        targets = [[0, 0, 10, 10], [50, 50, 10, 10]]
        reuse = scored("all_targets", targets, [[0, 0, 10, 10], [0, 0, 10, 10]])
        self.assertEqual(reuse["reason_code"], "below_threshold")
        self.assertEqual(reuse["matched_pairs"], [])
        self.assertIsNone(reuse["row_iou"])
        boxes = [[0, 0, 10, 10], [1, 1, 10, 10], [2, 2, 10, 10]]
        first = scored("all_targets", boxes, list(boxes))
        for _ in range(3):
            self.assertEqual(scored("all_targets", boxes, list(boxes)), first)
        self.assertEqual([(p["prediction_index"], p["target_index"]) for p in first["matched_pairs"]], [(0, 0), (1, 1), (2, 2)])

    def test_maximum_total_iou_beats_greedy_choice(self):
        targets = [[0, 0, 10, 10], [0, 0, 10, 8]]
        predictions = [[0, 0, 10, 9], [0, 0, 10, 10]]
        projection = scored("all_targets", targets, predictions)
        self.assertEqual([(p["prediction_index"], p["target_index"]) for p in projection["matched_pairs"]], [(0, 1), (1, 0)])
        self.assertEqual(projection["reason_code"], "passed")

    def test_empty_parsed_array_is_evidence_not_fabrication(self):
        projection = scored("single", [[10, 10, 20, 20]], [])
        self.assertEqual(projection["reason_code"], "prediction_count_mismatch")
        self.assertEqual(projection["prediction_count"], 0)
        self.assertEqual(projection["predicted_boxes_digest"], canonical.value_digest([]))

    def test_inconsistent_layer_statuses_reject(self):
        with self.assertRaises(ContractViolation):
            geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]], runtime_status="succeeded",
                             parse_status="parsed", task_value={"boxes": [[10, 10, 20, 20]], "required_field": "x"},
                             validation_status="invalid_geometry", threshold=HALF)
        with self.assertRaises(ContractViolation):
            geometry.project(policy="single", width=W, height=H, targets=[[10, 10, 20, 20]], runtime_status="succeeded",
                             parse_status="parsed", task_value={"boxes": "bad", "required_field": "x"},
                             validation_status="valid", threshold=HALF)
        with self.assertRaises(ContractViolation):
            geometry.project(policy="single", width=W, height=H, targets=[[95, 0, 10, 10]], runtime_status="succeeded",
                             parse_status="parsed", task_value={"boxes": [[10, 10, 20, 20]], "required_field": "x"},
                             validation_status="valid", threshold=HALF)

    def test_target_cardinality_is_structural(self):
        with self.assertRaises(ContractViolation):
            scored("single", [[0, 0, 10, 10], [5, 5, 10, 10]], [[0, 0, 10, 10]])
        with self.assertRaises(ContractViolation):
            scored("any_one", [], [[0, 0, 10, 10]])


if __name__ == "__main__":
    unittest.main()
