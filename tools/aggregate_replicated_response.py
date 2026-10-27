#!/usr/bin/env python3
"""Post-output exploratory aggregation for the replicated response screen."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import replicated_response


def grade_task_rows(rows: list[dict], base_predictions: list[dict], adapted_predictions: list[dict]) -> list[dict]:
    """Convert aligned raw task predictions into explicit paired binary grades."""
    return replicated_response.grade_task_rows(rows, base_predictions, adapted_predictions)


def analyze_candidate(
    rows: list[dict],
    base_predictions: list[dict],
    profile_predictions: dict[str, dict[str, list[dict]]],
    *,
    iterations: int,
    bootstrap_seed: int,
    confidence: float,
) -> dict:
    """Calculate post-output paired task intervals for each frozen adaptation profile."""
    return replicated_response.analyze_candidate(
        rows, base_predictions, profile_predictions, iterations=iterations,
        bootstrap_seed=bootstrap_seed, confidence=confidence,
    )


__all__ = ["analyze_candidate", "grade_task_rows"]
