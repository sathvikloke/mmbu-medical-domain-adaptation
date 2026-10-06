import copy
import math
import unittest

from mmbu_prep.metrics import score_rows, source_balanced_weights, paired_cluster_bootstrap


def row(i, adapted=1, base=0, context=None, source="s1", group=None, task="global_classification"):
    return {"record_id": str(i), "source_id": source, "group_id": group or str(i),
            "task": task, "base_correct": base, "adapted_correct": adapted,
            "context_correct": {"modality": 1} if context is None else context}


class MetricTests(unittest.TestCase):
    def test_metadata_is_averaged_within_example_before_examples(self):
        rows = [row(1), row(2, context={k: 0 for k in
                ("modality", "submodality", "specimen", "body_part", "stain", "medical_domain")})]
        result = score_rows(rows)
        self.assertEqual(result["C"], .5)
        self.assertAlmostEqual(result["S"], .9)

    def test_repeated_image_rows_are_not_deduplicated(self):
        rows = [row(i, group="image-a") for i in range(9)] + [row(9, context={"modality": 0})]
        self.assertEqual(score_rows(rows)["C"], .9)

    def test_negative_adaptation_is_not_clipped(self):
        result = score_rows([row(1, adapted=0, base=1)])
        self.assertEqual(result["S"], -.2)
        self.assertEqual(result["task_gain"], -1)

    def test_weighted_aggregates_precede_nonlinear_product(self):
        rows = [row(i, adapted=int(i < 9), base=int(i < 8), context={"modality": int(i < 9)}, source="a") for i in range(10)]
        rows += [row(i + 10, adapted=int(i < 3), context={"modality": int(i < 3)}, source="b") for i in range(10)]
        self.assertAlmostEqual(score_rows(rows)["S"], .12)

    def test_missing_grades_are_not_silently_dropped(self):
        r = row(1); del r["base_correct"]
        with self.assertRaises(ValueError): score_rows([r])

    def test_unknown_zero_metadata_policy_requires_explicit_resolution(self):
        with self.assertRaises(ValueError): score_rows([row(1, context={})])

    def test_invalid_grades_and_duplicate_ids_are_rejected(self):
        for value in [None, float("nan"), float("inf"), -.1, .5, 2, "1"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                score_rows([row(1, adapted=value)])
        with self.assertRaises(ValueError): score_rows([row(1), row(1)])
        with self.assertRaises(ValueError): score_rows([])
        with self.assertRaises(ValueError): score_rows([row(1, context={"made_up": 1})])

    def test_weights_require_one_finite_positive_entry_per_row(self):
        for weights in [[], [0], [-1], [float("nan")], [float("inf")], [True], [1, 2]]:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                score_rows([row(1)], weights=weights)

    def test_large_finite_weights_are_normalized_without_overflow(self):
        result = score_rows([row(1), row(2, adapted=0)], weights=[1e308, 1e308])
        self.assertAlmostEqual(result["S"], .3)

    def test_huge_integer_grade_has_a_validation_error(self):
        with self.assertRaises(ValueError): score_rows([row(1, adapted=10 ** 400)])

    def test_four_task_proxy_cannot_hide_missing_groups(self):
        with self.assertRaises(ValueError): source_balanced_weights([row(1)])

    def test_counting_shares_global_group_and_sources_are_balanced(self):
        rows = [row(1, source="a"), row(2, source="a", task="counting"), row(3, source="b")]
        rows += [row(4, task="box_classification"), row(5, task="mask_classification"), row(6, task="detection")]
        self.assertEqual(source_balanced_weights(rows), [.0625, .0625, .125, .25, .25, .25])

    def test_unknown_or_incomplete_task_weights_fail(self):
        rows = [row(i, task=t) for i, t in enumerate(("global_classification", "box_classification", "mask_classification", "detection"))]
        with self.assertRaises(ValueError): source_balanced_weights(rows, task_weights={"global_classification": 1})
        with self.assertRaises(ValueError): source_balanced_weights(rows, task_weights={t: float("nan") for t in [r["task"] for r in rows]})

    def test_cluster_bootstrap_keeps_correlated_rows_together(self):
        rows = [row(i, adapted=int(i < 4), group="a" if i < 4 else "b") for i in range(8)]
        original = copy.deepcopy(rows)
        result = paired_cluster_bootstrap(rows, iterations=500, seed=7)
        self.assertEqual(result["interval"], [0.0, 1.0])
        self.assertAlmostEqual(result["point"]["S"], .3)
        self.assertEqual(rows, original)
        self.assertEqual(result, paired_cluster_bootstrap(rows, iterations=500, seed=7))

    def test_one_group_per_source_cannot_produce_a_precision_claim(self):
        result = paired_cluster_bootstrap([row(1, source="a"), row(2, source="b")], iterations=100)
        self.assertIsNone(result["interval"])
        self.assertTrue(result["warnings"])

    def test_bootstrap_preserves_tiny_source_mass_before_weight_division(self):
        rows = [row(1, source="tiny"), row(2, source="tiny"),
                row(3, source="large", adapted=0), row(4, source="large", adapted=0)]
        result = paired_cluster_bootstrap(rows, weights=[1e-200, 1e-200, 1, 1],
                                          iterations=10, seed=4)
        # Tiny source keeps mass 1e-200: T=1e-200, C=1, baseline=0.
        # Every within-source draw therefore has S approximately 2e-201.
        for value in [result["point"]["S"], *result["interval"]]:
            self.assertTrue(math.isclose(value, 2e-201, rel_tol=1e-14, abs_tol=0.0),
                            f"Expected preserved tiny source contribution, got {value!r}")

    def test_bootstrap_parameters_are_validated(self):
        for kwargs in [{"iterations": 0}, {"iterations": True}, {"confidence": 1}, {"confidence": float("nan")}, {"confidence": 10 ** 400}, {"seed": True}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                paired_cluster_bootstrap([row(1), row(2)], **kwargs)


if __name__ == "__main__":
    unittest.main()
