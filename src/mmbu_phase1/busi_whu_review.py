"""Fail-closed BUSI-WHU clinical-review selection mechanics."""

from __future__ import annotations

import hashlib

from . import canonical


_INVENTORY_KEYS = {
    "annotation_member_join_complete", "annotation_payload_decoding_used", "artifact_name",
    "image_member_join_complete", "image_payload_decoding_used", "label_counts", "label_values_read",
    "mmbu_public_content_used", "model_use_authorized", "patient_count", "record_count",
    "record_digest", "records", "schema_id", "schema_version", "sheet_name",
}
_RECORD_KEYS = {"label_code", "parent_id", "record_id", "row_digest", "workbook_row"}


def _closed(value: object, keys: set[str], path: str) -> dict:
    if type(value) is not dict or set(value) != keys:
        raise ValueError(f"{path} must contain exactly {sorted(keys)}")
    return value


def _ranking(patient_id: str) -> tuple[bytes, bytes]:
    encoded = patient_id.encode("utf-8")
    return hashlib.sha256(b"busi-whu-review-v1\0" + encoded).digest(), encoded


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


__all__ = ["build_review_selection"]
