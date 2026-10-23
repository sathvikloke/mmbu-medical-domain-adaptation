"""Validate completed BUS-BRA human-review evidence without granting authority."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

from .busbra_review import _canonical_digest, _load_json


REVIEW_FIELDS = (
    "record_id", "case_id", "pathology", "birads", "width", "height",
    "decoded_width", "decoded_height",
    "source_bbox_xywh", "mask_derived_bbox_xywh", "image_member", "mask_member",
    "image_path", "mask_path", "mandatory_reasons",
    "primary_reviewer_id", "primary_reviewed_at", "image_interpretable",
    "mask_usable", "additional_or_incomplete_lesion", "source_fields_joined",
    "shortcut_artifact", "permitted_tasks", "primary_disposition", "primary_notes",
    "secondary_reviewer_id", "secondary_reviewed_at", "secondary_disposition",
    "secondary_notes", "adjudicator_id", "adjudicated_at", "final_disposition",
)
TASKS = (
    "pathology classification",
    "BI-RADS classification",
    "mask-grounded classification",
    "mask-derived object detection",
)
ANSWERS = {"yes", "no", "uncertain"}
SHORTCUTS = {"none", "present", "uncertain"}
DISPOSITIONS = {"eligible", "correction_required", "excluded", "unresolved"}
RIGHTS_DECISIONS = {"approve", "narrow", "decline", "unresolved"}
PROVENANCE_DECISIONS = {"distinct_lineage", "linked_lineage", "exclude_or_coassign", "unresolved"}
TIMESTAMP = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
PROFILE_KEYS = {
    "role", "reviewer_id", "qualification", "qualification_evidence_locator", "reviewed_at",
    "evidence_locator", "human_attested",
}
ROLE_QUALIFICATIONS = {
    "medical_primary": {
        "breast_imaging_clinician", "breast_ultrasound_clinician",
        "breast_imaging_researcher_with_clinical_review_qualification",
    },
    "medical_secondary": {
        "breast_imaging_clinician", "breast_ultrasound_clinician",
        "breast_imaging_researcher_with_clinical_review_qualification",
    },
    "adjudicator": {"breast_imaging_clinician", "breast_ultrasound_clinician"},
    "provenance": {"source_data_steward", "source_author"},
    "rights_release": {"team_rights_authority"},
}
SOURCE_KEYS = {
    "schema", "source_id", "source_version", "decision_status", "medical_review",
    "provenance_review", "rights_and_release_review", "review_complete", "training_ready",
    "model_use_authorized",
}
MEDICAL_KEYS = {"primary_reviewer", "secondary_reviewer", "adjudicator"}
PROVENANCE_KEYS = {"reviewer", "case_110_536_disposition", "evidence_locator"}
RIGHTS_KEYS = {
    "reviewer", "training", "development", "untouched_confirmation", "public_weight_release",
    "challenge_submission", "attribution_text", "redistribution_conditions",
}
RECEIPT_KEYS = {
    "schema", "source_id", "source_version", "manifest_digest", "record_count", "members",
    "review_complete", "training_ready", "model_use_authorized", "limitations", "receipt_digest",
}
MANIFEST_KEYS = {
    "schema", "source_id", "source_version", "archive_bytes", "archive_md5", "metadata_sha256",
    "stratified_plan_digest", "human_review_plan_digest", "structural_contract_digest", "record_count",
    "records", "review_status", "review_complete", "training_ready", "model_use_authorized",
    "manifest_digest",
}


def _text(value, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{label} must be nonblank trimmed text")
    return value


def _timestamp(value, label: str) -> datetime:
    value = _text(value, label)
    if TIMESTAMP.fullmatch(value) is None:
        raise ValueError(f"{label} must be a real UTC second timestamp")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{label} must be a real UTC second timestamp") from exc
    return parsed


def _closed(value, keys: set[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must be a closed object")
    return value


def _profile(value, label: str, role: str, *, optional: bool = False) -> dict | None:
    if value is None and optional:
        return None
    value = _closed(value, PROFILE_KEYS, label)
    if value["role"] != role:
        raise ValueError(f"{label}.role must be {role}")
    _text(value["reviewer_id"], f"{label}.reviewer_id")
    if value["qualification"] not in ROLE_QUALIFICATIONS[role]:
        raise ValueError(f"{label}.qualification is not allowed for {role}")
    _text(value["qualification_evidence_locator"], f"{label}.qualification_evidence_locator")
    _timestamp(value["reviewed_at"], f"{label}.reviewed_at")
    _text(value["evidence_locator"], f"{label}.evidence_locator")
    if value["human_attested"] is not True:
        raise ValueError(f"{label} requires an explicit human attestation")
    return value


def _validate_packet(packet: Path, expected_receipt_digest: str) -> tuple[dict, dict]:
    packet = packet.resolve(strict=True)
    if not packet.is_dir():
        raise ValueError("packet must be a directory")
    receipt = _closed(_load_json(packet / "packet-receipt.json"), RECEIPT_KEYS, "packet receipt")
    unsigned_receipt = dict(receipt)
    claimed_receipt_digest = unsigned_receipt.pop("receipt_digest")
    if claimed_receipt_digest != _canonical_digest(unsigned_receipt):
        raise ValueError("packet receipt digest mismatch")
    if (not isinstance(expected_receipt_digest, str) or
            re.fullmatch(r"[0-9a-f]{64}", expected_receipt_digest) is None or
            claimed_receipt_digest != expected_receipt_digest):
        raise ValueError("packet does not match the frozen packet receipt")
    if (receipt["schema"] != "mmbu.busbra.human_review_packet_receipt.v1" or
            receipt["source_id"] != "busbra" or receipt["source_version"] != "1.0" or
            receipt["review_complete"] is not False or receipt["training_ready"] is not False or
            receipt["model_use_authorized"] is not False):
        raise ValueError("packet receipt identity or pending status mismatch")
    if not isinstance(receipt["members"], list) or not receipt["members"]:
        raise ValueError("packet receipt members must be nonempty")
    seen = set()
    for index, member in enumerate(receipt["members"]):
        member = _closed(member, {"path", "bytes", "sha256"}, f"packet member {index}")
        name = member["path"]
        path = PurePosixPath(name) if isinstance(name, str) else None
        if (path is None or path.is_absolute() or path.as_posix() != name or ".." in path.parts or
                name in seen or type(member["bytes"]) is not int or member["bytes"] < 0 or
                not isinstance(member["sha256"], str) or re.fullmatch(r"[0-9a-f]{64}", member["sha256"]) is None):
            raise ValueError("packet receipt contains an invalid member")
        seen.add(name)
        target = packet / name
        info = target.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise ValueError("packet member is not a regular unaliased file")
        payload = target.read_bytes()
        if len(payload) != member["bytes"] or hashlib.sha256(payload).hexdigest() != member["sha256"]:
            raise ValueError("packet member digest mismatch")
    actual_members = {
        path.relative_to(packet).as_posix()
        for path in packet.rglob("*")
        if path.is_file() and path.relative_to(packet).as_posix() != "packet-receipt.json"
    }
    if actual_members != seen:
        raise ValueError("packet filesystem differs from the frozen receipt membership")
    manifest = _closed(_load_json(packet / "review-manifest.json"), MANIFEST_KEYS, "review manifest")
    unsigned_manifest = dict(manifest)
    claimed_manifest_digest = unsigned_manifest.pop("manifest_digest")
    if (claimed_manifest_digest != _canonical_digest(unsigned_manifest) or
            claimed_manifest_digest != receipt["manifest_digest"]):
        raise ValueError("review manifest digest mismatch")
    if (manifest["schema"] != "mmbu.busbra.human_review_packet_manifest.v1" or
            manifest["source_id"] != "busbra" or manifest["source_version"] != "1.0" or
            manifest["review_status"] != "pending_human_review" or
            manifest["review_complete"] is not False or manifest["training_ready"] is not False or
            manifest["model_use_authorized"] is not False):
        raise ValueError("review manifest identity or pending status mismatch")
    if (not isinstance(manifest["records"], list) or
            manifest["record_count"] != len(manifest["records"]) or
            receipt["record_count"] != manifest["record_count"]):
        raise ValueError("packet record count mismatch")
    return manifest, receipt


def _validate_source_review(source: dict) -> tuple[dict, dict[str, dict | None]]:
    source = _closed(source, SOURCE_KEYS, "completed source review")
    if (source["schema"] != "mmbu.busbra.source_review_completed.v1" or
            source["source_id"] != "busbra" or source["source_version"] != "1.0" or
            source["decision_status"] != "completed_human_review" or
            source["review_complete"] is not True or source["training_ready"] is not False or
            source["model_use_authorized"] is not False):
        raise ValueError("completed source review identity or authority status mismatch")
    medical = _closed(source["medical_review"], MEDICAL_KEYS, "medical_review")
    profiles = {
        "primary": _profile(
            medical["primary_reviewer"], "medical_review.primary_reviewer", "medical_primary"
        ),
        "secondary": _profile(
            medical["secondary_reviewer"], "medical_review.secondary_reviewer", "medical_secondary"
        ),
        "adjudicator": _profile(
            medical["adjudicator"], "medical_review.adjudicator", "adjudicator", optional=True
        ),
    }
    profile_ids = [value["reviewer_id"] for value in profiles.values() if value is not None]
    if len(profile_ids) != len(set(profile_ids)):
        raise ValueError("medical reviewer identities must be distinct")
    provenance = _closed(source["provenance_review"], PROVENANCE_KEYS, "provenance_review")
    _profile(provenance["reviewer"], "provenance_review.reviewer", "provenance")
    if provenance["case_110_536_disposition"] not in PROVENANCE_DECISIONS:
        raise ValueError("provenance_review disposition is unknown")
    _text(provenance["evidence_locator"], "provenance_review.evidence_locator")
    rights = _closed(source["rights_and_release_review"], RIGHTS_KEYS, "rights_and_release_review")
    _profile(rights["reviewer"], "rights_and_release_review.reviewer", "rights_release")
    for name in (
        "training", "development", "untouched_confirmation", "public_weight_release", "challenge_submission",
    ):
        if rights[name] not in RIGHTS_DECISIONS:
            raise ValueError(f"rights_and_release_review.{name} decision is unknown")
    _text(rights["attribution_text"], "rights_and_release_review.attribution_text")
    _text(rights["redistribution_conditions"], "rights_and_release_review.redistribution_conditions")
    return source, profiles


def _split_tasks(value: str, label: str) -> list[str]:
    if value == "":
        return []
    tasks = value.split("|")
    if len(tasks) != len(set(tasks)) or any(task not in TASKS for task in tasks):
        raise ValueError(f"{label} contains unknown or duplicate tasks")
    return tasks


def _bbox_wire(value: str, width: int, height: int, label: str) -> list[int]:
    try:
        box = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} must be a JSON xywh array") from exc
    if (not isinstance(box, list) or len(box) != 4 or any(type(item) is not int for item in box)):
        raise ValueError(f"{label} must contain four integers")
    x, y, box_width, box_height = box
    if (x < 0 or y < 0 or box_width < 1 or box_height < 1 or
            x + box_width > width or y + box_height > height):
        raise ValueError(f"{label} must be positive and in bounds")
    return box


def _strict_json_bytes(payload: bytes, label: str):
    def reject_duplicates(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"{label} contains duplicate JSON key {key}")
            result[key] = value
        return result

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} must be UTF-8") from exc
    return json.loads(
        text,
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"{label} contains non-finite JSON {value}")
        ),
    )


def _completed_rows(payload: bytes) -> list[dict[str, str]]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("completed record review must be UTF-8") from exc
    reader = csv.DictReader(text.splitlines(keepends=True))
    if reader.fieldnames != list(REVIEW_FIELDS):
        raise ValueError("completed record review columns differ from the frozen template")
    rows = list(reader)
    if any(None in row for row in rows):
        raise ValueError("completed record review has extra cells")
    return rows


def validate_completed_review(
    packet: Path,
    completed_records: Path,
    completed_source: Path,
    *,
    expected_packet_receipt_digest: str,
) -> dict:
    """Validate completeness and consistency; never emit an authorization."""
    manifest, receipt = _validate_packet(Path(packet), expected_packet_receipt_digest)
    records_payload = Path(completed_records).read_bytes()
    source_payload = Path(completed_source).read_bytes()
    source, profiles = _validate_source_review(
        _strict_json_bytes(source_payload, "completed source review")
    )
    rows = _completed_rows(records_payload)
    expected = manifest["records"]
    if [row.get("record_id") for row in rows] != [row.get("record_id") for row in expected]:
        raise ValueError("completed review must contain exactly the frozen record population in order")

    blocked = []
    excluded = []
    eligible = []
    for index, (row, frozen) in enumerate(zip(rows, expected, strict=True), 2):
        label = f"record review row {index}"
        for name in REVIEW_FIELDS:
            if not isinstance(row.get(name), str):
                raise ValueError(f"{label}.{name} must be text")
        for name, expected_value in (
            ("case_id", frozen["case_id"]),
            ("pathology", frozen["pathology"]),
            ("birads", frozen["birads"]),
            ("width", str(frozen["width"])),
            ("height", str(frozen["height"])),
            ("decoded_width", str(frozen["decoded_width"])),
            ("decoded_height", str(frozen["decoded_height"])),
            ("source_bbox_xywh", json.dumps(frozen["bbox_xywh"], separators=(",", ":"))),
            ("mask_derived_bbox_xywh", json.dumps(
                frozen["mask_derived_bbox_xywh"], separators=(",", ":")
            )),
            ("image_member", frozen["image_member"]),
            ("mask_member", frozen["mask_member"]),
            ("image_path", frozen["image_path"]),
            ("mask_path", frozen["mask_path"]),
            ("mandatory_reasons", "|".join(frozen["mandatory_reasons"])),
        ):
            if row[name] != expected_value:
                raise ValueError(f"{label}.{name} differs from the frozen manifest")
        _bbox_wire(
            row["mask_derived_bbox_xywh"], frozen["decoded_width"], frozen["decoded_height"],
            f"{label}.mask_derived_bbox_xywh",
        )
        if row["primary_reviewer_id"] != profiles["primary"]["reviewer_id"]:
            raise ValueError(f"{label} primary reviewer differs from the source review")
        primary_time = _timestamp(row["primary_reviewed_at"], f"{label}.primary_reviewed_at")
        if primary_time > _timestamp(profiles["primary"]["reviewed_at"], "primary profile reviewed_at"):
            raise ValueError(f"{label} primary review occurs after the primary profile completion")
        for name in (
            "image_interpretable", "mask_usable", "additional_or_incomplete_lesion", "source_fields_joined",
        ):
            if row[name] not in ANSWERS:
                raise ValueError(f"{label}.{name} has an unknown answer")
        if row["shortcut_artifact"] not in SHORTCUTS:
            raise ValueError(f"{label}.shortcut_artifact has an unknown answer")
        tasks = _split_tasks(row["permitted_tasks"], f"{label}.permitted_tasks")
        primary = row["primary_disposition"]
        final = row["final_disposition"]
        if primary not in DISPOSITIONS or final not in DISPOSITIONS:
            raise ValueError(f"{label} has an unknown disposition")
        _text(row["primary_notes"], f"{label}.primary_notes")

        material = bool(frozen["mandatory_reasons"])
        needs_secondary = material or primary != "eligible" or any(
            row[name] == "uncertain" for name in (
                "image_interpretable", "mask_usable", "additional_or_incomplete_lesion", "source_fields_joined",
            )
        ) or row["shortcut_artifact"] != "none"
        secondary_fields = (
            "secondary_reviewer_id", "secondary_reviewed_at", "secondary_disposition", "secondary_notes",
        )
        if needs_secondary:
            if any(not row[name] for name in secondary_fields):
                raise ValueError(f"{label} requires a complete secondary review")
            if row["secondary_reviewer_id"] != profiles["secondary"]["reviewer_id"]:
                raise ValueError(f"{label} requires the distinct secondary reviewer")
            if row["secondary_reviewer_id"] == row["primary_reviewer_id"]:
                raise ValueError(f"{label} requires a distinct secondary reviewer")
            secondary_time = _timestamp(row["secondary_reviewed_at"], f"{label}.secondary_reviewed_at")
            if secondary_time <= primary_time:
                raise ValueError(f"{label} secondary review must occur after the primary review")
            if secondary_time > _timestamp(profiles["secondary"]["reviewed_at"], "secondary profile reviewed_at"):
                raise ValueError(f"{label} secondary review occurs after the secondary profile completion")
            secondary = row["secondary_disposition"]
            if secondary not in DISPOSITIONS:
                raise ValueError(f"{label}.secondary_disposition is unknown")
            if secondary != primary:
                adjudicator = profiles["adjudicator"]
                if (adjudicator is None or row["adjudicator_id"] != adjudicator["reviewer_id"] or
                        row["adjudicator_id"] in {row["primary_reviewer_id"], row["secondary_reviewer_id"]}):
                    raise ValueError(f"{label} disagreement requires a distinct named adjudicator")
                adjudicated_time = _timestamp(row["adjudicated_at"], f"{label}.adjudicated_at")
                if adjudicated_time <= secondary_time:
                    raise ValueError(f"{label} adjudication must occur after both reviews")
                if adjudicated_time > _timestamp(adjudicator["reviewed_at"], "adjudicator profile reviewed_at"):
                    raise ValueError(f"{label} adjudication occurs after the adjudicator profile completion")
            elif row["adjudicator_id"] or row["adjudicated_at"] or final != primary:
                raise ValueError(f"{label} cannot claim adjudication without a disagreement")
        else:
            if any(row[name] for name in (*secondary_fields, "adjudicator_id", "adjudicated_at")):
                raise ValueError(f"{label} has an undeclared secondary or adjudication review")
            if final != primary:
                raise ValueError(f"{label} final disposition differs without adjudication")

        if final == "eligible":
            if not tasks:
                raise ValueError(f"{label} eligible record must name permitted tasks")
            if (row["image_interpretable"] != "yes" or row["mask_usable"] != "yes" or
                    row["additional_or_incomplete_lesion"] != "no" or row["source_fields_joined"] != "yes"):
                raise ValueError(f"{label} eligible disposition conflicts with review answers")
            eligible.append(row["record_id"])
        elif final in {"excluded", "unresolved"} and tasks:
            raise ValueError(f"{label} excluded or unresolved record cannot name permitted tasks")
        if final == "excluded":
            excluded.append(row["record_id"])
        elif final in {"unresolved", "correction_required"}:
            blocked.append(row["record_id"])

    rights = source["rights_and_release_review"]
    provenance = source["provenance_review"]
    purpose_names = (
        "training", "development", "untouched_confirmation", "public_weight_release", "challenge_submission",
    )
    allowed = [name for name in purpose_names if rights[name] == "approve"]
    source_blockers = []
    provenance_decision = provenance["case_110_536_disposition"]
    required_linked_case_groups = []
    if provenance_decision == "linked_lineage":
        required_linked_case_groups = [["110", "536"]]
    elif provenance_decision == "exclude_or_coassign":
        source_blockers.append("case_110_536_exclusion_or_coassignment_unresolved")
    elif provenance_decision == "unresolved":
        source_blockers.append("case_110_536_provenance_unresolved")
    for name in purpose_names:
        if rights[name] == "narrow":
            source_blockers.append(f"{name}_narrow_requires_scope_binding")
        elif rights[name] in {"decline", "unresolved"}:
            source_blockers.append(f"{name}_{rights[name]}")

    report = {
        "schema": "mmbu.busbra.human_review_validation.v1",
        "source_id": "busbra",
        "source_version": "1.0",
        "packet_receipt_digest": receipt["receipt_digest"],
        "packet_manifest_digest": manifest["manifest_digest"],
        "packet_member_inventory_digest": _canonical_digest(receipt["members"]),
        "completed_records_sha256": hashlib.sha256(records_payload).hexdigest(),
        "completed_records_semantic_digest": _canonical_digest(rows),
        "completed_source_sha256": hashlib.sha256(source_payload).hexdigest(),
        "completed_source_canonical_digest": _canonical_digest(source),
        "record_count": len(rows),
        "review_evidence_complete": True,
        "mechanically_ready_for_phase1_admission_review": not blocked and not source_blockers,
        "reviewer_identity_and_qualification_authenticated": False,
        "phase1_reviewer_attestations_required": True,
        "admission_review_ready": False,
        "eligible_record_ids": eligible,
        "excluded_record_ids": excluded,
        "blocked_record_ids": blocked,
        "source_blockers": source_blockers,
        "required_linked_case_groups": required_linked_case_groups,
        "proposed_allowed_purposes": allowed,
        "source_admission_authorized": False,
        "training_ready": False,
        "model_use_authorized": False,
        "limitations": [
            "This validates form completeness and internal consistency, not medical truth or reviewer identity.",
            "Role claims remain unauthenticated until bound by separate Phase 1 reviewer attestations.",
            "This report is not a source-admission, purpose-authorization, training, release, or submission record.",
            "A separate Phase 1 admission chain must bind the reviewed evidence before any model-use purpose exists.",
        ],
    }
    report["report_digest"] = _canonical_digest(report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--completed-records", type=Path, required=True)
    parser.add_argument("--completed-source", type=Path, required=True)
    parser.add_argument("--expected-packet-receipt-digest", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(
            validate_completed_review(
                args.packet,
                args.completed_records,
                args.completed_source,
                expected_packet_receipt_digest=args.expected_packet_receipt_digest,
            ),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        ))
        return 0
    except (OSError, TypeError, ValueError, KeyError, csv.Error) as exc:
        print(json.dumps({"error": str(exc)}), file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
