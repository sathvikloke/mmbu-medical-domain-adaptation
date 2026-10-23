"""The single Phase 1 canonical JSON kernel.

Parsing is strict I-JSON: UTF-8 without BOM, no duplicate keys, no lone
surrogates or noncharacters, and no number whose source lexeme differs in
exact decimal value from its RFC 8785 serialization (nonfinite, overflowing,
underflowing, or precision-losing values reject instead of rounding).
Serialization is RFC 8785: UTF-16 code-unit key order, minimal string
escaping, and ECMAScript shortest round-trip number text.  Every digest and
validator in ``mmbu_phase1`` goes through this module.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
import sys
from typing import Any, Mapping


if sys.float_repr_style != "short":  # pragma: no cover - CPython always uses short repr
    raise ImportError("RFC 8785 number serialization requires shortest round-trip float repr")

MAX_NUMBER_LEXEME = 1000
_WHITESPACE = " \t\n\r"
_SHORT_ESCAPES = {'"': '\\"', "\\": "\\\\", "\b": "\\b", "\t": "\\t", "\n": "\\n", "\f": "\\f", "\r": "\\r"}

# Digest domains whose subject omits exactly these top-level fields (SCHEMAS.md).
SUBJECT_DOMAINS: dict[str, frozenset[str]] = {
    "single_attestation": frozenset({"record_digest", "reviewer_attestation_digest"}),
    "multi_attestation": frozenset({"record_digest", "reviewer_attestation_digests"}),
    "source_approval": frozenset({"record_digest", "approval_attestation_digest"}),
    "model_lineage_completeness": frozenset({"record_digest", "completeness_attestation_digest"}),
}


class CanonicalJSONError(ValueError):
    """Strict JSON parse or canonicalization failure with a stable ``code``."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def es6_number(value: float) -> str:
    """Return the ECMAScript Number::toString text required by RFC 8785."""
    if type(value) is not float:
        raise TypeError("es6_number requires a float")
    if not math.isfinite(value):
        raise CanonicalJSONError("nonfinite", f"nonfinite JSON number: {value!r}")
    if value == 0.0:
        return "0"
    sign = "-" if value < 0 else ""
    mantissa, _, exponent = repr(abs(value)).partition("e")
    exp = int(exponent) if exponent else 0
    integer_part, _, fraction_part = mantissa.partition(".")
    digits = (integer_part + fraction_part).lstrip("0")
    exp -= len(fraction_part)
    stripped = digits.rstrip("0")
    exp += len(digits) - len(stripped)
    digits = stripped
    k = len(digits)
    n = exp + k
    if k <= n <= 21:
        text = digits + "0" * (n - k)
    elif 0 < n <= 21:
        text = digits[:n] + "." + digits[n:]
    elif -6 < n <= 0:
        text = "0." + "0" * (-n) + digits
    else:
        shown = n - 1
        text = digits[0] + ("." + digits[1:] if k > 1 else "") + "e" + ("+" if shown >= 0 else "-") + str(abs(shown))
    return sign + text


def _exact_int_text(value: int, label: str) -> str:
    try:
        as_float = float(value)
    except OverflowError:
        raise CanonicalJSONError("nonfinite", f"nonfinite JSON number: {label}") from None
    text = es6_number(as_float)
    if Decimal(text) != Decimal(value):
        raise CanonicalJSONError("inexact_number", f"JSON integer cannot be represented exactly: {label}")
    return text


def _parse_int(lexeme: str) -> int:
    if len(lexeme) > MAX_NUMBER_LEXEME:
        raise CanonicalJSONError("resource_limit", "JSON number lexeme exceeds the resource limit")
    try:
        value = int(lexeme)
    except ValueError:
        raise CanonicalJSONError("resource_limit", "JSON integer exceeds the conversion limit") from None
    _exact_int_text(value, lexeme)
    return value


def _parse_float(lexeme: str) -> float:
    if len(lexeme) > MAX_NUMBER_LEXEME:
        raise CanonicalJSONError("resource_limit", "JSON number lexeme exceeds the resource limit")
    value = float(lexeme)
    if not math.isfinite(value):
        raise CanonicalJSONError("nonfinite", f"nonfinite JSON number: {lexeme}")
    if value == 0.0:
        value = 0.0
    if Decimal(es6_number(value)) != Decimal(lexeme):
        raise CanonicalJSONError("inexact_number", f"JSON number cannot be represented exactly: {lexeme}")
    return value


def _parse_constant(name: str) -> Any:
    raise CanonicalJSONError("nonfinite", f"nonfinite JSON number: {name}")


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalJSONError("duplicate_key", f"duplicate JSON key: {key}")
        result[key] = value
    return result


_DECODER = json.JSONDecoder(
    object_pairs_hook=_pairs,
    parse_float=_parse_float,
    parse_int=_parse_int,
    parse_constant=_parse_constant,
    strict=True,
)
_PERMISSIVE = json.JSONDecoder()


def _skip_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index] in _WHITESPACE:
        index += 1
    return index


def _bad_code_point(code: int) -> bool:
    return 0xD800 <= code <= 0xDFFF or 0xFDD0 <= code <= 0xFDEF or (code & 0xFFFE) == 0xFFFE


def _check_text(text: str) -> None:
    for char in text:
        if _bad_code_point(ord(char)):
            raise CanonicalJSONError("invalid_unicode", f"string contains forbidden code point U+{ord(char):04X}")


