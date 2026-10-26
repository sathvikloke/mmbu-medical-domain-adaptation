"""Closed tests for deterministic BUSI-WHU clinical-review selection."""

from __future__ import annotations

import copy
import csv
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from mmbu_phase1 import canonical
from mmbu_phase1.busi_whu_review import build_review_packet, build_review_selection
from mmbu_phase1.busi_whu_review_validation import validate_completed_review


def metadata_inventory() -> dict:
    records = []
    for index in range(560):
        records.append({
            "label_code": "0",
            "parent_id": f"busi-whu:patient:b{index:04d}",
            "record_id": f"b{index:04d}",
            "row_digest": f"{index + 1:064x}",
            "workbook_row": index + 2,
        })
    for index in range(218):
        records.append({
            "label_code": "1",
            "parent_id": f"busi-whu:patient:m{index:04d}",
            "record_id": f"m{index:04d}",
            "row_digest": f"{index + 1001:064x}",
            "workbook_row": index + 562,
        })
    sizes = [2] * 15 + [3] * 4 + [4] * 6 + [5] * 5 + [6] * 2 + [7] * 3 + [8] * 2 + [9]
    row = 780
    for patient_index, size in enumerate(sizes):
        for record_index in range(size):
            records.append({
                "label_code": "1",
                "parent_id": f"busi-whu:patient:x{patient_index:02d}",
                "record_id": f"x{patient_index:02d}-{record_index}",
                "row_digest": f"{row + 2001:064x}",
                "workbook_row": row + 2,
            })
            row += 1
    records.sort(key=lambda item: item["record_id"])
    return canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_patient_join_inventory",
        "schema_version": 1,
        "artifact_name": "Patient_infos_BUSI-WHU.xlsx",
        "sheet_name": "Sheet1",
        "records": records,
        "record_count": 927,
        "patient_count": 816,
        "label_counts": {"0": 560, "1": 367},
        "image_member_join_complete": True,
        "annotation_member_join_complete": True,
        "label_values_read": True,
        "image_payload_decoding_used": False,
        "annotation_payload_decoding_used": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def bmp(width=2, height=2, rows=None) -> bytes:
    """Create a tiny uncompressed 8-bit grayscale BMP without Pillow."""
    if rows is None:
        rows = [[0, 255], [255, 0]]
    stride = (width + 3) & ~3
    pixels = b"".join(bytes(row) + b"\0" * (stride - width) for row in reversed(rows))
    palette = b"".join(bytes((value, value, value, 0)) for value in range(256))
    offset = 14 + 40 + len(palette)
    size = offset + len(pixels)
    return (
        b"BM"
        + struct.pack("<IHHI", size, 0, 0, offset)
        + struct.pack("<IiiHHIIiiII", 40, width, height, 1, 8, 0, len(pixels), 0, 0, 256, 0)
        + palette
        + pixels
    )


def packet_fixture(root: Path, *, changed_image=None, changed_mask=None):
    inventory = metadata_inventory()
    selection = build_review_selection(inventory)
    archive = root / "BUSI-WHU.zip"
    image = bmp()
    mask = bmp(rows=[[0, 255], [0, 0]])
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as stream:
        stream.writestr("img/", b"")
        stream.writestr("gt/", b"")
        for row in inventory["records"]:
            record_id = row["record_id"]
            stream.writestr(
                f"img/{record_id}.bmp",
                changed_image[1] if changed_image and changed_image[0] == record_id else image,
            )
            stream.writestr(
                f"gt/{record_id}_anno.bmp",
                changed_mask[1] if changed_mask and changed_mask[0] == record_id else mask,
            )
    workbook = root / "Patient_infos_BUSI-WHU.xlsx"
    workbook.write_bytes(b"synthetic-workbook-identity")
    return archive, workbook, inventory, selection


