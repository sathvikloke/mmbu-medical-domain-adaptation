"""Fail-closed BUSI-WHU held-out confirmation mechanics.

This module is CPU-only and performs validation and exact arithmetic. It has
no data acquisition, model, scheduler, network, or accelerator integration.
"""

from __future__ import annotations

from pathlib import Path

from mmbu_phase1 import canonical
from mmbu_phase1.fields import ContractViolation, closed, fail, literal, require


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


LINEAGE_KEYS = (
    "base_model_id", "base_revision", "expected_parameter_count", "legacy_exploratory_adapter_used",
    "lora_alpha", "lora_dropout", "lora_rank", "lora_target_suffixes", "mmbu_public_content_used",
    "optimizer_updates", "post_admission_retraining", "profile", "runtime_gate_id", "runtime_gate_passed",
    "source_purposes", "training_seed",
)


def validate_checkpoint_lineage(value: object, path: str = "heldout_confirmation.lineage") -> dict:
    """Accept only a newly retrained, fully authorized member of the fixed family."""
    row = closed(value, path, LINEAGE_KEYS)
    expected = {
        "base_model_id": "Qwen/Qwen3.5-9B",
        "base_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "expected_parameter_count": 9409813744,
        "legacy_exploratory_adapter_used": False,
        "lora_alpha": 16,
        "lora_dropout": 0,
        "lora_rank": 8,
        "lora_target_suffixes": ["q_proj", "v_proj"],
        "mmbu_public_content_used": False,
        "optimizer_updates": 1024,
        "post_admission_retraining": True,
        "profile": "dual",
        "runtime_gate_id": "qwen3.5-9b-successor-native-runtime",
        "runtime_gate_passed": True,
        "source_purposes": {"busbra": "train", "pathmnist": "train"},
    }
    for key, expected_value in expected.items():
        literal(row[key], f"{path}.{key}", expected_value)
    require(type(row["training_seed"]) is int and row["training_seed"] in (20261025, 20261026, 20261027),
            f"{path}.training_seed", "must be one of the three frozen non-boolean integer seeds")
    return row


__all__ = ["SPEC_DIGEST", "load_spec", "validate_checkpoint_lineage", "validate_spec"]

