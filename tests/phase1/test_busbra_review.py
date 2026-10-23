"""Synthetic conformance tests for the offline BUS-BRA human-review packet."""

from __future__ import annotations

import csv
from contextlib import redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

import mmbu_phase1.busbra_review as busbra_review
from mmbu_phase1.busbra_review import build_review_packet, main


PNG = b"\x89PNG\r\n\x1a\nsynthetic-fixture"


def canonical_digest(value: dict) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


class BusbraReviewPacketTests(unittest.TestCase):
    def test_production_pins_match_repository_review_inputs(self):
        root = Path(__file__).resolve().parents[2]
        human_plan = json.loads((root / "config/busbra-human-review-plan.json").read_text())
        contract = json.loads(
            (root / "outputs/BUSBRA-structural-transform-contract-2026-10-23.json").read_text()
        )
        self.assertEqual(canonical_digest(human_plan), busbra_review.HUMAN_PLAN_DIGEST)
        self.assertEqual(canonical_digest(contract), busbra_review.STRUCTURAL_CONTRACT_DIGEST)
        self.assertEqual(
            human_plan["medical_review_population"]["stratified_plan_digest"],
            busbra_review.STRATIFIED_PLAN_DIGEST,
        )

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.archive = self.root / "BUSBRA.zip"
        self.output = self.root / "review"
        self.rows = [
            ["bus_0001-l", "1", "h1", "benign", "2", "d", "8", "8", "left", "[1,1,3,3]"],
            ["bus_0002-l", "2", "h2", "malignant", "5", "d", "8", "8", "left", "[1,1,3,3]"],
            ["bus_0003-l", "3", "h3", "benign", "3", "d", "8", "8", "left", "[1,1,3,3]"],
            ["bus_0110-l", "110", "h4", "benign", "4", "d", "8", "8", "left", "[1,1,3,3]"],
            ["bus_0536-r", "536", "h5", "malignant", "4", "d", "8", "8", "right", "[1,1,3,3]"],
        ]
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX"))
        writer.writerows(self.rows)
        self.metadata = stream.getvalue().encode()
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("BUSBRA/bus_data.csv", self.metadata)
            for row in self.rows:
                record_id = row[0]
                suffix = record_id[4:]
                archive.writestr(f"BUSBRA/Images/{record_id}.png", PNG + record_id.encode())
                archive.writestr(f"BUSBRA/Masks/mask_{suffix}.png", PNG + b"mask-" + record_id.encode())

        selected = []
        for row in self.rows:
            record_id, case_id, _, pathology, birads, _, width, height, _, bbox = row
            suffix = record_id[4:]
            selected.append({
                "record_id": record_id,
                "case_id": case_id,
                "pathology": pathology,
                "birads": birads,
                "width": int(width),
                "height": int(height),
                "bbox_xywh": json.loads(bbox),
                "image_member": f"BUSBRA/Images/{record_id}.png",
                "mask_member": f"BUSBRA/Masks/mask_{suffix}.png",
            })
        selected.sort(key=lambda item: (item["pathology"], item["birads"], item["record_id"]))
        unsigned = {
            "schema": "mmbu.busbra.quarantine_sample_plan.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "metadata_member": "BUSBRA/bus_data.csv",
            "metadata_sha256": hashlib.sha256(self.metadata).hexdigest(),
            "selection_algorithm": "rarest-pathology-birads-stratum-then-record-id-case-exclusive-v1",
            "per_stratum": 35,
            "records": selected,
            "selected_case_count": 5,
            "biomedical_pixels_opened": False,
            "model_executed": False,
            "model_use_authorized": False,
        }
        self.stratified_plan = {**unsigned, "plan_digest": canonical_digest(unsigned)}
        contract_unsigned = {
            "bbox_exception_records": ["bus_0002-l", "bus_0003-l"],
            "dimension_exception_records": [],
            "schema": "mmbu.busbra.structural_transform_contract.v1",
            "source_id": "busbra",
            "source_version": "1.0",
        }
        self.contract = {**contract_unsigned, "contract_digest": canonical_digest(contract_unsigned)}
        self.human_plan = {
            "decision_status": "pending_human_review",
            "exception_population_source": "synthetic-contract.json",
            "exception_population_source_digest": self.contract["contract_digest"],
            "mandatory_record_rules": [
                "all bbox_exception_records", "all dimension_exception_records", "bus_0110-l", "bus_0536-r"
            ],
            "medical_review_population": {
                "expected_mandatory_record_count": 4,
                "expected_overlap_record_count": 4,
                "expected_stratified_record_count": 5,
                "expected_union_record_count": 5,
                "metadata_sha256": hashlib.sha256(self.metadata).hexdigest(),
                "selection": "union of the frozen stratified plan and mandatory_record_rules",
                "stratified_plan_digest": self.stratified_plan["plan_digest"],
                "stratified_plan_per_pathology_birads_stratum": 35,
                "stratified_plan_selection_algorithm": "rarest-pathology-birads-stratum-then-record-id-case-exclusive-v1",
            },
            "proposed_task_decisions": [
                "pathology classification", "BI-RADS classification", "mask-grounded classification", "mask-derived object detection"
            ],
            "review_roles": {
                "medical_primary": "human breast-imaging reviewer",
                "medical_secondary": "independent human breast-imaging reviewer for disagreements and every material exception",
                "provenance": "human data steward or source-author clarification",
                "rights_release": "human team authority accepting source obligations and challenge disclosure/release consequences",
            },
            "schema": "mmbu.busbra.human_review_plan.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "training_ready": False,
        }
        payload = self.archive.read_bytes()
        self.pins = {
            "ARCHIVE_BYTES": len(payload),
            "ARCHIVE_MD5": hashlib.md5(payload).hexdigest(),
            "STRATIFIED_PLAN_DIGEST": self.stratified_plan["plan_digest"],
            "HUMAN_PLAN_DIGEST": canonical_digest(self.human_plan),
            "STRUCTURAL_CONTRACT_DIGEST": canonical_digest(self.contract),
        }

    def tearDown(self):
        self.temp.cleanup()

    def build(self):
        with mock.patch.multiple(busbra_review, **self.pins):
            return build_review_packet(
                self.archive,
                self.stratified_plan,
                self.human_plan,
                self.contract,
                self.output,
            )

    def test_packet_exports_exact_union_without_granting_authority(self):
        receipt = self.build()
        manifest = json.loads((self.output / "review-manifest.json").read_text())
        self.assertEqual(
            [row["record_id"] for row in manifest["records"]],
            ["bus_0001-l", "bus_0002-l", "bus_0003-l", "bus_0110-l", "bus_0536-r"],
        )
        self.assertEqual(manifest["record_count"], 5)
        self.assertEqual(manifest["review_status"], "pending_human_review")
        self.assertIs(manifest["training_ready"], False)
        self.assertIs(manifest["model_use_authorized"], False)
        self.assertIs(receipt["review_complete"], False)
        self.assertIs(receipt["training_ready"], False)
        self.assertEqual(receipt["record_count"], 5)
        for record in manifest["records"]:
            self.assertTrue((self.output / record["image_path"]).is_file())
            self.assertTrue((self.output / record["mask_path"]).is_file())

    def test_packet_marks_every_exception_and_provenance_case(self):
        self.build()
        manifest = json.loads((self.output / "review-manifest.json").read_text())
        reasons = {row["record_id"]: row["mandatory_reasons"] for row in manifest["records"]}
        self.assertEqual(reasons["bus_0001-l"], [])
        self.assertEqual(reasons["bus_0002-l"], ["bbox_exception"])
        self.assertEqual(reasons["bus_0003-l"], ["bbox_exception"])
        self.assertEqual(reasons["bus_0110-l"], ["provenance_pair"])
        self.assertEqual(reasons["bus_0536-r"], ["provenance_pair"])

    def test_tampered_plan_fails_before_any_packet_is_published(self):
        self.stratified_plan["records"][0]["pathology"] = "tampered"
        with self.assertRaisesRegex(ValueError, "plan digest"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_human_plan_cannot_smuggle_unknown_authority_claims(self):
        self.human_plan["model_use_authorized"] = True
        with self.assertRaisesRegex(ValueError, "human-review plan must be closed"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_resealed_contract_for_another_source_is_rejected(self):
        unsigned = dict(self.contract)
        unsigned.pop("contract_digest")
        unsigned["source_id"] = "another-source"
        self.contract = {**unsigned, "contract_digest": canonical_digest(unsigned)}
        with self.assertRaisesRegex(ValueError, "frozen structural contract"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_resealed_plan_with_attacker_algorithm_is_rejected(self):
        unsigned = dict(self.stratified_plan)
        unsigned.pop("plan_digest")
        unsigned["selection_algorithm"] = "attacker-chosen-v1"
        self.stratified_plan = {**unsigned, "plan_digest": canonical_digest(unsigned)}
        with self.assertRaisesRegex(ValueError, "frozen stratified plan"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_resealed_contract_cannot_smuggle_authority_claim(self):
        unsigned = dict(self.contract)
        unsigned.pop("contract_digest")
        unsigned["rights_and_purpose_approved"] = True
        self.contract = {**unsigned, "contract_digest": canonical_digest(unsigned)}
        with self.assertRaisesRegex(ValueError, "frozen structural contract"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_missing_selected_asset_fails_atomically(self):
        broken = self.root / "broken.zip"
        with zipfile.ZipFile(self.archive) as source, zipfile.ZipFile(broken, "w") as target:
            for item in source.infolist():
                if item.filename != "BUSBRA/Masks/mask_0536-r.png":
                    target.writestr(item, source.read(item))
        self.archive = broken
        payload = broken.read_bytes()
        self.pins["ARCHIVE_BYTES"] = len(payload)
        self.pins["ARCHIVE_MD5"] = hashlib.md5(payload).hexdigest()
        with self.assertRaisesRegex(ValueError, "missing review asset"):
            self.build()
        self.assertFalse(self.output.exists())

    def test_existing_output_is_never_overwritten(self):
        self.output.mkdir()
        marker = self.output / "keep.txt"
        marker.write_text("keep")
        with self.assertRaises(FileExistsError):
            self.build()
        self.assertEqual(marker.read_text(), "keep")

    def test_destination_created_during_publication_is_not_replaced(self):
        original = busbra_review._rename_no_replace

        def race(source, destination):
            destination.mkdir()
            (destination / "competitor.txt").write_text("keep")
            return original(source, destination)

        with mock.patch.object(busbra_review, "_rename_no_replace", side_effect=race):
            with self.assertRaises(FileExistsError):
                self.build()
        self.assertEqual((self.output / "competitor.txt").read_text(), "keep")

    def test_cli_builds_from_strict_json_inputs(self):
        plan_path = self.root / "stratified-plan.json"
        human_path = self.root / "human-plan.json"
        contract_path = self.root / "contract.json"
        plan_path.write_text(json.dumps(self.stratified_plan))
        human_path.write_text(json.dumps(self.human_plan))
        contract_path.write_text(json.dumps(self.contract))
        with mock.patch.multiple(busbra_review, **self.pins), redirect_stdout(io.StringIO()):
            exit_code = main([
                str(self.archive),
                "--stratified-plan", str(plan_path),
                "--human-plan", str(human_path),
                "--structural-contract", str(contract_path),
                "--output", str(self.output),
            ])
        self.assertEqual(exit_code, 0)
        self.assertTrue((self.output / "packet-receipt.json").is_file())


if __name__ == "__main__":
    unittest.main()
