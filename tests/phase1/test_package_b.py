"""Package B synthetic lattice and exposure conformance tests; no biomedical inputs."""

from collections import Counter
from fractions import Fraction
import unittest

try:
    from mmbu_phase1 import exposure, lattice
except ImportError:
    exposure = lattice = None
from mmbu_phase1.fields import ContractViolation


class PackageModuleTests(unittest.TestCase):
    def test_package_b_modules_exist(self):
        self.assertIsNotNone(lattice, "Package B lattice module is missing")
        self.assertIsNotNone(exposure, "Package B exposure module is missing")


@unittest.skipIf(lattice is None, "Package B module not implemented")
class LatticeGeometryTests(unittest.TestCase):
    def test_mask_tight_box_uses_half_open_original_pixels(self):
        self.assertEqual(lattice.mask_to_tight_xywh([[1]], 1, 1), [0, 0, 1, 1])
        self.assertEqual(lattice.mask_to_tight_xywh([[0, 0, 0], [0, 1, 1]], 3, 2), [1, 1, 2, 1])
        self.assertEqual(lattice.mask_to_tight_xywh([[1, 0, 0], [0, 0, 1]], 3, 2), [0, 0, 3, 2])
        for invalid in ([], [[0]], [[1, 0], [1]], [[False]], [[2]]):
            with self.subTest(invalid=invalid), self.assertRaises(ContractViolation):
                lattice.mask_to_tight_xywh(invalid, 1 if invalid != [[1, 0], [1]] else 2,
                                           1 if invalid != [[1, 0], [1]] else 2)

    def test_source_box_round_trips_without_normalization_or_repair(self):
        xywh = lattice.parse_source_box([2, 3, 4, 5], "xywh_half_open", 10, 10)
        self.assertEqual(xywh, [2, 3, 4, 5])
        self.assertEqual(lattice.serialize_source_box(xywh, "xywh_half_open", 10, 10), [2, 3, 4, 5])
        converted = lattice.parse_source_box([2, 3, 6, 8], "xyxy_half_open", 10, 10)
        self.assertEqual(converted, [2, 3, 4, 5])
        self.assertEqual(lattice.serialize_source_box(converted, "xyxy_half_open", 10, 10), [2, 3, 6, 8])
        for box, convention in (([0.1, 0.1, 0.2, 0.2], "normalized_xywh"),
                                ([8, 8, 4, 4], "xywh_half_open"), ([6, 8, 2, 3], "xyxy_half_open")):
            with self.subTest(box=box), self.assertRaises(ContractViolation):
                lattice.parse_source_box(box, convention, 10, 10)


