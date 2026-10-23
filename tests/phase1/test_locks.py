"""Prospective locks, opening receipts, retry chains, and opening-receipt registry heads."""

import copy
import unittest

from mmbu_phase1 import canonical, locks, registries
from mmbu_phase1.experiment import validate_run
from mmbu_phase1.fields import ContractViolation

import lock_fixtures as fx


def nested(record, key, **changes):
    updated = copy.deepcopy(record)
    if isinstance(updated[key], list):
        updated[key][0].update(changes)
    else:
        updated[key].update(changes)
    return canonical.seal(updated)


class ProspectiveLockShapeTests(unittest.TestCase):
    def test_valid_lock_and_closed_members(self):
        record = fx.lock()
        locks.validate_prospective_lock(record)
        bad = (
            nested(record, "scope", phase="exploration"),
            nested(record, "scope", comparison_ids=[]),
            nested(record, "scope", comparison_ids=["b", "a"]),
            nested(record, "scope", extra=1),
            nested(record, "thresholds", direction="greater"),
            nested(record, "thresholds", underpowered_disposition="ignore"),
            nested(record, "thresholds", value="0.5"),
            nested(record, "groups", minimum_parents=0),
            nested(record, "groups", role="selected"),
            nested(record, "multiplicity_rule", alpha=1),
            nested(record, "multiplicity_rule", alpha=0),
            nested(record, "multiplicity_rule", method="fdr"),
            nested(record, "multiplicity_rule", hypothesis_ids=["a", "b"]),
            nested(record, "claim_boundary", primary_claim_id="claim-other"),
            nested(record, "claim_boundary", prohibited_claim_ids=["claim-primary"]),
            nested(record, "planned_opening_event", protected_artifact_digests=[]),
            nested(record, "planned_opening_event", opening_kind="manual"),
            nested(record, "retry_policies", failure_classes=[]),
            nested(record, "retry_policies", maximum_attempts=0),
            nested(record, "retry_policies", mutable_fields=["seed_ids"]),
            nested(record, "retry_policies", mutable_fields=["thresholds"]),
            nested(record, "retry_policies", invariant_digests=[]),
            fx.sealed(record, supersedes_digest=fx.d("prior")),
            fx.sealed(record, amendment_reason="changed seed"),
            fx.sealed(record, qa_sampling_plan_digest=fx.d("qa-plan")),
            fx.sealed(record, thresholds=list(reversed(record["thresholds"] * 2))),
            fx.sealed(record, extra_field=1),
        )
        for index, mutated in enumerate(bad):
            with self.subTest(case=index):
                with self.assertRaises(ContractViolation):
                    locks.validate_prospective_lock(mutated)

    def test_custody_qa_lock_requires_its_plan_digest(self):
        locks.validate_prospective_lock(fx.lock(phase="custody_qa", purpose="quarantine_inspection", qa_plan=fx.d("qa-plan")))
        with self.assertRaises(ContractViolation):
            locks.validate_prospective_lock(fx.lock(phase="custody_qa", purpose="quarantine_inspection"))

    def test_none_multiplicity_needs_exactly_one_hypothesis(self):
        record = fx.lock()
        two = nested(record, "multiplicity_rule", method="holm", hypothesis_ids=["a", "b"])
        locks.validate_prospective_lock(two)


class LockSuccessionTests(unittest.TestCase):
    def test_pre_opening_amendment_must_bind_predecessor(self):
        first = fx.lock()
        amended = fx.lock(created_at="2026-10-16T10:00:20Z", seed_ids=["seed-2"], supersedes_digest=first["record_digest"],
                          amendment_reason="seed corrected before opening")
        store = fx.RecordStore([first, amended])
        locks.check_lock_succession(store, amended["record_digest"])
        silent = fx.lock(created_at="2026-10-16T10:00:20Z", seed_ids=["seed-2"])
        with self.assertRaises(ContractViolation):
            locks.check_lock_succession(fx.RecordStore([first, silent]), silent["record_digest"])

    def test_post_opening_amendment_cannot_preserve_confirmation(self):
        first = fx.lock(phase="confirmation", purpose="confirmation")
        receipt = fx.opening(first)
        later_opening = {**first["planned_opening_event"], "not_before": "2026-10-16T10:03:00Z"}
        late = fx.lock(created_at="2026-10-16T10:02:00Z", phase="confirmation", purpose="confirmation",
                       planned_opening_event=later_opening,
                       supersedes_digest=first["record_digest"], amendment_reason="threshold changed after opening")
        locks.validate_prospective_lock(late)
        store = fx.RecordStore([first, receipt, late])
        with self.assertRaises(ContractViolation):
            locks.check_lock_succession(store, late["record_digest"])
        exploratory = fx.lock(created_at="2026-10-16T10:02:00Z", phase="discovery", purpose="adaptive_dev",
                              claim_boundary={"primary_claim_id": "claim-exploratory", "allowed_claim_ids": ["claim-exploratory"],
                                              "prohibited_claim_ids": ["claim-primary"], "failure_claim_id": "claim-failure"},
                              planned_opening_event=later_opening,
                              supersedes_digest=first["record_digest"], amendment_reason="new exploratory lineage")
        locks.check_lock_succession(fx.RecordStore([first, receipt, exploratory]), exploratory["record_digest"])

    def test_minimal_chronology_examples(self):
        lock_record = fx.lock()
        receipt = fx.opening(lock_record)
        self.assertEqual(locks.governance_status(lock_record, receipt, "2026-10-16T10:01:30Z"), "confirmatory")
        self.assertEqual(locks.governance_status(lock_record, receipt, "2026-10-16T09:59:00Z"), "exploratory")
        with self.assertRaises(ContractViolation):
            locks.check_opening_receipt_chain(fx.RecordStore([lock_record, fx.opening(lock_record, first_access_at="2026-10-16T10:00:00Z")]),
                                              fx.opening(lock_record, first_access_at="2026-10-16T10:00:00Z")["record_digest"])


