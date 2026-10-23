import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


def api():
    from tools.busbra_quarantine import build_sample_plan
    return build_sample_plan


HAS_PIL = importlib.util.find_spec("PIL") is not None


FIELDS = ["ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX"]


def metadata(rows, *, extra_fields=()):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS + list(extra_fields), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def row(identifier, case, pathology, birads, *, bbox="[1,2,3,4]", width="20", height="30", **extra):
    value = {
        "ID": identifier,
        "Case": str(case),
        "Histology": "fixture histology",
        "Pathology": pathology,
        "BIRADS": str(birads),
        "Device": "fixture device",
        "Width": width,
        "Height": height,
        "Side": "left",
        "BBOX": bbox,
    }
    value.update(extra)
    return value


class SamplePlanTests(unittest.TestCase):
    def test_selection_is_metadata_bound_stratified_and_patient_unique(self):
        build = api()
        payload = metadata([
            row("bus_0003-l", 3, "malignant", 5),
            row("bus_0001-r", 1, "benign", 4),
            row("bus_0001-l", 1, "benign", 4),
            row("bus_0002-l", 2, "benign", 4),
            row("bus_0003-r", 3, "malignant", 4),
            row("bus_0004-s", 4, "malignant", 4),
        ])

        plan = build(payload)

        self.assertEqual(plan["schema"], "mmbu.busbra.quarantine_sample_plan.v1")
        self.assertEqual(plan["metadata_sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual([x["record_id"] for x in plan["records"]],
                         ["bus_0001-l", "bus_0004-s", "bus_0003-l"])
        self.assertEqual([x["case_id"] for x in plan["records"]], ["1", "4", "3"])
        self.assertEqual(plan["selected_case_count"], 3)
        self.assertEqual(plan["records"][0]["image_member"], "BUSBRA/Images/bus_0001-l.png")
        self.assertEqual(plan["records"][0]["mask_member"], "BUSBRA/Masks/mask_0001-l.png")
        self.assertFalse(plan["biomedical_pixels_opened"])
        self.assertFalse(plan["model_use_authorized"])
        digest_input = dict(plan)
        digest_input.pop("plan_digest")
        encoded = json.dumps(digest_input, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                             allow_nan=False).encode("ascii")
        self.assertEqual(plan["plan_digest"], hashlib.sha256(encoded).hexdigest())

    def test_duplicate_ids_and_cases_that_disagree_fail_closed(self):
        build = api()
        bad = [
            [row("bus_0001-l", 1, "benign", 4), row("bus_0001-l", 1, "benign", 4)],
            [row("bus_0001-l", 1, "benign", 4), row("bus_0001-r", 1, "malignant", 4)],
        ]
        for rows in bad:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                build(metadata(rows))

    def test_unknown_or_validation_fields_cannot_influence_selection(self):
        build = api()
        payload = metadata([row("bus_0001-l", 1, "benign", 4, valid_1="True")], extra_fields=["valid_1"])
        with self.assertRaisesRegex(ValueError, "columns"):
            build(payload)

    def test_malformed_identity_geometry_and_limits_reject(self):
        build = api()
        bad_rows = [
            row("../bus_0001-l", 1, "benign", 4),
            row("bus_0001-l", 2, "benign", 4),
            row("bus_0001-l", 1, "benign", 4, bbox="[19,2,3,4]"),
            row("bus_0001-l", 1, "benign", 4, width="0"),
        ]
        for item in bad_rows:
            with self.subTest(item=item), self.assertRaises(ValueError):
                build(metadata([item]))
        for limit in (0, -1, True, 101):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                build(metadata([row("bus_0001-l", 1, "benign", 4)]), per_stratum=limit)


@unittest.skipUnless(HAS_PIL, "Pillow is an optional image-test dependency")
class QuarantineInspectionTests(unittest.TestCase):
    def test_bbox_iou_uses_y_coordinate_for_bottom_edge(self):
        from tools.busbra_quarantine import _box_iou
        self.assertEqual(_box_iou([4, 10, 2, 3], [3, 9, 3, 4]), 0.5)

    def png(self, mode, values, size=(4, 4)):
        from PIL import Image
        image = Image.new(mode, size)
        image.putdata(values)
        stream = io.BytesIO()
        image.save(stream, format="PNG")
        return stream.getvalue()

    def fixture(self, root, *, changed_metadata=False, dimension_mismatch=False,
                empty_mask=False, rgb_mask=False, valid_unselected=False,
                extra_pixel_member=False, source_dimension_mismatch=False):
        from tools.busbra_quarantine import build_sample_plan
        rows = [
            row("bus_0001-l", 1, "benign", 4, bbox="[1,1,2,2]", width="4", height="4"),
            row("bus_0002-l", 2, "malignant", 5, bbox="[0,0,1,1]", width="4", height="4"),
            row("bus_0003-l", 3, "benign", 4, bbox="[0,0,1,1]", width="4",
                height="5" if source_dimension_mismatch else "4"),
        ]
        frozen = metadata(rows)
        plan = build_sample_plan(frozen)
        archived = metadata(rows[:-1] + ([row("bus_0003-l", 3, "benign", 3, bbox="[0,0,1,1]", width="4", height="4")]
                                             if changed_metadata else [rows[-1]]))
        duplicate_image = self.png("L", list(range(16)))
        image_2 = self.png("L", list(range(16)), size=(5, 4)) if dimension_mismatch else duplicate_image
        mask_1_values = [0, 0, 0, 0, 0, 255, 255, 0, 0, 255, 255, 0, 0, 0, 0, 0]
        mask_2_values = [0] * 16 if empty_mask else [255] + [0] * 15
        if rgb_mask:
            mask_2 = self.png("RGB", [(255, 0, 0)] + [(0, 0, 0)] * 15)
        else:
            mask_2 = self.png("L", mask_2_values)
        archive = root / "BUSBRA.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("BUSBRA/", b"")
            z.writestr("BUSBRA/Images/", b"")
            z.writestr("BUSBRA/Masks/", b"")
            z.writestr("BUSBRA/bus_data.csv", archived)
            z.writestr("BUSBRA/Images/bus_0001-l.png", duplicate_image)
            z.writestr("BUSBRA/Masks/mask_0001-l.png", self.png("L", mask_1_values))
            z.writestr("BUSBRA/Images/bus_0002-l.png", image_2)
            z.writestr("BUSBRA/Masks/mask_0002-l.png", mask_2)
            if valid_unselected:
                z.writestr("BUSBRA/Images/bus_0003-l.png", self.png("L", list(reversed(range(16)))))
                z.writestr("BUSBRA/Masks/mask_0003-l.png", self.png("L", [0, 255] + [0] * 14))
            else:
                z.writestr("BUSBRA/Images/bus_0003-l.png", b"poison-unselected-image")
                z.writestr("BUSBRA/Masks/mask_0003-l.png", b"poison-unselected-mask")
            if extra_pixel_member:
                z.writestr("BUSBRA/Images/bus_9999-l.png", duplicate_image)
        payload = archive.read_bytes()
        return archive, plan, len(payload), hashlib.md5(payload).hexdigest()

    def test_inspection_binds_archive_decodes_geometry_and_reports_sample_duplicates(self):
        from tools.busbra_quarantine import inspect_quarantine
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, plan, size, md5 = self.fixture(root)

            receipt = inspect_quarantine(archive, plan, root / "out", expected_archive_bytes=size,
                                         expected_archive_md5=md5)

            self.assertTrue(receipt["ok"])
            self.assertFalse(receipt["training_ready"])
            self.assertFalse(receipt["model_use_authorized"])
            self.assertEqual(receipt["selected_records"], 2)
            self.assertEqual(receipt["records"][0]["mask_bbox_xywh"], [1, 1, 2, 2])
            self.assertEqual(receipt["records"][0]["bbox_iou"], 1.0)
            self.assertEqual(receipt["records"][0]["mask_values"], [0, 255])
            self.assertEqual(receipt["exact_decoded_duplicate_groups"], [["bus_0001-l", "bus_0002-l"]])
            self.assertFalse(receipt["corpus_duplicate_clearance"])
            self.assertEqual(json.loads((root / "out" / "receipt.json").read_text()), receipt)

    def test_archive_or_metadata_drift_fails_without_publishing(self):
        from tools.busbra_quarantine import inspect_quarantine
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, plan, size, md5 = self.fixture(root, changed_metadata=True)
            cases = [(size + 1, md5, "archive"), (size, "0" * 32, "archive"), (size, md5, "metadata")]
            for index, (wanted_size, wanted_md5, message) in enumerate(cases):
                output = root / f"out-{index}"
                with self.subTest(index=index), self.assertRaisesRegex(ValueError, message):
                    inspect_quarantine(archive, plan, output, expected_archive_bytes=wanted_size,
                                       expected_archive_md5=wanted_md5)
                self.assertFalse(output.exists())

    def test_bad_decoded_structure_fails_without_publishing(self):
        from tools.busbra_quarantine import inspect_quarantine
        options = ("dimension_mismatch", "empty_mask", "rgb_mask")
        for option in options:
            with self.subTest(option=option), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive, plan, size, md5 = self.fixture(root, **{option: True})
                with self.assertRaises(ValueError):
                    inspect_quarantine(archive, plan, root / "out", expected_archive_bytes=size,
                                       expected_archive_md5=md5)
                self.assertFalse((root / "out").exists())

    def test_existing_output_and_tampered_plan_fail_closed(self):
        from tools.busbra_quarantine import inspect_quarantine
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, plan, size, md5 = self.fixture(root)
            (root / "out").mkdir()
            with self.assertRaises(FileExistsError):
                inspect_quarantine(archive, plan, root / "out", expected_archive_bytes=size,
                                   expected_archive_md5=md5)
            tampered = dict(plan)
            tampered["per_stratum"] = 2
            with self.assertRaisesRegex(ValueError, "plan"):
                inspect_quarantine(archive, tampered, root / "fresh", expected_archive_bytes=size,
                                   expected_archive_md5=md5)
            self.assertFalse((root / "fresh").exists())

    def test_corpus_audit_closes_inventory_decodes_every_record_and_reports_collisions(self):
        from tools.busbra_quarantine import audit_corpus
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, _plan, size, md5 = self.fixture(root, valid_unselected=True)

            receipt = audit_corpus(archive, root / "census", expected_archive_bytes=size,
                                   expected_archive_md5=md5)

            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["record_count"], 3)
            self.assertEqual(receipt["case_count"], 3)
            self.assertEqual(receipt["image_mode_counts"], {"L": 3})
            self.assertEqual(receipt["mask_mode_counts"], {"L": 3})
            self.assertEqual(receipt["exact_image_duplicate_groups"], [{
                "case_ids": ["1", "2"],
                "cross_case": True,
                "pathologies": ["benign", "malignant"],
                "record_ids": ["bus_0001-l", "bus_0002-l"],
            }])
            self.assertFalse(receipt["exact_image_duplicate_clearance"])
            self.assertFalse(receipt["near_duplicate_clearance"])
            self.assertFalse(receipt["structural_clearance"])
            self.assertEqual(receipt["bbox_iou_below_0_95_records"], [{
                "bbox_iou": 0.0,
                "mask_bbox_xywh": [1, 0, 1, 1],
                "metadata_bbox_xywh": [0, 0, 1, 1],
                "record_id": "bus_0003-l",
            }])
            self.assertFalse(receipt["training_ready"])
            self.assertFalse(receipt["model_use_authorized"])
            self.assertEqual(json.loads((root / "census/receipt.json").read_text()), receipt)

    def test_corpus_audit_rejects_unlisted_pixels_and_bad_unselected_records(self):
        from tools.busbra_quarantine import audit_corpus
        for options in ({"extra_pixel_member": True, "valid_unselected": True}, {}):
            with self.subTest(options=options), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                archive, _plan, size, md5 = self.fixture(root, **options)
                with self.assertRaises(ValueError):
                    audit_corpus(archive, root / "census", expected_archive_bytes=size,
                                 expected_archive_md5=md5)
                self.assertFalse((root / "census").exists())

    def test_corpus_audit_is_deterministic_and_never_turns_exact_into_near_clearance(self):
        from tools.busbra_quarantine import audit_corpus
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, _plan, size, md5 = self.fixture(root, valid_unselected=True)
            first = audit_corpus(archive, root / "first", expected_archive_bytes=size,
                                 expected_archive_md5=md5)
            second = audit_corpus(archive, root / "second", expected_archive_bytes=size,
                                  expected_archive_md5=md5)
            self.assertEqual(first, second)
            self.assertFalse(first["near_duplicate_clearance"])

    def test_corpus_audit_verifies_and_decodes_the_same_single_open(self):
        from tools.busbra_quarantine import audit_corpus
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, _plan, size, md5 = self.fixture(root, valid_unselected=True)
            original = io.open
            archive_open_count = 0

            def tracked_open(file, *args, **kwargs):
                nonlocal archive_open_count
                if Path(file) == archive.resolve():
                    archive_open_count += 1
                return original(file, *args, **kwargs)

            with mock.patch("io.open", side_effect=tracked_open):
                audit_corpus(archive, root / "census", expected_archive_bytes=size,
                             expected_archive_md5=md5)

            self.assertEqual(archive_open_count, 1)

    def test_corpus_audit_records_metadata_size_errata_when_image_and_mask_agree(self):
        from tools.busbra_quarantine import audit_corpus
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, _plan, size, md5 = self.fixture(
                root, valid_unselected=True, source_dimension_mismatch=True)

            receipt = audit_corpus(archive, root / "census", expected_archive_bytes=size,
                                   expected_archive_md5=md5)

            self.assertEqual(receipt["metadata_dimension_mismatches"], [{
                "actual_height": 4,
                "actual_width": 4,
                "declared_height": 5,
                "declared_width": 4,
                "record_id": "bus_0003-l",
            }])
            self.assertFalse(receipt["metadata_dimension_clearance"])
            self.assertFalse(receipt["training_ready"])

    def test_near_duplicate_triage_binds_fingerprints_and_never_changes_records(self):
        from tools.busbra_quarantine import triage_near_duplicates
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, _plan, size, md5 = self.fixture(root, valid_unselected=True)

            receipt = triage_near_duplicates(
                archive, root / "triage", expected_archive_bytes=size, expected_archive_md5=md5)

            self.assertEqual(receipt["fingerprint_count"], 3)
            self.assertTrue(any(candidate["record_ids"] == ["bus_0001-l", "bus_0002-l"]
                                and candidate["hamming_distance"] == 0
                                and candidate["cross_case"]
                                and candidate["reason"] == "exact_decoded_match"
                                for candidate in receipt["candidates"]))
            fingerprints = (root / "triage/fingerprints.json").read_bytes()
            self.assertEqual(receipt["fingerprints_sha256"], hashlib.sha256(fingerprints).hexdigest())
            self.assertFalse(receipt["automatic_merge_or_exclusion"])
            self.assertFalse(receipt["absence_of_near_duplicates_certified"])
            self.assertFalse(receipt["training_ready"])
            self.assertFalse(receipt["model_use_authorized"])

    def test_near_duplicate_triage_rejects_invalid_thresholds_without_publishing(self):
        from tools.busbra_quarantine import triage_near_duplicates
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive, _plan, size, md5 = self.fixture(root, valid_unselected=True)
            for index, kwargs in enumerate(({"max_distance": True}, {"max_distance": 65},
                                            {"max_aspect_ratio_difference": float("nan")})):
                output = root / f"triage-{index}"
                with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                    triage_near_duplicates(
                        archive, output, expected_archive_bytes=size,
                        expected_archive_md5=md5, **kwargs)
                self.assertFalse(output.exists())


