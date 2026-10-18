"""``mmbu.phase1.experiment``, ``run``, and ``reproducibility`` records."""

from __future__ import annotations

from typing import Any

from mmbu_phase1 import fields as f
from mmbu_phase1.vocab import RUN_TERMINAL_STATUSES

RUN_KEYS = (
    "schema_id",
    "schema_version",
    "run_id",
    "experiment_digest",
    "execution_condition_digest",
    "reproducibility_record_digest",
    "source_state_digest",
    "command_digest",
    "input_manifest_digests",
    "output_manifest_digest",
    "started_at",
    "ended_at",
    "exit_code",
    "terminal_status",
    "consumed_experiment_digest",
    "record_digest",
)


def validate_run(record: Any, path: str = "run") -> dict:
    """Finalized immutable run record (not mutable scheduler state)."""
    f.record(record, "run", RUN_KEYS, path)
    f.text(record["run_id"], f"{path}.run_id")
    for name in (
        "experiment_digest",
        "execution_condition_digest",
        "reproducibility_record_digest",
        "source_state_digest",
        "command_digest",
        "output_manifest_digest",
        "consumed_experiment_digest",
    ):
        f.digest(record[name], f"{path}.{name}")
    f.digest_set(record["input_manifest_digests"], f"{path}.input_manifest_digests", nonempty=True)
    started = f.timestamp(record["started_at"], f"{path}.started_at")
    ended = f.timestamp(record["ended_at"], f"{path}.ended_at")
    f.require(ended >= started, f"{path}.ended_at", "must not precede started_at")
    status = f.one_of(record["terminal_status"], f"{path}.terminal_status", RUN_TERMINAL_STATUSES)
    if record["exit_code"] is None:
        f.require(status in {"cancelled", "preempted"}, f"{path}.exit_code",
                  "null only for an externally cancelled/preempted job")
    else:
        code = f.integer(record["exit_code"], f"{path}.exit_code")
        f.require((code == 0) == (status == "succeeded") or status in {"cancelled", "preempted"},
                  f"{path}.terminal_status", "succeeded exactly when exit code is zero")
    f.require(record["consumed_experiment_digest"] == record["experiment_digest"], f"{path}.consumed_experiment_digest",
              "must byte-equal experiment_digest")
    return record


# ---------------------------------------------------------------------------
# Experiment

EXPERIMENT_KEYS = (
    "schema_id", "schema_version", "experiment_id", "purpose", "authorization_registry_digest",
    "source_record_digests", "purpose_authorization_digests", "source_manifest_digests", "split_manifest_digests",
    "lineage_root_digests", "model_lineage_root_digests", "non_model_lineage_root_digests",
    "decision_execution_receipt_digests", "model_selection_receipt_digests",
    "non_model_decision_execution_receipt_digests", "model_digest", "adapted_from_model_digest",
    "execution_condition_digest", "prospective_lock_digest", "candidate_ids", "decision_function_digest",
    "created_at", "record_digest",
)
NON_SELECTING_PURPOSES = frozenset({"engineering", "quarantine_inspection", "official_audit"})
MODEL_SELECTION_KINDS = frozenset({"checkpoint_selection", "promotion", "release"})


