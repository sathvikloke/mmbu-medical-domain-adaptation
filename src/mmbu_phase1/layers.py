"""Example manifest, the four immutable evaluation layers, and the execution-output manifest."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from mmbu_phase1 import canonical, fields as f, geometry, paths
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import PURPOSES

MANIFEST_KEYS = ("schema_id", "schema_version", "manifest_id", "contract_digest", "purpose", "population_id", "rows",
                 "created_at", "record_digest")
ROW_KEYS = ("example_id", "independent_unit_id", "task_family", "input_digest", "requested_context_fields", "task_weight",
            "image_width", "image_height", "task_target_digest", "context_target_digest", "box_policy",
            "target_boxes_digest")
TASK_FAMILIES = ("classification", "counting", "detection", "open_generation")
COMMON = ("schema_id", "schema_version", "record_id", "example_id", "example_manifest_digest", "contract_digest",
          "created_at", "record_digest")
RAW_KEYS = COMMON + ("experiment_digest", "execution_condition_digest", "request_digest", "input_digest",
                     "processor_digest", "prompt_schema_contract_digest", "evaluator_digest", "parser_digest",
                     "validator_digest", "judge_policy_digest", "token_ids", "decoded_text", "finish_reason",
                     "effective_generation_settings", "timing", "runtime_status")
PARSED_KEYS = COMMON + ("raw_digest", "parser_digest", "parse_status", "parsed_value")
VALIDATED_KEYS = COMMON + ("raw_digest", "parsed_digest", "validator_digest", "validation_status",
                           "requested_context_fields", "geometry_status", "validated_value")
JUDGED_KEYS = COMMON + ("raw_digest", "parsed_digest", "validated_digest", "judge_digest", "judge_status", "task_grade",
                        "context_grades", "terminal_outcome")
RUNTIME_STATUSES = ("succeeded", "load_failed", "preprocess_failed", "timeout", "oom", "generation_failed")
PARSE_STATUSES = ("parsed", "invalid_json", "duplicate_key", "nonfinite", "multiple_objects", "unknown_key",
                  "missing_required", "not_run")
VALIDATION_STATUSES = ("valid", "invalid_schema", "invalid_value", "invalid_geometry", "not_run")
GEOMETRY_STATUSES = ("valid", "invalid", "not_applicable", "not_run")
JUDGE_STATUSES = ("judged", "judge_failed", "not_run")
TERMINAL_OUTCOMES = ("success", "runtime_failure", "parse_failure", "validation_failure", "judge_failure")
OUTPUT_MANIFEST_KEYS = ("schema_id", "schema_version", "output_manifest_id", "experiment_digest",
                        "execution_condition_digest", "example_manifest_digest", "contract_digest", "entries",
                        "created_at", "record_digest")
ENTRY_KEYS = ("path", "bytes", "sha256", "media_type", "schema_id", "schema_version", "record_digest", "role",
              "example_id")
LAYER_ROLES = {"raw_output": "raw_output", "parsed_output": "parsed_output", "validated_output": "validated_output",
               "judged_output": "judged_output"}
ENTRY_ROLES = ("raw_output", "parsed_output", "validated_output", "judged_output", "failure", "log")
FORBIDDEN_ENTRY_SCHEMAS = frozenset(f.SCHEMA_PREFIX + name for name in (
    "execution_output_manifest", "evidence_manifest", "source_state", "reproducibility", "run", "claims",
    "requirement_trace", "phase_decision", "task_change_summary", "geometry_summary"))


def _ordered_fields(value: Any, path: str) -> list[str]:
    items = f.array(value, path)
    for index, item in enumerate(items):
        f.text(item, f"{path}[{index}]")
    f.require(len(items) == len(set(items)), path, "must be a duplicate-free ordered subset")
    return items


def validate_example_manifest(record: Any, path: str = "example_manifest") -> dict:
    f.record(record, "example_manifest", MANIFEST_KEYS, path)
    f.text(record["manifest_id"], f"{path}.manifest_id")
    f.digest(record["contract_digest"], f"{path}.contract_digest")
    f.one_of(record["purpose"], f"{path}.purpose", PURPOSES)
    f.text(record["population_id"], f"{path}.population_id")
    rows = f.array(record["rows"], f"{path}.rows", nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}.rows[{index}]"
        f.closed(row, label, ROW_KEYS)
        f.text(row["example_id"], f"{label}.example_id")
        f.text(row["independent_unit_id"], f"{label}.independent_unit_id")
        family = f.one_of(row["task_family"], f"{label}.task_family", TASK_FAMILIES)
        f.digest(row["input_digest"], f"{label}.input_digest")
        f.digest(row["task_target_digest"], f"{label}.task_target_digest")
        fields_ = _ordered_fields(row["requested_context_fields"], f"{label}.requested_context_fields")
        if fields_:
            f.digest(row["context_target_digest"], f"{label}.context_target_digest")
        else:
            f.require(row["context_target_digest"] is None, f"{label}.context_target_digest",
                      "non-null exactly when context fields are requested")
        f.number(row["task_weight"], f"{label}.task_weight", minimum=0, min_exclusive=True)
        if family == "detection":
            f.integer(row["image_width"], f"{label}.image_width", minimum=1)
            f.integer(row["image_height"], f"{label}.image_height", minimum=1)
            f.one_of(row["box_policy"], f"{label}.box_policy", ("single", "all_targets", "any_one"))
            f.digest(row["target_boxes_digest"], f"{label}.target_boxes_digest")
        else:
            f.require(row["image_width"] is None and row["image_height"] is None and row["target_boxes_digest"] is None,
                      label, "non-detection rows have null dimensions and target boxes")
            f.literal(row["box_policy"], f"{label}.box_policy", "not_applicable")
    for key in ("example_id", "independent_unit_id"):
        values = [row[key] for row in rows]
        f.require(len(values) == len(set(values)), f"{path}.rows", f"{key} values must be unique")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def target_boxes(store: RecordStore, row: dict, path: str = "target_boxes") -> list:
    value = canonical.loads_canonical(store.artifact(row["target_boxes_digest"], path))
    return geometry.check_targets(row["box_policy"], row["image_width"], row["image_height"], value, path)


def check_example_manifest(store: RecordStore, digest: Any, path: str = "example_manifest") -> dict:
    from mmbu_phase1 import prompt_contract

    record = validate_example_manifest(store.get(digest, "example_manifest", path), path)
    contract = prompt_contract.check_prompt_schema_contract(store, record["contract_digest"], f"{path}.contract_digest")
    registry = set(prompt_contract.field_registry(store, contract))
    for index, row in enumerate(record["rows"]):
        label = f"{path}.rows[{index}]"
        f.require(set(row["requested_context_fields"]) <= registry, f"{label}.requested_context_fields",
                  "must be a subset of the prompt contract's field registry")
        store.artifact(row["input_digest"], f"{label}.input_digest")
        store.artifact(row["task_target_digest"], f"{label}.task_target_digest")
        if row["context_target_digest"] is not None:
            target = canonical.loads_canonical(store.artifact(row["context_target_digest"], f"{label}.context_target_digest"))
            f.require(type(target) is dict and list(target) == sorted(row["requested_context_fields"], key=str.encode)
                      and set(target) == set(row["requested_context_fields"]), f"{label}.context_target_digest",
                      "context targets must cover exactly the requested fields")
        if row["task_family"] == "detection":
            target_boxes(store, row, f"{label}.target_boxes_digest")
    return record


# ---------------------------------------------------------------------------
# Layer records


def _common(record: dict, schema: str, keys: tuple, path: str) -> None:
    f.record(record, schema, keys, path)
    f.text(record["record_id"], f"{path}.record_id")
    f.text(record["example_id"], f"{path}.example_id")
    f.digest(record["example_manifest_digest"], f"{path}.example_manifest_digest")
    f.digest(record["contract_digest"], f"{path}.contract_digest")
    f.timestamp(record["created_at"], f"{path}.created_at")


def validate_raw_output(record: Any, path: str = "raw_output") -> dict:
    from mmbu_phase1.condition import validate_decoding

    _common(record, "raw_output", RAW_KEYS, path)
    for name in ("experiment_digest", "execution_condition_digest", "request_digest", "input_digest", "processor_digest",
                 "prompt_schema_contract_digest", "evaluator_digest", "parser_digest", "validator_digest",
                 "judge_policy_digest"):
        f.digest(record[name], f"{path}.{name}")
    status = f.one_of(record["runtime_status"], f"{path}.runtime_status", RUNTIME_STATUSES)
    tokens, text, finish = record["token_ids"], record["decoded_text"], record["finish_reason"]
    if status == "succeeded" or tokens is not None:
        items = f.array(tokens, f"{path}.token_ids")
        for index, token in enumerate(items):
            f.integer(token, f"{path}.token_ids[{index}]", minimum=0)
    if status == "succeeded" or text is not None:
        f.text(text, f"{path}.decoded_text", allow_empty=True)
    if status == "succeeded" or finish is not None:
        f.text(finish, f"{path}.finish_reason")
    validate_decoding(record["effective_generation_settings"], f"{path}.effective_generation_settings")
    timing = f.closed(record["timing"], f"{path}.timing", ("started_at", "ended_at", "latency_ms"))
    started = f.timestamp(timing["started_at"], f"{path}.timing.started_at")
    ended = f.timestamp(timing["ended_at"], f"{path}.timing.ended_at")
    f.require(ended >= started, f"{path}.timing", "ended_at must not precede started_at")
    f.number(timing["latency_ms"], f"{path}.timing.latency_ms", minimum=0)
    f.require(f.timestamp(record["created_at"], path) >= ended, f"{path}.created_at",
              "the raw record is written after generation ends")
    return record


def validate_parsed_output(record: Any, path: str = "parsed_output") -> dict:
    _common(record, "parsed_output", PARSED_KEYS, path)
    f.digest(record["raw_digest"], f"{path}.raw_digest")
    f.digest(record["parser_digest"], f"{path}.parser_digest")
    status = f.one_of(record["parse_status"], f"{path}.parse_status", PARSE_STATUSES)
    if status == "parsed":
        f.require(type(record["parsed_value"]) is dict, f"{path}.parsed_value", "a parsed value is a closed object")
    else:
        f.require(record["parsed_value"] is None, f"{path}.parsed_value", "null unless parse_status is parsed")
    return record


def validate_validated_output(record: Any, path: str = "validated_output") -> dict:
    _common(record, "validated_output", VALIDATED_KEYS, path)
    for name in ("raw_digest", "parsed_digest", "validator_digest"):
        f.digest(record[name], f"{path}.{name}")
    status = f.one_of(record["validation_status"], f"{path}.validation_status", VALIDATION_STATUSES)
    geometry_status = f.one_of(record["geometry_status"], f"{path}.geometry_status", GEOMETRY_STATUSES)
    _ordered_fields(record["requested_context_fields"], f"{path}.requested_context_fields")
    if status == "valid":
        f.require(type(record["validated_value"]) is dict, f"{path}.validated_value", "non-null only for valid")
    else:
        f.require(record["validated_value"] is None, f"{path}.validated_value", "non-null only for valid")
    f.require((status == "not_run") == (geometry_status == "not_run"), f"{path}.geometry_status",
              "geometry is not_run exactly when validation is not_run")
    return record


def validate_judged_output(record: Any, path: str = "judged_output") -> dict:
    _common(record, "judged_output", JUDGED_KEYS, path)
    for name in ("raw_digest", "parsed_digest", "validated_digest", "judge_digest"):
        f.digest(record[name], f"{path}.{name}")
    status = f.one_of(record["judge_status"], f"{path}.judge_status", JUDGE_STATUSES)
    outcome = f.one_of(record["terminal_outcome"], f"{path}.terminal_outcome", TERMINAL_OUTCOMES)
    if status == "judged":
        f.number(record["task_grade"], f"{path}.task_grade", minimum=0, maximum=1)
        grades = record["context_grades"]
        f.require(type(grades) is dict, f"{path}.context_grades", "a closed map when judged")
        for name, value in grades.items():
            f.number(value, f"{path}.context_grades.{name}", minimum=0, maximum=1)
        f.literal(outcome, f"{path}.terminal_outcome", "success")
    else:
        f.require(record["task_grade"] is None and record["context_grades"] is None, path,
                  "grades are null unless judged")
        f.require(outcome != "success", f"{path}.terminal_outcome", "only a judged row succeeds")
        if status == "judge_failed":
            f.literal(outcome, f"{path}.terminal_outcome", "judge_failure")
    return record


def terminal_outcome(raw: dict, parsed: dict, validated: dict, judged: dict) -> str:
    if raw["runtime_status"] != "succeeded":
        return "runtime_failure"
    if parsed["parse_status"] != "parsed":
        return "parse_failure"
    if validated["validation_status"] != "valid":
        return "validation_failure"
    return "success" if judged["judge_status"] == "judged" else "judge_failure"


def check_layer_chain(raw: dict, parsed: dict, validated: dict, judged: dict, row: dict, manifest: dict,
                      condition: dict, experiment: dict, path: str) -> None:
    """Parent-hash binding, orthogonal status flow, and no rewriting of any parent."""
    validate_raw_output(raw, f"{path}.raw")
    validate_parsed_output(parsed, f"{path}.parsed")
    validate_validated_output(validated, f"{path}.validated")
    validate_judged_output(judged, f"{path}.judged")
    for name, layer in (("raw", raw), ("parsed", parsed), ("validated", validated), ("judged", judged)):
        f.require(layer["example_id"] == row["example_id"], f"{path}.{name}.example_id", "names another example")
        f.require(layer["example_manifest_digest"] == manifest["record_digest"], f"{path}.{name}", "binds another manifest")
        f.require(layer["contract_digest"] == manifest["contract_digest"], f"{path}.{name}", "binds another contract")
    components = condition["components"]
    request_row = next(r for r in condition["request_set"]["rows"] if r["example_id"] == row["example_id"])
    f.require(raw["experiment_digest"] == experiment["record_digest"], f"{path}.raw.experiment_digest", "another experiment")
    f.require(raw["execution_condition_digest"] == condition["record_digest"], f"{path}.raw.execution_condition_digest",
              "another execution condition")
    f.require(raw["request_digest"] == canonical.value_digest(request_row), f"{path}.raw.request_digest",
              "must equal the condition's exact request row")
    f.require(raw["input_digest"] == request_row["input_digest"], f"{path}.raw.input_digest", "differs from the request row")
    f.require(raw["processor_digest"] == condition["processor"]["processor_digest"], f"{path}.raw.processor_digest",
              "differs from the condition processor")
    for name in ("prompt_schema_contract_digest", "evaluator_digest", "parser_digest", "validator_digest",
                 "judge_policy_digest"):
        f.require(raw[name] == components[name], f"{path}.raw.{name}", "differs from the condition components")
    f.require(f.same(raw["effective_generation_settings"], condition["decoding"]),
              f"{path}.raw.effective_generation_settings", "effective decoding drifted from the condition")
    started = f.timestamp(raw["timing"]["started_at"], path)
    f.require(started >= f.timestamp(condition["created_at"], path) and started >= f.timestamp(experiment["created_at"], path),
              f"{path}.raw.timing.started_at", "generation cannot precede the condition or experiment")
    f.require(parsed["raw_digest"] == raw["record_digest"], f"{path}.parsed.raw_digest", "stale or foreign raw parent")
    f.require(parsed["parser_digest"] == components["parser_digest"], f"{path}.parsed.parser_digest", "differs from condition")
    f.require(validated["raw_digest"] == raw["record_digest"] and validated["parsed_digest"] == parsed["record_digest"],
              f"{path}.validated", "stale or foreign parent digest")
    f.require(validated["validator_digest"] == components["validator_digest"], f"{path}.validated.validator_digest",
              "differs from condition")
    f.require(validated["requested_context_fields"] == row["requested_context_fields"],
              f"{path}.validated.requested_context_fields", "must equal the manifest row subset")
    f.require(judged["raw_digest"] == raw["record_digest"] and judged["parsed_digest"] == parsed["record_digest"]
              and judged["validated_digest"] == validated["record_digest"], f"{path}.judged", "stale or foreign ancestry")
    f.require(judged["judge_digest"] == components["judge_policy_digest"], f"{path}.judged.judge_digest", "differs from condition")
    times = [f.timestamp(layer["created_at"], path) for layer in (raw, parsed, validated, judged)]
    f.require(times == sorted(times), path, "each layer is created after its parent")
    if raw["runtime_status"] != "succeeded":
        f.require(parsed["parse_status"] == "not_run" and validated["validation_status"] == "not_run"
                  and judged["judge_status"] == "not_run", path, "a runtime failure forces downstream not_run")
    else:
        f.require(parsed["parse_status"] != "not_run", f"{path}.parsed", "a successful raw record requires a parse attempt")
        if parsed["parse_status"] == "parsed":
            f.require(validated["validation_status"] != "not_run", f"{path}.validated", "parsed requires a validation attempt")
        else:
            f.require(validated["validation_status"] == "not_run" and judged["judge_status"] == "not_run", path,
                      "a parse failure forces validation and judging to not_run")
        if validated["validation_status"] == "valid":
            f.require(judged["judge_status"] in {"judged", "judge_failed"}, f"{path}.judged", "valid requires a judge attempt")
            f.require(f.same(validated["validated_value"], parsed["parsed_value"]), f"{path}.validated.validated_value",
                      "validation cannot rewrite its parsed parent")
        elif validated["validation_status"] != "not_run":
            f.require(judged["judge_status"] == "not_run", f"{path}.judged", "a validation failure forces judge not_run")
    if validated["validation_status"] != "not_run":
        expected_geometry = {"valid", "invalid"} if row["task_family"] == "detection" else {"not_applicable"}
        f.require(validated["geometry_status"] in expected_geometry, f"{path}.validated.geometry_status",
                  "geometry status does not match the task family")
    f.require(judged["terminal_outcome"] == terminal_outcome(raw, parsed, validated, judged),
              f"{path}.judged.terminal_outcome", "terminal outcome does not follow the deterministic status flow")
    if judged["judge_status"] == "judged":
        f.require(set(judged["context_grades"]) == set(row["requested_context_fields"])
                  and len(judged["context_grades"]) == len(row["requested_context_fields"]),
                  f"{path}.judged.context_grades", "a closed map over exactly the requested fields")


# ---------------------------------------------------------------------------
# Execution-output manifest


def validate_execution_output_manifest(record: Any, path: str = "execution_output_manifest") -> dict:
    f.record(record, "execution_output_manifest", OUTPUT_MANIFEST_KEYS, path)
    f.text(record["output_manifest_id"], f"{path}.output_manifest_id")
    for name in ("experiment_digest", "execution_condition_digest", "example_manifest_digest", "contract_digest"):
        f.digest(record[name], f"{path}.{name}")
    entries = f.array(record["entries"], f"{path}.entries", nonempty=True)
    for index, entry in enumerate(entries):
        label = f"{path}.entries[{index}]"
        f.closed(entry, label, ENTRY_KEYS)
        paths.relative_path(entry["path"], f"{label}.path")
        f.integer(entry["bytes"], f"{label}.bytes", minimum=0)
        f.digest(entry["sha256"], f"{label}.sha256")
        f.text(entry["media_type"], f"{label}.media_type")
        role = f.one_of(entry["role"], f"{label}.role", ENTRY_ROLES)
        governed = [entry[name] is not None for name in ("schema_id", "schema_version", "record_digest")]
        f.require(all(governed) or not any(governed), label, "schema fields are all non-null or all null")
        if all(governed):
            f.text(entry["schema_id"], f"{label}.schema_id")
            f.literal(entry["schema_version"], f"{label}.schema_version", 1)
            f.digest(entry["record_digest"], f"{label}.record_digest")
            f.require(entry["schema_id"] not in FORBIDDEN_ENTRY_SCHEMAS, label,
                      "an output manifest never lists itself or a later provenance record")
        if role in LAYER_ROLES:
            f.require(all(governed) and entry["schema_id"] == f.SCHEMA_PREFIX + role, label,
                      "a per-example layer entry carries its exact layer schema")
            f.text(entry["example_id"], f"{label}.example_id")
        else:
            f.require(entry["example_id"] is None, f"{label}.example_id", "null for failures and logs")
            if role == "log":
                f.require(not any(governed), label, "raw logs carry null schema fields")
    f.sorted_unique(entries, f"{path}.entries", lambda e: e["path"].encode("utf-8"))
    paths.unique_paths([e["path"] for e in entries], f"{path}.entries")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def check_execution_output_manifest(store: RecordStore, digest: Any, read: Callable[[str], bytes],
                                    path: str = "execution_output_manifest") -> dict:
    """Bytes, schemas, complete four-layer populations, and transitive layer chains."""
    from mmbu_phase1 import experiment as experiments

    record = validate_execution_output_manifest(store.get(digest, "execution_output_manifest", path), path)
    experiment = experiments.validate_experiment(store.get(record["experiment_digest"], "experiment", path))
    condition = store.get(record["execution_condition_digest"], "execution_condition", path)
    f.require(experiment["execution_condition_digest"] == record["execution_condition_digest"], path,
              "condition differs from the consumed experiment")
    f.require(condition["request_set"]["example_manifest_digest"] == record["example_manifest_digest"], path,
              "example manifest differs from the condition")
    manifest = store.get(record["example_manifest_digest"], "example_manifest", path)
    f.require(manifest["contract_digest"] == record["contract_digest"] == condition["components"]["prompt_schema_contract_digest"],
              f"{path}.contract_digest", "must equal the manifest and condition prompt contract")
    by_role: dict[str, dict[str, dict]] = {role: {} for role in LAYER_ROLES}
    for entry in record["entries"]:
        data = read(entry["path"])
        f.require(len(data) == entry["bytes"] and canonical.raw_digest(data) == entry["sha256"], f"{path}.entries",
                  f"{entry['path']} bytes or SHA-256 differ from the entry")
        if entry["schema_id"] is None:
            continue
        layer = canonical.loads_canonical(data)
        f.require(type(layer) is dict and layer.get("schema_id") == entry["schema_id"], f"{path}.entries",
                  f"{entry['path']} schema differs from its entry")
        f.sealed(layer, entry["path"])
        f.require(layer["record_digest"] == entry["record_digest"], f"{path}.entries", "entry record digest mismatch")
        if entry["role"] in LAYER_ROLES:
            f.require(layer["example_id"] == entry["example_id"], f"{path}.entries", "entry example ID mismatch")
            f.require(entry["example_id"] not in by_role[entry["role"]], f"{path}.entries",
                      f"duplicate {entry['role']} for {entry['example_id']}")
            by_role[entry["role"]][entry["example_id"]] = layer
    ids = [row["example_id"] for row in manifest["rows"]]
    for role, layers_ in by_role.items():
        f.require(set(layers_) == set(ids), f"{path}.entries",
                  f"{role} population must equal the complete example-manifest population")
    for row in manifest["rows"]:
        example = row["example_id"]
        check_layer_chain(by_role["raw_output"][example], by_role["parsed_output"][example],
                          by_role["validated_output"][example], by_role["judged_output"][example], row, manifest,
                          condition, experiment, f"{path}[{example}]")
    return record


def layers_by_example(record: dict, read: Callable[[str], bytes]) -> dict[str, dict[str, dict]]:
    result: dict[str, dict[str, dict]] = {}
    for entry in record["entries"]:
        if entry["role"] in LAYER_ROLES:
            result.setdefault(entry["example_id"], {})[entry["role"]] = canonical.loads_canonical(read(entry["path"]))
    return result


def bundle_reader(root: Path) -> Callable[[str], bytes]:
    root = Path(root)
    return lambda relative: paths.member_bytes(root, relative)
