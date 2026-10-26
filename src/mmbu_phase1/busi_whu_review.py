"""Fail-closed BUSI-WHU clinical-review selection mechanics."""

from __future__ import annotations

import csv
from contextlib import ExitStack
import ctypes
import errno
import hashlib
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import struct
import sys
import tempfile
import unicodedata
import zipfile

from . import canonical
from .busi_whu_authority import ReviewOpeningCapability
from .image_fingerprints import build_duplicate_candidates, dhash64
from .protected_io import open_authorized_artifact


_INVENTORY_KEYS = {
    "annotation_member_join_complete", "annotation_payload_decoding_used", "artifact_name",
    "image_member_join_complete", "image_payload_decoding_used", "label_counts", "label_values_read",
    "mmbu_public_content_used", "model_use_authorized", "patient_count", "record_count",
    "record_digest", "records", "schema_id", "schema_version", "sheet_name",
}
_RECORD_KEYS = {"label_code", "parent_id", "record_id", "row_digest", "workbook_row", "workbook_geometry"}
_WORKBOOK_GEOMETRY_KEYS = {
    "scale_pixel_per_cm", "scale_category", "gt_area_pixel2", "image_area_pixel2", "gt_cm2", "gt_all",
    "centroid_x", "centroid_y", "max_diameter", "min_diameter",
}
_SELECTION_KEYS = {
    "mandatory_multi_record_count", "mandatory_multi_record_patient_count",
    "mmbu_public_content_used", "model_use_authorized", "population_digest",
    "primary_patient_count", "primary_patient_ids", "primary_record_count", "primary_record_ids",
    "record_digest", "schema_id", "schema_version", "secondary_patient_count",
    "secondary_patient_ids", "secondary_record_count", "secondary_record_ids",
    "selected_singleton_patient_counts", "selected_singleton_patient_ids", "selection_rule",
    "singleton_patient_counts", "source_admission_authorized", "source_inventory_digest",
    "training_ready",
}
_REVIEW_FIELDS = (
    "record_id", "parent_id", "label_code", "canonical_target", "workbook_row", "image_path", "annotation_path",
    "decoded_width", "decoded_height", "annotation_bbox_xywh", "reviewer_id", "reviewed_at",
    "image_interpretable", "ultrasound_modality_supported", "breast_anatomy_supported",
    "annotation_usable", "label_plausible", "intended_lesion_supported",
    "grounded_target_complete", "localization_target_complete", "additional_lesion_risk",
    "shortcut_artifact", "disposition", "notes", "permitted_tasks",
)


