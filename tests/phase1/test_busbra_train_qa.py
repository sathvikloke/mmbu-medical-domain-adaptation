"""Synthetic conformance tests for the BUS-BRA train-only QA packet."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from mmbu_phase1.busbra_train_qa import build_train_qa_packet


def canonical_digest(value: dict) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("ascii")).hexdigest()


class BusbraTrainQaBuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.predecessor = self.root / "predecessor"
        self.predecessor.mkdir()
        records = []
        definitions = [
            ("bus_0001-l", "1", ["bbox_exception"]),
            ("bus_0845-s", "845", []),
            ("bus_0110-l", "110", ["provenance_pair"]),
            ("bus_0536-r", "536", ["provenance_pair"]),
            ("bus_1001-l", "1001", []),
            ("bus_1002-l", "1002", []),
            ("bus_1002-r", "1002", []),
            ("bus_1003-l", "1003", []),
        ]
        for record_id, case_id, reasons in definitions:
            record_dir = self.predecessor / "assets" / record_id
            record_dir.mkdir(parents=True)
            (record_dir / "image.png").write_bytes(("image:" + record_id).encode())
            (record_dir / "mask.png").write_bytes(("mask:" + record_id).encode())
            records.append({
                "record_id": record_id,
                "case_id": case_id,
                "pathology": "benign",
                "birads": "3",
                "width": 16,
                "height": 12,
                "decoded_width": 16,
                "decoded_height": 12,
                "bbox_xywh": [1, 1, 4, 4],
                "mask_derived_bbox_xywh": [1, 1, 4, 4],
                "image_member": f"BUSBRA/Images/{record_id}.png",
                "mask_member": f"BUSBRA/Masks/{record_id}.png",
                "mandatory_reasons": reasons,
                "image_path": f"assets/{record_id}/image.png",
                "mask_path": f"assets/{record_id}/mask.png",
                "review_status": "pending",
            })
        manifest = {
            "schema": "mmbu.busbra.human_review_packet_manifest.v2",
            "source_id": "busbra",
            "source_version": "1.0",
            "archive_bytes": 1,
            "archive_md5": "0" * 32,
            "metadata_sha256": "1" * 64,
            "stratified_plan_digest": "2" * 64,
            "human_review_plan_digest": "3" * 64,
            "structural_contract_digest": "4" * 64,
            "record_count": len(records),
            "records": records,
            "review_status": "pending_human_review",
            "review_complete": False,
            "training_ready": False,
            "model_use_authorized": False,
        }
        manifest["manifest_digest"] = canonical_digest(manifest)
        (self.predecessor / "review-manifest.json").write_text(
            json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
        )
        members = []
        for path in sorted(p for p in self.predecessor.rglob("*") if p.is_file()):
            payload = path.read_bytes()
            members.append({
                "path": path.relative_to(self.predecessor).as_posix(),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
        receipt = {
            "schema": "mmbu.busbra.human_review_packet_receipt.v2",
            "source_id": "busbra",
            "source_version": "1.0",
            "manifest_digest": manifest["manifest_digest"],
            "record_count": len(records),
            "members": members,
            "review_complete": False,
            "training_ready": False,
            "model_use_authorized": False,
            "limitations": ["synthetic fixture"],
        }
        receipt["receipt_digest"] = canonical_digest(receipt)
        (self.predecessor / "packet-receipt.json").write_text(
            json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_selects_mandatory_and_patient_exclusive_routine_records(self):
        output = self.root / "train-qa"
        receipt = build_train_qa_packet(self.predecessor, output)
        manifest = json.loads((output / "train-qa-manifest.json").read_text())
        by_id = {row["record_id"]: row for row in manifest["records"]}
        self.assertEqual(receipt["schema"], "mmbu.busbra.train_qa_packet_receipt.v1")
        self.assertIn("bus_0001-l", by_id)
        self.assertIn("bus_0845-s", by_id)
        self.assertNotIn("bus_0110-l", by_id)
        self.assertNotIn("bus_0536-r", by_id)
        routine_cases = [row["case_id"] for row in manifest["records"] if row["selection_role"] == "routine"]
        self.assertEqual(len(routine_cases), len(set(routine_cases)))
        self.assertLessEqual(len(routine_cases), 60)
        self.assertFalse(receipt["source_admission_authorized"])
        self.assertFalse(receipt["training_ready"])
        self.assertFalse(receipt["model_use_authorized"])

    def test_rejects_predecessor_member_tamper(self):
        (self.predecessor / "assets/bus_0001-l/image.png").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, r"predecessor member.*digest mismatch"):
            build_train_qa_packet(self.predecessor, self.root / "train-qa")

    def test_rejects_symlinked_predecessor_member(self):
        image = self.predecessor / "assets/bus_0001-l/image.png"
        target = self.root / "outside.png"
        target.write_bytes(image.read_bytes())
        image.unlink()
        image.symlink_to(target)
        with self.assertRaisesRegex(ValueError, "symbolic link"):
            build_train_qa_packet(self.predecessor, self.root / "train-qa")

    def test_refuses_to_overwrite_output(self):
        output = self.root / "train-qa"
        output.mkdir()
        with self.assertRaises(FileExistsError):
            build_train_qa_packet(self.predecessor, output)


if __name__ == "__main__":
    unittest.main()