@unittest.skipIf(lattice is None, "Package B module not implemented")
class LatticeViewTests(unittest.TestCase):
    def unit(self):
        return {
            "atom_ids": ["atom-class", "atom-box", "atom-mask", "atom-instances"],
            "image_height": 2,
            "image_width": 3,
            "independent_unit_id": "unit-1",
            "instance_ids": ["i1", "i2"],
            "instance_set_complete": True,
            "mask": [[1, 0, 0], [0, 1, 0]],
            "origin_class": "synthetic_engineering",
            "ontology": {"cell-a": ["Cell A", "A cell"], "cell-b": ["Cell B"]},
            "source_box": [0, 0, 2, 2],
            "source_box_convention": "xywh_half_open",
            "source_id": "synthetic-source",
            "source_label_id": "cell-a",
            "source_term": "Cell A",
            "split": "train",
            "split_group_id": "group-1",
        }

    def test_class_box_mask_localization_and_count_views_share_lineage(self):
        views = lattice.derive_views(self.unit())
        self.assertEqual({v["task_form"] for v in views}, {
            "ungrounded_classification", "box_grounded_classification", "mask_grounded_classification",
            "mask_localization", "box_localization", "counting",
        })
        self.assertTrue(all(v["independent_unit_id"] == "unit-1" and v["split"] == "train" for v in views))
        self.assertTrue(all(v.get("target_source_id") == "cell-a" for v in views
                            if "classification" in v["task_form"]))
        self.assertEqual(next(v["grounding"] for v in views
                              if v["task_form"] == "box_grounded_classification"),
                         {"kind": "box", "xywh": [0, 0, 2, 2]})
        self.assertEqual(next(v["grounding"] for v in views
                              if v["task_form"] == "mask_grounded_classification"),
                         {"kind": "mask", "mask": [[1, 0, 0], [0, 1, 0]]})
        self.assertEqual(next(v["target"] for v in views if v["task_form"] == "mask_localization"), [0, 0, 2, 2])
        self.assertEqual(next(v["target"] for v in views if v["task_form"] == "counting"), 2)

    def test_incomplete_counts_label_invention_and_public_inputs_fail_closed(self):
        for change in ({"instance_set_complete": False}, {"source_term": "invented"},
                       {"source_label_id": "cell-unknown"},
                       {"origin_class": "mmbu_official"}, {"atom_ids": []}):
            unit = {**self.unit(), **change}
            with self.subTest(change=change), self.assertRaises(ContractViolation):
                lattice.derive_views(unit)

    def test_open_closed_ontology_round_trip_and_seeded_permutation(self):
        ontology = {"cell-a": ["Cell A", "A cell"], "cell-b": ["Cell B"], "cell-c": ["Cell C"]}
        self.assertEqual(lattice.normalize_term(" a CELL ", ontology), "cell-a")
        first = lattice.closed_options("cell-a", ontology, "view-7")
        self.assertEqual(first, lattice.closed_options("cell-a", ontology, "view-7"))
        self.assertEqual(Counter(first["option_ids"]), Counter(ontology.keys()))
        self.assertEqual(first["option_ids"][first["correct_index"]], "cell-a")
        with self.assertRaises(ContractViolation):
            lattice.normalize_term("unknown", ontology)
        with self.assertRaises(ContractViolation):
            lattice.closed_options("cell-a", {"cell-a": ["same"], "cell-b": [" SAME "]}, "view-7")

    def test_split_before_expansion_rejects_group_and_lineage_crossing(self):
        good = lattice.derive_views(self.unit())
        lattice.validate_split_isolation(good)
        crossing = good + [{**good[0], "view_id": "cross", "split": "validation"}]
        with self.assertRaises(ContractViolation):
            lattice.validate_split_isolation(crossing)
        duplicate = good + [{**good[0], "view_id": "duplicate"}]
        with self.assertRaises(ContractViolation):
            lattice.validate_split_isolation(duplicate)
        missing = [{k: v for k, v in good[0].items() if k != "atom_ids"}]
        with self.assertRaises(ContractViolation):
            lattice.validate_split_isolation(missing)


def row(unit, endpoint, view, tokens, share, target, *, fields=(), accepted=True, reason=None,
        endpoint_share=Fraction(1)):
    return {
        "accepted": accepted,
        "base_unit_mass": Fraction(1),
        "effective_unit_mass": Fraction(1),
        "endpoint_id": endpoint,
        "endpoint_share": endpoint_share,
        "independent_unit_id": unit,
        "prospective_balance_multiplier": Fraction(1),
        "rejection_reason": reason,
        "requested_context_fields": list(fields),
        "source_family_id": "syn-family",
        "split_group_id": f"group-{unit}",
        "supervised_token_count": tokens,
        "target_bytes": target,
        "task_form": "synthetic",
        "token_normalization_id": "uniform_within_view_v1",
        "schedule_position_or_epoch_rule": "one_complete_cycle_v1",
        "unit_total_mass": Fraction(1),
        "view_id": view,
        "view_share": share,
    }


