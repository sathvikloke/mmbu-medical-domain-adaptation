"""``mmbu.phase1.current_status``: the sole repository status authority."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping

from mmbu_phase1 import canonical, fields as f
from mmbu_phase1.vocab import STATUS_PHASES

KEYS = (
    "schema_id",
    "schema_version",
    "contract_revision",
    "contract_manifest_digest",
    "official_source_hashes",
    "phase",
    "facts",
    "updated_at",
    "record_digest",
)
FACT_KEYS = ("fact_id", "status", "value", "unit", "evidence_digests", "limitation")
FACT_STATUSES = ("measured", "unknown", "blocked_external")
# Account/allocation facts need scheduler/allocation evidence; Phase 1A has no
# admissible schema for it, so they can never be ``measured`` here, and public
# specifications (``public.*`` evidence) can never support them.
ACCOUNT_FACT_PREFIX = "account."
PUBLIC_FACT_PREFIX = "public."
PREDECESSOR_FACT_ID = "authority.current_status_predecessor"
AUDIT_FACT_ID = "audit.busi_whu_decision_integrity"
REPAIR_FACT_ID = "repair.busi_whu_decision_integrity"
EVIDENCE_SCOPE_FACT_ID = "research.busi_whu_evidence_classification"
SUCCESSOR_FACT_IDS = frozenset({
    PREDECESSOR_FACT_ID, AUDIT_FACT_ID, REPAIR_FACT_ID, EVIDENCE_SCOPE_FACT_ID,
})


def validate_current_status(
    record: Any,
    *,
    contract_revision: str,
    contract_manifest_digest: str,
    official_source_hashes: Mapping[str, str],
    path: str = "current_status",
) -> dict:
    f.record(record, "current_status", KEYS, path)
    f.literal(record["contract_revision"], f"{path}.contract_revision", contract_revision)
    f.digest(record["contract_manifest_digest"], f"{path}.contract_manifest_digest")
    f.require(
        record["contract_manifest_digest"] == contract_manifest_digest,
        f"{path}.contract_manifest_digest",
        "must equal the verified contract-manifest SHA-256",
    )
    hashes = f.closed(record["official_source_hashes"], f"{path}.official_source_hashes", official_source_hashes)
    for name, expected in official_source_hashes.items():
        f.digest(hashes[name], f"{path}.official_source_hashes.{name}")
        f.require(hashes[name] == expected, f"{path}.official_source_hashes.{name}", "must equal the contract manifest")
    f.one_of(record["phase"], f"{path}.phase", STATUS_PHASES)
    facts = f.array(record["facts"], f"{path}.facts")
    public_evidence: set[str] = set()
    account_evidence: set[str] = set()
    for index, fact in enumerate(facts):
        label = f"{path}.facts[{index}]"
        f.closed(fact, label, FACT_KEYS)
        fact_id = f.text(fact["fact_id"], f"{label}.fact_id")
        status = f.one_of(fact["status"], f"{label}.status", FACT_STATUSES)
        evidence = f.digest_set(fact["evidence_digests"], f"{label}.evidence_digests", nonempty=status == "measured")
        if status == "measured":
            f.require(fact["value"] is not None, f"{label}.value", "measured facts require a non-null value")
            f.text(fact["unit"], f"{label}.unit")
            f.nullable(f.text, fact["limitation"], f"{label}.limitation")
        else:
            f.require(fact["value"] is None, f"{label}.value", "unmeasured facts cannot assert a value")
            f.require(fact["unit"] is None, f"{label}.unit", "unmeasured facts cannot assert a unit")
            f.text(fact["limitation"], f"{label}.limitation")
        if fact_id.startswith(ACCOUNT_FACT_PREFIX):
            f.require(
                status != "measured",
                f"{label}.status",
                "account/allocation facts require allocation evidence; public specifications cannot support them",
            )
            account_evidence.update(evidence)
        if fact_id.startswith(PUBLIC_FACT_PREFIX):
            public_evidence.update(evidence)
    f.sorted_unique(facts, f"{path}.facts", lambda fact: fact["fact_id"].encode("utf-8"))
    f.require(
        not (public_evidence & account_evidence),
        f"{path}.facts",
        "public-specification evidence cannot support an account/allocation fact",
    )
    f.timestamp(record["updated_at"], f"{path}.updated_at")
    return record


def _fact_map(record: dict, path: str) -> dict[str, dict]:
    rows = record["facts"]
    result = {row["fact_id"]: row for row in rows}
    f.require(len(result) == len(rows), path, "contains duplicate fact IDs")
    return result


def validate_status_transition(predecessor: Any, successor: Any) -> dict:
    """Validate one immutable, fail-closed current-status successor."""
    if type(predecessor) is not dict or type(successor) is not dict:
        f.fail("status_transition", "predecessor and successor must be objects")
    hashes = predecessor.get("official_source_hashes")
    if type(hashes) is not dict:
        f.fail("status_transition.predecessor", "official source hashes are missing")
    validate_current_status(
        predecessor,
        contract_revision=predecessor.get("contract_revision"),
        contract_manifest_digest=predecessor.get("contract_manifest_digest"),
        official_source_hashes=hashes,
        path="status_transition.predecessor",
    )
    validate_current_status(
        successor,
        contract_revision=predecessor["contract_revision"],
        contract_manifest_digest=predecessor["contract_manifest_digest"],
        official_source_hashes=hashes,
        path="status_transition.successor",
    )
    f.literal(successor["phase"], "status_transition.successor.phase", "phase1_returned_blocked")
    f.require(
        f.timestamp(successor["updated_at"], "status_transition.successor.updated_at")
        > f.timestamp(predecessor["updated_at"], "status_transition.predecessor.updated_at"),
        "status_transition.successor.updated_at", "must be later than the predecessor",
    )
    f.require(
        successor["record_digest"] != predecessor["record_digest"],
        "status_transition.successor.record_digest", "must create a new immutable record",
    )
    before = _fact_map(predecessor, "status_transition.predecessor.facts")
    after = _fact_map(successor, "status_transition.successor.facts")
    historical_ids = set(before) - {PREDECESSOR_FACT_ID}
    f.require(
        set(after) == historical_ids | SUCCESSOR_FACT_IDS,
        "status_transition.successor.facts", "must preserve history and add only the closed repair facts",
    )
    for fact_id in historical_ids:
        f.require(
            canonical.dumps(after[fact_id]) == canonical.dumps(before[fact_id]),
            f"status_transition.successor.facts.{fact_id}", "historical fact changed",
        )
    predecessor_fact = after[PREDECESSOR_FACT_ID]
    f.require(
        predecessor_fact["status"] == "measured"
        and predecessor_fact["value"] == predecessor["record_digest"]
        and predecessor_fact["unit"] == "record_digest"
        and len(predecessor_fact["evidence_digests"]) == 1,
        f"status_transition.successor.facts.{PREDECESSOR_FACT_ID}",
        "must bind the exact predecessor and its preserved bytes",
    )
    audit = after[AUDIT_FACT_ID]
    f.require(
        audit["status"] == "blocked_external" and audit["value"] is None
        and audit["unit"] is None and audit["evidence_digests"] == [],
        f"status_transition.successor.facts.{AUDIT_FACT_ID}",
        "must remain externally blocked without evidence claims",
    )
    repair = after[REPAIR_FACT_ID]
    f.require(
        repair["status"] == "measured" and repair["unit"] == "git_revision"
        and type(repair["value"]) is str
        and re.fullmatch(r"[0-9a-f]{40}", repair["value"]) is not None
        and len(repair["evidence_digests"]) == 1,
        f"status_transition.successor.facts.{REPAIR_FACT_ID}",
        "must bind one exact repaired Git revision and evidence digest",
    )
    evidence_scope = after[EVIDENCE_SCOPE_FACT_ID]
    f.require(
        evidence_scope["status"] == "measured"
        and evidence_scope["value"] == "exploratory_only"
        and evidence_scope["unit"] == "evidence_classification"
        and evidence_scope["evidence_digests"] == repair["evidence_digests"],
        f"status_transition.successor.facts.{EVIDENCE_SCOPE_FACT_ID}",
        "repair evidence must remain exploratory-only",
    )
    return successor


def build_status_successor(
    predecessor: dict, *, predecessor_raw_sha256: str, repaired_revision: str,
    repair_evidence_digest: str, audit_blockers: list[str], updated_at: str,
) -> dict:
    """Build and validate the canonical blocked successor for this repair."""
    f.digest(predecessor_raw_sha256, "status_successor.predecessor_raw_sha256")
    f.require(
        type(repaired_revision) is str and re.fullmatch(r"[0-9a-f]{40}", repaired_revision) is not None,
        "status_successor.repaired_revision", "must be a full lowercase Git SHA-1",
    )
    f.digest(repair_evidence_digest, "status_successor.repair_evidence_digest")
    blockers = f.array(audit_blockers, "status_successor.audit_blockers", nonempty=True)
    for index, blocker in enumerate(blockers):
        f.text(blocker, f"status_successor.audit_blockers[{index}]")
    f.sorted_unique(blockers, "status_successor.audit_blockers", lambda value: value.encode("utf-8"))
    f.require(
        f.timestamp(updated_at, "status_successor.updated_at")
        > f.timestamp(predecessor["updated_at"], "status_successor.predecessor.updated_at"),
        "status_successor.updated_at", "must be later than the predecessor",
    )
    facts = [
        deepcopy(row) for row in predecessor["facts"]
        if row["fact_id"] != PREDECESSOR_FACT_ID
    ]
    facts.extend((
        {
            "fact_id": AUDIT_FACT_ID, "status": "blocked_external", "value": None,
            "unit": None, "evidence_digests": [],
            "limitation": "Remaining external blockers: " + "; ".join(blockers) + ".",
        },
        {
            "fact_id": PREDECESSOR_FACT_ID, "status": "measured",
            "value": predecessor["record_digest"], "unit": "record_digest",
            "evidence_digests": [predecessor_raw_sha256],
            "limitation": "Exact canonical predecessor bytes are preserved; this grants no execution or scientific authority.",
        },
        {
            "fact_id": REPAIR_FACT_ID, "status": "measured", "value": repaired_revision,
            "unit": "git_revision", "evidence_digests": [repair_evidence_digest],
            "limitation": "Decision-integrity code and verification evidence only; no biomedical or competition effect claim.",
        },
        {
            "fact_id": EVIDENCE_SCOPE_FACT_ID, "status": "measured",
            "value": "exploratory_only", "unit": "evidence_classification",
            "evidence_digests": [repair_evidence_digest],
            "limitation": "Engineering validation is not source admission, clinical validation, confirmation, or competition performance.",
        },
    ))
    successor = canonical.seal({
        key: deepcopy(predecessor[key]) for key in (
            "schema_id", "schema_version", "contract_revision",
            "contract_manifest_digest", "official_source_hashes",
        )
    } | {
        "phase": "phase1_returned_blocked",
        "facts": sorted(facts, key=lambda row: row["fact_id"].encode("utf-8")),
        "updated_at": updated_at,
    })
    return validate_status_transition(predecessor, successor)
