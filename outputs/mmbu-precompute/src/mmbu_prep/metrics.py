"""Offline arithmetic over supplied grades; no semantic judge or model evaluation.

The bootstrap estimates conditional, fixed-source uncertainty over independent
groups. It cannot establish uncertainty about the unknown hidden distribution.
"""

from collections import defaultdict
from math import floor, fsum, isfinite
import random


FIELDS = frozenset({"modality", "submodality", "specimen", "body_part", "stain", "medical_domain"})
TASKS = ("global_classification", "box_classification", "mask_classification", "detection")


def _grade(value):
    if not isinstance(value, (int, float)) or value not in (0, 1):
        raise ValueError("Grades must be explicit binary 0/1 values; missing grades cannot be dropped")
    return float(value)


def _validate(rows):
    if not isinstance(rows, list) or not rows:
        raise ValueError("A nonempty list of pregraded rows is required")
    seen = set()
    values = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Each pregraded row must be an object")
        for key in ("record_id", "source_id", "group_id", "task"):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise ValueError(f"Missing/non-string {key}")
        if row["record_id"] in seen:
            raise ValueError(f"Duplicate record_id: {row['record_id']}")
        seen.add(row["record_id"])
        if row["task"] not in (*TASKS, "counting"):
            raise ValueError(f"Unknown task: {row['task']}")
        context = row.get("context_correct")
        if not isinstance(context, dict) or not context:
            raise ValueError("Zero annotated context fields: official scoring policy remains unresolved")
        if not context.keys() <= FIELDS:
            raise ValueError("Unknown context field")
        values.append((_grade(row.get("adapted_correct")),
                       _grade(row.get("base_correct")),
                       fsum(_grade(v) for v in context.values()) / len(context)))
    return values


def _weights(count, weights):
    if weights is None:
        return [1.0 / count] * count
    if not isinstance(weights, (list, tuple)) or len(weights) != count:
        raise ValueError("Supply exactly one positive finite weight per row")
    try:
        invalid = any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) or v <= 0 for v in weights)
    except OverflowError as exc:
        raise ValueError("Weights exceed supported finite numeric range") from exc
    if invalid:
        raise ValueError("Weights must be positive finite numbers")
    scale = max(weights)
    scaled = [v / scale for v in weights]
    total = fsum(scaled)
    normalized = [v / total for v in scaled]
    if any(v <= 0 for v in normalized):
        raise ValueError("Weight range underflows; no example may silently lose its weight")
    return normalized


def _aggregate(values, weights):
    t, baseline, context = (fsum(v[j] * w for v, w in zip(values, weights)) for j in range(3))
    gain = t - baseline
    return {"T": t, "C": context, "T_base": baseline,
            "task_gain": gain, "S": (.8 * t + .2 * context) * gain}


def score_rows(rows, *, weights=None):
    """Compute the published product from explicit grades, retaining every row.

    Correctness decisions are the caller's supplied evidence. This function does
    not parse answers, adjudicate labels, or decide failed-output credit.
    """
    values = _validate(rows)
    result = _aggregate(values, _weights(len(rows), weights))
    result.update({"n_examples": len(rows),
                   "n_sources": len({r["source_id"] for r in rows}),
                   "n_groups": len({(r["source_id"], r["group_id"]) for r in rows}),
                   "label": "arithmetic_over_supplied_grades_not_official_evaluation"})
    return result


def source_balanced_weights(rows, *, task_weights=None):
    """Equal source weights within task, equal example weights within source/task.

    All four task groups must be represented. Counting belongs to global
    classification. The chosen weights are a development proxy, not hidden-set
    composition estimates.
    """
    _validate(rows)
    if task_weights is None:
        task_weights = dict.fromkeys(TASKS, .25)
    if not isinstance(task_weights, dict) or set(task_weights) != set(TASKS):
        raise ValueError("Explicit weights must name exactly the four task groups")
    normalized = dict(zip(TASKS, _weights(4, [task_weights[t] for t in TASKS])))
    group = lambda r: "global_classification" if r["task"] == "counting" else r["task"]
    sources = defaultdict(set)
    counts = defaultdict(int)
    for row in rows:
        task = group(row)
        sources[task].add(row["source_id"])
        counts[task, row["source_id"]] += 1
    if set(sources) != set(TASKS):
        raise ValueError("Missing task groups: report partial diagnostics, not a full-task proxy")
    return [normalized[group(r)] / len(sources[group(r)]) / counts[group(r), r["source_id"]] for r in rows]


def _quantile(sorted_values, probability):
    position = (len(sorted_values) - 1) * probability
    low = floor(position)
    high = min(low + 1, len(sorted_values) - 1)
    return sorted_values[low] + (sorted_values[high] - sorted_values[low]) * (position - low)


def paired_cluster_bootstrap(rows, *, iterations=1000, seed=0, confidence=.95, weights=None):
    """Resample groups within each source, preserving that source's weight mass.

    Base, adapted and context grades share every draw. A group includes all its
    rows. Supplied row weights are normalized within each sampled source; source
    masses stay fixed. Task masses may vary within source as groups are sampled.
    Sources must already be independently grouped by the lineage review; this
    function cannot detect common patients hidden behind different source IDs.
    """
    values = _validate(rows)
    row_weights = _weights(len(rows), weights)
    if type(iterations) is not int or iterations < 1:
        raise ValueError("iterations must be a positive integer")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    sources = defaultdict(lambda: defaultdict(list))
    for i, row in enumerate(rows):
        sources[row["source_id"]][row["group_id"]].append(i)
    source_mass = {source: fsum(row_weights[i] for indices in groups.values() for i in indices)
                   for source, groups in sources.items()}
    warnings = ["Conditional fixed-source group bootstrap; not unseen-source or training-seed uncertainty."]
    result = {"point": score_rows(rows, weights=row_weights), "interval": None,
              "confidence": confidence, "iterations": iterations, "seed": seed,
              "estimand": "adaptation_score_conditional_on_fixed_sources_and_supplied_grades",
              "groups_per_source": {s: len(g) for s, g in sorted(sources.items())}, "warnings": warnings}
    inadequate = [s for s, groups in sources.items() if len(groups) < 2]
    if inadequate:
        warnings.append("No interval: fewer than two independent groups in source(s): " + ", ".join(sorted(inadequate)))
        return result
    if any(len(g) < 10 for g in sources.values()):
        warnings.append("Few groups: percentile coverage may be poor; interval is exploratory.")
    if iterations < 200:
        warnings.append("Few bootstrap draws: interval endpoints have substantial Monte Carlo uncertainty.")
    rng = random.Random(seed)
    samples = []
    for _ in range(iterations):
        drawn_values, drawn_weights = [], []
        for source, groups in sorted(sources.items()):
            keys = sorted(groups)
            indices = [i for _ in keys for i in groups[rng.choice(keys)]]
            denominator = fsum(row_weights[i] for i in indices)
            drawn_values.extend(values[i] for i in indices)
            drawn_weights.extend((row_weights[i] / denominator) * source_mass[source] for i in indices)
        samples.append(_aggregate(drawn_values, drawn_weights)["S"])
    samples.sort()
    tail = (1 - confidence) / 2
    result["interval"] = [_quantile(samples, tail), _quantile(samples, 1 - tail)]
    return result