def validate_experiment(record: Any, path: str = "experiment") -> dict:
    from mmbu_phase1.vocab import PURPOSES

    f.record(record, "experiment", EXPERIMENT_KEYS, path)
    f.text(record["experiment_id"], f"{path}.experiment_id")
    purpose = f.one_of(record["purpose"], f"{path}.purpose", PURPOSES)
    f.digest(record["authorization_registry_digest"], f"{path}.authorization_registry_digest")
    for name in ("source_record_digests", "purpose_authorization_digests", "source_manifest_digests",
                 "split_manifest_digests", "lineage_root_digests", "model_lineage_root_digests",
                 "non_model_lineage_root_digests", "decision_execution_receipt_digests",
                 "model_selection_receipt_digests", "non_model_decision_execution_receipt_digests"):
        f.digest_set(record[name], f"{path}.{name}")
    for whole, left, right in (("lineage_root_digests", "model_lineage_root_digests", "non_model_lineage_root_digests"),
                               ("decision_execution_receipt_digests", "model_selection_receipt_digests",
                                "non_model_decision_execution_receipt_digests")):
        f.require(not set(record[left]) & set(record[right]), f"{path}.{left}", "partitions must be disjoint")
        f.require(set(record[left]) | set(record[right]) == set(record[whole]), f"{path}.{whole}",
                  "partition union must equal the whole set")
    f.require(len(record["source_record_digests"]) == len(record["purpose_authorization_digests"]),
              f"{path}.purpose_authorization_digests", "exactly one authorization per consumed source")
    f.digest(record["model_digest"], f"{path}.model_digest")
    f.nullable(f.digest, record["adapted_from_model_digest"], f"{path}.adapted_from_model_digest")
    f.digest(record["execution_condition_digest"], f"{path}.execution_condition_digest")
    if record["prospective_lock_digest"] is None:
        f.require(purpose in {"engineering", "quarantine_inspection"}, f"{path}.prospective_lock_digest",
                  "null only for engineering or quarantine_inspection")
    else:
        f.digest(record["prospective_lock_digest"], f"{path}.prospective_lock_digest")
    f.string_set(record["candidate_ids"], f"{path}.candidate_ids", nonempty=True)
    if record["decision_function_digest"] is None:
        f.require(purpose in NON_SELECTING_PURPOSES, f"{path}.decision_function_digest",
                  "null only when the purpose cannot select, promote, confirm, or release")
    else:
        f.digest(record["decision_function_digest"], f"{path}.decision_function_digest")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def check_experiment(store: Any, digest: Any, path: str = "experiment", *, started_at: str | None = None) -> dict:
    """Resolve every bound input; reject missing, unrelated, stale, late, contaminated, or incomplete inputs."""
    from mmbu_phase1 import admission, condition as conditions, decisions, lineage, locks
    from mmbu_phase1.registries import check_authorization_registry_chain

    record = validate_experiment(store.get(digest, "experiment", path), path)
    created = f.timestamp(record["created_at"], path)
    condition = conditions.check_execution_condition(store, record["execution_condition_digest"],
                                                     f"{path}.execution_condition_digest")
    f.require(created > f.timestamp(condition["created_at"], path), f"{path}.created_at",
              "the execution condition is created before the experiment")
    manifest = store.get(condition["request_set"]["example_manifest_digest"], "example_manifest", path)
    f.require(manifest["purpose"] == record["purpose"], f"{path}.purpose", "differs from the example-manifest purpose")
    registry = check_authorization_registry_chain(store, record["authorization_registry_digest"],
                                                  f"{path}.authorization_registry_digest")
    at = f.timestamp(started_at, path) if started_at is not None else None
    sources = {}
    for source_digest in record["source_record_digests"]:
        source = admission.check_source(store, source_digest, f"{path}.source_record_digests")
        if at is not None:
            admission.require_active_leaf(store, registry, source_digest, "source", at, f"{path}.source_record_digests")
        sources[source_digest] = source
    covered = set()
    for authorization_digest in record["purpose_authorization_digests"]:
        authorization = admission.check_purpose_authorization(store, authorization_digest,
                                                              f"{path}.purpose_authorization_digests")
        f.require(authorization["decision"] == "allowed" and authorization["purpose"] == record["purpose"],
                  f"{path}.purpose_authorization_digests", "authorization does not allow this purpose")
        f.require(authorization["source_digest"] in sources and authorization["source_digest"] not in covered,
                  f"{path}.purpose_authorization_digests", "unrelated or duplicate authorization")
        covered.add(authorization["source_digest"])
        if at is not None:
            admission.require_active_leaf(store, registry, authorization_digest, "authorization", at,
                                          f"{path}.purpose_authorization_digests")
        f.require(set(authorization["split_digests"]) <= set(record["split_manifest_digests"]),
                  f"{path}.split_manifest_digests", "authorized splits must be bound by the experiment")
    for split_digest in record["split_manifest_digests"]:
        split = admission.check_split(store, split_digest, f"{path}.split_manifest_digests")
        f.require(split["role"] in admission.PURPOSE_SPLIT_TABLE[record["purpose"]], f"{path}.split_manifest_digests",
                  "split role is illegal for the experiment purpose")
    synthetic_only = True
    for root in record["lineage_root_digests"]:
        receipt = lineage.validate_lineage_receipt(store.get(root, "lineage_receipt", f"{path}.lineage_root_digests"))
        lineage.require_purpose(store, receipt["artifact_digest"], record["purpose"], f"{path}.lineage_root_digests",
                                not_after_ns=created)
        is_model = root in record["model_lineage_root_digests"]
        f.require(is_model == (receipt["artifact_digest"] == record["model_digest"]), f"{path}.model_lineage_root_digests",
                  "lineage partition is not determined by type (model roots are the experiment model's lineage)")
        synthetic_only &= all(r["origin_class"] == "synthetic_engineering"
                              for r in lineage.walk(store, receipt["artifact_digest"], path))
        if is_model:
            parents = [e["parent_digest"] for e in receipt["parents"] if e["edge_role"] == "model"]
            expected = [record["adapted_from_model_digest"]] if record["adapted_from_model_digest"] else []
            f.require(parents == expected, f"{path}.adapted_from_model_digest",
                      "adapted_from_model_digest must equal the model lineage's one exact adapted-from parent")
    f.require(bool(record["model_lineage_root_digests"]), f"{path}.model_lineage_root_digests",
              "the experiment model must have a lineage root")
    for receipt_digest in record["decision_execution_receipt_digests"]:
        receipt = decisions.check_decision_receipt(store, receipt_digest, f"{path}.decision_execution_receipt_digests")
        plan = store.get(receipt["plan_digest"], "decision_plan", path)
        is_model = receipt_digest in record["model_selection_receipt_digests"]
        f.require(is_model == (plan["decision_kind"] in MODEL_SELECTION_KINDS), f"{path}.model_selection_receipt_digests",
                  "receipt partition is not determined by decision kind")
    if not record["decision_execution_receipt_digests"]:
        f.require(record["purpose"] in {"engineering", "quarantine_inspection"} and synthetic_only,
                  f"{path}.decision_execution_receipt_digests",
                  "empty only for a synthetic engineering/quarantine run that makes no selection")
    if record["prospective_lock_digest"] is not None:
        locks.check_lock_succession(store, record["prospective_lock_digest"], f"{path}.prospective_lock_digest")
    return record


