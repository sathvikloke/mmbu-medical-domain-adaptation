"""Closed CPU-only tests for the BUSI-WHU held-out confirmation mechanics."""

from __future__ import annotations

import copy
import importlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from mmbu_phase1 import admission, canonical, rational
from mmbu_phase1.store import RecordStore
from mmbu_phase1.scope import REQUIRED_PHASE1_TEST_MODULES
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.busi_whu_review_validation import (
    authenticate_completed_review, completed_review_authority_subject,
)
from tests.phase1.admission_fixtures import AdmissionWorld, t
from tests.phase1.test_busi_whu_authority import ReviewAuthorityWorld
from tests.phase1.external_trust_fixtures import external_authority_for


REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "config/phase1/busi-whu-confirmation-spec-2026-10-26.json"
TOOL = REPO / "tools/busi_whu_confirmation.py"
FIXTURES = REPO / "tests/phase1/fixtures/heldout-confirmation"


class HeldoutConfirmationRegistrationTests(unittest.TestCase):
    def test_module_spec_and_suite_registration_exist(self):
        self.assertIsNotNone(importlib.util.find_spec("mmbu_phase1.heldout_confirmation"))
        self.assertTrue(SPEC.is_file())
        self.assertIn("test_heldout_confirmation.py", REQUIRED_PHASE1_TEST_MODULES)


class HeldoutConfirmationSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")
        cls.value = cls.module.load_spec(SPEC)

    def test_exact_frozen_protocol(self):
        value = self.value
        self.assertEqual(value["candidate"], {
            "expected_parameter_count": None,
            "model_id": None,
            "revision": None,
            "runtime_gate": None,
            "selection_authority": "none",
            "status": "blocked_unjustified",
            "track": None,
        })
        self.assertEqual(value["training"]["seeds"], [20261025, 20261026, 20261027])
        self.assertEqual(value["training"]["optimizer_updates"], 1024)
        self.assertEqual(value["training"]["lora_dropout"], 0)
        self.assertEqual(value["training"]["required_training_sources"], ["busbra"])
        self.assertEqual(value["training"]["minimum_training_source_families"], 3)
        self.assertTrue(value["training"]["source_portfolio_frozen_in_pre_execution_manifest"])
        self.assertNotIn("training_sources", value["training"])
        self.assertEqual(value["source"]["minimum_independent_patients"], 60)
        self.assertEqual((value["source"]["source_id"], value["source"]["source_version"]),
                         ("busi-whu", "3"))
        self.assertEqual(value["statistics"]["bootstrap_draws"], 10000)
        self.assertEqual(value["statistics"]["lower_bound_index_zero_based"], 999)
        self.assertEqual(value["statistics"]["decision_margin"], {"denominator": 20, "numerator": 1})
        self.assertFalse(value["authorization"]["mmbu_public_content_allowed"])
        self.assertEqual(value["prompts"]["context_endpoint"], {
            "promotion_authority": "none",
            "replacement_requirements": [
                "image-dependent-target",
                "per-record-targets",
                "at-least-two-distinct-target-vectors",
                "independent-review-authority",
            ],
            "status": "blocked_uninformative_constant",
        })

    def test_scope_widening_and_protocol_drift_reject(self):
        mutations = (
            lambda value: value.__setitem__("unknown", True),
            lambda value: value["candidate"].__setitem__("model_id", "other/model"),
            lambda value: value["candidate"].__setitem__("selection_authority", "remote-response-screen"),
            lambda value: value["training"].__setitem__("lora_dropout", 0.05),
            lambda value: value["training"].__setitem__("seeds", [20261025]),
            lambda value: value["training"].__setitem__("optimizer_updates", 1025),
            lambda value: value["prompts"].__setitem__("parser", "repair-json"),
            lambda value: value["statistics"].__setitem__("decision_margin", {"denominator": 10, "numerator": 1}),
            lambda value: value["resources"].__setitem__("attempts_per_condition", 2),
            lambda value: value["resources"].__setitem__("automatic_rescue_allowed", True),
            lambda value: value["source"].__setitem__("source_id", "bus-uclm"),
            lambda value: value["source"].__setitem__("source_version", "v3"),
            lambda value: value["authorization"].__setitem__("mmbu_public_content_allowed", True),
        )
        for index, mutate in enumerate(mutations):
            changed = copy.deepcopy(self.value)
            mutate(changed)
            with self.subTest(index=index), self.assertRaises(ContractViolation):
                self.module.validate_spec(changed)


class HeldoutConfirmationLineageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def valid_lineage(self):
        return {
            "base_model_id": "Qwen/Qwen3.5-9B",
            "base_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
            "expected_parameter_count": 9409813744,
            "legacy_exploratory_adapter_used": False,
            "lora_alpha": 16,
            "lora_dropout": 0,
            "lora_rank": 8,
            "lora_target_suffixes": ["q_proj", "v_proj"],
            "mmbu_public_content_used": False,
            "optimizer_updates": 1024,
            "post_admission_retraining": True,
            "profile": "dual",
            "runtime_gate_id": "qwen3.5-9b-successor-native-runtime",
            "runtime_gate_passed": True,
            "source_purposes": {
                "busbra": "train", "semantic-family-a": "train", "semantic-family-b": "train",
            },
            "training_seed": 20261025,
        }

    def test_provisional_qwen_lineage_has_no_executable_candidate_authority(self):
        with self.assertRaises(ContractViolation):
            self.module.validate_checkpoint_lineage(self.valid_lineage())

    def test_ineligible_or_incomplete_lineage_rejects(self):
        mutations = (
            lambda row: row.__setitem__("unknown", True),
            lambda row: row.__setitem__("legacy_exploratory_adapter_used", True),
            lambda row: row.__setitem__("post_admission_retraining", False),
            lambda row: row.__setitem__("runtime_gate_passed", False),
            lambda row: row.__setitem__("runtime_gate_id", "qwen2.5-vl-b1"),
            lambda row: row.__setitem__("source_purposes", {
                "busbra": "train", "semantic-family-a": "train",
            }),
            lambda row: row.__setitem__("source_purposes", {
                "semantic-family-a": "train", "semantic-family-b": "train", "semantic-family-c": "train",
            }),
            lambda row: row["source_purposes"].__setitem__("semantic-family-b", "eval"),
            lambda row: row["source_purposes"].__setitem__("sémantic-family-c", "train"),
            lambda row: row.__setitem__("lora_dropout", 0.05),
            lambda row: row.__setitem__("optimizer_updates", 1023),
            lambda row: row.__setitem__("training_seed", 7),
            lambda row: row.__setitem__("mmbu_public_content_used", True),
        )
        for index, mutate in enumerate(mutations):
            changed = self.valid_lineage()
            mutate(changed)
            with self.subTest(index=index), self.assertRaises(ContractViolation):
                self.module.validate_checkpoint_lineage(changed)


class HeldoutConfirmationAdmissionBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def report(self, count=60):
        records = [f"record-{index:03d}" for index in range(count)]
        patients = [f"busi-whu:patient:{index:03d}" for index in range(count)]
        population = {
            "record_ids": records, "record_count": count,
            "patient_ids": patients, "patient_count": count,
            "patient_to_records": dict(zip(patients, ([record] for record in records), strict=True)),
        }
        target_map = {
            record: ("benign" if index % 2 == 0 else "malignant")
            for index, record in enumerate(records)
        }
        return canonical.seal({
            "schema_id": "mmbu.phase1.busi_whu_review_validation", "schema_version": 1,
            "packet_receipt_digest": "1" * 64, "packet_manifest_digest": "2" * 64,
            "opening_authorization_digest": "9" * 64, "opening_receipt_digest": "a" * 64,
            "review_opening_sha256": "3" * 64, "primary_review_sha256": "4" * 64,
            "secondary_review_sha256": "5" * 64, "adjudication_review_sha256": "6" * 64,
            "rights_review_sha256": "7" * 64, "reviewed_record_count": count,
            "target_map": target_map, "target_map_digest": canonical.value_digest(target_map),
            "global_task_manifest_digest": "8" * 64,
            "independently_reviewed_record_count": count, "adjudicated_record_count": 0,
            "eligible_by_task": {
                "global_classification": population,
                "grounded_classification": population,
                "localization": population,
                "context_prediction": population,
            },
            "excluded_record_ids": [], "unresolved_record_ids": [],
            "duplicate_group_constraints": [], "duplicate_excluded_record_ids": [],
            "purpose_decisions": {
                "confirmation_evaluation": "approve", "challenge_reporting": "approve",
                "publication": "approve", "source_artifact_redistribution": "decline",
                "trained_weight_release": "unresolved", "training": "decline",
            },
            "source_blockers": [], "confirmation_purposes_ready": True,
            "review_evidence_complete": True, "reviewer_identity_authenticated": True,
            "reviewer_role_ids": {
                "clinical_adjudicator": "reviewer-0",
                "data_rights_authority": "reviewer-1",
                "primary_breast_ultrasound_reviewer": "reviewer-2",
                "secondary_breast_ultrasound_reviewer": "reviewer-3",
            },
            "review_authentication": {
                "authenticated_at": "2026-10-25T06:00:00Z",
                "base_review_report_digest": "b" * 64,
                "clinical_assessment_digest": "c" * 64,
                "custodian_assessment_digest": "d" * 64,
                "opening_authorization_digest": "9" * 64,
                "opening_receipt_digest": "a" * 64,
                "review_attestation_digests": [value * 64 for value in "4567"],
            },
            "phase1_admission_still_required": True, "source_admission_authorized": False,
            "training_ready": False, "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })

    def authenticated_report(self):
        authority = ReviewAuthorityWorld()
        base = dict(self.report())
        base.pop("record_digest")
        base["opening_authorization_digest"] = authority.authorization["record_digest"]
        base["opening_receipt_digest"] = authority.world.digest("review_opening")
        base["reviewer_identity_authenticated"] = False
        base["review_authentication"] = None
        base = canonical.seal(base)
        store = authority.store()
        store.add(base)
        credentials = {
            record["role"]: record for record in authority.records.values()
            if record["schema_id"] == "mmbu.phase1.reviewer_credential_verification"
        }
        attestations = []
        for index, (role, credential) in enumerate(sorted(credentials.items())):
            attestation = canonical.seal({
                "schema_id": "mmbu.phase1.busi_whu_review_attestation", "schema_version": 1,
                "attestation_id": f"bridge-attestation-{index}",
                "credential_verification_digest": credential["record_digest"],
                "reviewer_id": credential["reviewer_id"], "role": role,
                "subject_digest": base["record_digest"], "subject_created_at": t("09:20:00"),
                "disposition": "approved", "limitations_digest": "e" * 64,
                "attested_at": t("09:30:00"),
            })
            store.add(attestation)
            attestations.append(attestation["record_digest"])
        findings = {
            "image_annotation_join_issue": "absent", "lesion_completeness_issue": "absent",
            "patient_identity_issue": "absent", "target_semantics_issue": "absent",
        }
        assessments = {}
        for role in ("clinical_adjudicator", "data_rights_authority"):
            credential = credentials[role]
            assessment = canonical.seal({
                "schema_id": "mmbu.phase1.busi_whu_source_assessment", "schema_version": 1,
                "assessment_id": f"bridge-assessment-{role}", "role": role,
                "assessor_id": credential["reviewer_id"],
                "credential_verification_digest": credential["record_digest"],
                "subject_digest": base["record_digest"], "subject_created_at": t("09:20:00"),
                "findings": findings, "assessed_at": t("09:31:00"),
            })
            store.add(assessment)
            assessments[role] = assessment["record_digest"]
        subject = completed_review_authority_subject(
            base, attestations, assessments["clinical_adjudicator"],
            assessments["data_rights_authority"], report_created_at=t("09:20:00"),
            authenticated_at=t("09:40:00"),
        )
        external = external_authority_for(
            subject, namespace="mmbu.phase1.busi-whu-completed-review.v1",
            principal="external-review-board", role="review-board-authority",
            signed_at=t("09:35:00"), verified_at=t("09:39:00"),
        )
        report = authenticate_completed_review(
            base, store, authority.authorization["record_digest"], authority.world.digest("review_opening"),
            attestations, assessments["clinical_adjudicator"], assessments["data_rights_authority"],
            report_created_at=t("09:20:00"), now=t("09:40:00"), external_authority=external,
        )
        return report, store.records(), external

    def admission(self, report, evidence_records=()):
        world = AdmissionWorld(
            proposed=["confirmation"], source_id="busi-whu", version="3", family="busi-whu",
            extra_admission_input_digests=[report["record_digest"]],
        )
        world.extra.append(report)
        source_digest = world.digest("source_approved")
        split = copy.deepcopy(world.get("split_engineering"))
        split.pop("record_digest")
        split.update(split_id="split-confirmation", role="confirmation", created_at=t("08:39:30"))
        split = canonical.seal(split)
        world.single(
            "confirmation_authorization",
            world.authorization(
                "auth-confirmation", "confirmation", source_digest,
                [split["record_digest"]], [], t("08:42:00"),
            ),
            "purpose_authorization_reviewer", ["confirmation"],
            "syn-purpose-reviewer", t("08:42:00"),
        )
        admission_store = world.store(split)
        if evidence_records:
            records = [
                record for record in admission_store.records()
                if record["schema_id"] != "mmbu.phase1.opening_receipt_registry"
            ]
            admission_store = RecordStore([*records, *evidence_records])
        return admission_store, source_digest, world.digest("confirmation_authorization"), world

    def source_external(self, store, source_digest):
        subject = admission.source_admission_authority_subject(store, source_digest)
        return external_authority_for(
            subject, namespace="mmbu.phase1.source-admission.v1",
            principal="external-source-board", role="source-admission-authority",
            signed_at=t("09:42:00"), verified_at=t("09:43:00"),
        )

    def confirmation_external(self, report, source_digest, purpose_digest, source_external):
        subject = self.module.confirmation_authority_subject(
            report, source_digest, purpose_digest, source_external,
        )
        return external_authority_for(
            subject, namespace="mmbu.phase1.busi-whu-confirmation.v1",
            principal="external-confirmation-board", role="confirmation-authority",
            signed_at=t("09:45:00"), verified_at=t("09:46:00"),
        )

    def test_authenticated_review_builds_existing_population_inputs(self):
        report, evidence_records, external = self.authenticated_report()
        store, source_digest, purpose_digest, _ = self.admission(report, evidence_records)
        source_external = self.source_external(store, source_digest)
        confirmation_external = self.confirmation_external(
            report, source_digest, purpose_digest, source_external,
        )
        manifest = self.module.build_confirmation_source_manifest(
            report, store, source_digest, purpose_digest, external_authority=external,
            source_external_authority=source_external,
            confirmation_external_authority=confirmation_external,
        )
        self.assertEqual(manifest["patient_count"], 60)
        self.assertEqual(len(manifest["patient_to_records"]), 60)
        artifacts = self.module.build_authenticated_randomization_artifacts(
            report, manifest, store, source_digest, purpose_digest,
            created_at="2026-10-25T12:00:00Z", external_authority=external,
            source_external_authority=source_external,
            confirmation_external_authority=confirmation_external,
        )
        self.assertEqual(artifacts["population_binding"]["source_manifest_digest"], manifest["record_digest"])
        self.assertEqual(artifacts["target_map_digest"], manifest["target_map_digest"])
        self.assertFalse(hasattr(self.module, "build_randomization_artifacts"))

    def test_confirmation_transition_requires_exact_external_authority(self):
        report, evidence_records, review_external = self.authenticated_report()
        store, source_digest, purpose_digest, _ = self.admission(report, evidence_records)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, store, source_digest, purpose_digest,
                external_authority=review_external,
            )
        source_external = self.source_external(store, source_digest)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, store, source_digest, purpose_digest,
                external_authority=review_external,
                confirmation_external_authority=object(),
            )
        wrong = self.confirmation_external(
            report, source_digest, "f" * 64, source_external,
        )
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, store, source_digest, purpose_digest,
                external_authority=review_external,
                source_external_authority=source_external,
                confirmation_external_authority=wrong,
            )
        subject = self.module.confirmation_authority_subject(
            report, source_digest, purpose_digest, source_external,
        )
        same_principal = external_authority_for(
            subject, namespace="mmbu.phase1.busi-whu-confirmation.v1",
            principal=review_external.principal, role="confirmation-authority",
            signed_at=t("09:45:00"), verified_at=t("09:46:00"),
        )
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, store, source_digest, purpose_digest,
                external_authority=review_external,
                source_external_authority=source_external,
                confirmation_external_authority=same_principal,
            )

    def test_admitted_report_with_fabricated_authentication_chain_rejects(self):
        report = self.report()
        store, source_digest, purpose_digest, _ = self.admission(report)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, store, source_digest, purpose_digest
            )

    def test_authenticated_report_cannot_substitute_review_participant_identities(self):
        report, evidence_records, external = self.authenticated_report()
        forged = copy.deepcopy(report)
        forged["reviewer_role_ids"]["primary_breast_ultrasound_reviewer"] = "different-person"
        forged["record_digest"] = canonical.record_digest(forged)
        store, source_digest, purpose_digest, _ = self.admission(forged, evidence_records)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                forged, store, source_digest, purpose_digest, external_authority=external,
            )

    def test_unauthenticated_training_leakage_underpowered_and_cross_patient_duplicates_reject(self):
        report = self.report()
        store, source_digest, purpose_digest, world = self.admission(report)
        unauthenticated = copy.deepcopy(report)
        unauthenticated["reviewer_identity_authenticated"] = False
        unauthenticated["record_digest"] = canonical.record_digest(unauthenticated)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                unauthenticated, store, source_digest, purpose_digest
            )
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, RecordStore(), source_digest, purpose_digest
            )
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                report, store, source_digest, world.digest("engineering_authorization")
            )
        forged = copy.deepcopy(report)
        forged["primary_review_sha256"] = "8" * 64
        forged["record_digest"] = canonical.record_digest(forged)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(
                forged, store, source_digest, purpose_digest
            )
        with self.assertRaises(ContractViolation):
            underpowered = self.report(59)
            self.module.build_confirmation_source_manifest(underpowered, store, source_digest, purpose_digest)
        duplicate = self.report()
        duplicate["duplicate_group_constraints"] = [{
            "group_type": "exact", "digest": "a" * 64,
            "record_ids": ["record-000", "record-001"],
            "patient_ids": ["busi-whu:patient:000", "busi-whu:patient:001"],
        }]
        duplicate["record_digest"] = canonical.record_digest(duplicate)
        with self.assertRaises(ContractViolation):
            self.module.build_confirmation_source_manifest(duplicate, store, source_digest, purpose_digest)

    def test_post_lock_manifest_mutation_rejects(self):
        report, evidence_records, external = self.authenticated_report()
        store, source_digest, purpose_digest, _ = self.admission(report, evidence_records)
        source_external = self.source_external(store, source_digest)
        confirmation_external = self.confirmation_external(
            report, source_digest, purpose_digest, source_external,
        )
        manifest = self.module.build_confirmation_source_manifest(
            report, store, source_digest, purpose_digest, external_authority=external,
            source_external_authority=source_external,
            confirmation_external_authority=confirmation_external,
        )
        manifest["patient_to_records"][manifest["patient_ids"][0]].append("injected")
        with self.assertRaises(ContractViolation):
            self.module.validate_confirmation_source_manifest(
                manifest, report, store, source_digest, purpose_digest,
                external_authority=external,
                source_external_authority=source_external,
                confirmation_external_authority=confirmation_external,
            )
        manifest = self.module.build_confirmation_source_manifest(
            report, store, source_digest, purpose_digest, external_authority=external,
            source_external_authority=source_external,
            confirmation_external_authority=confirmation_external,
        )
        record_id = manifest["record_ids"][0]
        manifest["target_map"][record_id] = (
            "malignant" if manifest["target_map"][record_id] == "benign" else "benign"
        )
        with self.assertRaises(ContractViolation):
            self.module.validate_confirmation_source_manifest(
                manifest, report, store, source_digest, purpose_digest,
                external_authority=external,
                source_external_authority=source_external,
                confirmation_external_authority=confirmation_external,
            )


class HeldoutConfirmationStatisticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def patients(self):
        return [f"patient-{index:03d}" for index in range(60)]

    def rows(self):
        rows = []
        prompts = json.loads(SPEC.read_text(encoding="utf-8"))["prompts"]
        prompt_digest = canonical.value_digest(prompts)
        context_target = '{"body_part":"breast","medical_domain":"breast imaging","modality":"ultrasound"}'
        for patient_id in self.patients():
            for condition in ("base", "seed-20261025", "seed-20261026", "seed-20261027"):
                adapted = condition != "base"
                target = "benign" if int(patient_id[-3:]) % 2 == 0 else "malignant"
                task_raw = target if adapted else ("malignant" if target == "benign" else "benign")
                context_raw = context_target if adapted else "{}"
                rows.append({
                    "condition_id": condition,
                    "output_failed": False,
                    "patient_id": patient_id,
                    "post_reload_context_raw_output": context_raw,
                    "post_reload_task_raw_output": task_raw,
                    "pre_reload_context_raw_output": context_raw,
                    "pre_reload_task_raw_output": task_raw,
                    "prompt_spec_digest": prompt_digest,
                    "record_id": patient_id + "::image-0",
                    "target_label": target,
                })
        return rows

    def artifacts(self):
        return self.artifacts_for(self.patients())

    def artifacts_for(self, patient_ids, patient_to_records=None):
        if patient_to_records is None:
            patient_to_records = {patient_id: [patient_id + "::image-0"] for patient_id in patient_ids}
        fixture = {
            "synthetic_only": True,
            "biomedical_content_used": False,
            "mmbu_public_content_used": False,
            "patient_ids": patient_ids,
            "patient_to_records": patient_to_records,
            "target_map": {
                record_id: ("benign" if int(patient_id[-3:]) % 2 == 0 else "malignant")
                for patient_id, record_ids in patient_to_records.items()
                for record_id in record_ids
            },
        }
        return self.module.build_synthetic_randomization_artifacts(
            fixture,
            created_at="2026-10-25T12:00:00Z",
        )

    def analyze(self, rows, artifacts=None, *, first_output_at="2026-10-25T12:00:01Z"):
        artifacts = artifacts or self.artifacts()
        lock = self.module.build_confirmation_lock(
            artifacts, locked_at="2026-10-25T12:00:00.5Z", opening_receipt_digest="e" * 64
        )
        return self.module.analyze_patient_results(
            rows, artifacts, confirmation_lock=lock, first_output_at=first_output_at
        )

    def test_exact_patient_analysis_uses_locked_matrices(self):
        result = self.analyze(self.rows())
        self.assertEqual(result["patient_count"], 60)
        self.assertEqual(result["point_delta"], rational.to_wire(1))
        self.assertEqual(result["lower_bound"], rational.to_wire(1))
        self.assertEqual(result["seed_deltas"], {
            "seed-20261025": rational.to_wire(1),
            "seed-20261026": rational.to_wire(1),
            "seed-20261027": rational.to_wire(1),
        })
        self.assertEqual(result["base"]["task"], rational.to_wire(0))
        self.assertEqual(result["seed_mean"]["context"], rational.to_wire(1))
        seed = result["secondary"]["conditions"]["seed-20261025"]
        self.assertEqual(seed["task"], rational.to_wire(1))
        self.assertEqual(seed["context"], rational.to_wire(1))
        self.assertEqual(seed["q"], rational.to_wire(1))
        self.assertEqual(seed["context_validity"], rational.to_wire(1))
        self.assertEqual(seed["context_fields"], {
            "body_part": rational.to_wire(1),
            "medical_domain": rational.to_wire(1),
            "modality": rational.to_wire(1),
        })
        self.assertEqual(seed["class_balanced_accuracy"], rational.to_wire(1))
        self.assertEqual(seed["output_failure_rate"], rational.to_wire(0))

    def test_population_and_chronology_drift_reject(self):
        with self.assertRaises(ContractViolation):
            self.artifacts_for(self.patients()[:-1])
        with self.assertRaises(ContractViolation):
            self.artifacts_for(list(reversed(self.patients())))
        with self.assertRaises(ContractViolation):
            self.analyze(self.rows(), first_output_at="2026-10-25T11:59:59Z")

    def test_missing_duplicate_and_matrix_drift_reject(self):
        rows = self.rows()
        for changed in (rows[:-1], rows + [copy.deepcopy(rows[0])]):
            with self.assertRaises(ContractViolation):
                self.analyze(changed)
        artifact = self.artifacts()
        lock = self.module.build_confirmation_lock(
            artifact, locked_at="2026-10-25T12:00:00.5Z", opening_receipt_digest="e" * 64
        )
        artifact["index_matrix"][0][0] = 59
        artifact["index_matrix_digest"] = canonical.value_digest(artifact["index_matrix"])
        with self.assertRaises(ContractViolation):
            self.module.analyze_patient_results(
                rows, artifact, confirmation_lock=lock, first_output_at="2026-10-25T12:00:01Z"
            )

        mapping = {patient_id: [patient_id + "::image-0"] for patient_id in self.patients()}
        mapping["patient-001"] = mapping["patient-000"]
        with self.assertRaises(ContractViolation):
            self.artifacts_for(self.patients(), mapping)

    def test_consistent_target_flip_across_every_condition_rejects(self):
        rows = self.rows()
        record_id = rows[0]["record_id"]
        for row in rows:
            if row["record_id"] == record_id:
                row["target_label"] = "malignant" if row["target_label"] == "benign" else "benign"
        with self.assertRaises(ContractViolation):
            self.analyze(rows)

    def test_failures_stay_as_exact_zero_and_floats_reject(self):
        rows = self.rows()
        rows[0]["output_failed"] = True
        for key in ("pre_reload_task_raw_output", "pre_reload_context_raw_output",
                    "post_reload_task_raw_output", "post_reload_context_raw_output"):
            rows[0][key] = None
        result = self.analyze(rows)
        self.assertEqual(result["output_failure_count"], 1)
        self.assertEqual(result["reload_mismatch_count"], 1)

        rows = self.rows()
        rows[0]["pre_reload_task_raw_output"] = 0.0
        with self.assertRaises(ContractViolation):
            self.analyze(rows)

        rows = self.rows()
        rows[0]["post_reload_task_raw_output"] = "different"
        with self.assertRaises(ContractViolation):
            self.analyze(rows)

    def test_partial_context_scores_fields_individually(self):
        rows = self.rows()
        partial = '{"body_part":"breast","medical_domain":"breast imaging","modality":"mri"}'
        rows[1]["pre_reload_context_raw_output"] = partial
        rows[1]["post_reload_context_raw_output"] = partial
        result = self.analyze(rows)
        self.assertEqual(result["seed_mean"]["context"], rational.to_wire(rational.Fraction(539, 540)))
        seed = result["secondary"]["conditions"]["seed-20261025"]
        self.assertEqual(seed["context_validity"], rational.to_wire(1))
        self.assertEqual(seed["context_fields"]["body_part"], rational.to_wire(1))
        self.assertEqual(seed["context_fields"]["medical_domain"], rational.to_wire(1))
        self.assertEqual(seed["context_fields"]["modality"], rational.to_wire(rational.Fraction(59, 60)))


class HeldoutConfirmationDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def analysis(self):
        return {
            "base": {
                "context": rational.to_wire(1),
                "q": rational.to_wire(rational.Fraction(1, 5)),
                "task": rational.to_wire(0),
            },
            "class_diagnostics": {},
            "lower_bound": rational.to_wire(rational.Fraction(1, 10)),
            "output_failure_count": 0,
            "patient_count": 60,
            "point_delta": rational.to_wire(rational.Fraction(1, 10)),
            "reload_mismatch_count": 0,
            "secondary": {"conditions": {}, "seed_mean": {}},
            "seed_deltas": {
                "seed-20261025": rational.to_wire(rational.Fraction(1, 10)),
                "seed-20261026": rational.to_wire(rational.Fraction(1, 10)),
                "seed-20261027": rational.to_wire(rational.Fraction(1, 10)),
            },
            "seed_mean": {"context": rational.to_wire(1), "q": rational.to_wire(1), "task": rational.to_wire(1)},
            "sign_randomization_p": rational.to_wire(1),
        }

    def execution(self):
        return {
            "adapted_attempts": {"seed-20261025": 1, "seed-20261026": 1, "seed-20261027": 1},
            "base_attempts": 1,
            "identity_drift": False,
            "mmbu_public_content_used": False,
            "source_id": "busi-whu",
            "source_version": "3",
            "source_role": "confirmation",
        }

    def test_primary_mechanics_pass_ignores_only_secondary_and_sign_diagnostic(self):
        result = self.module._confirmation_decision_mechanics(self.analysis(), self.execution())
        self.assertEqual(result, {"reasons": [], "status": "confirmation_passed"})

    def test_production_decision_is_blocked_by_uninformative_constant_context_endpoint(self):
        result = self.module.confirmation_decision(self.analysis(), self.execution())
        self.assertEqual(result, {
            "reasons": ["context_endpoint_uninformative_constant"],
            "status": "blocked",
        })

    def test_context_and_competition_proxy_are_conjunctive_gates(self):
        analysis = self.analysis()
        analysis["seed_mean"]["context"] = rational.to_wire(rational.Fraction(19, 20))
        result = self.module._confirmation_decision_mechanics(analysis, self.execution())
        self.assertEqual(result["status"], "confirmation_failed")
        self.assertIn("context_below_base", result["reasons"])

        analysis = self.analysis()
        analysis["seed_mean"]["q"] = analysis["base"]["q"]
        result = self.module._confirmation_decision_mechanics(analysis, self.execution())
        self.assertEqual(result["status"], "confirmation_failed")
        self.assertIn("competition_proxy_not_improved", result["reasons"])

    def test_exact_margin_nonpositive_seed_and_lower_bound_fail(self):
        changes = (
            ("point_delta", rational.to_wire(rational.Fraction(1, 20)), "point_delta_not_above_margin"),
            ("lower_bound", rational.to_wire(rational.Fraction(1, 20)), "lower_bound_not_above_margin"),
        )
        for key, value, reason in changes:
            analysis = self.analysis()
            analysis[key] = value
            result = self.module._confirmation_decision_mechanics(analysis, self.execution())
            self.assertEqual(result["status"], "confirmation_failed")
            self.assertIn(reason, result["reasons"])
        analysis = self.analysis()
        analysis["seed_deltas"]["seed-20261026"] = rational.to_wire(0)
        result = self.module._confirmation_decision_mechanics(analysis, self.execution())
        self.assertIn("nonpositive_seed_delta:seed-20261026", result["reasons"])

    def test_execution_failures_cannot_be_rescued(self):
        mutations = (
            (lambda row: row.__setitem__("base_attempts", 2), "base_attempt_count"),
            (lambda row: row["adapted_attempts"].__setitem__("seed-20261027", 2), "adapted_attempt_count:seed-20261027"),
            (lambda row: row.__setitem__("identity_drift", True), "identity_drift"),
        )
        for mutate, reason in mutations:
            execution = self.execution()
            mutate(execution)
            result = self.module._confirmation_decision_mechanics(self.analysis(), execution)
            self.assertEqual(result["status"], "confirmation_failed")
            self.assertIn(reason, result["reasons"])

    def test_underpowered_and_source_substitution_are_terminal(self):
        analysis = self.analysis()
        analysis["patient_count"] = 59
        self.assertEqual(
            self.module._confirmation_decision_mechanics(analysis, self.execution())["status"], "underpowered"
        )
        execution = self.execution()
        execution["source_id"] = "bus-uclm"
        result = self.module._confirmation_decision_mechanics(self.analysis(), execution)
        self.assertEqual(result, {"reasons": ["source_identity_or_role"], "status": "blocked"})


class HeldoutConfirmationReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def lineage(self, seed):
        row = HeldoutConfirmationLineageTests().valid_lineage()
        row["training_seed"] = seed
        return row

    def manifest(self):
        return {
            "attempts_started": {
                "base": 0, "seed-20261025": 0, "seed-20261026": 0, "seed-20261027": 0,
            },
            "checkpoint_lineages": [self.lineage(seed) for seed in (20261025, 20261026, 20261027)],
            "chronology": {
                "confirmation_lock_at": "2026-10-25T12:00:03Z",
                "first_output_at": None,
                "inventory_closed_at": "2026-10-25T12:00:00Z",
                "qa_opened_at": "2026-10-25T12:00:02Z",
                "qa_plan_frozen_at": "2026-10-25T12:00:01Z",
            },
            "gate_records": {gate: "a" * 64 for gate in (
                "training-source-admission", "successor-runtime", "checkpoint-retraining-lineage",
                "confirmation-source-acquisition", "rights-review", "protected-inventory",
                "qa-lock-and-review", "duplicate-review", "confirmation-purpose-authorization",
                "eligible-population-lock", "hermetic-decision-receipt", "opening-and-execution-lock",
            )},
            "mmbu_public_content_used": False,
            "source_id": "busi-whu",
            "source_version": "3",
            "source_role": "confirmation",
        }

    def test_first_missing_gate_is_reported_in_frozen_order(self):
        manifest = self.manifest()
        manifest["gate_records"]["successor-runtime"] = None
        manifest["gate_records"]["training-source-admission"] = None
        self.assertEqual(self.module.readiness_status(manifest), {
            "missing": "training-source-admission", "status": "blocked",
        })

    def test_complete_digest_references_remain_blocked_without_authority_validation(self):
        self.assertEqual(self.module.readiness_status(self.manifest()), {
            "missing": "context-endpoint-authority", "status": "blocked",
        })

    def test_drift_attempts_and_qa_order_reject(self):
        mutations = (
            lambda row: row.__setitem__("mmbu_public_content_used", True),
            lambda row: row.__setitem__("source_id", "bus-uclm"),
            lambda row: row["attempts_started"].__setitem__("base", 1),
            lambda row: row["chronology"].__setitem__("qa_plan_frozen_at", "2026-10-25T11:59:59Z"),
            lambda row: row["chronology"].__setitem__("first_output_at", "2026-10-25T12:00:04Z"),
            lambda row: row["checkpoint_lineages"][0].__setitem__("legacy_exploratory_adapter_used", True),
        )
        for mutate in mutations:
            manifest = self.manifest()
            mutate(manifest)
            with self.assertRaises(ContractViolation):
                self.module.readiness_status(manifest)

    def test_all_seed_lineages_share_one_prospective_source_portfolio(self):
        manifest = self.manifest()
        manifest["checkpoint_lineages"][2]["source_purposes"] = {
            "busbra": "train", "semantic-family-a": "train", "semantic-family-c": "train",
        }
        with self.assertRaises(ContractViolation):
            self.module.readiness_status(manifest)

    def test_command_has_only_three_safe_modes_and_no_runtime_imports(self):
        source = TOOL.read_text(encoding="utf-8")
        for forbidden in ("subprocess", "socket", "requests", "transformers", "datasets", "torch", "paramiko", "slurm", "sbatch"):
            self.assertNotIn(forbidden, source)
        result = subprocess.run(
            [sys.executable, str(TOOL), "validate-spec", "--spec", str(SPEC)],
            cwd=REPO, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "valid")
        result = subprocess.run(
            [sys.executable, str(TOOL), "not-a-mode"], cwd=REPO, text=True, capture_output=True, check=False,
        )
        self.assertNotEqual(result.returncode, 0)

        result = subprocess.run(
            [sys.executable, str(TOOL), "synthetic-check", "--manifest", str(FIXTURES / "positive.json")],
            cwd=REPO, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "confirmation_passed")

    def test_readiness_command_reports_missing_without_opening_references(self):
        manifest = self.manifest()
        manifest["gate_records"]["rights-review"] = None
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(TOOL), "readiness", "--manifest", str(path)],
                cwd=REPO, text=True, capture_output=True, check=False,
            )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(json.loads(result.stdout), {"missing": "rights-review", "status": "blocked"})


class HeldoutConfirmationFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = importlib.import_module("mmbu_phase1.heldout_confirmation")

    def test_closed_synthetic_fixtures_have_expected_outcomes(self):
        expected = {
            "positive.json": "confirmation_passed",
            "threshold-failure.json": "confirmation_failed",
            "underpowered.json": "underpowered",
        }
        for name, status in expected.items():
            path = FIXTURES / name
            self.assertTrue(path.is_file(), name)
            fixture = json.loads(path.read_text(encoding="utf-8"))
            result = self.module.validate_synthetic_fixture(fixture)
            self.assertEqual(result["status"], status)
            self.assertEqual(result["evidence_scope"], "synthetic_mechanics_only")
            self.assertFalse(result["promotion_eligible"])
            self.assertFalse(result["readiness_evidence"])

    def test_fixture_boundary_and_unknown_fields_reject(self):
        fixture = json.loads((FIXTURES / "positive.json").read_text(encoding="utf-8"))
        mutations = (
            lambda row: row.__setitem__("unknown", True),
            lambda row: row.__setitem__("synthetic_only", False),
            lambda row: row.__setitem__("biomedical_content_used", True),
            lambda row: row.__setitem__("mmbu_public_content_used", True),
            lambda row: row.__setitem__("expected_status", "ready_for_authorized_execution"),
        )
        for mutate in mutations:
            changed = copy.deepcopy(fixture)
            mutate(changed)
            with self.assertRaises(ContractViolation):
                self.module.validate_synthetic_fixture(changed)


if __name__ == "__main__":
    unittest.main()
