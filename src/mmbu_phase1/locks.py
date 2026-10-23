"""Prospective locks and opening receipts with exhaustive retry chains.

Phase 1 implements only these schemas, the chronology/head validator, and
synthetic tests; it fabricates no empirical lock.
"""

from __future__ import annotations

from typing import Any

from mmbu_phase1 import canonical, fields as f
from mmbu_phase1.decisions import validate_opening_event
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import PURPOSES

LOCK_KEYS = (
    "schema_id",
    "schema_version",
    "lock_id",
    "scope",
    "source_state_digest",
    "input_artifact_digests",
    "qa_sampling_plan_digest",
    "excluded_result_digests",
    "candidate_ids",
    "seed_ids",
    "thresholds",
    "groups",
    "evaluator_digest",
    "multiplicity_rule",
    "compute_plan_digest",
    "decision_function_digest",
    "claim_boundary",
    "planned_opening_event",
    "retry_policies",
    "created_at",
    "supersedes_digest",
    "amendment_reason",
    "record_digest",
)
SCOPE_KEYS = ("scope_id", "purpose", "phase", "primary_estimand_id", "comparison_ids", "analysis_population_digest")
LOCK_PHASES = ("engineering", "custody_inventory", "custody_qa", "discovery", "confirmation", "release")
THRESHOLD_KEYS = ("threshold_id", "metric_id", "estimand_id", "value", "unit", "direction", "underpowered_disposition")
UNDERPOWERED = ("block", "narrow_claim", "exploratory_only")
GROUP_KEYS = ("group_id", "definition_digest", "parent_unit", "minimum_parents", "role", "underpowered_disposition")
MULTIPLICITY_KEYS = ("family_id", "alpha", "method", "hypothesis_ids", "rule_digest")
CLAIM_BOUNDARY_KEYS = ("primary_claim_id", "allowed_claim_ids", "prohibited_claim_ids", "failure_claim_id")
RETRY_POLICY_KEYS = (
    "retry_policy_id",
    "failure_classes",
    "maximum_attempts",
    "mutable_fields",
    "invariant_digests",
    "decision",
)
# A same-condition retry may never change these governed members.
IMMUTABLE_UNDER_RETRY = frozenset({
    "candidate_ids",
    "claim_boundary",
    "estimand_id",
    "evaluator_digest",
    "groups",
    "multiplicity_rule",
    "primary_estimand_id",
    "scope",
    "seed_ids",
    "thresholds",
})
OPENING_KEYS = (
    "schema_id",
    "schema_version",
    "opening_id",
    "lock_digest",
    "source_state_digest",
    "manifest_digests",
    "command_digest",
    "environment_digest",
    "operator_id",
    "opening_kind",
    "first_access_at",
    "receipt_generation",
    "supersedes_receipt_digest",
    "expected_run_ids",
    "observed_failure_ids",
    "retries",
    "record_digest",
)
RETRY_KEYS = (
    "retry_id",
    "retry_chain_id",
    "retry_policy_id",
    "root_failed_run_id",
    "failed_run_id",
    "retry_run_id",
    "failure_class",
    "attempt",
    "changed_fields",
    "command_digest",
    "started_at",
)
PRESERVED_RECEIPT_SCALARS = (
    "opening_id",
    "lock_digest",
    "source_state_digest",
    "manifest_digests",
    "command_digest",
    "environment_digest",
    "operator_id",
    "opening_kind",
    "first_access_at",
)


def validate_thresholds(value: Any, path: str) -> list:
    items = f.array(value, path)
    for index, item in enumerate(items):
        label = f"{path}[{index}]"
        f.closed(item, label, THRESHOLD_KEYS)
        for name in ("threshold_id", "metric_id", "estimand_id", "unit"):
            f.text(item[name], f"{label}.{name}")
        f.number(item["value"], f"{label}.value")
        f.one_of(item["direction"], f"{label}.direction", ("at_least", "at_most", "within"))
        f.one_of(item["underpowered_disposition"], f"{label}.underpowered_disposition", UNDERPOWERED)
    return f.sorted_unique(items, path, lambda item: item["threshold_id"].encode())