# ---------------------------------------------------------------------------
# Reproducibility

REPRO_KEYS = (
    "schema_id", "schema_version", "reproducibility_id", "declared_level", "source_state_digest",
    "contract_manifest_digest", "experiment_digest", "execution_condition_digest", "environment_launch_policy_digest",
    "environment_launch_receipt_digest", "observed_condition", "prospective_lock_digest", "opening_receipt_digest",
    "opening_receipt_registry_digest", "operator_id", "started_at", "ended_at", "terminal_status", "command",
    "command_digest", "working_directory", "locale", "timezone", "filesystem", "environment_variables",
    "environment_artifact_digests", "os_kernel", "python", "container_digest", "hardware", "frameworks",
    "effective_numeric_settings", "distributed_settings", "seed_namespaces", "rng_state_artifact_digests",
    "worker_sampler_order", "cache_network_policy", "input_digests", "output_digests", "log_digests", "exit_code",
    "tolerances", "compared_run_digest", "observed_differences", "reproduction_status", "reproduction_limitation",
    "created_at", "record_digest",
)
HARDWARE_KEYS = ("host_id", "architecture", "cpu_model", "cpu_count", "ram_bytes", "gpu_driver", "gpus", "scheduler")
FRAMEWORK_KEYS = ("python_executable_digest", "python_version", "torch", "transformers", "accelerate", "deepspeed",
                  "fsdp", "cuda_runtime", "cuda_toolkit", "cudnn", "nccl", "compiler", "attention_library",
                  "quantization_library", "image_decoder", "dependency_lock_digest", "resolver_report_digest",
                  "package_artifact_digests", "install_command_digest", "package_source_digests")
