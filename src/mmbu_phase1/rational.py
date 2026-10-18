"""The closed canonical reduced-rational wire type from EVALUATOR_MECHANICS.md."""

from __future__ import annotations

from fractions import Fraction
from math import gcd
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation, closed, fail, integer


def _representable(value: int, path: str) -> None:
    try:
        canonical.dumps(value)
    except canonical.CanonicalJSONError as exc:
        fail(path, f"exact rational component is unrepresentable: {exc}")


def to_wire(value: Fraction | int) -> dict[str, int]:
    """Encode an exact value; rejects rather than approximating huge terms."""
    if type(value) is int:
        value = Fraction(value)
    if type(value) is not Fraction:
        raise TypeError("rational.to_wire requires an int or Fraction")
    _representable(value.numerator, "rational.numerator")
    _representable(value.denominator, "rational.denominator")
    return {"denominator": value.denominator, "numerator": value.numerator}


def from_wire(value: Any, path: str = "rational") -> Fraction:
    """Decode and strictly validate ``{"denominator":D,"numerator":N}``."""
    closed(value, path, ("denominator", "numerator"))
    numerator = integer(value["numerator"], f"{path}.numerator")
    denominator = integer(value["denominator"], f"{path}.denominator", minimum=1)
    _representable(numerator, f"{path}.numerator")
    _representable(denominator, f"{path}.denominator")
    if gcd(abs(numerator), denominator) != 1:
        fail(path, "must be reduced with gcd(|numerator|, denominator) = 1 and zero as 0/1")
    return Fraction(numerator, denominator)


def equal(left: Any, right: Any, path: str = "rational") -> bool:
    """Compare two canonical wire rationals by cross multiplication."""
    a = from_wire(left, f"{path}.left")
    b = from_wire(right, f"{path}.right")
    return a.numerator * b.denominator == b.numerator * a.denominator


def require(value: Any, expected: Fraction, path: str) -> Fraction:
    actual = from_wire(value, path)
    if actual.numerator * expected.denominator != expected.numerator * actual.denominator:
        fail(path, f"expected exact rational {expected}, got {actual}")
    return actual


__all__ = ["ContractViolation", "equal", "from_wire", "require", "to_wire"]
