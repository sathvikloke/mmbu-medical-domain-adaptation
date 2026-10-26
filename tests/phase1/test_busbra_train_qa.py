"""Synthetic conformance tests for the BUS-BRA train-only QA packet."""

from __future__ import annotations

import hashlib
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from mmbu_phase1.busbra_train_qa import build_train_qa_packet
from mmbu_phase1.busbra_train_qa_validation import validate_train_qa


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

    def test_rejects_manifest_asset_not_bound_by_predecessor_receipt(self):
        receipt_path = self.predecessor / "packet-receipt.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["members"] = [
            row for row in receipt["members"]
            if row["path"] != "assets/bus_0001-l/image.png"
        ]
        receipt.pop("receipt_digest")
        receipt["receipt_digest"] = canonical_digest(receipt)
        receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "not bound by the predecessor receipt"):
            build_train_qa_packet(self.predecessor, self.root / "train-qa")

    def test_refuses_to_overwrite_output(self):
        output = self.root / "train-qa"
        output.mkdir()
        with self.assertRaises(FileExistsError):
            build_train_qa_packet(self.predecessor, output)


class BusbraTrainQaValidationTests(unittest.TestCase):
    def setUp(self):
        BusbraTrainQaBuildTests.setUp(self)
        self.packet = self.root / "train-qa"
        self.receipt = build_train_qa_packet(self.predecessor, self.packet)
        self.visual = self.root / "visual-completed.csv"
        with (self.packet / "visual-review-template.csv").open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fieldnames = reader.fieldnames
            rows = list(reader)
        for row in rows:
            row.update({
                "reviewer_id": "visual-reviewer-1",
                "reviewed_at": "2026-10-26T13:00:00Z",
                "asset_match": "yes",
                "image_interpretable": "yes",
                "modality_body_part_supported": "yes",
                "mask_alignment": "yes",
                "annotation_completeness_concern": "no",
                "shortcut_artifact": "none",
                "permitted_training_targets": "mask_context|pathology_classification",
                "final_disposition": "eligible",
                "notes": "publisher annotation usable for training-only QA",
            })
        with self.visual.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        self.rights = self.root / "rights-completed.json"
        rights = json.loads((self.packet / "rights-purpose-template.json").read_text())
        rights.update({
            "schema": "mmbu.busbra.train_rights_completed.v1",
            "reviewer_id": "rights-reviewer-1",
            "reviewed_at": "2026-10-26T13:05:00Z",
            "qualification_evidence_locator": "team-role-record:rights-reviewer-1",
            "conflict_status": "none_declared",
            "conflict_evidence_locator": "conflict-declaration:rights-reviewer-1",
            "license_evidence_locator": "zenodo:8231412:cc-by-4.0",
            "attribution_text": "BUS-BRA 1.0; Gomez-Flores et al.; CC BY 4.0",
            "challenge_disclosure": "Disclose BUS-BRA training use and exact version.",
            "retention_policy": "Quarantined source retained on protected scratch only.",
            "train_decision": "approve",
            "human_attested": True,
            "review_complete": True,
        })
        self.rights.write_text(json.dumps(rights, sort_keys=True) + "\n", encoding="utf-8")
        self.opening = self.root / "opening.json"
        opening = {
            "schema": "mmbu.busbra.train_qa_opening.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "packet_receipt_digest": self.receipt["receipt_digest"],
            "opened_at": "2026-10-26T12:00:00Z",
            "opened_by": "review-coordinator-1",
            "authorization_evidence_locator": "user-authorization:2026-10-26",
            "human_attested": True,
            "review_opening_authorized": True,
            "training_ready": False,
            "model_use_authorized": False,
        }
        self.opening.write_text(json.dumps(opening, sort_keys=True) + "\n", encoding="utf-8")

    def tearDown(self):
        BusbraTrainQaBuildTests.tearDown(self)

    def validate(self):
        return validate_train_qa(
            self.packet, self.visual, self.rights, self.opening,
            self.receipt["receipt_digest"], now=datetime(2026, 10, 26, 14, tzinfo=timezone.utc),
        )

    def rewrite_visual(self, mutate):
        with self.visual.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            fieldnames = reader.fieldnames
            rows = list(reader)
        mutate(rows)
        with self.visual.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def test_complete_train_only_evidence_is_admission_input_ready_but_non_authoritative(self):
        report = self.validate()
        self.assertTrue(report["admission_input_ready"])
        self.assertEqual(report["routine_critical_failure_count"], 0)
        self.assertFalse(report["source_admission_authorized"])
        self.assertFalse(report["training_ready"])
        self.assertFalse(report["model_use_authorized"])

    def test_routine_critical_failure_blocks_readiness(self):
        def mutate(rows):
            row = next(item for item in rows if item["selection_role"] == "routine")
            row.update({
                "asset_match": "no", "permitted_training_targets": "",
                "final_disposition": "exclude", "notes": "asset mismatch",
            })
        self.rewrite_visual(mutate)
        report = self.validate()
        self.assertFalse(report["admission_input_ready"])
        self.assertGreaterEqual(report["routine_critical_failure_count"], 1)

    def test_escalated_mandatory_record_blocks_readiness(self):
        def mutate(rows):
            row = next(item for item in rows if item["selection_role"] == "mandatory")
            row.update({"final_disposition": "escalate", "notes": "requires adjudication"})
        self.rewrite_visual(mutate)
        self.assertFalse(self.validate()["admission_input_ready"])

    def test_review_before_opening_is_rejected(self):
        self.rewrite_visual(lambda rows: rows[0].update({"reviewed_at": "2026-10-26T11:59:59Z"}))
        with self.assertRaisesRegex(ValueError, "after the authorized opening"):
            self.validate()

    def test_unresolved_rights_blocks_readiness(self):
        value = json.loads(self.rights.read_text())
        value["train_decision"] = "unresolved"
        self.rights.write_text(json.dumps(value) + "\n", encoding="utf-8")
        self.assertFalse(self.validate()["admission_input_ready"])

    def test_projected_packet_tamper_is_rejected(self):
        path = self.packet / "assets/bus_0001-l/image.png"
        path.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, r"packet member.*digest mismatch"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
