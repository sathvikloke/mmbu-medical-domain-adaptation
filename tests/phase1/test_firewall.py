"""External-only decision firewall: lineage, rule summaries, and decision receipts (synthetic canaries)."""

import copy
import unittest

from mmbu_phase1 import canonical, decisions, lineage
from mmbu_phase1.fields import ContractViolation

import firewall_fixtures as fx


def sealed(record, **changes):
    updated = copy.deepcopy(record)
    updated.update(changes)
    return canonical.seal(updated)


class LineageRecordTests(unittest.TestCase):
    def test_lineage_receipt_is_closed_and_sorted(self):
        world = fx.World()
        record = world.lineages[world.data]
        lineage.validate_lineage_receipt(record)
        bad = (
            {"origin_class": "external"},
            {"allowed_purposes": ["train", "engineering"]},
            {"allowed_purposes": ["development"]},
            {"parents": [{"parent_digest": fx.d("x"), "edge_role": "content"}]},
            {"parents": [{"parent_digest": fx.d("x")}]},
            {"parents": [{"parent_digest": fx.d("b"), "edge_role": "data"}, {"parent_digest": fx.d("b"), "edge_role": "data"}]},
            {"rights_receipt_digest": None},
            {"extra": 1},
        )
        for change in bad:
            with self.subTest(change=sorted(change)):
                with self.assertRaises(ContractViolation):
                    lineage.validate_lineage_receipt(sealed(record, **change))

    def test_purpose_and_split_are_independent(self):
        world = fx.World()
        store = world.store()
        self.assertEqual(lineage.effective_purposes(store, world.data), frozenset({"engineering", "train"}))
        record = world.lineages[world.data]
        for split_named_purpose in (["adaptive_dev", "dev"], ["development"], ["quarantine"]):
            with self.subTest(purposes=split_named_purpose):
                with self.assertRaises(ContractViolation):
                    lineage.validate_lineage_receipt(sealed(record, allowed_purposes=split_named_purpose))


class EffectivePurposeTests(unittest.TestCase):
    def setUp(self):
        self.world = fx.World()
        self.store = self.world.store()

    def test_firewall_rejects_public_source_for_promotion(self):
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, self.world.official, "train")
        lineage.require_purpose(self.store, self.world.official, "official_audit")

    def test_firewall_rejects_public_derivative_for_promotion(self):
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, self.world.derivative, "train")
        mixed = fx.d("mixed")
        record = fx.lineage(mixed, "external_reviewed", ["train"], [(self.world.data, "data"), (self.world.derivative, "data")],
                            reviewed=True)
        self.store.add(record)
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, mixed, "train")
        lying_manifest = fx.d("manifest-listing-official-content")
        self.store.add(fx.lineage(lying_manifest, "external_reviewed", ["train"], [(self.world.official, "data")], reviewed=True))
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, lying_manifest, "train")

    def test_lineage_receipt_is_required_for_promotion(self):
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, fx.d("no-lineage"), "train")
        orphan = fx.d("orphan")
        self.store.add(fx.lineage(orphan, "external_reviewed", ["train"], [(fx.d("missing-parent"), "data")], reviewed=True))
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, orphan, "train")
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, self.world.unknown, "train")
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, self.world.unknown, "engineering")

    def test_cycles_and_conflicting_lineage_declarations_reject(self):
        a, b = fx.d("cycle-a"), fx.d("cycle-b")
        self.store.add(fx.lineage(a, "synthetic_engineering", ["engineering"], [(b, "data")]))
        self.store.add(fx.lineage(b, "synthetic_engineering", ["engineering"], [(a, "data")]))
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, a, "engineering")
        forged_copy = fx.lineage(self.world.official, "external_reviewed", ["train"], reviewed=True, created_at=fx.T1)
        self.store.add(forged_copy)
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, self.world.official, "train")

    def test_empty_intersection_rejects(self):
        narrow = fx.d("narrow")
        self.store.add(fx.lineage(narrow, "external_reviewed", ["train"], [(self.world.synthetic, "data")], reviewed=True))
        self.assertEqual(lineage.effective_purposes(self.store, narrow), frozenset())
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, narrow, "train")

    def test_governance_reference_does_not_enter_data_purpose_intersection(self):
        payload = self.world.payload["record_digest"]
        self.assertEqual(lineage.effective_purposes(self.store, payload), frozenset({"train"}))
        through_data = fx.d("summary-as-data")
        self.store.add(fx.lineage(through_data, "external_reviewed", ["train"], [(self.world.summary, "data")], reviewed=True))
        self.assertEqual(lineage.effective_purposes(self.store, through_data), frozenset())

    def test_content_artifact_cannot_claim_governance_role(self):
        relabeled = fx.d("relabeled-content")
        self.store.add(fx.lineage(relabeled, "external_reviewed", ["train"], [(self.world.data, "governance")], reviewed=True))
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, relabeled, "train")
        relabeled_decision = fx.d("relabeled-decision")
        self.store.add(fx.lineage(relabeled_decision, "external_reviewed", ["train"],
                                  [(self.world.payload["record_digest"], "governance")], reviewed=True))
        with self.assertRaises(ContractViolation):
            lineage.require_purpose(self.store, relabeled_decision, "train")


