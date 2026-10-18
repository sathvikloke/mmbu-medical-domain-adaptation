"""Predecessor-bound authorization and opening-receipt registry generations."""

from __future__ import annotations

from typing import Any, Callable

from mmbu_phase1 import fields as f
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import PURPOSES

AUTHORIZATION_REGISTRY_KEYS = (
    "schema_id",
    "schema_version",
    "registry_id",
    "generation",
    "supersedes_registry_digest",
    "acquisition_authorization_digests",
    "source_record_digests",
    "purpose_authorization_digests",
    "acquisition_heads",
    "source_heads",
    "authorization_heads",
    "revoked_digests",
    "as_of",
    "record_digest",
)
OPENING_RECEIPT_REGISTRY_KEYS = (
    "schema_id",
    "schema_version",
    "registry_id",
    "generation",
    "supersedes_registry_digest",
    "heads",
    "created_at",
    "record_digest",
)
OPENING_HEAD_KEYS = ("lock_digest", "opening_id", "head_receipt_digest", "receipt_generation")
_RECORD_ARRAYS = {
    "acquisition_heads": "acquisition_authorization_digests",
    "source_heads": "source_record_digests",
    "authorization_heads": "purpose_authorization_digests",
}


def _generation(record: dict, path: str) -> int:
    generation = f.integer(record["generation"], f"{path}.generation", minimum=0)
    predecessor = record["supersedes_registry_digest"]
    if generation == 0:
        f.require(predecessor is None, f"{path}.supersedes_registry_digest", "generation zero has a null predecessor")
    else:
        f.digest(predecessor, f"{path}.supersedes_registry_digest")
    return generation


def _head_key(key: str, path: str, kind: str) -> None:
    f.text(key, path)
    parts = key.split("|")
    if kind == "source_heads":
        f.require(len(parts) == 1, path, "source head keys are a bare source_id")
        return
    f.require(len(parts) == 2 and all(parts), path, "head key must be canonical 'source_id|qualifier'")
    if kind == "authorization_heads":
        f.one_of(parts[1], path, PURPOSES)


def validate_authorization_registry(record: Any, path: str = "authorization_registry") -> dict:
    f.record(record, "authorization_registry", AUTHORIZATION_REGISTRY_KEYS, path)
    f.text(record["registry_id"], f"{path}.registry_id")
    _generation(record, path)
    listed: set[str] = set()
    for name in _RECORD_ARRAYS.values():
        listed.update(f.digest_set(record[name], f"{path}.{name}"))
    for heads_name, array_name in _RECORD_ARRAYS.items():
        heads = record[heads_name]
        if type(heads) is not dict:
            f.fail(f"{path}.{heads_name}", "must be a closed JSON object map")
        for key, value in heads.items():
            _head_key(key, f"{path}.{heads_name}[{key!r}]", heads_name)
            f.digest(value, f"{path}.{heads_name}[{key!r}]")
            f.require(value in record[array_name], f"{path}.{heads_name}[{key!r}]", "head is not a registered record")
    revoked = f.digest_set(record["revoked_digests"], f"{path}.revoked_digests")
    f.require(set(revoked) <= listed, f"{path}.revoked_digests", "revocations must name registered records")
    heads = {value for name in _RECORD_ARRAYS for value in record[name].values()}
    f.require(not heads & set(revoked), f"{path}.revoked_digests", "a digest cannot be both a head and revoked")
    f.timestamp(record["as_of"], f"{path}.as_of")
    return record


def validate_opening_receipt_registry(record: Any, path: str = "opening_receipt_registry") -> dict:
    f.record(record, "opening_receipt_registry", OPENING_RECEIPT_REGISTRY_KEYS, path)
    f.text(record["registry_id"], f"{path}.registry_id")
    _generation(record, path)
    heads = f.array(record["heads"], f"{path}.heads")
    for index, head in enumerate(heads):
        label = f"{path}.heads[{index}]"
        f.closed(head, label, OPENING_HEAD_KEYS)
        f.digest(head["lock_digest"], f"{label}.lock_digest")
        f.text(head["opening_id"], f"{label}.opening_id")
        f.digest(head["head_receipt_digest"], f"{label}.head_receipt_digest")
        f.integer(head["receipt_generation"], f"{label}.receipt_generation", minimum=0)
    f.sorted_unique(heads, f"{path}.heads", lambda head: head["lock_digest"].encode("utf-8"))
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


# ---------------------------------------------------------------------------
# Full predecessor-chain validation


def _record_specs() -> dict[str, tuple[str, Callable, Callable, Callable]]:
    from mmbu_phase1 import admission

    return {
        "acquisition_heads": (
            "acquisition_authorization",
            admission.validate_acquisition_authorization,
            lambda store, r: f"{r['source_id']}|{r['source_version']}",
            lambda r: r["authorized_at"],
        ),
        "source_heads": (
            "source",
            admission.validate_source,
            lambda store, r: r["source_id"],
            lambda r: r["reviewed_at"] or r["created_at"],
        ),
        "authorization_heads": (
            "purpose_authorization",
            admission.validate_purpose_authorization,
            lambda store, r: f"{store.get(r['source_digest'], 'source')['source_id']}|{r['purpose']}",
            lambda r: r["decided_at"],
        ),
    }


