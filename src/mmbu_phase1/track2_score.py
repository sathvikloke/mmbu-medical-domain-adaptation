"""Exact synthetic Track 2 score-proxy arithmetic.

This module encodes the documented algebra only.  It is not an official
harness and accepts no model output or benchmark record.
"""

from __future__ import annotations

from fractions import Fraction

from mmbu_phase1.fields import ContractViolation, fail


def _unit_interval(value: Fraction, path: str) -> Fraction:
    if type(value) is not Fraction:
        fail(path, "must be an exact fractions.Fraction")
    if value < 0 or value > 1:
        fail(path, "must be in the closed interval [0, 1]")
    return value


def score_proxy(task: Fraction, context: Fraction, base_task: Fraction) -> Fraction:
    """Return ``(4/5*T + 1/5*C) * (T - T_base)`` exactly."""
    task = _unit_interval(task, "score.task")
    context = _unit_interval(context, "score.context")
    base_task = _unit_interval(base_task, "score.base_task")
    return (Fraction(4, 5) * task + Fraction(1, 5) * context) * (task - base_task)


__all__ = ["ContractViolation", "score_proxy"]
