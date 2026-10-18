"""Content-addressed resolution of sealed records and raw artifacts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable

from mmbu_phase1 import canonical
from mmbu_phase1.fields import SCHEMA_PREFIX, ContractViolation, fail, sealed


class RecordStore:
    """Resolve ``record_digest`` references to records and SHA-256 to bytes.

    A reference is valid only when it resolves to a record of the named
    closed schema; an arbitrary non-null digest never satisfies it.
    """

    def __init__(self, records: Iterable[dict] = (), artifacts: Iterable[bytes] = ()):
        self._records: dict[str, dict] = {}
        self._artifacts: dict[str, bytes] = {}
        for record in records:
            self.add(record)
        for artifact in artifacts:
            self.add_artifact(artifact)

    def add(self, record: dict) -> str:
        if type(record) is not dict or type(record.get("schema_id")) is not str:
            fail("store", "only schema-identified JSON object records can be stored")
        digest = sealed(record, record["schema_id"])
        existing = self._records.get(digest)
        if existing is not None and canonical.dumps(existing) != canonical.dumps(record):
            fail("store", f"conflicting records share digest {digest}")
        self._records[digest] = deepcopy(record)
        return digest

    def add_artifact(self, data: bytes) -> str:
        digest = canonical.raw_digest(data)
        self._artifacts[digest] = bytes(data)
        return digest

    def __contains__(self, digest: object) -> bool:
        return digest in self._records

    def maybe(self, digest: Any) -> dict | None:
        record = self._records.get(digest) if type(digest) is str else None
        return deepcopy(record) if record is not None else None

    def get(self, digest: Any, schema: str | Iterable[str] | None = None, path: str = "reference") -> dict:
        record = self.maybe(digest)
        if record is None:
            fail(path, f"digest {digest!r} does not resolve to a stored record")
        if schema is not None:
            names = {schema} if isinstance(schema, str) else set(schema)
            if record["schema_id"] not in {SCHEMA_PREFIX + name for name in names}:
                fail(path, f"resolves to {record['schema_id']}, expected {sorted(names)}")
        return record

    def has_artifact(self, digest: Any) -> bool:
        return type(digest) is str and digest in self._artifacts

    def artifact(self, digest: Any, path: str = "artifact") -> bytes:
        if not self.has_artifact(digest):
            fail(path, f"digest {digest!r} does not resolve to stored artifact bytes")
        return self._artifacts[digest]

    def records(self, schema: str | None = None) -> list[dict]:
        values = deepcopy(list(self._records.values()))
        if schema is None:
            return values
        return [record for record in values if record["schema_id"] == SCHEMA_PREFIX + schema]


__all__ = ["ContractViolation", "RecordStore"]
