"""Real-source admission validators exercised only with synthetic canary records."""

import copy
import unittest

from mmbu_phase1 import admission, canonical, registries
from mmbu_phase1.fields import ContractViolation
from tests.phase1.external_trust_fixtures import external_authority_for

import admission_fixtures as fx
from admission_fixtures import AdmissionWorld, d, t


def resealed(record, **changes):
    updated = copy.deepcopy(record)
    updated.update(changes)
    return canonical.seal(updated)


class AdmissionTestCase(unittest.TestCase):
    def assertRejects(self, fragment, check, *args):
        with self.assertRaises(ContractViolation) as caught:
            check(*args)
        self.assertIn(fragment, str(caught.exception))
        return caught.exception

    def world_rejects(self, fragment, overrides, step="source_approved", checker=None):
        world = AdmissionWorld(overrides)
        checker = checker or admission.check_source
        return self.assertRejects(fragment, checker, world.store(), world.digest(step))


class CompleteChainTests(AdmissionTestCase):
    def test_complete_synthetic_admission_chain_validates(self):
        world = AdmissionWorld()
        store = world.store()
        admission.check_source(store, world.digest("source_approved"))
        admission.check_custody_summary(store, world.digest("custody"))
        admission.check_purpose_authorization(store, world.digest("engineering_authorization"))
        registries.check_authorization_registry_chain(store, world.digest("registry_g3"))
        registry = world.get("registry_g3")
        admission.require_active_leaf(store, registry, world.digest("source_approved"), "source",
                                      admission.ts(t("09:00:00"), "at"), "x")
        admission.require_active_leaf(store, registry, world.digest("engineering_authorization"), "authorization",
                                      admission.ts(t("09:00:00"), "at"), "x")

    def test_real_source_admission_requires_exact_external_authority(self):
        world = AdmissionWorld()
        store = world.store()
        source_digest = world.digest("source_approved")
        subject = admission.source_admission_authority_subject(store, source_digest)
        authority = external_authority_for(
            subject, namespace="mmbu.phase1.source-admission.v1",
            principal="external-source-board", role="source-admission-authority",
            signed_at=t("08:45:00"), verified_at=t("08:46:00"),
        )
        source = admission.check_externally_authorized_source(
            store, source_digest, authority, not_after=t("09:00:00"),
        )
        self.assertEqual(source["record_digest"], source_digest)
        with self.assertRaises(ContractViolation):
            admission.check_externally_authorized_source(store, source_digest, None)
        other = AdmissionWorld(source_id="different-source")
        wrong = external_authority_for(
            admission.source_admission_authority_subject(
                other.store(), other.digest("source_approved"),
            ),
            namespace="mmbu.phase1.source-admission.v1",
            principal="external-source-board", role="source-admission-authority",
            signed_at=t("08:45:00"), verified_at=t("08:46:00"),
        )
        with self.assertRaises(ContractViolation):
            admission.check_externally_authorized_source(store, source_digest, wrong)

    def test_every_admission_record_is_closed(self):
        world = AdmissionWorld()
        validators = {
            "acquisition": admission.validate_acquisition_authorization,
            "receipt": admission.validate_acquisition_execution_receipt,
            "manifest": admission.validate_source_artifact_manifest,
            "source_quarantined": admission.validate_source,
            "rights": admission.validate_rights_receipt,
            "grouping": admission.validate_grouping_receipt,
            "population": admission.validate_eligible_population_manifest,
            "qa_plan": admission.validate_qa_sampling_plan,
            "qa_receipt": admission.validate_qa_receipt,
            "custody": admission.validate_custody_summary,
            "split_quarantine": admission.validate_split,
            "quarantine_authorization": admission.validate_purpose_authorization,
            "rights_attestation": admission.validate_reviewer_attestation,
        }
        for step, validator in validators.items():
            with self.subTest(step=step):
                validator(world.get(step))
                with self.assertRaises(ContractViolation):
                    validator(resealed(world.get(step), unexpected_field=True))
                with self.assertRaises(ContractViolation):
                    validator({**world.get(step), "record_digest": "0" * 64})


