"""Validate completed human evidence from a BUS-BRA train-only QA packet."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from .busbra_train_qa import (
    RIGHTS_TEMPLATE_KEYS, UNRESOLVED_PROVENANCE_RECORDS, VISUAL_FIELDS,
    _canonical_digest, _load_json, _verify_file,
)


OPENING_KEYS = {
    "schema", "source_id", "source_version", "packet_receipt_digest", "opened_at", "opened_by",
    "authorization_evidence_locator", "human_attested", "review_opening_authorized",
    "training_ready", "model_use_authorized",
}
YES_NO = {"yes", "no"}
YES_NO_UNCERTAIN = {"yes", "no", "uncertain"}
SHORTCUTS = {"none", "overlay", "caliper", "crop", "text", "panel", "other"}
TARGETS = {"pathology_classification", "birads_classification", "mask_context"}
DISPOSITIONS = {"eligible", "exclude", "escalate"}
RIGHTS_DECISIONS = {"approve", "narrow", "decline", "unresolved"}


def _timestamp(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{label} must be a UTC timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{label} must be a UTC timestamp")
    return parsed


def _nonblank(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be nonblank")
    return value.strip()


def _verify_packet(packet_dir: Path, expected_receipt_digest: str) -> tuple[dict, dict]:
    packet_dir = Path(packet_dir)
    receipt_path = packet_dir / "packet-receipt.json"
    if receipt_path.is_symlink():
        raise ValueError("packet receipt may not be a symbolic link")
    receipt = _load_json(receipt_path)
    if receipt.get("schema") != "mmbu.busbra.train_qa_packet_receipt.v1":
        raise ValueError("packet receipt schema mismatch")
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    if digest != expected_receipt_digest or digest != _canonical_digest(unsigned):
        raise ValueError("packet receipt digest mismatch")
    if any(receipt.get(name) is not False for name in (
        "review_complete", "source_admission_authorized", "training_ready", "model_use_authorized",
    )):
        raise ValueError("packet receipt contains authority")
    seen = set()
    for index, row in enumerate(receipt.get("members", [])):
        path = _verify_file(packet_dir, row, f"packet member[{index}]")
        relative = path.relative_to(packet_dir).as_posix()
        if relative in seen:
            raise ValueError("packet receipt contains duplicate member paths")
        seen.add(relative)
    if "train-qa-manifest.json" not in seen:
        raise ValueError("packet receipt does not bind the train-QA manifest")
    manifest = _load_json(packet_dir / "train-qa-manifest.json")
    if manifest.get("schema") != "mmbu.busbra.train_qa_manifest.v1":
        raise ValueError("train-QA manifest schema mismatch")
    unsigned_manifest = dict(manifest)
    manifest_digest = unsigned_manifest.pop("manifest_digest", None)
    if manifest_digest != _canonical_digest(unsigned_manifest):
        raise ValueError("train-QA manifest digest mismatch")
    if receipt.get("manifest_digest") != manifest_digest:
        raise ValueError("packet receipt does not bind the train-QA manifest")
    if receipt.get("record_count") != manifest.get("record_count") or manifest.get("record_count") != len(manifest.get("records", [])):
        raise ValueError("train-QA record count mismatch")
    return receipt, manifest


def _read_visual(path: Path) -> tuple[bytes, list[dict[str, str]]]:
    payload = Path(path).read_bytes()
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("completed visual review must be UTF-8") from exc
    reader = csv.DictReader(text.splitlines(keepends=True))
    if reader.fieldnames != list(VISUAL_FIELDS):
        raise ValueError("completed visual review columns differ from the frozen template")
    rows = list(reader)
    return payload, rows


def _parse_targets(value: str, label: str) -> list[str]:
    values = value.split("|") if value else []
    if values != sorted(set(values)) or not set(values) <= TARGETS:
        raise ValueError(f"{label} contains invalid or noncanonical targets")
    return values


def validate_train_qa(
    packet_dir: Path,
    completed_visual: Path,
    completed_rights: Path,
    opening_path: Path,
    expected_receipt_digest: str,
    *,
    now: datetime | None = None,
) -> dict:
    """Return a non-authoritative mechanical readiness report."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo != timezone.utc:
        raise ValueError("now must be timezone-aware UTC")
    receipt, manifest = _verify_packet(Path(packet_dir), expected_receipt_digest)
    opening = _load_json(Path(opening_path))
    if set(opening) != OPENING_KEYS:
        raise ValueError("review opening record must be closed")
    if (opening["schema"] != "mmbu.busbra.train_qa_opening.v1" or
            opening["source_id"] != "busbra" or opening["source_version"] != "1.0" or
            opening["packet_receipt_digest"] != receipt["receipt_digest"] or
            opening["human_attested"] is not True or opening["review_opening_authorized"] is not True or
            opening["training_ready"] is not False or opening["model_use_authorized"] is not False):
        raise ValueError("review opening identity or authority mismatch")
    _nonblank(opening["opened_by"], "review opening.opened_by")
    _nonblank(opening["authorization_evidence_locator"], "review opening.authorization_evidence_locator")
    opened_at = _timestamp(opening["opened_at"], "review opening.opened_at")
    if opened_at > now:
        raise ValueError("review opening may not be in the future")

    visual_payload, rows = _read_visual(Path(completed_visual))
    expected = {row["record_id"]: row for row in manifest["records"]}
    if len(rows) != len(expected):
        raise ValueError("completed visual review row count mismatch")
    if len({row["record_id"] for row in rows}) != len(rows):
        raise ValueError("completed visual review contains duplicate record IDs")

    eligible = {}
    excluded = []
    escalated = []
    reviewers = set()
    routine_critical_failures = 0
    routine_count = 0
    shortcut_counts = {}
    for index, row in enumerate(rows):
        label = f"completed visual review row {index + 1}"
        source = expected.get(row["record_id"])
        if source is None:
            raise ValueError(f"{label} is not in the frozen population")
        frozen = {
            "record_id": source["record_id"], "case_id": source["case_id"],
            "selection_role": source["selection_role"],
            "mandatory_reasons": "|".join(source["mandatory_reasons"]),
            "image_path": source["image_path"], "mask_path": source["mask_path"],
        }
        if any(row[key] != value for key, value in frozen.items()):
            raise ValueError(f"{label} changes frozen identity fields")
        reviewer = _nonblank(row["reviewer_id"], f"{label}.reviewer_id")
        reviewers.add(reviewer)
        reviewed_at = _timestamp(row["reviewed_at"], f"{label}.reviewed_at")
        if reviewed_at <= opened_at:
            raise ValueError("completed visual review must occur after the authorized opening")
        if reviewed_at > now:
            raise ValueError("completed visual review may not be in the future")
        for key in ("asset_match", "image_interpretable"):
            if row[key] not in YES_NO:
                raise ValueError(f"{label}.{key} has an invalid value")
        for key in ("modality_body_part_supported", "mask_alignment", "annotation_completeness_concern"):
            if row[key] not in YES_NO_UNCERTAIN:
                raise ValueError(f"{label}.{key} has an invalid value")
        if row["shortcut_artifact"] not in SHORTCUTS:
            raise ValueError(f"{label}.shortcut_artifact has an invalid value")
        shortcut_counts[row["shortcut_artifact"]] = shortcut_counts.get(row["shortcut_artifact"], 0) + 1
        targets = _parse_targets(row["permitted_training_targets"], f"{label}.permitted_training_targets")
        if row["final_disposition"] not in DISPOSITIONS:
            raise ValueError(f"{label}.final_disposition has an invalid value")
        adverse = (
            row["asset_match"] == "no" or row["image_interpretable"] == "no" or
            row["modality_body_part_supported"] != "yes" or row["mask_alignment"] != "yes" or
            row["annotation_completeness_concern"] != "no" or row["shortcut_artifact"] != "none" or
            row["final_disposition"] != "eligible"
        )
        if adverse:
            _nonblank(row["notes"], f"{label}.notes")
        critical = (
            row["asset_match"] != "yes" or row["image_interpretable"] != "yes" or
            row["modality_body_part_supported"] != "yes"
        )
        if source["selection_role"] == "routine":
            routine_count += 1
            routine_critical_failures += int(critical)
        if "mask_context" in targets and (
            row["mask_alignment"] != "yes" or row["annotation_completeness_concern"] != "no"
        ):
            raise ValueError(f"{label} permits mask_context despite unresolved mask QA")
        if row["final_disposition"] == "eligible":
            if not targets or critical:
                raise ValueError(f"{label} is eligible without usable training targets")
            eligible[row["record_id"]] = targets
        elif row["final_disposition"] == "exclude":
            if targets:
                raise ValueError(f"{label} excludes a record but retains targets")
            excluded.append(row["record_id"])
        else:
            escalated.append(row["record_id"])

    rights_payload = Path(completed_rights).read_bytes()
    rights = _load_json(Path(completed_rights))
    if set(rights) != RIGHTS_TEMPLATE_KEYS:
        raise ValueError("completed rights review must be closed")
    if (rights["schema"] != "mmbu.busbra.train_rights_completed.v1" or
            rights["source_id"] != "busbra" or rights["source_version"] != "1.0" or
            rights["purpose"] != "train" or rights["human_attested"] is not True or
            rights["review_complete"] is not True):
        raise ValueError("completed rights review identity or completion mismatch")
    for key in (
        "reviewer_id", "qualification_evidence_locator", "conflict_status", "conflict_evidence_locator",
        "license_evidence_locator", "attribution_text", "challenge_disclosure", "retention_policy",
    ):
        _nonblank(rights[key], f"completed rights review.{key}")
    rights_at = _timestamp(rights["reviewed_at"], "completed rights review.reviewed_at")
    if rights_at <= opened_at:
        raise ValueError("completed rights review must occur after the authorized opening")
    if rights_at > now:
        raise ValueError("completed rights review may not be in the future")
    if rights["train_decision"] not in RIGHTS_DECISIONS:
        raise ValueError("completed rights review.train_decision has an invalid value")
    if rights["train_decision"] == "narrow":
        _nonblank(rights["narrow_scope"], "completed rights review.narrow_scope")
    elif rights["narrow_scope"] is not None:
        raise ValueError("completed rights review.narrow_scope is only valid for narrow")
    for key in (
        "public_weight_release_authorized", "adaptive_development_authorized", "confirmation_authorized",
        "upload_authorized", "submission_authorized",
    ):
        if rights[key] is not False:
            raise ValueError(f"completed rights review.{key} must remain false")

    mandatory_ids = {row["record_id"] for row in manifest["records"] if row["selection_role"] == "mandatory"}
    terminal_ids = set(eligible) | set(excluded)
    all_mandatory_terminal = mandatory_ids <= terminal_ids
    unresolved_absent = not (set(expected) & UNRESOLVED_PROVENANCE_RECORDS)
    rights_compatible = rights["train_decision"] in {"approve", "narrow"}
    ready = bool(
        all_mandatory_terminal and not escalated and routine_critical_failures == 0 and
        rights_compatible and unresolved_absent and eligible
    )
    visual_canonical = [dict(row) for row in sorted(rows, key=lambda row: row["record_id"])]
    report = {
        "schema": "mmbu.busbra.train_qa_validation.v1",
        "source_id": "busbra", "source_version": "1.0", "purpose": "train",
        "packet_receipt_digest": receipt["receipt_digest"],
        "opening_digest": _canonical_digest(opening),
        "completed_visual_raw_sha256": hashlib.sha256(visual_payload).hexdigest(),
        "completed_visual_canonical_digest": _canonical_digest(visual_canonical),
        "completed_rights_raw_sha256": hashlib.sha256(rights_payload).hexdigest(),
        "completed_rights_canonical_digest": _canonical_digest(rights),
        "visual_reviewer_ids": sorted(reviewers), "rights_reviewer_id": rights["reviewer_id"],
        "eligible_record_ids": sorted(eligible), "eligible_targets_by_record": eligible,
        "excluded_record_ids": sorted(excluded), "escalated_record_ids": sorted(escalated),
        "mandatory_records_terminal": all_mandatory_terminal,
        "routine_review_count": routine_count,
        "routine_critical_failure_count": routine_critical_failures,
        "routine_rule_of_three_upper_bound": None if routine_count == 0 else min(1.0, 3.0 / routine_count),
        "shortcut_artifact_counts": dict(sorted(shortcut_counts.items())),
        "rights_train_decision": rights["train_decision"],
        "admission_input_ready": ready,
        "source_admission_authorized": False, "training_ready": False, "model_use_authorized": False,
        "validated_at": now.isoformat().replace("+00:00", "Z"),
    }
    report["report_digest"] = _canonical_digest(report)
    return report
