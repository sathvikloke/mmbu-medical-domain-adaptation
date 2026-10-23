"""``mmbu.phase1.geometry_summary`` and ``mmbu.phase1.task_change_summary`` records.

Both are created only after their condition manifests exist, never enter a
manifest they digest, and are recomputed from the immutable layers: geometry
from raw/parsed/validated (never the judge), task change from the judged layer
under the pre-output pairing contract.
"""

from __future__ import annotations

from typing import Any, Callable

from mmbu_phase1 import canonical, fields as f, geometry, layers, rational, task_change
from mmbu_phase1.store import RecordStore

GEOMETRY_KEYS = ("schema_id", "schema_version", "summary_id", "example_manifest_digest", "output_manifest_digest",
                 "validator_digest", "threshold", "rows", "created_at", "record_digest")
GEOMETRY_ROW_KEYS = ("example_id", "box_policy", "image_width", "image_height", "target_boxes_digest",
                     "predicted_boxes_digest", "target_count", "prediction_count", "boxes_valid", "matched_pairs",
                     "row_iou", "passed", "reason_code")
TASK_CHANGE_KEYS = ("schema_id", "schema_version", "summary_id", "pairing_contract_digest", "example_manifest_digest",
                    "base_run_digest", "adapted_run_digest", "base_output_manifest_digest",
                    "adapted_output_manifest_digest", "judge_policy_digest", "rows", "totals", "binary_summary",
                    "created_at", "record_digest")


def geometry_rows(store: RecordStore, manifest: dict, by_example: dict, threshold: Any) -> list[dict]:
    rows = []
    for row in manifest["rows"]:
        if row["task_family"] != "detection":
            continue
        targets = layers.target_boxes(store, row)
        layer = by_example[row["example_id"]]
        raw, parsed, validated = layer["raw_output"], layer["parsed_output"], layer["validated_output"]
        task_value = parsed["parsed_value"]["task"] if parsed["parse_status"] == "parsed" else None
        projected = geometry.project(policy=row["box_policy"], width=row["image_width"], height=row["image_height"],
                                     targets=targets, runtime_status=raw["runtime_status"],
                                     parse_status=parsed["parse_status"], task_value=task_value,
                                     validation_status=validated["validation_status"], threshold=threshold)
        rows.append({"example_id": row["example_id"], "box_policy": row["box_policy"], "image_width": row["image_width"],
                     "image_height": row["image_height"], "target_boxes_digest": row["target_boxes_digest"],
                     "target_count": len(targets), **projected})
    return rows


def validate_geometry_summary(record: Any, path: str = "geometry_summary") -> dict:
    f.record(record, "geometry_summary", GEOMETRY_KEYS, path)
    f.text(record["summary_id"], f"{path}.summary_id")
    for name in ("example_manifest_digest", "output_manifest_digest", "validator_digest"):
        f.digest(record[name], f"{path}.{name}")
    rational.from_wire(record["threshold"], f"{path}.threshold")
    rows = f.array(record["rows"], f"{path}.rows")
    for index, row in enumerate(rows):
        label = f"{path}.rows[{index}]"
        f.closed(row, label, GEOMETRY_ROW_KEYS)
        f.one_of(row["reason_code"], f"{label}.reason_code", geometry.REASON_CODES)
        f.boolean(row["passed"], f"{label}.passed")
        f.require(row["passed"] == (row["reason_code"] == "passed"), f"{label}.passed", "passed exactly for reason passed")
        if row["row_iou"] is not None:
            rational.from_wire(row["row_iou"], f"{label}.row_iou")
        if row["matched_pairs"] is not None:
            pairs = f.array(row["matched_pairs"], f"{label}.matched_pairs")
            for pair_index, pair in enumerate(pairs):
                f.closed(pair, f"{label}.matched_pairs[{pair_index}]", ("iou", "prediction_index", "target_index"))
                f.integer(pair["prediction_index"], f"{label}.matched_pairs[{pair_index}].prediction_index", minimum=0)
                f.integer(pair["target_index"], f"{label}.matched_pairs[{pair_index}].target_index", minimum=0)
                rational.from_wire(pair["iou"], f"{label}.matched_pairs[{pair_index}].iou")
            keys = [(p["prediction_index"], p["target_index"]) for p in pairs]
            f.require(keys == sorted(keys), f"{label}.matched_pairs", "pairs must be sorted by prediction then target index")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def check_geometry_summary(store: RecordStore, digest: Any, read: Callable[[str], bytes], *,
                           condition: dict, path: str = "geometry_summary") -> dict:
    record = validate_geometry_summary(store.get(digest, "geometry_summary", path), path)
    output = layers.validate_execution_output_manifest(store.get(record["output_manifest_digest"],
                                                                 "execution_output_manifest", path))
    f.require(output["example_manifest_digest"] == record["example_manifest_digest"], path,
              "summary and output manifest bind different example manifests")
    f.require(output["execution_condition_digest"] == condition["record_digest"], path, "output manifest binds another condition")
    f.require(record["validator_digest"] == condition["components"]["validator_digest"], f"{path}.validator_digest",
              "must equal the execution-condition validator")
    f.require(f.same(record["threshold"], condition["components"]["geometry_threshold"]), f"{path}.threshold",
              "must byte-equal the condition/prompt/validator/evaluator threshold")
    manifest = store.get(record["example_manifest_digest"], "example_manifest", path)
    expected = geometry_rows(store, manifest, layers.layers_by_example(output, read),
                             rational.from_wire(record["threshold"]))
    f.require(len(record["rows"]) == len(expected), f"{path}.rows", "every detection example appears exactly once")
    for index, (row, wanted) in enumerate(zip(record["rows"], expected)):
        f.require(f.same(row, wanted), f"{path}.rows[{index}]",
                  "geometry row does not equal the deterministic raw/parsed/validated projection")
    f.require(f.timestamp(record["created_at"], path) >= f.timestamp(output["created_at"], path), f"{path}.created_at",
              "a summary is created only after its condition manifest exists")
    return record


