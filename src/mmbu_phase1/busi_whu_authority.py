"""Fail-closed authority for protected BUSI-WHU clinical-review opening.

This module validates records and synthetic fixtures only.  It does not open
payloads.  A validated capability is intentionally the sole input accepted by
the protected I/O layer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mmbu_phase1 import admission, fields as f, locks, registries
from mmbu_phase1.store import RecordStore


SOURCE_ID = "busi-whu"
SOURCE_VERSION = "3"
PURPOSE = "busi_whu_clinical_review"
ROLES = (
    "clinical_adjudicator",
    "data_rights_authority",
    "primary_breast_ultrasound_reviewer",
    "secondary_breast_ultrasound_reviewer",
)
QUALIFICATIONS = {
    "clinical_adjudicator": "board_certified_radiologist",
    "data_rights_authority": "institutional_data_rights_authority",
    "primary_breast_ultrasound_reviewer": "board_certified_breast_imager",
    "secondary_breast_ultrasound_reviewer": "board_certified_breast_imager",
}
OPERATIONS = (
    "decode_annotation_bmp",
    "decode_image_bmp",
    "read_workbook_geometry",
)

CREDENTIAL_KEYS = (
    "schema_id", "schema_version", "credential_id", "reviewer_id", "role",
    "qualification_class", "qualification_evidence_digest", "verifier_id",
    "verification_artifact_digest", "permitted_purposes", "verified_at",
    "expires_at", "supersedes_digest", "record_digest",
)
ATTESTATION_KEYS = (
    "schema_id", "schema_version", "attestation_id",
    "credential_verification_digest", "reviewer_id", "role", "subject_digest",
    "subject_created_at", "disposition", "limitations_digest", "attested_at",
    "record_digest",
)
AUTHORIZATION_KEYS = (
    "schema_id", "schema_version", "authorization_id", "source_id",
    "source_version", "source_artifact_manifest_digest", "quarantine_source_digest",
    "metadata_inventory_digest", "review_selection_digest", "review_schema_digest",
    "duplicate_contract_digest", "repository_revision", "artifact_bindings",
    "credential_verification_digests", "fingerprint_inventories",
    "allowed_operations", "input_root", "output_root", "maximum_attempts",
    "network_access_allowed", "model_use_allowed", "training_allowed",
    "mmbu_public_access_allowed", "upload_allowed", "submission_allowed",
    "prospective_lock_digest", "authorized_at", "expires_at", "record_digest",
)
ARTIFACT_KEYS = ("logical_path", "role", "bytes", "sha256")
FINGERPRINT_KEYS = ("source_id", "source_version", "inventory_digest")
REGISTRY_KEYS = (
    "schema_id", "schema_version", "registry_id", "generation",
    "supersedes_registry_digest", "authorization_digests",
    "active_authorization_digest", "revoked_digests", "created_at", "record_digest",
)


def validate_credential_verification(record: Any, path: str = "reviewer_credential_verification") -> dict:
    f.record(record, "reviewer_credential_verification", CREDENTIAL_KEYS, path)
    f.text(record["credential_id"], f"{path}.credential_id")
    reviewer = f.text(record["reviewer_id"], f"{path}.reviewer_id")
    role = f.one_of(record["role"], f"{path}.role", ROLES)
    f.literal(record["qualification_class"], f"{path}.qualification_class", QUALIFICATIONS[role])
    f.digest(record["qualification_evidence_digest"], f"{path}.qualification_evidence_digest")
    verifier = f.text(record["verifier_id"], f"{path}.verifier_id")
    f.require(verifier != reviewer, f"{path}.verifier_id", "qualification verifier must be independent")
    f.digest(record["verification_artifact_digest"], f"{path}.verification_artifact_digest")
    f.literal(record["permitted_purposes"], f"{path}.permitted_purposes", [PURPOSE])
    verified = f.timestamp(record["verified_at"], f"{path}.verified_at")
    expires = f.timestamp(record["expires_at"], f"{path}.expires_at")
    f.require(verified < expires, f"{path}.expires_at", "must be later than verification")
    if record["supersedes_digest"] is not None:
        f.digest(record["supersedes_digest"], f"{path}.supersedes_digest")
    return record


def validate_review_attestation(record: Any, path: str = "busi_whu_review_attestation") -> dict:
    f.record(record, "busi_whu_review_attestation", ATTESTATION_KEYS, path)
    f.text(record["attestation_id"], f"{path}.attestation_id")
    f.digest(record["credential_verification_digest"], f"{path}.credential_verification_digest")
    f.text(record["reviewer_id"], f"{path}.reviewer_id")
    f.one_of(record["role"], f"{path}.role", ROLES)
    f.digest(record["subject_digest"], f"{path}.subject_digest")
    subject_time = f.timestamp(record["subject_created_at"], f"{path}.subject_created_at")
    f.one_of(record["disposition"], f"{path}.disposition", ("approved", "blocked", "rejected"))
    f.digest(record["limitations_digest"], f"{path}.limitations_digest")
    attested = f.timestamp(record["attested_at"], f"{path}.attested_at")
    f.require(attested > subject_time, f"{path}.attested_at", "must follow immutable subject creation")
    return record


def _artifact_bindings(value: Any, path: str) -> list[dict]:
    rows = f.array(value, path, nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}[{index}]"
        f.closed(row, label, ARTIFACT_KEYS)
        from mmbu_phase1 import paths
        paths.relative_path(row["logical_path"], f"{label}.logical_path")
        f.one_of(row["role"], f"{label}.role", ("archive", "metadata", "annotation", "image", "terms"))
        f.integer(row["bytes"], f"{label}.bytes", minimum=1)
        f.digest(row["sha256"], f"{label}.sha256")
    return f.sorted_unique(rows, path, lambda row: row["logical_path"].encode("utf-8"))


def _fingerprints(value: Any, path: str) -> list[dict]:
    rows = f.array(value, path, nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}[{index}]"
        f.closed(row, label, FINGERPRINT_KEYS)
        f.text(row["source_id"], f"{label}.source_id")
        f.text(row["source_version"], f"{label}.source_version")
        f.digest(row["inventory_digest"], f"{label}.inventory_digest")
    return f.sorted_unique(rows, path, lambda row: (row["source_id"] + "\0" + row["source_version"]).encode())


def validate_review_opening_authorization(
    record: Any, path: str = "busi_whu_review_opening_authorization",
) -> dict:
    f.record(record, "busi_whu_review_opening_authorization", AUTHORIZATION_KEYS, path)
    f.text(record["authorization_id"], f"{path}.authorization_id")
    f.literal(record["source_id"], f"{path}.source_id", SOURCE_ID)
    f.literal(record["source_version"], f"{path}.source_version", SOURCE_VERSION)
    for name in (
        "source_artifact_manifest_digest", "quarantine_source_digest", "metadata_inventory_digest",
        "review_selection_digest", "review_schema_digest", "duplicate_contract_digest",
        "prospective_lock_digest",
    ):
        f.digest(record[name], f"{path}.{name}")
    revision = f.text(record["repository_revision"], f"{path}.repository_revision")
    f.require(len(revision) == 40 and all(char in "0123456789abcdef" for char in revision),
              f"{path}.repository_revision", "must be a full lowercase Git SHA-1")
    _artifact_bindings(record["artifact_bindings"], f"{path}.artifact_bindings")
    credentials = f.digest_set(record["credential_verification_digests"],
                               f"{path}.credential_verification_digests", nonempty=True)
    f.require(len(credentials) == len(ROLES), f"{path}.credential_verification_digests",
              "must contain exactly one credential per required role")
    _fingerprints(record["fingerprint_inventories"], f"{path}.fingerprint_inventories")
    f.literal(record["allowed_operations"], f"{path}.allowed_operations", list(OPERATIONS))
    from pathlib import Path
    for name in ("input_root", "output_root"):
        root = f.text(record[name], f"{path}.{name}")
        f.require(Path(root).is_absolute() and ".." not in Path(root).parts, f"{path}.{name}",
                  "must be an absolute normalized root")
    f.literal(record["maximum_attempts"], f"{path}.maximum_attempts", 1)
    for name in (
        "network_access_allowed", "model_use_allowed", "training_allowed",
        "mmbu_public_access_allowed", "upload_allowed", "submission_allowed",
    ):
        f.literal(record[name], f"{path}.{name}", False)
    authorized = f.timestamp(record["authorized_at"], f"{path}.authorized_at")
    expires = f.timestamp(record["expires_at"], f"{path}.expires_at")
    f.require(authorized < expires, f"{path}.expires_at", "must be later than authorization")
    return record


def validate_review_authority_registry(record: Any, path: str = "busi_whu_review_authority_registry") -> dict:
    f.record(record, "busi_whu_review_authority_registry", REGISTRY_KEYS, path)
    f.text(record["registry_id"], f"{path}.registry_id")
    generation = f.integer(record["generation"], f"{path}.generation", minimum=0)
    if generation == 0:
        f.require(record["supersedes_registry_digest"] is None, f"{path}.supersedes_registry_digest",
                  "generation zero must have no predecessor")
    else:
        f.digest(record["supersedes_registry_digest"], f"{path}.supersedes_registry_digest")
    authorizations = f.digest_set(record["authorization_digests"], f"{path}.authorization_digests", nonempty=True)
    active = f.digest(record["active_authorization_digest"], f"{path}.active_authorization_digest")
    f.require(active in authorizations, f"{path}.active_authorization_digest", "must be registered")
    revoked = f.digest_set(record["revoked_digests"], f"{path}.revoked_digests")
    f.require(set(revoked) <= set(authorizations), f"{path}.revoked_digests", "must name registered authority")
    f.require(active not in revoked, f"{path}.active_authorization_digest", "active authority is revoked")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def _check_registry_chain(store: RecordStore, digest: str, path: str) -> dict:
    record = validate_review_authority_registry(
        store.get(digest, "busi_whu_review_authority_registry", path), path,
    )
    if record["generation"] == 0:
        return record
    prior = _check_registry_chain(store, record["supersedes_registry_digest"], f"{path}<-prior")
    f.require(record["generation"] == prior["generation"] + 1, f"{path}.generation", "must increment by one")
    f.require(record["registry_id"] == prior["registry_id"], f"{path}.registry_id", "registry identity changed")
    f.require(set(prior["authorization_digests"]) <= set(record["authorization_digests"]),
              f"{path}.authorization_digests", "predecessor authorities were removed")
    f.require(set(prior["revoked_digests"]) <= set(record["revoked_digests"]),
              f"{path}.revoked_digests", "predecessor revocations were removed")
    f.require(f.timestamp(prior["created_at"], path) <= f.timestamp(record["created_at"], path),
              f"{path}.created_at", "registry moved backward in time")
    return record


_CAPABILITY_TOKEN = object()


@dataclass(frozen=True, init=False)
class ReviewOpeningCapability:
    source_id: str
    source_version: str
    authorization_digest: str
    opening_receipt_digest: str
    authority_registry_digest: str
    opening_registry_digest: str
    prospective_lock_digest: str
    source_artifact_manifest_digest: str
    input_root: str
    output_root: str
    maximum_attempts: int
    allowed_operations: tuple[str, ...]
    artifact_bindings: tuple[tuple[str, str, int, str], ...]
    credential_verification_digests: tuple[str, ...]
    fingerprint_inventory_digests: tuple[str, ...]

    def __init__(self, token: object, **values: Any):
        if token is not _CAPABILITY_TOKEN:
            raise TypeError("ReviewOpeningCapability is constructed only by validated authority")
        for name, value in values.items():
            object.__setattr__(self, name, value)


def _latest(records: list[dict], path: str) -> dict:
    f.require(bool(records), path, "no registry exists")
    highest = max(row["generation"] for row in records)
    rows = [row for row in records if row["generation"] == highest]
    f.require(len(rows) == 1, path, "latest registry generation is ambiguous")
    return rows[0]


def validate_busi_whu_review_opening(
    store: RecordStore,
    authorization_digest: str,
    opening_receipt_digest: str,
    now: str,
) -> ReviewOpeningCapability:
    """Resolve the complete pre-opening authority chain and return a frozen capability."""
    now_ns = f.timestamp(now, "busi_whu_review_opening.now")
    authorization = validate_review_opening_authorization(
        store.get(authorization_digest, "busi_whu_review_opening_authorization", "authorization"),
        "authorization",
    )

    authority_registry = _latest(store.records("busi_whu_review_authority_registry"), "authority_registry")
    authority_registry = _check_registry_chain(store, authority_registry["record_digest"], "authority_registry")
    f.require(authority_registry["active_authorization_digest"] == authorization_digest,
              "authority_registry.active_authorization_digest", "authorization is not the active head")

    lock = locks.check_lock_succession(store, authorization["prospective_lock_digest"], "review_lock")
    opening = locks.check_opening_receipt_chain(store, opening_receipt_digest, "review_opening")
    f.require(opening["lock_digest"] == lock["record_digest"], "review_opening.lock_digest", "lock mismatch")
    f.require(set(opening["manifest_digests"]) == {
        authorization_digest, authorization["source_artifact_manifest_digest"],
    }, "review_opening.manifest_digests", "must bind exactly the authorization and source manifest")

    opening_registry = _latest(store.records("opening_receipt_registry"), "opening_registry")
    opening_registry = registries.check_opening_receipt_registry_chain(
        store, opening_registry["record_digest"], "opening_registry",
    )
    heads = [row for row in opening_registry["heads"] if row["lock_digest"] == lock["record_digest"]]
    f.require(len(heads) == 1 and heads[0]["head_receipt_digest"] == opening_receipt_digest,
              "opening_registry.heads", "opening receipt is not the active head")

    authorized_ns = f.timestamp(authorization["authorized_at"], "authorization.authorized_at")
    expires_ns = f.timestamp(authorization["expires_at"], "authorization.expires_at")
    opened_ns = f.timestamp(opening["first_access_at"], "review_opening.first_access_at")
    f.require(authorized_ns < opened_ns <= now_ns <= expires_ns, "review_opening",
              "requires authorization < opening <= now <= expiry")

    credentials = []
    for index, digest in enumerate(authorization["credential_verification_digests"]):
        credential = validate_credential_verification(
            store.get(digest, "reviewer_credential_verification", f"credentials[{index}]"),
            f"credentials[{index}]",
        )
        f.require(f.timestamp(credential["verified_at"], "credential.verified_at") < authorized_ns,
                  f"credentials[{index}].verified_at", "must precede opening authorization")
        f.require(now_ns <= f.timestamp(credential["expires_at"], "credential.expires_at"),
                  f"credentials[{index}].expires_at", "credential is expired")
        credentials.append(credential)
    f.require({row["role"] for row in credentials} == set(ROLES), "credentials", "required roles are incomplete")
    f.require(len({row["reviewer_id"] for row in credentials}) == len(credentials), "credentials",
              "review roles require distinct people")
    f.require(not ({row["reviewer_id"] for row in credentials} & {row["verifier_id"] for row in credentials}),
              "credentials", "a reviewer cannot verify any member of the review panel")

    manifest = admission.check_source_artifact_manifest(
        store, authorization["source_artifact_manifest_digest"], "source_manifest",
    )
    source = admission.validate_source(
        store.get(authorization["quarantine_source_digest"], "source", "quarantine_source"),
        "quarantine_source",
    )
    for record, label in ((manifest, "source_manifest"), (source, "quarantine_source")):
        f.require(record["source_id"] == SOURCE_ID and record["source_version"] == SOURCE_VERSION,
                  label, "canonical source identity mismatch")
    f.require(source["artifact_manifest_digest"] == manifest["record_digest"], "quarantine_source",
              "source and artifact manifest differ")
    expected_bindings = [
        {name: row[name] for name in ARTIFACT_KEYS}
        for row in manifest["artifacts"]
    ]
    f.require(f.same(authorization["artifact_bindings"], expected_bindings), "authorization.artifact_bindings",
              "must equal the frozen source artifact manifest")

    governed = {
        authorization["source_artifact_manifest_digest"], authorization["metadata_inventory_digest"],
        authorization["review_selection_digest"], authorization["review_schema_digest"],
        authorization["duplicate_contract_digest"],
        *[row["inventory_digest"] for row in authorization["fingerprint_inventories"]],
    }
    f.require(governed <= set(lock["input_artifact_digests"]), "review_lock.input_artifact_digests",
              "lock does not bind every governed review input")

    values = {
        "source_id": SOURCE_ID,
        "source_version": SOURCE_VERSION,
        "authorization_digest": authorization_digest,
        "opening_receipt_digest": opening_receipt_digest,
        "authority_registry_digest": authority_registry["record_digest"],
        "opening_registry_digest": opening_registry["record_digest"],
        "prospective_lock_digest": lock["record_digest"],
        "source_artifact_manifest_digest": manifest["record_digest"],
        "input_root": authorization["input_root"],
        "output_root": authorization["output_root"],
        "maximum_attempts": authorization["maximum_attempts"],
        "allowed_operations": tuple(authorization["allowed_operations"]),
        "artifact_bindings": tuple(
            (row["logical_path"], row["role"], row["bytes"], row["sha256"])
            for row in authorization["artifact_bindings"]
        ),
        "credential_verification_digests": tuple(authorization["credential_verification_digests"]),
        "fingerprint_inventory_digests": tuple(
            row["inventory_digest"] for row in authorization["fingerprint_inventories"]
        ),
    }
    return ReviewOpeningCapability(_CAPABILITY_TOKEN, **values)


__all__ = [
    "ReviewOpeningCapability",
    "validate_busi_whu_review_opening",
    "validate_credential_verification",
    "validate_review_attestation",
    "validate_review_opening_authorization",
]