class BusiWhuReviewSelectionTests(unittest.TestCase):
    def test_exact_population_freezes_primary_and_enriched_secondary_review(self):
        source = metadata_inventory()
        result = build_review_selection(source)
        self.assertEqual(result["primary_record_count"], 927)
        self.assertEqual(result["primary_patient_count"], 816)
        self.assertEqual(result["secondary_record_count"], 249)
        self.assertEqual(result["secondary_patient_count"], 138)
        self.assertEqual(result["mandatory_multi_record_patient_count"], 38)
        self.assertEqual(result["mandatory_multi_record_count"], 149)
        self.assertEqual(result["singleton_patient_counts"], {"0": 560, "1": 218})
        self.assertEqual(result["selected_singleton_patient_counts"], {"0": 50, "1": 50})
        self.assertEqual(len(result["primary_record_ids"]), 927)
        self.assertEqual(len(result["secondary_record_ids"]), 249)
        self.assertEqual(len(result["secondary_patient_ids"]), 138)
        self.assertFalse(result["source_admission_authorized"])
        self.assertFalse(result["training_ready"])
        self.assertFalse(result["model_use_authorized"])

        by_patient = {}
        for record in source["records"]:
            by_patient.setdefault(record["parent_id"], []).append(record["record_id"])
        for patient_id, record_ids in by_patient.items():
            if len(record_ids) > 1:
                self.assertTrue(set(record_ids).issubset(result["secondary_record_ids"]))
        for label, prefix in (("0", "b"), ("1", "m")):
            candidates = [f"busi-whu:patient:{prefix}{index:04d}" for index in range(560 if label == "0" else 218)]
            expected = sorted(candidates, key=lambda patient_id: (
                hashlib.sha256(b"busi-whu-review-v1\0" + patient_id.encode("utf-8")).digest(),
                patient_id.encode("utf-8"),
            ))[:50]
            selected = [patient_id for patient_id in result["selected_singleton_patient_ids"] if patient_id.startswith(f"busi-whu:patient:{prefix}")]
            self.assertEqual(selected, sorted(expected))

    def test_selection_ids_are_order_invariant_but_predecessor_binding_changes(self):
        source = metadata_inventory()
        changed = copy.deepcopy(source)
        changed["records"] = list(reversed(changed["records"]))
        changed["record_digest"] = canonical.record_digest(changed)
        first = build_review_selection(source)
        second = build_review_selection(changed)
        self.assertEqual(first["primary_record_ids"], second["primary_record_ids"])
        self.assertEqual(first["secondary_record_ids"], second["secondary_record_ids"])
        self.assertNotEqual(first["source_inventory_digest"], second["source_inventory_digest"])
        self.assertNotEqual(first["record_digest"], second["record_digest"])

    def test_conflicting_patient_labels_and_population_drift_reject(self):
        source = metadata_inventory()
        conflicting = copy.deepcopy(source)
        patient_id = "busi-whu:patient:x00"
        patient_rows = [row for row in conflicting["records"] if row["parent_id"] == patient_id]
        patient_rows[0]["label_code"] = "0"
        conflicting["record_digest"] = canonical.record_digest(conflicting)
        with self.assertRaises(ValueError):
            build_review_selection(conflicting)

        missing = copy.deepcopy(source)
        missing["records"].pop()
        missing["record_count"] = 926
        missing["record_digest"] = canonical.record_digest(missing)
        with self.assertRaises(ValueError):
            build_review_selection(missing)


