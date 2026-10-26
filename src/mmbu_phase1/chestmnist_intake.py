"""Strict, metadata-only intake checks for the public ChestMNIST mapping."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import defaultdict
from typing import Mapping


SCHEMA_ID = "mmbu.phase1.chestmnist_mapping_audit"
SCHEMA_VERSION = 1
SPLITS = ("train", "val", "test")
IMAGE_ID = re.compile(r"[0-9]{8}_[0-9]{3}\Z")


def _expected_counts(value: Mapping[str, int]) -> dict[str, int]:
    if not isinstance(value, Mapping) or set(value) != set(SPLITS):
        raise ValueError("expected split counts must contain exactly train, val, and test")
    result: dict[str, int] = {}
    for split in SPLITS:
        count = value[split]
        if type(count) is not int or count < 0:
            raise ValueError(f"expected {split} count must be a nonnegative integer")
        result[split] = count
    return result


def audit_mapping_bytes(
    raw: bytes,
    *,
    expected_split_counts: Mapping[str, int],
    expected_patient_count: int | None = None,
) -> dict:
    """Validate exact mapping bytes and return a bounded non-admission summary."""
    if not isinstance(raw, bytes):
        raise TypeError("mapping input must be exact bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("UTF-8 BOM is forbidden")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"mapping is not valid UTF-8: {exc}") from None
    counts_expected = _expected_counts(expected_split_counts)
    if expected_patient_count is not None and (
        type(expected_patient_count) is not int or expected_patient_count < 0
    ):
        raise ValueError("expected patient count must be a nonnegative integer or null")

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("mapping is empty") from None
    except csv.Error as exc:
        raise ValueError(f"invalid CSV header: {exc}") from None
    if header != ["split", "index", "image_id"]:
        raise ValueError("mapping header must be exactly split,index,image_id")

    indices: dict[str, list[int]] = {split: [] for split in SPLITS}
    patient_splits: dict[str, set[str]] = defaultdict(set)
    image_ids: set[str] = set()
    patients_by_split: dict[str, set[str]] = {split: set() for split in SPLITS}
    row_count = 0
    try:
        for line_number, row in enumerate(reader, start=2):
            if len(row) != 3:
                raise ValueError(f"line {line_number} must contain exactly three fields")
            split, index_text, image_id = row
            if split not in indices:
                raise ValueError(f"line {line_number} has unknown split {split!r}")
            try:
                index = int(index_text)
            except ValueError:
                raise ValueError(f"line {line_number} has a non-integer index") from None
            if index < 0 or str(index) != index_text:
                raise ValueError(f"line {line_number} has a noncanonical index")
            if IMAGE_ID.fullmatch(image_id) is None:
                raise ValueError(f"line {line_number} has an invalid ChestX-ray14 image ID")
            if image_id in image_ids:
                raise ValueError(f"line {line_number} repeats image ID {image_id}")
            image_ids.add(image_id)
            indices[split].append(index)
            patient_id = image_id[:8]
            patient_splits[patient_id].add(split)
            patients_by_split[split].add(patient_id)
            row_count += 1
    except csv.Error as exc:
        raise ValueError(f"invalid CSV body: {exc}") from None

    observed_counts = {split: len(indices[split]) for split in SPLITS}
    if observed_counts != counts_expected:
        raise ValueError(f"split counts differ: expected {counts_expected}, observed {observed_counts}")
    for split in SPLITS:
        if indices[split] != list(range(counts_expected[split])):
            raise ValueError(f"{split} indices must be ordered and contiguous from zero")

    patient_count = len(patient_splits)
    if expected_patient_count is not None and patient_count != expected_patient_count:
        raise ValueError(
            f"patient count differs: expected {expected_patient_count}, observed {patient_count}"
        )
    crossing = sorted(patient for patient, splits in patient_splits.items() if len(splits) > 1)
    memberships = {patient: sorted(patient_splits[patient]) for patient in crossing}
    disjoint = not crossing
    return {
        "schema_id": SCHEMA_ID,
        "schema_version": SCHEMA_VERSION,
        "mapping_bytes": len(raw),
        "mapping_sha256": hashlib.sha256(raw).hexdigest(),
        "row_count": row_count,
        "split_counts": {split: observed_counts[split] for split in SPLITS},
        "patient_count": patient_count,
        "patient_counts_by_split": {
            split: len(patients_by_split[split]) for split in SPLITS
        },
        "cross_split_patient_count": len(crossing),
        "cross_split_patient_ids": crossing,
        "cross_split_patient_memberships": memberships,
        "official_split_patient_disjoint": disjoint,
        "development_rebuild_required": not disjoint,
        "test_mapping_metadata_read": counts_expected["test"] > 0,
        "labels_opened": False,
        "pixels_opened": False,
        "test_labels_opened": False,
        "test_images_opened": False,
        "source_admitted": False,
        "mmbu_public_content_used": False,
    }