def _check_unicode(value: Any) -> None:
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            _check_text(item)
        elif isinstance(item, dict):
            for key, child in item.items():
                _check_text(key)
                stack.append(child)
        elif isinstance(item, list):
            stack.extend(item)


def loads(raw: bytes | bytearray | memoryview) -> Any:
    """Parse one strict I-JSON document from exact bytes."""
    if not isinstance(raw, (bytes, bytearray, memoryview)):
        raise TypeError("canonical.loads requires bytes")
    data = bytes(raw)
    if data.startswith(b"\xef\xbb\xbf"):
        raise CanonicalJSONError("bom", "UTF-8 BOM is forbidden")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CanonicalJSONError("invalid_utf8", f"invalid UTF-8: {exc}") from None
    start = _skip_whitespace(text, 0)
    if start == len(text):
        raise CanonicalJSONError("invalid_json", "empty JSON document")
    try:
        value, end = _DECODER.raw_decode(text, start)
    except json.JSONDecodeError as exc:
        raise CanonicalJSONError("invalid_json", f"invalid JSON: {exc}") from None
    except RecursionError:
        raise CanonicalJSONError("resource_limit", "JSON nesting exceeds the resource limit") from None
    rest = _skip_whitespace(text, end)
    if rest != len(text):
        if rest == end and text[end - 1] not in '}]"':
            raise CanonicalJSONError("invalid_json", "invalid JSON: malformed trailing token")
        try:
            _PERMISSIVE.raw_decode(text, rest)
        except (json.JSONDecodeError, RecursionError, ValueError):
            raise CanonicalJSONError("invalid_json", "invalid JSON: extra data") from None
        raise CanonicalJSONError("multiple_values", "multiple top-level JSON values")
    _check_unicode(value)
    return value


def _emit_string(text: str, out: list[str]) -> None:
    out.append('"')
    for char in text:
        code = ord(char)
        if char in _SHORT_ESCAPES:
            out.append(_SHORT_ESCAPES[char])
        elif code < 0x20:
            out.append("\\u%04x" % code)
        elif _bad_code_point(code):
            raise CanonicalJSONError("invalid_unicode", f"string contains forbidden code point U+{code:04X}")
        else:
            out.append(char)
    out.append('"')


def _emit(value: Any, out: list[str]) -> None:
    kind = type(value)
    if value is None:
        out.append("null")
    elif value is True:
        out.append("true")
    elif value is False:
        out.append("false")
    elif kind is int:
        out.append(_exact_int_text(value, str(value) if abs(value) < 10 ** 30 else "large integer"))
    elif kind is float:
        out.append(es6_number(value))
    elif kind is str:
        _emit_string(value, out)
    elif kind is list:
        out.append("[")
        for index, item in enumerate(value):
            if index:
                out.append(",")
            _emit(item, out)
        out.append("]")
    elif kind is dict:
        for key in value:
            if type(key) is not str:
                raise CanonicalJSONError("unsupported_type", "JSON object keys must be strings")
        out.append("{")
        for index, key in enumerate(sorted(value, key=lambda item: item.encode("utf-16-be"))):
            if index:
                out.append(",")
            _emit_string(key, out)
            out.append(":")
            _emit(value[key], out)
        out.append("}")
    else:
        raise CanonicalJSONError("unsupported_type", f"unsupported JSON value type: {kind.__name__}")


def dumps(value: Any) -> bytes:
    """Serialize ``value`` as RFC 8785 canonical UTF-8 bytes."""
    out: list[str] = []
    try:
        _emit(value, out)
    except RecursionError:
        raise CanonicalJSONError("resource_limit", "JSON nesting exceeds the resource limit") from None
    return "".join(out).encode("utf-8")


def loads_canonical(raw: bytes | bytearray | memoryview) -> Any:
    """Parse bytes that must already be exactly RFC 8785 canonical."""
    value = loads(raw)
    if dumps(value) != bytes(raw):
        raise CanonicalJSONError("noncanonical", "JSON bytes are not RFC 8785 canonical")
    return value


def exact(value: Any) -> Fraction:
    """Exact rational value of a JSON number via its canonical decimal lexeme."""
    if type(value) is int:
        return Fraction(value)
    if type(value) is float:
        return Fraction(es6_number(value))
    raise TypeError("exact() requires a non-boolean JSON number")


def raw_digest(data: bytes) -> str:
    """SHA-256 over exact raw bytes (file/artifact domain)."""
    return hashlib.sha256(bytes(data)).hexdigest()


def value_digest(value: Any) -> str:
    """SHA-256 over the RFC 8785 bytes of a complete JSON value (no omission)."""
    return hashlib.sha256(dumps(value)).hexdigest()


def _without(record: Mapping[str, Any], omitted: frozenset[str]) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError("digest domains require a JSON object record")
    return {key: item for key, item in record.items() if key not in omitted}


def record_digest(record: Mapping[str, Any]) -> str:
    """Canonical record digest omitting only the top-level ``record_digest``."""
    return value_digest(_without(record, frozenset({"record_digest"})))


def subject_digest(record: Mapping[str, Any], domain: str) -> str:
    """Attestation subject digest for one closed SCHEMAS.md digest domain."""
    if domain not in SUBJECT_DOMAINS:
        raise ValueError(f"unknown attestation subject domain: {domain}")
    return value_digest(_without(record, SUBJECT_DOMAINS[domain]))


def seal(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``record`` whose ``record_digest`` is recomputed."""
    sealed = dict(_without(record, frozenset()))
    sealed["record_digest"] = record_digest(sealed)
    return sealed