class AcquisitionTests(AdmissionTestCase):
    def test_non_head_or_superseded_acquisition_rejects(self):
        self.world_rejects("not the active registry head",
                           {"receipt": lambda r, w: r.update(authorization_registry_digest=w.digest("registry_g0"))},
                           "receipt", admission.check_acquisition_execution_receipt)
        world = AdmissionWorld()
        successor = copy.deepcopy(world.get("acquisition"))
        successor.update(authorization_id="acq-2", authorized_at=t("08:01:30"), supersedes_digest=world.digest("acquisition"),
                         reviewer_attestation_digest=None)
        attestation = world.attest("acq2", successor, "single_attestation", "acquisition_reviewer",
                                   ["quarantine_inspection"], "syn-acq-reviewer", t("08:01:30"))
        successor = canonical.seal({**successor, "reviewer_attestation_digest": attestation["record_digest"]})
        g1 = resealed(world.get("registry_g1"), acquisition_authorization_digests=sorted([world.digest("acquisition"),
                                                                                         successor["record_digest"]]),
                      acquisition_heads={f"{fx.SOURCE_ID}|{fx.VERSION}": successor["record_digest"]})
        receipt = resealed(world.get("receipt"), authorization_registry_digest=g1["record_digest"])
        store = world.store(successor, g1, receipt)
        self.assertRejects("not the active registry head", admission.check_acquisition_execution_receipt, store,
                           receipt["record_digest"])

    def test_unreceipted_or_failed_acquisition_creates_no_manifest(self):
        self.world_rejects("does not resolve", {"manifest": {"acquisition_execution_receipt_digest": d("no-receipt")}},
                           "manifest", admission.check_source_artifact_manifest)
        self.world_rejects("creates no manifest", {"receipt": {"exit_code": 2, "terminal_status": "failed"}},
                           "manifest", admission.check_source_artifact_manifest)

    def test_execution_must_match_the_authorization(self):
        cases = (
            ("unlisted host", {"receipt": {"observed_hosts": ["other-host.invalid"]}}),
            ("byte cap", {"acquisition": {"maximum_bytes": 100}}),
            ("basenames", {"acquisition": {"allowed_artifact_names": ["annotations.json", "images.tar"]}}),
            ("differs from the acquisition authorization", {"receipt": {"executed_command_digest": d("other-command")}}),
            ("differs from the acquisition authorization", {"receipt": {"operator_id": "other-operator"}}),
            ("expired before start", {"acquisition": {"expires_at": t("08:02:30")}}),
            ("is not allowed", {"acquisition": {"decision": "denied"}}),
        )
        for fragment, overrides in cases:
            with self.subTest(fragment=fragment):
                self.world_rejects(fragment, overrides, "receipt", admission.check_acquisition_execution_receipt)

    def test_authorization_local_rules(self):
        world = AdmissionWorld()
        record = world.get("acquisition")
        for change in ({"allowed_artifact_names": ["*.tar"]}, {"allowed_artifact_names": ["syn/images.tar"]},
                       {"intended_purpose": "train"}, {"inspection_prohibited": False}, {"maximum_bytes": 0},
                       {"staging_destination": "relative/path"}, {"expires_at": t("08:00:00")}):
            with self.subTest(change=sorted(change)):
                with self.assertRaises(ContractViolation):
                    admission.validate_acquisition_authorization(resealed(record, **change))

    def test_manifest_must_equal_the_receipt_exactly(self):
        def bump(record, world):
            record["artifacts"][0]["bytes"] += 1
            record["total_bytes"] += 1
        self.world_rejects("must equal the execution receipt exactly", {"manifest": bump}, "manifest",
                           admission.check_source_artifact_manifest)
        self.world_rejects("must equal the receipt end time", {"manifest": {"retrieved_at": t("08:04:30")}},
                           "manifest", admission.check_source_artifact_manifest)
        world = AdmissionWorld()
        with self.assertRaises(ContractViolation):
            admission.validate_source_artifact_manifest(resealed(world.get("manifest"), total_bytes=1))


