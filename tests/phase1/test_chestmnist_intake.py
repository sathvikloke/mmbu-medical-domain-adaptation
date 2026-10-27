"""Fail-closed tests for the ChestMNIST public mapping intake."""

from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from mmbu_phase1 import canonical
from mmbu_phase1.chestmnist_intake import (
    audit_mapping_bytes,
    compile_official_development_manifest,
    freeze_official_patient_roles,
    reconcile_official_split_bytes,
)


REPO = Path(__file__).resolve().parents[2]
RECEIPT = REPO / "outputs/chestmnist-metadata-audit-2026-10-26/receipt.json"
DEVELOPMENT_EVIDENCE = REPO / "outputs/chestmnist-development-freeze-2026-10-26"


def _mapping(rows: list[tuple[str, int, str]], header: str = "split,index,image_id") -> bytes:
    body = [header, *(f"{split},{index},{image_id}" for split, index, image_id in rows)]
    return ("\n".join(body) + "\n").encode("utf-8")


def _patient_roles(rows: list[tuple[str, str]], header: str = "patient_id,role") -> bytes:
    body = [header, *(f"{patient},{role}" for patient, role in rows)]
    return ("\n".join(body) + "\n").encode("utf-8")


def _official_population_fixture() -> tuple[bytes, bytes]:
    def population(first_patient: int, patient_count: int, image_count: int) -> bytes:
        rows = [f"{patient:08d}_000.png" for patient in range(first_patient, first_patient + patient_count)]
        remaining = image_count - patient_count
        patient = first_patient
        follow_up = 1
        while remaining:
            rows.append(f"{patient:08d}_{follow_up:03d}.png")
            remaining -= 1
            follow_up += 1
            if follow_up == 1000:
                patient += 1
                follow_up = 1
        return ("\n".join(rows) + "\n").encode("utf-8")

    return population(1, 28_008, 86_524), population(50_000, 2_797, 25_596)


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

    def test_official_split_reconciliation_exposes_wrapper_drift(self):
        mapping = _mapping([
            ("train", 0, "00000001_001"),
            ("train", 1, "00000003_001"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000001_002"),
        ])
        result = reconcile_official_split_bytes(
            mapping,
            b"00000001_001.png\n00000001_002.png\n00000002_001.png\n",
            b"00000003_001.png\n",
        )
        self.assertTrue(result["official_split_patient_disjoint"])
        self.assertFalse(result["wrapper_roles_preserve_official_split"])
        self.assertEqual(result["wrapper_by_official_split"]["train"], {"official_test": 1, "official_train_val": 1})
        self.assertEqual(result["wrapper_by_official_split"]["test"], {"official_test": 0, "official_train_val": 1})

    def test_official_split_reconciliation_rejects_overlap_or_unmatched_universe(self):
        mapping = _mapping([
            ("train", 0, "00000001_001"),
            ("train", 1, "00000003_001"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000001_002"),
        ])
        with self.assertRaises(ValueError):
            reconcile_official_split_bytes(mapping, b"00000001_001.png\n", b"00000001_001.png\n")
        with self.assertRaises(ValueError):
            reconcile_official_split_bytes(mapping, b"00000001_001.png\n", b"00000003_001.png\n")

    def test_development_manifest_uses_only_official_train_val_patients(self):
        mapping = _mapping([
            ("train", 0, "00000001_001"),
            ("train", 1, "00000003_001"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000001_002"),
        ])
        result = compile_official_development_manifest(
            mapping,
            b"00000001_001.png\n00000001_002.png\n00000002_001.png\n",
            b"00000003_001.png\n",
            _patient_roles([
                ("00000001", "train"),
                ("00000002", "adaptive_development"),
            ]),
        )
        self.assertEqual(
            result["records"],
            [
                {"image_id": "00000001_001", "patient_id": "00000001", "role": "train", "wrapper_index": 0, "wrapper_split": "train"},
                {"image_id": "00000001_002", "patient_id": "00000001", "role": "train", "wrapper_index": 0, "wrapper_split": "test"},
                {"image_id": "00000002_001", "patient_id": "00000002", "role": "adaptive_development", "wrapper_index": 0, "wrapper_split": "val"},
            ],
        )
        self.assertEqual(result["role_image_counts"], {"adaptive_development": 1, "train": 2})
        self.assertEqual(result["role_patient_counts"], {"adaptive_development": 1, "train": 1})
        self.assertEqual(result["official_test_image_count_excluded"], 1)
        self.assertEqual(result["official_test_patient_count_excluded"], 1)
        self.assertTrue(result["official_test_excluded"])
        self.assertFalse(result["labels_opened"])
        self.assertFalse(result["pixels_opened"])
        self.assertFalse(result["source_admitted"])

    def test_patient_roles_are_frozen_before_labels_or_pixels(self):
        train_val, test = _official_population_fixture()
        roles, receipt = freeze_official_patient_roles(train_val, test)
        rows = roles.decode("utf-8").splitlines()
        self.assertEqual(rows[0], "patient_id,role")
        self.assertEqual(len(rows), 28_009)
        self.assertEqual(rows[1:], sorted(rows[1:]))
        self.assertEqual(sum(row.endswith(",adaptive_development") for row in rows[1:]), 2_801)
        self.assertEqual(sum(row.endswith(",train") for row in rows[1:]), 25_207)
        self.assertEqual(receipt["role_patient_counts"], {"adaptive_development": 2_801, "train": 25_207})
        self.assertEqual(receipt["official_test_patient_count_excluded"], 2_797)
        self.assertEqual(receipt["patient_roles_sha256"], __import__("hashlib").sha256(roles).hexdigest())
        self.assertFalse(receipt["labels_opened"])
        self.assertFalse(receipt["pixels_opened"])
        self.assertFalse(receipt["source_admitted"])
        self.assertFalse(receipt["mmbu_public_content_used"])
        repeated = freeze_official_patient_roles(train_val, test)
        self.assertEqual(repeated, (roles, receipt))

    def test_patient_role_freeze_rejects_wrong_population_or_leakage(self):
        train_val, test = _official_population_fixture()
        cases = [
            (train_val.rsplit(b"\n", 2)[0] + b"\n", test),
            (train_val, test.rsplit(b"\n", 2)[0] + b"\n"),
            (train_val, test + b"00000001_999.png\n"),
        ]
        for changed_train, changed_test in cases:
            with self.assertRaises(ValueError):
                freeze_official_patient_roles(changed_train, changed_test)

    def test_patient_role_freeze_cli_publishes_both_outputs_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            train_val, test = _official_population_fixture()
            (root / "train_val.txt").write_bytes(train_val)
            (root / "test.txt").write_bytes(test)
            roles = root / "roles.csv"
            receipt = root / "receipt.json"
            command = [
                sys.executable,
                str(REPO / "tools/freeze_chestmnist_patient_roles.py"),
                "--official-train-val", str(root / "train_val.txt"),
                "--official-test", str(root / "test.txt"),
                "--roles-output", str(roles),
                "--receipt-output", str(receipt),
            ]
            completed = subprocess.run(command, cwd=REPO, check=False, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr.decode())
            roles_before = roles.read_bytes()
            receipt_before = receipt.read_bytes()
            self.assertEqual(receipt_before, receipt_before.strip() + b"\n")
            self.assertEqual(json.loads(receipt_before)["patient_roles_sha256"], __import__("hashlib").sha256(roles_before).hexdigest())
            repeated = subprocess.run(command, cwd=REPO, check=False, capture_output=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(roles.read_bytes(), roles_before)
            self.assertEqual(receipt.read_bytes(), receipt_before)

    def test_development_manifest_rejects_role_or_population_drift(self):
        mapping = _mapping([
            ("train", 0, "00000001_001"),
            ("train", 1, "00000003_001"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000001_002"),
        ])
        train_val = b"00000001_001.png\n00000001_002.png\n00000002_001.png\n"
        test = b"00000003_001.png\n"
        invalid = {
            "missing_patient": _patient_roles([("00000001", "train")]),
            "official_test_patient": _patient_roles([
                ("00000001", "train"), ("00000002", "adaptive_development"), ("00000003", "train")
            ]),
            "unknown_role": _patient_roles([("00000001", "train"), ("00000002", "confirmation")]),
            "duplicate_patient": _patient_roles([
                ("00000001", "train"), ("00000001", "adaptive_development"), ("00000002", "train")
            ]),
            "empty_role": _patient_roles([("00000001", "train"), ("00000002", "train")]),
            "wrong_header": _patient_roles([("00000001", "train"), ("00000002", "adaptive_development")], "role,patient_id"),
        }
        for name, roles in invalid.items():
            with self.subTest(case=name), self.assertRaises(ValueError):
                compile_official_development_manifest(mapping, train_val, test, roles)

    def test_development_manifest_cli_emits_canonical_file(self):
        mapping = _mapping([
            ("train", 0, "00000001_001"),
            ("train", 1, "00000003_001"),
            ("val", 0, "00000002_001"),
            ("test", 0, "00000001_002"),
        ])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            inputs = {
                "mapping.csv": mapping,
                "train_val.txt": b"00000001_001.png\n00000001_002.png\n00000002_001.png\n",
                "test.txt": b"00000003_001.png\n",
                "patient_roles.csv": _patient_roles([
                    ("00000001", "train"),
                    ("00000002", "adaptive_development"),
                ]),
            }
            for name, payload in inputs.items():
                (root / name).write_bytes(payload)
            output = root / "manifest.json"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(REPO / "tools/compile_chestmnist_development.py"),
                    "--mapping", str(root / "mapping.csv"),
                    "--official-train-val", str(root / "train_val.txt"),
                    "--official-test", str(root / "test.txt"),
                    "--patient-roles", str(root / "patient_roles.csv"),
                    "--output", str(output),
                ],
                cwd=REPO,
                check=False,
                capture_output=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr.decode())
            payload = output.read_bytes()
            self.assertEqual(payload, payload.strip() + b"\n")
            result = json.loads(payload)
            repeated = subprocess.run(
                completed.args,
                cwd=REPO,
                check=False,
                capture_output=True,
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(output.read_bytes(), payload)
        self.assertTrue(result["official_test_excluded"])
        self.assertEqual(len(result["records"]), 3)


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
        official = receipt["official_nih_split_reconciliation"]
        self.assertEqual(official["official_split_counts"], {"test": 25_596, "train_val": 86_524})
        self.assertEqual(official["official_patient_counts"], {"test": 2_797, "train_val": 28_008})
        self.assertTrue(official["official_split_patient_disjoint"])
        self.assertFalse(official["wrapper_roles_preserve_official_split"])
        self.assertEqual(
            official["wrapper_by_official_split"],
            {
                "test": {"official_test": 5_212, "official_train_val": 17_221},
                "train": {"official_test": 17_919, "official_train_val": 60_549},
                "val": {"official_test": 2_465, "official_train_val": 8_754},
            },
        )

    def test_real_development_freeze_is_portable_exact_and_non_admitting(self):
        expected = {
            "mapping-audit.json": "a30d1b2165c7b2207f07989f7759a3d21a2da2f5c3b91a7b2e5684ea46f85c19",
            "patient-roles.csv": "a6c5eb102638c33fd6a88652394e36080e6cfb7ab70d2bd3952cbf0ea7e0613a",
            "patient-role-freeze-receipt.json": "12c8158ce216c64882391e1502dbfa70ecde1397bc7c8d36706f314432fc8177",
            "development-manifest.json": "eefd33a8fcdf8d22900efa1debeaeabd1be5b3296c770ced51e441a32d17343d",
        }
        portable = (DEVELOPMENT_EVIDENCE / "SHA256SUMS.portable").read_text().splitlines()
        self.assertEqual(
            portable,
            [f"{digest}  {name}" for name, digest in expected.items()],
        )
        for name, digest in expected.items():
            self.assertEqual(hashlib.sha256((DEVELOPMENT_EVIDENCE / name).read_bytes()).hexdigest(), digest)

        roles_raw = (DEVELOPMENT_EVIDENCE / "patient-roles.csv").read_bytes()
        receipt = json.loads((DEVELOPMENT_EVIDENCE / "patient-role-freeze-receipt.json").read_bytes())
        manifest = json.loads((DEVELOPMENT_EVIDENCE / "development-manifest.json").read_bytes())
        self.assertEqual(receipt["patient_roles_sha256"], hashlib.sha256(roles_raw).hexdigest())
        self.assertEqual(receipt["record_digest"], canonical.record_digest(receipt))
        self.assertEqual(manifest["record_digest"], canonical.record_digest(manifest))

        role_rows = roles_raw.decode("utf-8").splitlines()
        roles = dict(row.split(",", 1) for row in role_rows[1:])
        self.assertEqual(len(roles), 28_008)
        self.assertEqual(sum(role == "adaptive_development" for role in roles.values()), 2_801)
        self.assertEqual(sum(role == "train" for role in roles.values()), 25_207)
        records = manifest["records"]
        self.assertEqual(len(records), 86_524)
        self.assertEqual(len({row["image_id"] for row in records}), 86_524)
        self.assertEqual(len({(row["wrapper_split"], row["wrapper_index"]) for row in records}), 86_524)
        self.assertEqual({row["patient_id"] for row in records}, set(roles))
        self.assertTrue(all(row["patient_id"] == row["image_id"][:8] for row in records))
        self.assertTrue(all(row["role"] == roles[row["patient_id"]] for row in records))
        self.assertEqual(manifest["role_image_counts"], {"adaptive_development": 8_738, "train": 77_786})
        self.assertEqual(manifest["role_patient_counts"], {"adaptive_development": 2_801, "train": 25_207})
        self.assertEqual(manifest["official_test_image_count_excluded"], 25_596)
        self.assertEqual(manifest["official_test_patient_count_excluded"], 2_797)
        self.assertTrue(manifest["official_test_excluded"])
        for record in (receipt, manifest):
            self.assertFalse(record["labels_opened"])
            self.assertFalse(record["pixels_opened"])
            self.assertFalse(record["source_admitted"])
            self.assertFalse(record["mmbu_public_content_used"])


if __name__ == "__main__":
    unittest.main()
