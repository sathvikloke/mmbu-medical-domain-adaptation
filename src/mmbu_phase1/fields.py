"""Closed-record field primitives shared by every Phase 1 validator."""

from __future__ import annotations

import calendar
from datetime import datetime, timezone
import math
import re
from typing import Any, Callable, Iterable, NoReturn

from mmbu_phase1 import canonical

SCHEMA_PREFIX = "mmbu.phase1."
_DIGEST = re.compile(r"[0-9a-f]{64}")
_TIMESTAMP = re.compile(r"(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?Z")


class ContractViolation(ValueError):
    """A record, reference, or chronology rule failed closed."""

    def __init__(self, path: str, message: str):
        super().__init__(f"{path}: {message}")
        self.path = path
        self.message = message


def fail(path: str, message: str) -> NoReturn:
    raise ContractViolation(path, message)


def require(condition: bool, path: str, message: str) -> None:
    if not condition:
        fail(path, message)


def closed(value: Any, path: str, keys: Iterable[str]) -> dict:
    """Require a JSON object with exactly ``keys``."""
    expected = set(keys)
    if type(value) is not dict:
        fail(path, "must be a JSON object")
    missing = sorted(expected - set(value))
    extra = sorted(set(value) - expected)
    if missing or extra:
        fail(path, f"closed object mismatch; missing={missing} unknown={extra}")
    return value


def text(value: Any, path: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str:
        fail(path, "must be a string")
    if not allow_empty and not value:
        fail(path, "must be a nonempty string")
    return value


def integer(value: Any, path: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if type(value) is not int:
        fail(path, "must be a non-boolean JSON integer")
    if minimum is not None and value < minimum:
        fail(path, f"must be >= {minimum}")
    if maximum is not None and value > maximum:
        fail(path, f"must be <= {maximum}")
    return value


def number(
    value: Any,
    path: str,
    *,
    minimum: float | int | None = None,
    maximum: float | int | None = None,
    min_exclusive: bool = False,
    max_exclusive: bool = False,
) -> int | float:
    """A finite non-boolean JSON number; bounds compare exact canonical values."""
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        fail(path, "must be a finite non-boolean JSON number")
    exact = canonical.exact(value)
    if minimum is not None:
        low = canonical.exact(minimum)
        if exact < low or (min_exclusive and exact == low):
            fail(path, f"must be {'>' if min_exclusive else '>='} {minimum}")
    if maximum is not None:
        high = canonical.exact(maximum)
        if exact > high or (max_exclusive and exact == high):
            fail(path, f"must be {'<' if max_exclusive else '<='} {maximum}")
    return value


def boolean(value: Any, path: str) -> bool:
    if type(value) is not bool:
        fail(path, "must be a JSON boolean")
    return value


def literal(value: Any, path: str, expected: Any) -> Any:
    if type(value) is not type(expected) or value != expected:
        fail(path, f"must be exactly {expected!r}")
    return value


def one_of(value: Any, path: str, allowed: Iterable[str]) -> str:
    allowed = set(allowed)
    if type(value) is not str or value not in allowed:
        fail(path, f"must be one of {sorted(allowed)}")
    return value


def digest(value: Any, path: str) -> str:
    if type(value) is not str or not _DIGEST.fullmatch(value):
        fail(path, "must be a lowercase 64-character SHA-256 hex digest")
    return value


def nullable(check: Callable[..., Any], value: Any, path: str, **options: Any) -> Any:
    return None if value is None else check(value, path, **options)


def timestamp(value: Any, path: str) -> int:
    """Parse an RFC 3339 UTC ``Z`` timestamp into integer epoch nanoseconds."""
    if type(value) is not str:
        fail(path, "must be an RFC 3339 UTC timestamp string")
    match = _TIMESTAMP.fullmatch(value)
    if not match:
        fail(path, "must be an RFC 3339 UTC timestamp ending in Z")
    year, month, day, hour, minute, second = (int(part) for part in match.groups()[:6])
    try:
        moment = datetime(year, month, day, hour, minute, second, tzinfo=timezone.utc)
    except ValueError:
        fail(path, "is not a valid calendar instant")
    fraction = (match.group(7) or "").ljust(9, "0")
    return calendar.timegm(moment.utctimetuple()) * 1_000_000_000 + int(fraction or "0")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def utf8_key(value: str) -> bytes:
    return value.encode("utf-8")


def sorted_unique(items: list, path: str, key: Callable[[Any], Any]) -> list:
    keys = [key(item) for item in items]
    for index in range(1, len(keys)):
        if keys[index - 1] == keys[index]:
            fail(path, "must not contain duplicate members")
        if keys[index - 1] > keys[index]:
            fail(path, "must be sorted by UTF-8 bytes")
    return items


def array(value: Any, path: str, *, nonempty: bool = False) -> list:
    if type(value) is not list:
        fail(path, "must be a JSON array")
    if nonempty and not value:
        fail(path, "must be a nonempty array")
    return value


def string_set(
    value: Any,
    path: str,
    *,
    nonempty: bool = False,
    allowed: Iterable[str] | None = None,
    allow_empty_items: bool = False,
) -> list[str]:
    """A unique array of strings sorted by UTF-8 bytes."""
    items = array(value, path, nonempty=nonempty)
    allowed_set = set(allowed) if allowed is not None else None
    for index, item in enumerate(items):
        text(item, f"{path}[{index}]", allow_empty=allow_empty_items)
        if allowed_set is not None and item not in allowed_set:
            fail(f"{path}[{index}]", f"must be one of {sorted(allowed_set)}")
    return sorted_unique(items, path, utf8_key)


def digest_set(value: Any, path: str, *, nonempty: bool = False) -> list[str]:
    items = array(value, path, nonempty=nonempty)
    for index, item in enumerate(items):
        digest(item, f"{path}[{index}]")
    return sorted_unique(items, path, utf8_key)


def header(record: Any, schema: str, path: str | None = None) -> dict:
    """Require exact ``schema_id`` and integer ``schema_version`` 1."""
    label = path or schema
    if type(record) is not dict:
        fail(label, "record must be a JSON object")
    if record.get("schema_id") != SCHEMA_PREFIX + schema:
        fail(f"{label}.schema_id", f"must be exactly {SCHEMA_PREFIX + schema}")
    literal(record.get("schema_version"), f"{label}.schema_version", 1)
    return record


def sealed(record: dict, path: str) -> str:
    """Require ``record_digest`` to equal the canonical record digest."""
    value = digest(record.get("record_digest"), f"{path}.record_digest")
    try:
        computed = canonical.record_digest(record)
    except canonical.CanonicalJSONError as exc:
        fail(path, f"record is not canonicalizable: {exc}")
    if value != computed:
        fail(f"{path}.record_digest", "does not equal the canonical record digest")
    return value


def record(value: Any, schema: str, keys: Iterable[str], path: str | None = None) -> dict:
    """Header + closed key set + record digest for a standard sealed record."""
    label = path or schema
    header(value, schema, label)
    closed(value, label, keys)
    sealed(value, label)
    return value


def same(left: Any, right: Any) -> bool:
    """Byte equality after RFC 8785 canonicalization."""
    return canonical.dumps(left) == canonical.dumps(right)