class SourceTransitionTests(AdmissionTestCase):
    def test_pre_artifact_source_record_rejects(self):
        self.world_rejects("cannot predate its exact artifact manifest", {"source_candidate": {"created_at": t("08:03:30")}},
                           "source_candidate")

    def test_illegal_transitions_and_identity_mutation_reject(self):
        self.world_rejects("illegal source transition candidate -> candidate",
                           {"source_quarantined": {"status": "candidate", "allowed_purposes": []}}, "source_quarantined")
        self.world_rejects("illegal source transition None -> approved", {"source_approved": {"supersedes_digest": None}})
        self.world_rejects("cannot mutate across a source transition",
                           {"source_quarantined": {"proposed_purposes": ["engineering"]}}, "source_quarantined")
        world = AdmissionWorld()
        rejected = copy.deepcopy(world.get("source_approved"))
        rejected.update(status="rejected", origin_class="external_quarantine", allowed_purposes=[],
                        supersedes_digest=world.digest("source_approved"), created_at=t("08:50:00"),
                        reviewed_at=t("08:50:00"))
        rejected = canonical.seal(rejected)
        self.assertRejects("never silently returns", admission.check_source, world.store(rejected), rejected["record_digest"])
        back = canonical.seal({**copy.deepcopy(world.get("source_approved")), "status": "rejected", "allowed_purposes": [],
                               "supersedes_digest": world.digest("source_approved"), "created_at": t("08:50:00"),
                               "reviewed_at": t("08:50:00")})
        admission.check_source(world.store(back), back["record_digest"])
        again = canonical.seal({**copy.deepcopy(world.get("source_approved")), "supersedes_digest": back["record_digest"],
                                "created_at": t("08:55:00"), "reviewed_at": t("08:55:00")})
        self.assertRejects("illegal source transition rejected -> approved", admission.check_source,
                           world.store(back, again), again["record_digest"])

    def test_status_table_field_rules(self):
        world = AdmissionWorld()
        candidate = world.get("source_candidate")
        quarantined = world.get("source_quarantined")
        approved = world.get("source_approved")
        bad = (
            resealed(candidate, allowed_purposes=["engineering"]),
            resealed(candidate, rights_receipt_digest=world.digest("rights")),
            resealed(candidate, origin_class="external_reviewed"),
            resealed(quarantined, allowed_purposes=["engineering"]),
            resealed(quarantined, admission_decision_receipt_digest=world.digest("admission_receipt")),
            resealed(approved, allowed_purposes=[]),
            resealed(approved, allowed_purposes=["confirmation"]),
            resealed(approved, origin_class="external_quarantine"),
            resealed(approved, qa_receipt_digest=None),
            resealed(approved, proposed_purposes=["official_audit"]),
        )
        for index, record in enumerate(bad):
            with self.subTest(case=index):
                with self.assertRaises(ContractViolation):
                    admission.validate_source(record)

    def test_manual_or_unselected_candidate_admission_rejects(self):
        self.world_rejects("payload created outside the runner", {"admission_payload": {"created_at": t("08:33:30")}})
        self.world_rejects("must select this source", {"admission_payload": {
            "selected_subject_ids": [],
            "dispositions": [{"subject_id": fx.SOURCE_ID, "status": "not_selected", "reason_code": "held"}]}})
        def late_runner(record, world):
            record["ended_at"] = t("08:39:00")
            record["operator_attestation"]["attested_at"] = t("08:39:30")
            record["independent_review"]["reviewed_at"] = t("08:39:30")
        self.world_rejects("must predate the approval review", {"admission_receipt": late_runner})

    def test_approval_allowed_purposes_are_the_exact_intersection(self):
        def incompatible_train(record, world):
            record["purpose_findings"][1]["disposition"] = "incompatible"
        self.world_rejects("must equal the intersection", {"rights": incompatible_train})

    def test_approval_attestation_binds_reviewer_and_subject(self):
        self.world_rejects("differs from the reviewed record",
                           {"source_approved_attestation": lambda r, w: r["payload"].update(reviewer_id="someone-else")})
        self.world_rejects("must be one of", {"source_approved_attestation": lambda r, w: r["payload"].update(
            reviewer_role="rights_reviewer")})


