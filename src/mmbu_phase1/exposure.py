"""Exact synthetic exposure accounting for Package B; no trainer or model integration."""

from __future__ import annotations

from collections import Counter
from fractions import Fraction
from typing import Any, Iterable

from mmbu_phase1 import fields as f


_ROW_KEYS = {
    "accepted", "base_unit_mass", "effective_unit_mass", "endpoint_id", "endpoint_share",
    "independent_unit_id", "prospective_balance_multiplier", "rejection_reason",
    "requested_context_fields", "schedule_position_or_epoch_rule", "source_family_id",
    "split_group_id", "supervised_token_count", "target_bytes", "task_form",
    "token_normalization_id", "unit_total_mass", "view_id", "view_share",
}


def _share(value: Any, path: str) -> Fraction:
    f.require(type(value) is Fraction and value > 0, path, "must be a positive exact Fraction")
    return value


def audit_rows(rows: Any) -> dict:
    f.require(type(rows) is list and rows, "rows", "nonempty row list required")
    units: dict[str, Fraction] = {}
    tokens: dict[str, Fraction] = {}
    context: dict[str, Fraction] = {}
    context_fields: dict[tuple[str, str], Fraction] = {}
    endpoint_totals: dict[tuple[str, str], Fraction] = {}
    endpoint_declared: dict[tuple[str, str], Fraction] = {}
    unit_contract: dict[str, tuple[Fraction, Fraction, Fraction, Fraction]] = {}
    seen: set[str] = set()
    rejected: list[dict] = []
    for index, row in enumerate(rows):
        path = f"rows[{index}]"
        f.require(type(row) is dict, path, "must be an object")
        f.closed(row, path, _ROW_KEYS)
        accepted = f.boolean(row.get("accepted"), f"{path}.accepted")
        reason = row.get("rejection_reason")
        for key in ("independent_unit_id", "source_family_id", "split_group_id", "endpoint_id",
                    "task_form", "token_normalization_id", "schedule_position_or_epoch_rule", "view_id"):
            f.text(row.get(key), f"{path}.{key}")
        unit_total = _share(row.get("unit_total_mass"), f"{path}.unit_total_mass")
        base = _share(row.get("base_unit_mass"), f"{path}.base_unit_mass")
        multiplier = _share(row.get("prospective_balance_multiplier"),
                            f"{path}.prospective_balance_multiplier")
        effective = _share(row.get("effective_unit_mass"), f"{path}.effective_unit_mass")
        f.require(base * multiplier == effective == unit_total, path,
                  "unit mass fields must agree exactly for this canonical synthetic slice")
        unit = row["independent_unit_id"]
        contract = (unit_total, base, multiplier, effective)
        prior_contract = unit_contract.setdefault(unit, contract)
        f.require(prior_contract == contract, path, "unit mass contract changed between views")
        view_id = row["view_id"]
        f.require(view_id not in seen, f"{path}.view_id", "duplicate view ID")
        seen.add(view_id)
        if not accepted:
            f.text(reason, f"{path}.rejection_reason")
            rejected.append({"view_id": row.get("view_id"), "reason": reason})
            continue
        f.require(reason is None, f"{path}.rejection_reason", "accepted row cannot have a rejection reason")
        count = f.integer(row.get("supervised_token_count"), f"{path}.supervised_token_count", minimum=1)
        f.require(type(row.get("target_bytes")) is bytes and row["target_bytes"],
                  f"{path}.target_bytes", "nonempty synthetic target bytes required")
        try:
            row["target_bytes"].decode("utf-8")
        except UnicodeDecodeError:
            f.fail(f"{path}.target_bytes", "must be valid UTF-8")
        share = _share(row.get("view_share"), f"{path}.view_share")
        units[unit] = units.get(unit, Fraction(0)) + share
        tokens[unit] = tokens.get(unit, Fraction(0)) + (share / count) * count
        fields = row.get("requested_context_fields")
        f.require(type(fields) is list and len(fields) == len(set(fields))
                  and all(type(item) is str and item for item in fields),
                  f"{path}.requested_context_fields", "must be a unique string list")
        if row["endpoint_id"] == "context":
            f.require(bool(fields), f"{path}.requested_context_fields", "context row requires one or more fields")
            context[unit] = context.get(unit, Fraction(0)) + share
            per_field = share / len(fields)
            for field in fields:
                key = (unit, field)
                context_fields[key] = context_fields.get(key, Fraction(0)) + per_field
        else:
            f.require(not fields, f"{path}.requested_context_fields",
                      "non-context rows cannot claim requested context fields")
        endpoint_key = (unit, row["endpoint_id"])
        declared = _share(row.get("endpoint_share"), f"{path}.endpoint_share")
        prior_declared = endpoint_declared.setdefault(endpoint_key, declared)
        f.require(prior_declared == declared, path, "endpoint share changed between views")
        endpoint_totals[endpoint_key] = endpoint_totals.get(endpoint_key, Fraction(0)) + share
    f.require(bool(units), "rows", "at least one accepted row required")
    for key, mass in endpoint_totals.items():
        f.require(mass == endpoint_declared[key], f"endpoint_mass.{key[0]}.{key[1]}",
                  "view shares do not partition the declared endpoint share")
    for unit, mass in units.items():
        f.require(mass == unit_contract[unit][3], f"unit_mass.{unit}",
                  "accepted views must sum to the canonical effective unit mass")
    return {"context_field_mass": context_fields, "context_mass": context, "rejected_rows": rejected,
            "token_mass": tokens, "unit_mass": units}


