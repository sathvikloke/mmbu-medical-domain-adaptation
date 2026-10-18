"""Phase 1A child payload: execute the frozen synthetic run plan for base and adapted.

For every example in frozen batch order the child sends a task request and,
when fields are requested, a separate context request to a fresh stateless
responder; writes the raw record content-addressed and read-only before any
parsing; re-reads those exact bytes from disk; then parses, validates, and
judges, each layer bound to its parent's digest.  It never retries, repairs,
or drops a row.  Observations are independent of the prospective condition.
"""

from __future__ import annotations

import os
from pathlib import Path
import platform
import random
import sys
import time
from typing import Any

from mmbu_phase1 import canonical, evaluator, fields as f, geometry, observe, paths, rational, synthetic

LAYER_SCHEMAS = ("raw_output", "parsed_output", "validated_output", "judged_output")


def write_immutable(root: Path, relative: str, data: bytes) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)


def write_record(root: Path, prefix: str, record: dict) -> tuple[str, bytes]:
    sealed = canonical.seal(record)
    data = canonical.dumps(sealed)
    relative = f"{prefix}/{canonical.raw_digest(data)}.json"
    write_immutable(root, relative, data)
    return relative, data


def read_verified(root: Path, relative: str, digest: str) -> bytes:
    data = paths.member_bytes(root, relative)
    f.require(canonical.raw_digest(data) == digest, relative, "planned input bytes changed")
    return data


def load(root: Path, plan: dict, name: str) -> Any:
    entry = plan["files"][name]
    return canonical.loads_canonical(read_verified(root, entry["path"], entry["sha256"]))


def layer(schema: str, row: dict, manifest: dict, extra: dict) -> dict:
    base = {
        "schema_id": f.SCHEMA_PREFIX + schema,
        "schema_version": 1,
        "record_id": f"{schema}:{extra.pop('_label')}:{row['example_id']}",
        "example_id": row["example_id"],
        "example_manifest_digest": manifest["record_digest"],
        "contract_digest": manifest["contract_digest"],
        "created_at": f.utc_now(),
    }
    base.update(extra)
    return base