class ReviewEvidenceTests(AdmissionTestCase):
    @staticmethod
    def qa_store_with_roles(purposes, roles):
        world = AdmissionWorld(proposed=purposes)
        receipt = copy.deepcopy(world.get("qa_receipt"))
        receipt.pop("record_digest")
        receipt["reviewer_attestation_digests"] = sorted(
            world.digest(f"qa_receipt_{role}") for role in roles
        )
        receipt = canonical.seal(receipt)
        return world, receipt, world.store(receipt, without=("qa_receipt",))

    def test_training_only_qa_requires_visual_but_not_clinical(self):
        _, receipt, store = self.qa_store_with_roles(["train"], ["visual"])
        admission.check_qa_receipt(store, receipt["record_digest"])

        _, missing_visual, missing_visual_store = self.qa_store_with_roles(["train"], ["clinical"])
        self.assertRejects(
            "required QA reviewer roles",
            admission.check_qa_receipt,
            missing_visual_store,
            missing_visual["record_digest"],
        )

    def test_decision_bearing_qa_requires_clinical_and_visual(self):
        for purposes in (["adaptive_dev"], ["confirmation"], ["confirmation", "train"]):
            with self.subTest(purposes=purposes):
                _, receipt, store = self.qa_store_with_roles(purposes, ["visual"])
                self.assertRejects(
                    "required QA reviewer roles",
                    admission.check_qa_receipt,
                    store,
                    receipt["record_digest"],
                )

    def test_review_of_different_bytes_rejects(self):
        self.world_rejects("reviewed different bytes",
                           {"rights_attestation": lambda r, w: r["payload"].update(subject_digest=d("other-bytes"))},
                           "rights", admission.check_rights_receipt)
        self.world_rejects("is not approved",
                           {"grouping_attestation": lambda r, w: r["payload"].update(disposition="rejected")},
                           "grouping", admission.check_grouping_receipt)
        world = AdmissionWorld()
        record = world.get("rights_attestation")
        with self.assertRaises(ContractViolation):
            admission.validate_reviewer_attestation(resealed(record, payload_digest="0" * 64))

    def test_unbound_proposed_purposes_reject(self):
        def drop_train(record, world):
            record["purpose_findings"] = record["purpose_findings"][:1]
        self.world_rejects("every proposed purpose", {"rights": drop_train}, "rights", admission.check_rights_receipt)
        self.world_rejects("complete proposed-purpose set", {"qa_plan": {"purposes": ["engineering"]}}, "qa_plan",
                           admission.check_qa_sampling_plan)

    def test_opaque_or_wrong_schema_digests_reject(self):
        self.world_rejects("resolves to mmbu.phase1.grouping_receipt",
                           {"source_approved": lambda r, w: r.update(rights_receipt_digest=w.digest("grouping"))})
        self.world_rejects("does not resolve", {"source_approved": {"qa_receipt_digest": d("opaque-qa")}})

    def test_grouping_rules(self):
        world = AdmissionWorld()
        record = world.get("grouping")
        def check(item):
            return resealed(record, duplicate_checks=[{**record["duplicate_checks"][0], **item}])
        bad = (
            resealed(record, independence_claim="study"),
            resealed(record, parent_count=9),
            check({"reviewed_collision_count": 0}),
            check({"disposition": "ignored"}),
            check({"compared_manifest_digests": []}),
        )
        for index, item in enumerate(bad):
            with self.subTest(case=index):
                with self.assertRaises(ContractViolation):
                    admission.validate_grouping_receipt(item)


