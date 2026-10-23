"""Build a deterministic offline BUS-BRA packet for accountable human review.

The packet is preparation evidence only.  It never records a medical, rights,
training, release, or model-use approval.
"""

from __future__ import annotations

import argparse
import ctypes
import csv
import errno
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile


ARCHIVE_BYTES = 133_917_740
ARCHIVE_MD5 = "1f8b2be6476d58fc97bfb5e5a1ea9bab"
SELECTION_ALGORITHM = "rarest-pathology-birads-stratum-then-record-id-case-exclusive-v1"
PER_STRATUM = 35
STRATIFIED_PLAN_DIGEST = "71281236f41d658b1985906c872896647f773f6598947b526221509d34a5b912"
HUMAN_PLAN_DIGEST = "98f9f5f00658429bd68a90102dcc4b325f657d1544b15b55d69074c42443d247"
STRUCTURAL_CONTRACT_DIGEST = "6d9f478cc55ffd761f94bf21dee9e66ec111846c63113aa440bcac8afd8ddf4f"
METADATA_MEMBER = "BUSBRA/bus_data.csv"
METADATA_FIELDS = (
    "ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX"
)
PLAN_KEYS = {
    "schema", "source_id", "source_version", "metadata_member", "metadata_sha256",
    "selection_algorithm", "per_stratum", "records", "selected_case_count",
    "biomedical_pixels_opened", "model_executed", "model_use_authorized", "plan_digest",
}
PLAN_RECORD_KEYS = {
    "record_id", "case_id", "pathology", "birads", "width", "height", "bbox_xywh",
    "image_member", "mask_member",
}
EXPECTED_MANDATORY_RULES = [
    "all bbox_exception_records",
    "all dimension_exception_records",
    "bus_0110-l",
    "bus_0536-r",
]
HUMAN_PLAN_KEYS = {
    "decision_status", "exception_population_source", "exception_population_source_digest",
    "mandatory_record_rules", "medical_review_population", "proposed_task_decisions", "review_roles",
    "schema", "source_id", "source_version", "training_ready",
}
HUMAN_POPULATION_KEYS = {
    "expected_mandatory_record_count", "expected_overlap_record_count",
    "expected_stratified_record_count", "expected_union_record_count", "metadata_sha256", "selection",
    "stratified_plan_digest", "stratified_plan_per_pathology_birads_stratum",
    "stratified_plan_selection_algorithm",
}
REVIEW_ROLE_KEYS = {"medical_primary", "medical_secondary", "provenance", "rights_release"}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ID_PATTERN = re.compile(r"bus_([0-9]{4})-([lrs])")


