#!/usr/bin/env python3
"""Validate BUS-UCLM metadata and archive inventory without opening pixels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import sys
import unicodedata


ROOT = "BUS-UCLM Breast ultrasound lesion segmentation dataset/BUS-UCLM/"
METADATA_MEMBER = ROOT + "INFO.csv"
FIELDS = ["Image", "Resolution", "Label", "Doppler", "Marks", "Combined"]
IMAGE_PATTERN = re.compile(r"([A-Z]{4})_[0-9]{3}\.png")
INVENTORY_KEYS = {"name", "file_size", "compress_size", "crc32"}
ARCHIVE_BYTES = 336_713_241
ARCHIVE_ETAG = '"66fea5503ae433b324be1cbf54ca8866"'
ARCHIVE_LAST_MODIFIED = "Mon, 27 Jan 2025 12:36:20 GMT"
ARCHIVE_VERSION_ID = "OtNyHu6R84RS3_v.5.KA6bykStLQaxxw"


def _digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                         allow_nan=False).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def _read_metadata(payload):
    if not isinstance(payload, bytes) or not payload:
        raise ValueError("metadata must be nonempty bytes")
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("metadata must be UTF-8") from exc
    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=";")
    if reader.fieldnames != FIELDS:
        raise ValueError("metadata columns must exactly match BUS-UCLM INFO.csv")
    records = []
    seen = set()
    for line, raw in enumerate(reader, 2):
        if None in raw or any(not isinstance(raw[field], str) or not raw[field] for field in FIELDS):
            raise ValueError(f"metadata row {line} is incomplete")
        match = IMAGE_PATTERN.fullmatch(raw["Image"])
        if match is None or raw["Image"] in seen:
            raise ValueError("image names must be unique canonical BUS-UCLM PNG names")
        seen.add(raw["Image"])
        size = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", raw["Resolution"])
        if size is None:
            raise ValueError("resolution must be positive canonical WIDTHxHEIGHT")
        if raw["Label"] not in {"Normal", "Benign", "Malignant"}:
            raise ValueError("label is outside the published BUS-UCLM ontology")
        if raw["Doppler"] not in {"No", "Yes", "Y"}:
            raise ValueError("Doppler contains an unknown value")
        if raw["Marks"] not in {"No", "Yes"} or raw["Combined"] not in {"No", "Yes"}:
            raise ValueError("Marks and Combined must use canonical Yes/No values")
        records.append({
            "image": raw["Image"],
            "patient_id": match.group(1),
            "width": int(size.group(1)),
            "height": int(size.group(2)),
            "label": raw["Label"],
            "doppler": raw["Doppler"],
            "marks": raw["Marks"],
            "combined": raw["Combined"],
        })
    if not records:
        raise ValueError("metadata must contain records")
    return records


def _read_inventory(inventory):
    if not isinstance(inventory, list) or not inventory:
        raise ValueError("inventory must be a nonempty list")
    normalized = set()
    names = set()
    result = []
    for row in inventory:
        if not isinstance(row, dict) or set(row) != INVENTORY_KEYS:
            raise ValueError("inventory rows must be closed")
        name = row["name"]
        if not isinstance(name, str) or not name:
            raise ValueError("inventory name must be a nonempty string")
        path = PurePosixPath(name)
        canonical = unicodedata.normalize("NFC", name).casefold()
        if (path.is_absolute() or path.as_posix() != name or ".." in path.parts or
                "\\" in name or "\0" in name or ":" in name or
                name in names or canonical in normalized):
            raise ValueError("inventory contains an unsafe or duplicate member")
        for field in ("file_size", "compress_size"):
            if type(row[field]) is not int or row[field] < 0:
                raise ValueError("inventory sizes must be nonnegative integers")
        if not isinstance(row["crc32"], str) or re.fullmatch(r"[0-9a-f]{8}", row["crc32"]) is None:
            raise ValueError("inventory CRC32 must be lowercase hexadecimal")
        names.add(name)
        normalized.add(canonical)
        result.append(dict(row))
    return result


def audit_metadata(metadata_bytes: bytes, inventory: list[dict]) -> dict:
    """Return a closed metadata-only receipt; never authorize biomedical use."""
    records = _read_metadata(metadata_bytes)
    members = _read_inventory(inventory)
    names = {item["name"] for item in members}
    expected = {METADATA_MEMBER}
    expected.update(ROOT + "images/" + record["image"] for record in records)
    expected.update(ROOT + "masks/" + record["image"] for record in records)
    if names != expected:
        raise ValueError("archive inventory does not close against INFO.csv")

    label_counts = {}
    patient_labels = {}
    resolutions = {}
    feature_counts = {"combined_yes": 0, "doppler_yes_or_y": 0, "marks_yes": 0}
    for record in records:
        label_counts[record["label"]] = label_counts.get(record["label"], 0) + 1
        patient_labels.setdefault(record["patient_id"], set()).add(record["label"])
        resolution = f"{record['width']}x{record['height']}"
        resolutions[resolution] = resolutions.get(resolution, 0) + 1
        feature_counts["combined_yes"] += record["combined"] == "Yes"
        feature_counts["doppler_yes_or_y"] += record["doppler"] in {"Yes", "Y"}
        feature_counts["marks_yes"] += record["marks"] == "Yes"
    label_sets = {}
    for values in patient_labels.values():
        key = "|".join(sorted(values))
        label_sets[key] = label_sets.get(key, 0) + 1
    noncanonical = []
    doppler_y = sum(record["doppler"] == "Y" for record in records)
    if doppler_y:
        noncanonical.append({"column": "Doppler", "value": "Y", "count": doppler_y})

    receipt = {
        "schema": "mmbu.busuclm.metadata_gate_receipt.v1",
        "source_id": "bus-uclm",
        "source_version": "3",
        "source_doi": "10.17632/7fvgj4jsp7.3",
        "archive_bytes": ARCHIVE_BYTES,
        "archive_etag": ARCHIVE_ETAG,
        "archive_last_modified": ARCHIVE_LAST_MODIFIED,
        "archive_version_id": ARCHIVE_VERSION_ID,
        "metadata_member": METADATA_MEMBER,
        "metadata_bytes": len(metadata_bytes),
        "metadata_sha256": hashlib.sha256(metadata_bytes).hexdigest(),
        "inventory_digest": _digest(members),
        "inventory_member_count": len(members),
        "record_count": len(records),
        "patient_count": len(patient_labels),
        "label_counts": dict(sorted(label_counts.items())),
        "resolution_counts": dict(sorted(resolutions.items())),
        "patient_label_set_counts": dict(sorted(label_sets.items())),
        "feature_counts": feature_counts,
        "noncanonical_values": noncanonical,
        "inventory_clearance": True,
        "schema_clearance": not noncanonical,
        "patient_grouping_required": True,
        "license_authorities": {
            "mendeley_v3": "CC BY 4.0",
            "authors_repository_readme": "CC BY 4.0",
            "authors_repository_license_file": "CC BY-NC 4.0",
        },
        "license_disposition": "conflict_blocks_model_use",
        "biomedical_pixels_opened": False,
        "model_executed": False,
        "training_ready": False,
        "model_use_authorized": False,
        "limitations": [
            "Metadata and member-name closure do not establish pixel, mask, or medical correctness.",
            "Patient prefixes bind grouping but do not make image-level labels patient-level diagnoses.",
            "Conflicting first-party license statements require authoritative clarification.",
        ],
    }
    receipt["receipt_digest"] = _digest(receipt)
    return receipt


def _load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = audit_metadata(args.metadata.read_bytes(), _load_json(args.inventory))
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2, sort_keys=True, allow_nan=False)
            stream.write("\n")
        print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