class PopulationAndQaTests(AdmissionTestCase):
    def test_incomplete_or_opaque_populations_reject(self):
        self.world_rejects("must equal the eligible projection", {"population_payload": {"eligible_record_count": 3}},
                           "population", admission.check_eligible_population_manifest)
        self.world_rejects("canonical projection",
                           {"population_payload": lambda r, w: r["records"].pop(0)},
                           "population", admission.check_eligible_population_manifest)
        self.world_rejects("does not resolve", {"population": {"lineage_receipt_digest": d("opaque-lineage")}},
                           "population", admission.check_eligible_population_manifest)
        self.world_rejects("declares exactly", {"population_lineage": {"allowed_purposes": ["engineering", "quarantine_inspection"]}},
                           "population", admission.check_eligible_population_manifest)
        self.world_rejects("excluding missing-parent policy",
                           {"grouping": {"missing_parent_policy": "source_only_no_independence_claim"}},
                           "population", admission.check_eligible_population_manifest)
        world = AdmissionWorld()
        stale = resealed(world.get("population"), converter_digest=d("other-converter"))
        with self.assertRaises(ContractViolation):
            admission.validate_eligible_population_manifest(stale)

    def test_pre_manifest_inspection_rejects(self):
        overrides = {
            "inventory_lock": lambda r, w: (r.update(created_at=t("08:03:00")),
                                            r["planned_opening_event"].update(not_before=t("08:03:10"))),
            "inventory_opening": {"first_access_at": t("08:03:30")},
        }
        self.world_rejects("pre-manifest inspection", overrides, "population", admission.check_eligible_population_manifest)

    def test_backdated_or_mismatched_qa_plans_reject(self):
        cases = (
            ("plan must follow the population", {"qa_plan": {"created_at": t("08:19:00")}}),
            ("backdating", {"qa_plan": {"created_at": t("08:22:10")}}),
            ("must equal the plan", {"qa_lock": lambda r, w: r["thresholds"][0].update(value=0.2)}),
            ("singleton seed_material_digest", {"qa_lock": {"seed_ids": [d("other-seed")]}}),
            ("exact stratum projection", {"qa_lock": lambda r, w: r["groups"][0].update(minimum_parents=1)}),
            ("must include the exact plan and population", {"qa_lock": lambda r, w: r.update(
                input_artifact_digests=[w.digest("population")])}),
            ("must bind both the plan and population", {"qa_opening": lambda r, w: r.update(
                manifest_digests=[w.digest("population")])}),
        )
        for fragment, overrides in cases:
            with self.subTest(fragment=fragment):
                self.world_rejects(fragment, overrides, "qa_plan", admission.check_qa_sampling_plan)

    def test_qa_plan_local_rules(self):
        world = AdmissionWorld()
        plan = world.get("qa_plan")
        bad = (
            resealed(plan, required_n=4),
            resealed(plan, sample_independent_unit_count=2),
            resealed(plan, confidence=1),
            resealed(plan, strata=[{**plan["strata"][0], "planned_review_units": 4}, plan["strata"][1]]),
            resealed(plan, thresholds=plan["thresholds"][:3],
                     multiplicity_rule={**plan["multiplicity_rule"], "hypothesis_ids": [x["threshold_id"] for x in plan["thresholds"][:3]]}),
            resealed(plan, multiplicity_rule={**plan["multiplicity_rule"], "hypothesis_ids": ["t-overall"]}),
            resealed(plan, method="convenience"),
        )
        for index, record in enumerate(bad):
            with self.subTest(case=index):
                with self.assertRaises(ContractViolation):
                    admission.validate_qa_sampling_plan(record)

    def test_qa_receipt_recomputes_dispositions(self):
        def underpowered(record, world):
            record["strata_results"][0]["reviewed_units"] = 1
        cases = (
            ("must recompute as underpowered", {"qa_receipt": underpowered}),
            ("must recompute as fail", {"qa_receipt": lambda r, w: r["strata_results"][0].update(critical_upper_bound=0.3)}),
            ("approval requires complete review", {"qa_receipt": lambda r, w: r["error_counts"].update(reviewed_independent_units=2)}),
            ("approval requires complete review", {"qa_receipt": lambda r, w: r.update(critical_error_upper_bound=0.2)}),
            ("must resolve the plan's sole overall", {"qa_receipt": {"overall_threshold_id": "t-s1"}}),
            ("must equal the frozen overall value", {"qa_receipt": {"critical_error_ceiling": 0.5}}),
            ("sample digests must equal the frozen plan", {"qa_receipt": {"sample_ids_digest": d("other-sample")}}),
            ("must follow the QA opening", {"qa_receipt": {"reviewed_at": t("08:22:50")}}),
            ("every planned shortcut rule", {"qa_receipt": lambda r, w: r["shortcut_results"][0].update(probe_kind="label_only")}),
            ("required QA reviewer roles", {"qa_receipt_visual": lambda r, w: r["payload"].update(reviewer_role="clinical_qa_reviewer")}),
        )
        for fragment, overrides in cases:
            with self.subTest(fragment=fragment):
                self.world_rejects(fragment, overrides, "qa_receipt", admission.check_qa_receipt)

    def test_zero_observed_errors_cannot_repair_missing_completeness(self):
        def incomplete(record, world):
            record["annotation_completeness"][0].update(disposition="blocked_external")
            record["error_counts"].update(critical=0, major=0, minor=0)
        self.world_rejects("approval requires", {"qa_receipt": incomplete}, "qa_receipt", admission.check_qa_receipt)


