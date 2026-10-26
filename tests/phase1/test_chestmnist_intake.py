"""Fail-closed tests for the ChestMNIST public mapping intake."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mmbu_phase1.chestmnist_intake import audit_mapping_bytes


REPO = Path(__file__).resolve().parents[2]
RECEIPT = REPO / "outputs/chestmnist-metadata-audit-2026-10-26/receipt.json"


def _mapping(rows: list[tuple[str, int, str]], header: str = "split,index,image_id") -> bytes:
    body = [header, *(f"{split},{index},{image_id}" for split, index, image_id in rows)]
    return ("\n".join(body) + "\n").encode("utf-8")


class ChestMNISTMappingTests(unittest.TestCase):
    def audit(self, rows: list[tuple[str, int, str]], **overrides):
        expected = {"train": 2, "val": 1, "test": 1}
        expected.update(overrides.pop("expected_split_counts", {}))
        return audit_mapping_bytes(
            _mapping(rows),
            expected_split_counts=expected,
            expected_patient_count=overrides.pop("expected_patient_count", None),
        )

    def test_disjoint_mapping_passes_without_claiming_admission(self):
        result = self.audit(
            [
                ("train", 0, "00000001_001"),
                ("train", 1, "00000001_002"),
                ("val", 0, "00000002_001"),
                ("test", 0, "00000003_001"),
            ],
            expected_patient_count=3,
        )
        self.assertTrue(result["official_split_patient_disjoint"])
        self.assertFalse(result["development_rebuild_required"])
        self.assertEqual(result["cross_split_patient_ids"], [])
        self.assertFalse(result["labels_opened"])
        self.assertFalse(result["pixels_opened"])
        self.assertFalse(result["source_admitted"])
        self.assertFalse(result["mmbu_public_content_used"])

    def test_cross_split_patients_are_reported_deterministically(self):
        result = self.audit(
            [
                ("train", 0, "00000001_001"),
                ("train", 1, "00000002_001"),
                ("val", 0, "00000001_002"),
                ("test", 0, "00000002_002"),
            ],
            expected_patient_count=2,
        )
        self.assertFalse(result["official_split_patient_disjoint"])
        self.assertTrue(result["development_rebuild_required"])
        self.assertEqual(result["cross_split_patient_ids"], ["00000001", "00000002"])
        self.assertEqual(
            result["cross_split_patient_memberships"],
            {"00000001": ["train", "val"], "00000002": ["test", "train"]},
        )

    def test_malformed_or_ambiguous_mapping_rejects(self):
        valid = [
            ("train", 0, "00000001_001"),
            ("train", 1, "00000001_002"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000003_001"),
        ]
        cases = {
            "bom": b"\xef\xbb\xbf" + _mapping(valid),
            "wrong_header": _mapping(valid, "split,image_id,index"),
            "bad_utf8": _mapping(valid) + b"\xff",
            "unknown_split": _mapping([*valid[:-1], ("holdout", 0, "00000003_001")]),
            "index_gap": _mapping([valid[0], ("train", 2, valid[1][2]), *valid[2:]]),
            "duplicate_image": _mapping([*valid[:-1], ("test", 0, valid[0][2])]),
            "bad_image_id": _mapping([*valid[:-1], ("test", 0, "patient-3")]),
            "extra_column": _mapping(valid, "split,index,image_id,surprise"),
        }
        for name, payload in cases.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                audit_mapping_bytes(
                    payload,
                    expected_split_counts={"train": 2, "val": 1, "test": 1},
                )

    def test_wrong_counts_or_patient_count_rejects(self):
        rows = [
            ("train", 0, "00000001_001"),
            ("train", 1, "00000001_002"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000003_001"),
        ]
        with self.assertRaises(ValueError):
            self.audit(rows, expected_split_counts={"train": 3})
        with self.assertRaises(ValueError):
            self.audit(rows, expected_patient_count=4)

    def test_cli_emits_canonical_summary(self):
        rows = [
            ("train", 0, "00000001_001"),
            ("train", 1, "00000001_002"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000003_001"),
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "mapping.csv"
            path.write_bytes(_mapping(rows))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "tools/audit_chestmnist_mapping.py"),
                    "--mapping",
                    str(path),
                    "--train-count",
                    "2",
                    "--val-count",
                    "1",
                    "--test-count",
                    "1",
                    "--patient-count",
                    "3",
                ],
                cwd=REPO,
                check=False,
                capture_output=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        result = json.loads(completed.stdout)
        self.assertEqual(result["row_count"], 4)
        self.assertEqual(result["patient_count"], 3)


class ChestMNISTEvidenceTests(unittest.TestCase):
    def test_real_metadata_receipt_is_exact_and_non_admitting(self):
        receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(receipt["mapping_bytes"], 2_836_941)
        self.assertEqual(
            receipt["mapping_sha256"],
            "3cfe66207037f1f99b1bf457f1f009b0cfc2346ea7a710505a23e02c8ff492e9",
        )
        self.assertEqual(receipt["split_counts"], {"test": 22_433, "train": 78_468, "val": 11_219})
        self.assertEqual(receipt["patient_count"], 30_805)
        self.assertEqual(receipt["cross_split_patient_ids"], ["00005681", "00027864", "00028591"])
        self.assertFalse(receipt["official_split_patient_disjoint"])
        self.assertTrue(receipt["development_rebuild_required"])
        self.assertTrue(receipt["test_mapping_metadata_read"])
        self.assertFalse(receipt["test_labels_opened"])
        self.assertFalse(receipt["test_images_opened"])
        self.assertFalse(receipt["source_admitted"])
        self.assertFalse(receipt["mmbu_public_content_used"])


if __name__ == "__main__":
    unittest.main()
