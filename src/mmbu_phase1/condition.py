"""``mmbu.phase1.execution_condition`` and ``mmbu.phase1.paired_condition_contract``.

The execution condition is the sole prospective non-model inference/evaluation
condition.  Every nested object is closed; completeness is transitive (policy,
example manifest, prompt contract, request artifacts, adapter specs), and a
pair may differ only in the fixed five-field model identity.
"""

from __future__ import annotations

from fractions import Fraction
import hashlib
import hmac
from typing import Any

from mmbu_phase1 import canonical, fields as f, rational
from mmbu_phase1.store import RecordStore

CONDITION_KEYS = (
    "schema_id",
    "schema_version",
    "condition_id",
    "environment_launch_policy_digest",
    "request_set",
    "components",
    "processor",
    "randomness",
    "decoding",
    "call_isolation",
    "failure_retry",
    "runtime",
    "batching",
    "precision_backend",
    "created_at",
    "record_digest",
)
OBJECT_NAMES = ("request_set", "components", "processor", "randomness", "decoding", "call_isolation",
                "failure_retry", "runtime", "batching", "precision_backend")
REQUEST_ROW_KEYS = ("example_id", "input_digest", "task_request_digest", "context_request_digest", "requested_context_fields")
COMPONENT_KEYS = ("prompt_schema_contract_digest", "evaluator_digest", "parser_digest", "validator_digest",
                  "judge_policy_digest", "geometry_threshold")
PROCESSOR_KEYS = ("processor_digest", "preprocessor_config_digest", "template_digest", "image_decoder_digest")
STREAM_KEYS = ("name", "seed", "algorithm", "version", "derivation", "parent_name")
DECODING_KEYS = ("decoding_method", "max_new_tokens", "temperature", "top_p", "top_k", "do_sample", "num_beams",
                 "num_return_sequences", "repetition_penalty", "stop_token_ids", "cache_enabled")
ISOLATION_KEYS = ("mode", "fresh_state_per_call", "conversation_reuse", "kv_cache_reuse",
                  "task_receives_context_output", "context_receives_task_output", "cross_call_allowed_fields")
RETRY_KEYS = ("terminal_rules", "retry_mode", "maximum_attempts", "retryable_outcomes")
TERMINAL_RULE_KEYS = ("terminal_outcome", "retain_row", "grade_contribution")
TERMINAL_FAILURES = ("judge_failure", "parse_failure", "runtime_failure", "validation_failure")
RUNTIME_KEYS = ("os", "architecture", "python_executable_digest", "python_version", "locale", "timezone", "filesystem",
                "software", "environment_variables", "devices", "topology", "cache_network")
SOFTWARE_KEYS = ("name", "version", "artifact_digest")
DEVICE_KEYS = ("device_id", "device_type", "model", "ordinal", "memory_bytes")
TOPOLOGY_KEYS = ("world_size", "node_count", "process_count", "launcher", "visible_device_order")
CACHE_KEYS = ("cache_root_digests", "snapshot_digests", "offline_requested", "network_denied", "remote_request_count",
              "hidden_fetch_count", "request_log_digest")
BATCHING_KEYS = ("batch_size", "shuffle", "drop_last", "worker_count", "row_order", "batches", "padding_side",
                 "padding_policy", "truncation", "max_input_tokens", "remainder_policy", "image_order")
PRECISION_KEYS = ("parameter_dtype", "compute_dtype", "autocast_dtype", "tf32", "deterministic_algorithms",
                  "cudnn_benchmark", "attention_backend", "kernel_digests", "compile_mode", "fallbacks", "cache_backend")
DTYPES = ("float32", "bfloat16", "float16")
PAIR_KEYS = ("schema_id", "schema_version", "pairing_id", "base_experiment_digest", "adapted_experiment_digest",
             "example_manifest_digest", "matched_conditions", "base_model_identity", "adapted_model_identity",
             "allowed_difference_fields", "created_at", "record_digest")
MATCHED_FIELDS = ("purpose", "authorization_registry_digest", "source_record_digests", "purpose_authorization_digests",
                  "source_manifest_digests", "split_manifest_digests", "non_model_lineage_root_digests",
                  "non_model_decision_execution_receipt_digests", "execution_condition_digest", "prospective_lock_digest",
                  "decision_function_digest")
