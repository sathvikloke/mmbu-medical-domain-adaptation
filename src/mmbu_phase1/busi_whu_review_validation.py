"""Validate BUSI-WHU human-review evidence without granting authority."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
from pathlib import Path, PurePosixPath
import re
import stat

from . import canonical
from .busi_whu_authority import (
    ROLES, validate_busi_whu_review_opening, validate_credential_verification,
    validate_review_attestation,
)
from .busi_whu_review import _REVIEW_FIELDS
from .store import RecordStore


TASKS = (
    "global_classification", "grounded_classification", "localization", "context_prediction",
)
ANSWERS = {"yes", "no", "uncertain"}
DISPOSITIONS = {"eligible", "narrow", "excluded", "unresolved"}
PURPOSE_DECISIONS = {"approve", "narrow", "decline", "unresolved"}
PURPOSES = {
    "confirmation_evaluation", "challenge_reporting", "publication",
    "source_artifact_redistribution", "trained_weight_release", "training",
}
IMMUTABLE_FIELDS = (
    "record_id", "parent_id", "label_code", "canonical_target", "workbook_row", "image_path", "annotation_path",
    "decoded_width", "decoded_height", "annotation_bbox_xywh",
)
DECISION_FIELDS = (
    "image_interpretable", "ultrasound_modality_supported", "breast_anatomy_supported",
    "annotation_usable", "label_plausible", "intended_lesion_supported",
    "grounded_target_complete", "localization_target_complete", "additional_lesion_risk",
    "shortcut_artifact", "permitted_tasks", "disposition",
)
AUTHORITY_FIELDS = (
    "source_admission_authorized", "training_ready", "model_use_authorized",
    "mmbu_public_content_used",
)
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
SOURCE_FINDINGS = {
    "image_annotation_join_issue", "lesion_completeness_issue",
    "patient_identity_issue", "target_semantics_issue",
}
SOURCE_ASSESSMENT_KEYS = {
    "schema_id", "schema_version", "assessment_id", "role", "assessor_id",
    "credential_verification_digest", "subject_digest", "subject_created_at",
    "findings", "assessed_at", "record_digest",
}
COMPLETED_REPORT_KEYS = {
    "schema_id", "schema_version", "packet_receipt_digest", "packet_manifest_digest",
    "opening_authorization_digest", "opening_receipt_digest", "review_opening_sha256",
    "primary_review_sha256", "secondary_review_sha256", "adjudication_review_sha256",
    "rights_review_sha256", "reviewed_record_count", "independently_reviewed_record_count",
    "adjudicated_record_count", "target_map", "target_map_digest",
    "global_task_manifest_digest", "eligible_by_task", "excluded_record_ids",
    "unresolved_record_ids", "duplicate_group_constraints", "duplicate_excluded_record_ids",
    "purpose_decisions", "source_blockers", "confirmation_purposes_ready",
    "review_evidence_complete", "reviewer_identity_authenticated", "review_authentication",
    "reviewer_role_ids",
    "phase1_admission_still_required", "source_admission_authorized", "training_ready",
    "model_use_authorized", "mmbu_public_content_used", "record_digest",
}


def _closed(value: object, keys: set[str], label: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{label} must be a closed object")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be nonblank trimmed text")
    return value


def _time(value: object, label: str) -> datetime:
    text = _text(value, label)
    if TIMESTAMP.fullmatch(text) is None:
        raise ValueError(f"{label} must be a UTC second timestamp")
    try:
        parsed = datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{label} must be a real UTC second timestamp") from exc
    if parsed > datetime.now(timezone.utc):
        raise ValueError(f"{label} may not be in the future")
    return parsed


def _load_canonical(path: Path, label: str) -> tuple[dict, bytes]:
    payload = Path(path).read_bytes()
    value = canonical.loads(payload)
    if type(value) is not dict or canonical.dumps(value) != payload:
        raise ValueError(f"{label} must be one canonical JSON object")
    return value, payload


def _validate_sealed(value: dict, label: str) -> dict:
    if canonical.record_digest(value) != value.get("record_digest"):
        raise ValueError(f"{label} digest mismatch")
    return value


def _source_assessment(
    store: RecordStore, assessment_digest: str, expected_role: str,
    subject_digest: str, subject_created_at: str, label: str,
) -> dict:
    value = store.get(assessment_digest, "busi_whu_source_assessment", label)
    _closed(value, SOURCE_ASSESSMENT_KEYS, label)
    _validate_sealed(value, label)
    if value["schema_id"] != "mmbu.phase1.busi_whu_source_assessment" or value["schema_version"] != 1:
        raise ValueError(f"{label} identity mismatch")
    if value["role"] != expected_role:
        raise ValueError(f"{label} role mismatch")
    for field in ("assessment_id", "assessor_id"):
        _text(value[field], f"{label}.{field}")
    if value["subject_digest"] != subject_digest or value["subject_created_at"] != subject_created_at:
        raise ValueError(f"{label} subject binding mismatch")
    created = _time(value["subject_created_at"], f"{label}.subject_created_at")
    if _time(value["assessed_at"], f"{label}.assessed_at") <= created:
        raise ValueError(f"{label} must follow immutable subject creation")
    findings = _closed(value["findings"], SOURCE_FINDINGS, f"{label}.findings")
    if any(status not in {"absent", "present", "unresolved"} for status in findings.values()):
        raise ValueError(f"{label}.findings contains an unknown status")
    credential = validate_credential_verification(
        store.get(value["credential_verification_digest"], "reviewer_credential_verification",
                  f"{label}.credential"),
        f"{label}.credential",
    )
    if (
        credential["record_digest"] != value["credential_verification_digest"]
        or credential["role"] != expected_role
        or credential["reviewer_id"] != value["assessor_id"]
    ):
        raise ValueError(f"{label} credential binding mismatch")
    return value


def validate_source_assessments(
    store: RecordStore, clinical_assessment_digest: str, custodian_assessment_digest: str,
    *, subject_digest: str, subject_created_at: str,
) -> dict:
    """Resolve two independent source assessments and return fail-closed blockers."""
    if not isinstance(store, RecordStore):
        raise ValueError("source assessment store must be a Phase 1 record store")
    if not re.fullmatch(r"[0-9a-f]{64}", subject_digest):
        raise ValueError("source assessment subject digest is invalid")
    _time(subject_created_at, "source assessment subject_created_at")
    clinical = _source_assessment(
        store, clinical_assessment_digest, "clinical_adjudicator", subject_digest,
        subject_created_at, "clinical source assessment",
    )
    custodian = _source_assessment(
        store, custodian_assessment_digest, "data_rights_authority", subject_digest,
        subject_created_at, "custodian source assessment",
    )
    if clinical["assessor_id"] == custodian["assessor_id"]:
        raise ValueError("source assessments require distinct people")
    blockers = []
    for finding in sorted(SOURCE_FINDINGS):
        left = clinical["findings"][finding]
        right = custodian["findings"][finding]
        if left != right:
            blockers.append(f"source_assessor_disagreement:{finding}")
        elif left != "absent":
            blockers.append(f"source_finding:{finding}:{left}")
    return {
        "authenticated": True,
        "blockers": blockers,
        "clinical_assessment_digest": clinical["record_digest"],
        "custodian_assessment_digest": custodian["record_digest"],
    }


def authenticate_completed_review(
    report: object, store: RecordStore, authorization_digest: str, opening_receipt_digest: str,
    review_attestation_digests: list[str], clinical_assessment_digest: str,
    custodian_assessment_digest: str, *, report_created_at: str, now: str,
) -> dict:
    """Promote a validated report only through the full pre/post human authority chain."""
    report = _closed(report, COMPLETED_REPORT_KEYS, "completed review report")
    if canonical.record_digest(report) != report.get("record_digest"):
        raise ValueError("completed review report must be one sealed record")
    if report["schema_id"] != "mmbu.phase1.busi_whu_review_validation" or report["schema_version"] != 1:
        raise ValueError("completed review report identity mismatch")
    if report.get("reviewer_identity_authenticated") is not False or report.get("review_authentication") is not None:
        raise ValueError("completed review report is not an unauthenticated base report")
    if (
        report.get("opening_authorization_digest") != authorization_digest
        or report.get("opening_receipt_digest") != opening_receipt_digest
    ):
        raise ValueError("completed review opening authority binding mismatch")
    _time(report_created_at, "completed review report_created_at")
    _time(now, "completed review authenticated_at")
    capability = validate_busi_whu_review_opening(
        store, authorization_digest, opening_receipt_digest, now
    )
    if type(review_attestation_digests) is not list or len(review_attestation_digests) != len(ROLES):
        raise ValueError("completed review requires exactly one attestation per authority role")
    if len(review_attestation_digests) != len(set(review_attestation_digests)):
        raise ValueError("completed review contains a repeated attestation digest")
    credentials = {}
    for credential_digest in capability.credential_verification_digests:
        credential = validate_credential_verification(
            store.get(credential_digest, "reviewer_credential_verification", "review credential"),
            "review credential",
        )
        credentials[credential["role"]] = credential
    credential_reviewer_ids = {
        role: credential["reviewer_id"] for role, credential in sorted(credentials.items())
    }
    if report.get("reviewer_role_ids") != credential_reviewer_ids:
        raise ValueError("completed review participant identities differ from verified credentials")
    attestations = {}
    for index, attestation_digest in enumerate(review_attestation_digests):
        attestation = validate_review_attestation(
            store.get(attestation_digest, "busi_whu_review_attestation",
                      f"review attestations[{index}]"),
            f"review attestations[{index}]",
        )
        role = attestation["role"]
        if role in attestations or role not in credentials:
            raise ValueError("completed review attestation role is unknown or repeated")
        credential = credentials[role]
        if (
            attestation["credential_verification_digest"] != credential["record_digest"]
            or attestation["reviewer_id"] != credential["reviewer_id"]
            or attestation["subject_digest"] != report["record_digest"]
            or attestation["subject_created_at"] != report_created_at
            or attestation["disposition"] != "approved"
        ):
            raise ValueError("completed review attestation binding or disposition mismatch")
        attestations[role] = attestation
    if set(attestations) != set(ROLES):
        raise ValueError("completed review attestation roles are incomplete")
    source_assessments = validate_source_assessments(
        store, clinical_assessment_digest, custodian_assessment_digest,
        subject_digest=report["record_digest"], subject_created_at=report_created_at,
    )
    blockers = sorted(set(report["source_blockers"]) | set(source_assessments["blockers"]))
    result = dict(report)
    result.pop("record_digest")
    result["source_blockers"] = blockers
    result["confirmation_purposes_ready"] = report["confirmation_purposes_ready"] and not blockers
    result["reviewer_identity_authenticated"] = True
    result["review_authentication"] = {
        "base_review_report_digest": report["record_digest"],
        "opening_authorization_digest": authorization_digest,
        "opening_receipt_digest": opening_receipt_digest,
        "review_attestation_digests": sorted(review_attestation_digests),
        "clinical_assessment_digest": source_assessments["clinical_assessment_digest"],
        "custodian_assessment_digest": source_assessments["custodian_assessment_digest"],
        "authenticated_at": now,
    }
    return canonical.seal(result)


def validate_authenticated_completed_review(report: object, store: RecordStore) -> dict:
    """Re-resolve and reproduce an authenticated report from its sealed evidence chain."""
    report = _closed(report, COMPLETED_REPORT_KEYS, "authenticated completed review report")
    if canonical.record_digest(report) != report.get("record_digest"):
        raise ValueError("authenticated completed review report must be one sealed record")
    if report.get("reviewer_identity_authenticated") is not True:
        raise ValueError("completed review report is not authenticated")
    authentication = report.get("review_authentication")
    if type(authentication) is not dict:
        raise ValueError("completed review authentication is missing")
    base = store.get(
        authentication.get("base_review_report_digest"), "busi_whu_review_validation",
        "completed review base report",
    )
    attestation_digests = authentication.get("review_attestation_digests")
    if type(attestation_digests) is not list or not attestation_digests:
        raise ValueError("completed review attestations are missing")
    subject_times = set()
    for index, attestation_digest in enumerate(attestation_digests):
        attestation = validate_review_attestation(
            store.get(attestation_digest, "busi_whu_review_attestation",
                      f"completed review attestations[{index}]"),
            f"completed review attestations[{index}]",
        )
        subject_times.add(attestation["subject_created_at"])
    if len(subject_times) != 1:
        raise ValueError("completed review attestations disagree on subject chronology")
    reproduced = authenticate_completed_review(
        base, store,
        authentication.get("opening_authorization_digest"),
        authentication.get("opening_receipt_digest"),
        attestation_digests,
        authentication.get("clinical_assessment_digest"),
        authentication.get("custodian_assessment_digest"),
        report_created_at=subject_times.pop(),
        now=authentication.get("authenticated_at"),
    )
    if reproduced != report:
        raise ValueError("authenticated completed review differs from its resolved evidence chain")
    return report


def _negative_authority(value: dict, label: str) -> None:
    for field in AUTHORITY_FIELDS:
        if value.get(field) is not False:
            raise ValueError(f"{label}.{field} must remain false")


def _validate_packet(packet: Path, expected_digest: str) -> tuple[dict, dict, dict, dict, dict, dict]:
    packet = Path(packet).resolve(strict=True)
    if not packet.is_dir():
        raise ValueError("packet must be a directory")
    receipt, receipt_payload = _load_canonical(packet / "packet-receipt.json", "packet receipt")
    _validate_sealed(receipt, "packet receipt")
    if receipt["record_digest"] != expected_digest:
        raise ValueError("packet differs from the expected frozen receipt")
    _negative_authority(receipt, "packet receipt")
    seen = set()
    for member in receipt.get("members", []):
        member = _closed(member, {"path", "bytes", "sha256"}, "packet member")
        name = member["path"]
        pure = PurePosixPath(name) if isinstance(name, str) else None
        if (
            pure is None or pure.is_absolute() or pure.as_posix() != name or ".." in pure.parts
            or name in seen or type(member["bytes"]) is not int or member["bytes"] < 0
            or not isinstance(member["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", member["sha256"]) is None
        ):
            raise ValueError("packet receipt contains an invalid member")
        seen.add(name)
        target = packet / name
        info = target.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("packet member must be a regular unaliased file")
        payload = target.read_bytes()
        if len(payload) != member["bytes"] or hashlib.sha256(payload).hexdigest() != member["sha256"]:
            raise ValueError("packet member digest mismatch")
    actual = {
        path.relative_to(packet).as_posix() for path in packet.rglob("*")
        if path.is_file() and path.name != "packet-receipt.json"
    }
    if seen != actual:
        raise ValueError("packet filesystem differs from its receipt")
    manifest, _ = _load_canonical(packet / "review-manifest.json", "review manifest")
    decode, _ = _load_canonical(packet / "decode-inventory.json", "decode inventory")
    duplicates, _ = _load_canonical(packet / "duplicate-candidates.json", "duplicate inventory")
    targets, _ = _load_canonical(packet / "target-manifest.json", "target manifest")
    global_task, _ = _load_canonical(
        packet / "task-manifest-global_classification.json", "global task manifest"
    )
    for name, value in (
        ("manifest", manifest), ("decode inventory", decode), ("duplicates", duplicates),
        ("target manifest", targets), ("global task manifest", global_task),
    ):
        _validate_sealed(value, name)
        _negative_authority(value, name)
    if (
        receipt["manifest_digest"] != manifest["record_digest"]
        or receipt["decode_inventory_digest"] != decode["record_digest"]
        or receipt["duplicate_candidates_digest"] != duplicates["record_digest"]
        or manifest["decode_inventory_digest"] != decode["record_digest"]
        or manifest["duplicate_candidates_digest"] != duplicates["record_digest"]
        or receipt["target_map_digest"] != targets["record_digest"]
        or manifest["target_map_digest"] != targets["record_digest"]
        or decode["target_map_digest"] != targets["record_digest"]
        or manifest["mechanical_task_manifest_digests"]["global_classification"]
        != global_task["record_digest"]
        or global_task["target_map_digest"] != targets["record_digest"]
        or global_task["decode_inventory_digest"] != decode["record_digest"]
    ):
        raise ValueError("packet transitive digest chain mismatch")
    if decode.get("record_count") != 927 or len(decode.get("records", [])) != 927:
        raise ValueError("decode inventory must contain exactly 927 records")
    record_targets = targets.get("record_targets")
    decoded_targets = {row["record_id"]: row["canonical_target"] for row in decode["records"]}
    if (
        type(record_targets) is not dict
        or targets.get("record_count") != len(record_targets)
        or record_targets != decoded_targets
        or global_task.get("mechanically_candidate_record_ids") != sorted(record_targets)
        or global_task.get("mechanically_blocked_record_ids") != []
    ):
        raise ValueError("packet target or global-task population mismatch")
    return receipt, manifest, decode, duplicates, targets, global_task


def _read_rows(path: Path, label: str) -> tuple[list[dict[str, str]], bytes]:
    payload = Path(path).read_bytes()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} must be UTF-8") from exc
    reader = csv.DictReader(text.splitlines(keepends=True))
    if reader.fieldnames != list(_REVIEW_FIELDS):
        raise ValueError(f"{label} columns differ from the frozen template")
    rows = list(reader)
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError(f"{label} contains malformed cells")
    return rows, payload


def _template_rows(packet: Path, name: str) -> list[dict[str, str]]:
    rows, _ = _read_rows(packet / name, name)
    return rows


def _profile_map(opening: dict) -> tuple[dict[str, dict], datetime]:
    keys = {
        "schema_id", "schema_version", "packet_receipt_digest", "opened_at", "opened_by",
        "authorization_evidence_locator", "review_opening_authorized", "reviewers", *AUTHORITY_FIELDS,
    }
    _closed(opening, keys, "review opening")
    if opening["schema_id"] != "mmbu.phase1.busi_whu_review_opening" or opening["schema_version"] != 1:
        raise ValueError("review opening identity mismatch")
    if opening["review_opening_authorized"] is not True:
        raise ValueError("review opening is not authorized")
    _negative_authority(opening, "review opening")
    _text(opening["opened_by"], "review opening.opened_by")
    _text(opening["authorization_evidence_locator"], "review opening.authorization_evidence_locator")
    opened_at = _time(opening["opened_at"], "review opening.opened_at")
    profiles = {}
    profile_keys = {
        "role", "reviewer_id", "qualification", "qualification_evidence_locator",
        "conflict_status", "human_attested",
    }
    allowed = {
        "primary": {"breast_ultrasound_clinician", "breast_imaging_clinician",
                    "breast_imaging_researcher_with_clinical_review_qualification"},
        "secondary": {"breast_ultrasound_clinician", "breast_imaging_clinician",
                      "breast_imaging_researcher_with_clinical_review_qualification"},
        "adjudicator": {"breast_ultrasound_clinician", "breast_imaging_clinician"},
    }
    if not isinstance(opening["reviewers"], list) or len(opening["reviewers"]) != 3:
        raise ValueError("review opening must assign three qualified reviewer roles")
    for raw in opening["reviewers"]:
        profile = _closed(raw, profile_keys, "reviewer profile")
        role = profile["role"]
        if role not in allowed or role in profiles:
            raise ValueError("reviewer profile role is invalid or duplicated")
        if profile["qualification"] not in allowed[role]:
            raise ValueError(f"{role} reviewer qualification is not allowed")
        _text(profile["reviewer_id"], f"{role}.reviewer_id")
        _text(profile["qualification_evidence_locator"], f"{role}.qualification_evidence_locator")
        if profile["conflict_status"] not in {"none_declared", "declared_managed"}:
            raise ValueError(f"{role} conflict disclosure is unresolved")
        if profile["human_attested"] is not True:
            raise ValueError(f"{role} reviewer must be human-attested")
        profiles[role] = profile
    identities = [value["reviewer_id"] for value in profiles.values()]
    if len(identities) != len(set(identities)):
        raise ValueError("primary, secondary, and adjudicator identities must be distinct")
    return profiles, opened_at


def _tasks(value: str, label: str) -> list[str]:
    if value == "":
        return []
    result = value.split("|")
    if len(result) != len(set(result)) or any(task not in TASKS for task in result):
        raise ValueError(f"{label} contains unknown or duplicate tasks")
    return result


def _decision(row: dict[str, str], label: str) -> dict:
    for field in (
        "image_interpretable", "ultrasound_modality_supported", "breast_anatomy_supported",
        "annotation_usable", "label_plausible", "intended_lesion_supported",
        "grounded_target_complete", "localization_target_complete",
    ):
        if row[field] not in ANSWERS:
            raise ValueError(f"{label}.{field} has an unknown answer")
    if row["shortcut_artifact"] not in {"no", "present", "uncertain"}:
        raise ValueError(f"{label}.shortcut_artifact has an unknown answer")
    if row["additional_lesion_risk"] not in {"no", "present", "uncertain"}:
        raise ValueError(f"{label}.additional_lesion_risk has an unknown answer")
    if row["disposition"] not in DISPOSITIONS:
        raise ValueError(f"{label}.disposition is unknown")
    tasks = _tasks(row["permitted_tasks"], f"{label}.permitted_tasks")
    disposition = row["disposition"]
    if disposition in {"eligible", "narrow"} and not tasks:
        raise ValueError(f"{label} eligible or narrowed review must name tasks")
    if disposition in {"excluded", "unresolved"} and tasks:
        raise ValueError(f"{label} excluded or unresolved review cannot name tasks")
    if disposition == "eligible" and set(tasks) != set(TASKS):
        raise ValueError(f"{label} eligible review must permit the full task set")
    if disposition == "narrow" and set(tasks) == set(TASKS):
        raise ValueError(f"{label} narrow review must remove at least one task")
    for task in tasks:
        for field in ("image_interpretable", "ultrasound_modality_supported", "breast_anatomy_supported"):
            if row[field] != "yes":
                raise ValueError(f"{label}.{task} requires {field}=yes")
        if task in {"global_classification", "grounded_classification"} and row["label_plausible"] != "yes":
            raise ValueError(f"{label}.{task} requires label_plausible=yes")
        if task in {"global_classification", "grounded_classification", "localization"} and row["intended_lesion_supported"] != "yes":
            raise ValueError(f"{label}.{task} requires intended_lesion_supported=yes")
        if task in {"grounded_classification", "localization"} and row["annotation_usable"] != "yes":
            raise ValueError(f"{label}.{task} requires annotation_usable=yes")
        if task == "grounded_classification" and row["grounded_target_complete"] != "yes":
            raise ValueError(f"{label}.{task} requires grounded_target_complete=yes")
        if task == "localization" and row["localization_target_complete"] != "yes":
            raise ValueError(f"{label}.{task} requires localization_target_complete=yes")
        if task in {"grounded_classification", "localization"} and row["additional_lesion_risk"] != "no":
            raise ValueError(f"{label}.{task} requires additional_lesion_risk=no")
        if row["shortcut_artifact"] != "no":
            raise ValueError(f"{label}.{task} requires shortcut_artifact=no")
    _text(row["notes"], f"{label}.notes")
    return {field: row[field] for field in DECISION_FIELDS}


def _validate_rows(
    rows: list[dict[str, str]], template: list[dict[str, str]], reviewer_id: str,
    opened_at: datetime, label: str, *, allowed_extra: dict[str, dict[str, str]] | None = None,
) -> dict[str, dict]:
    frozen = {row["record_id"]: row for row in template}
    if allowed_extra:
        frozen.update(allowed_extra)
    expected_ids = list(frozen)
    if [row["record_id"] for row in rows] != expected_ids:
        raise ValueError(f"{label} review must contain the exact assigned population in order")
    result = {}
    for index, row in enumerate(rows, 2):
        expected = frozen[row["record_id"]]
        if any(row[field] != expected[field] for field in IMMUTABLE_FIELDS):
            raise ValueError(f"{label} row {index} differs from frozen packet metadata")
        if row["reviewer_id"] != reviewer_id:
            raise ValueError(f"{label} row {index} reviewer identity mismatch")
        if _time(row["reviewed_at"], f"{label} row {index}.reviewed_at") <= opened_at:
            raise ValueError(f"{label} review must occur after the authorized opening")
        result[row["record_id"]] = _decision(row, f"{label} row {index}")
    return result


def _validate_rights(value: dict, receipt_digest: str, opened_at: datetime) -> tuple[dict, list[str]]:
    keys = {
        "schema_id", "schema_version", "packet_receipt_digest", "reviewer_id", "reviewed_at",
        "qualification", "qualification_evidence_locator", "conflict_status", "human_attested",
        "license_identity", "attribution_text", "decisions", *AUTHORITY_FIELDS,
    }
    _closed(value, keys, "rights review")
    if value["schema_id"] != "mmbu.phase1.busi_whu_rights_purpose_review" or value["schema_version"] != 1:
        raise ValueError("rights review identity mismatch")
    if value["packet_receipt_digest"] != receipt_digest:
        raise ValueError("rights review packet digest mismatch")
    _negative_authority(value, "rights review")
    for field in ("reviewer_id", "qualification_evidence_locator", "license_identity", "attribution_text"):
        _text(value[field], f"rights review.{field}")
    if value["qualification"] != "team_rights_authority" or value["human_attested"] is not True:
        raise ValueError("rights review requires an attested team rights authority")
    if value["conflict_status"] not in {"none_declared", "declared_managed"}:
        raise ValueError("rights reviewer conflict is unresolved")
    if _time(value["reviewed_at"], "rights review.reviewed_at") <= opened_at:
        raise ValueError("rights review must occur after the authorized opening")
    decisions = _closed(value["decisions"], PURPOSES, "rights review.decisions")
    if any(decision not in PURPOSE_DECISIONS for decision in decisions.values()):
        raise ValueError("rights review contains an unknown purpose decision")
    if decisions["training"] != "decline":
        raise ValueError("BUSI-WHU training purpose must remain decline")
    blockers = [
        f"{purpose}_{decisions[purpose]}" for purpose in ("confirmation_evaluation", "challenge_reporting")
        if decisions[purpose] != "approve"
    ]
    return decisions, blockers


def validate_completed_review(
    packet: Path,
    primary_review: Path,
    secondary_review: Path,
    adjudication_review: Path,
    rights_review: Path,
    review_opening: Path,
    *,
    expected_packet_receipt_digest: str,
) -> dict:
    """Validate complete evidence and emit task manifests, never admission authority."""
    packet = Path(packet).resolve(strict=True)
    receipt, manifest, decode, duplicates, targets, global_task = _validate_packet(
        packet, expected_packet_receipt_digest
    )
    opening, opening_payload = _load_canonical(review_opening, "review opening")
    if opening.get("packet_receipt_digest") != receipt["record_digest"]:
        raise ValueError("review opening packet digest mismatch")
    profiles, opened_at = _profile_map(opening)
    primary_rows, primary_payload = _read_rows(primary_review, "primary")
    secondary_rows, secondary_payload = _read_rows(secondary_review, "secondary")
    primary_template = _template_rows(packet, "primary-review.csv")
    secondary_template = _template_rows(packet, "secondary-review.csv")
    primary = _validate_rows(
        primary_rows, primary_template, profiles["primary"]["reviewer_id"], opened_at, "primary"
    )
    primary_by_id = {row["record_id"]: row for row in primary_rows}
    frozen_secondary_ids = [row["record_id"] for row in secondary_template]
    flagged = [
        record_id for record_id, decision in primary.items()
        if record_id not in set(frozen_secondary_ids) and (
            decision["disposition"] != "eligible"
            or any(decision[field] != "yes" for field in (
                "image_interpretable", "ultrasound_modality_supported", "breast_anatomy_supported",
                "annotation_usable", "label_plausible", "intended_lesion_supported",
                "grounded_target_complete", "localization_target_complete",
            ))
            or decision["shortcut_artifact"] != "no"
            or decision["additional_lesion_risk"] != "no"
        )
    ]
    extra = {record_id: primary_by_id[record_id] for record_id in flagged}
    expected_secondary = secondary_template + [extra[record_id] for record_id in sorted(extra)]
    secondary = _validate_rows(
        secondary_rows, expected_secondary, profiles["secondary"]["reviewer_id"], opened_at,
        "secondary",
    )

    adjudication, adjudication_payload = _load_canonical(adjudication_review, "adjudication")
    adj_keys = {
        "schema_id", "schema_version", "packet_receipt_digest", "adjudications",
        "duplicate_dispositions", *AUTHORITY_FIELDS,
    }
    _closed(adjudication, adj_keys, "adjudication")
    if (
        adjudication["schema_id"] != "mmbu.phase1.busi_whu_completed_adjudication"
        or adjudication["schema_version"] != 1
        or adjudication["packet_receipt_digest"] != receipt["record_digest"]
    ):
        raise ValueError("adjudication identity or packet binding mismatch")
    _negative_authority(adjudication, "adjudication")
    disagreements = {
        record_id for record_id in secondary if secondary[record_id] != primary[record_id]
    }
    entries = adjudication["adjudications"]
    if not isinstance(entries, list):
        raise ValueError("adjudication entries must be a list")
    entry_ids = [row.get("record_id") for row in entries if isinstance(row, dict)]
    if len(entry_ids) != len(entries) or len(entry_ids) != len(set(entry_ids)):
        raise ValueError("adjudication contains a repeated record ID")
    if set(entry_ids) != disagreements:
        raise ValueError("adjudication must exactly cover every independent-review disagreement")
    adjudicated = {}
    entry_keys = {
        "record_id", "adjudicator_id", "adjudicated_at", *DECISION_FIELDS, "notes",
    }
    primary_times = {row["record_id"]: _time(row["reviewed_at"], "primary reviewed_at") for row in primary_rows}
    secondary_times = {row["record_id"]: _time(row["reviewed_at"], "secondary reviewed_at") for row in secondary_rows}
    latest_independent_review_at = max([*primary_times.values(), *secondary_times.values()])
    for entry in entries:
        _closed(entry, entry_keys, "adjudication entry")
        record_id = entry["record_id"]
        if entry["adjudicator_id"] != profiles["adjudicator"]["reviewer_id"]:
            raise ValueError("adjudication requires the distinct assigned adjudicator")
        when = _time(entry["adjudicated_at"], "adjudication.adjudicated_at")
        if when <= max(primary_times[record_id], secondary_times[record_id]) or when <= opened_at:
            raise ValueError("adjudication must occur after both independent reviews")
        adjudicated[record_id] = _decision(entry, f"adjudication {record_id}")

    expected_duplicate_groups = {}
    for group_type, digest_field, group_rows in (
        ("exact", "decoded_image_sha256", duplicates["exact_image_groups"]),
        ("perceptual", "perceptual_hash", duplicates["perceptual_image_groups"]),
    ):
        for group in group_rows:
            key = (group_type, group[digest_field])
            if key in expected_duplicate_groups:
                raise ValueError("packet contains a repeated duplicate group")
            expected_duplicate_groups[key] = group
    duplicate_rows = adjudication["duplicate_dispositions"]
    if not isinstance(duplicate_rows, list):
        raise ValueError("duplicate dispositions must be a list")
    duplicate_keys = {
        "group_type", "digest", "record_ids", "primary_reviewer_id", "primary_decision",
        "secondary_reviewer_id", "secondary_decision", "adjudicator_id", "adjudicated_at",
        "final_decision", "rationale",
    }
    observed_duplicate_keys = set()
    duplicate_constraints = []
    duplicate_excluded = set()
    duplicate_blockers = []
    duplicate_decisions = {"distinct", "coassign", "exclude", "unresolved"}
    for index, raw in enumerate(duplicate_rows):
        row = _closed(raw, duplicate_keys, f"duplicate disposition {index}")
        key = (row["group_type"], row["digest"])
        if key in observed_duplicate_keys or key not in expected_duplicate_groups:
            raise ValueError("duplicate disposition identifies an unknown or repeated group")
        observed_duplicate_keys.add(key)
        expected_group = expected_duplicate_groups[key]
        if row["record_ids"] != expected_group["record_ids"]:
            raise ValueError("duplicate disposition record population differs from the packet")
        if (
            row["primary_reviewer_id"] != profiles["primary"]["reviewer_id"]
            or row["secondary_reviewer_id"] != profiles["secondary"]["reviewer_id"]
        ):
            raise ValueError("duplicate disposition requires both assigned independent reviewers")
        if row["primary_decision"] not in duplicate_decisions or row["secondary_decision"] not in duplicate_decisions:
            raise ValueError("duplicate disposition contains an unknown decision")
        final_decision = row["final_decision"]
        if row["primary_decision"] == row["secondary_decision"]:
            if row["adjudicator_id"] or row["adjudicated_at"]:
                raise ValueError("duplicate agreement cannot claim adjudication")
            if final_decision != row["primary_decision"]:
                raise ValueError("duplicate final decision differs from independent agreement")
        else:
            if row["adjudicator_id"] != profiles["adjudicator"]["reviewer_id"]:
                raise ValueError("duplicate disagreement requires the distinct assigned adjudicator")
            if _time(row["adjudicated_at"], "duplicate adjudicated_at") <= latest_independent_review_at:
                raise ValueError("duplicate adjudication must occur after both independent reviews")
            if final_decision not in duplicate_decisions:
                raise ValueError("duplicate adjudication final decision is unknown")
        _text(row["rationale"], "duplicate disposition.rationale")
        if final_decision == "coassign":
            duplicate_constraints.append({
                "group_type": row["group_type"], "digest": row["digest"],
                "record_ids": row["record_ids"], "patient_ids": expected_group["patient_ids"],
            })
        elif final_decision == "exclude":
            duplicate_excluded.update(row["record_ids"])
        elif final_decision == "unresolved" and expected_group["cross_patient"]:
            duplicate_blockers.append(f"unresolved_cross_patient_{row['group_type']}_duplicate")
    if observed_duplicate_keys != set(expected_duplicate_groups):
        raise ValueError("duplicate dispositions must exactly cover every packet candidate group")

    rights, rights_payload = _load_canonical(rights_review, "rights review")
    decisions, blockers = _validate_rights(rights, receipt["record_digest"], opened_at)
    blockers.extend(duplicate_blockers)
    if duplicates["cross_source_candidates"]:
        blockers.append("unresolved_cross_source_duplicate_candidates")
    final = dict(primary)
    final.update(secondary)
    final.update(adjudicated)
    records = {row["record_id"]: row for row in decode["records"]}
    eligible_by_task = {}
    for task in TASKS:
        record_ids = sorted(record_id for record_id, decision in final.items() if record_id not in duplicate_excluded and task in _tasks(
            decision["permitted_tasks"], f"final {record_id}.permitted_tasks"
        ))
        patient_ids = sorted({records[record_id]["parent_id"] for record_id in record_ids})
        patient_to_records = {
            patient_id: sorted(
                record_id for record_id in record_ids if records[record_id]["parent_id"] == patient_id
            )
            for patient_id in patient_ids
        }
        eligible_by_task[task] = {
            "record_ids": record_ids, "record_count": len(record_ids),
            "patient_ids": patient_ids, "patient_count": len(patient_ids),
            "patient_to_records": patient_to_records,
        }
    unresolved = sorted(record_id for record_id, decision in final.items() if decision["disposition"] == "unresolved")
    excluded = sorted({
        record_id for record_id, decision in final.items()
        if decision["disposition"] in {"excluded", "unresolved"}
    } | duplicate_excluded)
    if eligible_by_task["global_classification"]["patient_count"] < 60:
        blockers.append("fewer_than_60_global_classification_patients")
    report = canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_review_validation",
        "schema_version": 1,
        "packet_receipt_digest": receipt["record_digest"],
        "packet_manifest_digest": manifest["record_digest"],
        "opening_authorization_digest": receipt["opening_authorization_digest"],
        "opening_receipt_digest": receipt["opening_receipt_digest"],
        "review_opening_sha256": hashlib.sha256(opening_payload).hexdigest(),
        "primary_review_sha256": hashlib.sha256(primary_payload).hexdigest(),
        "secondary_review_sha256": hashlib.sha256(secondary_payload).hexdigest(),
        "adjudication_review_sha256": hashlib.sha256(adjudication_payload).hexdigest(),
        "rights_review_sha256": hashlib.sha256(rights_payload).hexdigest(),
        "reviewed_record_count": len(primary),
        "independently_reviewed_record_count": len(secondary),
        "adjudicated_record_count": len(adjudicated),
        "target_map": targets["record_targets"],
        "target_map_digest": canonical.value_digest(targets["record_targets"]),
        "global_task_manifest_digest": global_task["record_digest"],
        "eligible_by_task": eligible_by_task,
        "excluded_record_ids": excluded,
        "unresolved_record_ids": unresolved,
        "duplicate_group_constraints": duplicate_constraints,
        "duplicate_excluded_record_ids": sorted(duplicate_excluded),
        "purpose_decisions": decisions,
        "source_blockers": sorted(blockers),
        "confirmation_purposes_ready": not blockers,
        "review_evidence_complete": True,
        "reviewer_role_ids": {
            "clinical_adjudicator": profiles["adjudicator"]["reviewer_id"],
            "data_rights_authority": rights["reviewer_id"],
            "primary_breast_ultrasound_reviewer": profiles["primary"]["reviewer_id"],
            "secondary_breast_ultrasound_reviewer": profiles["secondary"]["reviewer_id"],
        },
        "reviewer_identity_authenticated": False,
        "review_authentication": None,
        "phase1_admission_still_required": True,
        "source_admission_authorized": False,
        "training_ready": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })
    return report


__all__ = [
    "authenticate_completed_review", "validate_authenticated_completed_review",
    "validate_completed_review", "validate_source_assessments",
]