class RuleSummaryTests(unittest.TestCase):
    def check_summary(self, extraction_record=None, summary_lineage=None):
        world = fx.World()
        if extraction_record is not None:
            world.extractions = [extraction_record]
        if summary_lineage is not None:
            world.lineages[world.summary] = summary_lineage
        store = world.store()
        return lineage.require_official_rule_summary(store, world.summary)

    def test_valid_two_reviewer_span_receipt_admits_summary(self):
        self.check_summary()

    def test_official_rule_summary_requires_two_reviewed_span_receipt(self):
        world = fx.World()
        o, s = world.official, world.summary
        good = fx.extraction(o, s)
        spans = good["included_spans"]
        variants = {
            "one_reviewer": fx.extraction(o, s, reviewers=("reviewer-a",), dispositions=("approved",)),
            "reviewer_collision": fx.extraction(o, s, reviewers=("reviewer-a", "reviewer-a")),
            "rejected_review": fx.extraction(o, s, dispositions=("approved", "rejected")),
            "missing_class": fx.extraction(o, s, classes=fx.EXCLUDED_CLASSES[1:]),
            "extra_class": fx.extraction(o, s, classes=sorted(fx.EXCLUDED_CLASSES + ["prompt"])),
            "unsorted_classes": fx.extraction(o, s, classes=list(reversed(fx.EXCLUDED_CLASSES))),
            "wrong_source_origin": sealed(good, source_origin_class="external_reviewed"),
            "empty_spans": sealed(good, included_spans=[]),
            "overlapping_spans": sealed(good, included_spans=[spans[0], {**spans[1], "start": 100}, spans[2]]),
            "unsorted_spans": sealed(good, included_spans=[spans[2], spans[0], spans[1]]),
            "empty_span": sealed(good, included_spans=[{**spans[0], "end": 0}, spans[1], spans[2]]),
            "reviewed_other_bytes": sealed(good, reviewer_attestations=[
                good["reviewer_attestations"][0], {**good["reviewer_attestations"][1], "reviewed_output_digest": fx.d("other")}]),
            "output_mismatch": fx.extraction(o, fx.d("changed-output")),
            "other_source": fx.extraction(fx.d("other-source"), s),
        }
        for name, record in variants.items():
            with self.subTest(variant=name):
                with self.assertRaises(ContractViolation):
                    self.check_summary(extraction_record=record)

    def test_summary_lineage_needs_exactly_one_governance_parent(self):
        world = fx.World()
        for parents in ([], [(world.official, "data")], [(world.official, "governance"), (world.data, "governance")]):
            with self.subTest(parents=parents):
                with self.assertRaises(ContractViolation):
                    self.check_summary(summary_lineage=fx.lineage(world.summary, "official_rule_summary", [], parents))
        with self.assertRaises(ContractViolation):
            self.check_summary(summary_lineage=fx.lineage(world.summary, "external_reviewed", ["train"],
                                                          [(world.official, "governance")], reviewed=True))


