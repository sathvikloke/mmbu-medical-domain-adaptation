import copy
import unittest

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.store import RecordStore

from mmbu_phase1.busi_whu_authority import (
    ReviewOpeningCapability,
    validate_busi_whu_review_opening,
    validate_credential_verification,
    validate_review_attestation,
    validate_review_opening_authorization,
)
from tests.phase1.admission_fixtures import AdmissionWorld, d, t


P = "mmbu.phase1."
ROLES = {
    "clinical_adjudicator": "board_certified_radiologist",
    "data_rights_authority": "institutional_data_rights_authority",
    "primary_breast_ultrasound_reviewer": "board_certified_breast_imager",
    "secondary_breast_ultrasound_reviewer": "board_certified_breast_imager",
}
OPERATIONS = ["decode_annotation_bmp", "decode_image_bmp", "read_workbook_geometry"]


def seal(value):
    return canonical.seal(value)


class ReviewAuthorityWorld:
    def __init__(self, mutate=None):
        self.artifacts = [
            {"logical_path": "busi-whu/archive.zip", "bytes": 4096, "sha256": d("archive-bytes")},
            {"logical_path": "busi-whu/metadata.xlsx", "bytes": 120, "sha256": d("workbook-bytes")},
        ]
        self.world = AdmissionWorld(
            source_id="busi-whu", version="3", family="busi-whu", artifacts=self.artifacts,
        )
        self.records = {}
        self.mutate = mutate
        self._build()

    def add(self, name, value):
        value = copy.deepcopy(value)
        if self.mutate is not None:
            self.mutate(name, value, self)
        self.records[name] = seal(value)
        return self.records[name]

    def _build(self):
        credentials = []
        for index, (role, qualification) in enumerate(sorted(ROLES.items())):
            row = self.add(f"credential_{role}", {
                "schema_id": P + "reviewer_credential_verification",
                "schema_version": 1,
                "credential_id": f"credential-{index}",
                "reviewer_id": f"reviewer-{index}",
                "role": role,
                "qualification_class": qualification,
                "qualification_evidence_digest": d(f"qualification-{index}"),
                "verifier_id": f"verifier-{index}",
                "verification_artifact_digest": d(f"credential-proof-{index}"),
                "permitted_purposes": ["busi_whu_clinical_review"],
                "verified_at": t("08:50:00"),
                "expires_at": t("10:50:00"),
                "supersedes_digest": None,
            })
            credentials.append(row["record_digest"])

        inputs = sorted([
            self.world.digest("manifest"), d("busi-metadata"), d("review-selection"),
            d("review-schema"), d("duplicate-contract"), d("busbra-fingerprints"),
        ])
        review_lock = self.world.lock(
            "busi-whu-clinical-review", "custody_inventory", None, inputs,
            d("review-population"), [], t("09:00:00"), t("09:10:00"),
        )
        self.world.seal("review_lock", review_lock)

        artifacts = [
            {
                "logical_path": "busi-whu/archive.zip",
                "role": "archive",
                "bytes": 4096,
                "sha256": d("archive-bytes"),
            },
            {
                "logical_path": "busi-whu/metadata.xlsx",
                "role": "archive",
                "bytes": 120,
                "sha256": d("workbook-bytes"),
            },
        ]
        authorization = self.add("authorization", {
            "schema_id": P + "busi_whu_review_opening_authorization",
            "schema_version": 1,
            "authorization_id": "busi-whu-review-opening-1",
            "source_id": "busi-whu",
            "source_version": "3",
            "source_artifact_manifest_digest": self.world.digest("manifest"),
            "quarantine_source_digest": self.world.digest("source_quarantined"),
            "metadata_inventory_digest": d("busi-metadata"),
            "review_selection_digest": d("review-selection"),
            "review_schema_digest": d("review-schema"),
            "duplicate_contract_digest": d("duplicate-contract"),
            "repository_revision": "a" * 40,
            "artifact_bindings": artifacts,
            "credential_verification_digests": sorted(credentials),
            "fingerprint_inventories": [
                {"source_id": "bus-bra", "source_version": "1", "inventory_digest": d("busbra-fingerprints")},
            ],
            "allowed_operations": OPERATIONS,
            "output_root": "/storage/scr/npl015/mmbu/review-1",
            "maximum_attempts": 1,
            "network_access_allowed": False,
            "model_use_allowed": False,
            "training_allowed": False,
            "mmbu_public_access_allowed": False,
            "upload_allowed": False,
            "submission_allowed": False,
            "prospective_lock_digest": self.world.digest("review_lock"),
            "authorized_at": t("09:05:00"),
            "expires_at": t("10:05:00"),
        })

        authority_registry = self.add("authority_registry", {
            "schema_id": P + "busi_whu_review_authority_registry",
            "schema_version": 1,
            "registry_id": "busi-whu-review-authority",
            "generation": 0,
            "supersedes_registry_digest": None,
            "authorization_digests": [authorization["record_digest"]],
            "active_authorization_digest": authorization["record_digest"],
            "revoked_digests": [],
            "created_at": t("09:06:00"),
        })

        opening = self.world.opening(
            "busi-whu-review-opening",
            self.world.get("review_lock"),
            sorted([authorization["record_digest"], self.world.digest("manifest")]),
            t("09:10:00"),
        )
        self.world.seal("review_opening", opening)
        old_registry = self.world.get("opening_g1")
        heads = list(old_registry["heads"]) + [
            self.world.head(self.world.digest("review_lock"), self.world.get("review_opening"))
        ]
        self.world.seal("opening_g2", self.world.opening_registry(
            2, self.world.digest("opening_g1"), heads, t("09:10:01"),
        ))
        self.authorization = authorization
        self.authority_registry = authority_registry

    def store(self):
        return self.world.store(*self.records.values())


