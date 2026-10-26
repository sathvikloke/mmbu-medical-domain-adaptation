"""Project an immutable BUS-BRA review packet into train-only visual QA.

Projection is preparation evidence only. It grants no source admission,
training, model-use, release, or clinical authority.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile

from .busbra_review import _rename_no_replace


ROUTINE_PATIENT_TARGET = 60
UNRESOLVED_PROVENANCE_RECORDS = frozenset({"bus_0110-l", "bus_0536-r"})
FORCED_VISUAL_RECORDS = frozenset({"bus_0845-s"})
VISUAL_FIELDS = (
    "record_id", "case_id", "selection_role", "mandatory_reasons", "image_path", "mask_path",
    "reviewer_id", "reviewed_at", "asset_match", "image_interpretable",
    "modality_body_part_supported", "mask_alignment", "annotation_completeness_concern",
    "shortcut_artifact", "permitted_training_targets", "final_disposition", "notes",
)
RIGHTS_TEMPLATE_KEYS = {
    "schema", "source_id", "source_version", "purpose", "reviewer_id", "reviewed_at",
    "qualification_evidence_locator", "conflict_status", "conflict_evidence_locator",
    "license_evidence_locator", "attribution_text", "challenge_disclosure", "retention_policy",
    "train_decision", "narrow_scope", "public_weight_release_authorized",
    "adaptive_development_authorized", "confirmation_authorized", "upload_authorized",
    "submission_authorized", "human_attested", "review_complete",
}


def _canonical_bytes(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("ascii")


def _canonical_digest(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _load_json(path: Path):
    def reject_duplicates(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(
        path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON: {value}")),
    )


def _safe_relative(value: object, label: str) -> PurePosixPath:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"{label} is not a safe relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"{label} is not a safe relative path")
    return path


def _verify_file(root: Path, row: dict, prefix: str) -> Path:
    if not isinstance(row, dict) or set(row) != {"path", "bytes", "sha256"}:
        raise ValueError(f"{prefix} entry must be closed")
    relative = _safe_relative(row["path"], f"{prefix}.path")
    path = root.joinpath(*relative.parts)
    if path.is_symlink():
        raise ValueError(f"{prefix} may not be a symbolic link")
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"{prefix} is unreadable") from exc
    if len(payload) != row["bytes"] or hashlib.sha256(payload).hexdigest() != row["sha256"]:
        raise ValueError(f"{prefix} digest mismatch")
    return path


def verify_predecessor_packet(packet_dir: Path) -> tuple[dict, dict]:
    packet_dir = Path(packet_dir)
    receipt_path = packet_dir / "packet-receipt.json"
    if receipt_path.is_symlink():
        raise ValueError("predecessor receipt may not be a symbolic link")
    receipt = _load_json(receipt_path)
    if receipt.get("schema") != "mmbu.busbra.human_review_packet_receipt.v2":
        raise ValueError("predecessor receipt schema mismatch")
    if receipt.get("source_id") != "busbra" or receipt.get("source_version") != "1.0":
        raise ValueError("predecessor source identity mismatch")
    if any(receipt.get(name) is not False for name in (
        "review_complete", "training_ready", "model_use_authorized",
    )):
        raise ValueError("predecessor receipt contains authority")
    unsigned = dict(receipt)
    digest = unsigned.pop("receipt_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("predecessor receipt digest mismatch")
    members = receipt.get("members")
    if not isinstance(members, list) or not members:
        raise ValueError("predecessor receipt members are missing")
    seen = set()
    for index, row in enumerate(members):
        path = _verify_file(packet_dir, row, f"predecessor member[{index}]")
        relative = path.relative_to(packet_dir).as_posix()
        if relative in seen:
            raise ValueError("predecessor receipt contains duplicate member paths")
        seen.add(relative)
    if "review-manifest.json" not in seen:
        raise ValueError("predecessor receipt does not bind the review manifest")
    manifest = _load_json(packet_dir / "review-manifest.json")
    if manifest.get("schema") != "mmbu.busbra.human_review_packet_manifest.v2":
        raise ValueError("predecessor manifest schema mismatch")
    if manifest.get("source_id") != "busbra" or manifest.get("source_version") != "1.0":
        raise ValueError("predecessor manifest source identity mismatch")
    unsigned_manifest = dict(manifest)
    manifest_digest = unsigned_manifest.pop("manifest_digest", None)
    if manifest_digest != _canonical_digest(unsigned_manifest):
        raise ValueError("predecessor manifest digest mismatch")
    if receipt.get("manifest_digest") != manifest_digest:
        raise ValueError("predecessor receipt does not bind the manifest")
    records = manifest.get("records")
    if not isinstance(records, list) or manifest.get("record_count") != len(records):
        raise ValueError("predecessor record count mismatch")
    if receipt.get("record_count") != len(records):
        raise ValueError("predecessor receipt record count mismatch")
    ids = [row.get("record_id") for row in records if isinstance(row, dict)]
    if len(ids) != len(records) or len(ids) != len(set(ids)):
        raise ValueError("predecessor record IDs must be unique")
    for row in records:
        for key in ("image_path", "mask_path"):
            relative = _safe_relative(row.get(key), f"record {row['record_id']}.{key}").as_posix()
            if relative not in seen:
                raise ValueError(
                    f"record {row['record_id']} {key} is not bound by the predecessor receipt"
                )
    return receipt, manifest


def _selection(manifest: dict) -> list[dict]:
    candidates = []
    for row in manifest["records"]:
        record_id = row.get("record_id")
        case_id = row.get("case_id")
        if not isinstance(record_id, str) or not isinstance(case_id, str) or not case_id:
            raise ValueError("predecessor record identity is invalid")
        for key in ("image_path", "mask_path"):
            _safe_relative(row.get(key), f"record {record_id}.{key}")
        reasons = row.get("mandatory_reasons")
        if not isinstance(reasons, list) or any(not isinstance(value, str) for value in reasons):
            raise ValueError("predecessor mandatory reasons are invalid")
        if record_id in UNRESOLVED_PROVENANCE_RECORDS:
            continue
        mandatory = bool(reasons) or record_id in FORCED_VISUAL_RECORDS
        candidates.append((row, mandatory))

    mandatory_rows = [row for row, mandatory in candidates if mandatory]
    routine_by_case = {}
    for row, mandatory in candidates:
        if mandatory:
            continue
        routine_by_case.setdefault(row["case_id"], []).append(row)
    ranked_cases = sorted(
        routine_by_case,
        key=lambda case_id: (
            hashlib.sha256(f"{manifest['manifest_digest']}:{case_id}".encode()).hexdigest(), case_id,
        ),
    )[:ROUTINE_PATIENT_TARGET]
    routine_rows = [
        sorted(routine_by_case[case_id], key=lambda row: row["record_id"])[0]
        for case_id in ranked_cases
    ]
    selected = [(row, "mandatory") for row in mandatory_rows] + [
        (row, "routine") for row in routine_rows
    ]
    return [
        {**row, "selection_role": role}
        for row, role in sorted(selected, key=lambda item: item[0]["record_id"])
    ]


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _file_entry(root: Path, path: Path) -> dict:
    payload = path.read_bytes()
    return {"path": path.relative_to(root).as_posix(), "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest()}


def build_train_qa_packet(packet_dir: Path, output_dir: Path) -> dict:
    """Create a no-overwrite BUS-BRA train-only human-QA packet."""
    packet_dir = Path(packet_dir)
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise FileExistsError(str(output_dir))
    predecessor_receipt, predecessor_manifest = verify_predecessor_packet(packet_dir)
    selected = _selection(predecessor_manifest)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".busbra-train-qa-", dir=output_dir.parent))
    try:
        manifest_rows = []
        for row in selected:
            record_id = row["record_id"]
            target_dir = staging / "assets" / record_id
            target_dir.mkdir(parents=True)
            projected_paths = {}
            for role in ("image", "mask"):
                source_relative = _safe_relative(row[f"{role}_path"], f"record {record_id}.{role}_path")
                source = packet_dir.joinpath(*source_relative.parts)
                if source.is_symlink():
                    raise ValueError(f"record {record_id} {role} may not be a symbolic link")
                target = target_dir / f"{role}.png"
                target.write_bytes(source.read_bytes())
                projected_paths[role] = target.relative_to(staging).as_posix()
            manifest_rows.append({
                "record_id": record_id,
                "case_id": row["case_id"],
                "pathology": row["pathology"],
                "birads": row["birads"],
                "decoded_width": row["decoded_width"],
                "decoded_height": row["decoded_height"],
                "mask_derived_bbox_xywh": row["mask_derived_bbox_xywh"],
                "mandatory_reasons": row["mandatory_reasons"],
                "selection_role": row["selection_role"],
                "image_path": projected_paths["image"],
                "mask_path": projected_paths["mask"],
            })
        manifest = {
            "schema": "mmbu.busbra.train_qa_manifest.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "purpose": "train",
            "predecessor_packet_receipt_digest": predecessor_receipt["receipt_digest"],
            "predecessor_manifest_digest": predecessor_manifest["manifest_digest"],
            "selection_algorithm": "mandatory-plus-sha256-patient-rank-v1",
            "routine_patient_target": ROUTINE_PATIENT_TARGET,
            "excluded_provenance_records": sorted(UNRESOLVED_PROVENANCE_RECORDS),
            "record_count": len(manifest_rows),
            "mandatory_record_count": sum(row["selection_role"] == "mandatory" for row in manifest_rows),
            "routine_patient_count": sum(row["selection_role"] == "routine" for row in manifest_rows),
            "records": manifest_rows,
            "review_complete": False,
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
        }
        manifest["manifest_digest"] = _canonical_digest(manifest)
        _write_json(staging / "train-qa-manifest.json", manifest)
        with (staging / "visual-review-template.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=VISUAL_FIELDS, lineterminator="\n")
            writer.writeheader()
            for row in manifest_rows:
                writer.writerow({
                    "record_id": row["record_id"], "case_id": row["case_id"],
                    "selection_role": row["selection_role"],
                    "mandatory_reasons": "|".join(row["mandatory_reasons"]),
                    "image_path": row["image_path"], "mask_path": row["mask_path"],
                })
        rights = {
            "schema": "mmbu.busbra.train_rights_template.v1",
            "source_id": "busbra", "source_version": "1.0", "purpose": "train",
            "reviewer_id": None, "reviewed_at": None, "qualification_evidence_locator": None,
            "conflict_status": None, "conflict_evidence_locator": None,
            "license_evidence_locator": None, "attribution_text": None,
            "challenge_disclosure": None, "retention_policy": None, "train_decision": None,
            "narrow_scope": None, "public_weight_release_authorized": False,
            "adaptive_development_authorized": False, "confirmation_authorized": False,
            "upload_authorized": False, "submission_authorized": False,
            "human_attested": None, "review_complete": False,
        }
        if set(rights) != RIGHTS_TEMPLATE_KEYS:
            raise AssertionError("rights template schema drift")
        _write_json(staging / "rights-purpose-template.json", rights)
        (staging / "README.txt").write_text(
            "BUS-BRA TRAIN-ONLY VISUAL QA PACKET\n\n"
            "This packet grants no source admission, training, model-use, release, clinical, upload, or submission "
            "authority. Copy the two templates outside this immutable directory, complete them with accountable "
            "human evidence, and run the validator before the separate Phase 1 admission chain.\n",
            encoding="utf-8",
        )
        member_paths = sorted(
            (path for path in staging.rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(staging).as_posix().encode(),
        )
        receipt = {
            "schema": "mmbu.busbra.train_qa_packet_receipt.v1",
            "source_id": "busbra", "source_version": "1.0", "purpose": "train",
            "predecessor_packet_receipt_digest": predecessor_receipt["receipt_digest"],
            "manifest_digest": manifest["manifest_digest"], "record_count": len(manifest_rows),
            "members": [_file_entry(staging, path) for path in member_paths],
            "review_complete": False, "source_admission_authorized": False,
            "training_ready": False, "model_use_authorized": False,
        }
        receipt["receipt_digest"] = _canonical_digest(receipt)
        _write_json(staging / "packet-receipt.json", receipt)
        _rename_no_replace(staging, output_dir)
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)
