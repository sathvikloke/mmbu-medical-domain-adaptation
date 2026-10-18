"""Synthetic prospective-lock, opening-receipt, and finalized-run fixtures."""

import copy

from mmbu_phase1 import canonical
from mmbu_phase1.store import RecordStore

P = "mmbu.phase1."


def d(label):
    return canonical.raw_digest(("synthetic-lock:" + label).encode())


def sealed(record, **changes):
    updated = copy.deepcopy(record)
    updated.update(changes)
    return canonical.seal(updated)


def lock(created_at="2026-10-16T10:00:00Z", phase="discovery", purpose="adaptive_dev", qa_plan=None, **changes):
    record = {
        "schema_id": P + "prospective_lock",
        "schema_version": 1,
        "lock_id": "lock-1",
        "scope": {
            "scope_id": "scope-1",
            "purpose": purpose,
            "phase": phase,
            "primary_estimand_id": "estimand-primary",
            "comparison_ids": ["base-vs-adapted"],
            "analysis_population_digest": d("population"),
        },
        "source_state_digest": d("source-state"),
        "input_artifact_digests": sorted([d("input-a"), d("input-b")]),
        "qa_sampling_plan_digest": qa_plan,
        "excluded_result_digests": [],
        "candidate_ids": ["cand-a"],
        "seed_ids": ["seed-1"],
        "thresholds": [
            {"threshold_id": "t-primary", "metric_id": "net_task_change", "estimand_id": "estimand-primary",
             "value": 0, "unit": "grade", "direction": "at_least", "underpowered_disposition": "block"},
        ],
        "groups": [
            {"group_id": "g-all", "definition_digest": d("group-def"), "parent_unit": "patient", "minimum_parents": 3,
             "role": "primary", "underpowered_disposition": "block"},
        ],
        "evaluator_digest": d("evaluator"),
        "multiplicity_rule": {"family_id": "family-1", "alpha": 0.05, "method": "none", "hypothesis_ids": ["t-primary"],
                              "rule_digest": d("multiplicity")},
        "compute_plan_digest": d("compute"),
        "decision_function_digest": d("decision-fn"),
        "claim_boundary": {"primary_claim_id": "claim-primary", "allowed_claim_ids": ["claim-primary"],
                           "prohibited_claim_ids": ["claim-medical"], "failure_claim_id": "claim-failure"},
        "planned_opening_event": {
            "opening_kind": "first_output",
            "trigger": "first raw output",
            "not_before": "2026-10-16T10:00:30Z",
            "operator_role": "runner",
            "protected_artifact_digests": [d("protected")],
            "command_template_digest": d("command-template"),
        },
        "retry_policies": [
            {"retry_policy_id": "retry-oom", "failure_classes": ["oom"], "maximum_attempts": 2,
             "mutable_fields": ["batch_size"], "invariant_digests": [d("invariant")], "decision": "retry_same_condition"},
            {"retry_policy_id": "retry-stop", "failure_classes": ["load_failed"], "maximum_attempts": 1,
             "mutable_fields": ["none"], "invariant_digests": [d("invariant")], "decision": "stop"},
        ],
        "created_at": created_at,
        "supersedes_digest": None,
        "amendment_reason": None,
    }
    record.update(changes)
    return canonical.seal(record)


def run(run_id, status="failed", started="2026-10-16T10:02:00Z", ended="2026-10-16T10:03:00Z", exit_code=None):
    if exit_code is None:
        exit_code = 0 if status == "succeeded" else 1
    experiment = d("experiment-" + run_id)
    return canonical.seal({
        "schema_id": P + "run",
        "schema_version": 1,
        "run_id": run_id,
        "experiment_digest": experiment,
        "execution_condition_digest": d("condition"),
        "reproducibility_record_digest": d("repro-" + run_id),
        "source_state_digest": d("source-state"),
        "command_digest": d("command"),
        "input_manifest_digests": [d("example-manifest")],
        "output_manifest_digest": d("output-manifest-" + run_id),
        "started_at": started,
        "ended_at": ended,
        "exit_code": exit_code,
        "terminal_status": status,
        "consumed_experiment_digest": experiment,
    })


def chain_id(lock_digest, policy_id, root_run_id):
    return canonical.value_digest([lock_digest, policy_id, root_run_id])