def _closed(value: object, keys: set[str], path: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{path} must contain exactly {sorted(keys)}")
    return value


def _ranking(patient_id: str) -> tuple[bytes, bytes]:
    encoded = patient_id.encode("utf-8")
    return hashlib.sha256(b"busi-whu-review-v1\0" + encoded).digest(), encoded


def _workbook_geometry(value: object, path: str) -> dict:
    row = _closed(value, _WORKBOOK_GEOMETRY_KEYS, path)
    if not isinstance(row["scale_category"], str) or not row["scale_category"]:
        raise ValueError(f"{path}.scale_category must be nonblank text")
    for name in _WORKBOOK_GEOMETRY_KEYS - {"scale_category"}:
        if type(row[name]) not in {int, float}:
            raise ValueError(f"{path}.{name} must be a finite non-boolean number")
    if row["scale_pixel_per_cm"] <= 0 or row["image_area_pixel2"] <= 0 or row["gt_area_pixel2"] < 0:
        raise ValueError(f"{path} contains invalid nonpositive geometry")
    return row


def build_review_selection(metadata_inventory: object) -> dict:
    """Freeze full primary review and the enriched independent second review."""
    inventory = _closed(metadata_inventory, _INVENTORY_KEYS, "metadata_inventory")
    if canonical.record_digest(inventory) != inventory["record_digest"]:
        raise ValueError("metadata_inventory digest mismatch")
    expected = {
        "schema_id": "mmbu.phase1.busi_whu_patient_join_inventory",
        "schema_version": 1,
        "artifact_name": "Patient_infos_BUSI-WHU.xlsx",
        "sheet_name": "Sheet1",
        "record_count": 927,
        "patient_count": 816,
        "label_counts": {"0": 560, "1": 367},
        "image_member_join_complete": True,
        "annotation_member_join_complete": True,
        "label_values_read": True,
        "image_payload_decoding_used": False,
        "annotation_payload_decoding_used": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    }
    for key, value in expected.items():
        if inventory[key] != value:
            raise ValueError(f"metadata_inventory.{key} differs from the frozen contract")
    records = inventory["records"]
    if type(records) is not list or len(records) != 927:
        raise ValueError("metadata_inventory.records must contain exactly 927 rows")

    normalized = []
    by_patient: dict[str, list[dict]] = {}
    record_ids: set[str] = set()
    for index, value in enumerate(records):
        row = _closed(value, _RECORD_KEYS, f"metadata_inventory.records[{index}]")
        _workbook_geometry(row["workbook_geometry"], f"metadata_inventory.records[{index}].workbook_geometry")
        if row["label_code"] not in {"0", "1"}:
            raise ValueError("record label_code must be 0 or 1")
        if not isinstance(row["record_id"], str) or not row["record_id"] or row["record_id"] in record_ids:
            raise ValueError("record_id must be a unique nonempty string")
        if not isinstance(row["parent_id"], str) or not row["parent_id"].startswith("busi-whu:patient:"):
            raise ValueError("parent_id must use the BUSI-WHU patient namespace")
        if not isinstance(row["row_digest"], str) or len(row["row_digest"]) != 64:
            raise ValueError("row_digest must be SHA-256 shaped")
        if isinstance(row["workbook_row"], bool) or not isinstance(row["workbook_row"], int) or row["workbook_row"] < 2:
            raise ValueError("workbook_row must be a positive data-row index")
        record_ids.add(row["record_id"])
        normalized.append(dict(row))
        by_patient.setdefault(row["parent_id"], []).append(row)
    if len(by_patient) != 816:
        raise ValueError("metadata inventory must contain exactly 816 patient groups")
    normalized.sort(key=lambda row: row["record_id"].encode("utf-8"))

    multi_patients: list[str] = []
    singleton_by_label = {"0": [], "1": []}
    for patient_id, patient_rows in by_patient.items():
        labels = {row["label_code"] for row in patient_rows}
        if len(labels) != 1:
            raise ValueError("one patient cannot carry conflicting labels")
        if len(patient_rows) > 1:
            multi_patients.append(patient_id)
        else:
            singleton_by_label[next(iter(labels))].append(patient_id)
    if len(multi_patients) != 38 or sum(len(by_patient[value]) for value in multi_patients) != 149:
        raise ValueError("multi-record patient population differs from the frozen contract")
    if {key: len(value) for key, value in singleton_by_label.items()} != {"0": 560, "1": 218}:
        raise ValueError("singleton patient population differs from the frozen contract")

    selected_singletons = {
        label: sorted(sorted(values, key=_ranking)[:50])
        for label, values in singleton_by_label.items()
    }
    selected_singleton_ids = sorted(selected_singletons["0"] + selected_singletons["1"])
    secondary_patients = sorted(multi_patients + selected_singleton_ids)
    secondary_patient_set = set(secondary_patients)
    secondary_records = sorted(
        row["record_id"] for row in normalized if row["parent_id"] in secondary_patient_set
    )
    population_digest = canonical.value_digest(normalized)
    return canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_review_selection",
        "schema_version": 1,
        "source_inventory_digest": inventory["record_digest"],
        "population_digest": population_digest,
        "selection_rule": "all-multi-record-patients-plus-hash-ranked-50-singletons-per-label-v1",
        "primary_record_ids": sorted(record_ids),
        "primary_patient_ids": sorted(by_patient),
        "primary_record_count": 927,
        "primary_patient_count": 816,
        "secondary_record_ids": secondary_records,
        "secondary_patient_ids": secondary_patients,
        "secondary_record_count": 249,
        "secondary_patient_count": 138,
        "mandatory_multi_record_count": 149,
        "mandatory_multi_record_patient_count": 38,
        "singleton_patient_counts": {"0": 560, "1": 218},
        "selected_singleton_patient_ids": selected_singleton_ids,
        "selected_singleton_patient_counts": {"0": 50, "1": 50},
        "source_admission_authorized": False,
        "training_ready": False,
        "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def _safe_archive_members(archive: zipfile.ZipFile, expected_ids: set[str]) -> dict[str, zipfile.ZipInfo]:
    members: dict[str, zipfile.ZipInfo] = {}
    aliases: set[str] = set()
    total = 0
    expected = {"img/", "gt/"}
    expected.update(f"img/{record_id}.bmp" for record_id in expected_ids)
    expected.update(f"gt/{record_id}_anno.bmp" for record_id in expected_ids)
    for info in archive.infolist():
        name = info.filename
        path = PurePosixPath(name)
        alias = unicodedata.normalize("NFC", name).casefold()
        canonical_name = path.as_posix() + ("/" if info.is_dir() else "")
        if (
            not name or path.is_absolute() or ".." in path.parts or "." in path.parts
            or "\\" in name or "\0" in name or name != canonical_name
            or name in members or alias in aliases
        ):
            raise ValueError("archive contains an unsafe or duplicate member")
        if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError("archive contains an encrypted or linked member")
        if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
            raise ValueError("archive member uses an unsupported compression method")
        aliases.add(alias)
        members[name] = info
        if not info.is_dir():
            if info.file_size < 54 or info.file_size > 50_000_000:
                raise ValueError("archive BMP member violates the byte ceiling")
            total += info.file_size
    if set(members) != expected:
        raise ValueError("archive members differ from the frozen image/annotation closure")
    if total > 1_000_000_000:
        raise ValueError("archive exceeds the full-corpus byte ceiling")
    return members


def _decode_bmp(payload: bytes, *, annotation: bool) -> dict:
    """Strictly decode an uncompressed 8-bit or 24-bit Windows BMP."""
    if len(payload) < 54 or payload[:2] != b"BM":
        raise ValueError("asset is not a closed Windows BMP")
    declared_size, reserved1, reserved2, pixel_offset = struct.unpack_from("<IHHI", payload, 2)
    if declared_size != len(payload) or reserved1 != 0 or reserved2 != 0:
        raise ValueError("BMP file header is inconsistent")
    dib_size = struct.unpack_from("<I", payload, 14)[0]
    if dib_size < 40 or 14 + dib_size > pixel_offset or 14 + dib_size > len(payload):
        raise ValueError("BMP DIB header is unsupported")
    width, signed_height, planes, bits, compression, image_size = struct.unpack_from(
        "<iiHHII", payload, 18
    )
    colors_used = struct.unpack_from("<I", payload, 46)[0]
    if width < 1 or signed_height == 0 or planes != 1 or bits not in {8, 24} or compression != 0:
        raise ValueError("BMP representation is unsupported")
    height = abs(signed_height)
    if width * height > 4_000_000:
        raise ValueError("BMP exceeds the decoded-pixel ceiling")
    stride = ((width * bits + 31) // 32) * 4
    required = stride * height
    if image_size not in {0, required} or pixel_offset + required != len(payload):
        raise ValueError("BMP pixel extent is inconsistent")

    palette = None
    if bits == 8:
        palette_count = colors_used or 256
        if not 1 <= palette_count <= 256 or 14 + dib_size + 4 * palette_count > pixel_offset:
            raise ValueError("BMP palette is inconsistent")
        palette = []
        for index in range(palette_count):
            blue, green, red, reserved = struct.unpack_from(
                "<BBBB", payload, 14 + dib_size + 4 * index
            )
            if reserved != 0:
                raise ValueError("BMP palette contains ambiguous alpha data")
            palette.append((red, green, blue))

    rgb = bytearray()
    foreground_left = width
    foreground_top = height
    foreground_right = -1
    foreground_bottom = -1
    foreground_count = 0
    foreground_x_sum = 0
    foreground_y_sum = 0
    for logical_y in range(height):
        stored_y = logical_y if signed_height < 0 else height - 1 - logical_y
        start = pixel_offset + stored_y * stride
        if bits == 8:
            row = []
            for index in payload[start:start + width]:
                if index >= len(palette):
                    raise ValueError("BMP pixel indexes outside its palette")
                row.append(palette[index])
        else:
            row = []
            for x in range(width):
                blue, green, red = struct.unpack_from("<BBB", payload, start + 3 * x)
                row.append((red, green, blue))
        for x, (red, green, blue) in enumerate(row):
            rgb.extend((red, green, blue))
            if annotation:
                if red != green or green != blue or red not in {0, 255}:
                    raise ValueError("annotation pixels must be exactly binary 0/255")
                if red == 255:
                    foreground_count += 1
                    foreground_x_sum += x
                    foreground_y_sum += logical_y
                    foreground_left = min(foreground_left, x)
                    foreground_top = min(foreground_top, logical_y)
                    foreground_right = max(foreground_right, x)
                    foreground_bottom = max(foreground_bottom, logical_y)

    bbox = None
    if annotation:
        if foreground_right < 0:
            raise ValueError("annotation contains no foreground")
        bbox = [
            foreground_left,
            foreground_top,
            foreground_right - foreground_left + 1,
            foreground_bottom - foreground_top + 1,
        ]
    grayscale_rows = []
    for y_index in range(8):
        y = min(height - 1, y_index * height // 8)
        grayscale_row = []
        for x_index in range(9):
            x = min(width - 1, x_index * width // 9)
            offset = 3 * (y * width + x)
            red, green, blue = rgb[offset:offset + 3]
            grayscale_row.append((299 * red + 587 * green + 114 * blue + 500) // 1000)
        grayscale_rows.append(grayscale_row)
    decoded = struct.pack("<II", width, height) + bytes(rgb)
    return {
        "width": width,
        "height": height,
        "decoded_sha256": hashlib.sha256(decoded).hexdigest(),
        "perceptual_hash": f"{dhash64(grayscale_rows):016x}",
        "bbox_xywh": bbox,
        "foreground_area": foreground_count if annotation else None,
        "foreground_centroid": (
            [foreground_x_sum / foreground_count, foreground_y_sum / foreground_count]
            if annotation else None
        ),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_bytes(canonical.dumps(value))


def _file_entry(root: Path, path: Path) -> dict:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _rename_no_replace(source: Path, destination: Path) -> None:
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    if sys.platform == "darwin":
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renamex_np
        rename.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        rename.restype = ctypes.c_int
        result = rename(source_bytes, destination_bytes, 0x00000004)
    elif sys.platform.startswith("linux"):
        libc = ctypes.CDLL(None, use_errno=True)
        if not hasattr(libc, "renameat2"):
            raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
        rename = libc.renameat2
        rename.argtypes = (
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
        )
        rename.restype = ctypes.c_int
        result = rename(-100, source_bytes, -100, destination_bytes, 1)
    else:
        raise OSError(errno.ENOTSUP, "atomic no-replace rename is unavailable")
    if result != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(destination))


def _write_review_csv(path: Path, records: list[dict]) -> None:
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=_REVIEW_FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in records:
            writer.writerow({
                "record_id": row["record_id"],
                "parent_id": row["parent_id"],
                "label_code": row["label_code"],
                "workbook_row": row["workbook_row"],
                "image_path": row["image_path"],
                "annotation_path": row["annotation_path"],
                "decoded_width": row["decoded_width"],
                "decoded_height": row["decoded_height"],
                "annotation_bbox_xywh": canonical.dumps(row["annotation_bbox_xywh"]).decode("ascii"),
                "canonical_target": row["canonical_target"],
            })


def _geometry_evidence(workbook: dict, image: dict, annotation: dict) -> tuple[dict, str]:
    derived = {
        "gt_area_pixel2": annotation["foreground_area"],
        "image_area_pixel2": image["width"] * image["height"],
        "gt_cm2": annotation["foreground_area"] / (workbook["scale_pixel_per_cm"] ** 2),
        "gt_all": annotation["foreground_area"] / (image["width"] * image["height"]),
        "centroid_x": annotation["foreground_centroid"][0],
        "centroid_y": annotation["foreground_centroid"][1],
    }
    evidence = {}
    unresolved = False
    for name, observed in derived.items():
        expected = workbook[name]
        disposition = "consistent" if canonical.exact(expected) == canonical.exact(observed) else "unresolved"
        evidence[name] = {"workbook": expected, "derived": observed, "disposition": disposition}
        unresolved = unresolved or disposition == "unresolved"
    for name in ("max_diameter", "min_diameter"):
        evidence[name] = {
            "workbook": workbook[name], "derived": None, "disposition": "not_directly_recomputed",
        }
    return evidence, "unresolved" if unresolved else "consistent"


def build_review_packet(
    capability: ReviewOpeningCapability,
    metadata_inventory: dict,
    selection: dict,
    source_fingerprint_inventories: dict,
) -> dict:
    """Decode the closed corpus and atomically publish a pending review packet."""
    inventory = _closed(metadata_inventory, _INVENTORY_KEYS, "metadata_inventory")
    chosen = _closed(selection, _SELECTION_KEYS, "selection")
    if inventory["record_digest"] != capability.metadata_inventory_digest:
        raise ValueError("metadata inventory differs from the opening authorization")
    if chosen["record_digest"] != capability.review_selection_digest:
        raise ValueError("review selection differs from the opening authorization")
    if chosen != build_review_selection(inventory):
        raise ValueError("selection differs from the recomputed frozen review selection")
    supplied_inventory_digests = {
        row.get("inventory_digest") for row in source_fingerprint_inventories.get("inventories", [])
        if type(row) is dict
    }
    if supplied_inventory_digests != set(capability.fingerprint_inventory_digests):
        raise ValueError("fingerprint inventory closure differs from the opening authorization")
    if type(capability) is not ReviewOpeningCapability:
        raise ValueError("a validated BUSI-WHU review-opening capability is required")
    output = Path(capability.output_root)
    if output.exists():
        raise FileExistsError(str(output))
    archive_rows = [row for row in capability.artifact_bindings if row[1] == "archive"]
    workbook_rows = [row for row in capability.artifact_bindings if row[1] == "metadata"]
    if len(archive_rows) != 1 or len(workbook_rows) != 1:
        raise ValueError("capability must bind exactly one archive and one metadata workbook")
    output.parent.mkdir(parents=True, exist_ok=True)
    attempt = output.parent / f".{output.name}.attempt-{capability.authorization_digest}"
    attempt_payload = canonical.dumps(canonical.seal({
        "schema_id": "mmbu.phase1.busi_whu_review_attempt",
        "schema_version": 1,
        "authorization_digest": capability.authorization_digest,
        "opening_receipt_digest": capability.opening_receipt_digest,
        "output_root": str(output),
    }))
    try:
        attempt_fd = os.open(
            attempt, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0), 0o600,
        )
    except FileExistsError:
        raise FileExistsError(f"review attempt already consumed: {attempt}") from None
    try:
        view = memoryview(attempt_payload)
        while view:
            view = view[os.write(attempt_fd, view):]
        os.fsync(attempt_fd)
    finally:
        os.close(attempt_fd)
    directory_flag = getattr(os, "O_DIRECTORY", 0)
    if type(directory_flag) is not int or directory_flag == 0:
        raise RuntimeError("durable attempt publication requires O_DIRECTORY")
    attempt_parent_fd = os.open(
        output.parent, os.O_RDONLY | directory_flag | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        os.fsync(attempt_parent_fd)
    finally:
        os.close(attempt_parent_fd)
    staging = Path(tempfile.mkdtemp(prefix=".busi-whu-review-", dir=output.parent))
    resources = ExitStack()
    try:
        archive_artifact = resources.enter_context(
            open_authorized_artifact(capability, archive_rows[0][0], "archive")
        )
        workbook_artifact = resources.enter_context(
            open_authorized_artifact(capability, workbook_rows[0][0], "metadata")
        )
        archive_stream = resources.enter_context(archive_artifact.stream())
        source_rows = {row["record_id"]: row for row in inventory["records"]}
        decoded_rows = []
        image_hashes: dict[str, list[str]] = {}
        perceptual_hashes: dict[str, list[str]] = {}
        assets = staging / "assets"
        assets.mkdir()
        with zipfile.ZipFile(archive_stream) as archive:
            members = _safe_archive_members(archive, set(source_rows))
            for record_id in sorted(source_rows, key=lambda value: value.encode("utf-8")):
                source = source_rows[record_id]
                image_member = f"img/{record_id}.bmp"
                annotation_member = f"gt/{record_id}_anno.bmp"
                image_payload = archive.read(members[image_member])
                annotation_payload = archive.read(members[annotation_member])
                if len(image_payload) != members[image_member].file_size or len(annotation_payload) != members[annotation_member].file_size:
                    raise ValueError("archive member read was incomplete")
                image = _decode_bmp(image_payload, annotation=False)
                annotation = _decode_bmp(annotation_payload, annotation=True)
                if (image["width"], image["height"]) != (annotation["width"], annotation["height"]):
                    raise ValueError(f"image and annotation dimensions differ for {record_id}")
                record_dir = assets / record_id
                record_dir.mkdir()
                image_path = record_dir / "image.bmp"
                annotation_path = record_dir / "annotation.bmp"
                image_path.write_bytes(image_payload)
                annotation_path.write_bytes(annotation_payload)
                image_hashes.setdefault(image["decoded_sha256"], []).append(record_id)
                perceptual_hashes.setdefault(image["perceptual_hash"], []).append(record_id)
                geometry_evidence, geometry_disposition = _geometry_evidence(
                    source["workbook_geometry"], image, annotation,
                )
                decoded_rows.append({
                    **source,
                    "canonical_target": {"0": "benign", "1": "malignant"}[source["label_code"]],
                    "image_member": image_member,
                    "annotation_member": annotation_member,
                    "image_path": image_path.relative_to(staging).as_posix(),
                    "annotation_path": annotation_path.relative_to(staging).as_posix(),
                    "image_file_sha256": hashlib.sha256(image_payload).hexdigest(),
                    "annotation_file_sha256": hashlib.sha256(annotation_payload).hexdigest(),
                    "image_decoded_sha256": image["decoded_sha256"],
                    "image_perceptual_hash": image["perceptual_hash"],
                    "annotation_decoded_sha256": annotation["decoded_sha256"],
                    "decoded_width": image["width"],
                    "decoded_height": image["height"],
                    "annotation_bbox_xywh": annotation["bbox_xywh"],
                    "geometry_evidence": geometry_evidence,
                    "geometry_consistency_disposition": geometry_disposition,
                    "review_status": "pending",
                })

        record_targets = {
            row["record_id"]: row["canonical_target"]
            for row in sorted(decoded_rows, key=lambda row: row["record_id"].encode("utf-8"))
        }
        target_manifest = canonical.seal({
            "schema_id": "mmbu.phase1.busi_whu_target_manifest",
            "schema_version": 1,
            "source_inventory_digest": inventory["record_digest"],
            "record_targets": record_targets,
            "record_count": len(record_targets),
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })
        _write_json(staging / "target-manifest.json", target_manifest)

        decode_inventory = canonical.seal({
            "schema_id": "mmbu.phase1.busi_whu_decode_inventory",
            "schema_version": 1,
            "source_inventory_digest": inventory["record_digest"],
            "selection_digest": chosen["record_digest"],
            "target_map_digest": target_manifest["record_digest"],
            "record_targets": record_targets,
            "archive_sha256": archive_artifact.sha256,
            "workbook_sha256": workbook_artifact.sha256,
            "opening_authorization_digest": capability.authorization_digest,
            "opening_receipt_digest": capability.opening_receipt_digest,
            "records": decoded_rows,
            "record_count": len(decoded_rows),
            "decoded_image_count": len(decoded_rows),
            "decoded_annotation_count": len(decoded_rows),
            "image_annotation_dimension_match_complete": True,
            "binary_nonempty_annotation_check_complete": True,
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })
        _write_json(staging / "decode-inventory.json", decode_inventory)

        def duplicate_group(digest_name: str, digest: str, record_ids: list[str]) -> dict:
            patient_ids = sorted({source_rows[value]["parent_id"] for value in record_ids})
            return {
                digest_name: digest,
                "record_ids": sorted(record_ids),
                "patient_ids": patient_ids,
                "cross_patient": len(patient_ids) > 1,
                "disposition": "pending_independent_review",
            }

        duplicate_groups = [
            duplicate_group("decoded_image_sha256", digest, record_ids)
            for digest, record_ids in sorted(image_hashes.items()) if len(record_ids) > 1
        ]
        perceptual_groups = [
            duplicate_group("perceptual_hash", digest, record_ids)
            for digest, record_ids in sorted(perceptual_hashes.items()) if len(record_ids) > 1
        ]
        fingerprint_rows = [
            {"source_id": "busi-whu", "source_version": "3", "record_id": row["record_id"],
             "decoded_sha256": row["image_decoded_sha256"], "dhash64": row["image_perceptual_hash"],
             "width": row["decoded_width"], "height": row["decoded_height"]}
            for row in decoded_rows
        ]
        cross_source_candidates = build_duplicate_candidates(
            fingerprint_rows, source_fingerprint_inventories, include_within_source=False,
        )
        duplicates = canonical.seal({
            "schema_id": "mmbu.phase1.busi_whu_duplicate_candidates",
            "schema_version": 1,
            "decode_inventory_digest": decode_inventory["record_digest"],
            "exact_image_groups": duplicate_groups,
            "perceptual_image_groups": perceptual_groups,
            "cross_source_candidates": cross_source_candidates,
            "source_fingerprint_inventory_digests": sorted(supplied_inventory_digests),
            "exact_duplicate_record_count": sum(len(row["record_ids"]) for row in duplicate_groups),
            "cross_patient_exact_group_count": sum(row["cross_patient"] for row in duplicate_groups),
            "cross_patient_perceptual_group_count": sum(row["cross_patient"] for row in perceptual_groups),
            "human_disposition_required": bool(
                duplicate_groups or perceptual_groups or cross_source_candidates
            ),
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })
        _write_json(staging / "duplicate-candidates.json", duplicates)

        all_record_ids = sorted(row["record_id"] for row in decoded_rows)
        geometry_blocked_ids = sorted(
            row["record_id"] for row in decoded_rows
            if row["geometry_consistency_disposition"] != "consistent"
        )
        task_manifest_digests = {}
        for task in (
            "context_prediction", "global_classification", "grounded_classification", "localization",
        ):
            blocked = geometry_blocked_ids if task in {"grounded_classification", "localization"} else []
            blocked_set = set(blocked)
            task_manifest = canonical.seal({
                "schema_id": "mmbu.phase1.busi_whu_mechanical_task_manifest",
                "schema_version": 1,
                "task": task,
                "target_map_digest": target_manifest["record_digest"],
                "decode_inventory_digest": decode_inventory["record_digest"],
                "mechanically_candidate_record_ids": [
                    record_id for record_id in all_record_ids if record_id not in blocked_set
                ],
                "mechanically_blocked_record_ids": blocked,
                "eligibility_status": "pending_human_review",
                "source_admission_authorized": False,
                "training_ready": False,
                "model_use_authorized": False,
                "mmbu_public_content_used": False,
            })
            _write_json(staging / f"task-manifest-{task}.json", task_manifest)
            task_manifest_digests[task] = task_manifest["record_digest"]

        manifest = canonical.seal({
            "schema_id": "mmbu.phase1.busi_whu_review_packet_manifest",
            "schema_version": 1,
            "source_inventory_digest": inventory["record_digest"],
            "selection_digest": chosen["record_digest"],
            "target_map_digest": target_manifest["record_digest"],
            "decode_inventory_digest": decode_inventory["record_digest"],
            "duplicate_candidates_digest": duplicates["record_digest"],
            "mechanical_task_manifest_digests": task_manifest_digests,
            "record_count": len(decoded_rows),
            "primary_record_count": len(decoded_rows),
            "secondary_record_count": chosen["secondary_record_count"],
            "review_status": "pending_human_review",
            "review_complete": False,
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })
        _write_json(staging / "review-manifest.json", manifest)
        _write_review_csv(staging / "primary-review.csv", decoded_rows)
        secondary = [row for row in decoded_rows if row["record_id"] in set(chosen["secondary_record_ids"])]
        _write_review_csv(staging / "secondary-review.csv", secondary)
        _write_json(staging / "adjudication-template.json", {
            "schema_id": "mmbu.phase1.busi_whu_adjudication_template",
            "schema_version": 1,
            "review_manifest_digest": manifest["record_digest"],
            "adjudicator_id": None,
            "reviewed_at": None,
            "disagreements": [],
            "review_complete": False,
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })
        (staging / "README.txt").write_text(
            "BUSI-WHU PROTECTED CLINICAL REVIEW PACKET\n\n"
            "This immutable packet prepares the closed confirmation corpus for independent human review. "
            "It grants no source admission, training, model-use, release, or submission authority. Complete "
            "copies of the worksheets outside this directory and validate them separately.\n",
            encoding="utf-8",
        )
        files = sorted(
            (path for path in staging.rglob("*") if path.is_file()),
            key=lambda path: path.relative_to(staging).as_posix().encode("utf-8"),
        )
        receipt = canonical.seal({
            "schema_id": "mmbu.phase1.busi_whu_review_packet_receipt",
            "schema_version": 1,
            "opening_authorization_digest": capability.authorization_digest,
            "opening_receipt_digest": capability.opening_receipt_digest,
            "manifest_digest": manifest["record_digest"],
            "target_map_digest": target_manifest["record_digest"],
            "decode_inventory_digest": decode_inventory["record_digest"],
            "duplicate_candidates_digest": duplicates["record_digest"],
            "members": [_file_entry(staging, path) for path in files],
            "record_count": len(decoded_rows),
            "review_complete": False,
            "source_admission_authorized": False,
            "training_ready": False,
            "model_use_authorized": False,
            "mmbu_public_content_used": False,
        })
        _write_json(staging / "packet-receipt.json", receipt)
        _rename_no_replace(staging, output)
        return receipt
    finally:
        resources.close()
        if staging.exists():
            shutil.rmtree(staging)


__all__ = ["build_review_packet", "build_review_selection"]
