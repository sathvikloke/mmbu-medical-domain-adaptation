#!/usr/bin/env python3
"""Bind BUS-BRA structural receipts to a fail-closed transform contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path


ARCHIVE_BYTES = 133_917_740
ARCHIVE_MD5 = "1f8b2be6476d58fc97bfb5e5a1ea9bab"
METADATA_SHA256 = "f218d0f10b0aeeb14ff4b2cfed8631b2f4a7cf608e564548b35bddd55f3aafb3"


def _digest(value):
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False).encode("ascii")).hexdigest()


def _is_positive_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _load_json(path):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value):
        raise ValueError(f"non-finite JSON value: {value}")

    return json.loads(Path(path).read_text(encoding="utf-8"),
                      object_pairs_hook=pairs, parse_constant=reject_constant)


def _verify_receipt(value, schema):
    if not isinstance(value, dict) or value.get("schema") != schema:
        raise ValueError("receipt schema mismatch")
    unsigned = copy.deepcopy(value)
    claimed = unsigned.pop("receipt_digest", None)
    if not isinstance(claimed, str) or claimed != _digest(unsigned):
        raise ValueError("receipt digest mismatch")
    if (value.get("source_id"), value.get("source_version")) != ("busbra", "1.0"):
        raise ValueError("receipt identifies a different source")
    if value.get("archive_bytes") != ARCHIVE_BYTES or value.get("archive_md5") != ARCHIVE_MD5:
        raise ValueError("receipt archive identity mismatch")
    if value.get("metadata_sha256") != METADATA_SHA256:
        raise ValueError("receipt metadata identity mismatch")
    if any(value.get(key) is not False for key in
           ("training_ready", "model_executed", "model_use_authorized")):
        raise ValueError("input receipt escalates authority")
    return claimed


def _linked_groups(candidates):
    parents = {}

    def find(item):
        parents.setdefault(item, item)
        if parents[item] != item:
            parents[item] = find(parents[item])
        return parents[item]

    def union(left, right):
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parents[max(left_root, right_root)] = min(left_root, right_root)

    seen = set()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("triage candidate must be an object")
        cases = candidate.get("case_ids")
        records = candidate.get("record_ids")
        if (not isinstance(cases, list) or len(cases) != 2 or
                not all(isinstance(item, str) and item.isdigit() for item in cases) or
                cases != sorted(set(cases), key=lambda item: item.encode("utf-8"))):
            raise ValueError("candidate case IDs must be two unique sorted numeric strings")
        if (not isinstance(records, list) or len(records) != 2 or
                records != sorted(set(records), key=lambda item: item.encode("utf-8"))):
            raise ValueError("candidate record IDs must be two unique sorted strings")
        identity = (tuple(cases), tuple(records))
        if identity in seen:
            raise ValueError("duplicate triage candidate")
        seen.add(identity)
        if candidate.get("cross_case") is not True or candidate.get("exact_decoded_match") is not False:
            raise ValueError("only unresolved cross-case nonexact candidates may be linked")
        union(cases[0], cases[1])
    groups = {}
    for case in parents:
        groups.setdefault(find(case), []).append(case)
    return sorted((sorted(group, key=lambda item: item.encode("utf-8"))
                   for group in groups.values() if len(group) > 1), key=lambda group: group[0])


def _exception_ids(receipt, field, declared_count=None):
    values = receipt.get(field)
    if not isinstance(values, list):
        raise ValueError(f"{field} must be a list")
    identifiers = []
    for value in values:
        if not isinstance(value, dict) or not isinstance(value.get("record_id"), str):
            raise ValueError(f"{field} contains an invalid record")
        identifiers.append(value["record_id"])
    if len(set(identifiers)) != len(identifiers):
        raise ValueError(f"{field} contains duplicate records")
    if declared_count is not None and declared_count != len(identifiers):
        raise ValueError(f"{field} does not match its declared count")
    return sorted(identifiers, key=lambda item: item.encode("utf-8"))


def build_contract(corpus_receipt, triage_receipt):
    """Return a geometry/split contract without approving medical or model use."""
    corpus_digest = _verify_receipt(
        corpus_receipt, "mmbu.busbra.quarantine_corpus_audit_receipt.v1")
    triage_digest = _verify_receipt(
        triage_receipt, "mmbu.busbra.near_duplicate_triage_receipt.v1")
    if corpus_receipt.get("ok") is not True:
        raise ValueError("corpus audit did not complete")
    if not _is_positive_int(corpus_receipt.get("record_count")):
        raise ValueError("corpus record count is invalid")
    if (not _is_positive_int(corpus_receipt.get("case_count")) or
            corpus_receipt["case_count"] > corpus_receipt["record_count"]):
        raise ValueError("corpus case count is invalid")
    if (corpus_receipt.get("image_mode_counts") != {"L": corpus_receipt["record_count"]} or
            corpus_receipt.get("mask_mode_counts") != {"1": corpus_receipt["record_count"]}):
        raise ValueError("decoded image/mask population is not closed")
    if (corpus_receipt.get("exact_image_duplicate_clearance") is not True or
            corpus_receipt.get("exact_mask_duplicate_clearance") is not True or
            corpus_receipt.get("exact_image_duplicate_groups") != [] or
            corpus_receipt.get("exact_mask_duplicate_groups") != []):
        raise ValueError("exact duplicates are not cleared")
    dimension_exceptions = _exception_ids(
        corpus_receipt, "metadata_dimension_mismatches")
    if corpus_receipt.get("metadata_dimension_clearance") is (len(dimension_exceptions) > 0):
        raise ValueError("dimension clearance contradicts the exception population")
    bbox_exceptions = _exception_ids(
        corpus_receipt, "bbox_iou_below_0_95_records",
        corpus_receipt.get("bbox_iou_below_0_95"))
    candidates = triage_receipt.get("candidates")
    if (not isinstance(candidates, list) or
            not isinstance(triage_receipt.get("candidate_count"), int) or
            isinstance(triage_receipt.get("candidate_count"), bool) or
            triage_receipt["candidate_count"] != len(candidates)):
        raise ValueError("triage candidate population is incomplete")
    if (not _is_positive_int(triage_receipt.get("fingerprint_count")) or
            triage_receipt["fingerprint_count"] != corpus_receipt["record_count"]):
        raise ValueError("triage does not cover the decoded corpus")
    if (not isinstance(triage_receipt.get("cross_case_candidate_count"), int) or
            isinstance(triage_receipt.get("cross_case_candidate_count"), bool) or
            triage_receipt["cross_case_candidate_count"] != len(candidates)):
        raise ValueError("cross-case candidate count is incomplete")
    if triage_receipt.get("automatic_merge_or_exclusion") is not False:
        raise ValueError("triage may not make an automatic record decision")
    linked = _linked_groups(candidates)
    contract = {
        "schema": "mmbu.busbra.structural_transform_contract.v1",
        "source_id": "busbra",
        "source_version": "1.0",
        "corpus_receipt_digest": corpus_digest,
        "triage_receipt_digest": triage_digest,
        "record_count": corpus_receipt["record_count"],
        "case_count": corpus_receipt["case_count"],
        "independent_unit": "Case",
        "canonical_dimensions": "decoded_image_dimensions",
        "image_mask_dimension_rule": "decoded_dimensions_must_match_exactly",
        "localization_target": "tight_half_open_xywh_from_binary_mask_foreground",
        "qa_only_metadata_fields": ["BBOX", "Height", "Width"],
        "prohibited_split_fields": [f"valid_{index}" for index in range(1, 11)],
        "source_split_field": "kFold",
        "linked_case_groups": linked,
        "linked_case_policy": "coassign_one_split_until_provenance_resolved",
        "dimension_exception_records": dimension_exceptions,
        "bbox_exception_records": bbox_exceptions,
        "structural_transform_clearance": True,
        "medical_correctness_reviewed": False,
        "source_proximity_reviewed": False,
        "rights_and_purpose_approved": False,
        "training_ready": False,
        "model_executed": False,
        "model_use_authorized": False,
        "limitations": [
            "Mask-derived geometry is a deterministic transform, not medical validation.",
            "Conservative case linkage prevents split leakage but does not establish shared patient identity.",
            "This contract grants no training, evaluation, selection, release, or submission purpose.",
        ],
    }
    contract["contract_digest"] = _digest(contract)
    return contract


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("corpus_receipt", type=Path)
    parser.add_argument("triage_receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise SystemExit("output already exists")
    try:
        corpus = _load_json(args.corpus_receipt)
        triage = _load_json(args.triage_receipt)
        contract = build_contract(corpus, triage)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            json.dump(contract, stream, sort_keys=True, indent=2, allow_nan=False)
            stream.write("\n")
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(str(exc)) from exc
    print(json.dumps(contract, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