IDENTITY_FIELDS = ("adapted_from_model_digest", "candidate_ids", "model_digest", "model_lineage_root_digests",
                   "model_selection_receipt_digests")
SYNTHETIC_THRESHOLD = {"denominator": 2, "numerator": 1}


def _ordered_unique(value: Any, path: str) -> list[str]:
    items = f.array(value, path)
    for index, item in enumerate(items):
        f.text(item, f"{path}[{index}]")
    f.require(len(items) == len(set(items)), path, "must be duplicate-free")
    return items


def validate_request_set(value: Any, path: str) -> dict:
    f.closed(value, path, ("example_manifest_digest", "rows"))
    f.digest(value["example_manifest_digest"], f"{path}.example_manifest_digest")
    rows = f.array(value["rows"], f"{path}.rows", nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}.rows[{index}]"
        f.closed(row, label, REQUEST_ROW_KEYS)
        f.text(row["example_id"], f"{label}.example_id")
        f.digest(row["input_digest"], f"{label}.input_digest")
        f.digest(row["task_request_digest"], f"{label}.task_request_digest")
        fields_ = _ordered_unique(row["requested_context_fields"], f"{label}.requested_context_fields")
        if fields_:
            f.digest(row["context_request_digest"], f"{label}.context_request_digest")
        else:
            f.require(row["context_request_digest"] is None, f"{label}.context_request_digest",
                      "null exactly when no context fields are requested")
    ids = [row["example_id"] for row in rows]
    f.require(len(ids) == len(set(ids)), f"{path}.rows", "example IDs must be unique")
    return value


def validate_components(value: Any, path: str) -> dict:
    f.closed(value, path, COMPONENT_KEYS)
    for name in COMPONENT_KEYS[:-1]:
        f.digest(value[name], f"{path}.{name}")
    rational.from_wire(value["geometry_threshold"], f"{path}.geometry_threshold")
    return value


def validate_processor(value: Any, path: str) -> dict:
    f.closed(value, path, PROCESSOR_KEYS)
    f.digest(value["processor_digest"], f"{path}.processor_digest")
    f.digest(value["preprocessor_config_digest"], f"{path}.preprocessor_config_digest")
    f.nullable(f.digest, value["template_digest"], f"{path}.template_digest")
    f.nullable(f.digest, value["image_decoder_digest"], f"{path}.image_decoder_digest")
    return value


def derive_seed(parent_seed: int, namespace: str, name: str) -> int:
    key = parent_seed.to_bytes(8, "big")
    message = (namespace + "\x00" + name).encode("utf-8")
    return int.from_bytes(hmac.new(key, message, hashlib.sha256).digest()[:8], "big")


def validate_randomness(value: Any, path: str) -> dict:
    f.closed(value, path, ("seed_namespace", "streams"))
    namespace = f.text(value["seed_namespace"], f"{path}.seed_namespace")
    streams = f.array(value["streams"], f"{path}.streams", nonempty=True)
    for index, stream in enumerate(streams):
        label = f"{path}.streams[{index}]"
        f.closed(stream, label, STREAM_KEYS)
        f.text(stream["name"], f"{label}.name")
        f.integer(stream["seed"], f"{label}.seed", minimum=0, maximum=2 ** 64 - 1)
        f.text(stream["algorithm"], f"{label}.algorithm")
        f.text(stream["version"], f"{label}.version")
        derivation = f.one_of(stream["derivation"], f"{label}.derivation", ("direct", "hmac_sha256"))
        if derivation == "direct":
            f.require(stream["parent_name"] is None, f"{label}.parent_name", "direct derivation has a null parent")
        else:
            f.text(stream["parent_name"], f"{label}.parent_name")
    f.sorted_unique(streams, f"{path}.streams", lambda s: s["name"].encode("utf-8"))
    by_name = {s["name"]: s for s in streams}
    f.require("generation" in by_name, f"{path}.streams", "must include the generation stream")
    for stream in streams:
        if stream["derivation"] == "hmac_sha256":
            parent = by_name.get(stream["parent_name"])
            f.require(parent is not None and parent["name"] != stream["name"], f"{path}.streams[{stream['name']}]",
                      "HMAC derivation requires another listed parent stream")
            f.require(stream["seed"] == derive_seed(parent["seed"], namespace, stream["name"]),
                      f"{path}.streams[{stream['name']}].seed", "does not equal the HMAC-SHA-256 derivation")
    for stream in streams:
        seen, cursor = set(), stream
        while cursor["parent_name"] is not None:
            f.require(cursor["name"] not in seen, f"{path}.streams", "parent graph must be acyclic")
            seen.add(cursor["name"])
            cursor = by_name[cursor["parent_name"]]
    return value