def validate_task_change_summary(record: Any, path: str = "task_change_summary") -> dict:
    f.record(record, "task_change_summary", TASK_CHANGE_KEYS, path)
    f.text(record["summary_id"], f"{path}.summary_id")
    for name in TASK_CHANGE_KEYS[3:10]:
        f.digest(record[name], f"{path}.{name}")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def judged_by_example(output: dict, read: Callable[[str], bytes]) -> dict[str, dict]:
    return {example: layer["judged_output"] for example, layer in layers.layers_by_example(output, read).items()}


def check_task_change_summary(store: RecordStore, digest: Any, read: Callable[[str], bytes], *, run_check: Callable,
                              path: str = "task_change_summary") -> dict:
    """Pairing predates every raw record; runs/manifests/conditions match; rows and totals recompute."""
    from mmbu_phase1 import condition as conditions

    record = validate_task_change_summary(store.get(digest, "task_change_summary", path), path)
    pairing = conditions.check_paired_condition_contract(store, record["pairing_contract_digest"],
                                                         f"{path}.pairing_contract_digest")
    condition = store.get(pairing["matched_conditions"]["execution_condition_digest"], "execution_condition", path)
    f.require(record["example_manifest_digest"] == pairing["example_manifest_digest"], f"{path}.example_manifest_digest",
              "differs from the pairing contract")
    f.require(record["judge_policy_digest"] == condition["components"]["judge_policy_digest"], f"{path}.judge_policy_digest",
              "must equal the execution-condition judge component")
    judged = {}
    earliest_raw = None
    for side in ("base", "adapted"):
        run = run_check(store, record[f"{side}_run_digest"], read, f"{path}.{side}_run_digest")
        f.require(run["experiment_digest"] == pairing[f"{side}_experiment_digest"], f"{path}.{side}_run_digest",
                  "run consumed an experiment outside the pairing contract (third experiment)")
        f.require(run["output_manifest_digest"] == record[f"{side}_output_manifest_digest"],
                  f"{path}.{side}_output_manifest_digest", "differs from the run's output manifest")
        f.require(run["execution_condition_digest"] == condition["record_digest"], f"{path}.{side}_run_digest",
                  "run binds a different execution condition")
        output = store.get(run["output_manifest_digest"], "execution_output_manifest", path)
        for example, layer in layers.layers_by_example(output, read).items():
            created = f.timestamp(layer["raw_output"]["created_at"], path)
            earliest_raw = created if earliest_raw is None else min(earliest_raw, created)
        judged[side] = judged_by_example(output, read)
    f.require(f.timestamp(pairing["created_at"], path) < earliest_raw, f"{path}.pairing_contract_digest",
              "the pairing contract must predate every governed raw output (late contract)")
    manifest = store.get(record["example_manifest_digest"], "example_manifest", path)
    policy = canonical.loads_canonical(store.artifact(record["judge_policy_digest"], f"{path}.judge_policy_digest"))
    rule = policy.get("binary_correctness")
    task_change.verify(record["rows"], record["totals"], record["binary_summary"], manifest["rows"],
                       judged["base"], judged["adapted"], rule, path)
    return record