class OpeningReceiptTests(unittest.TestCase):
    def test_retry_chain_with_finalized_failures_validates(self):
        world = fx.RetryWorld()
        store = world.store()
        for receipt in (world.r0, world.r1, world.r2):
            locks.check_opening_receipt_chain(store, receipt["record_digest"])
        validate_run(world.run1)

    def test_successor_preserves_every_prior_scalar_and_retry(self):
        world = fx.RetryWorld()
        changes = (
            {"operator_id": "operator-2"},
            {"command_digest": fx.d("other-command")},
            {"first_access_at": "2026-10-16T10:01:05Z"},
            {"opening_id": "opening-2"},
            {"expected_run_ids": ["run-2"]},
            {"observed_failure_ids": []},
            {"receipt_generation": 2},
            {"supersedes_receipt_digest": world.r1["record_digest"]},
        )
        for change in changes:
            with self.subTest(change=sorted(change)):
                bad = fx.sealed(world.r1, **change)
                with self.assertRaises(ContractViolation) as caught:
                    locks.check_opening_receipt_chain(world.store(bad, exclude=(world.r1, world.r2, world.g2, world.g3)),
                                                      bad["record_digest"])
                self.assertNotIn("branches", str(caught.exception))

    def test_retry_chain_resets_branches_and_overruns_reject(self):
        world = fx.RetryWorld()
        first = world.r1["retries"][0]
        reset = fx.retry(world.lock, "retry-2", 1, "run-1", "run-1", "run-3", "2026-10-16T10:05:30Z")
        overrun = fx.retry(world.lock, "retry-3", 3, "run-1", "run-3", "run-4", "2026-10-16T10:07:30Z")
        variants = {
            "reset": [first, reset],
            "skipped_attempt": [first, {**fx.retry(world.lock, "retry-2", 3, "run-1", "run-2", "run-3", "2026-10-16T10:05:30Z")}],
            "wrong_parent": [first, fx.retry(world.lock, "retry-2", 2, "run-1", "run-1", "run-3", "2026-10-16T10:05:30Z")],
            "not_after_failure": [first, fx.retry(world.lock, "retry-2", 2, "run-1", "run-2", "run-3", "2026-10-16T10:04:30Z")],
            "unlisted_field": [first, fx.retry(world.lock, "retry-2", 2, "run-1", "run-2", "run-3", "2026-10-16T10:05:30Z",
                                               changed=("seed_ids",))],
            "stop_policy": [first, fx.retry(world.lock, "retry-2", 1, "run-2", "run-2", "run-3", "2026-10-16T10:05:30Z",
                                            policy="retry-stop", failure_class="load_failed", changed=("none",))],
            "unknown_policy": [first, fx.retry(world.lock, "retry-2", 1, "run-2", "run-2", "run-3", "2026-10-16T10:05:30Z",
                                               policy="retry-any")],
            "wrong_class": [first, fx.retry(world.lock, "retry-2", 2, "run-1", "run-2", "run-3", "2026-10-16T10:05:30Z",
                                            failure_class="timeout")],
            "bad_chain_id": [first, {**fx.retry(world.lock, "retry-2", 2, "run-1", "run-2", "run-3", "2026-10-16T10:05:30Z"),
                                     "retry_chain_id": fx.d("forged-chain")}],
        }
        for name, retries in variants.items():
            with self.subTest(variant=name):
                bad = fx.opening(world.lock, 2, world.r1, expected=("run-1", "run-2", "run-3"),
                                 failures=(world.run1["record_digest"], world.run2["record_digest"]), retries=retries)
                with self.assertRaises(ContractViolation) as caught:
                    locks.check_opening_receipt_chain(world.store(bad, exclude=(world.r2, world.g3)), bad["record_digest"])
                self.assertNotIn("branches", str(caught.exception))
        with self.subTest(variant="max_attempts"):
            run3 = fx.run("run-3", "failed", "2026-10-16T10:06:00Z", "2026-10-16T10:07:00Z")
            bad = fx.opening(world.lock, 3, world.r2, expected=("run-1", "run-2", "run-3", "run-4"),
                             failures=(world.run1["record_digest"], world.run2["record_digest"], run3["record_digest"]),
                             retries=(*world.r2["retries"], overrun))
            with self.assertRaises(ContractViolation) as caught:
                locks.check_opening_receipt_chain(world.store(run3, bad), bad["record_digest"])
            self.assertIn("exceed", str(caught.exception))

    def test_failures_must_be_finalized_unsuccessful_runs(self):
        world = fx.RetryWorld()
        good_run = fx.run("run-ok", "succeeded")
        later = (world.r1, world.r2, world.g2, world.g3)
        bad = fx.opening(world.lock, 1, world.r0, expected=("run-1", "run-ok"), failures=(good_run["record_digest"],))
        with self.assertRaises(ContractViolation) as caught:
            locks.check_opening_receipt_chain(world.store(good_run, bad, exclude=later), bad["record_digest"])
        self.assertIn("finalized failed", str(caught.exception))
        missing = fx.opening(world.lock, 1, world.r0, expected=("run-1",), failures=(fx.d("unresolved-run"),))
        with self.assertRaises(ContractViolation) as caught:
            locks.check_opening_receipt_chain(world.store(missing, exclude=later), missing["record_digest"])
        self.assertIn("does not resolve", str(caught.exception))

    def test_run_record_rules(self):
        validate_run(fx.run("run-x", "succeeded"))
        for record in (fx.run("run-x", "succeeded", exit_code=1),
                       fx.run("run-x", "failed", exit_code=0),
                       fx.run("run-x", "failed", started="2026-10-16T10:05:00Z", ended="2026-10-16T10:04:00Z"),
                       fx.sealed(fx.run("run-x"), consumed_experiment_digest=fx.d("other")),
                       fx.sealed(fx.run("run-x"), exit_code=None),
                       fx.sealed(fx.run("run-x"), terminal_status="running"),
                       fx.sealed(fx.run("run-x"), input_manifest_digests=[])):
            with self.subTest(record=record["terminal_status"]):
                with self.assertRaises(ContractViolation):
                    validate_run(record)
        validate_run(fx.sealed(fx.run("run-x", "cancelled"), exit_code=None))