def validate_groups(value: Any, path: str) -> list:
    items = f.array(value, path)
    for index, item in enumerate(items):
        label = f"{path}[{index}]"
        f.closed(item, label, GROUP_KEYS)
        f.text(item["group_id"], f"{label}.group_id")
        f.digest(item["definition_digest"], f"{label}.definition_digest")
        f.text(item["parent_unit"], f"{label}.parent_unit")
        f.integer(item["minimum_parents"], f"{label}.minimum_parents", minimum=1)
        f.one_of(item["role"], f"{label}.role", ("primary", "multiplicity_family", "diagnostic", "excluded"))
        f.one_of(item["underpowered_disposition"], f"{label}.underpowered_disposition", UNDERPOWERED)
    return f.sorted_unique(items, path, lambda item: item["group_id"].encode())


def validate_multiplicity(value: Any, path: str) -> dict:
    f.closed(value, path, MULTIPLICITY_KEYS)
    f.text(value["family_id"], f"{path}.family_id")
    f.number(value["alpha"], f"{path}.alpha", minimum=0, maximum=1, min_exclusive=True, max_exclusive=True)
    method = f.one_of(value["method"], f"{path}.method", ("bonferroni", "holm", "fixed_sequence", "none"))
    hypotheses = f.string_set(value["hypothesis_ids"], f"{path}.hypothesis_ids", nonempty=True)
    if method == "none":
        f.require(len(hypotheses) == 1, f"{path}.method", "'none' is legal only for one hypothesis")
    f.digest(value["rule_digest"], f"{path}.rule_digest")
    return value


def validate_lock_scope(value: Any, path: str) -> dict:
    f.closed(value, path, SCOPE_KEYS)
    f.text(value["scope_id"], f"{path}.scope_id")
    f.one_of(value["purpose"], f"{path}.purpose", PURPOSES)
    f.one_of(value["phase"], f"{path}.phase", LOCK_PHASES)
    f.text(value["primary_estimand_id"], f"{path}.primary_estimand_id")
    f.string_set(value["comparison_ids"], f"{path}.comparison_ids", nonempty=True)
    f.digest(value["analysis_population_digest"], f"{path}.analysis_population_digest")
    return value


def validate_claim_boundary(value: Any, path: str) -> dict:
    f.closed(value, path, CLAIM_BOUNDARY_KEYS)
    primary = f.text(value["primary_claim_id"], f"{path}.primary_claim_id")
    allowed = f.string_set(value["allowed_claim_ids"], f"{path}.allowed_claim_ids", nonempty=True)
    prohibited = f.string_set(value["prohibited_claim_ids"], f"{path}.prohibited_claim_ids")
    f.text(value["failure_claim_id"], f"{path}.failure_claim_id")
    f.require(primary in allowed, f"{path}.primary_claim_id", "primary claim must be allowed")
    f.require(not set(allowed) & set(prohibited), path, "allowed and prohibited claims must be disjoint")
    return value


def validate_retry_policies(value: Any, path: str) -> list:
    items = f.array(value, path)
    for index, item in enumerate(items):
        label = f"{path}[{index}]"
        f.closed(item, label, RETRY_POLICY_KEYS)
        f.text(item["retry_policy_id"], f"{label}.retry_policy_id")
        f.string_set(item["failure_classes"], f"{label}.failure_classes", nonempty=True)
        f.integer(item["maximum_attempts"], f"{label}.maximum_attempts", minimum=1)
        mutable = f.string_set(item["mutable_fields"], f"{label}.mutable_fields", nonempty=True)
        f.digest_set(item["invariant_digests"], f"{label}.invariant_digests", nonempty=True)
        decision = f.one_of(item["decision"], f"{label}.decision",
                            ("retry_same_condition", "new_exploratory_lineage", "stop"))
        if decision == "retry_same_condition":
            f.require(not set(mutable) & IMMUTABLE_UNDER_RETRY, f"{label}.mutable_fields",
                      "a same-condition retry cannot change a governed candidate/seed/threshold/group/evaluator/rule")
    return f.sorted_unique(items, path, lambda item: item["retry_policy_id"].encode())