def opening(lock_record, generation=0, prior=None, expected=("run-1",), failures=(), retries=(),
            first_access_at="2026-10-16T10:01:00Z", **changes):
    record = {
        "schema_id": P + "opening_receipt",
        "schema_version": 1,
        "opening_id": "opening-1",
        "lock_digest": lock_record["record_digest"],
        "source_state_digest": lock_record["source_state_digest"],
        "manifest_digests": [d("example-manifest")],
        "command_digest": d("command"),
        "environment_digest": d("environment"),
        "operator_id": "operator-1",
        "opening_kind": "first_output",
        "first_access_at": first_access_at,
        "receipt_generation": generation,
        "supersedes_receipt_digest": prior["record_digest"] if prior else None,
        "expected_run_ids": sorted(expected),
        "observed_failure_ids": sorted(failures),
        "retries": sorted(retries, key=lambda r: r["retry_id"]),
    }
    record.update(changes)
    return canonical.seal(record)


def retry(lock_record, retry_id, attempt, root, failed, retry_run, started, policy="retry-oom",
          failure_class="oom", changed=("batch_size",)):
    return {
        "retry_id": retry_id,
        "retry_chain_id": chain_id(lock_record["record_digest"], policy, root),
        "retry_policy_id": policy,
        "root_failed_run_id": root,
        "failed_run_id": failed,
        "retry_run_id": retry_run,
        "failure_class": failure_class,
        "attempt": attempt,
        "changed_fields": list(changed),
        "command_digest": d("command"),
        "started_at": started,
    }


def registry(generation, heads, prior=None, created_at=None):
    return canonical.seal({
        "schema_id": P + "opening_receipt_registry",
        "schema_version": 1,
        "registry_id": f"opening-registry-g{generation}",
        "generation": generation,
        "supersedes_registry_digest": prior["record_digest"] if prior else None,
        "heads": sorted(heads, key=lambda h: h["lock_digest"]),
        "created_at": created_at or f"2026-10-16T10:0{generation}:30Z",
    })


def head(lock_record, receipt):
    return {"lock_digest": lock_record["record_digest"], "opening_id": receipt["opening_id"],
            "head_receipt_digest": receipt["record_digest"], "receipt_generation": receipt["receipt_generation"]}


class RetryWorld:
    """Lock L; run-1 fails (oom); retry attempt 1 runs run-2, which also fails; attempt 2 runs run-3."""

    def __init__(self):
        self.lock = lock()
        self.run1 = run("run-1", "failed", "2026-10-16T10:02:00Z", "2026-10-16T10:03:00Z")
        self.run2 = run("run-2", "failed", "2026-10-16T10:04:00Z", "2026-10-16T10:05:00Z")
        self.r0 = opening(self.lock)
        self.r1 = opening(self.lock, 1, self.r0, expected=("run-1", "run-2"), failures=(self.run1["record_digest"],),
                          retries=(retry(self.lock, "retry-1", 1, "run-1", "run-1", "run-2", "2026-10-16T10:03:30Z"),))
        self.r2 = opening(self.lock, 2, self.r1, expected=("run-1", "run-2", "run-3"),
                          failures=(self.run1["record_digest"], self.run2["record_digest"]),
                          retries=(self.r1["retries"][0],
                                   retry(self.lock, "retry-2", 2, "run-1", "run-2", "run-3", "2026-10-16T10:05:30Z")))
        self.g0 = registry(0, [], created_at="2026-10-16T10:00:10Z")
        self.g1 = registry(1, [head(self.lock, self.r0)], self.g0, created_at="2026-10-16T10:00:55Z")
        self.g2 = registry(2, [head(self.lock, self.r1)], self.g1, created_at="2026-10-16T10:03:15Z")
        self.g3 = registry(3, [head(self.lock, self.r2)], self.g2, created_at="2026-10-16T10:05:15Z")

    def store(self, *extra, exclude=()):
        base = [self.lock, self.run1, self.run2, self.r0, self.r1, self.r2, self.g0, self.g1, self.g2, self.g3]
        excluded = {record["record_digest"] for record in exclude}
        return RecordStore([r for r in base if r["record_digest"] not in excluded] + list(extra))