def run_experiment(root: Path, plan: dict, label: str, condition: dict, manifest: dict, experiment: dict,
                   table: dict, judge_policy: dict, threshold: Any, observed_batches: list) -> tuple[list, dict, str, str]:
    prefix = f"runs/{label}"
    components = condition["components"]
    rows = {row["example_id"]: row for row in manifest["rows"]}
    requests = {row["example_id"]: row for row in condition["request_set"]["rows"]}
    entries = []
    log = []
    exposure = {"examples": 0, "task_calls": 0, "context_calls": 0}
    started = f.utc_now()
    batches_seen = []
    task_outputs: list[str] = []
    for batch in condition["batching"]["batches"]:
        batches_seen.append(list(batch))
        for example_id in batch:
            row, request_row = rows[example_id], requests[example_id]
            task_bytes = read_verified(root, plan["requests"][example_id]["task"], request_row["task_request_digest"])
            context_bytes = None
            if request_row["context_request_digest"] is not None:
                context_bytes = read_verified(root, plan["requests"][example_id]["context"],
                                              request_row["context_request_digest"])
            call_started = f.utc_now()
            clock = time.monotonic()
            task_call = synthetic.respond(table, task_bytes)  # fresh stateless call
            context_call = synthetic.respond(table, context_bytes) if context_bytes is not None else None
            latency = round((time.monotonic() - clock) * 1000, 3)
            call_ended = f.utc_now()
            exposure["examples"] += 1
            exposure["task_calls"] += 1
            exposure["context_calls"] += context_bytes is not None
            if task_call.text:
                task_outputs.append(task_call.text)
            packed = evaluator.transcript(task_call, context_call)
            raw = layer("raw_output", row, manifest, {
                "_label": label,
                "experiment_digest": experiment["record_digest"],
                "execution_condition_digest": condition["record_digest"],
                "request_digest": canonical.value_digest(request_row),
                "input_digest": request_row["input_digest"],
                "processor_digest": condition["processor"]["processor_digest"],
                "prompt_schema_contract_digest": components["prompt_schema_contract_digest"],
                "evaluator_digest": components["evaluator_digest"],
                "parser_digest": components["parser_digest"],
                "validator_digest": components["validator_digest"],
                "judge_policy_digest": components["judge_policy_digest"],
                "token_ids": packed["token_ids"],
                "decoded_text": packed["decoded_text"],
                "finish_reason": packed["finish_reason"],
                "effective_generation_settings": condition["decoding"],
                "timing": {"started_at": call_started, "ended_at": call_ended, "latency_ms": latency},
                "runtime_status": packed["runtime_status"],
            })
            raw_path, raw_bytes = write_record(root, f"{prefix}/raw", raw)
            os.chmod(root / raw_path, 0o444)
            raw_on_disk = canonical.loads_canonical(read_verified(root, raw_path, canonical.raw_digest(raw_bytes)))
            parse_status, parsed_value = evaluator.parse(raw_on_disk, row)
            parsed = layer("parsed_output", row, manifest, {
                "_label": label, "raw_digest": raw_on_disk["record_digest"], "parser_digest": components["parser_digest"],
                "parse_status": parse_status, "parsed_value": parsed_value})
            parsed_path, parsed_bytes = write_record(root, f"{prefix}/parsed", parsed)
            parsed_on_disk = canonical.loads_canonical(parsed_bytes)
            targets = None
            if row["task_family"] == "detection":
                targets = canonical.loads_canonical(read_verified(root, plan["targets"][example_id]["boxes"],
                                                                  row["target_boxes_digest"]))
            validation_status, geometry_status, validated_value = evaluator.validate(parse_status, parsed_on_disk["parsed_value"],
                                                                                    row, targets)
            validated = layer("validated_output", row, manifest, {
                "_label": label, "raw_digest": raw_on_disk["record_digest"], "parsed_digest": parsed_on_disk["record_digest"],
                "validator_digest": components["validator_digest"], "validation_status": validation_status,
                "requested_context_fields": row["requested_context_fields"], "geometry_status": geometry_status,
                "validated_value": validated_value})
            validated_path, validated_bytes = write_record(root, f"{prefix}/validated", validated)
            validated_on_disk = canonical.loads_canonical(validated_bytes)
            task_target = canonical.loads_canonical(read_verified(root, plan["targets"][example_id]["task"],
                                                                  row["task_target_digest"]))
            context_target = None
            if row["context_target_digest"] is not None:
                context_target = canonical.loads_canonical(read_verified(root, plan["targets"][example_id]["context"],
                                                                         row["context_target_digest"]))
            judge_status, task_grade, context_grades = evaluator.judge(
                validation_status, validated_on_disk["validated_value"], row, judge_policy, task_target, context_target,
                targets, threshold)
            judged = layer("judged_output", row, manifest, {
                "_label": label, "raw_digest": raw_on_disk["record_digest"], "parsed_digest": parsed_on_disk["record_digest"],
                "validated_digest": validated_on_disk["record_digest"], "judge_digest": components["judge_policy_digest"],
                "judge_status": judge_status, "task_grade": task_grade, "context_grades": context_grades,
                "terminal_outcome": "pending"})
            judged["terminal_outcome"] = _terminal(raw_on_disk, parsed_on_disk, validated_on_disk, judge_status)
            judged_path, judged_bytes = write_record(root, f"{prefix}/judged", judged)
            for role, relative, data in (("raw_output", raw_path, raw_bytes), ("parsed_output", parsed_path, parsed_bytes),
                                         ("validated_output", validated_path, validated_bytes),
                                         ("judged_output", judged_path, judged_bytes)):
                record = canonical.loads_canonical(data)
                entries.append({"path": relative, "bytes": len(data), "sha256": canonical.raw_digest(data),
                                "media_type": "application/json", "schema_id": record["schema_id"], "schema_version": 1,
                                "record_digest": record["record_digest"], "role": role, "example_id": example_id})
            log.append({"example_id": example_id, "task_request_digest": request_row["task_request_digest"],
                        "context_request_digest": request_row["context_request_digest"],
                        "runtime_status": raw_on_disk["runtime_status"], "terminal_outcome": judged["terminal_outcome"]})
    ended = f.utc_now()
    log_bytes = canonical.dumps({"experiment": label, "calls": log})
    log_path = f"{prefix}/execution-log.json"
    write_immutable(root, log_path, log_bytes)
    entries.append({"path": log_path, "bytes": len(log_bytes), "sha256": canonical.raw_digest(log_bytes),
                    "media_type": "application/json", "schema_id": None, "schema_version": None, "record_digest": None,
                    "role": "log", "example_id": None})
    entries.sort(key=lambda e: e["path"].encode("utf-8"))
    output_manifest = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "execution_output_manifest", "schema_version": 1,
        "output_manifest_id": f"output-manifest-{label}", "experiment_digest": experiment["record_digest"],
        "execution_condition_digest": condition["record_digest"], "example_manifest_digest": manifest["record_digest"],
        "contract_digest": manifest["contract_digest"], "entries": entries, "created_at": f.utc_now()})
    write_immutable(root, f"{prefix}/output-manifest.json", canonical.dumps(output_manifest))
    observed_batches.append(batches_seen)
    return task_outputs, exposure, started, ended