class DecisionReceiptTests(unittest.TestCase):
    def eligible(self, world):
        return decisions.check_decision_receipt(world.store(), world.receipt["record_digest"])

    def test_promotable_decision_with_clean_lineage_is_eligible(self):
        world = fx.World()
        self.eligible(world)

    def test_admitted_engineering_positive_control_passes(self):
        world = fx.World()
        world.build(inputs=[world.synthetic], purpose="engineering")
        self.eligible(world)

    def test_public_and_derivative_inputs_reject_for_promotable_plans(self):
        for attr in ("official", "derivative", "unknown"):
            with self.subTest(input=attr):
                world = fx.World()
                world.build(inputs=[world.data, getattr(world, attr)])
                with self.assertRaises(ContractViolation):
                    self.eligible(world)

    def test_restricted_hash_index_detects_copied_official_bytes_without_exposing_content(self):
        world = fx.World()
        copied = fx.d("official-rules-pdf-copy")
        world.lineages[copied] = fx.lineage(copied, "external_reviewed", ["train"], reviewed=True)
        world.build(inputs=[world.data, copied])
        decisions.check_decision_receipt(world.store(), world.receipt["record_digest"])
        index = frozenset({copied})
        with self.assertRaises(ContractViolation) as caught:
            decisions.check_decision_receipt(world.store(), world.receipt["record_digest"], official_hash_index=index)
        self.assertNotIn(copied, str(caught.exception))
        self.assertEqual(lineage.hash_index_hits([world.data, copied], index), 1)

    def test_decision_plan_precedes_protected_input_opening(self):
        cases = ({"created_at": "2026-10-16T10:12:00Z"}, {"created_at": "2026-10-16T10:06:00Z"})
        for change in cases:
            with self.subTest(change=change):
                world = fx.World()
                world.plan.update(change)
                world.relink()
                with self.assertRaises(ContractViolation):
                    self.eligible(world)
        world = fx.World()
        world.receipt = sealed(world.receipt, started_at="2026-10-16T10:04:00Z")
        with self.assertRaises(ContractViolation):
            self.eligible(world)

    def test_decision_runner_rejects_unallowlisted_mount_read_and_network(self):
        world0 = fx.World()
        extra = sorted(world0.receipt["mounted_input_digests"] + [world0.synthetic])
        changes = (
            {"mounted_input_digests": extra},
            {"mounted_input_digests": [world0.data]},
            {"observed_content_read_digests": sorted(world0.receipt["observed_content_read_digests"] + [world0.official])},
            {"observed_content_read_digests": [world0.data, world0.data]},
            {"attempted_denied_reads": [{"path": "/protected/official", "digest": world0.official}]},
            {"network_events": [{"host": "example.invalid", "port": 443}]},
            {"source_state_digest": fx.d("other-source-state")},
            {"command_digest": fx.d("other-command")},
            {"sandbox_policy_digest": fx.d("other-sandbox")},
        )
        for change in changes:
            with self.subTest(change=sorted(change)):
                world = fx.World()
                world.receipt = sealed(world.receipt, **change)
                with self.assertRaises(ContractViolation):
                    self.eligible(world)

    def test_decision_lineage_covers_every_mounted_content_input(self):
        world0 = fx.World()
        variants = (
            [(world0.data, "decision")],
            [(world0.data, "decision"), (world0.summary, "governance"), (world0.synthetic, "decision")],
            [(world0.data, "governance"), (world0.summary, "governance")],
            [(world0.data, "data"), (world0.summary, "governance")],
            [(world0.data, "decision"), (world0.summary, "decision")],
        )
        for parents in variants:
            with self.subTest(parents=parents):
                world = fx.World()
                world.output_lineage = fx.lineage(world.payload["record_digest"], "external_reviewed", ["train"], parents,
                                                  created_at="2026-10-16T10:15:00Z", reviewed=True)
                world.receipt = sealed(world.receipt, output_lineage_receipt_digest=world.output_lineage["record_digest"])
                with self.assertRaises(ContractViolation):
                    self.eligible(world)
        world = fx.World()
        world.output_lineage = sealed(world.output_lineage, origin_class="mmbu_derivative")
        world.receipt = sealed(world.receipt, output_lineage_receipt_digest=world.output_lineage["record_digest"])
        with self.assertRaises(ContractViolation):
            self.eligible(world)

    def test_copied_rationale_and_manual_decision_payload_are_ineligible(self):
        world = fx.World()
        world.payload["rationale_digest"] = world.data
        world.receipt["rationale_digest"] = world.data
        world.receipt["independent_review"]["reviewed_rationale_digest"] = world.data
        world.relink()
        with self.assertRaises(ContractViolation):
            self.eligible(world)
        world = fx.World()
        world.payload["created_at"] = "2026-10-16T09:00:00Z"
        world.relink()
        with self.assertRaises(ContractViolation):
            self.eligible(world)
        world = fx.World()
        world.receipt = sealed(world.receipt, emitted_output_digests=sorted([fx.d("other-payload"), world.rationale]))
        with self.assertRaises(ContractViolation):
            self.eligible(world)
        world = fx.World()
        world.receipt = sealed(world.receipt, decision_payload_digest=fx.d("manual-payload"))
        with self.assertRaises(ContractViolation):
            self.eligible(world)
        world = fx.World()
        world.receipt = sealed(world.receipt, exit_code=1, terminal_status="failed")
        with self.assertRaises(ContractViolation):
            self.eligible(world)

    def test_decision_operator_cannot_self_review(self):
        mutations = (
            lambda r: r["independent_review"].update(reviewer_id="operator-1"),
            lambda r: r["independent_review"].update(disposition="rejected"),
            lambda r: r["independent_review"].update(reviewed_payload_digest=fx.d("other")),
            lambda r: r["operator_attestation"].update(no_protected_memory_used=False),
            lambda r: r["operator_attestation"].update(no_undeclared_influence=False),
            lambda r: r["operator_attestation"].update(operator_id="operator-2"),
            lambda r: r.pop("independent_review"),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                world = fx.World()
                receipt = copy.deepcopy(world.receipt)
                mutate(receipt)
                world.receipt = canonical.seal(receipt)
                with self.assertRaises(ContractViolation):
                    self.eligible(world)

    def test_decision_records_are_closed_and_internally_consistent(self):
        world = fx.World()
        decisions.validate_decision_plan(world.plan)
        decisions.validate_decision_payload(world.payload)
        decisions.validate_decision_execution_receipt(world.receipt)
        plan_bad = (
            {"forbidden_origin_classes": ["mmbu_official"]},
            {"subject_ids": []},
            {"subject_ids": ["b", "a"]},
            {"allowed_input_digests": []},
            {"decision_kind": "baseline_choice"},
            {"extra": 1},
        )
        for change in plan_bad:
            with self.subTest(plan=sorted(change)):
                with self.assertRaises(ContractViolation):
                    decisions.validate_decision_plan(sealed(world.plan, **change))
        payload_bad = (
            {"selected_subject_ids": ["cand-z"]},
            {"selected_subject_ids": ["cand-b"]},
            {"dispositions": world.payload["dispositions"][:1]},
            {"dispositions": list(reversed(world.payload["dispositions"]))},
            {"claim_digests": []},
        )
        for change in payload_bad:
            with self.subTest(payload=sorted(change)):
                with self.assertRaises(ContractViolation):
                    decisions.validate_decision_payload(sealed(world.payload, **change))
        world2 = fx.World()
        world2.payload = sealed(world2.payload, purpose="adaptive_dev")
        world2.receipt = sealed(world2.receipt, decision_payload_digest=world2.payload["record_digest"])
        with self.assertRaises(ContractViolation):
            self.eligible(world2)

    def test_candidate_admission_plan_is_quarantine_only_single_subject(self):
        world = fx.World()
        plan = sealed(world.plan, decision_kind="candidate_admission", purpose="train")
        with self.assertRaises(ContractViolation):
            decisions.validate_decision_plan(plan)
        plan = sealed(world.plan, decision_kind="candidate_admission", purpose="quarantine_inspection")
        with self.assertRaises(ContractViolation):
            decisions.validate_decision_plan(plan)


if __name__ == "__main__":
    unittest.main()