class OpeningRegistryHeadTests(unittest.TestCase):
    def test_registry_generations_track_the_receipt_heads(self):
        world = fx.RetryWorld()
        store = world.store()
        registries.check_opening_receipt_registry_chain(store, world.g3["record_digest"])
        locks.require_registered_head(store, world.g3["record_digest"], world.r2["record_digest"])
        with self.assertRaises(ContractViolation):
            locks.require_registered_head(store, world.g3["record_digest"], world.r1["record_digest"])

    def test_registry_rejects_branch_rewrite_removal_and_backward_moves(self):
        world = fx.RetryWorld()
        other_lock = fx.lock(lock_id="lock-2", created_at="2026-10-16T10:00:01Z")
        other_receipt = fx.opening(other_lock)
        branch = fx.opening(world.lock, 1, world.r0, expected=("run-1", "run-9"))
        bad = {
            "skip_successor": fx.registry(2, [fx.head(world.lock, world.r2)], world.g1),
            "branch": fx.registry(2, [fx.head(world.lock, branch)], world.g1),
            "removal": fx.registry(2, [], world.g1),
            "backward": fx.registry(3, [fx.head(world.lock, world.r0)], world.g2),
            "two_changes": fx.registry(3, [fx.head(world.lock, world.r2), fx.head(other_lock, other_receipt)], world.g2),
            "skip_generation": fx.registry(3, [fx.head(world.lock, world.r1)], world.g1),
            "rewritten_head": fx.registry(2, [{**fx.head(world.lock, world.r1), "opening_id": "opening-x"}], world.g1),
        }
        for name, registry in bad.items():
            with self.subTest(variant=name):
                extra = (branch,) if name == "branch" else ()
                store = world.store(other_lock, other_receipt, *extra, registry)
                with self.assertRaises(ContractViolation) as caught:
                    registries.check_opening_receipt_registry_chain(store, registry["record_digest"])
                if name != "branch":
                    self.assertNotIn("branches", str(caught.exception))
        added = fx.registry(4, [fx.head(world.lock, world.r2), fx.head(other_lock, other_receipt)], world.g3,
                            created_at="2026-10-16T10:06:00Z")
        registries.check_opening_receipt_registry_chain(world.store(other_lock, other_receipt, added), added["record_digest"])


if __name__ == "__main__":
    unittest.main()
