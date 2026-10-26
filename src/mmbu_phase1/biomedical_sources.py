"""Fail-closed compilers for authorized external biomedical experiment sources.

The compilers preserve source-provided targets and independent-unit boundaries.
They never inspect or derive anything from MMBU data.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import io
from pathlib import Path
import re
import struct
from typing import Any
import zipfile

from mmbu_phase1 import canonical
from mmbu_phase1.fields import (
    ContractViolation,
    array,
    closed,
    integer,
    literal,
    require,
    string_set,
    text,
)


BUSBRA_METADATA_COLUMNS = (
    "ID", "Case", "Histology", "Pathology", "BIRADS", "Device", "Width", "Height", "Side", "BBOX",
)
_DECLARATION_KEYS = (
    "archive_bytes",
    "archive_md5",
    "archive_sha256",
    "citation",
    "excluded_case_ids",
    "fold_member",
    "image_member_template",
    "license_member",
    "license_required_phrases",
    "metadata_member",
    "source_id",
    "source_version",
    "split_by_fold",
)
_MD5 = re.compile(r"[0-9a-f]{32}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_RECORD_ID = re.compile(r"bus_[0-9]{4}-(?:l|r|s)")
_PATHOLOGIES = {"benign", "malignant"}
_SIDES = {"left", "right", "single"}
_SPLITS = {"train", "development", "confirmation"}
_EXCLUDED_CASES = ["110", "536"]
_PATHMNIST_DECLARATION_KEYS = (
    "archive_bytes",
    "archive_md5",
    "citation",
    "download_url",
    "image_shape",
    "labels",
    "license_id",
    "sample_counts",
    "source_id",
    "source_version",
    "split_roles",
    "status",
)
_PATHMNIST_LABELS = [
    "adipose",
    "background",
    "debris",
    "lymphocytes",
    "mucus",
    "smooth muscle",
    "normal colon mucosa",
    "cancer-associated stroma",
    "colorectal adenocarcinoma epithelium",
]


def _hex(value: Any, path: str, pattern: re.Pattern[str]) -> str:
    value = text(value, path)
    require(pattern.fullmatch(value) is not None, path, "must be lowercase hexadecimal with the required length")
    return value


def validate_busbra_declaration(value: Any) -> dict:
    """Validate the immutable BUS-BRA experiment intake declaration."""
    value = closed(value, "busbra_declaration", _DECLARATION_KEYS)
    literal(value["source_id"], "busbra_declaration.source_id", "busbra")
    literal(value["source_version"], "busbra_declaration.source_version", "1.0")
    integer(value["archive_bytes"], "busbra_declaration.archive_bytes", minimum=1)
    _hex(value["archive_md5"], "busbra_declaration.archive_md5", _MD5)
    _hex(value["archive_sha256"], "busbra_declaration.archive_sha256", _SHA256)
    for key in ("citation", "fold_member", "image_member_template", "license_member", "metadata_member"):
        text(value[key], f"busbra_declaration.{key}")
    require(value["image_member_template"].count("{record_id}") == 1,
            "busbra_declaration.image_member_template", "must contain exactly one {record_id} placeholder")
    phrases = array(value["license_required_phrases"], "busbra_declaration.license_required_phrases", nonempty=True)
    for index, phrase in enumerate(phrases):
        text(phrase, f"busbra_declaration.license_required_phrases[{index}]")
    require(phrases == sorted(set(phrases), key=lambda item: item.encode("utf-8")),
            "busbra_declaration.license_required_phrases", "must be unique and sorted by UTF-8 bytes")
    string_set(value["excluded_case_ids"], "busbra_declaration.excluded_case_ids", nonempty=True)
    require(value["excluded_case_ids"] == _EXCLUDED_CASES,
            "busbra_declaration.excluded_case_ids", "must exclude the unresolved cases 110 and 536")
    folds = closed(value["split_by_fold"], "busbra_declaration.split_by_fold", ("1", "2", "3", "4", "5"))
    for key, split in folds.items():
        require(split in _SPLITS, f"busbra_declaration.split_by_fold.{key}", "unsupported split role")
    require([folds[str(index)] for index in range(1, 6)] ==
            ["train", "train", "train", "development", "confirmation"],
            "busbra_declaration.split_by_fold", "must preserve the frozen 3/1/1 fold roles")
    return value


def _csv_member(archive: zipfile.ZipFile, member: str, columns: tuple[str, ...], path: str) -> list[dict[str, str]]:
    try:
        raw = archive.read(member)
    except KeyError:
        raise ContractViolation(path, f"missing archive member {member!r}") from None
    try:
        stream = io.StringIO(raw.decode("utf-8-sig"), newline="")
    except UnicodeDecodeError:
        raise ContractViolation(path, "must be UTF-8 CSV") from None
    reader = csv.DictReader(stream)
    require(tuple(reader.fieldnames or ()) == columns, path, f"columns must be exactly {list(columns)!r}")
    rows = list(reader)
    require(bool(rows), path, "must contain at least one row")
    require(all(None not in row and all(value is not None for value in row.values()) for row in rows),
            path, "contains a malformed row")
    return rows


def _bbox(value: str, width: int, height: int, path: str) -> list[int]:
    try:
        parsed = ast.literal_eval(value)
    except (SyntaxError, ValueError):
        raise ContractViolation(path, "must be a literal [x,y,width,height] box") from None
    require(type(parsed) is list and len(parsed) == 4 and all(type(item) is int for item in parsed),
            path, "must be four JSON-compatible integers")
    x, y, box_width, box_height = parsed
    require(x >= 0 and y >= 0 and box_width > 0 and box_height > 0,
            path, "must have nonnegative origin and positive size")
    require(x + box_width <= width and y + box_height <= height, path, "must fit the declared image dimensions")
    return parsed


def compile_busbra(archive_path: str | Path, declaration: Any) -> dict:
    """Compile verified BUS-BRA metadata into patient-safe experiment rows."""
    declaration = validate_busbra_declaration(declaration)
    archive_path = Path(archive_path)
    require(archive_path.is_file(), "busbra_archive", "must be a regular file")
    raw = archive_path.read_bytes()
    require(len(raw) == declaration["archive_bytes"], "busbra_archive.bytes", "does not match declaration")
    require(hashlib.md5(raw).hexdigest() == declaration["archive_md5"],  # nosec: published dataset checksum
            "busbra_archive.md5", "does not match declaration")
    require(hashlib.sha256(raw).hexdigest() == declaration["archive_sha256"],
            "busbra_archive.sha256", "does not match declaration")

    try:
        archive = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile:
        raise ContractViolation("busbra_archive", "must be a valid ZIP file") from None
    with archive:
        names = set(archive.namelist())
        require(len(names) == len(archive.namelist()), "busbra_archive.members", "duplicate member names are forbidden")
        try:
            license_bytes = archive.read(declaration["license_member"])
            license_text = license_bytes.decode("utf-8")
        except KeyError:
            raise ContractViolation("busbra_archive.license", "license member is missing") from None
        except UnicodeDecodeError:
            raise ContractViolation("busbra_archive.license", "license must be UTF-8") from None
        for phrase in declaration["license_required_phrases"]:
            require(phrase in license_text, "busbra_archive.license", f"required phrase is absent: {phrase!r}")

        metadata = _csv_member(
            archive, declaration["metadata_member"], BUSBRA_METADATA_COLUMNS, "busbra_archive.metadata",
        )
        folds = _csv_member(
            archive, declaration["fold_member"],
            ("ID", "Pathology", "kFold", "valid_1", "valid_2", "valid_3", "valid_4", "valid_5"),
            "busbra_archive.folds",
        )
        metadata_by_id = {row["ID"]: row for row in metadata}
        folds_by_id = {row["ID"]: row for row in folds}
        require(len(metadata_by_id) == len(metadata), "busbra_archive.metadata.ID", "must be unique")
        require(len(folds_by_id) == len(folds), "busbra_archive.folds.ID", "must be unique")
        require(set(metadata_by_id) == set(folds_by_id), "busbra_archive.rows", "metadata and fold IDs must match exactly")

        rows = []
        case_fold: dict[str, str] = {}
        excluded_counts = {case_id: 0 for case_id in declaration["excluded_case_ids"]}
        for record_id in sorted(metadata_by_id, key=lambda item: item.encode("utf-8")):
            source = metadata_by_id[record_id]
            fold = folds_by_id[record_id]
            require(_RECORD_ID.fullmatch(record_id) is not None, f"busbra.rows.{record_id}.ID", "invalid record ID")
            pathology = source["Pathology"].strip().lower()
            require(pathology in _PATHOLOGIES, f"busbra.rows.{record_id}.Pathology", "unsupported source label")
            require(fold["Pathology"].strip().lower() == pathology,
                    f"busbra.rows.{record_id}.fold_pathology", "does not match metadata")
            fold_id = fold["kFold"].strip()
            require(fold_id in declaration["split_by_fold"], f"busbra.rows.{record_id}.kFold", "unsupported fold")
            for index in range(1, 6):
                expected = "NaN" if str(index) == fold_id else None
                observed = fold[f"valid_{index}"].strip()
                if expected is not None:
                    require(observed == expected, f"busbra.rows.{record_id}.valid_{index}",
                            "held-out fold must be NaN")
                else:
                    require(observed in {"0", "1"}, f"busbra.rows.{record_id}.valid_{index}",
                            "non-held-out fold flag must be binary")
            case_id = source["Case"].strip()
            require(case_id.isdecimal() and int(case_id) > 0, f"busbra.rows.{record_id}.Case", "invalid case ID")
            previous_fold = case_fold.setdefault(case_id, fold_id)
            require(previous_fold == fold_id, f"busbra.case.{case_id}", "patient records cross fold boundaries")
            image_member = declaration["image_member_template"].format(record_id=record_id)
            require(image_member in names, f"busbra.rows.{record_id}.image", "image member is missing")
            if case_id in excluded_counts:
                excluded_counts[case_id] += 1
                continue
            width = integer(int(source["Width"]), f"busbra.rows.{record_id}.Width", minimum=1)
            height = integer(int(source["Height"]), f"busbra.rows.{record_id}.Height", minimum=1)
            side = source["Side"].strip().lower()
            require(side in _SIDES, f"busbra.rows.{record_id}.Side", "unsupported side")
            birads = source["BIRADS"].strip()
            require(birads in {"2", "3", "4", "5"}, f"busbra.rows.{record_id}.BIRADS", "unsupported BI-RADS")
            context = {
                "bbox_xywh": _bbox(source["BBOX"], width, height, f"busbra.rows.{record_id}.BBOX"),
                "birads": birads,
                "image_size": [width, height],
                "side": side,
            }
            rows.append({
                "context_prompt": (
                    "Using only the ultrasound image, return compact JSON with keys bbox_xywh, birads, "
                    "image_size, and side."
                ),
                "context_target": context,
                "context_target_text": canonical.dumps(context).decode("utf-8"),
                "image_member": image_member,
                "independent_unit_id": f"busbra::case::{case_id}",
                "row_id": record_id,
                "source_id": "busbra",
                "split": declaration["split_by_fold"][fold_id],
                "task_prompt": (
                    "Classify the breast ultrasound finding as benign or malignant. Answer with one word."
                ),
                "task_target": pathology,
            })

    require(all(count > 0 for count in excluded_counts.values()), "busbra.exclusions",
            "every frozen excluded case must be present in the source")
    split_units = {split: set() for split in sorted(_SPLITS)}
    for row in rows:
        split_units[row["split"]].add(row["independent_unit_id"])
    for left in split_units:
        for right in split_units:
            if left < right:
                require(split_units[left].isdisjoint(split_units[right]), "busbra.splits", "patient overlap detected")
    receipt = {
        "archive_bytes": len(raw),
        "archive_md5": declaration["archive_md5"],
        "archive_sha256": declaration["archive_sha256"],
        "citation": declaration["citation"],
        "excluded_case_ids": declaration["excluded_case_ids"],
        "license_sha256": hashlib.sha256(license_bytes).hexdigest(),
        "mmbu_content_used": False,
        "row_count": len(rows),
        "rows_digest": canonical.value_digest(rows),
        "schema_id": "mmbu.biomedical.busbra_compilation_receipt",
        "schema_version": 1,
        "source_id": "busbra",
        "source_version": "1.0",
        "split_row_counts": {split: sum(row["split"] == split for row in rows) for split in sorted(_SPLITS)},
        "split_unit_counts": {split: len(split_units[split]) for split in sorted(_SPLITS)},
    }
    return {"receipt": receipt, "rows": rows}


def validate_pathmnist_declaration(value: Any) -> dict:
    """Validate the official PathMNIST-224 artifact and split declaration."""
    value = closed(value, "pathmnist_declaration", _PATHMNIST_DECLARATION_KEYS)
    literal(value["source_id"], "pathmnist_declaration.source_id", "pathmnist")
    literal(value["source_version"], "pathmnist_declaration.source_version", "3")
    literal(value["license_id"], "pathmnist_declaration.license_id", "CC-BY-4.0")
    require(value["status"] in {"acquisition_pending", "acquired_verified"},
            "pathmnist_declaration.status", "unsupported acquisition status")
    integer(value["archive_bytes"], "pathmnist_declaration.archive_bytes", minimum=1)
    _hex(value["archive_md5"], "pathmnist_declaration.archive_md5", _MD5)
    for key in ("citation", "download_url"):
        text(value[key], f"pathmnist_declaration.{key}")
    shape = array(value["image_shape"], "pathmnist_declaration.image_shape")
    require(len(shape) == 3, "pathmnist_declaration.image_shape", "must have height, width, channels")
    for index, dimension in enumerate(shape):
        integer(dimension, f"pathmnist_declaration.image_shape[{index}]", minimum=1)
    labels = array(value["labels"], "pathmnist_declaration.labels")
    require(labels == _PATHMNIST_LABELS, "pathmnist_declaration.labels", "must match official label order")
    counts = closed(value["sample_counts"], "pathmnist_declaration.sample_counts", ("test", "train", "val"))
    for split, count in counts.items():
        integer(count, f"pathmnist_declaration.sample_counts.{split}", minimum=1)
    roles = closed(value["split_roles"], "pathmnist_declaration.split_roles", ("test", "train", "val"))
    require(roles == {"test": "confirmation", "train": "train", "val": "development"},
            "pathmnist_declaration.split_roles", "must preserve the official external-center confirmation split")
    return value


def _hash_file(path: Path) -> tuple[int, str]:
    checksum = hashlib.md5()  # nosec: published dataset checksum
    total = 0
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(8 * 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            checksum.update(chunk)
    return total, checksum.hexdigest()


def _npy_header(stream: Any, path: str) -> tuple[str, tuple[int, ...], int]:
    require(stream.read(6) == b"\x93NUMPY", path, "invalid NPY magic")
    version = stream.read(2)
    require(version in {b"\x01\x00", b"\x02\x00", b"\x03\x00"}, path, "unsupported NPY version")
    width = 2 if version == b"\x01\x00" else 4
    raw_length = stream.read(width)
    require(len(raw_length) == width, path, "truncated NPY header length")
    header_length = struct.unpack("<H" if width == 2 else "<I", raw_length)[0]
    header_raw = stream.read(header_length)
    require(len(header_raw) == header_length, path, "truncated NPY header")
    try:
        header = ast.literal_eval(header_raw.decode("latin1").strip())
    except (SyntaxError, ValueError, UnicodeDecodeError):
        raise ContractViolation(path, "invalid NPY header") from None
    require(type(header) is dict and set(header) == {"descr", "fortran_order", "shape"},
            path, "NPY header must contain exactly descr, fortran_order, and shape")
    require(header["fortran_order"] is False, path, "Fortran-order arrays are unsupported")
    require(type(header["descr"]) is str, path, "invalid dtype descriptor")
    shape = header["shape"]
    require(type(shape) is tuple and shape and all(type(item) is int and item > 0 for item in shape),
            path, "invalid positive array shape")
    return header["descr"], shape, 6 + 2 + width + header_length


def compile_pathmnist(archive_path: str | Path, declaration: Any) -> dict:
    """Compile PathMNIST indexes and labels while leaving the large image payload in place."""
    declaration = validate_pathmnist_declaration(declaration)
    archive_path = Path(archive_path)
    require(archive_path.is_file(), "pathmnist_archive", "must be a regular file")
    byte_count, md5 = _hash_file(archive_path)
    require(byte_count == declaration["archive_bytes"], "pathmnist_archive.bytes", "does not match declaration")
    require(md5 == declaration["archive_md5"], "pathmnist_archive.md5", "does not match declaration")
    expected_members = {f"{split}_{kind}.npy" for split in ("train", "val", "test")
                        for kind in ("images", "labels")}
    try:
        archive = zipfile.ZipFile(archive_path)
    except zipfile.BadZipFile:
        raise ContractViolation("pathmnist_archive", "must be a valid NPZ/ZIP file") from None
    rows = []
    with archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names) == len(set(names)), "pathmnist_archive.members", "duplicate member names are forbidden")
        require(set(names) == expected_members, "pathmnist_archive.members", "must contain exactly six official arrays")
        by_name = {info.filename: info for info in infos}
        for split in ("test", "train", "val"):
            count = declaration["sample_counts"][split]
            image_name = f"{split}_images.npy"
            with archive.open(image_name) as stream:
                dtype, shape, offset = _npy_header(stream, f"pathmnist_archive.{image_name}")
            require(dtype == "|u1", f"pathmnist_archive.{image_name}.dtype", "must be uint8")
            require(shape == (count, *declaration["image_shape"]),
                    f"pathmnist_archive.{image_name}.shape", "does not match declaration")
            expected_image_bytes = count
            for dimension in declaration["image_shape"]:
                expected_image_bytes *= dimension
            require(by_name[image_name].file_size == offset + expected_image_bytes,
                    f"pathmnist_archive.{image_name}.bytes", "image payload length does not match shape")

            label_name = f"{split}_labels.npy"
            with archive.open(label_name) as stream:
                dtype, shape, offset = _npy_header(stream, f"pathmnist_archive.{label_name}")
                require(dtype == "|u1", f"pathmnist_archive.{label_name}.dtype", "must match official uint8 labels")
                require(shape == (count, 1), f"pathmnist_archive.{label_name}.shape", "does not match declaration")
                payload = stream.read()
            require(len(payload) == count and by_name[label_name].file_size == offset + len(payload),
                    f"pathmnist_archive.{label_name}.bytes", "label payload length does not match shape")
            labels = payload
            for index, label in enumerate(labels):
                require(0 <= label < len(declaration["labels"]),
                        f"pathmnist_archive.{label_name}[{index}]", "label is out of range")
                row_id = f"pathmnist::{split}::{index}"
                rows.append({
                    "context_prompt": None,
                    "context_target": None,
                    "context_target_text": None,
                    "image_array_key": f"{split}_images",
                    "image_index": index,
                    "independent_unit_id": row_id,
                    "row_id": row_id,
                    "source_id": "pathmnist",
                    "split": declaration["split_roles"][split],
                    "task_prompt": (
                        "Classify this colorectal histology patch as one of: adipose, background, debris, "
                        "lymphocytes, mucus, smooth muscle, normal colon mucosa, cancer-associated stroma, "
                        "or colorectal adenocarcinoma epithelium. Answer with the class name only."
                    ),
                    "task_target": declaration["labels"][label],
                })
    receipt = {
        "archive_bytes": byte_count,
        "archive_md5": md5,
        "citation": declaration["citation"],
        "image_shape": declaration["image_shape"],
        "license_id": declaration["license_id"],
        "mmbu_content_used": False,
        "row_count": len(rows),
        "rows_digest": canonical.value_digest(rows),
        "schema_id": "mmbu.biomedical.pathmnist_compilation_receipt",
        "schema_version": 1,
        "source_id": "pathmnist",
        "source_version": declaration["source_version"],
        "split_row_counts": {
            role: sum(row["split"] == role for row in rows)
            for role in ("confirmation", "development", "train")
        },
    }
    return {"receipt": receipt, "rows": rows}


__all__ = [
    "BUSBRA_METADATA_COLUMNS",
    "ContractViolation",
    "compile_busbra",
    "compile_pathmnist",
    "validate_busbra_declaration",
    "validate_pathmnist_declaration",
]