def _check_record_chains(store: RecordStore, registry: dict, path: str) -> None:
    if not any(registry[name] for name in _RECORD_ARRAYS.values()):
        return
    as_of = f.timestamp(registry["as_of"], f"{path}.as_of")
    sources = set(registry["source_record_digests"])
    for heads_name, (schema, validator, key_of, time_of) in _record_specs().items():
        array_name = _RECORD_ARRAYS[heads_name]
        listed = registry[array_name]
        by_digest: dict[str, dict] = {}
        for digest in listed:
            label = f"{path}.{array_name}[{digest[:12]}]"
            record = store.get(digest, schema, label)
            validator(record, label)
            if schema == "purpose_authorization":
                f.require(record["source_digest"] in sources, label, "authorization source is not registered")
            f.require(f.timestamp(time_of(record), label) <= as_of, label, "record is later than registry as_of")
            by_digest[digest] = record
        successors: dict[str, str] = {}
        keys: dict[str, list[str]] = {}
        for digest, record in by_digest.items():
            key = key_of(store, record)
            keys.setdefault(key, []).append(digest)
            predecessor = record["supersedes_digest"]
            if predecessor is None:
                continue
            label = f"{path}.{array_name}[{digest[:12]}].supersedes_digest"
            f.require(predecessor in by_digest, label, "predecessor is not registered (missing record chain)")
            f.require(key_of(store, by_digest[predecessor]) == key, label, "successor changes registry identity")
            f.require(predecessor not in successors, label, "registry chain branches")
            successors[predecessor] = digest
        heads = registry[heads_name]
        f.require(set(heads) == set(keys), f"{path}.{heads_name}", "heads must cover exactly every registered key")
        for key, members in keys.items():
            leaves = [digest for digest in members if digest not in successors]
            roots = [digest for digest in members if by_digest[digest]["supersedes_digest"] is None]
            f.require(len(roots) == 1 and len(leaves) == 1, f"{path}.{heads_name}[{key!r}]", "chain must be one unbranched line")
            f.require(heads[key] == leaves[0], f"{path}.{heads_name}[{key!r}]", "head is not the chain leaf")


def check_authorization_registry_chain(store: RecordStore, digest: str, path: str = "authorization_registry") -> dict:
    """Validate a registry plus every predecessor generation and record chain."""
    registry = store.get(digest, "authorization_registry", path)
    validate_authorization_registry(registry, path)
    if registry["generation"] > 0:
        prior_digest = registry["supersedes_registry_digest"]
        prior = check_authorization_registry_chain(store, prior_digest, f"{path}<-g{registry['generation'] - 1}")
        f.require(prior["generation"] == registry["generation"] - 1, f"{path}.generation", "must increment by exactly one")
        f.require(
            f.timestamp(registry["as_of"], path) >= f.timestamp(prior["as_of"], path),
            f"{path}.as_of",
            "successor registry cannot move backward in time",
        )
        for name in (*_RECORD_ARRAYS.values(), "revoked_digests"):
            f.require(set(prior[name]) <= set(registry[name]), f"{path}.{name}", "prior entries were rewritten or dropped")
        for heads_name, array_name in _RECORD_ARRAYS.items():
            new_records = set(registry[array_name]) - set(prior[array_name])
            for key, old_head in prior[heads_name].items():
                f.require(key in registry[heads_name], f"{path}.{heads_name}", f"head {key!r} was removed")
                new_head = registry[heads_name][key]
                if new_head != old_head:
                    f.require(new_head in new_records, f"{path}.{heads_name}[{key!r}]", "head change lacks a new successor")
            for key in set(registry[heads_name]) - set(prior[heads_name]):
                f.require(registry[heads_name][key] in new_records, f"{path}.{heads_name}[{key!r}]", "new head is not newly appended")
    _check_record_chains(store, registry, path)
    return registry


def _receipt_chain(store: RecordStore, head: dict, path: str) -> None:
    from mmbu_phase1 import locks

    receipt = locks.check_opening_receipt_chain(store, head["head_receipt_digest"], path)
    f.require(receipt["lock_digest"] == head["lock_digest"], path, "head receipt names another lock")
    f.require(receipt["opening_id"] == head["opening_id"], path, "head receipt names another opening")
    f.require(receipt["receipt_generation"] == head["receipt_generation"], path, "head generation mismatch")


def check_opening_receipt_registry_chain(store: RecordStore, digest: str, path: str = "opening_receipt_registry") -> dict:
    """Validate the registry chain and every head's unbranched receipt chain."""
    registry = store.get(digest, "opening_receipt_registry", path)
    validate_opening_receipt_registry(registry, path)
    if registry["generation"] > 0:
        prior = check_opening_receipt_registry_chain(
            store, registry["supersedes_registry_digest"], f"{path}<-g{registry['generation'] - 1}"
        )
        f.require(prior["generation"] == registry["generation"] - 1, f"{path}.generation", "must increment by exactly one")
        f.require(
            f.timestamp(registry["created_at"], path) >= f.timestamp(prior["created_at"], path),
            f"{path}.created_at",
            "successor registry cannot move backward in time",
        )
        old = {head["lock_digest"]: head for head in prior["heads"]}
        new = {head["lock_digest"]: head for head in registry["heads"]}
        f.require(set(old) <= set(new), f"{path}.heads", "a registered lock was removed")
        added = set(new) - set(old)
        changed = [lock for lock in old if not f.same(old[lock], new[lock])]
        f.require(len(added) + len(changed) <= 1, f"{path}.heads", "a successor may add one lock or advance one head")
        for lock in changed:
            before, after = old[lock], new[lock]
            f.require(after["opening_id"] == before["opening_id"], f"{path}.heads", "head changed opening identity")
            f.require(
                after["receipt_generation"] == before["receipt_generation"] + 1,
                f"{path}.heads",
                "head must advance to its direct successor",
            )
            receipt = store.get(after["head_receipt_digest"], "opening_receipt", f"{path}.heads")
            f.require(
                receipt["supersedes_receipt_digest"] == before["head_receipt_digest"],
                f"{path}.heads",
                "new head does not directly succeed the prior head",
            )
    for index, head in enumerate(registry["heads"]):
        _receipt_chain(store, head, f"{path}.heads[{index}]")
    return registry