def validate_decoding(value: Any, path: str) -> dict:
    f.closed(value, path, DECODING_KEYS)
    method = f.one_of(value["decoding_method"], f"{path}.decoding_method", ("greedy", "sampling", "beam"))
    f.integer(value["max_new_tokens"], f"{path}.max_new_tokens", minimum=1)
    beams = f.integer(value["num_beams"], f"{path}.num_beams", minimum=1)
    returns = f.integer(value["num_return_sequences"], f"{path}.num_return_sequences", minimum=1)
    sample = f.boolean(value["do_sample"], f"{path}.do_sample")
    f.number(value["repetition_penalty"], f"{path}.repetition_penalty", minimum=0, min_exclusive=True)
    stops = f.array(value["stop_token_ids"], f"{path}.stop_token_ids")
    for index, token in enumerate(stops):
        f.integer(token, f"{path}.stop_token_ids[{index}]", minimum=0)
    f.require(stops == sorted(set(stops)), f"{path}.stop_token_ids", "must be unique and sorted")
    f.boolean(value["cache_enabled"], f"{path}.cache_enabled")
    scalars = ("temperature", "top_p", "top_k")
    if method == "greedy":
        f.require(not sample and beams == 1 and returns == 1, path, "greedy requires do_sample=false and one beam/sequence")
        f.require(all(value[name] is None for name in scalars), path, "greedy requires null temperature/top_p/top_k")
    elif method == "sampling":
        f.require(sample and beams == 1 and returns == 1, path, "sampling requires do_sample=true and one beam/sequence")
        f.number(value["temperature"], f"{path}.temperature", minimum=0, min_exclusive=True)
        f.number(value["top_p"], f"{path}.top_p", minimum=0, maximum=1, min_exclusive=True)
        f.integer(value["top_k"], f"{path}.top_k", minimum=0)
    else:
        f.require(not sample and beams >= 2 and returns <= beams, path,
                  "beam requires do_sample=false, num_beams>=2, num_return_sequences<=num_beams")
        f.require(all(value[name] is None for name in scalars), path, "beam requires null sampling scalars")
    return value


def validate_call_isolation(value: Any, path: str) -> dict:
    f.closed(value, path, ISOLATION_KEYS)
    f.literal(value["mode"], f"{path}.mode", "separate_task_and_context")
    f.literal(value["fresh_state_per_call"], f"{path}.fresh_state_per_call", True)
    for name in ("conversation_reuse", "kv_cache_reuse", "task_receives_context_output", "context_receives_task_output"):
        f.literal(value[name], f"{path}.{name}", False)
    f.require(value["cross_call_allowed_fields"] == [] and type(value["cross_call_allowed_fields"]) is list,
              f"{path}.cross_call_allowed_fields", "must be empty")
    return value


def validate_failure_retry(value: Any, path: str) -> dict:
    f.closed(value, path, RETRY_KEYS)
    rules = f.array(value["terminal_rules"], f"{path}.terminal_rules")
    for index, rule in enumerate(rules):
        label = f"{path}.terminal_rules[{index}]"
        f.closed(rule, label, TERMINAL_RULE_KEYS)
        f.one_of(rule["terminal_outcome"], f"{label}.terminal_outcome", TERMINAL_FAILURES)
        f.literal(rule["retain_row"], f"{label}.retain_row", True)
        rational.require(rule["grade_contribution"], Fraction(0), f"{label}.grade_contribution")
    f.sorted_unique(rules, f"{path}.terminal_rules", lambda r: r["terminal_outcome"].encode())
    f.require([r["terminal_outcome"] for r in rules] == list(TERMINAL_FAILURES), f"{path}.terminal_rules",
              "exactly one row for each terminal failure outcome")
    f.literal(value["retry_mode"], f"{path}.retry_mode", "none")
    f.literal(value["maximum_attempts"], f"{path}.maximum_attempts", 1)
    f.require(value["retryable_outcomes"] == [] and type(value["retryable_outcomes"]) is list,
              f"{path}.retryable_outcomes", "Phase 1A permits no retryable outcome")
    return value


