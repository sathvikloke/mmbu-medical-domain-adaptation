"""Joint comparisons use aligned records and the same resampled groups."""

import copy
import importlib
import math
import unittest

try:
    comparison = importlib.import_module("mmbu_prep.comparison")
except ModuleNotFoundError as error:
    if error.name not in {"mmbu_prep", "mmbu_prep.comparison"}:
        raise
    comparison = None


def row(identifier, *, adapted=1, base=0, context=None, source="source", group=None,
        task="global_classification"):
    return {"record_id": str(identifier), "source_id": source,
            "group_id": str(identifier) if group is None else group, "task": task,
            "adapted_correct": adapted, "base_correct": base,
            "context_correct": {"modality": 1} if context is None else context}


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(comparison, "The joint comparison module is not implemented yet")

    def test_candidates_keep_their_own_baselines_and_signed_scores(self):
        candidates = {
            "adapted": [row("a", adapted=0, base=1), row("b", adapted=0, base=1)],
            "other": [row("a"), row("b")],
        }
        result = comparison.compare_candidates(candidates, iterations=10, seed=1)
        self.assertEqual(result["candidates"]["adapted"]["S"], -.2)
        self.assertEqual(result["candidates"]["other"]["S"], 1.0)
        self.assertEqual(result["pairwise"][0]["left"], "adapted")
        self.assertEqual(result["pairwise"][0]["right"], "other")
        self.assertEqual(result["pairwise"][0]["delta_S"], -1.2)
        self.assertEqual(result["pairwise"][0]["interval"], [-1.2, -1.2])

    def test_delta_is_not_clipped_to_unit_interval(self):
        # A: T=6/16, B=1, C=1 -> S=-5/16. B: T=C=1, baseline=0 -> S=1.
        candidates = {
            "a": [row(i, adapted=int(i < 6), base=1) for i in range(16)],
            "b": [row(i) for i in range(16)],
        }
        result = comparison.compare_candidates(candidates, iterations=10, seed=2)
        self.assertEqual(result["pairwise"][0]["delta_S"], -1.3125)

    def test_identical_candidates_have_zero_difference_on_every_shared_draw(self):
        rows = [row(i, adapted=int(i < 4), base=int(i % 3 == 0),
                    context={"modality": int(i % 2 == 0)}, group="a" if i < 4 else "b")
                for i in range(8)]
        result = comparison.compare_candidates({"one": rows, "two": copy.deepcopy(rows)},
                                               iterations=300, seed=9)
        self.assertEqual(result["pairwise"][0]["delta_S"], 0.0)
        self.assertEqual(result["pairwise"][0]["interval"], [0.0, 0.0])

    def test_opposing_correlated_rows_stay_in_whole_groups(self):
        # Whole-group draws give deltas -1, 0, +1; row resampling narrows the tails.
        candidates = {
            "left": [row(i, adapted=int(i < 4), group="g1" if i < 4 else "g2") for i in range(8)],
            "right": [row(i, adapted=int(i >= 4), group="g1" if i < 4 else "g2") for i in range(8)],
        }
        result = comparison.compare_candidates(candidates, iterations=500, seed=7)
        self.assertEqual(result["candidates"]["left"]["T"], .5)
        self.assertAlmostEqual(result["candidates"]["left"]["S"], .3)
        self.assertEqual(result["pairwise"][0]["delta_S"], 0.0)
        self.assertEqual(result["pairwise"][0]["interval"], [-1.0, 1.0])

    def test_source_mass_stays_fixed_despite_unequal_group_sizes(self):
        records = [row("a1", source="a", group="one"),
                   row("a2", source="a", group="two"),
                   row("a3", source="a", group="two"),
                   row("b1", source="b", group="one", adapted=0, context={"modality": 0}),
                   row("b2", source="b", group="two", adapted=0, context={"modality": 0})]
        zero = [dict(r, adapted_correct=0, base_correct=0) for r in records]
        result = comparison.compare_candidates({"a": records, "zero": zero}, iterations=100, seed=11)
        # Source a retains 3/5 of total weight; T=C=.6, S=.36 on every draw.
        self.assertAlmostEqual(result["pairwise"][0]["delta_S"], .36)
        for endpoint in result["pairwise"][0]["interval"]:
            self.assertAlmostEqual(endpoint, .36)
        self.assertEqual(result["bootstrap"]["groups_per_source"], {"a": 2, "b": 2})

    def test_context_is_averaged_per_example_not_per_annotated_field(self):
        six_fields = {k: 0 for k in ("modality", "submodality", "specimen", "body_part", "stain", "medical_domain")}
        candidates = {
            "a": [row("1"), row("2", context=six_fields)],
            "b": [row("1", base=1), row("2", base=1, context={k: 1 for k in six_fields})],
        }
        result = comparison.compare_candidates(candidates, iterations=10)
        self.assertEqual(result["candidates"]["a"]["C"], .5)
        self.assertAlmostEqual(result["pairwise"][0]["delta_S"], .9)

    def test_named_weights_follow_record_ids_and_apply_to_every_candidate(self):
        candidates = {
            "a": [row("second", adapted=0), row("first")],
            "b": [row("first", base=1), row("second", base=1)],
        }
        result = comparison.compare_candidates(candidates, weights={"first": 3, "second": 1}, iterations=10)
        self.assertEqual(result["record_ids"], ["first", "second"])
        self.assertEqual(result["normalized_weights"], {"first": .75, "second": .25})
        self.assertEqual(result["weighting"], "record_id_weights")
        self.assertEqual(result["candidates"]["a"]["T"], .75)
        self.assertAlmostEqual(result["pairwise"][0]["delta_S"], .6)

    def test_uniform_weights_are_explicit_and_keep_repeated_group_rows(self):
        records = [row(i, group="same") for i in range(3)]
        result = comparison.compare_candidates({"a": records, "b": copy.deepcopy(records)}, iterations=10)
        self.assertEqual(result["n_examples"], 3)
        self.assertEqual(result["normalized_weights"], {"0": 1 / 3, "1": 1 / 3, "2": 1 / 3})
        self.assertEqual(result["weighting"], "uniform")

    def test_candidate_and_record_order_do_not_change_seeded_results(self):
        candidates = {"z": [row(i, adapted=i % 2) for i in range(6)],
                      "a": [row(i, adapted=int(i > 1), base=int(i == 5)) for i in range(6)]}
        original = copy.deepcopy(candidates)
        reversed_order = {name: list(reversed(rows)) for name, rows in reversed(list(candidates.items()))}
        weights = {str(i): i + 1 for i in range(6)}
        first = comparison.compare_candidates(candidates, weights=weights, iterations=200, seed=44)
        second = comparison.compare_candidates(reversed_order, weights=dict(reversed(list(weights.items()))),
                                                iterations=200, seed=44)
        self.assertEqual(first, second)
        self.assertEqual(first["candidate_names"], ["a", "z"])
        self.assertEqual(candidates, original)

    def test_every_pair_is_reported_in_stable_order_without_winner_claim(self):
        records = [row("one"), row("two")]
        result = comparison.compare_candidates({"c": records, "a": records, "b": records}, iterations=10)
        self.assertEqual([(p["left"], p["right"]) for p in result["pairwise"]],
                         [("a", "b"), ("a", "c"), ("b", "c")])
        self.assertFalse(result["official_evaluation"])
        self.assertEqual(result["inference"], "exploratory_pairwise_comparison")
        self.assertFalse(result["bootstrap"]["multiplicity_adjusted"])
        self.assertNotIn("winner", result)

    def test_one_underpowered_source_withholds_every_pairwise_interval(self):
        records = [row("a1", source="a", group="only"), row("a2", source="a", group="only"),
                   row("b1", source="b"), row("b2", source="b")]
        result = comparison.compare_candidates({"one": records, "two": copy.deepcopy(records)}, iterations=10)
        self.assertIsNone(result["pairwise"][0]["interval"])
        self.assertEqual(result["candidates"]["one"]["S"], 1.0)
        self.assertTrue(any("fewer than two" in warning for warning in result["warnings"]))

    def test_few_groups_and_draws_are_flagged_as_exploratory(self):
        records = [row("one"), row("two")]
        result = comparison.compare_candidates({"one": records, "two": records}, iterations=10)
        self.assertTrue(any("Few groups" in warning for warning in result["warnings"]))
        self.assertTrue(any("Few bootstrap draws" in warning for warning in result["warnings"]))

    def test_at_least_two_nonblank_candidate_names_are_required(self):
        records = [row("one"), row("two")]
        for candidates in ({}, {"a": records}, {"": records, "b": records},
                           {1: records, "b": records}, [records, records], None):
            with self.subTest(candidates=candidates), self.assertRaises(ValueError):
                comparison.compare_candidates(candidates, iterations=10)

    def test_missing_or_extra_record_ids_fail_instead_of_intersecting(self):
        records = [row("one"), row("two")]
        for other in ([row("one")], [row("one"), row("two"), row("extra")], [row("one"), row("different")]):
            with self.subTest(other=other), self.assertRaises(ValueError):
                comparison.compare_candidates({"a": records, "b": other}, iterations=10)

    def test_duplicate_record_with_conflicting_baseline_is_rejected(self):
        records = [row("one"), row("two")]
        with self.assertRaises(ValueError):
            comparison.compare_candidates({"a": records, "b": [row("one"), row("one", base=1)]}, iterations=10)

    def test_source_group_task_and_context_field_coverage_must_align_per_record(self):
        records = [row("one"), row("two")]
        for change in ({"source_id": "other"}, {"group_id": "different"}, {"task": "counting"},
                       {"context_correct": {"stain": 1}}, {"context_correct": {"modality": 1, "stain": 0}}):
            other = copy.deepcopy(records)
            other[1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                comparison.compare_candidates({"a": records, "b": other}, iterations=10)

    def test_invalid_or_missing_grades_and_zero_fields_reuse_metric_validation(self):
        records = [row("one"), row("two")]
        for change in ({"base_correct": None}, {"adapted_correct": math.nan}, {"context_correct": {}},
                       {"context_correct": {"modality": .5}}, {"adapted_correct": 10**400}):
            other = copy.deepcopy(records)
            other[1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                comparison.compare_candidates({"a": records, "b": other}, iterations=10)

    def test_weights_must_name_exactly_the_aligned_ids_and_remain_positive(self):
        records = [row("one"), row("two")]
        for weights in ([], {"one": 1}, {"one": 1, "two": 1, "extra": 1}, {"one": 1, "missing": 1},
                        {"one": 1, "two": 0}, {"one": 1, "two": True}, {"one": math.nan, "two": 1},
                        {"one": math.inf, "two": 1}, {"one": 1e-300, "two": 1e300}):
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                comparison.compare_candidates({"a": records, "b": records}, weights=weights, iterations=10)

    def test_finite_large_weights_are_normalized_consistently(self):
        records = [row("one"), row("two", adapted=0)]
        result = comparison.compare_candidates({"a": records, "b": records},
                                               weights={"one": 1e308, "two": 1e308}, iterations=10)
        self.assertEqual(result["normalized_weights"], {"one": .5, "two": .5})
        self.assertEqual(result["pairwise"][0]["interval"], [0.0, 0.0])

    def test_bootstrap_configuration_rejects_invalid_values(self):
        records = [row("one"), row("two")]
        for kwargs in ({"iterations": 0}, {"iterations": True}, {"iterations": 1.5}, {"seed": True},
                       {"seed": "1"}, {"confidence": 0}, {"confidence": 1}, {"confidence": math.nan},
                       {"confidence": math.inf}, {"confidence": 10**400}, {"confidence": True}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                comparison.compare_candidates({"a": records, "b": records}, **kwargs)


if __name__ == "__main__":
    unittest.main()