def _canonical_bytes(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def _canonical_digest(value) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _validate_digest_record(value: dict, field: str, label: str) -> None:
    if not isinstance(value, dict) or not isinstance(value.get(field), str):
        raise ValueError(f"{label} digest is missing")
    unsigned = dict(value)
    claimed = unsigned.pop(field)
    if claimed != _canonical_digest(unsigned):
        raise ValueError(f"{label} digest mismatch")


def _positive_integer(value: str, label: str) -> int:
    if not isinstance(value, str) or not value.isdigit() or int(value) < 1:
        raise ValueError(f"{label} must be a positive integer")
    return int(value)


def _bbox(value: str, width: int, height: int) -> list[int]:
    try:
        result = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("BBOX must be a JSON xywh array") from exc
    if (not isinstance(result, list) or len(result) != 4 or
            any(type(item) is not int for item in result)):
        raise ValueError("BBOX must contain four integers")
    x, y, box_width, box_height = result
    if (x < 0 or y < 0 or box_width < 1 or box_height < 1 or
            x + box_width > width or y + box_height > height):
        raise ValueError("BBOX is not positive and in bounds")
    return result


def _read_metadata(payload: bytes) -> dict[str, dict]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("metadata must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != list(METADATA_FIELDS):
        raise ValueError("metadata columns must exactly match BUS-BRA bus_data.csv")
    records = {}
    for line, row in enumerate(reader, 2):
        if None in row or any(not isinstance(row[name], str) or row[name] == "" for name in METADATA_FIELDS):
            raise ValueError(f"metadata row {line} is incomplete")
        match = ID_PATTERN.fullmatch(row["ID"])
        if match is None or row["ID"] in records:
            raise ValueError("record IDs must be unique canonical BUS-BRA IDs")
        case_id = _positive_integer(row["Case"], "Case")
        if int(match.group(1)) != case_id:
            raise ValueError("record ID and Case disagree")
        width = _positive_integer(row["Width"], "Width")
        height = _positive_integer(row["Height"], "Height")
        suffix = row["ID"][4:]
        records[row["ID"]] = {
            "record_id": row["ID"],
            "case_id": str(case_id),
            "pathology": row["Pathology"],
            "birads": row["BIRADS"],
            "width": width,
            "height": height,
            "bbox_xywh": _bbox(row["BBOX"], width, height),
            "image_member": f"BUSBRA/Images/{row['ID']}.png",
            "mask_member": f"BUSBRA/Masks/mask_{suffix}.png",
        }
    if not records:
        raise ValueError("metadata must contain at least one record")
    return records


def _safe_members(archive: zipfile.ZipFile) -> dict[str, zipfile.ZipInfo]:
    members = {}
    aliases = set()
    total = 0
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        normalized = unicodedata.normalize("NFC", name).casefold()
        if (not name or path.is_absolute() or ".." in path.parts or "." in path.parts or
                "\\" in name or "\0" in name or name != path.as_posix() + ("/" if info.is_dir() else "") or
                name in members or normalized in aliases):
            raise ValueError("archive contains an unsafe or duplicate member")
        aliases.add(normalized)
        if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError("archive contains an encrypted or linked member")
        if not info.is_dir():
            if info.file_size > 20_000_000:
                raise ValueError("archive member exceeds the review size ceiling")
            total += info.file_size
            members[name] = info
        if len(aliases) > 5_000 or total > 500_000_000:
            raise ValueError("archive exceeds review inventory ceilings")
    return members


def _archive_identity(path: Path, expected_bytes: int, expected_md5: str) -> bytes:
    if type(expected_bytes) is not int or expected_bytes < 1:
        raise ValueError("expected archive byte count must be positive")
    if not isinstance(expected_md5, str) or re.fullmatch(r"[0-9a-f]{32}", expected_md5) is None:
        raise ValueError("expected archive MD5 must be lowercase hexadecimal")
    path = Path(path).resolve(strict=True)
    payload = path.read_bytes()
    if len(payload) != expected_bytes or hashlib.md5(payload).hexdigest() != expected_md5:
        raise ValueError("archive identity differs from the pinned source")
    return payload


def _validate_plan(plan: dict, metadata: bytes, records: dict[str, dict]) -> None:
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
        raise ValueError("stratified plan must be closed")
    _validate_digest_record(plan, "plan_digest", "plan")
    if plan["plan_digest"] != STRATIFIED_PLAN_DIGEST:
        raise ValueError("plan is not the frozen stratified plan")
    if (plan["schema"] != "mmbu.busbra.quarantine_sample_plan.v1" or
            plan["source_id"] != "busbra" or plan["source_version"] != "1.0" or
            plan["metadata_member"] != METADATA_MEMBER or
            plan["selection_algorithm"] != SELECTION_ALGORITHM or
            plan["per_stratum"] != PER_STRATUM):
        raise ValueError("stratified plan identifies a different source")
    if plan["metadata_sha256"] != hashlib.sha256(metadata).hexdigest():
        raise ValueError("stratified plan metadata digest mismatch")
    if any(plan[name] is not False for name in ("biomedical_pixels_opened", "model_executed", "model_use_authorized")):
        raise ValueError("stratified plan may not claim access or authority")
    if not isinstance(plan["records"], list) or not plan["records"]:
        raise ValueError("stratified plan must select records")
    seen = set()
    for row in plan["records"]:
        if not isinstance(row, dict) or set(row) != PLAN_RECORD_KEYS:
            raise ValueError("stratified plan record is not closed")
        record_id = row["record_id"]
        if record_id in seen or records.get(record_id) != row:
            raise ValueError("stratified plan record differs from source metadata")
        seen.add(record_id)
    if plan["selected_case_count"] != len({row["case_id"] for row in plan["records"]}):
        raise ValueError("stratified plan selected-case count mismatch")
    if plan["records"] != _recompute_stratified_records(records):
        raise ValueError("plan records differ from the independently recomputed frozen selection")


def _recompute_stratified_records(records: dict[str, dict]) -> list[dict]:
    strata: dict[tuple[str, str], list[dict]] = {}
    for record in records.values():
        strata.setdefault((record["pathology"], record["birads"]), []).append(record)
    stratum_order = sorted(
        strata,
        key=lambda key: (len({row["case_id"] for row in strata[key]}), key),
    )
    selected = []
    used_cases = set()
    for key in stratum_order:
        chosen = 0
        for record in sorted(strata[key], key=lambda row: row["record_id"]):
            if record["case_id"] in used_cases:
                continue
            used_cases.add(record["case_id"])
            selected.append(record)
            chosen += 1
            if chosen == PER_STRATUM:
                break
    return sorted(selected, key=lambda row: (row["pathology"], row["birads"], row["record_id"]))


def _review_population(plan: dict, human_plan: dict, contract: dict) -> tuple[list[str], dict[str, list[str]]]:
    if not isinstance(human_plan, dict) or set(human_plan) != HUMAN_PLAN_KEYS:
        raise ValueError("human-review plan must be closed")
    if human_plan.get("schema") != "mmbu.busbra.human_review_plan.v1":
        raise ValueError("human-review plan schema mismatch")
    if _canonical_digest(human_plan) != HUMAN_PLAN_DIGEST:
        raise ValueError("human-review plan is not the frozen human-review plan")
    if human_plan.get("decision_status") != "pending_human_review" or human_plan.get("training_ready") is not False:
        raise ValueError("human-review plan must remain pending and non-training-ready")
    if human_plan.get("source_id") != "busbra" or human_plan.get("source_version") != "1.0":
        raise ValueError("human-review plan identifies a different source")
    if human_plan.get("mandatory_record_rules") != EXPECTED_MANDATORY_RULES:
        raise ValueError("human-review plan mandatory rules differ")
    _validate_digest_record(contract, "contract_digest", "structural contract")
    if _canonical_digest(contract) != STRUCTURAL_CONTRACT_DIGEST:
        raise ValueError("structural contract is not the frozen structural contract")
    if (contract.get("schema") != "mmbu.busbra.structural_transform_contract.v1" or
            contract.get("source_id") != "busbra" or contract.get("source_version") != "1.0"):
        raise ValueError("structural contract identifies a different source")
    if human_plan.get("exception_population_source_digest") != contract["contract_digest"]:
        raise ValueError("human-review plan does not bind the structural contract")
    population = human_plan.get("medical_review_population")
    if not isinstance(population, dict) or set(population) != HUMAN_POPULATION_KEYS:
        raise ValueError("human-review population must be closed")
    roles = human_plan.get("review_roles")
    if not isinstance(roles, dict) or set(roles) != REVIEW_ROLE_KEYS:
        raise ValueError("human-review roles must be closed")
    if (not isinstance(human_plan.get("proposed_task_decisions"), list) or
            not human_plan["proposed_task_decisions"] or
            any(not isinstance(value, str) or not value for value in human_plan["proposed_task_decisions"])):
        raise ValueError("human-review task decisions must be explicit")
    if population.get("stratified_plan_digest") != plan["plan_digest"]:
        raise ValueError("human-review plan does not bind the stratified plan")
    if population.get("metadata_sha256") != plan["metadata_sha256"]:
        raise ValueError("human-review population metadata digest mismatch")
    if population.get("stratified_plan_per_pathology_birads_stratum") != plan["per_stratum"]:
        raise ValueError("human-review per-stratum setting mismatch")
    if population.get("stratified_plan_selection_algorithm") != plan["selection_algorithm"]:
        raise ValueError("human-review selection algorithm mismatch")

    reasons: dict[str, list[str]] = {}
    for record_id in contract.get("bbox_exception_records", []):
        reasons.setdefault(record_id, []).append("bbox_exception")
    for record_id in contract.get("dimension_exception_records", []):
        reasons.setdefault(record_id, []).append("dimension_exception")
    for record_id in ("bus_0110-l", "bus_0536-r"):
        reasons.setdefault(record_id, []).append("provenance_pair")
    mandatory = set(reasons)
    stratified = {row["record_id"] for row in plan["records"]}
    union = sorted(stratified | mandatory)
    overlap = stratified & mandatory
    expected = {
        "expected_mandatory_record_count": len(mandatory),
        "expected_overlap_record_count": len(overlap),
        "expected_stratified_record_count": len(stratified),
        "expected_union_record_count": len(union),
    }
    if any(population.get(name) != value for name, value in expected.items()):
        raise ValueError("human-review population arithmetic mismatch")
    return union, reasons


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def _load_json(path: Path):
    def reject_duplicates(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(
        Path(path).read_text(encoding="utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON: {value}")),
    )


def _file_entry(root: Path, path: Path) -> dict:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _rename_no_replace(source: Path, destination: Path) -> None:
    """Atomically publish a directory and fail when the destination exists."""
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        renamex_np = libc.renamex_np
        renamex_np.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        renamex_np.restype = ctypes.c_int
        result = renamex_np(source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        if not hasattr(libc, "renameat2"):
            raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
        renameat2 = libc.renameat2
        renameat2.argtypes = (
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        result = renameat2(-100, source_bytes, -100, destination_bytes, 1)  # AT_FDCWD, RENAME_NOREPLACE
    elif os.name == "nt":
        os.rename(source, destination)
        return
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def build_review_packet(
    archive_path: Path,
    stratified_plan: dict,
    human_plan: dict,
    structural_contract: dict,
    output: Path,
) -> dict:
    """Atomically publish a local, still-pending human-review packet."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".busbra-review-", dir=output.parent))
    try:
        archive_payload = _archive_identity(archive_path, ARCHIVE_BYTES, ARCHIVE_MD5)
        with zipfile.ZipFile(io.BytesIO(archive_payload)) as archive:
            members = _safe_members(archive)
            metadata_info = members.get(METADATA_MEMBER)
            if metadata_info is None or metadata_info.file_size > 1_000_000:
                raise ValueError("BUS-BRA metadata member is missing or too large")
            metadata = archive.read(metadata_info)
            records = _read_metadata(metadata)
            _validate_plan(stratified_plan, metadata, records)
            record_ids, reasons = _review_population(stratified_plan, human_plan, structural_contract)
            if any(record_id not in records for record_id in record_ids):
                raise ValueError("review population contains a record absent from metadata")

            assets = staging / "assets"
            assets.mkdir()
            manifest_rows = []
            for record_id in record_ids:
                source = records[record_id]
                record_dir = assets / record_id
                record_dir.mkdir()
                paths = {}
                for role, member_name, filename in (
                    ("image", source["image_member"], "image.png"),
                    ("mask", source["mask_member"], "mask.png"),
                ):
                    info = members.get(member_name)
                    if info is None:
                        raise ValueError(f"missing review asset: {member_name}")
                    payload = archive.read(info)
                    if len(payload) != info.file_size or not payload.startswith(PNG_SIGNATURE):
                        raise ValueError(f"invalid review PNG: {member_name}")
                    target = record_dir / filename
                    target.write_bytes(payload)
                    paths[role] = target.relative_to(staging).as_posix()
                manifest_rows.append({
                    **source,
                    "mandatory_reasons": reasons.get(record_id, []),
                    "image_path": paths["image"],
                    "mask_path": paths["mask"],
                    "review_status": "pending",
                })

        manifest = {
            "schema": "mmbu.busbra.human_review_packet_manifest.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "archive_bytes": ARCHIVE_BYTES,
            "archive_md5": ARCHIVE_MD5,
            "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
            "stratified_plan_digest": stratified_plan["plan_digest"],
            "human_review_plan_digest": _canonical_digest(human_plan),
            "structural_contract_digest": structural_contract["contract_digest"],
            "record_count": len(manifest_rows),
            "records": manifest_rows,
            "review_status": "pending_human_review",
            "review_complete": False,
            "training_ready": False,
            "model_use_authorized": False,
        }
        manifest["manifest_digest"] = _canonical_digest(manifest)
        _write_json(staging / "review-manifest.json", manifest)

        review_fields = [
            "record_id", "case_id", "pathology", "birads", "mandatory_reasons",
            "primary_reviewer_id", "primary_reviewed_at", "image_interpretable",
            "mask_usable", "additional_or_incomplete_lesion", "source_fields_joined",
            "shortcut_artifact", "permitted_tasks", "primary_disposition", "primary_notes",
            "secondary_reviewer_id", "secondary_reviewed_at", "secondary_disposition",
            "secondary_notes", "adjudicator_id", "adjudicated_at", "final_disposition",
        ]
        with (staging / "record-review-template.csv").open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=review_fields, lineterminator="\n")
            writer.writeheader()
            for row in manifest_rows:
                writer.writerow({
                    "record_id": row["record_id"],
                    "case_id": row["case_id"],
                    "pathology": row["pathology"],
                    "birads": row["birads"],
                    "mandatory_reasons": "|".join(row["mandatory_reasons"]),
                })

        source_review = {
            "schema": "mmbu.busbra.source_review_template.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "decision_status": "pending_human_review",
            "medical_review": {"primary_reviewer": None, "secondary_reviewer": None, "adjudicator": None},
            "provenance_review": {"reviewer": None, "case_110_536_disposition": None, "evidence_locator": None},
            "rights_and_release_review": {
                "reviewer": None,
                "training": None,
                "development": None,
                "untouched_confirmation": None,
                "public_weight_release": None,
                "challenge_submission": None,
                "attribution_text": None,
                "redistribution_conditions": None,
            },
            "review_complete": False,
            "training_ready": False,
            "model_use_authorized": False,
        }
        _write_json(staging / "source-review-template.json", source_review)
        (staging / "README.txt").write_text(
            "BUS-BRA HUMAN REVIEW PACKET\n\n"
            "This packet prepares frozen records for accountable human review. It grants no medical, rights, "
            "training, release, or model-use approval. Complete the record worksheet with qualified reviewers; "
            "complete the separate source/provenance/rights form; preserve evidence locators and dates; and then "
            "run a separately reviewed admission process. Do not edit review-manifest.json or packet-receipt.json.\n",
            encoding="utf-8",
        )

        member_paths = sorted(
            (path for path in staging.rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(staging).as_posix().encode("utf-8"),
        )
        receipt = {
            "schema": "mmbu.busbra.human_review_packet_receipt.v1",
            "source_id": "busbra",
            "source_version": "1.0",
            "manifest_digest": manifest["manifest_digest"],
            "record_count": len(manifest_rows),
            "members": [_file_entry(staging, path) for path in member_paths],
            "review_complete": False,
            "training_ready": False,
            "model_use_authorized": False,
            "limitations": [
                "Packet generation does not perform or validate medical review.",
                "Packet generation does not establish rights, provenance, release, or challenge eligibility.",
                "A completed worksheet is not itself a Phase 1 source-admission or purpose-authorization record.",
            ],
        }
        receipt["receipt_digest"] = _canonical_digest(receipt)
        _write_json(staging / "packet-receipt.json", receipt)
        _rename_no_replace(staging, output)
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--stratified-plan", type=Path, required=True)
    parser.add_argument("--human-plan", type=Path, required=True)
    parser.add_argument("--structural-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        receipt = build_review_packet(
            args.archive,
            _load_json(args.stratified_plan),
            _load_json(args.human_plan),
            _load_json(args.structural_contract),
            args.output,
        )
        print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, TypeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": str(exc)}), file=os.sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