def validate_prospective_lock(record: Any, path: str = "prospective_lock") -> dict:
    f.record(record, "prospective_lock", LOCK_KEYS, path)
    f.text(record["lock_id"], f"{path}.lock_id")
    scope = validate_lock_scope(record["scope"], f"{path}.scope")
    f.digest(record["source_state_digest"], f"{path}.source_state_digest")
    f.digest_set(record["input_artifact_digests"], f"{path}.input_artifact_digests", nonempty=True)
    if scope["phase"] == "custody_qa":
        f.digest(record["qa_sampling_plan_digest"], f"{path}.qa_sampling_plan_digest")
    else:
        f.require(record["qa_sampling_plan_digest"] is None, f"{path}.qa_sampling_plan_digest",
                  "non-null exactly for a custody_qa lock")
    f.digest_set(record["excluded_result_digests"], f"{path}.excluded_result_digests")
    f.string_set(record["candidate_ids"], f"{path}.candidate_ids")
    f.string_set(record["seed_ids"], f"{path}.seed_ids")
    validate_thresholds(record["thresholds"], f"{path}.thresholds")
    validate_groups(record["groups"], f"{path}.groups")
    for name in ("evaluator_digest", "compute_plan_digest", "decision_function_digest"):
        f.digest(record[name], f"{path}.{name}")
    validate_multiplicity(record["multiplicity_rule"], f"{path}.multiplicity_rule")
    validate_claim_boundary(record["claim_boundary"], f"{path}.claim_boundary")
    event = validate_opening_event(record["planned_opening_event"], f"{path}.planned_opening_event")
    validate_retry_policies(record["retry_policies"], f"{path}.retry_policies")
    created = f.timestamp(record["created_at"], f"{path}.created_at")
    f.require(created <= f.timestamp(event["not_before"], path), f"{path}.planned_opening_event.not_before",
              "a lock cannot plan an opening before it exists")
    supersedes, reason = record["supersedes_digest"], record["amendment_reason"]
    f.require((supersedes is None) == (reason is None), f"{path}.supersedes_digest",
              "supersedes_digest and amendment_reason are both null or both non-null")
    if supersedes is not None:
        f.digest(supersedes, f"{path}.supersedes_digest")
        f.text(reason, f"{path}.amendment_reason")
    return record


def _openings_for(store: RecordStore, lock_digest: str) -> list[dict]:
    return [r for r in store.records("opening_receipt") if r["lock_digest"] == lock_digest]


def check_lock_succession(store: RecordStore, lock_digest: Any, path: str = "prospective_lock") -> dict:
    """A changed lock must bind its predecessor; post-opening successors are exploratory."""
    record = validate_prospective_lock(store.get(lock_digest, "prospective_lock", path), path)
    chain = {record["record_digest"]}
    cursor = record
    while cursor["supersedes_digest"] is not None:
        prior = validate_prospective_lock(store.get(cursor["supersedes_digest"], "prospective_lock", path), path)
        f.require(f.timestamp(prior["created_at"], path) < f.timestamp(cursor["created_at"], path),
                  f"{path}.supersedes_digest", "a successor lock must be later than its predecessor")
        opened = [r for r in _openings_for(store, prior["record_digest"])
                  if f.timestamp(r["first_access_at"], path) <= f.timestamp(cursor["created_at"], path)]
        if opened:
            f.require(cursor["scope"]["phase"] != "confirmation", f"{path}.scope.phase",
                      "a post-opening successor creates exploratory lineage and cannot preserve confirmation")
            f.require(cursor["claim_boundary"]["primary_claim_id"] != prior["claim_boundary"]["primary_claim_id"],
                      f"{path}.claim_boundary", "a post-opening successor cannot preserve the old primary claim")
        chain.add(prior["record_digest"])
        cursor = prior
    for other in store.records("prospective_lock"):
        if other["lock_id"] == record["lock_id"] and other["record_digest"] not in chain:
            if f.timestamp(other["created_at"], path) <= f.timestamp(record["created_at"], path):
                f.fail(f"{path}.supersedes_digest", "silent amendment: an earlier lock with this ID is not superseded")
    return record


def governance_status(lock: dict, receipt: dict, first_output_at: str) -> str:
    """``confirmatory`` only when lock < opening <= first output; otherwise exploratory."""
    locked = f.timestamp(lock["created_at"], "lock.created_at")
    opened = f.timestamp(receipt["first_access_at"], "opening.first_access_at")
    output = f.timestamp(first_output_at, "first_output_at")
    if receipt["lock_digest"] == lock["record_digest"] and locked < opened <= output:
        return "confirmatory"
    return "exploratory"


