"""Synthetic conformance tests for the offline BUS-BRA human-review packet."""

from __future__ import annotations

import csv
from contextlib import redirect_stdout
import hashlib
import io
import json
import copy
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

try:
    from PIL import Image
except ImportError:
    Image = None

import mmbu_phase1.busbra_review as busbra_review
from mmbu_phase1.busbra_review import build_review_packet, main
from mmbu_phase1.busbra_review_validation import validate_completed_review


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

    def test_mask_grounded_task_names_one_explicit_target(self):
        root = Path(__file__).resolve().parents[2]
        human_plan = json.loads((root / "config/busbra-human-review-plan.json").read_text())
        tasks = human_plan["proposed_task_decisions"]
        self.assertIn("mask-grounded pathology classification", tasks)
        self.assertNotIn("mask-grounded classification", tasks)

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
                "pathology classification", "BI-RADS classification", "mask-grounded pathology classification", "mask-derived object detection"
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
        with mock.patch.multiple(busbra_review, **self.pins), mock.patch.object(
            busbra_review, "_decode_image_size", return_value=(8, 8)
        ), mock.patch.object(
            busbra_review, "_decode_mask_bbox", return_value=[1, 1, 3, 3]
        ):
            return build_review_packet(
                self.archive,
                self.stratified_plan,
                self.human_plan,
                self.contract,
                self.output,
            )

    def test_template_exposes_independent_decision_vectors_and_context_fields(self):
        receipt = self.build()
        manifest = json.loads((self.output / "review-manifest.json").read_text())
        self.assertEqual(receipt["schema"], "mmbu.busbra.human_review_packet_receipt.v2")
        self.assertEqual(manifest["schema"], "mmbu.busbra.human_review_packet_manifest.v2")
        with (self.output / "record-review-template.csv").open(newline="", encoding="utf-8") as stream:
            fields = set(csv.DictReader(stream).fieldnames or [])
        required = {
            "primary_modality_supported", "primary_body_part_supported",
            "primary_pathology_target_plausible", "primary_birads_target_plausible",
            "primary_permitted_tasks", "secondary_image_interpretable",
            "secondary_permitted_tasks", "adjudicator_image_interpretable",
            "adjudicator_permitted_tasks", "adjudicator_disposition", "adjudicator_notes",
            "final_permitted_tasks",
        }
        self.assertEqual(required - fields, set())

    def test_source_template_retains_reviewer_conflict_declarations(self):
        self.build()
        source = json.loads((self.output / "source-review-template.json").read_text())
        self.assertEqual(source["schema"], "mmbu.busbra.source_review_template.v2")
        for review in (
            source["medical_review"]["primary_reviewer"],
            source["medical_review"]["secondary_reviewer"],
            source["provenance_review"]["reviewer"],
            source["rights_and_release_review"]["reviewer"],
        ):
            self.assertIn("conflict_status", review)
            self.assertIn("conflict_evidence_locator", review)

    def completed_review_files(self):
        self.build()
        manifest = json.loads((self.output / "review-manifest.json").read_text())
        template = self.output / "record-review-template.csv"
        with template.open(newline="", encoding="utf-8") as stream:
            fieldnames = csv.DictReader(stream).fieldnames
        rows = []
        tasks = "|".join(self.human_plan["proposed_task_decisions"])
        for record in manifest["records"]:
            mandatory = bool(record["mandatory_reasons"])
            rows.append({
                "record_id": record["record_id"],
                "case_id": record["case_id"],
                "pathology": record["pathology"],
                "birads": record["birads"],
                "width": str(record["width"]),
                "height": str(record["height"]),
                "decoded_width": str(record["decoded_width"]),
                "decoded_height": str(record["decoded_height"]),
                "source_bbox_xywh": json.dumps(record["bbox_xywh"], separators=(",", ":")),
                "mask_derived_bbox_xywh": json.dumps(
                    record["mask_derived_bbox_xywh"], separators=(",", ":")
                ),
                "image_member": record["image_member"],
                "mask_member": record["mask_member"],
                "image_path": record["image_path"],
                "mask_path": record["mask_path"],
                "mandatory_reasons": "|".join(record["mandatory_reasons"]),
                "primary_reviewer_id": "medical-primary",
                "primary_reviewed_at": "2026-10-23T20:00:00Z",
                "primary_image_interpretable": "yes",
                "primary_modality_supported": "yes",
                "primary_body_part_supported": "yes",
                "primary_mask_usable": "yes",
                "primary_additional_or_incomplete_lesion": "no",
                "primary_pathology_target_plausible": "yes",
                "primary_birads_target_plausible": "yes",
                "primary_shortcut_artifact": "none",
                "primary_permitted_tasks": tasks,
                "primary_disposition": "eligible",
                "primary_notes": "reviewed against the frozen image, mask, and source fields",
                "secondary_reviewer_id": "medical-secondary" if mandatory else "",
                "secondary_reviewed_at": "2026-10-23T21:00:00Z" if mandatory else "",
                "secondary_image_interpretable": "yes" if mandatory else "",
                "secondary_modality_supported": "yes" if mandatory else "",
                "secondary_body_part_supported": "yes" if mandatory else "",
                "secondary_mask_usable": "yes" if mandatory else "",
                "secondary_additional_or_incomplete_lesion": "no" if mandatory else "",
                "secondary_pathology_target_plausible": "yes" if mandatory else "",
                "secondary_birads_target_plausible": "yes" if mandatory else "",
                "secondary_shortcut_artifact": "none" if mandatory else "",
                "secondary_permitted_tasks": tasks if mandatory else "",
                "secondary_disposition": "eligible" if mandatory else "",
                "secondary_notes": "independent mandatory-case review" if mandatory else "",
                "adjudicator_id": "",
                "adjudicated_at": "",
                "adjudicator_image_interpretable": "",
                "adjudicator_modality_supported": "",
                "adjudicator_body_part_supported": "",
                "adjudicator_mask_usable": "",
                "adjudicator_additional_or_incomplete_lesion": "",
                "adjudicator_pathology_target_plausible": "",
                "adjudicator_birads_target_plausible": "",
                "adjudicator_shortcut_artifact": "",
                "adjudicator_permitted_tasks": "",
                "adjudicator_disposition": "",
                "adjudicator_notes": "",
                "final_permitted_tasks": tasks,
                "final_disposition": "eligible",
            })
        completed_records = self.root / "record-review-completed.csv"
        with completed_records.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

        profile = lambda role, reviewer_id, qualification, reviewed_at: {
            "role": role,
            "reviewer_id": reviewer_id,
            "qualification": qualification,
            "qualification_evidence_locator": "qualification-record:" + reviewer_id,
            "conflict_status": "none_declared",
            "conflict_evidence_locator": "conflict-declaration:" + reviewer_id,
            "reviewed_at": reviewed_at,
            "evidence_locator": "local-review-log:" + reviewer_id,
            "human_attested": True,
        }
        completed_source = {
            "schema": "mmbu.busbra.source_review_completed.v2",
            "source_id": "busbra",
            "source_version": "1.0",
            "decision_status": "completed_human_review",
            "medical_review": {
                "primary_reviewer": profile(
                    "medical_primary", "medical-primary", "breast_ultrasound_clinician", "2026-10-23T20:00:00Z"
                ),
                "secondary_reviewer": profile(
                    "medical_secondary", "medical-secondary", "breast_imaging_clinician", "2026-10-23T21:00:00Z"
                ),
                "adjudicator": None,
            },
            "provenance_review": {
                "reviewer": profile(
                    "provenance", "data-steward", "source_data_steward", "2026-10-23T22:00:00Z"
                ),
                "case_110_536_disposition": "distinct_lineage",
                "evidence_locator": "source-author-record:110-536",
            },
            "rights_and_release_review": {
                "reviewer": profile(
                    "rights_release", "team-authority", "team_rights_authority", "2026-10-23T22:30:00Z"
                ),
                "training": "approve",
                "development": "approve",
                "untouched_confirmation": "approve",
                "public_weight_release": "approve",
                "challenge_submission": "approve",
                "attribution_text": "BUS-BRA v1.0, Zenodo 8231412, CC BY 4.0",
                "redistribution_conditions": "Preserve attribution and source notices.",
            },
            "review_complete": True,
            "training_ready": False,
            "model_use_authorized": False,
        }
        completed_source_path = self.root / "source-review-completed.json"
        completed_source_path.write_text(json.dumps(completed_source))
        receipt = json.loads((self.output / "packet-receipt.json").read_text())
        opening = {
            "schema": "mmbu.busbra.review_opening_record.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "packet_receipt_digest": receipt["receipt_digest"],
            "opened_at": "2026-10-23T19:00:00Z",
            "opened_by": "review-coordinator",
            "authorization_evidence_locator": "controller-authorization:busbra-review-opening",
            "human_attested": True,
            "review_opening_authorized": True,
            "training_ready": False,
            "model_use_authorized": False,
        }
        self.opening_path = self.root / "review-opening.json"
        self.opening_path.write_text(json.dumps(opening))
        return completed_records, completed_source_path, rows, completed_source

    def validate_completed(self, records_path, source_path):
        receipt = json.loads((self.output / "packet-receipt.json").read_text())
        return validate_completed_review(
            self.output,
            records_path,
            source_path,
            review_opening=self.opening_path,
            expected_packet_receipt_digest=receipt["receipt_digest"],
        )

    @staticmethod
    def write_rows(path, rows):
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    def test_completed_human_review_is_machine_checkable_but_grants_no_authority(self):
        records_path, source_path, _, _ = self.completed_review_files()
        report = self.validate_completed(records_path, source_path)
        self.assertIs(report["review_evidence_complete"], True)
        self.assertIs(report["mechanically_ready_for_phase1_admission_review"], True)
        self.assertIs(report["admission_review_ready"], False)
        self.assertEqual(report["record_count"], 5)
        self.assertIs(report["source_admission_authorized"], False)
        self.assertIs(report["training_ready"], False)
        self.assertIs(report["model_use_authorized"], False)

    def test_mandatory_record_requires_distinct_secondary_review(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        mandatory = next(row for row in rows if row["mandatory_reasons"])
        mandatory["secondary_reviewer_id"] = mandatory["primary_reviewer_id"]
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "distinct secondary reviewer"):
            self.validate_completed(records_path, source_path)

    def test_disagreement_requires_a_distinct_named_adjudicator(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        mandatory = next(row for row in rows if row["mandatory_reasons"])
        mandatory["secondary_disposition"] = "excluded"
        mandatory["secondary_permitted_tasks"] = ""
        mandatory["final_disposition"] = "excluded"
        mandatory["final_permitted_tasks"] = ""
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "adjudicator"):
            self.validate_completed(records_path, source_path)

    def test_classification_only_record_does_not_require_a_usable_mask(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        row = next(value for value in rows if not value["mandatory_reasons"])
        row["primary_mask_usable"] = "no"
        row["primary_additional_or_incomplete_lesion"] = "yes"
        row["primary_permitted_tasks"] = "pathology classification|BI-RADS classification"
        row["final_permitted_tasks"] = row["primary_permitted_tasks"]
        self.write_rows(records_path, rows)
        with self.assertRaisesRegex(ValueError, "secondary review"):
            self.validate_completed(records_path, source_path)

        row["secondary_reviewer_id"] = "medical-secondary"
        row["secondary_reviewed_at"] = "2026-10-23T21:00:00Z"
        for name in (
            "image_interpretable", "modality_supported", "body_part_supported", "mask_usable",
            "additional_or_incomplete_lesion", "pathology_target_plausible",
            "birads_target_plausible", "shortcut_artifact", "permitted_tasks", "disposition",
        ):
            row[f"secondary_{name}"] = row[f"primary_{name}"]
        row["secondary_notes"] = "independent review of the annotation-completeness concern"
        self.write_rows(records_path, rows)
        report = self.validate_completed(records_path, source_path)
        self.assertIn(row["record_id"], report["eligible_record_ids"])

    def test_localization_task_requires_mask_and_complete_lesion_annotation(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        row = next(value for value in rows if not value["mandatory_reasons"])
        row["primary_mask_usable"] = "no"
        row["primary_permitted_tasks"] = "mask-derived object detection"
        row["final_permitted_tasks"] = row["primary_permitted_tasks"]
        self.write_rows(records_path, rows)
        with self.assertRaisesRegex(ValueError, "mask-derived object detection"):
            self.validate_completed(records_path, source_path)

    def test_task_disagreement_requires_full_adjudication_even_when_dispositions_match(self):
        records_path, source_path, rows, source = self.completed_review_files()
        row = next(value for value in rows if value["mandatory_reasons"])
        row["secondary_permitted_tasks"] = "pathology classification"
        self.write_rows(records_path, rows)
        with self.assertRaisesRegex(ValueError, "adjudicator"):
            self.validate_completed(records_path, source_path)

    def test_adjudicator_decision_vector_controls_the_final_result(self):
        records_path, source_path, rows, source = self.completed_review_files()
        row = next(value for value in rows if value["mandatory_reasons"])
        row["secondary_permitted_tasks"] = "pathology classification"
        source["medical_review"]["adjudicator"] = {
            "role": "adjudicator",
            "reviewer_id": "medical-adjudicator",
            "qualification": "breast_ultrasound_clinician",
            "qualification_evidence_locator": "qualification-record:medical-adjudicator",
            "conflict_status": "none_declared",
            "conflict_evidence_locator": "conflict-declaration:medical-adjudicator",
            "reviewed_at": "2026-10-23T22:00:00Z",
            "evidence_locator": "local-review-log:medical-adjudicator",
            "human_attested": True,
        }
        for name in (
            "image_interpretable", "modality_supported", "body_part_supported", "mask_usable",
            "additional_or_incomplete_lesion", "pathology_target_plausible",
            "birads_target_plausible", "shortcut_artifact",
        ):
            row[f"adjudicator_{name}"] = row[f"primary_{name}"]
        row["adjudicator_id"] = "medical-adjudicator"
        row["adjudicated_at"] = "2026-10-23T21:30:00Z"
        row["adjudicator_permitted_tasks"] = "pathology classification"
        row["adjudicator_disposition"] = "eligible"
        row["adjudicator_notes"] = "resolved the task-scope disagreement"
        row["final_permitted_tasks"] = row["adjudicator_permitted_tasks"]
        self.write_rows(records_path, rows)
        source_path.write_text(json.dumps(source))
        report = self.validate_completed(records_path, source_path)
        self.assertIn(row["record_id"], report["eligible_record_ids"])

    def test_unresolved_decision_blocks_readiness_without_becoming_authority(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        row = next(value for value in rows if value["mandatory_reasons"])
        row["primary_disposition"] = "unresolved"
        row["secondary_disposition"] = "unresolved"
        row["final_disposition"] = "unresolved"
        row["primary_permitted_tasks"] = ""
        row["secondary_permitted_tasks"] = ""
        row["final_permitted_tasks"] = ""
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        report = self.validate_completed(records_path, source_path)
        self.assertIs(report["review_evidence_complete"], True)
        self.assertIs(report["admission_review_ready"], False)
        self.assertIn(row["record_id"], report["blocked_record_ids"])
        self.assertIs(report["source_admission_authorized"], False)

    def test_tampered_packet_or_missing_completed_record_fails_closed(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        image = next((self.output / "assets").rglob("image.png"))
        image.write_bytes(image.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "packet member digest"):
            self.validate_completed(records_path, source_path)
        image.write_bytes(image.read_bytes()[:-8])
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows[:-1])
        with self.assertRaisesRegex(ValueError, "exactly the frozen record population"):
            self.validate_completed(records_path, source_path)

    def test_resealed_packet_does_not_match_the_pre_review_receipt(self):
        records_path, source_path, _, _ = self.completed_review_files()
        receipt_path = self.output / "packet-receipt.json"
        receipt = json.loads(receipt_path.read_text())
        frozen_digest = receipt["receipt_digest"]
        image = next((self.output / "assets").rglob("image.png"))
        image.write_bytes(image.read_bytes() + b"resealed")
        member = next(value for value in receipt["members"] if value["path"] == image.relative_to(self.output).as_posix())
        member["bytes"] = image.stat().st_size
        member["sha256"] = hashlib.sha256(image.read_bytes()).hexdigest()
        unsigned = dict(receipt)
        unsigned.pop("receipt_digest")
        receipt["receipt_digest"] = canonical_digest(unsigned)
        receipt_path.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(ValueError, "frozen packet receipt"):
            validate_completed_review(
                self.output,
                records_path,
                source_path,
                review_opening=self.opening_path,
                expected_packet_receipt_digest=frozen_digest,
            )

    def test_source_roles_require_qualifications_and_evidence(self):
        records_path, source_path, _, source = self.completed_review_files()
        source["medical_review"]["primary_reviewer"]["qualification"] = ""
        source_path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, "qualification"):
            self.validate_completed(records_path, source_path)

    def test_self_asserted_nonhuman_or_wrong_role_profile_is_rejected(self):
        records_path, source_path, _, source = self.completed_review_files()
        profile = source["medical_review"]["primary_reviewer"]
        profile["qualification"] = "AI model"
        source_path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, "qualification is not allowed"):
            self.validate_completed(records_path, source_path)
        profile["qualification"] = "breast_ultrasound_clinician"
        profile["human_attested"] = False
        source_path.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError, "human attestation"):
            self.validate_completed(records_path, source_path)

    def test_report_binds_exact_packet_and_completed_evidence_bytes(self):
        records_path, source_path, rows, source = self.completed_review_files()
        first = self.validate_completed(records_path, source_path)
        self.assertEqual(
            first["packet_receipt_digest"],
            json.loads((self.output / "packet-receipt.json").read_text())["receipt_digest"],
        )
        rows[0]["primary_notes"] += "; exact-note-change"
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        source["rights_and_release_review"]["reviewer"]["evidence_locator"] += ":changed"
        source_path.write_text(json.dumps(source))
        second = self.validate_completed(records_path, source_path)
        self.assertNotEqual(first["completed_records_sha256"], second["completed_records_sha256"])
        self.assertNotEqual(first["completed_source_sha256"], second["completed_source_sha256"])
        self.assertNotEqual(first["report_digest"], second["report_digest"])

    def test_narrow_rights_or_ambiguous_provenance_stays_blocked(self):
        records_path, source_path, _, source = self.completed_review_files()
        source["rights_and_release_review"]["training"] = "narrow"
        source["provenance_review"]["case_110_536_disposition"] = "unresolved"
        source_path.write_text(json.dumps(source))
        report = self.validate_completed(records_path, source_path)
        self.assertIs(report["mechanically_ready_for_phase1_admission_review"], False)
        self.assertNotIn("training", report["proposed_allowed_purposes"])
        self.assertIn("training_narrow_requires_scope_binding", report["source_blockers"])
        self.assertIn("case_110_536_provenance_unresolved", report["source_blockers"])

    def test_explicit_provenance_actions_emit_exclusion_or_coassignment(self):
        records_path, source_path, _, source = self.completed_review_files()
        source["provenance_review"]["case_110_536_disposition"] = "exclude_both"
        source_path.write_text(json.dumps(source))
        report = self.validate_completed(records_path, source_path)
        self.assertEqual(report["required_excluded_case_ids"], ["110", "536"])
        self.assertNotIn("bus_0110-l", report["eligible_record_ids"])
        self.assertNotIn("bus_0536-r", report["eligible_record_ids"])

        source["provenance_review"]["case_110_536_disposition"] = "coassign"
        source_path.write_text(json.dumps(source))
        report = self.validate_completed(records_path, source_path)
        self.assertEqual(report["required_linked_case_groups"], [["110", "536"]])

    def test_linked_lineage_emits_the_required_coassignment(self):
        records_path, source_path, _, source = self.completed_review_files()
        source["provenance_review"]["case_110_536_disposition"] = "linked_lineage"
        source_path.write_text(json.dumps(source))
        report = self.validate_completed(records_path, source_path)
        self.assertEqual(report["required_linked_case_groups"], [["110", "536"]])
        self.assertIs(report["mechanically_ready_for_phase1_admission_review"], True)

    def test_impossible_or_reversed_review_chronology_is_rejected(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        rows[0]["primary_reviewed_at"] = "9999-99-99T99:99:99Z"
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "real UTC second timestamp"):
            self.validate_completed(records_path, source_path)
        row = next(value for value in rows if value["mandatory_reasons"])
        rows[0]["primary_reviewed_at"] = "2026-10-23T20:00:00Z"
        row["secondary_reviewed_at"] = "2026-10-23T19:00:00Z"
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "after the primary review"):
            self.validate_completed(records_path, source_path)

    def test_future_review_timestamp_is_rejected(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        rows[0]["primary_reviewed_at"] = "2999-01-01T00:00:00Z"
        self.write_rows(records_path, rows)
        with self.assertRaisesRegex(ValueError, "future"):
            self.validate_completed(records_path, source_path)

    def test_reviews_must_follow_the_digest_bound_authorized_opening(self):
        records_path, source_path, _, _ = self.completed_review_files()
        opening = json.loads(self.opening_path.read_text())
        opening["opened_at"] = "2026-10-23T20:30:00Z"
        self.opening_path.write_text(json.dumps(opening))
        try:
            with self.assertRaisesRegex(ValueError, "after the authorized review opening"):
                self.validate_completed(records_path, source_path)
        except TypeError as exc:
            self.fail(f"review-opening evidence is not accepted by the validator: {exc}")

    def test_review_opening_must_bind_the_frozen_packet_receipt(self):
        records_path, source_path, _, _ = self.completed_review_files()
        opening = json.loads(self.opening_path.read_text())
        opening["packet_receipt_digest"] = "0" * 64
        self.opening_path.write_text(json.dumps(opening))
        with self.assertRaisesRegex(ValueError, "packet receipt digest"):
            self.validate_completed(records_path, source_path)

    def test_reviewer_conflict_status_is_retained_and_unresolved_conflict_blocks(self):
        records_path, source_path, _, source = self.completed_review_files()
        source["medical_review"]["primary_reviewer"]["conflict_status"] = "unresolved"
        source_path.write_text(json.dumps(source))
        report = self.validate_completed(records_path, source_path)
        self.assertIn("medical_primary_conflict_unresolved", report["source_blockers"])
        self.assertIs(report["mechanically_ready_for_phase1_admission_review"], False)

    def test_frozen_geometry_and_asset_fields_are_carried_and_checked(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        rows[0]["width"] = "999"
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "width differs from the frozen manifest"):
            self.validate_completed(records_path, source_path)
        rows[0]["width"] = "8"
        rows[0]["mask_derived_bbox_xywh"] = ""
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(ValueError, "mask_derived_bbox_xywh"):
            self.validate_completed(records_path, source_path)

    def test_plausible_but_wrong_mask_box_is_rejected(self):
        records_path, source_path, rows, _ = self.completed_review_files()
        rows[0]["mask_derived_bbox_xywh"] = "[0,0,1,1]"
        with records_path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=rows[0], lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(
            ValueError, "mask_derived_bbox_xywh differs from the frozen manifest"
        ):
            self.validate_completed(records_path, source_path)

    @unittest.skipUnless(Image is not None, "Pillow is an optional image-test dependency")
    def test_decoded_image_size_and_mask_box_come_from_pixels(self):
        image = Image.new("L", (8, 7), 20)
        image_payload = io.BytesIO()
        image.save(image_payload, format="PNG")
        self.assertEqual(busbra_review._decode_image_size(image_payload.getvalue()), (8, 7))

        mask = Image.new("L", (8, 8), 0)
        for y in range(2, 6):
            for x in range(1, 4):
                mask.putpixel((x, y), 255)
        payload = io.BytesIO()
        mask.save(payload, format="PNG")
        self.assertEqual(busbra_review._decode_mask_bbox(payload.getvalue(), (8, 8)), [1, 2, 3, 4])
        with self.assertRaisesRegex(ValueError, "same-size"):
            busbra_review._decode_mask_bbox(payload.getvalue(), (9, 8))

        mask.putpixel((0, 0), 127)
        payload = io.BytesIO()
        mask.save(payload, format="PNG")
        with self.assertRaisesRegex(ValueError, "exactly binary"):
            busbra_review._decode_mask_bbox(payload.getvalue(), (8, 8))

    def test_known_declared_dimension_exception_uses_decoded_image_size(self):
        contract = copy.deepcopy(self.contract)
        contract.pop("contract_digest")
        contract["dimension_exception_records"] = ["bus_0002-l"]
        contract["contract_digest"] = canonical_digest(contract)
        human_plan = copy.deepcopy(self.human_plan)
        human_plan["exception_population_source_digest"] = contract["contract_digest"]
        pins = {
            **self.pins,
            "HUMAN_PLAN_DIGEST": canonical_digest(human_plan),
            "STRUCTURAL_CONTRACT_DIGEST": canonical_digest(contract),
        }

        def image_size(payload):
            return (8, 7) if b"bus_0002-l" in payload else (8, 8)

        def mask_bbox(payload, expected_size):
            expected = (8, 7) if b"bus_0002-l" in payload else (8, 8)
            self.assertEqual(expected_size, expected)
            return [1, 1, 3, 3]

        with mock.patch.multiple(busbra_review, **pins), mock.patch.object(
            busbra_review, "_decode_image_size", side_effect=image_size
        ), mock.patch.object(
            busbra_review, "_decode_mask_bbox", side_effect=mask_bbox
        ):
            build_review_packet(
                self.archive, self.stratified_plan, human_plan, contract, self.output
            )
        manifest = json.loads((self.output / "review-manifest.json").read_text())
        row = next(item for item in manifest["records"] if item["record_id"] == "bus_0002-l")
        self.assertEqual((row["width"], row["height"]), (8, 8))
        self.assertEqual((row["decoded_width"], row["decoded_height"]), (8, 7))

    def test_unlisted_declared_dimension_mismatch_fails_atomically(self):
        def image_size(payload):
            return (8, 7) if b"bus_0002-l" in payload else (8, 8)

        with mock.patch.multiple(busbra_review, **self.pins), mock.patch.object(
            busbra_review, "_decode_image_size", side_effect=image_size
        ), mock.patch.object(
            busbra_review, "_decode_mask_bbox", return_value=[1, 1, 3, 3]
        ):
            with self.assertRaisesRegex(ValueError, "dimension exception status differs"):
                build_review_packet(
                    self.archive, self.stratified_plan, self.human_plan, self.contract, self.output
                )
        self.assertFalse(self.output.exists())

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
        with mock.patch.multiple(busbra_review, **self.pins), mock.patch.object(
            busbra_review, "_decode_image_size", return_value=(8, 8)
        ), mock.patch.object(
            busbra_review, "_decode_mask_bbox", return_value=[1, 1, 3, 3]
        ), redirect_stdout(io.StringIO()):
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
