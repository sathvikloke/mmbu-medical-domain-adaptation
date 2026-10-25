#!/usr/bin/env python3
"""Post-output exploratory aggregation for the replicated response screen."""

from __future__ import annotations

from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import biomedical_lane1, fields as f, replicated_response


def grade_task_rows(rows: list[dict], base_predictions: list[dict], adapted_predictions: list[dict]) -> list[dict]:
    """Convert aligned raw task predictions into explicit paired binary grades."""
    f.require(len(rows) == len(base_predictions) == len(adapted_predictions), "response.aggregate.predictions",
              "rows, base predictions, and adapted predictions must align one-to-one")
    grades = []
    for index, (row, base, adapted) in enumerate(zip(rows, base_predictions, adapted_predictions)):
        path = f"response.aggregate.predictions[{index}]"
        f.require(base.get("row_id") == adapted.get("row_id") == row.get("row_id"), f"{path}.row_id",
                  "does not align")
        grades.append({
            "adapted_correct": int(
                biomedical_lane1.normalize_answer(adapted.get("task"))
                == biomedical_lane1.normalize_answer(row.get("task_target"))
            ),
            "base_correct": int(
                biomedical_lane1.normalize_answer(base.get("task"))
                == biomedical_lane1.normalize_answer(row.get("task_target"))
            ),
            "group_id": row["independent_unit_id"],
            "record_id": row["row_id"],
            "source_id": row["source_id"],
        })
    return grades


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
    f.require(type(profile_predictions) is dict and set(profile_predictions) == {"dual", "task_only"},
              "response.aggregate.profile_predictions", "must contain dual and task_only exactly")
    profiles = {}
    for profile in ("task_only", "dual"):
        predictions_by_seed = profile_predictions[profile]
        f.require(type(predictions_by_seed) is dict and bool(predictions_by_seed),
                  f"response.aggregate.{profile}", "must contain at least one seed")
        seed_rows = {
            seed_id: grade_task_rows(rows, base_predictions, predictions)
            for seed_id, predictions in predictions_by_seed.items()
        }
        profiles[profile] = replicated_response.paired_seed_mean_task_bootstrap(
            seed_rows,
            iterations=iterations,
            bootstrap_seed=bootstrap_seed,
            confidence=confidence,
        )
    return {
        "inference": "post_output_exploratory_fixed_development_population",
        "profiles": profiles,
        "promotion_eligible": False,
    }


__all__ = ["analyze_candidate", "grade_task_rows"]
