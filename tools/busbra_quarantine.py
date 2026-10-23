#!/usr/bin/env python3
"""Plan and inspect local BUS-BRA quarantine data; never grant model use."""

from __future__ import annotations

import csv
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import unicodedata
import zipfile


FIELDS = ("ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX")
ID_PATTERN = re.compile(r"bus_([0-9]{4})-([lrs])")
PLAN_SCHEMA = "mmbu.busbra.quarantine_sample_plan.v1"
SELECTION_ALGORITHM = "rarest-pathology-birads-stratum-then-record-id-case-exclusive-v1"
ARCHIVE_BYTES = 133_917_740
ARCHIVE_MD5 = "1f8b2be6476d58fc97bfb5e5a1ea9bab"
PLAN_KEYS = {
    "schema", "source_id", "source_version", "metadata_member", "metadata_sha256",
    "selection_algorithm", "per_stratum", "records", "selected_case_count",
    "biomedical_pixels_opened", "model_executed", "model_use_authorized", "plan_digest",
}
RECORD_KEYS = {
    "record_id", "case_id", "pathology", "birads", "width", "height", "bbox_xywh",
    "image_member", "mask_member",
}


def _canonical_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                         allow_nan=False).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _positive_integer(value, name):
    if not isinstance(value, str) or not value.isdigit() or int(value) < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def _bbox(value, width, height):
    try:
        box = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ValueError("BBOX must be a JSON xywh array") from exc
    if (not isinstance(box, list) or len(box) != 4 or
            any(type(item) is not int for item in box)):
        raise ValueError("BBOX must contain four integers")
    x, y, w, h = box
    if x < 0 or y < 0 or w < 1 or h < 1 or x + w > width or y + h > height:
        raise ValueError("BBOX is not positive and in bounds")
    return box


