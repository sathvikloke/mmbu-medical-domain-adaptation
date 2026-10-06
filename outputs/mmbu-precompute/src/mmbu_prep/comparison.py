"""Joint, paired candidate arithmetic over aligned supplied correctness grades.

This module does not grade predictions, verify baseline identity, adjust for
multiple comparisons, select a winner, or estimate hidden-source performance.
"""

from collections import defaultdict
from collections.abc import Mapping
from itertools import combinations
from math import fsum
import random

from .metrics import _aggregate, _quantile, _validate, _weights


def _align(candidates: Mapping) -> tuple:
    if not isinstance(candidates, Mapping) or len(candidates) < 2:
        raise ValueError("Supply at least two named candidates")
    if any(not isinstance(name, str) or not name.strip() for name in candidates):
        raise ValueError("Candidate names must be nonempty strings")
    names = sorted(candidates)
    by_name, values_by_name = {}, {}
    for name in names:
        rows = candidates[name]
        try:
            values = _validate(rows)
        except ValueError as error:
            raise ValueError(f"Candidate {name!r}: {error}") from error
        by_name[name] = {row["record_id"]: row for row in rows}
        values_by_name[name] = {row["record_id"]: value for row, value in zip(rows, values)}

    reference = by_name[names[0]]
    record_ids = sorted(reference)
    for name in names[1:]:
        other = by_name[name]
        if set(other) != set(reference):
            missing = sorted(set(reference) - set(other))
            extra = sorted(set(other) - set(reference))
            raise ValueError(f"Candidate {name!r} record IDs do not align; missing={missing}, extra={extra}")
        for identifier in record_ids:
            for field in ("source_id", "group_id", "task"):
                if other[identifier][field] != reference[identifier][field]:
                    raise ValueError(f"Candidate {name!r}, record {identifier!r}: mismatched {field}")
            if set(other[identifier]["context_correct"]) != set(reference[identifier]["context_correct"]):
                raise ValueError(f"Candidate {name!r}, record {identifier!r}: mismatched context field coverage")
    values = {name: [values_by_name[name][identifier] for identifier in record_ids] for name in names}
    return names, record_ids, [reference[identifier] for identifier in record_ids], values


def compare_candidates(candidates: Mapping[str, list[dict]], *,
                       weights: Mapping[str, int | float] | None = None,
                       iterations: int = 1000, seed: int = 0,
                       confidence: float = .95) -> dict:
    """Compare aligned candidate adaptation scores on shared bootstrap draws.

    ``candidates`` maps at least two names to lists accepted by metrics.score_rows.
    Each candidate supplies its own base/adapted/context correctness grades.
    Record IDs, source/group/task assignments, and annotated context-field sets
    must match exactly. All inputs are left unchanged. Names and IDs are sorted
    lexicographically before weighting and resampling, so insertion order does
    not affect the result.

    ``weights`` is either None (equal row mass) or a mapping with exactly one
    positive finite weight for every aligned record ID. It is shared by all
    candidates. Each bootstrap draw samples complete groups within each fixed
    source and carries all candidates and their own baseline grades together.

    For each lexicographically ordered pair, delta_S is left S minus right S.
    Intervals are unadjusted empirical percentile intervals for that paired
    difference. They are exploratory; no winner or significance claim is made.
    If any source has fewer than two groups, every interval is withheld.
    """
    names, record_ids, reference_rows, values = _align(candidates)
    if type(iterations) is not int or iterations < 1:
        raise ValueError("iterations must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    if weights is not None:
        if not isinstance(weights, Mapping) or set(weights) != set(record_ids):
            raise ValueError("Weights must map exactly the aligned record IDs to positive finite numbers")
        row_weights = _weights(len(record_ids), [weights[identifier] for identifier in record_ids])
    else:
        row_weights = _weights(len(record_ids), None)

    scores = {name: _aggregate(values[name], row_weights) for name in names}
    pairs = [{"left": left, "right": right,
              "delta_S": scores[left]["S"] - scores[right]["S"], "interval": None}
             for left, right in combinations(names, 2)]
    sources = defaultdict(lambda: defaultdict(list))
    for index, row in enumerate(reference_rows):
        sources[row["source_id"]][row["group_id"]].append(index)
    source_mass = {source: fsum(row_weights[i] for indices in groups.values() for i in indices)
                   for source, groups in sources.items()}
    warnings = [
        "Conditional fixed-source group bootstrap; not unseen-source or training-seed uncertainty.",
        "Pairwise intervals are exploratory and unadjusted for multiplicity; confirmatory use requires "
        "predeclared comparisons and a separately justified multiplicity procedure.",
        "Supplied grades do not verify baseline/candidate identity, judge calibration, or grouping independence.",
    ]
    result = {
        "label": "joint_comparison_over_supplied_grades_not_official_evaluation",
        "official_evaluation": False,
        "inference": "exploratory_pairwise_comparison",
        "candidate_names": names,
        "record_ids": record_ids,
        "n_candidates": len(names),
        "n_examples": len(record_ids),
        "weighting": "uniform" if weights is None else "record_id_weights",
        "normalized_weights": dict(zip(record_ids, row_weights)),
        "candidates": scores,
        "pairwise": pairs,
        "bootstrap": {
            "confidence": confidence,
            "iterations": iterations,
            "seed": seed,
            "groups_per_source": {source: len(groups) for source, groups in sorted(sources.items())},
            "interval_type": "unadjusted_percentile",
            "multiplicity_adjusted": False,
            "estimand": "pairwise_adaptation_score_difference_conditional_on_fixed_sources_and_supplied_grades",
        },
        "warnings": warnings,
    }
    inadequate = sorted(source for source, groups in sources.items() if len(groups) < 2)
    if inadequate:
        warnings.append("No intervals: fewer than two independent groups in source(s): " + ", ".join(inadequate))
        return result
    if any(len(groups) < 10 for groups in sources.values()):
        warnings.append("Few groups: percentile coverage may be poor; intervals are exploratory.")
    if iterations < 200:
        warnings.append("Few bootstrap draws: interval endpoints have substantial Monte Carlo uncertainty.")

    rng = random.Random(seed)
    samples = [[] for _ in pairs]
    for _ in range(iterations):
        drawn_indices, drawn_weights = [], []
        for source, groups in sorted(sources.items()):
            keys = sorted(groups)
            indices = [index for _ in keys for index in groups[rng.choice(keys)]]
            denominator = fsum(row_weights[index] for index in indices)
            drawn_indices.extend(indices)
            # Form the within-source fraction first, avoiding a product of two
            # potentially very small global masses before division.
            drawn_weights.extend((row_weights[index] / denominator) * source_mass[source] for index in indices)
        drawn_scores = {name: _aggregate([values[name][index] for index in drawn_indices], drawn_weights)["S"]
                        for name in names}
        for pair, pair_samples in zip(pairs, samples):
            pair_samples.append(drawn_scores[pair["left"]] - drawn_scores[pair["right"]])
    tail = (1 - confidence) / 2
    for pair, pair_samples in zip(pairs, samples):
        pair_samples.sort()
        pair["interval"] = [_quantile(pair_samples, tail), _quantile(pair_samples, 1 - tail)]
    return result