OPTIONAL_FRAMEWORKS = ("torch", "transformers", "accelerate", "deepspeed", "fsdp", "cuda_runtime", "cuda_toolkit",
                       "cudnn", "nccl", "attention_library", "quantization_library", "image_decoder")
NUMERIC_KEYS = ("parameter_dtype", "compute_dtype", "autocast_dtype", "tf32", "deterministic_algorithms",
                "cudnn_benchmark", "cublas_workspace_config", "attention_backend", "cache_backend", "kernel_ids",
                "fused_optimizer", "compile_mode", "gradient_checkpointing", "fallbacks")
DISTRIBUTED_KEYS = ("world_size", "node_count", "rank_topology", "launcher", "rendezvous_digest",
                    "visible_device_order", "gradient_reduction", "sharding_policy", "microbatch_size",
                    "accumulation_steps", "effective_batch_size", "remainder_policy")
WORKER_KEYS = ("worker_count", "persistent_workers", "prefetch_factor", "multiprocessing_start_method",
               "worker_seed_rule_digest", "sampler_type", "sampler_epoch", "ordered_parent_ids_digest",
               "ordered_record_ids_digest", "batch_membership_digest", "rejected_skipped_digest",
               "padding_truncation_digest", "exposure_digest", "resume_cursor_digest")
CACHE_POLICY_KEYS = ("cache_root_digest", "snapshot_digests", "offline_requested", "network_denied",
                     "network_probe_digest", "remote_request_log_digest", "hidden_fetch_count")
SEED_KEYS = ("name", "seed", "derivation_rule_digest", "rng_state_digest")
TOLERANCE_KEYS = ("object_id", "metric", "absolute", "relative", "aggregation", "rationale", "pre_result_source_digest")
DIFFERENCE_KEYS = ("object_id", "comparison_kind", "metric", "observed", "allowed", "pass")
LEVELS = ("R-I", "R-B", "R-N", "R-S")
REPRODUCTION_STATUSES = ("not_requested", "matched", "within_tolerance", "mismatch", "unavailable")


