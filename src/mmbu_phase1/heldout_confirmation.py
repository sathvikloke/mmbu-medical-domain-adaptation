"""Fail-closed BUSI-WHU held-out confirmation mechanics.

This module is CPU-only and performs validation and exact arithmetic. It has
no data acquisition, model, scheduler, network, or accelerator integration.
"""

from __future__ import annotations

from pathlib import Path

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation, closed, fail


SPEC_DIGEST = "a7a074d0acac95da79a6505bc791faf30e48f879218ad0b30027f2b56916c703"
SPEC_KEYS = (
    "authorization", "candidate", "confirmation_id", "gates", "prompts", "resources",
    "schema_id", "schema_version", "source", "statistics", "training",
)


def validate_spec(value: object) -> dict:
    """Validate the one prospectively frozen confirmation protocol exactly."""
    record = closed(value, "heldout_confirmation.spec", SPEC_KEYS)
    try:
        digest = canonical.value_digest(record)
    except (canonical.CanonicalJSONError, TypeError, ValueError) as exc:
        fail("heldout_confirmation.spec", f"is not canonicalizable: {exc}")
    if digest != SPEC_DIGEST:
        fail("heldout_confirmation.spec", "does not match the frozen protocol digest")
    return record


def load_spec(path: Path) -> dict:
    try:
        value = canonical.loads(path.read_bytes())
    except (OSError, canonical.CanonicalJSONError) as exc:
        raise ContractViolation("heldout_confirmation.spec", f"cannot load: {exc}") from None
    return validate_spec(value)


__all__ = ["SPEC_DIGEST", "load_spec", "validate_spec"]