class CustodyTests(AdmissionTestCase):
    def test_container_inventory_and_qa_chronology(self):
        cases = (
            ("began before its opening receipt", {"custody": {"inventory_started_at": t("08:09:50")}}),
            ("population must follow the inventory window", {"custody": {"inventory_ended_at": t("08:20:30")}}),
            ("QA must start after the plan", {"custody": {"qa_started_at": t("08:20:30")}}),
            ("outside the QA window", {"custody": {"qa_ended_at": t("08:28:00")}}),
            ("expires inside the window", {"quarantine_authorization": {"expires_at": t("08:25:00")}}),
            ("must equal the population's eligible-parent count", {"custody": {"eligible_independent_unit_count": 4}}),
            ("eligible-ID manifest", {"custody": {"eligible_id_manifest_digest": d("other-ids")}}),
        )
        for fragment, overrides in cases:
            with self.subTest(fragment=fragment):
                self.world_rejects(fragment, overrides, "custody", admission.check_custody_summary)

    def test_unsanitized_custody_content_is_unrepresentable(self):
        world = AdmissionWorld()
        for leak in ({"record_ids": ["rec-1"]}, {"labels": {"rec-1": "a"}}, {"reviewer_disagreements": []}):
            with self.subTest(leak=sorted(leak)):
                with self.assertRaises(ContractViolation):
                    admission.validate_custody_summary(resealed(world.get("custody"), **leak))

    def test_custody_attestations_are_distinct_and_bind_the_summary(self):
        self.world_rejects("reviewed different bytes",
                           {"custody_custodian": lambda r, w: r["payload"].update(subject_digest=d("other"))},
                           "custody", admission.check_custody_summary)
        self.world_rejects("is not approved", {"custody_custodian": lambda r, w: r["payload"].update(disposition="rejected")},
                           "custody", admission.check_custody_summary)


