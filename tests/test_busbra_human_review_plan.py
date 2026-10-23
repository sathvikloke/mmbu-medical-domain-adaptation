"""Closure checks for the pending BUS-BRA human review plan."""

import json
from pathlib import Path
import unittest


REPO = Path(__file__).resolve().parents[1]


class BusbraHumanReviewPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((REPO / "config/busbra-human-review-plan.json").read_text())
        self.contract_path = REPO / "outputs/BUSBRA-structural-transform-contract-2026-10-23.json"
        self.contract = json.loads(self.contract_path.read_text())

    def test_plan_is_pending_closed_and_binds_the_structural_contract(self):
        self.assertEqual(set(self.plan), {
            "decision_status", "exception_population_source", "exception_population_source_digest",
            "mandatory_record_rules", "medical_review_population", "proposed_task_decisions", "review_roles",
            "schema", "source_id", "source_version", "training_ready",
        })
        self.assertEqual(self.plan["schema"], "mmbu.busbra.human_review_plan.v1")
        self.assertEqual(self.plan["decision_status"], "pending_human_review")
        self.assertIs(self.plan["training_ready"], False)
        self.assertEqual(self.plan["exception_population_source_digest"], self.contract["contract_digest"])

    def test_mandatory_population_and_union_arithmetic_are_exact(self):
        mandatory = set(self.contract["bbox_exception_records"])
        mandatory.update(self.contract["dimension_exception_records"])
        mandatory.update(("bus_0110-l", "bus_0536-r"))
        population = self.plan["medical_review_population"]
        self.assertEqual(len(mandatory), population["expected_mandatory_record_count"])
        self.assertEqual(population["expected_stratified_record_count"], 199)
        self.assertEqual(population["expected_overlap_record_count"], 5)
        self.assertEqual(
            population["expected_stratified_record_count"] + len(mandatory)
            - population["expected_overlap_record_count"],
            population["expected_union_record_count"],
        )
        self.assertEqual(population["expected_union_record_count"], 244)

    def test_all_roles_and_tasks_are_explicit_but_not_approved(self):
        self.assertEqual(set(self.plan["review_roles"]), {
            "medical_primary", "medical_secondary", "provenance", "rights_release",
        })
        self.assertEqual(len(self.plan["proposed_task_decisions"]), 4)
        self.assertNotIn("approved", json.dumps(self.plan["proposed_task_decisions"]).lower())


if __name__ == "__main__":
    unittest.main()