def validate_reproducibility(record: Any, path: str = "reproducibility") -> dict:
    from mmbu_phase1.condition import validate_condition_objects

    f.record(record, "reproducibility", REPRO_KEYS, path)
    f.text(record["reproducibility_id"], f"{path}.reproducibility_id")
    f.one_of(record["declared_level"], f"{path}.declared_level", LEVELS)
    for name in ("source_state_digest", "contract_manifest_digest", "experiment_digest", "execution_condition_digest",
                 "environment_launch_policy_digest", "environment_launch_receipt_digest", "command_digest"):
        f.digest(record[name], f"{path}.{name}")
    validate_condition_objects(record["observed_condition"], f"{path}.observed_condition")
    governed = [record[name] for name in ("prospective_lock_digest", "opening_receipt_digest",
                                          "opening_receipt_registry_digest")]
    f.require(all(v is None for v in governed) or all(v is not None for v in governed), path,
              "lock, opening receipt, and opening registry are all null or all non-null")
    for value, name in zip(governed, ("prospective_lock_digest", "opening_receipt_digest", "opening_receipt_registry_digest")):
        f.nullable(f.digest, value, f"{path}.{name}")
    f.text(record["operator_id"], f"{path}.operator_id")
    started = f.timestamp(record["started_at"], f"{path}.started_at")
    f.require(f.timestamp(record["ended_at"], f"{path}.ended_at") >= started, f"{path}.ended_at", "must not precede start")
    status = f.one_of(record["terminal_status"], f"{path}.terminal_status", RUN_TERMINAL_STATUSES)
    command = f.array(record["command"], f"{path}.command", nonempty=True)
    for index, item in enumerate(command):
        f.text(item, f"{path}.command[{index}]", allow_empty=True)
    f.require(record["command_digest"] == canonical_value_digest(command), f"{path}.command_digest",
              "must be the canonical digest of the exact command")
    for name in ("working_directory", "locale", "timezone", "filesystem", "os_kernel", "python"):
        f.text(record[name], f"{path}.{name}")
    rows = f.array(record["environment_variables"], f"{path}.environment_variables", nonempty=True)
    for index, row in enumerate(rows):
        f.closed(row, f"{path}.environment_variables[{index}]", ("name", "value"))
    f.sorted_unique(rows, f"{path}.environment_variables", lambda r: r["name"].encode("utf-8"))
    for name in ("environment_artifact_digests", "rng_state_artifact_digests", "input_digests", "output_digests",
                 "log_digests"):
        f.digest_set(record[name], f"{path}.{name}", nonempty=name in {"input_digests", "log_digests"})
    f.nullable(f.digest, record["container_digest"], f"{path}.container_digest")
    hardware = f.closed(record["hardware"], f"{path}.hardware", HARDWARE_KEYS)
    for name in ("host_id", "architecture", "cpu_model"):
        f.text(hardware[name], f"{path}.hardware.{name}")
    f.integer(hardware["cpu_count"], f"{path}.hardware.cpu_count", minimum=1)
    f.integer(hardware["ram_bytes"], f"{path}.hardware.ram_bytes", minimum=0)
    f.array(hardware["gpus"], f"{path}.hardware.gpus")
    f.require((hardware["gpu_driver"] is None) == (hardware["gpus"] == []), f"{path}.hardware.gpu_driver",
              "null exactly when gpus is empty")
    f.require(hardware["scheduler"] is None, f"{path}.hardware.scheduler", "Phase 1A CPU runs have no scheduler allocation")
    frameworks = f.closed(record["frameworks"], f"{path}.frameworks", FRAMEWORK_KEYS)
    f.digest(frameworks["python_executable_digest"], f"{path}.frameworks.python_executable_digest")
    f.text(frameworks["python_version"], f"{path}.frameworks.python_version")
    for name in OPTIONAL_FRAMEWORKS:
        f.nullable(f.text, frameworks[name], f"{path}.frameworks.{name}")
    f.text(frameworks["compiler"], f"{path}.frameworks.compiler")
    for name in ("dependency_lock_digest", "resolver_report_digest", "install_command_digest"):
        f.digest(frameworks[name], f"{path}.frameworks.{name}")
    f.digest_set(frameworks["package_artifact_digests"], f"{path}.frameworks.package_artifact_digests")
    f.digest_set(frameworks["package_source_digests"], f"{path}.frameworks.package_source_digests")
    f.closed(record["effective_numeric_settings"], f"{path}.effective_numeric_settings", NUMERIC_KEYS)
    distributed = f.closed(record["distributed_settings"], f"{path}.distributed_settings", DISTRIBUTED_KEYS)
    if distributed["world_size"] == 1:
        f.require(distributed["rendezvous_digest"] is None, f"{path}.distributed_settings.rendezvous_digest",
                  "null only (and exactly) at world size one")
    f.closed(record["worker_sampler_order"], f"{path}.worker_sampler_order", WORKER_KEYS)
    cache = f.closed(record["cache_network_policy"], f"{path}.cache_network_policy", CACHE_POLICY_KEYS)
    if cache["remote_request_log_digest"] is None:
        f.require(cache["network_denied"] is True and cache["hidden_fetch_count"] == 0, f"{path}.cache_network_policy",
                  "request log may be null only when network denial is proven and hidden fetches are zero")
    seeds = f.array(record["seed_namespaces"], f"{path}.seed_namespaces", nonempty=True)
    for index, item in enumerate(seeds):
        f.closed(item, f"{path}.seed_namespaces[{index}]", SEED_KEYS)
        f.integer(item["seed"], f"{path}.seed_namespaces[{index}].seed", minimum=0)
    f.sorted_unique(seeds, f"{path}.seed_namespaces", lambda s: s["name"].encode("utf-8"))
    tolerances = f.array(record["tolerances"], f"{path}.tolerances")
    for index, item in enumerate(tolerances):
        f.closed(item, f"{path}.tolerances[{index}]", TOLERANCE_KEYS)
        f.number(item["absolute"], f"{path}.tolerances[{index}].absolute", minimum=0)
        f.number(item["relative"], f"{path}.tolerances[{index}].relative", minimum=0)
    code = record["exit_code"]
    if code is None:
        f.require(status in {"cancelled", "preempted"}, f"{path}.exit_code", "null only for external cancellation")
    else:
        f.integer(code, f"{path}.exit_code")
    reproduction = f.one_of(record["reproduction_status"], f"{path}.reproduction_status", REPRODUCTION_STATUSES)
    differences = f.array(record["observed_differences"], f"{path}.observed_differences")
    if reproduction in {"not_requested", "unavailable"}:
        f.require(record["compared_run_digest"] is None and differences == [], path,
                  "no compared run or differences without a requested comparison")
    else:
        f.digest(record["compared_run_digest"], f"{path}.compared_run_digest")
        f.require(bool(differences), f"{path}.observed_differences", "a comparison status requires difference rows")
    if reproduction == "unavailable":
        f.text(record["reproduction_limitation"], f"{path}.reproduction_limitation")
    else:
        f.require(record["reproduction_limitation"] is None, f"{path}.reproduction_limitation",
                  "nonempty only for unavailable")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def canonical_value_digest(value: Any) -> str:
    from mmbu_phase1 import canonical

    return canonical.value_digest(value)