@unittest.skipIf(exposure is None, "Package B module not implemented")
class ExposureAuditTests(unittest.TestCase):
    def test_annotation_density_context_fields_and_target_length_preserve_unit_mass(self):
        rows = [
            row("u1", "task", "u1-v1", 1, Fraction(1), b"a"),
            *[row("u2", "task", f"u2-v{i}", n, Fraction(1, 4), b"x" * n)
              for i, n in enumerate((1, 2, 5, 12), 1)],
            row("u3", "context", "u3-c1", 3, Fraction(1), b"ctx", fields=("f1",)),
            *[row("u4", "context", f"u4-c{i}", 2, Fraction(1, 6), f"f{i}".encode(), fields=(f"f{i}",))
              for i in range(1, 7)],
        ]
        report = exposure.audit_rows(rows)
        self.assertEqual(report["unit_mass"], {"u1": Fraction(1), "u2": Fraction(1),
                                               "u3": Fraction(1), "u4": Fraction(1)})
        self.assertEqual(report["token_mass"]["u2"], Fraction(1))
        self.assertEqual(report["context_mass"], {"u3": Fraction(1), "u4": Fraction(1)})
        self.assertEqual(sum(mass for (unit, _), mass in report["context_field_mass"].items()
                             if unit == "u4"), Fraction(1))

    def test_closed_manifest_and_endpoint_partition_fail_closed(self):
        valid = row("u1", "task", "v1", 1, Fraction(1), b"a")
        with self.assertRaises(ContractViolation):
            exposure.audit_rows([{key: value for key, value in valid.items()
                                  if key != "token_normalization_id"}])
        with self.assertRaises(ContractViolation):
            exposure.audit_rows([{**valid, "endpoint_share": Fraction(1, 2)}])
        with self.assertRaises(ContractViolation):
            exposure.audit_rows([{**valid, "requested_context_fields": ["f1"]}])
        context = row("u1", "context", "c1", 1, Fraction(1), b"a", fields=("f1", "f1"))
        with self.assertRaises(ContractViolation):
            exposure.audit_rows([context])

    def test_microbatch_and_distributed_aggregation_use_global_numerator_denominator(self):
        left = [(Fraction(1), Fraction(1)), (Fraction(3), Fraction(1))]
        right = [(Fraction(9), Fraction(6))]
        reference = exposure.weighted_loss(left + right)
        self.assertEqual(reference, Fraction(29, 4))
        self.assertEqual(exposure.combine_partials([exposure.partial(left), exposure.partial(right)]), reference)
        self.assertNotEqual((exposure.weighted_loss(left) + exposure.weighted_loss(right)) / 2, reference)
        with self.assertRaises(ContractViolation):
            exposure.weighted_loss([])

    def test_drop_last_invalid_view_and_candidate_population_drift_reject(self):
        full = [row("u1", "task", "v1", 1, Fraction(1), b"a"),
                row("u2", "task", "v2", 1, Fraction(1), b"b")]
        exposure.compare_candidates({"base": full, "adapted": list(full)})
        for bad in ([full[0]], [full[0], {**full[1], "accepted": False, "rejection_reason": "invalid"}]):
            with self.subTest(bad=bad), self.assertRaises(ContractViolation):
                exposure.compare_candidates({"base": full, "adapted": bad})
        with self.assertRaises(ContractViolation):
            exposure.audit_rows([{**full[0], "accepted": False, "rejection_reason": None}])
        with self.assertRaises(ContractViolation):
            exposure.audit_rows([{**full[0], "target_bytes": b"\xff"}])
        with self.assertRaises(ContractViolation):
            exposure.audit_rows(full + [{**full[0], "accepted": False,
                                         "rejection_reason": "duplicate invalid row"}])
        exposure.compare_candidates({
            "tokenizer-a": full,
            "tokenizer-b": [{**full[0], "supervised_token_count": 3},
                            {**full[1], "supervised_token_count": 2}],
        })
        with self.assertRaises(ContractViolation):
            exposure.compare_candidates({
                "base": full,
                "drifted": [{**full[0], "source_family_id": "other-family"}, full[1]],
            })

    def test_schedule_multisets_early_stop_and_resume_are_exact(self):
        cycle = [row("u1", "task", "v1", 1, Fraction(1), b"a"),
                 row("u2", "task", "v2", 2, Fraction(1), b"bb")]
        variants = {"static": cycle, "forward": cycle, "reverse": list(reversed(cycle)),
                    "shuffled": [cycle[1], cycle[0]]}
        exposure.validate_schedules(variants, cycle_length=2)
        self.assertEqual(exposure.eligible_stop_boundaries(6, 2), [2, 4, 6])
        doubled = cycle * 2
        exposure.validate_schedules({"static": doubled, "reverse": list(reversed(cycle)) * 2}, cycle_length=2)
        self.assertEqual(exposure.resume_sequence(doubled, 3, doubled[:3]), [cycle[1]])
        with self.assertRaises(ContractViolation):
            exposure.resume_sequence(doubled, 3, doubled[:2])
        bad = {**variants, "forward": [{**cycle[0], "target_bytes": b"changed"}, cycle[1]]}
        with self.assertRaises(ContractViolation):
            exposure.validate_schedules(bad, cycle_length=2)
        with self.assertRaises(ContractViolation):
            exposure.resume_sequence(cycle, 3, cycle)


if __name__ == "__main__":
    unittest.main()
