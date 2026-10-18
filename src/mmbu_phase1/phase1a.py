"""Build, execute, and close the Phase 1A synthetic base/adapted evaluator run.

Order (all prospective records precede the child): adapter artifacts and
requests; environment-launch policy; condition parts; prompt/schema contract
(binding the inference-settings projection); example manifest; execution
condition; lineage receipts; base and adapted experiments; the pre-output
paired-condition contract.  The child then runs from an empty mapping, and the
parent closes reproducibility records, finalized runs, and summaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import platform
from typing import Any

from mmbu_phase1 import (canonical, environment, fields as f, geometry, layers, observe, paths, prompt_contract,
                         rational, summaries, synthetic, task_change)
from mmbu_phase1.store import RecordStore

P = f.SCHEMA_PREFIX
SEED_NAMESPACE = "mmbu.phase1a.synthetic"
GENERATION_SEED = 17
BATCH_SIZE = 8
OPERATOR_ID = "phase1a-implementation-agent"


class Clock:
    """Strictly increasing UTC timestamps (microsecond resolution)."""

    def __init__(self) -> None:
        self.last: datetime | None = None

    def __call__(self) -> str:
        now = datetime.now(timezone.utc)
        if self.last is not None and now <= self.last:
            now = self.last + timedelta(microseconds=1)
        self.last = now
        return now.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass
class World:
    root: Path
    store: RecordStore
    clock: Clock
    files: dict[str, str] = field(default_factory=dict)  # relative path -> sha256
    records: dict[str, dict] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    plan: dict = field(default_factory=dict)

    def write(self, relative: str, data: bytes) -> str:
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
        digest = canonical.raw_digest(data)
        self.files[relative] = digest
        self.store.add_artifact(data)
        return digest

    def artifact(self, relative: str, value: Any) -> str:
        return self.write(relative, canonical.dumps(value))

    def record(self, name: str, relative: str, record: dict) -> dict:
        sealed = canonical.seal(record)
        self.write(relative, canonical.dumps(sealed))
        self.store.add(sealed)
        self.records[name] = sealed
        self.paths[name] = relative
        return sealed

    def read(self, relative: str) -> bytes:
        return paths.member_bytes(self.root, relative)


def decoding() -> dict:
    return {"decoding_method": "greedy", "max_new_tokens": synthetic.MAX_NEW_TOKENS, "temperature": None, "top_p": None,
            "top_k": None, "do_sample": False, "num_beams": 1, "num_return_sequences": 1, "repetition_penalty": 1,
            "stop_token_ids": [], "cache_enabled": False}


def call_isolation() -> dict:
    return {"mode": "separate_task_and_context", "fresh_state_per_call": True, "conversation_reuse": False,
            "kv_cache_reuse": False, "task_receives_context_output": False, "context_receives_task_output": False,
            "cross_call_allowed_fields": []}


def failure_retry() -> dict:
    return {"terminal_rules": [{"terminal_outcome": name, "retain_row": True,
                                "grade_contribution": {"denominator": 1, "numerator": 0}}
                               for name in ("judge_failure", "parse_failure", "runtime_failure", "validation_failure")],
            "retry_mode": "none", "maximum_attempts": 1, "retryable_outcomes": []}


def batching(row_order: list[str]) -> dict:
    batches = [row_order[i:i + BATCH_SIZE] for i in range(0, len(row_order), BATCH_SIZE)]
    return {"batch_size": BATCH_SIZE, "shuffle": False, "drop_last": False, "worker_count": 0, "row_order": row_order,
            "batches": batches, "padding_side": "left", "padding_policy": "no_padding", "truncation": False,
            "max_input_tokens": None, "remainder_policy": "keep", "image_order": "manifest_order"}


def precision_backend() -> dict:
    return {"parameter_dtype": "float32", "compute_dtype": "float32", "autocast_dtype": None, "tf32": None,
            "deterministic_algorithms": True, "cudnn_benchmark": None, "attention_backend": "eager", "kernel_digests": [],
            "compile_mode": "disabled", "fallbacks": [], "cache_backend": "none"}


def build_world(bundle_root: Path, *, repository_root: str, run_root: str, python_executable: str,
                authority_files: dict[str, bytes], clock: Clock | None = None) -> World:
    """Create every prospective record and artifact before any child exists."""
    world = World(Path(bundle_root), RecordStore(), clock or Clock())
    for relative, data in authority_files.items():
        digest = world.write("authority/" + relative.rsplit("/", 1)[-1], data)
        world.store.add(canonical.loads_canonical(data))
        world.paths[relative] = "authority/" + relative.rsplit("/", 1)[-1]
        f.require(digest == canonical.raw_digest(data), relative, "authority copy differs")
    registry = canonical.loads_canonical(authority_files["config/phase1/authorization-registry.json"])
    specs = {name: world.write(f"artifacts/specs/{name}.json", data) for name, data in synthetic.spec_artifacts().items()}
    plan: dict[str, Any] = {"files": {}, "specs": {n: f"artifacts/specs/{n}.json" for n in specs}, "requests": {},
                            "targets": {}, "models": {}}
    inputs, task_targets, context_targets, boxes, task_requests, context_requests = {}, {}, {}, {}, {}, {}
    for case in synthetic.CASES:
        cid = case.example_id
        inputs[cid] = world.artifact(f"artifacts/inputs/{cid}.json", synthetic.input_descriptor(case))
        task_targets[cid] = world.artifact(f"artifacts/targets/{cid}.task.json", synthetic.task_target(case))
        plan["targets"][cid] = {"task": f"artifacts/targets/{cid}.task.json"}
        if case.fields:
            context_targets[cid] = world.artifact(f"artifacts/targets/{cid}.context.json", synthetic.context_target(case))
            plan["targets"][cid]["context"] = f"artifacts/targets/{cid}.context.json"
        if case.family == "detection":
            boxes[cid] = world.artifact(f"artifacts/targets/{cid}.boxes.json", [list(b) for b in case.boxes])
            plan["targets"][cid]["boxes"] = f"artifacts/targets/{cid}.boxes.json"
        task_requests[cid] = world.artifact(f"artifacts/requests/{cid}.task.json", synthetic.task_request(case, specs))
        plan["requests"][cid] = {"task": f"artifacts/requests/{cid}.task.json"}
        context = synthetic.context_request(case, specs)
        if context is not None:
            context_requests[cid] = world.artifact(f"artifacts/requests/{cid}.context.json", context)
            plan["requests"][cid]["context"] = f"artifacts/requests/{cid}.context.json"
    models = {}
    for side in ("base", "adapted"):
        models[side] = world.artifact(f"artifacts/models/synthetic-{side}.json", synthetic.responder_table(side, specs))
        plan["models"][side] = f"artifacts/models/synthetic-{side}.json"
    policy = environment.build_policy(repository_root, run_root, python_executable, created_at=world.clock())
    world.record("environment_launch_policy", "records/environment-launch-policy.json", policy)
    row_order = [case.example_id for case in synthetic.CASES]
    runtime = observe.runtime(policy, environment.projection(policy))
    objects = {"decoding": decoding(), "call_isolation": call_isolation(), "failure_retry": failure_retry(),
               "runtime": runtime, "batching": batching(row_order), "precision_backend": precision_backend()}
    threshold = {"denominator": 2, "numerator": 1}
    contract = world.record("prompt_schema_contract", "records/prompt-schema-contract.json", {
        "schema_id": P + "prompt_schema_contract", "schema_version": 1, "contract_id": "phase1a-synthetic-contract",
        "contract_status": "synthetic", "task_prompt_digest": specs["task_prompt"],
        "context_prompt_digest": specs["context_prompt"], "task_output_schema_digest": specs["task_output_schema"],
        "context_output_schema_digest": specs["context_output_schema"],
        "requested_context_field_registry_digest": specs["field_registry"], "parser_digest": specs["parser"],
        "validator_digest": specs["validator"], "judge_policy_digest": specs["judge_policy"],
        "geometry_threshold": threshold,
        "inference_settings_digest": prompt_contract.inference_settings_digest(objects),
        "official_source_digests": [], "supersedes_digest": None, "created_at": world.clock()})
    rows = []
    for case in synthetic.CASES:
        cid, detection = case.example_id, case.family == "detection"
        rows.append({"example_id": cid, "independent_unit_id": f"unit-{cid}", "task_family": case.family,
                     "input_digest": inputs[cid], "requested_context_fields": list(case.fields),
                     "task_weight": case.weight, "image_width": synthetic.WIDTH if detection else None,
                     "image_height": synthetic.HEIGHT if detection else None, "task_target_digest": task_targets[cid],
                     "context_target_digest": context_targets.get(cid), "box_policy": case.policy,
                     "target_boxes_digest": boxes.get(cid)})
    manifest = world.record("example_manifest", "records/example-manifest.json", {
        "schema_id": P + "example_manifest", "schema_version": 1, "manifest_id": "phase1a-synthetic-manifest",
        "contract_digest": contract["record_digest"], "purpose": "engineering",
        "population_id": "phase1a-synthetic-population", "rows": rows, "created_at": world.clock()})
    request_rows = [{"example_id": row["example_id"], "input_digest": row["input_digest"],
                     "task_request_digest": task_requests[row["example_id"]],
                     "context_request_digest": context_requests.get(row["example_id"]),
                     "requested_context_fields": row["requested_context_fields"]} for row in rows]
    condition = world.record("execution_condition", "records/execution-condition.json", {
        "schema_id": P + "execution_condition", "schema_version": 1, "condition_id": "phase1a-synthetic-condition",
        "environment_launch_policy_digest": policy["record_digest"],
        "request_set": {"example_manifest_digest": manifest["record_digest"], "rows": request_rows},
        "components": {"prompt_schema_contract_digest": contract["record_digest"], "evaluator_digest": specs["evaluator"],
                       "parser_digest": specs["parser"], "validator_digest": specs["validator"],
                       "judge_policy_digest": specs["judge_policy"], "geometry_threshold": threshold},
        "processor": {"processor_digest": specs["processor"], "preprocessor_config_digest": specs["preprocessor_config"],
                      "template_digest": specs["template"], "image_decoder_digest": specs["image_decoder"]},
        "randomness": {"seed_namespace": SEED_NAMESPACE,
                       "streams": [{"name": "generation", "seed": GENERATION_SEED, "algorithm": "mt19937",
                                    "version": "cpython-" + platform.python_version() + "-random",
                                    "derivation": "direct", "parent_name": None}]},
        **objects, "created_at": world.clock()})
    lineage_created = world.clock()

    def lineage(name: str, artifact: str, parents: list) -> dict:
        return world.record(f"lineage_{name}", f"records/lineage/{name}.json", {
            "schema_id": P + "lineage_receipt", "schema_version": 1, "lineage_id": f"phase1a-{name}",
            "artifact_digest": artifact, "origin_class": "synthetic_engineering", "allowed_purposes": ["engineering"],
            "parents": parents, "source_version": None, "rights_receipt_digest": None, "grouping_receipt_digest": None,
            "qa_receipt_digest": None, "created_at": lineage_created})

    data_lineage = lineage("fixture", manifest["record_digest"], [])
    prompt_lineage = lineage("prompt_contract", contract["record_digest"], [])
    base_lineage = lineage("model_base", models["base"], [])
    adapted_lineage = lineage("model_adapted", models["adapted"], [{"parent_digest": models["base"], "edge_role": "model"}])
    non_model = sorted([data_lineage["record_digest"], prompt_lineage["record_digest"]])
    experiments = {}
    for side, model_lineage, adapted_from in (("base", base_lineage, None),
                                              ("adapted", adapted_lineage, models["base"])):
        experiments[side] = world.record(f"experiment_{side}", f"records/experiment-{side}.json", {
            "schema_id": P + "experiment", "schema_version": 1, "experiment_id": f"phase1a-synthetic-{side}",
            "purpose": "engineering", "authorization_registry_digest": registry["record_digest"],
            "source_record_digests": [], "purpose_authorization_digests": [], "source_manifest_digests": [],
            "split_manifest_digests": [], "lineage_root_digests": sorted(non_model + [model_lineage["record_digest"]]),
            "model_lineage_root_digests": [model_lineage["record_digest"]], "non_model_lineage_root_digests": non_model,
            "decision_execution_receipt_digests": [], "model_selection_receipt_digests": [],
            "non_model_decision_execution_receipt_digests": [], "model_digest": models[side],
            "adapted_from_model_digest": adapted_from, "execution_condition_digest": condition["record_digest"],
            "prospective_lock_digest": None, "candidate_ids": [f"synthetic-{side}"], "decision_function_digest": None,
            "created_at": world.clock()})
    matched = {name: experiments["base"][name] for name in (
        "purpose", "authorization_registry_digest", "source_record_digests", "purpose_authorization_digests",
        "source_manifest_digests", "split_manifest_digests", "non_model_lineage_root_digests",
        "non_model_decision_execution_receipt_digests", "execution_condition_digest", "prospective_lock_digest",
        "decision_function_digest")}
    identity = lambda e: {k: e[k] for k in ("adapted_from_model_digest", "candidate_ids", "model_digest",  # noqa: E731
                                            "model_lineage_root_digests", "model_selection_receipt_digests")}
    world.record("paired_condition_contract", "records/paired-condition-contract.json", {
        "schema_id": P + "paired_condition_contract", "schema_version": 1, "pairing_id": "phase1a-synthetic-pair",
        "base_experiment_digest": experiments["base"]["record_digest"],
        "adapted_experiment_digest": experiments["adapted"]["record_digest"],
        "example_manifest_digest": manifest["record_digest"], "matched_conditions": matched,
        "base_model_identity": identity(experiments["base"]), "adapted_model_identity": identity(experiments["adapted"]),
        "allowed_difference_fields": ["adapted_from_model_digest", "candidate_ids", "model_digest",
                                      "model_lineage_root_digests", "model_selection_receipt_digests"],
        "created_at": world.clock()})
    for name in ("environment_launch_policy", "execution_condition", "example_manifest", "prompt_schema_contract",
                 "experiment_base", "experiment_adapted"):
        plan["files"][name] = {"path": world.paths[name], "sha256": world.files[world.paths[name]]}
    world.plan = plan
    world.artifact("runs/plan.json", plan)
    return world


@dataclass
class Execution:
    world: World
    launch: environment.LaunchResult
    observation: dict
    reproducibility: dict[str, dict]
    runs: dict[str, dict]
    geometry: dict[str, dict]
    task_change: dict


def execute(world: World, *, source_state_digest: str, contract_manifest_digest: str) -> Execution:
    """Launch the child from an empty mapping, then close records from its evidence."""
    policy = world.records["environment_launch_policy"]
    result = environment.launch(policy, ["evaluate", str(world.root), "runs/plan.json"])
    world.write("runs/launch/child.stdout", result.stdout)
    world.write("runs/launch/child.stderr", result.stderr)
    capture_digest = world.write("runs/launch/child-environment-capture.json", result.capture_bytes)
    receipt = world.record("environment_launch_receipt", "runs/launch/environment-launch-receipt.json", result.receipt)
    environment.check_environment_launch_receipt(world.store, receipt["record_digest"], capture=result.capture)
    f.require(result.receipt["exit_code"] == 0, "child", "the Phase 1A child failed: " + result.stderr.decode(errors="replace")[-2000:])
    observation_bytes = world.read("runs/launch/observation.json")
    observation_digest = canonical.raw_digest(observation_bytes)
    world.files["runs/launch/observation.json"] = observation_digest
    observation = canonical.loads_canonical(observation_bytes)
    probe_digest = world.artifact("runs/launch/network-probe.json", observation["network_probe"])
    rng_digest = world.artifact("runs/launch/rng-state-generation.json", observation["rng_state"]["generation"])
    lock_digest = world.artifact("artifacts/environment/dependency-lock.json", {
        "kind": "mmbu.phase1a.dependency_closure", "version": 1, "installed_packages": [],
        "software": world.records["execution_condition"]["runtime"]["software"],
        "statement": "standard library only; nothing installed"})
    resolver_digest = world.artifact("artifacts/environment/resolver-report.json", {
        "kind": "mmbu.phase1a.resolver_report", "version": 1, "resolver": None, "statement": "no resolver was run"})
    install_digest = world.artifact("artifacts/environment/install-command.json", {
        "kind": "mmbu.phase1a.install_command", "version": 1, "command": None, "statement": "no install command"})
    condition = world.records["execution_condition"]
    manifest = world.records["example_manifest"]
    reproducibility, runs, outputs = {}, {}, {}
    for side in ("base", "adapted"):
        output_bytes = world.read(f"runs/{side}/output-manifest.json")
        output = canonical.loads_canonical(output_bytes)
        world.files[f"runs/{side}/output-manifest.json"] = canonical.raw_digest(output_bytes)
        world.store.add(output)
        for entry in output["entries"]:
            data = world.read(entry["path"])
            world.files[entry["path"]] = canonical.raw_digest(data)
            if entry["schema_id"] is not None:
                world.store.add(canonical.loads_canonical(data))
        outputs[side] = output
        experiment = world.records[f"experiment_{side}"]
        window = observation["windows"][side]
        runtime = observation["observed_condition"]["runtime"]
        repro = world.record(f"reproducibility_{side}", f"runs/{side}/reproducibility.json", {
            "schema_id": P + "reproducibility", "schema_version": 1, "reproducibility_id": f"reproducibility-{side}",
            "declared_level": "R-I", "source_state_digest": source_state_digest,
            "contract_manifest_digest": contract_manifest_digest, "experiment_digest": experiment["record_digest"],
            "execution_condition_digest": condition["record_digest"],
            "environment_launch_policy_digest": policy["record_digest"],
            "environment_launch_receipt_digest": receipt["record_digest"],
            "observed_condition": observation["observed_condition"], "prospective_lock_digest": None,
            "opening_receipt_digest": None, "opening_receipt_registry_digest": None, "operator_id": OPERATOR_ID,
            "started_at": window["started_at"], "ended_at": window["ended_at"],
            "terminal_status": "succeeded" if receipt["exit_code"] == 0 else "failed", "command": receipt["argv"],
            "command_digest": canonical.value_digest(receipt["argv"]), "working_directory": policy["working_directory"],
            "locale": runtime["locale"], "timezone": runtime["timezone"], "filesystem": runtime["filesystem"],
            "environment_variables": receipt["child_environment"], "environment_artifact_digests": [capture_digest],
            "os_kernel": observation["os_kernel"], "python": observation["python"], "container_digest": None,
            "hardware": observation["hardware"],
            "frameworks": {"python_executable_digest": runtime["python_executable_digest"],
                           "python_version": runtime["python_version"], "torch": None, "transformers": None,
                           "accelerate": None, "deepspeed": None, "fsdp": None, "cuda_runtime": None,
                           "cuda_toolkit": None, "cudnn": None, "nccl": None, "compiler": observation["compiler"],
                           "attention_library": None, "quantization_library": None,
                           "image_decoder": "mmbu.phase1a.synthetic_descriptor_decoder@1",
                           "dependency_lock_digest": lock_digest, "resolver_report_digest": resolver_digest,
                           "package_artifact_digests": sorted(s["artifact_digest"] for s in runtime["software"]),
                           "install_command_digest": install_digest, "package_source_digests": []},
            "effective_numeric_settings": _experiment_module().expected_numeric(condition),
            "distributed_settings": _experiment_module().expected_distributed(condition),
            "seed_namespaces": _experiment_module().expected_seed_namespaces(condition, {"generation": rng_digest}),
            "rng_state_artifact_digests": [rng_digest],
            "worker_sampler_order": _experiment_module().expected_worker_order(condition, manifest,
                                                                               observation["exposure"][side]),
            "cache_network_policy": {"cache_root_digest": canonical.value_digest(runtime["cache_network"]["cache_root_digests"]),
                                     "snapshot_digests": runtime["cache_network"]["snapshot_digests"],
                                     "offline_requested": runtime["cache_network"]["offline_requested"],
                                     "network_denied": runtime["cache_network"]["network_denied"],
                                     "network_probe_digest": probe_digest,
                                     "remote_request_log_digest": runtime["cache_network"]["request_log_digest"],
                                     "hidden_fetch_count": runtime["cache_network"]["hidden_fetch_count"]},
            "input_digests": sorted({manifest["record_digest"], condition["record_digest"], experiment["model_digest"],
                                     *(r["task_request_digest"] for r in condition["request_set"]["rows"]),
                                     *(r["context_request_digest"] for r in condition["request_set"]["rows"]
                                       if r["context_request_digest"] is not None)}),
            "output_digests": sorted({entry["sha256"] for entry in output["entries"]}),
            "log_digests": sorted({receipt["stdout_digest"], receipt["stderr_digest"], capture_digest, observation_digest}),
            "exit_code": receipt["exit_code"], "tolerances": [], "compared_run_digest": None, "observed_differences": [],
            "reproduction_status": "not_requested", "reproduction_limitation": None, "created_at": world.clock()})
        reproducibility[side] = repro
        runs[side] = world.record(f"run_{side}", f"runs/{side}/run.json", {
            "schema_id": P + "run", "schema_version": 1, "run_id": f"phase1a-run-{side}",
            "experiment_digest": experiment["record_digest"], "execution_condition_digest": condition["record_digest"],
            "reproducibility_record_digest": repro["record_digest"], "source_state_digest": source_state_digest,
            "command_digest": repro["command_digest"], "input_manifest_digests": [manifest["record_digest"]],
            "output_manifest_digest": output["record_digest"], "started_at": window["started_at"],
            "ended_at": window["ended_at"], "exit_code": receipt["exit_code"], "terminal_status": repro["terminal_status"],
            "consumed_experiment_digest": experiment["record_digest"]})
    geometry_records = {}
    threshold = rational.from_wire(condition["components"]["geometry_threshold"])
    for side in ("base", "adapted"):
        rows = summaries.geometry_rows(world.store, manifest, layers.layers_by_example(outputs[side], world.read), threshold)
        geometry_records[side] = world.record(f"geometry_{side}", f"summaries/geometry-{side}.json", {
            "schema_id": P + "geometry_summary", "schema_version": 1, "summary_id": f"phase1a-geometry-{side}",
            "example_manifest_digest": manifest["record_digest"], "output_manifest_digest": outputs[side]["record_digest"],
            "validator_digest": condition["components"]["validator_digest"],
            "threshold": condition["components"]["geometry_threshold"], "rows": rows, "created_at": world.clock()})
    judged = {side: summaries.judged_by_example(outputs[side], world.read) for side in ("base", "adapted")}
    policy_spec = canonical.loads_canonical(world.store.artifact(condition["components"]["judge_policy_digest"]))
    rows, totals, binary = task_change.build(manifest["rows"], judged["base"], judged["adapted"],
                                             policy_spec["binary_correctness"])
    change = world.record("task_change", "summaries/task-change.json", {
        "schema_id": P + "task_change_summary", "schema_version": 1, "summary_id": "phase1a-task-change",
        "pairing_contract_digest": world.records["paired_condition_contract"]["record_digest"],
        "example_manifest_digest": manifest["record_digest"], "base_run_digest": runs["base"]["record_digest"],
        "adapted_run_digest": runs["adapted"]["record_digest"],
        "base_output_manifest_digest": outputs["base"]["record_digest"],
        "adapted_output_manifest_digest": outputs["adapted"]["record_digest"],
        "judge_policy_digest": condition["components"]["judge_policy_digest"], "rows": rows, "totals": totals,
        "binary_summary": binary, "created_at": world.clock()})
    return Execution(world, result, observation, reproducibility, runs, geometry_records, change)


def _experiment_module():
    from mmbu_phase1 import experiment

    return experiment


def verify_records(store: RecordStore, read: Any, *, contract_manifest_digest: str) -> dict:
    """Re-validate the paired run transitively from bundle bytes alone (no in-memory world)."""
    from mmbu_phase1 import condition as conditions, experiment as experiments

    pairings = store.records("paired_condition_contract")
    f.require(len(pairings) == 1, "bundle", "exactly one paired-condition contract")
    pairing = pairings[0]
    observation = canonical.loads_canonical(read("runs/launch/observation.json"))
    rng = {"generation": canonical.raw_digest(read("runs/launch/rng-state-generation.json"))}
    runs = {}
    for run in store.records("run"):
        side = "base" if run["experiment_digest"] == pairing["base_experiment_digest"] else "adapted"
        f.require(side not in runs, "bundle", "exactly one finalized run per paired experiment")
        runs[side] = run
    f.require(set(runs) == {"base", "adapted"}, "bundle", "both paired runs must be present")

    def run_check(store_: RecordStore, digest: str, read_: Any, path: str) -> dict:
        side = "base" if digest == runs["base"]["record_digest"] else "adapted"
        return experiments.check_run(store_, digest, read_, path, contract_manifest_digest=contract_manifest_digest,
                                     exposure=observation["exposure"][side], rng_state_digests=rng)

    conditions.check_paired_condition_contract(store, pairing["record_digest"])
    condition = store.get(pairing["matched_conditions"]["execution_condition_digest"], "execution_condition")
    for side in ("base", "adapted"):
        experiments.check_experiment(store, pairing[f"{side}_experiment_digest"],
                                     started_at=observation["windows"][side]["started_at"])
        run_check(store, runs[side]["record_digest"], read, f"run_{side}")
    geometry_records = store.records("geometry_summary")
    f.require(len(geometry_records) == 2, "bundle", "one geometry summary per condition manifest")
    for record in geometry_records:
        summaries.check_geometry_summary(store, record["record_digest"], read, condition=condition)
    changes = store.records("task_change_summary")
    f.require(len(changes) == 1, "bundle", "exactly one task-change summary")
    summaries.check_task_change_summary(store, changes[0]["record_digest"], read, run_check=run_check)
    return {"pairing": pairing, "runs": runs, "observation": observation, "task_change": changes[0], "condition": condition}


def verify_execution(world: World, execution: Execution, *, contract_manifest_digest: str) -> dict:
    return verify_records(world.store, world.read, contract_manifest_digest=contract_manifest_digest)