class StandaloneCliTests(unittest.TestCase):
    def run_cli(self, *args):
        script = Path(__file__).resolve().parents[1] / "tools/busbra_quarantine.py"
        return subprocess.run([sys.executable, str(script), *args], text=True, capture_output=True, timeout=30)

    def test_plan_cli_is_json_only_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "bus_data.csv"
            output = root / "plan.json"
            source.write_bytes(metadata([row("bus_0001-l", 1, "benign", 4)]))
            made = self.run_cli("plan", str(source), "--output", str(output))
            self.assertEqual(made.returncode, 0, made.stderr)
            self.assertEqual(json.loads(made.stdout), json.loads(output.read_text()))
            again = self.run_cli("plan", str(source), "--output", str(output))
            self.assertEqual(again.returncode, 2)
            self.assertEqual(json.loads(again.stderr)["command"], "plan")

    @unittest.skipUnless(HAS_PIL, "Pillow is an optional image-test dependency")
    def test_inspect_cli_publishes_closed_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = QuarantineInspectionTests(
                methodName="test_inspection_binds_archive_decodes_geometry_and_reports_sample_duplicates")
            archive, plan, size, md5 = fixture.fixture(root)
            plan_path = root / "plan.json"
            plan_path.write_text(json.dumps(plan))
            out = self.run_cli("inspect", str(archive), str(plan_path), "--output", str(root / "out"),
                               "--expected-archive-bytes", str(size), "--expected-archive-md5", md5)
            self.assertEqual(out.returncode, 0, out.stderr)
            receipt = json.loads(out.stdout)
            self.assertEqual(receipt, json.loads((root / "out/receipt.json").read_text()))
            self.assertFalse(receipt["training_ready"])
            self.assertFalse(receipt["model_use_authorized"])


if __name__ == "__main__":
    unittest.main()
