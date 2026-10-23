"""Exact continuous task-change arithmetic and the secondary binary-flip table.

``B = sum(w b)/W``, ``T = sum(w a)/W``, ``d = a - b``; positive/negative mass are
the weighted positive/negative parts of ``d`` over ``W``; the net change is
``T - B``.  A non-success terminal outcome contributes exact zero while its
stored grade stays null.  Binary flips exist only for a prospectively bound
correctness predicate and keep every example in ``N``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, Mapping

from mmbu_phase1 import canonical, fields as f, rational

TERMINAL_OUTCOMES = ("success", "runtime_failure", "parse_failure", "validation_failure", "judge_failure")
ROW_KEYS = ("example_id", "independent_unit_id", "task_weight", "base_terminal_outcome", "adapted_terminal_outcome",
            "base_grade", "adapted_grade", "delta", "state")
TOTAL_KEYS = ("example_count", "weight_sum", "base_mean", "adapted_mean", "positive_mass", "negative_mass",
              "net_task_change")
BINARY_KEYS = ("correctness_rule_digest", "N", "PF", "NF", "other", "binary_net_flip_rate")
CORRECTNESS_RULES = {"task_grade_equals_one"}


def correctness_rule(name: str) -> dict:
    """The closed prospective correctness predicate object bound by a judge policy."""
    f.one_of(name, "correctness_rule", CORRECTNESS_RULES)
    return {"rule": name, "version": 1}


def _grade(judged: Mapping[str, Any], path: str) -> tuple[str, Any, Fraction]:
    outcome = f.one_of(judged.get("terminal_outcome"), f"{path}.terminal_outcome", TERMINAL_OUTCOMES)
    grade = judged.get("task_grade")
    if outcome == "success":
        f.number(grade, f"{path}.task_grade", minimum=0, maximum=1)
        return outcome, grade, canonical.exact(grade)
    f.require(grade is None, f"{path}.task_grade", "a non-success outcome keeps a null grade (no fabricated zero)")
    return outcome, None, Fraction(0)


def _correct(rule: dict | None, outcome: str, value: Fraction) -> bool:
    return outcome == "success" and value == 1


def build(manifest_rows: list, base: Mapping[str, Mapping], adapted: Mapping[str, Mapping],
          rule: dict | None) -> tuple[list, dict, dict | None]:
    """Rows in manifest order, recomputed totals, and the optional binary summary."""
    f.require(bool(manifest_rows), "task_change", "the population must be nonempty")
    ids = [row["example_id"] for row in manifest_rows]
    f.require(set(base) == set(ids) and set(adapted) == set(ids), "task_change",
              "every manifest row needs exactly one base and one adapted judged record (missing row is structural)")
    rows, weights, deltas, base_values, adapted_values, flips = [], [], [], [], [], []
    for row in manifest_rows:
        example = row["example_id"]
        weight = f.number(row["task_weight"], f"task_change[{example}].task_weight", minimum=0, min_exclusive=True)
        b_outcome, b_grade, b_value = _grade(base[example], f"task_change[{example}].base")
        a_outcome, a_grade, a_value = _grade(adapted[example], f"task_change[{example}].adapted")
        delta = a_value - b_value
        rows.append({
            "example_id": example,
            "independent_unit_id": row["independent_unit_id"],
            "task_weight": weight,
            "base_terminal_outcome": b_outcome,
            "adapted_terminal_outcome": a_outcome,
            "base_grade": b_grade,
            "adapted_grade": a_grade,
            "delta": rational.to_wire(delta),
            "state": "positive" if delta > 0 else "negative" if delta < 0 else "zero",
        })
        w = canonical.exact(weight)
        weights.append(w)
        deltas.append(delta)
        base_values.append(b_value)
        adapted_values.append(a_value)
        flips.append((_correct(rule, b_outcome, b_value), _correct(rule, a_outcome, a_value)))
    total = sum(weights, Fraction(0))
    base_mean = sum((w * b for w, b in zip(weights, base_values)), Fraction(0)) / total
    adapted_mean = sum((w * a for w, a in zip(weights, adapted_values)), Fraction(0)) / total
    positive = sum((w * max(d, Fraction(0)) for w, d in zip(weights, deltas)), Fraction(0)) / total
    negative = sum((w * max(-d, Fraction(0)) for w, d in zip(weights, deltas)), Fraction(0)) / total
    f.require(adapted_mean - base_mean == positive - negative, "task_change", "identity T - B = positive - negative failed")
    totals = {
        "example_count": len(rows),
        "weight_sum": rational.to_wire(total),
        "base_mean": rational.to_wire(base_mean),
        "adapted_mean": rational.to_wire(adapted_mean),
        "positive_mass": rational.to_wire(positive),
        "negative_mass": rational.to_wire(negative),
        "net_task_change": rational.to_wire(adapted_mean - base_mean),
    }
    binary = None
    if rule is not None:
        f.one_of(rule.get("rule"), "correctness_rule", CORRECTNESS_RULES)
        pf = sum(1 for before, after in flips if not before and after)
        nf = sum(1 for before, after in flips if before and not after)
        binary = {
            "correctness_rule_digest": canonical.value_digest(rule),
            "N": len(rows),
            "PF": pf,
            "NF": nf,
            "other": len(rows) - pf - nf,
            "binary_net_flip_rate": rational.to_wire(Fraction(pf - nf, len(rows))),
        }
    return rows, totals, binary


def verify(rows: Any, totals: Any, binary: Any, manifest_rows: list, base: Mapping, adapted: Mapping,
           rule: dict | None, path: str = "task_change_summary") -> None:
    """Recompute every row and total; supplied values never override the rows."""
    rows = f.array(rows, f"{path}.rows", nonempty=True)
    for index, row in enumerate(rows):
        f.closed(row, f"{path}.rows[{index}]", ROW_KEYS)
        rational.from_wire(row["delta"], f"{path}.rows[{index}].delta")
    f.closed(totals, f"{path}.totals", TOTAL_KEYS)
    f.integer(totals["example_count"], f"{path}.totals.example_count", minimum=1)
    for name in TOTAL_KEYS[1:]:
        rational.from_wire(totals[name], f"{path}.totals.{name}")
    if binary is not None:
        f.closed(binary, f"{path}.binary_summary", BINARY_KEYS)
        for name in ("N", "PF", "NF", "other"):
            f.integer(binary[name], f"{path}.binary_summary.{name}", minimum=0)
        rational.from_wire(binary["binary_net_flip_rate"], f"{path}.binary_summary.binary_net_flip_rate")
        f.require(binary["N"] == binary["PF"] + binary["NF"] + binary["other"], f"{path}.binary_summary",
                  "N must equal PF + NF + other")
    expected_rows, expected_totals, expected_binary = build(manifest_rows, base, adapted, rule)
    f.require(len(rows) == len(expected_rows), f"{path}.rows", "every example must appear exactly once")
    for index, (row, expected) in enumerate(zip(rows, expected_rows)):
        f.require(f.same(row, expected), f"{path}.rows[{index}]", "row does not recompute exactly in manifest order")
    f.require(f.same(totals, expected_totals), f"{path}.totals", "totals do not recompute from the rows")
    if expected_binary is None:
        f.require(binary is None, f"{path}.binary_summary", "no prospective correctness predicate: binary summary is null")
    else:
        f.require(f.same(binary, expected_binary), f"{path}.binary_summary", "binary summary does not recompute")
