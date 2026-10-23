"""Typed lineage receipts, sanitized rule extraction, and effective purposes.

Every reference edge is typed.  The effective allowed-purpose set is the
intersection of the child's declaration with every content-bearing ancestor
reached through ``data``/``model``/``prompt``/``processor``/``judge``/
``decision`` edges.  A ``governance`` edge is pruned only when its target
validates as an ``official_rule_summary`` backed by a two-reviewer
``sanitized_rule_extraction`` receipt; a validated summary is a sanitized
boundary whose own source ancestry is not traversed.  Governance relabeling,
cycles, missing parents, unknown ancestry, conflicting declarations, and
public/derivative ancestry in promotable purposes fail closed.
"""

from __future__ import annotations

from typing import Any, Iterable

from mmbu_phase1 import fields as f
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import EDGE_ROLES, ORIGINS, PROMOTABLE_PURPOSES, PURPOSES

LINEAGE_KEYS = (
    "schema_id",
    "schema_version",
    "lineage_id",
    "artifact_digest",
    "origin_class",
    "allowed_purposes",
    "parents",
    "source_version",
    "rights_receipt_digest",
    "grouping_receipt_digest",
    "qa_receipt_digest",
    "created_at",
    "record_digest",
)
REVIEW_FIELDS = ("source_version", "rights_receipt_digest", "grouping_receipt_digest", "qa_receipt_digest")
MODEL_USE_PURPOSES = frozenset({"engineering", "train", "adaptive_dev", "confirmation", "release"})
EXTRACTION_KEYS = (
    "schema_id",
    "schema_version",
    "extraction_id",
    "source_digest",
    "source_origin_class",
    "source_span_registry_digest",
    "included_spans",
    "excluded_content_classes",
    "extraction_function_digest",
    "output_digest",
    "reviewer_attestations",
    "created_at",
    "record_digest",
)
SPAN_KEYS = ("source_locator", "start", "end", "extracted_bytes_digest")
EXTRACTION_REVIEW_KEYS = ("reviewer_id", "reviewed_output_digest", "disposition", "reviewed_at", "attestation_digest")
EXCLUDED_CONTENT_CLASSES = (
    "annotation",
    "answer",
    "benchmark_outcome",
    "error_analysis",
    "example_derived_recommendation",
    "example_id",
    "example_statistic",
    "image",
    "label",
    "question",
)


def validate_lineage_receipt(record: Any, path: str = "lineage_receipt") -> dict:
    f.record(record, "lineage_receipt", LINEAGE_KEYS, path)
    f.text(record["lineage_id"], f"{path}.lineage_id")
    f.digest(record["artifact_digest"], f"{path}.artifact_digest")
    origin = f.one_of(record["origin_class"], f"{path}.origin_class", ORIGINS)
    purposes = f.string_set(record["allowed_purposes"], f"{path}.allowed_purposes", allowed=PURPOSES)
    parents = f.array(record["parents"], f"{path}.parents")
    for index, edge in enumerate(parents):
        label = f"{path}.parents[{index}]"
        f.closed(edge, label, ("parent_digest", "edge_role"))
        f.digest(edge["parent_digest"], f"{label}.parent_digest")
        f.one_of(edge["edge_role"], f"{label}.edge_role", EDGE_ROLES)
        f.require(edge["parent_digest"] != record["artifact_digest"], label, "an artifact cannot be its own parent")
    f.sorted_unique(parents, f"{path}.parents", lambda e: (e["parent_digest"].encode(), e["edge_role"].encode()))
    for name in REVIEW_FIELDS:
        f.nullable(f.digest, record[name], f"{path}.{name}")
    if origin == "external_reviewed" and set(purposes) & MODEL_USE_PURPOSES:
        for name in REVIEW_FIELDS:
            f.require(record[name] is not None, f"{path}.{name}", "required for external_reviewed model-use purposes")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def validate_sanitized_rule_extraction(record: Any, path: str = "sanitized_rule_extraction") -> dict:
    f.record(record, "sanitized_rule_extraction", EXTRACTION_KEYS, path)
    f.text(record["extraction_id"], f"{path}.extraction_id")
    f.digest(record["source_digest"], f"{path}.source_digest")
    f.literal(record["source_origin_class"], f"{path}.source_origin_class", "mmbu_official")
    f.digest(record["source_span_registry_digest"], f"{path}.source_span_registry_digest")
    spans = f.array(record["included_spans"], f"{path}.included_spans", nonempty=True)
    for index, span in enumerate(spans):
        label = f"{path}.included_spans[{index}]"
        f.closed(span, label, SPAN_KEYS)
        f.text(span["source_locator"], f"{label}.source_locator")
        start = f.integer(span["start"], f"{label}.start", minimum=0)
        f.integer(span["end"], f"{label}.end", minimum=start + 1)
        f.digest(span["extracted_bytes_digest"], f"{label}.extracted_bytes_digest")
    f.sorted_unique(spans, f"{path}.included_spans", lambda s: (s["source_locator"].encode(), s["start"]))
    for left, right in zip(spans, spans[1:]):
        if left["source_locator"] == right["source_locator"]:
            f.require(left["end"] <= right["start"], f"{path}.included_spans", "spans overlap")
    classes = f.string_set(record["excluded_content_classes"], f"{path}.excluded_content_classes")
    f.require(
        tuple(classes) == EXCLUDED_CONTENT_CLASSES,
        f"{path}.excluded_content_classes",
        "must be exactly the complete sorted protected-content class set",
    )
    f.digest(record["extraction_function_digest"], f"{path}.extraction_function_digest")
    output = f.digest(record["output_digest"], f"{path}.output_digest")
    reviews = f.array(record["reviewer_attestations"], f"{path}.reviewer_attestations")
    f.require(len(reviews) == 2, f"{path}.reviewer_attestations", "exactly two independent reviews are required")
    for index, review in enumerate(reviews):
        label = f"{path}.reviewer_attestations[{index}]"
        f.closed(review, label, EXTRACTION_REVIEW_KEYS)
        f.text(review["reviewer_id"], f"{label}.reviewer_id")
        f.require(review["reviewed_output_digest"] == output, f"{label}.reviewed_output_digest", "review covers other bytes")
        f.one_of(review["disposition"], f"{label}.disposition", ("approved", "rejected"))
        f.require(review["disposition"] == "approved", f"{label}.disposition", "both reviews must approve")
        f.timestamp(review["reviewed_at"], f"{label}.reviewed_at")
        f.digest(review["attestation_digest"], f"{label}.attestation_digest")
    f.require(reviews[0]["reviewer_id"] != reviews[1]["reviewer_id"], f"{path}.reviewer_attestations", "reviewer collision")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def lineage_for(store: RecordStore, artifact_digest: Any, path: str = "lineage") -> dict:
    """The unique lineage receipt for an artifact; absent or conflicting fails."""
    f.digest(artifact_digest, path)
    matches = [r for r in store.records("lineage_receipt") if r["artifact_digest"] == artifact_digest]
    f.require(bool(matches), path, "artifact has no lineage receipt")
    f.require(len(matches) == 1, path, "artifact has conflicting lineage declarations")
    return validate_lineage_receipt(matches[0], path)