def validate_runtime(value: Any, path: str) -> dict:
    f.closed(value, path, RUNTIME_KEYS)
    f.one_of(value["os"], f"{path}.os", ("linux", "darwin"))
    for name in ("architecture", "python_version", "locale", "timezone", "filesystem"):
        f.text(value[name], f"{path}.{name}")
    f.digest(value["python_executable_digest"], f"{path}.python_executable_digest")
    software = f.array(value["software"], f"{path}.software", nonempty=True)
    for index, item in enumerate(software):
        f.closed(item, f"{path}.software[{index}]", SOFTWARE_KEYS)
        f.text(item["name"], f"{path}.software[{index}].name")
        f.text(item["version"], f"{path}.software[{index}].version")
        f.digest(item["artifact_digest"], f"{path}.software[{index}].artifact_digest")
    f.sorted_unique(software, f"{path}.software", lambda s: s["name"].encode("utf-8"))
    env = f.array(value["environment_variables"], f"{path}.environment_variables", nonempty=True)
    for index, row in enumerate(env):
        f.closed(row, f"{path}.environment_variables[{index}]", ("name", "value"))
        f.text(row["name"], f"{path}.environment_variables[{index}].name")
        f.text(row["value"], f"{path}.environment_variables[{index}].value", allow_empty=True)
    f.sorted_unique(env, f"{path}.environment_variables", lambda r: r["name"].encode("utf-8"))
    devices = f.array(value["devices"], f"{path}.devices", nonempty=True)
    for index, device in enumerate(devices):
        label = f"{path}.devices[{index}]"
        f.closed(device, label, DEVICE_KEYS)
        f.text(device["device_id"], f"{label}.device_id")
        f.one_of(device["device_type"], f"{label}.device_type", ("cpu", "cuda", "mps"))
        f.text(device["model"], f"{label}.model")
        f.integer(device["ordinal"], f"{label}.ordinal", minimum=0)
        f.nullable(f.integer, device["memory_bytes"], f"{label}.memory_bytes", minimum=0)
    f.sorted_unique(devices, f"{path}.devices", lambda d: d["device_id"].encode("utf-8"))
    topology = f.closed(value["topology"], f"{path}.topology", TOPOLOGY_KEYS)
    for name in ("world_size", "node_count", "process_count"):
        f.integer(topology[name], f"{path}.topology.{name}", minimum=1)
    if topology["process_count"] == 1:
        f.require(topology["launcher"] is None, f"{path}.topology.launcher", "null exactly for one process")
    else:
        f.text(topology["launcher"], f"{path}.topology.launcher")
    order = _ordered_unique(topology["visible_device_order"], f"{path}.topology.visible_device_order")
    f.require(set(order) <= {d["device_id"] for d in devices}, f"{path}.topology.visible_device_order",
              "visible devices must be declared devices")
    cache = f.closed(value["cache_network"], f"{path}.cache_network", CACHE_KEYS)
    f.digest_set(cache["cache_root_digests"], f"{path}.cache_network.cache_root_digests")
    f.digest_set(cache["snapshot_digests"], f"{path}.cache_network.snapshot_digests")
    f.boolean(cache["offline_requested"], f"{path}.cache_network.offline_requested")
    denied = f.boolean(cache["network_denied"], f"{path}.cache_network.network_denied")
    remote = f.integer(cache["remote_request_count"], f"{path}.cache_network.remote_request_count", minimum=0)
    hidden = f.integer(cache["hidden_fetch_count"], f"{path}.cache_network.hidden_fetch_count", minimum=0)
    if cache["request_log_digest"] is None:
        f.require(denied and remote == 0 and hidden == 0, f"{path}.cache_network.request_log_digest",
                  "null only when network is denied and both counts are zero")
    else:
        f.digest(cache["request_log_digest"], f"{path}.cache_network.request_log_digest")
    # Phase 1A: one CPU device, one node/process/world, offline, denied, zero fetches.
    f.require(len(devices) == 1 and devices[0]["device_type"] == "cpu", f"{path}.devices", "Phase 1A requires one CPU device")
    f.require(topology["world_size"] == topology["node_count"] == topology["process_count"] == 1,
              f"{path}.topology", "Phase 1A requires one node, process, and world")
    f.require(order == [devices[0]["device_id"]], f"{path}.topology.visible_device_order", "must list the one device")
    f.require(cache["offline_requested"] and denied and remote == 0 and hidden == 0, f"{path}.cache_network",
              "Phase 1A requires offline, network-denied execution with zero remote or hidden fetches")
    return value