def expected_numeric(condition: dict) -> dict:
    precision = condition["precision_backend"]
    return {"parameter_dtype": precision["parameter_dtype"], "compute_dtype": precision["compute_dtype"],
            "autocast_dtype": precision["autocast_dtype"], "tf32": precision["tf32"],
            "deterministic_algorithms": precision["deterministic_algorithms"],
            "cudnn_benchmark": precision["cudnn_benchmark"], "cublas_workspace_config": None,
            "attention_backend": precision["attention_backend"], "cache_backend": precision["cache_backend"],
            "kernel_ids": precision["kernel_digests"], "fused_optimizer": None, "compile_mode": precision["compile_mode"],
            "gradient_checkpointing": False, "fallbacks": precision["fallbacks"]}


def expected_distributed(condition: dict) -> dict:
    topology, batching = condition["runtime"]["topology"], condition["batching"]
    return {"world_size": topology["world_size"], "node_count": topology["node_count"], "rank_topology": "single_process",
            "launcher": topology["launcher"], "rendezvous_digest": None,
            "visible_device_order": topology["visible_device_order"], "gradient_reduction": "none",
            "sharding_policy": "none", "microbatch_size": batching["batch_size"], "accumulation_steps": 1,
            "effective_batch_size": batching["batch_size"], "remainder_policy": batching["remainder_policy"]}


def expected_worker_order(condition: dict, manifest: dict, exposure: dict) -> dict:
    from mmbu_phase1 import canonical

    batching = condition["batching"]
    units = {row["example_id"]: row["independent_unit_id"] for row in manifest["rows"]}
    return {"worker_count": batching["worker_count"], "persistent_workers": None, "prefetch_factor": None,
            "multiprocessing_start_method": None, "worker_seed_rule_digest": None, "sampler_type": "sequential",
            "sampler_epoch": 0,
            "ordered_parent_ids_digest": canonical.value_digest([units[i] for i in batching["row_order"]]),
            "ordered_record_ids_digest": canonical.value_digest(batching["row_order"]),
            "batch_membership_digest": canonical.value_digest(batching["batches"]),
            "rejected_skipped_digest": canonical.value_digest([]),
            "padding_truncation_digest": canonical.value_digest({
                "max_input_tokens": batching["max_input_tokens"], "padding_policy": batching["padding_policy"],
                "padding_side": batching["padding_side"], "truncation": batching["truncation"]}),
            "exposure_digest": canonical.value_digest(exposure), "resume_cursor_digest": None}


def expected_seed_namespaces(condition: dict, rng_state_digests: dict) -> list:
    from mmbu_phase1 import canonical

    randomness = condition["randomness"]
    return [{"name": s["name"], "seed": s["seed"],
             "derivation_rule_digest": canonical.value_digest({"derivation": s["derivation"], "parent_name": s["parent_name"],
                                                               "seed_namespace": randomness["seed_namespace"]}),
             "rng_state_digest": rng_state_digests[s["name"]]} for s in randomness["streams"]]