def _read_metadata(payload):
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("metadata must be nonempty bytes")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("metadata must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != list(FIELDS):
        raise ValueError("metadata columns must exactly match BUS-BRA bus_data.csv")
    records = []
    seen_ids = set()
    case_claims = {}
    for line, raw in enumerate(reader, 2):
        if None in raw or any(not isinstance(raw[name], str) or raw[name] == "" for name in FIELDS):
            raise ValueError(f"metadata row {line} is incomplete")
        match = ID_PATTERN.fullmatch(raw["ID"])
        if not match or raw["ID"] in seen_ids:
            raise ValueError("record IDs must be unique canonical BUS-BRA IDs")
        seen_ids.add(raw["ID"])
        case_number = _positive_integer(raw["Case"], "Case")
        if int(match.group(1)) != case_number:
            raise ValueError("record ID and Case disagree")
        width = _positive_integer(raw["Width"], "Width")
        height = _positive_integer(raw["Height"], "Height")
        box = _bbox(raw["BBOX"], width, height)
        claim = (raw["Histology"], raw["Pathology"], raw["Device"])
        if case_number in case_claims and case_claims[case_number] != claim:
            raise ValueError("records in one Case disagree on patient-level claims")
        case_claims[case_number] = claim
        suffix = raw["ID"][4:]
        records.append({
            "record_id": raw["ID"],
            "case_id": str(case_number),
            "pathology": raw["Pathology"],
            "birads": raw["BIRADS"],
            "width": width,
            "height": height,
            "bbox_xywh": box,
            "image_member": f"BUSBRA/Images/{raw['ID']}.png",
            "mask_member": f"BUSBRA/Masks/mask_{suffix}.png",
        })
    if not records:
        raise ValueError("metadata must contain at least one record")
    return records


def build_sample_plan(metadata_bytes: bytes, *, per_stratum: int = 1) -> dict:
    """Freeze a patient-exclusive sample using metadata only.

    Rare strata allocate their cases first so a multi-view patient cannot make a
    rarer stratum disappear after a more common stratum consumes that patient.
    """
    if type(per_stratum) is not int or not 1 <= per_stratum <= 100:
        raise ValueError("per_stratum must be an integer in [1,100]")
    records = _read_metadata(metadata_bytes)
    strata = {}
    for record in records:
        strata.setdefault((record["pathology"], record["birads"]), []).append(record)
    order = sorted(strata, key=lambda key: (len({x["case_id"] for x in strata[key]}), key))
    used_cases = set()
    selected = []
    for key in order:
        chosen = 0
        for record in sorted(strata[key], key=lambda item: item["record_id"]):
            if record["case_id"] in used_cases:
                continue
            used_cases.add(record["case_id"])
            selected.append(record)
            chosen += 1
            if chosen == per_stratum:
                break
    selected.sort(key=lambda item: (item["pathology"], item["birads"], item["record_id"]))
    plan = {
        "schema": PLAN_SCHEMA,
        "source_id": "busbra",
        "source_version": "1.0",
        "metadata_member": "BUSBRA/bus_data.csv",
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "selection_algorithm": SELECTION_ALGORITHM,
        "per_stratum": per_stratum,
        "records": selected,
        "selected_case_count": len(used_cases),
        "biomedical_pixels_opened": False,
        "model_executed": False,
        "model_use_authorized": False,
    }
    plan["plan_digest"] = _canonical_digest(plan)
    return plan


def _validate_plan(plan):
    if not isinstance(plan, dict) or set(plan) != PLAN_KEYS:
        raise ValueError("plan must be a closed BUS-BRA sample plan")
    if plan["schema"] != PLAN_SCHEMA or plan["source_id"] != "busbra" or plan["source_version"] != "1.0":
        raise ValueError("plan identifies a different source or schema")
    if plan["metadata_member"] != "BUSBRA/bus_data.csv" or plan["selection_algorithm"] != SELECTION_ALGORITHM:
        raise ValueError("plan uses an unknown metadata member or selection algorithm")
    if any(plan[name] is not False for name in ("biomedical_pixels_opened", "model_executed", "model_use_authorized")):
        raise ValueError("plan may not claim pixel access, model execution, or model-use authority")
    if not isinstance(plan["records"], list) or not plan["records"]:
        raise ValueError("plan must select at least one record")
    if any(not isinstance(row, dict) or set(row) != RECORD_KEYS for row in plan["records"]):
        raise ValueError("plan records must be closed")
    unsigned = dict(plan)
    digest = unsigned.pop("plan_digest")
    if not isinstance(digest, str) or digest != _canonical_digest(unsigned):
        raise ValueError("plan digest mismatch")


def _safe_archive(archive):
    names = set()
    normalized = set()
    total = 0
    infos = {}
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        canonical = unicodedata.normalize("NFC", name).casefold()
        normalized_path = path.as_posix() + ("/" if info.is_dir() else "")
        if (not name or path.is_absolute() or normalized_path != name or ".." in path.parts or
                "\\" in name or "\0" in name or ":" in name or name in names or canonical in normalized):
            raise ValueError("archive contains an unsafe or duplicate member")
        names.add(name)
        normalized.add(canonical)
        if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError("archive contains an encrypted or linked member")
        if not info.is_dir():
            if info.file_size > 20_000_000:
                raise ValueError("archive member exceeds the quarantine size ceiling")
            total += info.file_size
            infos[name] = info
        if len(names) > 5_000 or total > 500_000_000:
            raise ValueError("archive exceeds quarantine inventory ceilings")
    return infos


def _read_member(archive, infos, name, *, maximum):
    info = infos.get(name)
    if info is None or info.file_size > maximum:
        raise ValueError("selected archive member is absent or exceeds its size ceiling")
    payload = archive.read(info)
    if len(payload) != info.file_size:
        raise ValueError("selected archive member length mismatch")
    return payload


def _decoded_digest(mode, width, height, payload):
    prefix = f"mmbu-decoded-pixels-v1\0{mode}\0{width}x{height}\0".encode("ascii")
    return hashlib.sha256(prefix + payload).hexdigest()


def _decode_image(payload, expected_size=None):
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("Pillow is required for BUS-BRA structural inspection") from exc
    try:
        with Image.open(io.BytesIO(payload), formats=("PNG",)) as image:
            if image.format != "PNG" or getattr(image, "n_frames", 1) != 1:
                raise ValueError("selected image must be a single-frame PNG")
            if image.width * image.height > 40_000_000:
                raise ValueError("selected image exceeds the decoded-pixel ceiling")
            if expected_size is not None and image.size != expected_size:
                raise ValueError("selected image dimensions disagree with frozen metadata")
            if image.mode not in ("L", "RGB") or "transparency" in image.info:
                raise ValueError("selected image has an unsupported or ambiguous representation")
            image.verify()
        with Image.open(io.BytesIO(payload), formats=("PNG",)) as image:
            orientation = image.getexif().get(274)
            if orientation not in (None, 1):
                raise ValueError("selected image requires an undeclared orientation transform")
            image.load()
            pixels = image.tobytes()
            return {
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
                "raw_sha256": hashlib.sha256(payload).hexdigest(),
                "pixel_sha256": _decoded_digest(image.mode, image.width, image.height, pixels),
            }
    except OSError as exc:
        raise ValueError("selected image is not a valid PNG") from exc


def _decode_mask(payload, expected_size=None):
    try:
        from PIL import Image
    except ImportError as exc:
        raise ValueError("Pillow is required for BUS-BRA structural inspection") from exc
    try:
        with Image.open(io.BytesIO(payload), formats=("PNG",)) as mask:
            if mask.format != "PNG" or getattr(mask, "n_frames", 1) != 1:
                raise ValueError("selected mask must be a same-size single-frame PNG")
            if mask.width * mask.height > 40_000_000:
                raise ValueError("selected mask exceeds the decoded-pixel ceiling")
            if expected_size is not None and mask.size != expected_size:
                raise ValueError("selected mask must be a same-size single-frame PNG")
            if mask.mode not in ("1", "L") or "transparency" in mask.info:
                raise ValueError("selected mask must be an unambiguous single-channel image")
            mask.verify()
        with Image.open(io.BytesIO(payload), formats=("PNG",)) as mask:
            mask.load()
            gray = mask.convert("L") if mask.mode == "1" else mask
            histogram = gray.histogram()
            values = [value for value, count in enumerate(histogram) if count]
            if not values or any(value not in (0, 255) for value in values):
                raise ValueError("selected mask values must be exactly binary 0/255")
            bounds = gray.getbbox()
            if bounds is None:
                raise ValueError("selected mask has no annotated foreground")
            left, top, right, bottom = bounds
            box = [left, top, right - left, bottom - top]
            pixels = gray.tobytes()
            return {
                "mode": mask.mode,
                "width": mask.width,
                "height": mask.height,
                "raw_sha256": hashlib.sha256(payload).hexdigest(),
                "pixel_sha256": _decoded_digest("L", mask.width, mask.height, pixels),
                "values": values,
                "bbox_xywh": box,
                "foreground_pixels": histogram[255],
            }
    except OSError as exc:
        raise ValueError("selected mask is not a valid PNG") from exc


def _box_iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    left, top = max(ax, bx), max(ay, by)
    right, bottom = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    intersection = max(0, right - left) * max(0, bottom - top)
    union = aw * ah + bw * bh - intersection
    return intersection / union


def _archive_identity(archive_path, expected_archive_bytes, expected_archive_md5):
    if type(expected_archive_bytes) is not int or expected_archive_bytes < 1:
        raise ValueError("expected archive byte count must be positive")
    if (not isinstance(expected_archive_md5, str) or
            re.fullmatch(r"[0-9a-f]{32}", expected_archive_md5) is None):
        raise ValueError("expected archive MD5 must be lowercase hexadecimal")
    archive_path = Path(archive_path).resolve(strict=True)
    stream = archive_path.open("rb")
    try:
        digest = hashlib.md5()
        archive_bytes = 0
        while chunk := stream.read(1_048_576):
            digest.update(chunk)
            archive_bytes += len(chunk)
        if archive_bytes != expected_archive_bytes or digest.hexdigest() != expected_archive_md5:
            raise ValueError("archive identity differs from the pinned source")
        stream.seek(0)
        return stream, archive_bytes
    except Exception:
        stream.close()
        raise


def _collision_groups(records, digest_key):
    by_digest = {}
    for record in records:
        by_digest.setdefault(record[digest_key], []).append(record)
    groups = []
    for members in by_digest.values():
        if len(members) < 2:
            continue
        record_ids = sorted(item["record_id"] for item in members)
        case_ids = sorted({item["case_id"] for item in members}, key=lambda item: int(item))
        groups.append({
            "record_ids": record_ids,
            "case_ids": case_ids,
            "cross_case": len(case_ids) > 1,
            "pathologies": sorted({item["pathology"] for item in members}),
        })
    return sorted(groups, key=lambda item: item["record_ids"])


def audit_corpus(archive_path: Path, output: Path, *,
                 expected_archive_bytes: int = ARCHIVE_BYTES,
                 expected_archive_md5: str = ARCHIVE_MD5) -> dict:
    """Decode every metadata-bound pair and publish an aggregate quarantine receipt."""
    output = Path(output)
    if output.exists():
        raise FileExistsError(str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".busbra-corpus-", dir=output.parent))
    try:
        archive_stream, archive_bytes = _archive_identity(
            archive_path, expected_archive_bytes, expected_archive_md5)
        with archive_stream:
            with zipfile.ZipFile(archive_stream) as archive:
                infos = _safe_archive(archive)
                metadata = _read_member(archive, infos, "BUSBRA/bus_data.csv", maximum=1_000_000)
                source_records = _read_metadata(metadata)
                expected_images = {item["image_member"] for item in source_records}
                expected_masks = {item["mask_member"] for item in source_records}
                actual_images = {name for name in infos if name.startswith("BUSBRA/Images/")}
                actual_masks = {name for name in infos if name.startswith("BUSBRA/Masks/")}
                if actual_images != expected_images or actual_masks != expected_masks:
                    raise ValueError("archive pixel inventory differs from metadata")

                decoded = []
                image_modes = {}
                mask_modes = {}
                dimension_mismatches = []
                for source in source_records:
                    declared_size = (source["width"], source["height"])
                    image = _decode_image(
                        _read_member(archive, infos, source["image_member"], maximum=20_000_000))
                    mask = _decode_mask(
                        _read_member(archive, infos, source["mask_member"], maximum=20_000_000),
                        (image["width"], image["height"]))
                    actual_size = (image["width"], image["height"])
                    if actual_size != declared_size:
                        dimension_mismatches.append({
                            "record_id": source["record_id"],
                            "declared_width": declared_size[0],
                            "declared_height": declared_size[1],
                            "actual_width": actual_size[0],
                            "actual_height": actual_size[1],
                        })
                    x, y, width, height = source["bbox_xywh"]
                    if x + width > actual_size[0] or y + height > actual_size[1]:
                        raise ValueError("metadata BBOX exceeds decoded image dimensions")
                    image_modes[image["mode"]] = image_modes.get(image["mode"], 0) + 1
                    mask_modes[mask["mode"]] = mask_modes.get(mask["mode"], 0) + 1
                    decoded.append({
                        "record_id": source["record_id"],
                        "case_id": source["case_id"],
                        "pathology": source["pathology"],
                        "birads": source["birads"],
                        "image_raw_sha256": image["raw_sha256"],
                        "image_pixel_sha256": image["pixel_sha256"],
                        "mask_raw_sha256": mask["raw_sha256"],
                        "mask_pixel_sha256": mask["pixel_sha256"],
                        "metadata_bbox_xywh": source["bbox_xywh"],
                        "mask_bbox_xywh": mask["bbox_xywh"],
                        "bbox_iou": _box_iou(source["bbox_xywh"], mask["bbox_xywh"]),
                    })

        image_groups = _collision_groups(decoded, "image_pixel_sha256")
        mask_groups = _collision_groups(decoded, "mask_pixel_sha256")
        ious = [item["bbox_iou"] for item in decoded]
        pathology_counts = {}
        birads_counts = {}
        for item in decoded:
            pathology_counts[item["pathology"]] = pathology_counts.get(item["pathology"], 0) + 1
            birads_counts[item["birads"]] = birads_counts.get(item["birads"], 0) + 1
        receipt = {
            "schema": "mmbu.busbra.quarantine_corpus_audit_receipt.v1",
            "ok": True,
            "source_id": "busbra",
            "source_version": "1.0",
            "archive_bytes": archive_bytes,
            "archive_md5": expected_archive_md5,
            "metadata_sha256": hashlib.sha256(metadata).hexdigest(),
            "record_count": len(decoded),
            "case_count": len({item["case_id"] for item in decoded}),
            "pathology_counts": dict(sorted(pathology_counts.items())),
            "birads_counts": dict(sorted(birads_counts.items())),
            "image_mode_counts": dict(sorted(image_modes.items())),
            "mask_mode_counts": dict(sorted(mask_modes.items())),
            "metadata_dimension_mismatches": dimension_mismatches,
            "metadata_dimension_clearance": not dimension_mismatches,
            "bbox_iou_min": min(ious),
            "bbox_iou_max": max(ious),
            "bbox_iou_below_0_95": sum(value < 0.95 for value in ious),
            "bbox_iou_below_0_95_records": [{
                "record_id": item["record_id"],
                "metadata_bbox_xywh": item["metadata_bbox_xywh"],
                "mask_bbox_xywh": item["mask_bbox_xywh"],
                "bbox_iou": item["bbox_iou"],
            } for item in decoded if item["bbox_iou"] < 0.95],
            "exact_image_duplicate_groups": image_groups,
            "exact_mask_duplicate_groups": mask_groups,
            "exact_image_duplicate_clearance": not image_groups,
            "exact_mask_duplicate_clearance": not mask_groups,
            "structural_clearance": (not dimension_mismatches and min(ious) >= 0.95 and
                                     not image_groups and not mask_groups),
            "near_duplicate_clearance": False,
            "medical_correctness_reviewed": False,
            "source_proximity_reviewed": False,
            "model_executed": False,
            "training_ready": False,
            "model_use_authorized": False,
            "limitations": [
                "Exact decoded equality does not establish near-duplicate or patient-identity clearance.",
                "Geometry agreement does not establish clinical correctness or annotation completeness.",
                "This receipt grants no training, evaluation, selection, release, or submission purpose.",
            ],
        }
        receipt["receipt_digest"] = _canonical_digest(receipt)
        (staging / "receipt.json").write_text(
            json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        if output.exists():
            raise FileExistsError(str(output))
        staging.rename(output)
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def inspect_quarantine(archive_path: Path, plan: dict, output: Path, *,
                       expected_archive_bytes: int = ARCHIVE_BYTES,
                       expected_archive_md5: str = ARCHIVE_MD5) -> dict:
    """Inspect only a frozen local sample and atomically publish a closed receipt."""
    _validate_plan(plan)
    output = Path(output)
    if output.exists():
        raise FileExistsError(str(output))
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".busbra-intake-", dir=output.parent))
    try:
        archive_stream, archive_bytes = _archive_identity(
            archive_path, expected_archive_bytes, expected_archive_md5)
        with archive_stream:
            with zipfile.ZipFile(archive_stream) as archive:
                infos = _safe_archive(archive)
                metadata = _read_member(archive, infos, plan["metadata_member"], maximum=1_000_000)
                if hashlib.sha256(metadata).hexdigest() != plan["metadata_sha256"]:
                    raise ValueError("metadata differs from the frozen sample plan")
                rebuilt = build_sample_plan(metadata, per_stratum=plan["per_stratum"])
                if rebuilt != plan:
                    raise ValueError("plan is not the deterministic expansion of archive metadata")
                records = []
                for selected in plan["records"]:
                    image_payload = _read_member(archive, infos, selected["image_member"], maximum=20_000_000)
                    mask_payload = _read_member(archive, infos, selected["mask_member"], maximum=20_000_000)
                    expected_size = (selected["width"], selected["height"])
                    image = _decode_image(image_payload, expected_size)
                    mask = _decode_mask(mask_payload, expected_size)
                    records.append({
                        "record_id": selected["record_id"],
                        "case_id": selected["case_id"],
                        "image_member": selected["image_member"],
                        "mask_member": selected["mask_member"],
                        "image_raw_sha256": image["raw_sha256"],
                        "image_pixel_sha256": image["pixel_sha256"],
                        "image_mode": image["mode"],
                        "mask_raw_sha256": mask["raw_sha256"],
                        "mask_pixel_sha256": mask["pixel_sha256"],
                        "mask_mode": mask["mode"],
                        "mask_values": mask["values"],
                        "mask_foreground_pixels": mask["foreground_pixels"],
                        "metadata_bbox_xywh": selected["bbox_xywh"],
                        "mask_bbox_xywh": mask["bbox_xywh"],
                        "bbox_iou": _box_iou(selected["bbox_xywh"], mask["bbox_xywh"]),
                    })
        by_pixels = {}
        for record in records:
            by_pixels.setdefault(record["image_pixel_sha256"], []).append(record["record_id"])
        duplicate_groups = sorted(sorted(ids) for ids in by_pixels.values() if len(ids) > 1)
        receipt = {
            "schema": "mmbu.busbra.quarantine_inspection_receipt.v1",
            "ok": True,
            "source_id": "busbra",
            "source_version": "1.0",
            "archive_bytes": archive_bytes,
            "archive_md5": expected_archive_md5,
            "sample_plan_digest": plan["plan_digest"],
            "selected_records": len(records),
            "records": records,
            "exact_decoded_duplicate_groups": duplicate_groups,
            "corpus_duplicate_clearance": False,
            "medical_correctness_reviewed": False,
            "source_proximity_reviewed": False,
            "model_executed": False,
            "training_ready": False,
            "model_use_authorized": False,
            "limitations": [
                "A deterministic sample is not a corpus-wide duplicate audit.",
                "Geometry agreement does not establish clinical correctness or annotation completeness.",
                "This receipt grants no training, evaluation, selection, release, or submission purpose.",
            ],
        }
        receipt["receipt_digest"] = _canonical_digest(receipt)
        (staging / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
                                               encoding="utf-8")
        if output.exists():
            raise FileExistsError(str(output))
        staging.rename(output)
        return receipt
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def _load_json(path):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value
    return json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON: {value}")))


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="Freeze a metadata-only sample")
    plan.add_argument("metadata", type=Path)
    plan.add_argument("--per-stratum", type=int, default=1)
    plan.add_argument("--output", type=Path, required=True)
    inspect = commands.add_parser("inspect", help="Inspect a frozen sample in a local archive")
    inspect.add_argument("archive", type=Path)
    inspect.add_argument("plan", type=Path)
    inspect.add_argument("--output", type=Path, required=True)
    inspect.add_argument("--expected-archive-bytes", type=int, default=ARCHIVE_BYTES,
                         help="Pinned source size; override only for synthetic conformance tests")
    inspect.add_argument("--expected-archive-md5", default=ARCHIVE_MD5,
                         help="Pinned source MD5; override only for synthetic conformance tests")
    audit = commands.add_parser("audit-corpus", help="Structurally audit every pair in a local archive")
    audit.add_argument("archive", type=Path)
    audit.add_argument("--output", type=Path, required=True)
    audit.add_argument("--expected-archive-bytes", type=int, default=ARCHIVE_BYTES,
                       help="Pinned source size; override only for synthetic conformance tests")
    audit.add_argument("--expected-archive-md5", default=ARCHIVE_MD5,
                       help="Pinned source MD5; override only for synthetic conformance tests")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            result = build_sample_plan(args.metadata.read_bytes(), per_stratum=args.per_stratum)
            with args.output.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
                stream.write("\n")
        elif args.command == "inspect":
            result = inspect_quarantine(args.archive, _load_json(args.plan), args.output,
                                        expected_archive_bytes=args.expected_archive_bytes,
                                        expected_archive_md5=args.expected_archive_md5)
        else:
            result = audit_corpus(args.archive, args.output,
                                  expected_archive_bytes=args.expected_archive_bytes,
                                  expected_archive_md5=args.expected_archive_md5)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": str(exc), "command": args.command}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