def partial(weighted_losses: Iterable[tuple[Fraction, Fraction]]) -> tuple[Fraction, Fraction]:
    numerator = Fraction(0)
    denominator = Fraction(0)
    for loss, weight in weighted_losses:
        f.require(type(loss) is Fraction, "loss", "must be an exact Fraction")
        f.require(type(weight) is Fraction and weight > 0, "weight", "must be a positive exact Fraction")
        numerator += loss * weight
        denominator += weight
    f.require(denominator > 0, "weighted_step", "empty-target optimizer step is forbidden")
    return numerator, denominator


def combine_partials(parts: Iterable[tuple[Fraction, Fraction]]) -> Fraction:
    numerator = Fraction(0)
    denominator = Fraction(0)
    for local_numerator, local_denominator in parts:
        f.require(type(local_numerator) is Fraction and type(local_denominator) is Fraction
                  and local_denominator > 0, "partial", "invalid weighted partial")
        numerator += local_numerator
        denominator += local_denominator
    f.require(denominator > 0, "weighted_step", "empty-target optimizer step is forbidden")
    return numerator / denominator


def weighted_loss(weighted_losses: Iterable[tuple[Fraction, Fraction]]) -> Fraction:
    return combine_partials([partial(weighted_losses)])


def _fingerprint(row: dict) -> tuple:
    return (row["independent_unit_id"], row["split_group_id"], row["source_family_id"], row["view_id"],
            row["endpoint_id"], row["task_form"], tuple(row["requested_context_fields"]),
            row["target_bytes"], row["view_share"], row["endpoint_share"], row["effective_unit_mass"],
            row["token_normalization_id"])


def compare_candidates(candidates: Any) -> None:
    f.require(type(candidates) is dict and len(candidates) >= 2, "candidates", "at least two candidates required")
    reference = None
    for candidate, rows in candidates.items():
        f.text(candidate, "candidate")
        audit_rows(rows)
        current = Counter(_fingerprint(row) for row in rows if row["accepted"])
        if reference is None:
            reference = current
        else:
            f.require(current == reference, f"candidates.{candidate}",
                      "drop/rejection changed the frozen unit/view/target/weight population")


def validate_schedules(variants: Any, cycle_length: int) -> None:
    f.integer(cycle_length, "cycle_length", minimum=1)
    f.require(type(variants) is dict and variants, "variants", "schedule variants required")
    reference = None
    for name, rows in variants.items():
        f.text(name, "schedule_name")
        f.require(type(rows) is list and rows and len(rows) % cycle_length == 0, f"variants.{name}",
                  "schedule must contain one or more complete cycles")
        for boundary in range(cycle_length, len(rows) + 1, cycle_length):
            cycle = rows[boundary - cycle_length:boundary]
            audit_rows(cycle)
            signature = Counter(_fingerprint(row) for row in cycle if row["accepted"])
            if reference is None:
                reference = signature
            else:
                f.require(signature == reference, f"variants.{name}.boundary.{boundary}",
                          "every complete cycle must contain the identical multiset; only order may differ")


def eligible_stop_boundaries(total_rows: int, cycle_length: int) -> list[int]:
    f.integer(total_rows, "total_rows", minimum=1)
    f.integer(cycle_length, "cycle_length", minimum=1)
    f.require(total_rows % cycle_length == 0, "total_rows", "must end on a complete-cycle boundary")
    return list(range(cycle_length, total_rows + 1, cycle_length))


def resume_sequence(sequence: Any, cursor: int, completed_prefix: Any) -> list:
    f.require(type(sequence) is list, "sequence", "must be a list")
    f.integer(cursor, "cursor", minimum=0, maximum=len(sequence))
    f.require(type(completed_prefix) is list and completed_prefix == sequence[:cursor], "completed_prefix",
              "resume receipt does not match the exact completed sampler prefix")
    return list(sequence[cursor:])
