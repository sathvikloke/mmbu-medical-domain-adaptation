"""Canonical closed vocabularies from CONTRACT.md and SCHEMAS.md."""

PURPOSES = ("engineering", "quarantine_inspection", "train", "adaptive_dev", "confirmation", "official_audit", "release")
# Purposes that can select, promote, confirm, or release a model.
PROMOTABLE_PURPOSES = frozenset({"train", "adaptive_dev", "confirmation", "release"})
ORIGINS = (
    "mmbu_official",
    "mmbu_derivative",
    "official_rule_summary",
    "external_reviewed",
    "external_quarantine",
    "synthetic_engineering",
    "unknown",
)
FORBIDDEN_PROMOTABLE_ORIGINS = ("mmbu_derivative", "mmbu_official", "unknown")
CLAIM_STATUSES = ("verified", "failed", "untested", "blocked_external")
CONTRACT_STATUSES = ("synthetic", "brief_snapshot", "organizer_confirmed")
EDGE_ROLES = ("governance", "data", "model", "prompt", "processor", "judge", "decision")
CONTENT_EDGE_ROLES = frozenset({"data", "model", "prompt", "processor", "judge", "decision"})
DECISION_KINDS = (
    "candidate_admission",
    "experiment_priority",
    "hyperparameter_choice",
    "seed_choice",
    "prompt_choice",
    "checkpoint_selection",
    "promotion",
    "release",
)
PHASE_DECISIONS = ("accepted", "returned_blocked", "rejected")
STATUS_PHASES = ("design_only", "phase1_running", "phase1_returned_blocked", "phase1_rejected", "phase1_accepted")
RUN_TERMINAL_STATUSES = ("succeeded", "failed", "cancelled", "preempted")
LEGACY_PURPOSE_VALUES = ("development", "dev", "external-development", "official_dev")
