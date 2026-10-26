"""Strict, metadata-only intake checks for the public ChestMNIST mapping."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from collections import defaultdict
from typing import Mapping

from . import canonical


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


def _official_ids(raw: bytes, label: str) -> set[str]:
    if not isinstance(raw, bytes) or raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError(f"{label} must be exact UTF-8 bytes without BOM")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{label} is not valid UTF-8: {exc}") from None
    result: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not re.fullmatch(r"[0-9]{8}_[0-9]{3}\.png", line):
            raise ValueError(f"{label} line {line_number} has an invalid filename")
        image_id = line[:-4]
        if image_id in result:
            raise ValueError(f"{label} repeats image ID {image_id}")
        result.add(image_id)
    if not result:
        raise ValueError(f"{label} is empty")
    return result


def reconcile_official_split_bytes(mapping_raw: bytes, train_val_raw: bytes, test_raw: bytes) -> dict:
    """Compare wrapper roles with the NIH-published patient-level split lists."""
    try:
        text = mapping_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"mapping is not valid UTF-8: {exc}") from None
    if mapping_raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("mapping UTF-8 BOM is forbidden")
    reader = csv.DictReader(io.StringIO(text, newline=""), strict=True)
    if reader.fieldnames != ["split", "index", "image_id"]:
        raise ValueError("mapping header must be exactly split,index,image_id")
    wrapper: dict[str, set[str]] = {split: set() for split in SPLITS}
    seen: set[str] = set()
    for row in reader:
        if set(row) != {"split", "index", "image_id"} or row["split"] not in wrapper:
            raise ValueError("mapping row is outside the closed schema")
        if IMAGE_ID.fullmatch(row["image_id"]) is None or row["image_id"] in seen:
            raise ValueError("mapping contains an invalid or duplicate image ID")
        seen.add(row["image_id"])
        wrapper[row["split"]].add(row["image_id"])

    official_train = _official_ids(train_val_raw, "official train/validation list")
    official_test = _official_ids(test_raw, "official test list")
    if official_train & official_test:
        raise ValueError("official split lists overlap")
    mapping_ids = set.union(*wrapper.values())
    if mapping_ids != official_train | official_test:
        raise ValueError("official split lists do not cover the mapping universe exactly")
    train_patients = {image[:8] for image in official_train}
    test_patients = {image[:8] for image in official_test}
    if train_patients & test_patients:
        raise ValueError("official split lists are not patient-disjoint")

    matrix = {
        split: {
            "official_test": len(wrapper[split] & official_test),
            "official_train_val": len(wrapper[split] & official_train),
        }
        for split in SPLITS
    }
    preserves = (
        matrix["train"]["official_test"] == 0
        and matrix["val"]["official_test"] == 0
        and matrix["test"]["official_train_val"] == 0
    )
    return {
        "schema_id": "mmbu.phase1.chestmnist_official_split_reconciliation",
        "schema_version": 1,
        "official_train_val_bytes": len(train_val_raw),
        "official_train_val_sha256": hashlib.sha256(train_val_raw).hexdigest(),
        "official_test_bytes": len(test_raw),
        "official_test_sha256": hashlib.sha256(test_raw).hexdigest(),
        "official_split_counts": {"train_val": len(official_train), "test": len(official_test)},
        "official_patient_counts": {"train_val": len(train_patients), "test": len(test_patients)},
        "official_split_patient_disjoint": True,
        "mapping_universe_matches_official_lists": True,
        "wrapper_by_official_split": matrix,
        "wrapper_roles_preserve_official_split": preserves,
        "labels_opened": False,
        "pixels_opened": False,
        "source_admitted": False,
        "mmbu_public_content_used": False,
    }


def compile_official_development_manifest(
    mapping_raw: bytes,
    train_val_raw: bytes,
    test_raw: bytes,
    patient_roles_raw: bytes,
) -> dict:
    """Compile frozen train/development records without admitting NIH test patients.

    The caller chooses patient roles in a separate frozen CSV. This function does
    not choose ratios or inspect labels; it only proves exact population closure
    and translates scientific roles to the wrapper array locations required to
    retrieve the corresponding images later.
    """
    reconciliation = reconcile_official_split_bytes(mapping_raw, train_val_raw, test_raw)
    official_train = _official_ids(train_val_raw, "official train/validation list")
    official_test = _official_ids(test_raw, "official test list")

    if not isinstance(patient_roles_raw, bytes) or patient_roles_raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("patient roles must be exact UTF-8 bytes without BOM")
    try:
        roles_text = patient_roles_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"patient roles are not valid UTF-8: {exc}") from None
    roles_reader = csv.reader(io.StringIO(roles_text, newline=""), strict=True)
    try:
        roles_header = next(roles_reader)
    except StopIteration:
        raise ValueError("patient roles are empty") from None
    if roles_header != ["patient_id", "role"]:
        raise ValueError("patient-role header must be exactly patient_id,role")

    permitted_roles = ("train", "adaptive_development")
    patient_roles: dict[str, str] = {}
    try:
        for line_number, row in enumerate(roles_reader, start=2):
            if len(row) != 2:
                raise ValueError(f"patient-role line {line_number} must contain exactly two fields")
            patient_id, role = row
            if re.fullmatch(r"[0-9]{8}", patient_id) is None:
                raise ValueError(f"patient-role line {line_number} has an invalid patient ID")
            if role not in permitted_roles:
                raise ValueError(f"patient-role line {line_number} has an unknown role")
            if patient_id in patient_roles:
                raise ValueError(f"patient-role line {line_number} repeats patient {patient_id}")
            patient_roles[patient_id] = role
    except csv.Error as exc:
        raise ValueError(f"invalid patient-role CSV: {exc}") from None

    official_train_patients = {image_id[:8] for image_id in official_train}
    official_test_patients = {image_id[:8] for image_id in official_test}
    if set(patient_roles) != official_train_patients:
        missing = len(official_train_patients - set(patient_roles))
        extra = len(set(patient_roles) - official_train_patients)
        test_patients = len(set(patient_roles) & official_test_patients)
        raise ValueError(
            "patient roles do not exactly cover official train/validation patients "
            f"(missing={missing}, extra={extra}, official_test={test_patients})"
        )
    role_patient_counts = {
        role: sum(assigned == role for assigned in patient_roles.values())
        for role in permitted_roles
    }
    if any(count == 0 for count in role_patient_counts.values()):
        raise ValueError("both train and adaptive_development require at least one patient")

    if mapping_raw.startswith(b"\xef\xbb\xbf"):
        raise ValueError("mapping UTF-8 BOM is forbidden")
    try:
        mapping_text = mapping_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"mapping is not valid UTF-8: {exc}") from None
    mapping_reader = csv.reader(io.StringIO(mapping_text, newline=""), strict=True)
    try:
        mapping_header = next(mapping_reader)
    except StopIteration:
        raise ValueError("mapping is empty") from None
    if mapping_header != ["split", "index", "image_id"]:
        raise ValueError("mapping header must be exactly split,index,image_id")

    locations: dict[str, tuple[str, int]] = {}
    next_index = {split: 0 for split in SPLITS}
    try:
        for line_number, row in enumerate(mapping_reader, start=2):
            if len(row) != 3:
                raise ValueError(f"mapping line {line_number} must contain exactly three fields")
            split, index_text, image_id = row
            if split not in next_index:
                raise ValueError(f"mapping line {line_number} has an unknown split")
            try:
                index = int(index_text)
            except ValueError:
                raise ValueError(f"mapping line {line_number} has a non-integer index") from None
            if str(index) != index_text or index != next_index[split]:
                raise ValueError(f"mapping line {line_number} has a noncanonical or noncontiguous index")
            next_index[split] += 1
            if IMAGE_ID.fullmatch(image_id) is None or image_id in locations:
                raise ValueError(f"mapping line {line_number} has an invalid or duplicate image ID")
            locations[image_id] = (split, index)
    except csv.Error as exc:
        raise ValueError(f"invalid mapping CSV: {exc}") from None
    if set(locations) != official_train | official_test:
        raise ValueError("mapping and official split universes differ")

    records = []
    for image_id in sorted(official_train):
        wrapper_split, wrapper_index = locations[image_id]
        patient_id = image_id[:8]
        records.append({
            "image_id": image_id,
            "patient_id": patient_id,
            "role": patient_roles[patient_id],
            "wrapper_index": wrapper_index,
            "wrapper_split": wrapper_split,
        })
    role_image_counts = {
        role: sum(record["role"] == role for record in records)
        for role in permitted_roles
    }
    return canonical.seal({
        "schema_id": "mmbu.phase1.chestmnist_development_manifest",
        "schema_version": 1,
        "mapping_sha256": hashlib.sha256(mapping_raw).hexdigest(),
        "official_train_val_sha256": reconciliation["official_train_val_sha256"],
        "official_test_sha256": reconciliation["official_test_sha256"],
        "patient_roles_sha256": hashlib.sha256(patient_roles_raw).hexdigest(),
        "records": records,
        "role_image_counts": role_image_counts,
        "role_patient_counts": role_patient_counts,
        "official_test_image_count_excluded": len(official_test),
        "official_test_patient_count_excluded": len(official_test_patients),
        "official_test_excluded": not any(record["image_id"] in official_test for record in records),
        "labels_opened": False,
        "pixels_opened": False,
        "source_admitted": False,
        "mmbu_public_content_used": False,
    })
