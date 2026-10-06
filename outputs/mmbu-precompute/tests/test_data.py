"""Behavioral checks for provenance gates and leakage-safe split assignment."""
import copy
import hashlib
import importlib
from pathlib import Path
import tempfile
import unittest

try:
    data = importlib.import_module("mmbu_prep.data")
except ModuleNotFoundError:
    data = None


def source(source_id="external-a", **changes):
    value = {
        "source_id": source_id, "source_version": "v1", "source_family": "family-a",
        "source_role": "external", "status": "approved",
        "allowed_purposes": ["engineering", "train", "dev", "confirmation"],
        "evidence": [{"kind": "test-fixture", "note": "Invented test approval; no real rights decision."}],
        "reviewed_by": "unit-test-fixture", "reviewed_at": "2026-10-03",
    }
    value.update(changes)
    return value


def registry(*sources):
    return {"schema_version": 1, "sources": list(sources or [source()])}


def record(record_id="a", **changes):
    value = {
        "schema_version": 1, "record_id": record_id, "source_id": "external-a",
        "source_version": "v1", "source_family": "family-a", "split": "train",
        "image_path": f"images/{record_id}.png",
        "image_sha256": hashlib.sha256(record_id.encode()).hexdigest(),
        "parent_image_sha256": None, "group_id": f"group-{record_id}",
        "task": "global_classification", "question": "Which shape is present?",
        "answer": "square", "context": {"modality": "synthetic test"},
        "annotation_origin": "invented-unit-test", "conversion_version": "test-v1",
        "review_status": "approved", "synthetic": False,
    }
    value.update(changes)
    return value


class ManifestTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(data, "data module is not implemented")

    def assertRejected(self, rows, sources=None, code=None, **kwargs):
        result = data.validate_manifest(rows, sources or registry(), **kwargs)
        self.assertFalse(result["ok"], result)
        self.assertTrue(result["errors"])
        self.assertTrue(all(isinstance(error, dict) and "code" in error for error in result["errors"]))
        if code:
            self.assertIn(code, {error["code"] for error in result["errors"]}, result)
        return result

    def test_approved_external_has_counts_and_honest_limits(self):
        result = data.validate_manifest([record()], registry(), purpose="train")
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["counts"]["records"], 1)
        self.assertEqual(result["counts"]["components"], 1)
        self.assertIn("files_unchecked", {warning["code"] for warning in result["warnings"]})
        self.assertIn("semantic_checks_not_performed", {warning["code"] for warning in result["warnings"]})

    def test_synthetic_engineering_fixture_is_allowed(self):
        fixture_source = source("fixture", source_family="fixture", source_role="synthetic",
                                status="engineering_only", allowed_purposes=["engineering"])
        fixture = record(source_id="fixture", source_family="fixture", split="engineering",
                         synthetic=True, review_status="engineering_reviewed")
        self.assertTrue(data.validate_manifest([fixture], registry(fixture_source))["ok"])

    def test_duplicate_record_ids_are_rejected_even_same_split(self):
        self.assertRejected([record(), record()], code="duplicate_record_id")

    def test_missing_id_does_not_get_fabricated(self):
        item = record()
        del item["record_id"]
        self.assertRejected([item], code="missing_field")
        self.assertNotIn("record_id", item)

    def test_missing_provenance_fields_are_rejected(self):
        for field in ("source_version", "parent_image_sha256", "group_id", "annotation_origin", "conversion_version"):
            with self.subTest(field=field):
                item = record()
                del item[field]
                self.assertRejected([item], code="missing_field")

    def test_malformed_record_fields_return_errors(self):
        for field, value in (("record_id", ""), ("group_id", "  "), ("schema_version", True),
                             ("synthetic", "false"), ("context", []), ("answer", None),
                             ("answer", {"bad": float("nan")}), ("question", " "),
                             ("task", "guess"), ("split", "validation"),
                             ("image_sha256", "xyz"), ("parent_image_sha256", "abc")):
            with self.subTest(field=field, value=value):
                self.assertRejected([record(**{field: value})])

    def test_invalid_containers_return_structured_errors(self):
        for rows, sources in ((None, registry()), ({}, registry()), ([None], registry()),
                              ([], {}), ([], {"schema_version": 1, "sources": "bad"}),
                              ([], {"schema_version": 1, "sources": [None]})):
            with self.subTest(rows=rows, sources=sources):
                result = data.validate_manifest(rows, sources)
                self.assertFalse(result["ok"])
                self.assertTrue(result["errors"])

    def test_unknown_source_is_rejected(self):
        self.assertRejected([record(source_id="missing")], code="unknown_source")

    def test_unused_candidates_do_not_block_valid_fixture(self):
        sources = registry(source(), source("candidate", status="candidate", allowed_purposes=[],
                                             evidence=[], reviewed_by=None, reviewed_at=None))
        self.assertTrue(data.validate_manifest([record()], sources)["ok"])

    def test_candidate_and_quarantined_sources_are_ineligible(self):
        for status in ("candidate", "quarantined"):
            with self.subTest(status=status):
                self.assertRejected([record()], registry(source(status=status)), code="source_ineligible")

    def test_source_version_and_family_must_match_registry(self):
        for field in ("source_version", "source_family"):
            with self.subTest(field=field):
                self.assertRejected([record(**{field: "wrong"})], code="source_mismatch")

    def test_duplicate_registry_ids_and_unknown_status_are_rejected(self):
        self.assertRejected([record()], registry(source(), source()), code="duplicate_source_id")
        self.assertRejected([record()], registry(source(status="probably-ok")), code="invalid_source_field")

    def test_approved_source_needs_evidence_and_reviewer(self):
        for field, value in (("evidence", []), ("reviewed_by", ""), ("reviewed_at", None)):
            with self.subTest(field=field):
                self.assertRejected([record()], registry(source(**{field: value})), code="missing_approval_evidence")

    def test_purpose_and_record_split_both_need_permission(self):
        self.assertRejected([record()], registry(source(allowed_purposes=["engineering"])), code="split_not_permitted")
        self.assertRejected([record()], registry(source(allowed_purposes=["train"])), code="purpose_not_permitted")
        self.assertRejected([record()], purpose="training", code="invalid_purpose")

    def test_operational_purpose_requires_exact_record_split(self):
        for purpose in ("train", "dev", "confirmation"):
            for existing in ("engineering", "train", "dev", "confirmation"):
                with self.subTest(purpose=purpose, existing=existing):
                    if purpose == existing:
                        self.assertTrue(data.validate_manifest([record(split=existing)], registry(), purpose=purpose)["ok"])
                    else:
                        self.assertRejected([record(split=existing)], purpose=purpose, code="purpose_split_mismatch")
        official = registry(source(source_role="official", allowed_purposes=["engineering", "official_dev"]))
        self.assertRejected([record(split="engineering")], official, purpose="official_dev", code="purpose_split_mismatch")

    def test_engineering_audit_allows_distinct_existing_splits_but_still_checks_leakage(self):
        rows = [record("a", split="train"), record("b", split="dev"), record("c", split="confirmation")]
        self.assertTrue(data.validate_manifest(rows, registry(), purpose="engineering")["ok"])
        rows[2]["group_id"] = "group-a"
        self.assertRejected(rows, purpose="engineering", code="split_leakage")

    def test_public_validation_has_no_split_gate_bypass_argument(self):
        with self.assertRaises(TypeError):
            data.validate_manifest([record(split="confirmation")], registry(), purpose="train", require_purpose_split=False)

    def test_training_needs_item_approval(self):
        self.assertRejected([record(review_status="pending")], purpose="train", code="record_not_approved")

    def test_engineering_only_must_be_synthetic_and_engineering(self):
        self.assertRejected([record()], registry(source(status="engineering_only")), code="invalid_engineering_source")
        fixture_source = source(source_role="synthetic", status="engineering_only", allowed_purposes=["engineering", "train"])
        self.assertRejected([record(synthetic=True)], registry(fixture_source), code="invalid_engineering_source")

    def test_synthetic_role_and_record_flag_must_agree(self):
        self.assertRejected([record(synthetic=True)], code="synthetic_mismatch")

    def test_synthetic_training_is_forbidden_even_with_approval(self):
        self.assertRejected([record(synthetic=True)], registry(source(source_role="synthetic")),
                            purpose="train", code="synthetic_not_engineering")

    def test_official_source_cannot_be_relabelled_train(self):
        self.assertRejected([record()], registry(source(source_role="official")), purpose="train",
                            code="official_split_forbidden")

    def test_official_dev_requires_official_role(self):
        self.assertRejected([record(split="official_dev")],
                            registry(source(allowed_purposes=["engineering", "official_dev"])),
                            code="official_dev_requires_official")

    def test_official_dev_purpose_also_requires_official_role(self):
        self.assertRejected([record(split="engineering")],
                            registry(source(allowed_purposes=["engineering", "official_dev"])),
                            purpose="official_dev", code="official_dev_requires_official")

    def test_whitespace_answer_is_missing_label(self):
        self.assertRejected([record(answer=" \n\t")], code="invalid_record_field")

    def test_explicit_official_dev_permission_supports_diagnostic_validation(self):
        sources = registry(source(source_role="official", allowed_purposes=["official_dev"]))
        self.assertTrue(data.validate_manifest([record(split="official_dev")], sources,
                                               purpose="official_dev")["ok"])

    def test_duplicate_image_hash_cannot_cross_splits(self):
        self.assertRejected([record(), record("b", image_sha256=record()["image_sha256"], split="dev")],
                            code="split_leakage")

    def test_lineage_is_transitive_through_absent_parent_and_group(self):
        parent = "f" * 64
        rows = [record("a", parent_image_sha256=parent),
                record("b", parent_image_sha256=parent, group_id="shared"),
                record("c", group_id="shared", split="dev")]
        result = self.assertRejected(rows, code="split_leakage")
        leak = next(error for error in result["errors"] if error["code"] == "split_leakage")
        self.assertEqual(leak["record_ids"], ["a", "b", "c"])
        self.assertEqual(result["counts"]["components"], 1)

    def test_parent_hash_links_to_original_across_source_families(self):
        rows = [record(), record("b", source_id="external-b", source_family="family-b", split="dev",
                                 parent_image_sha256=record()["image_sha256"])]
        self.assertRejected(rows, registry(source(), source("external-b", source_family="family-b")),
                            code="split_leakage")

    def test_group_namespace_is_family_not_source_id(self):
        rows = [record(), record("b", source_id="external-b", split="dev", group_id="group-a")]
        self.assertRejected(rows, registry(source(), source("external-b")), code="split_leakage")
        rows[1]["source_family"] = "family-b"
        result = data.validate_manifest(rows, registry(source(), source("external-b", source_family="family-b")))
        self.assertTrue(result["ok"], result)

    def test_paths_reject_absolute_traversal_and_windows_forms_without_root(self):
        for path in ("/tmp/a.png", "../a.png", "images/../../a.png", "C:\\images\\a.png", "images\\a.png", ""):
            with self.subTest(path=path):
                self.assertRejected([record(image_path=path)], code="unsafe_image_path")

    def test_file_hash_is_checked_and_mismatch_is_not_repaired(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "image.bin").write_bytes(b"abc")
            item = record(image_path="image.bin", image_sha256="ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            result = data.validate_manifest([item], registry(), image_root=root)
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["counts"]["files_checked"], 1)
            item["image_sha256"] = "0" * 64
            self.assertRejected([item], image_root=root, code="image_hash_mismatch")
            self.assertEqual(item["image_sha256"], "0" * 64)

    def test_symlink_escape_and_missing_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "root"
            root.mkdir()
            outside = parent / "outside.bin"
            outside.write_bytes(b"abc")
            (root / "escape.bin").symlink_to(outside)
            self.assertRejected([record(image_path="escape.bin")], image_root=root, code="unsafe_image_path")
            self.assertRejected([record(image_path="missing.bin")], image_root=root, code="image_file_error")
            self.assertRejected([record(image_path="root")], image_root=outside, code="invalid_image_root")

    def test_validation_does_not_mutate_caller_data(self):
        rows, sources = [record()], registry()
        before = copy.deepcopy((rows, sources))
        data.validate_manifest(rows, sources)
        self.assertEqual((rows, sources), before)

    def test_empty_manifest_is_not_reported_as_ready(self):
        self.assertRejected([], code="empty_manifest")

    def test_only_canonical_context_fields_with_nonblank_values_are_allowed(self):
        for context in ({"diagnosis": "square"}, {"modality": ""}, {"stain": " \n"},
                        {"body_part": None}, {"specimen": 1}, {"medical_domain": ["x"]}):
            with self.subTest(context=context):
                self.assertRejected([record(context=context)], code="invalid_context")
        accepted = {"modality": "m", "submodality": "s", "specimen": "s", "body_part": "b",
                    "stain": "s", "medical_domain": "m"}
        self.assertTrue(data.validate_manifest([record(context=accepted)], registry())["ok"])
        self.assertTrue(data.validate_manifest([record(context={})], registry())["ok"])

    def test_classification_rejects_missing_or_structured_labels(self):
        for task in ("global_classification", "box_classification"):
            for answer in ({}, [], ["square"], 0, False, " "):
                with self.subTest(task=task, answer=answer):
                    self.assertRejected([record(task=task, answer=answer)], code="invalid_target")

    def test_mask_classification_allows_single_or_multiple_nonblank_labels(self):
        for answer in ("cell", ["cell", "nucleus"]):
            with self.subTest(answer=answer):
                self.assertTrue(data.validate_manifest([record(task="mask_classification", answer=answer)], registry())["ok"])
        for answer in ([], {}, ["cell", ""], ["cell", 2], False):
            with self.subTest(answer=answer):
                self.assertRejected([record(task="mask_classification", answer=answer)], code="invalid_target")

    def test_counting_requires_canonical_nonnegative_integer(self):
        for answer in (0, 4, "0", "42"):
            with self.subTest(answer=answer):
                self.assertTrue(data.validate_manifest([record(task="counting", answer=answer)], registry())["ok"])
        for answer in (-1, 1.0, True, "01", "+1", "-1", "1.0", " 1", "١", [], {}):
            with self.subTest(answer=answer):
                self.assertRejected([record(task="counting", answer=answer)], code="invalid_target")

    def test_detection_supports_one_or_multiple_boxes_without_mutation(self):
        for answer in ([0, 0, 10, 8], [[0, 0, 5, 4], [5, 4, 5, 4]], [0.5, 0.5, 1.5, 1.5]):
            with self.subTest(answer=answer):
                item = record(task="detection", answer=answer, image_width=10, image_height=8)
                before = copy.deepcopy(item)
                self.assertTrue(data.validate_manifest([item], registry())["ok"])
                self.assertEqual(item, before)

    def test_detection_rejects_unsafe_or_ambiguous_geometry(self):
        for answer in ([9, 0, 2, 1], [-1, 0, 1, 1], [0, 0, 0, 1], [0, 0, 1, -1],
                       [0, 0, 1, float("inf")], [False, 0, 1, 1], [0, 0, "1", 1],
                       [], {}, [[0, 0, 1, 1], [9, 0, 2, 1]], [0, 1, 2]):
            with self.subTest(answer=answer):
                self.assertRejected([record(task="detection", answer=answer, image_width=10, image_height=8)],
                                    code="invalid_target")

    def test_detection_needs_positive_finite_image_dimensions(self):
        self.assertRejected([record(task="detection", answer=[0, 0, 1, 1])], code="invalid_target")
        for width, height in ((0, 8), (10, -1), (True, 8), ("10", 8), (10, float("nan"))):
            with self.subTest(width=width, height=height):
                self.assertRejected([record(task="detection", answer=[0, 0, 1, 1], image_width=width, image_height=height)],
                                    code="invalid_target")


class SplitTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(data, "data module is not implemented")
        self.ratios = {"train": .5, "dev": .25, "confirmation": .25}

    def split(self, rows, **changes):
        args = {"registry": registry(), "seed": 23, "ratios": self.ratios}
        args.update(changes)
        return data.assign_splits(rows, **args)

    def test_registry_is_mandatory_for_authorization(self):
        with self.assertRaises(TypeError):
            data.assign_splits([record()], seed=23, ratios=self.ratios)

    def test_candidate_quarantined_unreviewed_synthetic_and_official_cannot_split(self):
        for item, sources in ((record(), registry(source(status="candidate"))),
                              (record(), registry(source(status="quarantined"))),
                              (record(review_status="pending"), registry()),
                              (record(), registry(source(source_role="official"))),
                              (record(synthetic=True), registry(source(source_role="synthetic")))):
            with self.subTest(item=item, sources=sources):
                with self.assertRaises(ValueError):
                    self.split([item], registry=sources)

    def test_all_target_split_permissions_are_required(self):
        with self.assertRaises(ValueError):
            self.split([record()], registry=registry(source(allowed_purposes=["train"])))

    def test_ratios_reject_invalid_totals_values_and_unknown_targets(self):
        for ratios in ({}, {"train": .8}, {"train": 1.1, "dev": -.1},
                       {"train": float("nan")}, {"train": float("inf")},
                       {"train": True}, {"train": "1"}, {"official_dev": 1}, {"engineering": 1}):
            with self.subTest(ratios=ratios):
                with self.assertRaises(ValueError):
                    self.split([record()], ratios=ratios)

    def test_outsized_integer_ratio_rejects_without_overflow(self):
        with self.assertRaises(ValueError):
            self.split([record()], ratios={"train": 10 ** 1000})

    def test_invalid_seed_and_duplicate_ids_are_rejected(self):
        for seed in (True, "23", None, 1.5):
            with self.subTest(seed=seed):
                with self.assertRaises(ValueError):
                    self.split([record()], seed=seed)
        with self.assertRaises(ValueError):
            self.split([record(), record()])

    def test_reordering_records_and_ratio_keys_preserves_assignment(self):
        rows = [record(str(index)) for index in range(40)]
        first = self.split(rows)
        second = self.split(list(reversed(rows)), ratios={"confirmation": .25, "train": .5, "dev": .25})
        self.assertEqual({row["record_id"]: row["split"] for row in first},
                         {row["record_id"]: row["split"] for row in second})
        self.assertEqual([row["record_id"] for row in second], [row["record_id"] for row in reversed(rows)])
        self.assertEqual({row["split"] for row in first}, {"train", "dev", "confirmation"})

    def test_parent_group_component_stays_together(self):
        rows = [record("a", parent_image_sha256="f" * 64),
                record("b", parent_image_sha256="f" * 64, group_id="shared"),
                record("c", group_id="shared")]
        result = self.split(rows)
        self.assertEqual(len({row["split"] for row in result}), 1)

    def test_existing_leakage_is_rejected_instead_of_silently_repaired(self):
        rows = [record(), record("b", split="dev", group_id="group-a")]
        with self.assertRaises(ValueError):
            self.split(rows)

    def test_heldout_records_cannot_be_retired_implicitly_by_assignment(self):
        for existing in ("dev", "confirmation"):
            for target in ("train", "dev", "confirmation"):
                if target == existing:
                    continue
                with self.subTest(existing=existing, target=target):
                    item = record(split=existing)
                    before = copy.deepcopy(item)
                    with self.assertRaisesRegex(ValueError, "protected"):
                        self.split([item], ratios={target: 1})
                    self.assertEqual(item, before)

    def test_heldout_records_reject_mixture_that_could_reassign_them(self):
        for existing in ("dev", "confirmation"):
            with self.subTest(existing=existing):
                with self.assertRaisesRegex(ValueError, "protected"):
                    self.split([record(split=existing)], ratios={existing: .99, "train": .01})

    def test_heldout_records_allow_unchanged_single_target(self):
        for existing in ("dev", "confirmation"):
            with self.subTest(existing=existing):
                item = record(split=existing)
                sources = registry(source(allowed_purposes=[existing]))
                self.assertEqual(self.split([item], registry=sources, ratios={existing: 1, "train": 0}), [item])

    def test_preassignment_engineering_and_train_records_can_receive_new_split(self):
        for existing in ("engineering", "train"):
            for target in ("train", "dev", "confirmation"):
                with self.subTest(existing=existing, target=target):
                    assigned = self.split([record(split=existing)], ratios={target: 1})
                    self.assertEqual(assigned[0]["split"], target)

    def test_zero_ratio_target_is_never_assigned(self):
        result = self.split([record(str(index)) for index in range(20)], ratios={"train": 1, "dev": 0})
        self.assertEqual({row["split"] for row in result}, {"train"})

    def test_returned_records_are_deep_copies(self):
        rows = [record()]
        before = copy.deepcopy(rows)
        result = self.split(rows)
        result[0]["context"]["modality"] = "changed"
        self.assertEqual(rows, before)


if __name__ == "__main__":
    unittest.main()