class SplitAndAuthorizationTests(AdmissionTestCase):
    def test_model_lineage_cannot_substitute_contributor_splits_or_roots(self):
        world = fx.release_world()
        lineage = copy.deepcopy(world.get("model_lineage"))
        lineage.pop("record_digest")
        lineage["contributing_sources"][0]["split_digests"] = [d("substituted-split")]
        lineage["completeness_attestation_digest"] = None
        attestation = world.attest("bad_lineage_attestation", lineage, "model_lineage_completeness",
                                   "release_reviewer", ["release"], "syn-release-reviewer", t("08:46:00"))
        bad_lineage = canonical.seal({**lineage, "completeness_attestation_digest": attestation["record_digest"]})
        store = world.store(bad_lineage, without=("model_lineage", "model_lineage_attestation"))
        self.assertRejects("split digests must equal", admission.check_model_lineage,
                           store, bad_lineage["record_digest"])

    def test_release_runs_the_full_decision_firewall(self):
        world = fx.release_world()
        bad_receipt = resealed(world.get("release_receipt"), network_events=[{"host": "undeclared.invalid"}])
        release = copy.deepcopy(world.get("release_authorization"))
        release.pop("record_digest")
        release.update(release_decision_receipt_digest=bad_receipt["record_digest"],
                       reviewer_attestation_digest=None)
        attestation = world.attest("bad_release_attestation", release, "single_attestation", "release_reviewer",
                                   ["release"], release["reviewer_id"], t("08:50:00"))
        bad_release = canonical.seal({**release, "reviewer_attestation_digest": attestation["record_digest"]})
        store = world.store(bad_receipt, bad_release,
                            without=("release_authorization", "release_authorization_attestation"))
        self.assertRejects("network activity recorded", admission.check_purpose_authorization,
                           store, bad_release["record_digest"])

    def test_quarantine_split_is_the_canonical_path_projection(self):
        self.world_rejects("artifact_path", {"split_quarantine": {"parent_namespace": "patient"}}, "split_quarantine",
                           admission.check_split)
        self.world_rejects("artifact-path projection", {"split_quarantine": {"record_ids_digest": d("other")}},
                           "split_quarantine", admission.check_split)
        self.world_rejects("approved post-inventory source",
                           {"split_engineering": lambda r, w: r.update(source_digest=w.digest("source_quarantined"))},
                           "split_engineering", admission.check_split)

    def test_purpose_and_split_roles_are_independent_and_tabled(self):
        self.world_rejects("is illegal for purpose", {"split_engineering": {"role": "train"}},
                           "engineering_authorization", admission.check_purpose_authorization)
        self.world_rejects("subset of the source's allowed purposes",
                           {"quarantine_authorization": {"purpose": "engineering"}}, "quarantine_authorization",
                           admission.check_purpose_authorization)

    def test_biomedical_parent_cannot_cross_train_and_confirmation(self):
        world = AdmissionWorld()
        train = resealed(world.get("split_engineering"), split_id="split-train", role="train")
        confirm = resealed(world.get("split_engineering"), split_id="split-confirm", role="confirmation")
        store = world.store(train, confirm)
        admission.check_split_parent_disjointness(store, [train["record_digest"]])
        self.assertRejects("crosses", admission.check_split_parent_disjointness, store,
                           [train["record_digest"], confirm["record_digest"]])

    def test_purpose_authorization_local_rules(self):
        world = AdmissionWorld()
        record = world.get("engineering_authorization")
        bad = (
            resealed(record, released_checkpoint_digest=d("checkpoint")),
            resealed(record, no_new_data_access=True),
            resealed(record, decision="maybe"),
            resealed(record, decision_basis_digests=[]),
            resealed(record, purpose="development"),
            resealed(record, expires_at=t("08:00:00")),
        )
        for index, item in enumerate(bad):
            with self.subTest(case=index):
                with self.assertRaises(ContractViolation):
                    admission.validate_purpose_authorization(item)
        self.world_rejects("differs from the reviewed record",
                           {"engineering_authorization": {"reviewer_id": "other-reviewer"}},
                           "engineering_authorization", admission.check_purpose_authorization)

    def test_authorization_registry_rejects_branches_and_unregistered_records(self):
        world = AdmissionWorld()
        branch = canonical.seal({**copy.deepcopy(world.get("source_quarantined")), "created_at": t("08:06:10")})
        registry = resealed(world.get("registry_g2"),
                            source_record_digests=sorted(world.get("registry_g2")["source_record_digests"] + [branch["record_digest"]]))
        store = world.store(branch, registry)
        self.assertRejects("branches", registries.check_authorization_registry_chain, store, registry["record_digest"])
        missing_source = resealed(world.get("registry_g2"), source_record_digests=[world.digest("source_candidate")],
                                  source_heads={fx.SOURCE_ID: world.digest("source_candidate")})
        self.assertRejects("not registered", registries.check_authorization_registry_chain,
                           world.store(missing_source), missing_source["record_digest"])
        stale_head = resealed(world.get("registry_g2"), source_heads={fx.SOURCE_ID: world.digest("source_candidate")})
        self.assertRejects("not the chain leaf", registries.check_authorization_registry_chain,
                           world.store(stale_head), stale_head["record_digest"])

    def test_active_leaf_rejects_superseded_or_expired_records(self):
        world = AdmissionWorld()
        store = world.store()
        registry = world.get("registry_g3")
        self.assertRejects("not the active registry head", admission.require_active_leaf, store, registry,
                           world.digest("source_quarantined"), "source", admission.ts(t("09:00:00"), "at"), "x")
        expiring = AdmissionWorld({"engineering_authorization": {"expires_at": t("08:45:00")}})
        self.assertRejects("authorization expired", admission.require_active_leaf, expiring.store(),
                           expiring.get("registry_g3"), expiring.digest("engineering_authorization"), "authorization",
                           admission.ts(t("09:00:00"), "at"), "x")


if __name__ == "__main__":
    unittest.main()