class ClosedRecordTests(unittest.TestCase):
    def test_credential_is_closed_and_verifier_is_independent(self):
        world = ReviewAuthorityWorld()
        credential = copy.deepcopy(world.records["credential_clinical_adjudicator"])
        credential["unknown"] = True
        credential = seal({k: v for k, v in credential.items() if k != "record_digest"})
        with self.assertRaises(ContractViolation):
            validate_credential_verification(credential)

        credential = copy.deepcopy(world.records["credential_clinical_adjudicator"])
        credential["verifier_id"] = credential["reviewer_id"]
        credential = seal({k: v for k, v in credential.items() if k != "record_digest"})
        with self.assertRaises(ContractViolation):
            validate_credential_verification(credential)

    def test_review_attestation_requires_post_subject_chronology(self):
        credential = ReviewAuthorityWorld().records["credential_clinical_adjudicator"]
        attestation = seal({
            "schema_id": P + "busi_whu_review_attestation",
            "schema_version": 1,
            "attestation_id": "completed-review-attestation",
            "credential_verification_digest": credential["record_digest"],
            "reviewer_id": credential["reviewer_id"],
            "role": credential["role"],
            "subject_digest": d("completed-report"),
            "subject_created_at": t("09:30:00"),
            "disposition": "approved",
            "limitations_digest": d("limitations"),
            "attested_at": t("09:29:59"),
        })
        with self.assertRaises(ContractViolation):
            validate_review_attestation(attestation)

    def test_authorization_is_exactly_busi_whu_v3_and_exact_operations(self):
        world = ReviewAuthorityWorld()
        for field, bad in (("source_id", "busi-whu-v3"), ("source_version", "v3")):
            authorization = copy.deepcopy(world.authorization)
            authorization[field] = bad
            authorization = seal({k: v for k, v in authorization.items() if k != "record_digest"})
            with self.assertRaises(ContractViolation):
                validate_review_opening_authorization(authorization)

        authorization = copy.deepcopy(world.authorization)
        authorization["allowed_operations"] = sorted(OPERATIONS + ["read_label_values"])
        authorization = seal({k: v for k, v in authorization.items() if k != "record_digest"})
        with self.assertRaises(ContractViolation):
            validate_review_opening_authorization(authorization)


class OpeningChainTests(unittest.TestCase):
    def test_positive_chain_returns_private_immutable_capability(self):
        world = ReviewAuthorityWorld()
        capability = validate_busi_whu_review_opening(
            world.store(), world.authorization["record_digest"],
            world.world.digest("review_opening"), t("09:10:02"),
        )
        self.assertIs(type(capability), ReviewOpeningCapability)
        self.assertEqual(capability.source_id, "busi-whu")
        self.assertEqual(capability.source_version, "3")
        self.assertEqual(capability.maximum_attempts, 1)
        with self.assertRaises((AttributeError, TypeError)):
            capability.source_id = "changed"

    def test_late_credential_and_reused_reviewer_reject(self):
        def late(name, record, _world):
            if name == "credential_clinical_adjudicator":
                record["verified_at"] = t("09:05:01")

        with self.assertRaises(ContractViolation):
            world = ReviewAuthorityWorld(late)
            validate_busi_whu_review_opening(
                world.store(), world.authorization["record_digest"],
                world.world.digest("review_opening"), t("09:10:02"),
            )

        def reused(name, record, world):
            if name == "credential_secondary_breast_ultrasound_reviewer":
                record["reviewer_id"] = world.records["credential_primary_breast_ultrasound_reviewer"]["reviewer_id"]

        with self.assertRaises(ContractViolation):
            world = ReviewAuthorityWorld(reused)
            validate_busi_whu_review_opening(
                world.store(), world.authorization["record_digest"],
                world.world.digest("review_opening"), t("09:10:02"),
            )

    def test_non_head_authorization_and_opening_reject(self):
        world = ReviewAuthorityWorld()
        stale_auth = copy.deepcopy(world.authorization)
        stale_auth["authorization_id"] = "stale"
        stale_auth["authorized_at"] = t("09:04:00")
        stale_auth = seal({k: v for k, v in stale_auth.items() if k != "record_digest"})
        store = world.store()
        store.add(stale_auth)
        with self.assertRaises(ContractViolation):
            validate_busi_whu_review_opening(
                store, stale_auth["record_digest"], world.world.digest("review_opening"), t("09:10:02"),
            )

        old_opening = world.world.get("inventory_opening")
        with self.assertRaises(ContractViolation):
            validate_busi_whu_review_opening(
                world.store(), world.authorization["record_digest"], old_opening["record_digest"], t("09:10:02"),
            )

    def test_expired_or_widened_authority_rejects(self):
        world = ReviewAuthorityWorld()
        with self.assertRaises(ContractViolation):
            validate_busi_whu_review_opening(
                world.store(), world.authorization["record_digest"],
                world.world.digest("review_opening"), t("10:05:01"),
            )


if __name__ == "__main__":
    unittest.main()
