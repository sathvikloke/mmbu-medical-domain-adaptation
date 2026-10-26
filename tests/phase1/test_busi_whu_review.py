"""Closed tests for deterministic BUSI-WHU clinical-review selection."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile

from mmbu_phase1 import canonical
from mmbu_phase1.busi_whu_review import build_review_packet, build_review_selection


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


if __name__ == "__main__":
    unittest.main()
