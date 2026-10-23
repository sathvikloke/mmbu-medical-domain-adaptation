"""Normative continuous task-change and secondary binary-flip arithmetic."""

import copy
import unittest

from mmbu_phase1 import canonical, task_change
from mmbu_phase1.fields import ContractViolation


def r(n, d=1):
    return {"denominator": d, "numerator": n}


MANIFEST = [
    {"example_id": "a", "independent_unit_id": "u-a", "task_weight": 1},
    {"example_id": "b", "independent_unit_id": "u-b", "task_weight": 2},
    {"example_id": "c", "independent_unit_id": "u-c", "task_weight": 1},
    {"example_id": "d", "independent_unit_id": "u-d", "task_weight": 2},
]
BASE = {
    "a": {"terminal_outcome": "success", "task_grade": 0.25},
    "b": {"terminal_outcome": "success", "task_grade": 0.8},
    "c": {"terminal_outcome": "success", "task_grade": 0.4},
    "d": {"terminal_outcome": "success", "task_grade": 1},
}
ADAPTED = {
    "a": {"terminal_outcome": "success", "task_grade": 0.75},
    "b": {"terminal_outcome": "success", "task_grade": 0.5},
    "c": {"terminal_outcome": "success", "task_grade": 0.4},
    "d": {"terminal_outcome": "runtime_failure", "task_grade": None},
}
RULE = task_change.correctness_rule("task_grade_equals_one")


def build(predicate="task_grade_equals_one", manifest=MANIFEST, base=BASE, adapted=ADAPTED):
    return task_change.build(manifest, base, adapted, RULE if predicate else None)


class ConformanceVectorTests(unittest.TestCase):
    def test_continuous_task_change_identity_holds(self):
        rows, totals, _ = build()
        self.assertEqual([row["delta"] for row in rows], [r(1, 2), r(-3, 10), r(0), r(-1)])
        self.assertEqual([row["state"] for row in rows], ["positive", "negative", "zero", "negative"])
        self.assertEqual(totals, {
            "example_count": 4,
            "weight_sum": r(6),
            "base_mean": r(17, 24),
            "adapted_mean": r(43, 120),
            "positive_mass": r(1, 12),
            "negative_mass": r(13, 30),
            "net_task_change": r(-7, 20),
        })
        self.assertEqual(rows[3]["adapted_grade"], None)
        self.assertEqual(rows[3]["adapted_terminal_outcome"], "runtime_failure")
        self.assertEqual(rows[0]["base_grade"], 0.25)

    def test_binary_flip_rate_identity_holds_when_applicable(self):
        _, _, binary = build()
        self.assertEqual(binary, {"correctness_rule_digest": canonical.value_digest(RULE), "N": 4, "PF": 0, "NF": 1,
                                  "other": 3, "binary_net_flip_rate": r(-1, 4)})
        _, _, absent = build(predicate=None)
        self.assertIsNone(absent)

    def test_rows_and_totals_recompute_exactly(self):
        rows, totals, binary = build()
        task_change.verify(rows, totals, binary, MANIFEST, BASE, ADAPTED, RULE)