def require_official_rule_summary(store: RecordStore, artifact_digest: Any, path: str = "official_rule_summary") -> dict:
    """Prove an artifact is a sanitized two-reviewer official rule summary."""
    receipt = lineage_for(store, artifact_digest, path)
    f.require(receipt["origin_class"] == "official_rule_summary", path, "artifact is not an official_rule_summary")
    edges = receipt["parents"]
    f.require(
        len(edges) == 1 and edges[0]["edge_role"] == "governance",
        f"{path}.parents",
        "an official_rule_summary has exactly one direct governance parent",
    )
    extractions = [r for r in store.records("sanitized_rule_extraction") if r["output_digest"] == artifact_digest]
    f.require(len(extractions) == 1, path, "summary lacks exactly one matching sanitized_rule_extraction receipt")
    extraction = validate_sanitized_rule_extraction(extractions[0], f"{path}.extraction")
    f.require(
        extraction["source_digest"] == edges[0]["parent_digest"],
        f"{path}.extraction.source_digest",
        "extraction source differs from the governance parent",
    )
    return receipt


def is_official_rule_summary(store: RecordStore, artifact_digest: Any) -> bool:
    try:
        require_official_rule_summary(store, artifact_digest)
    except f.ContractViolation:
        return False
    return True


def walk(store: RecordStore, artifact_digest: Any, path: str = "lineage") -> list[dict]:
    """Every receipt in the content-bearing ancestry (self first)."""
    visited: dict[str, dict] = {}
    order: list[dict] = []

    def visit(digest: str, trail: tuple[str, ...]) -> None:
        if digest in trail:
            f.fail(path, "lineage graph contains a cycle")
        if digest in visited:
            return
        receipt = lineage_for(store, digest, f"{path}[{digest[:12]}]")
        visited[digest] = receipt
        order.append(receipt)
        if receipt["origin_class"] == "official_rule_summary":
            require_official_rule_summary(store, digest, f"{path}[{digest[:12]}]")
            return  # sanitized boundary: extraction receipt replaces source ancestry
        for edge in receipt["parents"]:
            if edge["edge_role"] == "governance":
                if not is_official_rule_summary(store, edge["parent_digest"]):
                    f.fail(path, "governance edge targets content or decision material (relabeling)")
                continue
            visit(edge["parent_digest"], trail + (digest,))

    visit(artifact_digest, ())
    return order


def effective_purposes(store: RecordStore, artifact_digest: Any, path: str = "lineage") -> frozenset[str]:
    receipts = walk(store, artifact_digest, path)
    result = set(PURPOSES)
    for receipt in receipts:
        if receipt["origin_class"] == "unknown":
            f.fail(path, "an unknown-origin ancestor rejects use")
        result &= set(receipt["allowed_purposes"])
    return frozenset(result)


def require_purpose(
    store: RecordStore,
    artifact_digest: Any,
    purpose: str,
    path: str = "lineage",
    *,
    not_after_ns: int | None = None,
) -> frozenset[str]:
    """Fail closed unless ``purpose`` survives the complete lineage intersection."""
    f.one_of(purpose, f"{path}.purpose", PURPOSES)
    receipts = walk(store, artifact_digest, path)
    if purpose in PROMOTABLE_PURPOSES:
        for receipt in receipts:
            f.require(
                receipt["origin_class"] not in {"mmbu_official", "mmbu_derivative", "unknown"},
                path,
                f"{receipt['origin_class']} ancestry is forbidden for promotable purpose {purpose}",
            )
    if not_after_ns is not None:
        for receipt in receipts:
            f.require(f.timestamp(receipt["created_at"], path) <= not_after_ns, path, "lineage receipt is late")
    allowed = effective_purposes(store, artifact_digest, path)
    f.require(purpose in allowed, path, f"purpose {purpose} does not survive lineage intersection {sorted(allowed)}")
    return allowed


def hash_index_hits(digests: Iterable[str], index: frozenset[str]) -> int:
    """Restricted-role check: count matches against an official hash index, revealing no content."""
    return sum(1 for digest in set(digests) if digest in index)