def check_reproducibility(store: Any, digest: Any, path: str = "reproducibility", *, contract_manifest_digest: str,
                          exposure: dict, rng_state_digests: dict) -> dict:
    """Bind experiment, condition, policy/receipt, and project every observed field leaf-for-leaf."""
    from mmbu_phase1 import canonical, condition as conditions, environment

    record = validate_reproducibility(store.get(digest, "reproducibility", path), path)
    experiment = validate_experiment(store.get(record["experiment_digest"], "experiment", path))
    f.require(record["execution_condition_digest"] == experiment["execution_condition_digest"],
              f"{path}.execution_condition_digest", "must equal the experiment's condition")
    condition = conditions.validate_execution_condition(store.get(record["execution_condition_digest"],
                                                                  "execution_condition", path))
    f.require(record["contract_manifest_digest"] == contract_manifest_digest, f"{path}.contract_manifest_digest",
              "must bind the exact contract manifest")
    f.require(record["environment_launch_policy_digest"] == condition["environment_launch_policy_digest"],
              f"{path}.environment_launch_policy_digest", "must equal the condition's policy digest")
    captures = []
    for artifact_digest in record["environment_artifact_digests"]:
        try:
            candidate = canonical.loads_canonical(store.artifact(artifact_digest, f"{path}.environment_artifact_digests"))
        except (canonical.CanonicalJSONError, f.ContractViolation):
            continue
        if type(candidate) is dict and set(candidate) == {
            "captured_at", "environment", "phase1_modules_loaded_before_capture"
        }:
            captures.append((artifact_digest, candidate))
    f.require(len(captures) == 1, f"{path}.environment_artifact_digests",
              "must bind exactly one complete child-environment capture")
    capture_digest, capture = captures[0]
    f.require(capture_digest in record["log_digests"], f"{path}.log_digests",
              "must include the child-environment capture digest")
    receipt = environment.check_environment_launch_receipt(store, record["environment_launch_receipt_digest"],
                                                           f"{path}.environment_launch_receipt_digest", capture=capture)
    f.require(receipt["policy_digest"] == record["environment_launch_policy_digest"], path,
              "the launch receipt resolves another policy")
    policy = store.get(receipt["policy_digest"], "environment_launch_policy", path)
    for name in conditions.OBJECT_NAMES:
        f.require(f.same(record["observed_condition"][name], condition[name]), f"{path}.observed_condition.{name}",
                  "observed condition differs from the prospective condition")
    runtime = condition["runtime"]
    projection = environment.projection(policy)
    for label, value in (("environment_variables", record["environment_variables"]),
                         ("receipt.passed_environment", receipt["passed_environment"]),
                         ("receipt.child_environment", receipt["child_environment"]),
                         ("observed_condition.runtime.environment_variables",
                          record["observed_condition"]["runtime"]["environment_variables"])):
        f.require(f.same(value, projection), f"{path}.{label}", "differs from the policy projection")
    f.require(record["locale"] == runtime["locale"] and record["timezone"] == runtime["timezone"]
              and record["filesystem"] == runtime["filesystem"], path, "locale/timezone/filesystem projection drift")
    f.require(record["working_directory"] == policy["working_directory"], f"{path}.working_directory",
              "must equal the policy working directory")
    f.require(record["command"] == receipt["argv"], f"{path}.command", "must be the exact launched command")
    f.require(record["exit_code"] == receipt["exit_code"], f"{path}.exit_code", "must equal the launch receipt")
    f.require(record["frameworks"]["python_executable_digest"] == runtime["python_executable_digest"]
              and record["frameworks"]["python_version"] == runtime["python_version"], f"{path}.frameworks",
              "python identity differs from the condition runtime")
    device = runtime["devices"][0]
    f.require(record["hardware"]["architecture"] == runtime["architecture"]
              and record["hardware"]["cpu_model"] == device["model"]
              and record["hardware"]["ram_bytes"] == device["memory_bytes"], f"{path}.hardware",
              "hardware differs from the condition devices")
    f.require(f.same(record["effective_numeric_settings"], expected_numeric(condition)),
              f"{path}.effective_numeric_settings", "differs from the condition precision/backend")
    f.require(f.same(record["distributed_settings"], expected_distributed(condition)), f"{path}.distributed_settings",
              "differs from the condition topology/batching")
    manifest = store.get(condition["request_set"]["example_manifest_digest"], "example_manifest", path)
    f.require(f.same(record["worker_sampler_order"], expected_worker_order(condition, manifest, exposure)),
              f"{path}.worker_sampler_order", "worker/sampler/order projection differs from the condition")
    f.require(f.same(record["seed_namespaces"], expected_seed_namespaces(condition, rng_state_digests)),
              f"{path}.seed_namespaces", "seed namespaces do not project the RNG streams")
    f.require(set(record["rng_state_artifact_digests"]) == set(rng_state_digests.values()), f"{path}.rng_state_artifact_digests",
              "RNG state artifacts must equal the per-stream state digests")
    cache = runtime["cache_network"]
    f.require(f.same({k: record["cache_network_policy"][k] for k in ("snapshot_digests", "offline_requested",
                                                                     "network_denied", "hidden_fetch_count")},
                     {k: cache[k] for k in ("snapshot_digests", "offline_requested", "network_denied", "hidden_fetch_count")})
              and record["cache_network_policy"]["cache_root_digest"] == canonical.value_digest(cache["cache_root_digests"])
              and record["cache_network_policy"]["remote_request_log_digest"] == cache["request_log_digest"],
              f"{path}.cache_network_policy", "cache/network policy differs from the condition")
    if experiment["prospective_lock_digest"] is None:
        f.require(record["prospective_lock_digest"] is None, path, "an unlocked experiment has no governing lock")
    else:
        f.require(record["prospective_lock_digest"] == experiment["prospective_lock_digest"], path, "lock mismatch")
    f.require(f.timestamp(record["started_at"], path) >= f.timestamp(receipt["started_at"], path)
              and f.timestamp(record["ended_at"], path) <= f.timestamp(receipt["ended_at"], path), path,
              "the run window must lie inside the launch window")
    return record


