"""Frozen 64-bit dHash and deterministic duplicate-candidate projection."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from mmbu_phase1 import canonical, fields as f


RECORD_KEYS = (
    "source_id", "source_version", "record_id", "decoded_sha256", "dhash64", "width", "height",
)
SOURCE_KEYS = ("source_id", "source_version")
INVENTORY_KEYS = ("source_id", "source_version", "complete", "records", "inventory_digest")
CLOSURE_KEYS = ("eligible_sources", "inventories")


def dhash64(grayscale_rows: Any) -> int:
    """Return row-major adjacent-comparison dHash for an exact 9x8 grid."""
    rows = f.array(grayscale_rows, "dhash64.rows")
    f.require(len(rows) == 8, "dhash64.rows", "must contain exactly 8 rows")
    value = 0
    for y, row in enumerate(rows):
        cells = f.array(row, f"dhash64.rows[{y}]")
        f.require(len(cells) == 9, f"dhash64.rows[{y}]", "must contain exactly 9 columns")
        for x, cell in enumerate(cells):
            f.integer(cell, f"dhash64.rows[{y}][{x}]", minimum=0, maximum=255)
        for x in range(8):
            value = (value << 1) | int(cells[x] > cells[x + 1])
    return value


def hamming64(left: Any, right: Any) -> int:
    for value, name in ((left, "left"), (right, "right")):
        f.integer(value, f"hamming64.{name}", minimum=0, maximum=(1 << 64) - 1)
    return (left ^ right).bit_count()


def _record(value: Any, path: str) -> dict:
    row = f.closed(value, path, RECORD_KEYS)
    for name in ("source_id", "source_version", "record_id"):
        f.text(row[name], f"{path}.{name}")
    f.digest(row["decoded_sha256"], f"{path}.decoded_sha256")
    fingerprint = f.text(row["dhash64"], f"{path}.dhash64")
    f.require(len(fingerprint) == 16 and all(char in "0123456789abcdef" for char in fingerprint),
              f"{path}.dhash64", "must be 16 lowercase hexadecimal characters")
    f.integer(row["width"], f"{path}.width", minimum=1)
    f.integer(row["height"], f"{path}.height", minimum=1)
    return row


def _identity(row: dict) -> tuple[str, str, str]:
    return row["source_id"], row["source_version"], row["record_id"]


def _source(value: Any, path: str) -> dict:
    row = f.closed(value, path, SOURCE_KEYS)
    f.text(row["source_id"], f"{path}.source_id")
    f.text(row["source_version"], f"{path}.source_version")
    return row


def _inventory(value: Any, path: str) -> dict:
    item = f.closed(value, path, INVENTORY_KEYS)
    f.text(item["source_id"], f"{path}.source_id")
    f.text(item["source_version"], f"{path}.source_version")
    f.literal(item["complete"], f"{path}.complete", True)
    rows = f.array(item["records"], f"{path}.records")
    for index, row in enumerate(rows):
        _record(row, f"{path}.records[{index}]")
        f.require(
            (row["source_id"], row["source_version"]) == (item["source_id"], item["source_version"]),
            f"{path}.records[{index}]", "record identity differs from inventory source",
        )
    f.sorted_unique(rows, f"{path}.records", lambda row: row["record_id"].encode("utf-8"))
    payload = {name: item[name] for name in ("source_id", "source_version", "complete", "records")}
    f.require(item["inventory_digest"] == canonical.value_digest(payload), f"{path}.inventory_digest",
              "does not bind the complete inventory payload")
    return item


def _aspect_delta(left: dict, right: dict) -> Fraction:
    left_ratio = Fraction(left["width"], left["height"])
    right_ratio = Fraction(right["width"], right["height"])
    return abs(left_ratio - right_ratio) / max(left_ratio, right_ratio)


def _candidate(left: dict, right: dict) -> dict | None:
    exact = left["decoded_sha256"] == right["decoded_sha256"]
    distance = hamming64(int(left["dhash64"], 16), int(right["dhash64"], 16))
    delta = _aspect_delta(left, right)
    perceptual = distance <= 4 and delta <= Fraction(5, 100)
    if not exact and not perceptual:
        return None
    return {
        "left_source_id": left["source_id"],
        "left_source_version": left["source_version"],
        "left_record_id": left["record_id"],
        "right_source_id": right["source_id"],
        "right_source_version": right["source_version"],
        "right_record_id": right["record_id"],
        "exact_decoded_match": exact,
        "hamming_distance": distance,
        "aspect_relative_delta": {
            "numerator": delta.numerator,
            "denominator": delta.denominator,
        },
        "perceptual_match": perceptual,
        "disposition": "pending_independent_review",
    }


def build_duplicate_candidates(
    records: Any, source_inventories: Any, *, include_within_source: bool = True,
) -> list[dict]:
    """Compare local records within-source and against a complete eligible-source closure."""
    local = f.array(records, "duplicate_candidates.records")
    for index, row in enumerate(local):
        _record(row, f"duplicate_candidates.records[{index}]")
    f.sorted_unique(sorted(local, key=_identity), "duplicate_candidates.records.sorted", _identity)
    f.require(len({_identity(row) for row in local}) == len(local), "duplicate_candidates.records",
              "record identities must be unique")

    closure = f.closed(source_inventories, "duplicate_candidates.source_inventories", CLOSURE_KEYS)
    eligible = f.array(closure["eligible_sources"], "duplicate_candidates.eligible_sources")
    for index, row in enumerate(eligible):
        _source(row, f"duplicate_candidates.eligible_sources[{index}]")
    f.sorted_unique(eligible, "duplicate_candidates.eligible_sources",
                    lambda row: (row["source_id"] + "\0" + row["source_version"]).encode())
    inventories = f.array(closure["inventories"], "duplicate_candidates.inventories")
    for index, item in enumerate(inventories):
        _inventory(item, f"duplicate_candidates.inventories[{index}]")
    expected = {(row["source_id"], row["source_version"]) for row in eligible}
    observed = {(row["source_id"], row["source_version"]) for row in inventories}
    f.require(observed == expected, "duplicate_candidates.inventories",
              "must contain exactly one complete inventory for every eligible source")
    f.require(len(observed) == len(inventories), "duplicate_candidates.inventories",
              "source inventories must be unique")

    local = sorted(local, key=_identity)
    candidates = []
    for left_index, left in enumerate(local):
        if include_within_source:
            for right in local[left_index + 1:]:
                item = _candidate(left, right)
                if item is not None:
                    candidates.append(item)
        for inventory_item in inventories:
            for right in inventory_item["records"]:
                item = _candidate(left, right)
                if item is not None:
                    candidates.append(item)
    candidates.sort(key=lambda row: (
        row["left_source_id"], row["left_source_version"], row["left_record_id"],
        row["right_source_id"], row["right_source_version"], row["right_record_id"],
    ))
    return candidates


__all__ = ["build_duplicate_candidates", "dhash64", "hamming64"]
