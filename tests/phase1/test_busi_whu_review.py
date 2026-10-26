"""Closed tests for deterministic BUSI-WHU clinical-review selection."""

from __future__ import annotations

import copy
import hashlib
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.busi_whu_review import build_review_selection


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


if __name__ == "__main__":
    unittest.main()