def _terminal(raw: dict, parsed: dict, validated: dict, judge_status: str) -> str:
    if raw["runtime_status"] != "succeeded":
        return "runtime_failure"
    if parsed["parse_status"] != "parsed":
        return "parse_failure"
    if validated["validation_status"] != "valid":
        return "validation_failure"
    return "success" if judge_status == "judged" else "judge_failure"


def rng_state_digest(generator: random.Random) -> str:
    version, state, gauss = generator.getstate()
    return canonical.value_digest({"gauss": gauss, "state": list(state), "version": version})


def run(argv: list[str]) -> int:
    root, plan_path = Path(argv[0]), argv[1]
    guard = observe.NetworkGuard().install()
    probe_denied = guard.probe()
    plan = canonical.loads_canonical(paths.member_bytes(root, plan_path))
    policy = load(root, plan, "environment_launch_policy")
    condition = load(root, plan, "execution_condition")
    manifest = load(root, plan, "example_manifest")
    contract = load(root, plan, "prompt_schema_contract")
    judge_policy = canonical.loads_canonical(read_verified(root, plan["specs"]["judge_policy"],
                                                           condition["components"]["judge_policy_digest"]))
    validator = canonical.loads_canonical(read_verified(root, plan["specs"]["validator"],
                                                        condition["components"]["validator_digest"]))
    threshold = rational.from_wire(validator["geometry_threshold"])
    stream = condition["randomness"]["streams"][0]
    generator = random.Random(stream["seed"])
    before = rng_state_digest(generator)
    observed_batches: list = []
    windows, exposures, task_outputs = {}, {}, []
    for label in ("base", "adapted"):
        experiment = load(root, plan, f"experiment_{label}")
        table = canonical.loads_canonical(read_verified(root, plan["models"][label], experiment["model_digest"]))
        outputs, exposure, started, ended = run_experiment(root, plan, label, condition, manifest, experiment, table,
                                                           judge_policy, threshold, observed_batches)
        windows[label] = {"started_at": started, "ended_at": ended}
        exposures[label] = exposure
        task_outputs.extend(outputs)
    after = rng_state_digest(generator)
    context_leak = any(any(output.encode("utf-8") in paths.member_bytes(root, request["context"])
                           for output in task_outputs if output)
                       for request in plan["requests"].values() if request.get("context"))
    capture_rows = sorted(({"name": k, "value": v} for k, v in os.environ.items()), key=lambda r: r["name"].encode("utf-8"))
    violations = observe.loaded_module_violations()
    runtime = observe.runtime(policy, capture_rows, observed_locale=observe.effective_locale(),
                              observed_timezone=time.tzname[0], network=guard.cache_network())
    if violations:
        runtime["software"] = sorted(runtime["software"] + [{"name": "undeclared:" + name, "version": "unknown",
                                                              "artifact_digest": "0" * 64} for name in violations],
                                     key=lambda row: row["name"].encode("utf-8"))
    request_rows = []
    for row in manifest["rows"]:
        request = plan["requests"][row["example_id"]]
        task_digest = canonical.raw_digest(paths.member_bytes(root, request["task"]))
        context_digest = canonical.raw_digest(paths.member_bytes(root, request["context"])) if request.get("context") else None
        request_rows.append({"example_id": row["example_id"], "input_digest": row["input_digest"],
                             "task_request_digest": task_digest, "context_request_digest": context_digest,
                             "requested_context_fields": row["requested_context_fields"]})
    specs = {name: canonical.raw_digest(paths.member_bytes(root, rel)) for name, rel in plan["specs"].items()}
    observed = {
        "request_set": {"example_manifest_digest": manifest["record_digest"], "rows": request_rows},
        "components": {"prompt_schema_contract_digest": contract["record_digest"], "evaluator_digest": specs["evaluator"],
                       "parser_digest": specs["parser"], "validator_digest": specs["validator"],
                       "judge_policy_digest": specs["judge_policy"], "geometry_threshold": validator["geometry_threshold"]},
        "processor": {"processor_digest": specs["processor"], "preprocessor_config_digest": specs["preprocessor_config"],
                      "template_digest": specs["template"], "image_decoder_digest": specs["image_decoder"]},
        "randomness": {"seed_namespace": condition["randomness"]["seed_namespace"],
                       "streams": [{"name": "generation", "seed": stream["seed"], "algorithm": "mt19937",
                                    "version": "cpython-" + platform.python_version() + "-random",
                                    "derivation": "direct", "parent_name": None}]},
        "decoding": condition["decoding"],
        "call_isolation": {"mode": "separate_task_and_context", "fresh_state_per_call": True,
                           "conversation_reuse": False, "kv_cache_reuse": False,
                           "task_receives_context_output": False, "context_receives_task_output": context_leak,
                           "cross_call_allowed_fields": []},
        "failure_retry": {"terminal_rules": [{"terminal_outcome": name, "retain_row": True,
                                              "grade_contribution": {"denominator": 1, "numerator": 0}}
                                             for name in ("judge_failure", "parse_failure", "runtime_failure",
                                                          "validation_failure")],
                          "retry_mode": "none", "maximum_attempts": 1, "retryable_outcomes": []},
        "runtime": runtime,
        "batching": {**condition["batching"], "row_order": [i for batch in observed_batches[0] for i in batch],
                     "batches": observed_batches[0]},
        "precision_backend": {"parameter_dtype": "float32", "compute_dtype": "float32", "autocast_dtype": None,
                              "tf32": None, "deterministic_algorithms": True, "cudnn_benchmark": None,
                              "attention_backend": "eager", "kernel_digests": [], "compile_mode": "disabled",
                              "fallbacks": [], "cache_backend": "none"},
    }
    observation = {
        "observed_condition": observed,
        "network_probe": {"denied": probe_denied, "attempts_after_probe": guard.attempts},
        "rng_state": {"generation": {"before": before, "after": after, "consumed": before != after}},
        "exposure": exposures,
        "windows": windows,
        "loaded_module_violations": violations,
        "batches_identical_across_experiments": observed_batches[0] == observed_batches[1],
        "hardware": observe.hardware(),
        "os_kernel": platform.platform(),
        "compiler": platform.python_compiler(),
        "python": sys.executable,
    }
    write_immutable(root, "runs/launch/observation.json", canonical.dumps(observation))
    return 0 if probe_denied and not violations and not context_leak and observation["batches_identical_across_experiments"] else 4