def validate_opening_receipt(record: Any, path: str = "opening_receipt") -> dict:
    f.record(record, "opening_receipt", OPENING_KEYS, path)
    f.text(record["opening_id"], f"{path}.opening_id")
    for name in ("lock_digest", "source_state_digest", "command_digest", "environment_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.digest_set(record["manifest_digests"], f"{path}.manifest_digests", nonempty=True)
    f.text(record["operator_id"], f"{path}.operator_id")
    f.one_of(record["opening_kind"], f"{path}.opening_kind", ("first_output", "protected_access"))
    f.timestamp(record["first_access_at"], f"{path}.first_access_at")
    generation = f.integer(record["receipt_generation"], f"{path}.receipt_generation", minimum=0)
    if generation == 0:
        f.require(record["supersedes_receipt_digest"] is None, f"{path}.supersedes_receipt_digest",
                  "the initial receipt has a null predecessor")
    else:
        f.digest(record["supersedes_receipt_digest"], f"{path}.supersedes_receipt_digest")
    f.string_set(record["expected_run_ids"], f"{path}.expected_run_ids")
    f.digest_set(record["observed_failure_ids"], f"{path}.observed_failure_ids")
    retries = f.array(record["retries"], f"{path}.retries")
    for index, item in enumerate(retries):
        label = f"{path}.retries[{index}]"
        f.closed(item, label, RETRY_KEYS)
        for name in ("retry_id", "retry_policy_id", "root_failed_run_id", "failed_run_id", "retry_run_id", "failure_class"):
            f.text(item[name], f"{label}.{name}")
        f.digest(item["retry_chain_id"], f"{label}.retry_chain_id")
        f.integer(item["attempt"], f"{label}.attempt", minimum=1)
        f.string_set(item["changed_fields"], f"{label}.changed_fields")
        f.digest(item["command_digest"], f"{label}.command_digest")
        f.timestamp(item["started_at"], f"{label}.started_at")
    f.sorted_unique(retries, f"{path}.retries", lambda item: item["retry_id"].encode())
    return record


def retry_chain_id(lock_digest: str, policy_id: str, root_failed_run_id: str) -> str:
    return canonical.value_digest([lock_digest, policy_id, root_failed_run_id])


def check_opening_receipt_chain(store: RecordStore, receipt_digest: Any, path: str = "opening_receipt") -> dict:
    """Validate one receipt, its complete unbranched predecessor chain, failures, and retries."""
    from mmbu_phase1.experiment import validate_run

    receipt = validate_opening_receipt(store.get(receipt_digest, "opening_receipt", path), path)
    lock = validate_prospective_lock(store.get(receipt["lock_digest"], "prospective_lock", f"{path}.lock_digest"))
    f.require(f.timestamp(receipt["first_access_at"], path) > f.timestamp(lock["created_at"], path),
              f"{path}.first_access_at", "opening must be strictly later than the governing lock")
    f.require(receipt["opening_kind"] == lock["planned_opening_event"]["opening_kind"], f"{path}.opening_kind",
              "differs from the lock's planned opening")
    f.require(receipt["source_state_digest"] == lock["source_state_digest"], f"{path}.source_state_digest",
              "differs from the lock")
    chain = [receipt]
    cursor = receipt
    while cursor["supersedes_receipt_digest"] is not None:
        prior = validate_opening_receipt(store.get(cursor["supersedes_receipt_digest"], "opening_receipt", path), path)
        label = f"{path}<-g{prior['receipt_generation']}"
        f.require(prior["receipt_generation"] == cursor["receipt_generation"] - 1, label, "generation must increment by one")
        for name in PRESERVED_RECEIPT_SCALARS:
            f.require(f.same(prior[name], cursor[name]), f"{label}.{name}", "successor changed a prior scalar")
        f.require(set(prior["expected_run_ids"]) <= set(cursor["expected_run_ids"]), label, "expected runs dropped")
        f.require(set(prior["observed_failure_ids"]) <= set(cursor["observed_failure_ids"]), label, "failures dropped")
        prior_retries = {item["retry_id"]: item for item in prior["retries"]}
        current_retries = {item["retry_id"]: item for item in cursor["retries"]}
        for retry_id, item in prior_retries.items():
            f.require(retry_id in current_retries and f.same(item, current_retries[retry_id]), label,
                      "a prior retry was rewritten or dropped")
        f.require(len(set(current_retries) - set(prior_retries)) <= 1, label, "at most one newly authorized retry")
        chain.append(prior)
        cursor = prior
    f.require(cursor["receipt_generation"] == 0, path, "receipt chain does not reach generation zero")
    for member in chain:
        for sibling in store.records("opening_receipt"):
            if (sibling["record_digest"] != member["record_digest"]
                    and sibling["lock_digest"] == member["lock_digest"]
                    and sibling["opening_id"] == member["opening_id"]
                    and sibling["supersedes_receipt_digest"] == member["supersedes_receipt_digest"]):
                f.fail(path, "opening receipt chain branches")
    failures: dict[str, dict] = {}
    for digest in receipt["observed_failure_ids"]:
        run = validate_run(store.get(digest, "run", f"{path}.observed_failure_ids"))
        f.require(run["terminal_status"] in {"failed", "cancelled", "preempted"}, f"{path}.observed_failure_ids",
                  "only finalized failed/cancelled/preempted runs are failures")
        failures[run["run_id"]] = run
    policies = {item["retry_policy_id"]: item for item in lock["retry_policies"]}
    retry_runs = [item["retry_run_id"] for item in receipt["retries"]]
    f.require(len(retry_runs) == len(set(retry_runs)), f"{path}.retries", "retry_run_id must be unique")
    chains: dict[str, list[dict]] = {}
    for item in receipt["retries"]:
        label = f"{path}.retries[{item['retry_id']}]"
        policy = policies.get(item["retry_policy_id"])
        f.require(policy is not None, label, "retry policy is not prospectively allowed by the lock")
        f.require(policy["decision"] != "stop", label, "a stop policy permits no retry")
        f.require(item["failure_class"] in policy["failure_classes"], label, "failure class is not authorized")
        f.require(set(item["changed_fields"]) <= set(policy["mutable_fields"]), label, "changed field is not mutable")
        f.require(item["retry_chain_id"] == retry_chain_id(receipt["lock_digest"], item["retry_policy_id"],
                                                          item["root_failed_run_id"]), label, "retry_chain_id mismatch")
        f.require(item["retry_run_id"] in receipt["expected_run_ids"], label, "retry run is not an expected run")
        failed = failures.get(item["failed_run_id"])
        f.require(failed is not None, label, "failed run does not resolve to a finalized observed failure")
        f.require(f.timestamp(failed["ended_at"], label) < f.timestamp(item["started_at"], label), label,
                  "retry started before the failed run ended")
        chains.setdefault(item["retry_chain_id"], []).append(item)
    for chain_id, items in chains.items():
        items.sort(key=lambda item: item["attempt"])
        attempts = [item["attempt"] for item in items]
        f.require(attempts == list(range(1, len(items) + 1)), f"{path}.retries", "attempts must be exactly 1..n")
        policy = policies[items[0]["retry_policy_id"]]
        f.require(len(items) <= policy["maximum_attempts"], f"{path}.retries", "retry attempts exceed the policy")
        for index, item in enumerate(items):
            expected_failed = item["root_failed_run_id"] if index == 0 else items[index - 1]["retry_run_id"]
            f.require(item["failed_run_id"] == expected_failed, f"{path}.retries", "retry does not continue its chain")
            if index:
                f.require(f.timestamp(items[index - 1]["started_at"], path) < f.timestamp(item["started_at"], path),
                          f"{path}.retries", "retry start times must strictly increase")
    return receipt


def require_registered_head(store: RecordStore, registry_digest: Any, receipt_digest: Any,
                            path: str = "opening_receipt_registry") -> dict:
    """The receipt is the registered head for its lock in a valid registry chain."""
    from mmbu_phase1.registries import check_opening_receipt_registry_chain

    registry = check_opening_receipt_registry_chain(store, registry_digest, path)
    receipt = check_opening_receipt_chain(store, receipt_digest, f"{path}.receipt")
    heads = [h for h in registry["heads"] if h["lock_digest"] == receipt["lock_digest"]]
    f.require(len(heads) == 1 and heads[0]["head_receipt_digest"] == receipt_digest, path,
              "receipt is not the active registered head (stale or unregistered)")
    return receipt