def check_run(store: Any, digest: Any, read: Any, path: str = "run", **repro_kwargs: Any) -> dict:
    """A finalized run binds its experiment, condition, reproducibility, and complete output manifest."""
    from mmbu_phase1 import layers

    record = validate_run(store.get(digest, "run", path), path)
    experiment = validate_experiment(store.get(record["experiment_digest"], "experiment", path))
    reproducibility = check_reproducibility(store, record["reproducibility_record_digest"],
                                            f"{path}.reproducibility_record_digest", **repro_kwargs)
    f.require(record["execution_condition_digest"] == experiment["execution_condition_digest"]
              == reproducibility["execution_condition_digest"], f"{path}.execution_condition_digest",
              "must equal the experiment and reproducibility condition")
    f.require(reproducibility["experiment_digest"] == record["experiment_digest"], path, "reproducibility binds another experiment")
    for name in ("source_state_digest", "command_digest", "terminal_status", "exit_code"):
        f.require(record[name] == reproducibility[name], f"{path}.{name}", "differs from the reproducibility record")
    manifest = layers.check_execution_output_manifest(store, record["output_manifest_digest"], read,
                                                      f"{path}.output_manifest_digest")
    f.require(manifest["experiment_digest"] == record["experiment_digest"]
              and manifest["execution_condition_digest"] == record["execution_condition_digest"], path,
              "output manifest binds another experiment or condition")
    f.require({e["sha256"] for e in manifest["entries"]} == set(reproducibility["output_digests"])
              and len(manifest["entries"]) == len(reproducibility["output_digests"]), f"{path}.output_manifest_digest",
              "entry SHA-256 set must equal the reproducibility output_digests exactly")
    f.require(record["input_manifest_digests"] == [manifest["example_manifest_digest"]], f"{path}.input_manifest_digests",
              "must be the complete manifest-input set: the governing example manifest")
    return record