class BusiWhuReviewPacketTests(unittest.TestCase):
    def test_packet_closes_full_decode_inventory_and_authority(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive, workbook, inventory, selection = packet_fixture(root)
            output = root / "packet"
            receipt = build_review_packet(archive, workbook, inventory, selection, output)
            manifest = json.loads((output / "review-manifest.json").read_text())
            decode = json.loads((output / "decode-inventory.json").read_text())
            duplicates = json.loads((output / "duplicate-candidates.json").read_text())
            self.assertEqual(manifest["record_count"], 927)
            self.assertEqual(decode["record_count"], 927)
            self.assertEqual(decode["decoded_image_count"], 927)
            self.assertEqual(decode["decoded_annotation_count"], 927)
            self.assertEqual(len(duplicates["exact_image_groups"]), 1)
            self.assertEqual(len(duplicates["exact_image_groups"][0]["record_ids"]), 927)
            self.assertTrue(duplicates["exact_image_groups"][0]["cross_patient"])
            self.assertEqual(len(duplicates["perceptual_image_groups"]), 1)
            self.assertTrue((output / "primary-review.csv").is_file())
            self.assertTrue((output / "secondary-review.csv").is_file())
            self.assertFalse(receipt["source_admission_authorized"])
            self.assertFalse(receipt["training_ready"])
            self.assertFalse(receipt["model_use_authorized"])
            self.assertFalse(receipt["mmbu_public_content_used"])

    def test_dimension_mismatch_rejects_without_publishing(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive, workbook, inventory, selection = packet_fixture(
                root, changed_image=("b0000", bmp(3, 2, [[0, 1, 2], [3, 4, 5]]))
            )
            output = root / "packet"
            with self.assertRaisesRegex(ValueError, "dimensions"):
                build_review_packet(archive, workbook, inventory, selection, output)
            self.assertFalse(output.exists())

    def test_nonbinary_and_empty_annotations_reject(self):
        for name, mask in (
            ("nonbinary", bmp(rows=[[0, 127], [0, 0]])),
            ("empty", bmp(rows=[[0, 0], [0, 0]])),
        ):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                archive, workbook, inventory, selection = packet_fixture(
                    root, changed_mask=("b0000", mask)
                )
                output = root / "packet"
                with self.assertRaises(ValueError):
                    build_review_packet(archive, workbook, inventory, selection, output)
                self.assertFalse(output.exists())

    def test_existing_output_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive, workbook, inventory, selection = packet_fixture(root)
            output = root / "packet"
            output.mkdir()
            sentinel = output / "sentinel"
            sentinel.write_text("keep", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                build_review_packet(archive, workbook, inventory, selection, output)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")


TASKS = "global_classification|grounded_classification|localization|context_prediction"


class BusiWhuCompletedReviewTests(unittest.TestCase):
    def completed_fixture(self, root: Path):
        archive, workbook, inventory, selection = packet_fixture(root)
        packet = root / "packet"
        receipt = build_review_packet(archive, workbook, inventory, selection, packet)

        def complete(template_name, reviewer_id, reviewed_at):
            with (packet / template_name).open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
                fields = list(stream.seek(0) or csv.DictReader(stream).fieldnames or [])
            for row in rows:
                row.update({
                    "reviewer_id": reviewer_id,
                    "reviewed_at": reviewed_at,
                    "image_interpretable": "yes",
                    "ultrasound_modality_supported": "yes",
                    "breast_anatomy_supported": "yes",
                    "annotation_usable": "yes",
                    "label_plausible": "yes",
                    "shortcut_artifact": "no",
                    "permitted_tasks": TASKS,
                    "disposition": "eligible",
                    "notes": "independent human review complete",
                })
            path = root / f"completed-{template_name}"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
                writer.writeheader()
                writer.writerows(rows)
            return path, rows, fields

        primary, primary_rows, primary_fields = complete(
            "primary-review.csv", "primary-clinician", "2026-10-25T02:00:00Z"
        )
        secondary, secondary_rows, secondary_fields = complete(
            "secondary-review.csv", "secondary-clinician", "2026-10-25T03:00:00Z"
        )
        opening = {
            "schema_id": "mmbu.phase1.busi_whu_review_opening",
            "schema_version": 1,
            "packet_receipt_digest": receipt["record_digest"],
            "opened_at": "2026-10-25T01:00:00Z",
            "opened_by": "review-coordinator",
            "authorization_evidence_locator": "authority:protected-review-opening",
            "review_opening_authorized": True,
            "reviewers": [
                {
                    "role": "primary", "reviewer_id": "primary-clinician",
                    "qualification": "breast_ultrasound_clinician",
                    "qualification_evidence_locator": "qualification:primary",
                    "conflict_status": "none_declared", "human_attested": True,
                },
                {
                    "role": "secondary", "reviewer_id": "secondary-clinician",
                    "qualification": "breast_ultrasound_clinician",
                    "qualification_evidence_locator": "qualification:secondary",
                    "conflict_status": "none_declared", "human_attested": True,
                },
                {
                    "role": "adjudicator", "reviewer_id": "adjudicator-clinician",
                    "qualification": "breast_ultrasound_clinician",
                    "qualification_evidence_locator": "qualification:adjudicator",
                    "conflict_status": "none_declared", "human_attested": True,
                },
            ],
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        }
        adjudication = {
            "schema_id": "mmbu.phase1.busi_whu_completed_adjudication",
            "schema_version": 1,
            "packet_receipt_digest": receipt["record_digest"],
            "adjudications": [],
            "duplicate_dispositions": [
                {
                    "group_type": group_type,
                    "digest": group[digest_field],
                    "record_ids": group["record_ids"],
                    "primary_reviewer_id": "primary-clinician",
                    "primary_decision": "coassign",
                    "secondary_reviewer_id": "secondary-clinician",
                    "secondary_decision": "coassign",
                    "adjudicator_id": "",
                    "adjudicated_at": "",
                    "final_decision": "coassign",
                    "rationale": "identical synthetic fixture; preserve one split boundary",
                }
                for group_type, digest_field, groups in (
                    ("exact", "decoded_image_sha256", json.loads(
                        (packet / "duplicate-candidates.json").read_text()
                    )["exact_image_groups"]),
                    ("perceptual", "perceptual_hash", json.loads(
                        (packet / "duplicate-candidates.json").read_text()
                    )["perceptual_image_groups"]),
                )
                for group in groups
            ],
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        }
        rights = {
            "schema_id": "mmbu.phase1.busi_whu_rights_purpose_review",
            "schema_version": 1,
            "packet_receipt_digest": receipt["record_digest"],
            "reviewer_id": "team-rights-authority",
            "reviewed_at": "2026-10-25T05:00:00Z",
            "qualification": "team_rights_authority",
            "qualification_evidence_locator": "qualification:rights",
            "conflict_status": "none_declared",
            "human_attested": True,
            "license_identity": "CC BY 4.0",
            "attribution_text": "BUSI-WHU v3, DOI 10.17632/k6cpmwybk3.3",
            "decisions": {
                "confirmation_evaluation": "approve",
                "challenge_reporting": "approve",
                "publication": "approve",
                "source_artifact_redistribution": "decline",
                "trained_weight_release": "unresolved",
                "training": "decline",
            },
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        }
        paths = {}
        for name, value in (("opening", opening), ("adjudication", adjudication), ("rights", rights)):
            path = root / f"{name}.json"
            path.write_bytes(canonical.dumps(value))
            paths[name] = path
        return {
            "packet": packet, "receipt": receipt, "primary": primary, "secondary": secondary,
            "primary_rows": primary_rows, "secondary_rows": secondary_rows,
            "primary_fields": primary_fields, "secondary_fields": secondary_fields,
            "opening_value": opening, "adjudication_value": adjudication, "rights_value": rights,
            **paths,
        }

    @staticmethod
    def rewrite_csv(path, fields, rows):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    @staticmethod
    def rewrite_json(path, value):
        path.write_bytes(canonical.dumps(value))

    def validate(self, fixture):
        return validate_completed_review(
            fixture["packet"], fixture["primary"], fixture["secondary"],
            fixture["adjudication"], fixture["rights"], fixture["opening"],
            expected_packet_receipt_digest=fixture["receipt"]["record_digest"],
        )

    def test_complete_reviews_emit_task_manifests_but_no_authority(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            report = self.validate(fixture)
            self.assertEqual(report["reviewed_record_count"], 927)
            self.assertEqual(report["independently_reviewed_record_count"], 249)
            self.assertEqual(report["eligible_by_task"]["global_classification"]["record_count"], 927)
            self.assertEqual(report["eligible_by_task"]["global_classification"]["patient_count"], 816)
            self.assertTrue(report["confirmation_purposes_ready"])
            self.assertEqual(len(report["duplicate_group_constraints"]), 2)
            self.assertFalse(report["source_admission_authorized"])
            self.assertFalse(report["training_ready"])
            self.assertFalse(report["model_use_authorized"])

    def test_primary_and_frozen_secondary_coverage_are_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            fixture["primary_rows"].pop()
            self.rewrite_csv(fixture["primary"], fixture["primary_fields"], fixture["primary_rows"])
            with self.assertRaisesRegex(ValueError, "primary.*exact"):
                self.validate(fixture)
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            fixture["secondary_rows"].pop()
            self.rewrite_csv(fixture["secondary"], fixture["secondary_fields"], fixture["secondary_rows"])
            with self.assertRaisesRegex(ValueError, "secondary.*exact"):
                self.validate(fixture)

    def test_qualification_and_chronology_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            fixture["opening_value"]["reviewers"][0]["qualification"] = "AI model"
            self.rewrite_json(fixture["opening"], fixture["opening_value"])
            with self.assertRaisesRegex(ValueError, "qualification"):
                self.validate(fixture)
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            fixture["primary_rows"][0]["reviewed_at"] = "2026-10-25T00:00:00Z"
            self.rewrite_csv(fixture["primary"], fixture["primary_fields"], fixture["primary_rows"])
            with self.assertRaisesRegex(ValueError, "after.*opening"):
                self.validate(fixture)

    def test_disagreement_requires_distinct_complete_adjudication(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            record_id = fixture["secondary_rows"][0]["record_id"]
            fixture["secondary_rows"][0]["disposition"] = "excluded"
            fixture["secondary_rows"][0]["permitted_tasks"] = ""
            self.rewrite_csv(fixture["secondary"], fixture["secondary_fields"], fixture["secondary_rows"])
            with self.assertRaisesRegex(ValueError, "adjudication"):
                self.validate(fixture)
            fixture["adjudication_value"]["adjudications"] = [{
                "record_id": record_id,
                "adjudicator_id": "adjudicator-clinician",
                "adjudicated_at": "2026-10-25T04:00:00Z",
                "image_interpretable": "yes", "ultrasound_modality_supported": "yes",
                "breast_anatomy_supported": "yes", "annotation_usable": "yes",
                "label_plausible": "yes", "shortcut_artifact": "no",
                "permitted_tasks": TASKS, "disposition": "eligible",
                "notes": "resolved after independent disagreement review",
            }]
            self.rewrite_json(fixture["adjudication"], fixture["adjudication_value"])
            self.assertIn(record_id, self.validate(fixture)["eligible_by_task"]["localization"]["record_ids"])

    def test_task_narrowing_and_unresolved_exclusion_are_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            record_id = fixture["secondary_rows"][0]["record_id"]
            for rows in (fixture["primary_rows"], fixture["secondary_rows"]):
                row = next(value for value in rows if value["record_id"] == record_id)
                row["annotation_usable"] = "no"
                row["permitted_tasks"] = "global_classification|context_prediction"
                row["disposition"] = "narrow"
            self.rewrite_csv(fixture["primary"], fixture["primary_fields"], fixture["primary_rows"])
            self.rewrite_csv(fixture["secondary"], fixture["secondary_fields"], fixture["secondary_rows"])
            report = self.validate(fixture)
            self.assertIn(record_id, report["eligible_by_task"]["global_classification"]["record_ids"])
            self.assertNotIn(record_id, report["eligible_by_task"]["localization"]["record_ids"])

            for rows in (fixture["primary_rows"], fixture["secondary_rows"]):
                row = next(value for value in rows if value["record_id"] == record_id)
                row["permitted_tasks"] = ""
                row["disposition"] = "unresolved"
            self.rewrite_csv(fixture["primary"], fixture["primary_fields"], fixture["primary_rows"])
            self.rewrite_csv(fixture["secondary"], fixture["secondary_fields"], fixture["secondary_rows"])
            report = self.validate(fixture)
            self.assertIn(record_id, report["excluded_record_ids"])
            self.assertIn(record_id, report["unresolved_record_ids"])

    def test_purpose_decisions_are_separate_and_training_is_never_allowed(self):
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            fixture["rights_value"]["decisions"]["confirmation_evaluation"] = "decline"
            self.rewrite_json(fixture["rights"], fixture["rights_value"])
            report = self.validate(fixture)
            self.assertFalse(report["confirmation_purposes_ready"])
            self.assertIn("confirmation_evaluation_decline", report["source_blockers"])
        with tempfile.TemporaryDirectory() as folder:
            fixture = self.completed_fixture(Path(folder))
            fixture["rights_value"]["decisions"]["training"] = "approve"
            self.rewrite_json(fixture["rights"], fixture["rights_value"])
            with self.assertRaisesRegex(ValueError, "training.*decline"):
                self.validate(fixture)


if __name__ == "__main__":
    unittest.main()
