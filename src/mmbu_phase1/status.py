"""``mmbu.phase1.current_status``: the sole repository status authority."""

from __future__ import annotations

from typing import Any, Mapping

from mmbu_phase1 import fields as f
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