def validate_batching(value: Any, path: str, request_ids: list[str] | None = None) -> dict:
    f.closed(value, path, BATCHING_KEYS)
    size = f.integer(value["batch_size"], f"{path}.batch_size", minimum=1)
    f.literal(value["shuffle"], f"{path}.shuffle", False)
    f.literal(value["drop_last"], f"{path}.drop_last", False)
    f.literal(value["worker_count"], f"{path}.worker_count", 0)
    order = _ordered_unique(value["row_order"], f"{path}.row_order")
    batches = f.array(value["batches"], f"{path}.batches", nonempty=True)
    flat = []
    for index, batch in enumerate(batches):
        members = f.array(batch, f"{path}.batches[{index}]", nonempty=True)
        for item in members:
            f.text(item, f"{path}.batches[{index}]")
        f.require(len(members) <= size, f"{path}.batches[{index}]", "batch exceeds batch_size")
        if index < len(batches) - 1:
            f.require(len(members) == size, f"{path}.batches[{index}]", "only the final batch may be short")
        flat.extend(members)
    f.require(flat == order, f"{path}.batches", "batches must exactly partition row_order in order")
    f.one_of(value["padding_side"], f"{path}.padding_side", ("left", "right"))
    f.one_of(value["padding_policy"], f"{path}.padding_policy", ("no_padding", "pad_to_longest"))
    truncation = f.boolean(value["truncation"], f"{path}.truncation")
    if truncation:
        f.integer(value["max_input_tokens"], f"{path}.max_input_tokens", minimum=1)
    else:
        f.require(value["max_input_tokens"] is None, f"{path}.max_input_tokens", "null exactly without truncation")
    remainder = f.one_of(value["remainder_policy"], f"{path}.remainder_policy", ("keep", "error"))
    if remainder == "error":
        f.require(len(order) % size == 0, f"{path}.remainder_policy", "a remainder exists under the error policy")
    f.literal(value["image_order"], f"{path}.image_order", "manifest_order")
    if request_ids is not None:
        f.require(order == request_ids, f"{path}.row_order", "must equal the request-set order")
    return value


def validate_precision_backend(value: Any, path: str, decoding: dict | None = None) -> dict:
    f.closed(value, path, PRECISION_KEYS)
    f.one_of(value["parameter_dtype"], f"{path}.parameter_dtype", DTYPES)
    f.one_of(value["compute_dtype"], f"{path}.compute_dtype", DTYPES)
    f.nullable(f.one_of, value["autocast_dtype"], f"{path}.autocast_dtype", allowed=DTYPES)
    f.nullable(f.boolean, value["tf32"], f"{path}.tf32")
    f.boolean(value["deterministic_algorithms"], f"{path}.deterministic_algorithms")
    f.nullable(f.boolean, value["cudnn_benchmark"], f"{path}.cudnn_benchmark")
    f.one_of(value["attention_backend"], f"{path}.attention_backend", ("eager", "sdpa"))
    f.digest_set(value["kernel_digests"], f"{path}.kernel_digests")
    f.string_set(value["fallbacks"], f"{path}.fallbacks")
    f.literal(value["compile_mode"], f"{path}.compile_mode", "disabled")
    f.one_of(value["cache_backend"], f"{path}.cache_backend", ("none", "dynamic"))
    expected = {"parameter_dtype": "float32", "compute_dtype": "float32", "autocast_dtype": None, "tf32": None,
                "deterministic_algorithms": True, "cudnn_benchmark": None, "attention_backend": "eager",
                "kernel_digests": [], "fallbacks": []}
    for name, wanted in expected.items():
        f.require(f.same(value[name], wanted), f"{path}.{name}", f"Phase 1A CPU requires {wanted!r}")
    if decoding is not None:
        wanted = "dynamic" if decoding["cache_enabled"] else "none"
        f.require(value["cache_backend"] == wanted, f"{path}.cache_backend", "must match decoding.cache_enabled")
    return value


