"""Synthetic tests for the answer/context objective preflight adapter."""

from fractions import Fraction
import unittest

try:
    from mmbu_phase1 import dual_objective
except ImportError:
    dual_objective = None
from mmbu_phase1.fields import ContractViolation


class DualObjectiveModuleTests(unittest.TestCase):
    def test_dual_objective_module_exists(self):
        self.assertIsNotNone(dual_objective, "dual-objective preflight adapter is missing")


def row(unit, endpoint, view, share, tokens, *, endpoint_share, fields=()):
    return {
        "accepted": True,
        "base_unit_mass": Fraction(1),
        "effective_unit_mass": Fraction(1),
        "endpoint_id": endpoint,
        "endpoint_share": endpoint_share,
        "independent_unit_id": unit,
        "prospective_balance_multiplier": Fraction(1),
        "rejection_reason": None,
        "requested_context_fields": list(fields),
        "source_family_id": "synthetic-family",
        "split_group_id": f"group-{unit}",
        "supervised_token_count": tokens,
        "target_bytes": view.encode("utf-8"),
        "task_form": "synthetic",
        "token_normalization_id": "uniform_within_view_v1",
        "schedule_position_or_epoch_rule": "one_complete_cycle_v1",
        "unit_total_mass": Fraction(1),
        "view_id": view,
        "view_share": share,
    }


@unittest.skipIf(dual_objective is None, "dual-objective preflight adapter not implemented")
class DualObjectivePlanTests(unittest.TestCase):
    def rows(self):
        return [
            row("u1", "task", "u1-task", Fraction(3, 4), 1,
                endpoint_share=Fraction(3, 4)),
            row("u1", "context", "u1-context", Fraction(1, 4), 3,
                endpoint_share=Fraction(1, 4), fields=("modality", "stain")),
            row("u2", "task", "u2-task", Fraction(1), 2,
                endpoint_share=Fraction(1)),
        ]

    def labels(self):
        return {
            "u1-task": [-100, -100, 7],
            "u1-context": [-100, 8, 9, 10],
            "u2-task": [-100, -100, 11, 12],
        }

    def test_target_length_and_endpoint_density_preserve_declared_mass(self):
        plan = dual_objective.compile_plan(self.rows(), self.labels())
        self.assertEqual(plan["total_mass"], Fraction(2))
        self.assertEqual(plan["unit_mass"], {"u1": Fraction(1), "u2": Fraction(1)})
        self.assertEqual(plan["endpoint_mass"], {
            ("u1", "task"): Fraction(3, 4),
            ("u1", "context"): Fraction(1, 4),
            ("u2", "task"): Fraction(1),
        })
        self.assertEqual(plan["token_weights"]["u1-task"], [Fraction(0), Fraction(3, 4)])
        self.assertEqual(plan["token_weights"]["u1-context"],
                         [Fraction(1, 12), Fraction(1, 12), Fraction(1, 12)])
        self.assertEqual(plan["token_weights"]["u2-task"],
                         [Fraction(0), Fraction(1, 2), Fraction(1, 2)])

    def test_shifted_target_count_and_exact_population_fail_closed(self):
        for labels in (
            {**self.labels(), "u1-context": [-100, 8, 9]},
            {**self.labels(), "extra": [-100, 1]},
            {key: value for key, value in self.labels().items() if key != "u1-task"},
            {**self.labels(), "u1-task": [-100]},
            {**self.labels(), "u1-task": [-100, True, 7]},
        ):
            with self.subTest(labels=labels), self.assertRaises(ContractViolation):
                dual_objective.compile_plan(self.rows(), labels)

    def test_framework_shaped_weights_match_exact_plan(self):
        plan = dual_objective.compile_plan(self.rows(), self.labels())
        matrix = dual_objective.padded_float_weights(
            plan, ["u1-task", "u1-context", "u2-task"], width=4
        )
        self.assertEqual(matrix, [
            [0.0, 0.75, 0.0, 0.0],
            [1 / 12, 1 / 12, 1 / 12, 0.0],
            [0.0, 0.5, 0.5, 0.0],
        ])
        with self.assertRaises(ContractViolation):
            dual_objective.padded_float_weights(plan, ["u1-task", "u1-task"], width=4)
        with self.assertRaises(ContractViolation):
            dual_objective.padded_float_weights(plan, ["u1-context"], width=2)

    def test_microbatch_padding_reprojects_the_same_frozen_view_mass(self):
        plan = dual_objective.compile_plan(self.rows(), self.labels())
        projected = dual_objective.runtime_float_weights(
            plan,
            ["u1-context", "u2-task"],
            [[-100, 8, 9, 10, -100], [-100, -100, 11, 12, -100]],
        )
        self.assertEqual(projected, [
            [1 / 12, 1 / 12, 1 / 12, 0.0],
            [0.0, 0.5, 0.5, 0.0],
        ])
        with self.assertRaises(ContractViolation):
            dual_objective.runtime_float_weights(
                plan, ["u1-context"], [[-100, 8, 9, -100]]
            )

    def test_full_and_accumulated_weighted_objectives_are_identical(self):
        plan = dual_objective.compile_plan(self.rows(), self.labels())
        token_losses = {
            "u1-task": [Fraction(0), Fraction(2)],
            "u1-context": [Fraction(3), Fraction(6), Fraction(9)],
            "u2-task": [Fraction(0), Fraction(4), Fraction(8)],
        }
        full = dual_objective.loss_partial(plan, token_losses)
        left = dual_objective.loss_partial(plan, {"u1-task": token_losses["u1-task"]})
        right = dual_objective.loss_partial(
            plan, {key: token_losses[key] for key in ("u1-context", "u2-task")}
        )
        self.assertEqual(dual_objective.combine_loss_partials([full]), Fraction(9, 2))
        self.assertEqual(dual_objective.combine_loss_partials([left, right]), Fraction(9, 2))
        self.assertNotEqual((dual_objective.combine_loss_partials([left])
                             + dual_objective.combine_loss_partials([right])) / 2,
                            Fraction(9, 2))

    def test_loss_population_and_width_fail_closed(self):
        plan = dual_objective.compile_plan(self.rows(), self.labels())
        with self.assertRaises(ContractViolation):
            dual_objective.loss_partial(plan, {})
        with self.assertRaises(ContractViolation):
            dual_objective.loss_partial(plan, {"unknown": [Fraction(1)]})
        with self.assertRaises(ContractViolation):
            dual_objective.loss_partial(plan, {
                "u1-task": [Fraction(0), Fraction(1), Fraction(2)],
                "u1-context": [Fraction(1), Fraction(1), Fraction(1)],
                "u2-task": [Fraction(0), Fraction(1), Fraction(1)],
            })


if __name__ == "__main__":
    unittest.main()