class NegativeArithmeticTests(unittest.TestCase):
    def verify(self, rows, totals, binary, **kwargs):
        args = {"manifest": MANIFEST, "base": BASE, "adapted": ADAPTED, "rule": RULE}
        args.update(kwargs)
        task_change.verify(rows, totals, binary, args["manifest"], args["base"], args["adapted"], args["rule"])

    def test_failures_remain_in_denominator(self):
        rows, totals, binary = build()
        with self.assertRaises(ContractViolation):
            self.verify(rows[:3], totals, binary)
        keep = {"a", "b", "c"}
        omitted_rows, omitted_totals, omitted_binary = build(
            manifest=MANIFEST[:3], base={k: v for k, v in BASE.items() if k in keep},
            adapted={k: v for k, v in ADAPTED.items() if k in keep})
        with self.assertRaises(ContractViolation):
            self.verify(omitted_rows, omitted_totals, omitted_binary)
        wrong = copy.deepcopy(totals)
        wrong["weight_sum"] = r(4)
        wrong["base_mean"] = r(17, 16)
        with self.assertRaises(ContractViolation):
            self.verify(rows, wrong, binary)

    def test_fabricated_zero_grade_and_changed_failure_contribution_reject(self):
        rows, totals, binary = build()
        fabricated = copy.deepcopy(rows)
        fabricated[3]["adapted_grade"] = 0
        with self.assertRaises(ContractViolation):
            self.verify(fabricated, totals, binary)
        credited = dict(ADAPTED, d={"terminal_outcome": "runtime_failure", "task_grade": 1})
        with self.assertRaises(ContractViolation):
            task_change.build(MANIFEST, BASE, credited, RULE)

    def test_missing_layer_row_is_structural_invalidity(self):
        with self.assertRaises(ContractViolation):
            task_change.build(MANIFEST, BASE, {k: v for k, v in ADAPTED.items() if k != "d"}, RULE)

    def test_noncanonical_rationals_and_wrong_states_reject(self):
        rows, totals, binary = build()
        for mutate in (
            lambda rw, tt, bb: rw[0].update(delta={"denominator": 4, "numerator": 2}),
            lambda rw, tt, bb: rw[0].update(delta=0.5),
            lambda rw, tt, bb: rw[2].update(state="positive"),
            lambda rw, tt, bb: tt.update(net_task_change={"denominator": -20, "numerator": 7}),
            lambda rw, tt, bb: tt.update(example_count=3),
            lambda rw, tt, bb: tt.update(positive_mass={"denominator": 2, "numerator": 0}),
            lambda rw, tt, bb: rw[1].update(task_weight=1),
            lambda rw, tt, bb: rw[0].update(independent_unit_id="u-z"),
            lambda rw, tt, bb: rw.reverse(),
            lambda rw, tt, bb: bb.update(PF=1, other=2),
            lambda rw, tt, bb: bb.update(binary_net_flip_rate={"denominator": 3, "numerator": -1}),
        ):
            with self.subTest(mutation=mutate):
                rw, tt, bb = copy.deepcopy(rows), copy.deepcopy(totals), copy.deepcopy(binary)
                mutate(rw, tt, bb)
                with self.assertRaises(ContractViolation):
                    self.verify(rw, tt, bb)

    def test_unbound_binary_threshold_cannot_be_emitted(self):
        rows, totals, binary = build()
        with self.assertRaises(ContractViolation):
            self.verify(rows, totals, binary, rule=None)
        with self.assertRaises(ContractViolation):
            task_change.correctness_rule("grade_at_least_half")

    def test_weights_must_be_positive_finite_and_frozen(self):
        for weight in (0, -1, True, "2"):
            with self.subTest(weight=weight):
                manifest = copy.deepcopy(MANIFEST)
                manifest[0]["task_weight"] = weight
                with self.assertRaises(ContractViolation):
                    task_change.build(manifest, BASE, ADAPTED, RULE)

    def test_fractional_and_weighted_ties(self):
        manifest = [{"example_id": "x", "independent_unit_id": "u-x", "task_weight": 0.5},
                    {"example_id": "y", "independent_unit_id": "u-y", "task_weight": 1.5}]
        base = {"x": {"terminal_outcome": "success", "task_grade": 0.1},
                "y": {"terminal_outcome": "parse_failure", "task_grade": None}}
        adapted = {"x": {"terminal_outcome": "judge_failure", "task_grade": None},
                   "y": {"terminal_outcome": "validation_failure", "task_grade": None}}
        rows, totals, binary = task_change.build(manifest, base, adapted, None)
        self.assertEqual(rows[0]["delta"], r(-1, 10))
        self.assertEqual(rows[1]["state"], "zero")
        self.assertEqual(totals["weight_sum"], r(2))
        self.assertEqual(totals["base_mean"], r(1, 40))
        self.assertEqual(totals["net_task_change"], r(-1, 40))
        self.assertIsNone(binary)


if __name__ == "__main__":
    unittest.main()