def validate_condition_objects(objects: Any, path: str) -> dict:
    """Validate the ten closed condition objects and their cross-object rules."""
    f.closed(objects, path, OBJECT_NAMES)
    request_set = validate_request_set(objects["request_set"], f"{path}.request_set")
    validate_components(objects["components"], f"{path}.components")
    validate_processor(objects["processor"], f"{path}.processor")
    validate_randomness(objects["randomness"], f"{path}.randomness")
    decoding = validate_decoding(objects["decoding"], f"{path}.decoding")
    validate_call_isolation(objects["call_isolation"], f"{path}.call_isolation")
    validate_failure_retry(objects["failure_retry"], f"{path}.failure_retry")
    validate_runtime(objects["runtime"], f"{path}.runtime")
    validate_batching(objects["batching"], f"{path}.batching", [row["example_id"] for row in request_set["rows"]])
    validate_precision_backend(objects["precision_backend"], f"{path}.precision_backend", decoding)
    return objects


def validate_execution_condition(record: Any, path: str = "execution_condition") -> dict:
    f.record(record, "execution_condition", CONDITION_KEYS, path)
    f.text(record["condition_id"], f"{path}.condition_id")
    f.digest(record["environment_launch_policy_digest"], f"{path}.environment_launch_policy_digest")
    validate_condition_objects({name: record[name] for name in OBJECT_NAMES}, path)
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def check_execution_condition(store: RecordStore, digest: Any, path: str = "execution_condition") -> dict:
    """Transitive completeness: policy, manifest, contract, requests, and adapters all match."""
    from mmbu_phase1 import environment, layers, prompt_contract

    condition = validate_execution_condition(store.get(digest, "execution_condition", path), path)
    policy = environment.validate_environment_launch_policy(
        store.get(condition["environment_launch_policy_digest"], "environment_launch_policy",
                  f"{path}.environment_launch_policy_digest"))
    runtime = condition["runtime"]
    projection = environment.projection(policy)
    f.require(f.same(runtime["environment_variables"], projection), f"{path}.runtime.environment_variables",
              "must byte-equal the policy name/value projection")
    env = {row["name"]: row["value"] for row in projection}
    f.require(runtime["os"] == policy["platform"], f"{path}.runtime.os", "must equal the policy platform")
    f.require(runtime["python_executable_digest"] == policy["python_executable_digest"],
              f"{path}.runtime.python_executable_digest", "must equal the policy executable digest")
    f.require(runtime["locale"] == env["LC_ALL"] == env["LANG"], f"{path}.runtime.locale", "must equal LC_ALL/LANG")
    f.require(runtime["timezone"] == env["TZ"], f"{path}.runtime.timezone", "must equal TZ")
    f.require(f.timestamp(condition["created_at"], path) >= f.timestamp(policy["created_at"], path), f"{path}.created_at",
              "the condition cannot predate its environment-launch policy")
    manifest = layers.check_example_manifest(store, condition["request_set"]["example_manifest_digest"],
                                             f"{path}.request_set.example_manifest_digest")
    rows = condition["request_set"]["rows"]
    f.require(len(rows) == len(manifest["rows"]), f"{path}.request_set.rows", "must cover the example manifest exactly")
    for index, (row, example) in enumerate(zip(rows, manifest["rows"])):
        label = f"{path}.request_set.rows[{index}]"
        f.require(row["example_id"] == example["example_id"], label, "example order differs from the manifest")
        f.require(row["input_digest"] == example["input_digest"], label, "input digest differs from the manifest")
        f.require(row["requested_context_fields"] == example["requested_context_fields"], label,
                  "requested context fields differ from the manifest")
        _check_request(store, row, example, label)
    contract = prompt_contract.check_prompt_schema_contract(
        store, condition["components"]["prompt_schema_contract_digest"], f"{path}.components.prompt_schema_contract_digest")
    f.require(manifest["contract_digest"] == contract["record_digest"], f"{path}.components",
              "example manifest binds another prompt/schema contract")
    components = condition["components"]
    for name in ("parser_digest", "validator_digest", "judge_policy_digest"):
        f.require(components[name] == contract[name], f"{path}.components.{name}", "must equal the prompt contract")
    f.require(f.same(components["geometry_threshold"], contract["geometry_threshold"]),
              f"{path}.components.geometry_threshold", "must equal the prompt-contract geometry threshold")
    if contract["contract_status"] == "synthetic":
        f.require(f.same(components["geometry_threshold"], SYNTHETIC_THRESHOLD), f"{path}.components.geometry_threshold",
                  "the synthetic suite fixes the threshold to exactly 1/2")
    for name in ("evaluator_digest", "validator_digest"):
        spec = canonical.loads_canonical(store.artifact(components[name], f"{path}.components.{name}"))
        f.require(type(spec) is dict and f.same(spec.get("geometry_threshold"), components["geometry_threshold"]),
                  f"{path}.components.{name}", "adapter specification threshold differs from the condition")
    store.artifact(components["parser_digest"], f"{path}.components.parser_digest")
    store.artifact(components["judge_policy_digest"], f"{path}.components.judge_policy_digest")
    f.require(contract["inference_settings_digest"] == prompt_contract.inference_settings_digest(condition),
              f"{path}.prompt_contract.inference_settings_digest", "does not recompute from the condition projection")
    processor = condition["processor"]
    for name in ("processor_digest", "preprocessor_config_digest"):
        store.artifact(processor[name], f"{path}.processor.{name}")
    prompt = canonical.loads_canonical(store.artifact(contract["task_prompt_digest"], f"{path}.task_prompt"))
    if processor["template_digest"] is None:
        f.require(prompt.get("template_required") is False, f"{path}.processor.template_digest",
                  "null only when the prompt contract declares no template")
    else:
        store.artifact(processor["template_digest"], f"{path}.processor.template_digest")
    image_requests = any(_request(store, row["task_request_digest"]).get("input", {}).get("kind", "").endswith(
        "image_descriptor") for row in rows)
    if processor["image_decoder_digest"] is None:
        f.require(not image_requests, f"{path}.processor.image_decoder_digest", "null only when every request is non-image")
    else:
        store.artifact(processor["image_decoder_digest"], f"{path}.processor.image_decoder_digest")
    return condition


