"""Official-style biomedical-context evaluator tests."""

from __future__ import annotations

import unittest

from mmbu_phase1 import biomedical_lane1, official_context
from mmbu_phase1.fields import ContractViolation


class OfficialContextEvaluatorTests(unittest.TestCase):
    def test_exact_raw_json_scores_all_requested_fields(self):
        raw = '{"modality":"ultrasound","medical_domain":"radiology"}'
        result = official_context.score_context_output(
            raw,
            {"medical_domain": "Radiology", "modality": "Ultrasound"},
            ["medical_domain", "modality"],
        )
        self.assertEqual(result, {
            "field_grades": {"medical_domain": 1, "modality": 1},
            "reason": "valid",
            "score": {"denominator": 1, "numerator": 1},
            "valid": True,
        })

    def test_valid_object_receives_field_level_partial_credit(self):
        result = official_context.score_context_output(
            '{"body_part":"lung","modality":"CT","submodality":"contrast"}',
            {"body_part": "lung", "modality": "CT", "submodality": "noncontrast"},
            ["body_part", "modality", "submodality"],
        )
        self.assertTrue(result["valid"])
        self.assertEqual(result["field_grades"], {"body_part": 1, "modality": 1, "submodality": 0})
        self.assertEqual(result["score"], {"denominator": 3, "numerator": 2})

    def test_dynamic_subset_does_not_require_unrequested_fields(self):
        parsed = official_context.parse_context_output('{"stain":"H&E"}', ["stain"])
        self.assertEqual(parsed, {"reason": "valid", "valid": True, "value": {"stain": "H&E"}})

    def test_strict_parser_rejects_non_raw_or_non_closed_json(self):
        cases = {
            "fence": '```json\n{"modality":"CT"}\n```',
            "duplicate": '{"modality":"CT","modality":"MRI"}',
            "unknown": '{"modality":"CT","extra":"x"}',
            "missing": '{}',
            "trailing": '{"modality":"CT"} {"modality":"MRI"}',
            "non_string": '{"modality":3}',
        }
        expected = {
            "fence": "invalid_json", "duplicate": "duplicate_key", "unknown": "field_set_mismatch",
            "missing": "field_set_mismatch", "trailing": "invalid_json", "non_string": "invalid_value",
        }
        for label, raw in cases.items():
            with self.subTest(label=label):
                parsed = official_context.parse_context_output(raw, ["modality"])
                self.assertFalse(parsed["valid"])
                self.assertEqual(parsed["reason"], expected[label])
                self.assertIsNone(parsed["value"])
                scored = official_context.score_context_output(raw, {"modality": "CT"}, ["modality"])
                self.assertEqual(scored["score"], {"denominator": 1, "numerator": 0})
                self.assertEqual(scored["field_grades"], {})

    def test_requested_subset_and_target_are_fail_closed(self):
        invalid = ([], ["unknown_field"], ["modality", "modality"])
        for fields in invalid:
            with self.subTest(fields=fields), self.assertRaises(ContractViolation):
                official_context.parse_context_output('{"modality":"CT"}', fields)
        with self.assertRaises(ContractViolation):
            official_context.score_context_output(
                '{"modality":"CT"}', {"modality": "CT", "stain": "H&E"}, ["modality"]
            )

    def test_lane1_routes_declared_official_field_rows_to_successor_scorer(self):
        rows = [{
            "context_target": {"medical_domain": "radiology", "modality": "ultrasound"},
            "requested_context_fields": ["medical_domain", "modality"],
            "row_id": "synthetic-context-1",
            "source_id": "busbra",
            "task_target": "benign",
        }]
        predictions = [{
            "context": '{"medical_domain":"radiology","modality":"ultrasound"}',
            "row_id": "synthetic-context-1",
            "task": "benign",
        }]
        metrics = biomedical_lane1.score_predictions(rows, predictions)
        self.assertEqual(metrics["context_macro_score"], {"denominator": 1, "numerator": 1})


if __name__ == "__main__":
    unittest.main()