def _request(store: RecordStore, digest: str) -> dict:
    value = canonical.loads_canonical(store.artifact(digest, "request"))
    f.require(type(value) is dict, "request", "serialized request must be an object")
    return value


def _check_request(store: RecordStore, row: dict, example: dict, path: str) -> None:
    task = _request(store, row["task_request_digest"])
    f.closed(task, f"{path}.task_request", ("call", "input", "input_digest", "prompt_digest", "output_schema_digest",
                                            "task_family", "box_policy"))
    f.require(task["call"] == "task" and task["input_digest"] == row["input_digest"]
              and canonical.value_digest(task["input"]) == row["input_digest"], f"{path}.task_request",
              "task request must serialize only this example's input")
    f.require(task["task_family"] == example["task_family"] and task["box_policy"] == example["box_policy"],
              f"{path}.task_request", "task request instructions differ from the manifest")
    if row["context_request_digest"] is not None:
        context = _request(store, row["context_request_digest"])
        f.closed(context, f"{path}.context_request", ("call", "input", "input_digest", "prompt_digest",
                                                      "output_schema_digest", "requested_context_fields"))
        f.require(context["call"] == "context" and context["input_digest"] == row["input_digest"]
                  and context["requested_context_fields"] == row["requested_context_fields"], f"{path}.context_request",
                  "context request must serialize only this example's input and requested fields")
    for target in (example["task_target_digest"], example["context_target_digest"], example["target_boxes_digest"]):
        if target is not None:
            for request_digest in (row["task_request_digest"], row["context_request_digest"]):
                if request_digest is not None:
                    f.require(target.encode() not in store.artifact(request_digest), path,
                              "a request leaks a target digest")


# ---------------------------------------------------------------------------
# Paired base/adapted condition contract


def validate_paired_condition_contract(record: Any, path: str = "paired_condition_contract") -> dict:
    f.record(record, "paired_condition_contract", PAIR_KEYS, path)
    f.text(record["pairing_id"], f"{path}.pairing_id")
    for name in ("base_experiment_digest", "adapted_experiment_digest", "example_manifest_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.require(record["base_experiment_digest"] != record["adapted_experiment_digest"], path,
              "base and adapted experiments must be distinct")
    matched = f.closed(record["matched_conditions"], f"{path}.matched_conditions", MATCHED_FIELDS)
    f.digest(matched["execution_condition_digest"], f"{path}.matched_conditions.execution_condition_digest")
    for side in ("base_model_identity", "adapted_model_identity"):
        identity = f.closed(record[side], f"{path}.{side}", IDENTITY_FIELDS)
        f.digest(identity["model_digest"], f"{path}.{side}.model_digest")
        f.string_set(identity["candidate_ids"], f"{path}.{side}.candidate_ids", nonempty=True)
        f.digest_set(identity["model_lineage_root_digests"], f"{path}.{side}.model_lineage_root_digests")
        f.digest_set(identity["model_selection_receipt_digests"], f"{path}.{side}.model_selection_receipt_digests")
        f.nullable(f.digest, identity["adapted_from_model_digest"], f"{path}.{side}.adapted_from_model_digest")
    f.require(record["allowed_difference_fields"] == list(IDENTITY_FIELDS), f"{path}.allowed_difference_fields",
              "must equal exactly the fixed five-member model-identity set")
    f.require(record["base_model_identity"]["adapted_from_model_digest"] is None, f"{path}.base_model_identity",
              "the base adapted_from_model_digest is null")
    f.require(record["adapted_model_identity"]["adapted_from_model_digest"]
              == record["base_model_identity"]["model_digest"], f"{path}.adapted_model_identity",
              "the adapted model must be adapted from the base model")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def check_paired_condition_contract(store: RecordStore, digest: Any, path: str = "paired_condition_contract") -> dict:
    """Both experiments project field-for-field to one matched condition and their identities."""
    from mmbu_phase1 import experiment as experiments, lineage

    record = validate_paired_condition_contract(store.get(digest, "paired_condition_contract", path), path)
    sides = {}
    for side in ("base", "adapted"):
        sides[side] = experiments.check_experiment(store, record[f"{side}_experiment_digest"], f"{path}.{side}_experiment")
        exp = sides[side]
        for name in MATCHED_FIELDS:
            f.require(f.same(exp[name], record["matched_conditions"][name]), f"{path}.matched_conditions.{name}",
                      f"{side} experiment differs from the matched condition")
        for name in IDENTITY_FIELDS:
            f.require(f.same(exp[name], record[f"{side}_model_identity"][name]), f"{path}.{side}_model_identity.{name}",
                      f"{side} experiment differs from its model identity")
        f.require(f.timestamp(record["created_at"], path) > f.timestamp(exp["created_at"], path), f"{path}.created_at",
                  "the pairing contract binds already immutable experiments")
    condition = store.get(record["matched_conditions"]["execution_condition_digest"], "execution_condition", path)
    f.require(condition["request_set"]["example_manifest_digest"] == record["example_manifest_digest"],
              f"{path}.example_manifest_digest", "differs from the bound execution condition")
    adapted_roots = record["adapted_model_identity"]["model_lineage_root_digests"]
    base_model = record["base_model_identity"]["model_digest"]
    rooted = False
    for root in adapted_roots:
        receipt = lineage.validate_lineage_receipt(store.get(root, "lineage_receipt", path))
        rooted |= any(e["parent_digest"] == base_model and e["edge_role"] == "model" for e in receipt["parents"])
    f.require(rooted, f"{path}.adapted_model_identity.model_lineage_root_digests",
              "adapted model lineage is not rooted at the named base model")
    return record
