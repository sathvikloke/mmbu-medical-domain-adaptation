"""A complete synthetic-canary real-source admission chain with per-step overrides.

Every identity, byte count, hash, reviewer, and timestamp is synthetic.  Steps are
built in dependency order so an override at one step re-derives every
downstream digest, letting negatives prove semantic rejection, not stale hashes.
"""

import copy

from mmbu_phase1 import canonical
from mmbu_phase1.store import RecordStore

P = "mmbu.phase1."
SOURCE_ID = "syn-src"
VERSION = "v1"
FAMILY = "syn-family"
PROPOSED = ["engineering", "train"]


def d(label):
    return canonical.raw_digest(("synthetic-admission:" + label).encode())


def t(hhmmss):
    return f"2026-10-16T{hhmmss}Z"


class AdmissionWorld:
    def __init__(self, overrides=None, proposed=None, *, source_id=SOURCE_ID, version=VERSION, family=FAMILY,
                 artifacts=None, extra_admission_input_digests=()):
        self.overrides = overrides or {}
        self.proposed = sorted(proposed or PROPOSED)
        self.source_id = source_id
        self.version = version
        self.family = family
        self.artifacts = artifacts
        self.extra_admission_input_digests = list(extra_admission_input_digests)
        self.records = {}
        self.extra = []
        self.build()

    # -- helpers -------------------------------------------------------
    def apply(self, step, record):
        record = copy.deepcopy(record)
        change = self.overrides.get(step)
        if callable(change):
            change(record, self)
        elif change:
            record.update(copy.deepcopy(change))
        return record

    def seal(self, step, record):
        sealed = canonical.seal(self.apply(step, record))
        self.records[step] = sealed
        return sealed

    def attest(self, step, subject, domain, role, purposes, reviewer, at, disposition="approved"):
        payload = {
            "statement_version": "mmbu-review-attestation-v1",
            "reviewer_id": reviewer,
            "reviewer_role": role,
            "subject_digest": canonical.subject_digest(subject, domain),
            "purposes": sorted(purposes),
            "disposition": disposition,
            "limitations_digest": d("limitations-" + step),
            "reviewed_at": at,
            "declaration_text_digest": d("declaration-" + step),
        }
        record = {
            "schema_id": P + "reviewer_attestation",
            "schema_version": 1,
            "attestation_id": "att-" + step,
            "payload": payload,
            "payload_digest": None,
            "verification": {"method": "manual_identity_check", "verifier_id": "syn-verifier", "verified_at": at,
                             "verification_artifact_digest": d("verification-" + step)},
        }
        record = self.apply(step, record)
        record["payload_digest"] = canonical.value_digest(record["payload"])
        sealed = canonical.seal(record)
        self.records[step] = sealed
        return sealed

    def single(self, step, record, role, purposes, reviewer, at, field="reviewer_attestation_digest", domain="single_attestation"):
        record = {**record, field: None}
        record = self.apply(step, record)
        attestation = self.attest(step + "_attestation", record, domain, role, purposes, reviewer, at)
        record[field] = attestation["record_digest"]
        sealed = canonical.seal(record)
        self.records[step] = sealed
        return sealed

    def multi(self, step, record, specs, at):
        record = {**record, "reviewer_attestation_digests": []}
        record = self.apply(step, record)
        digests = []
        for name, role, purposes, reviewer, disposition in specs:
            att = self.attest(f"{step}_{name}", record, "multi_attestation", role, purposes, reviewer, at, disposition)
            digests.append(att["record_digest"])
        record["reviewer_attestation_digests"] = sorted(digests)
        sealed = canonical.seal(record)
        self.records[step] = sealed
        return sealed

    def get(self, step):
        return self.records[step]

    def digest(self, step):
        return self.records[step]["record_digest"]

    def store(self, *extra, without=()):
        excluded = set(without)
        records = [r for k, r in self.records.items() if k not in excluded]
        store = RecordStore(records + list(self.extra) + list(extra))
        store.add_artifact(canonical.dumps(self.parent_ids))
        return store

    # -- chain -----------------------------------------------------------
    def build(self):
        artifacts = self.artifacts or [
            {"logical_path": "syn/annotations.json", "bytes": 120, "sha256": d("annotations-bytes")},
            {"logical_path": "syn/images.tar", "bytes": 4096, "sha256": d("images-bytes")},
            {"logical_path": "syn/terms.txt", "bytes": 64, "sha256": d("terms-bytes")},
        ]
        self.seal("registry_g0", self.registry(0, None, [], [], [], {}, {}, {}, t("07:59:00")))
        acquisition = {
            "schema_id": P + "acquisition_authorization", "schema_version": 1, "authorization_id": "acq-1",
            "source_id": self.source_id, "source_version": self.version, "source_family": self.family,
            "canonical_locator_ids": ["syn-locator-1"], "identity_evidence_digests": [d("identity")],
            "terms_digest": d("terms"),
            "allowed_artifact_names": sorted(row["logical_path"].rsplit("/", 1)[-1] for row in artifacts),
            "intended_purpose": "quarantine_inspection", "staging_destination": "/srv/syn-staging/syn-src",
            "retrieval_method_digest": d("method"), "retrieval_command_digest": d("command"),
            "operator_id": "syn-operator", "network_host_allowlist": ["syn-host.invalid"],
            "maximum_bytes": max(10000, sum(row["bytes"] for row in artifacts)),
            "decision": "allowed", "inspection_prohibited": True, "authorized_at": t("08:01:00"),
            "expires_at": "2027-01-01T00:00:00Z", "supersedes_digest": None,
        }
        self.single("acquisition", acquisition, "acquisition_reviewer", ["quarantine_inspection"], "syn-acq-reviewer", t("08:00:30"))
        a = self.digest("acquisition")
        self.seal("registry_g1", self.registry(1, self.digest("registry_g0"), [a], [], [],
                                               {f"{self.source_id}|{self.version}": a}, {}, {}, t("08:02:00")))
        self.seal("receipt", {
            "schema_id": P + "acquisition_execution_receipt", "schema_version": 1, "receipt_id": "acq-receipt-1",
            "acquisition_authorization_digest": a, "authorization_registry_digest": self.digest("registry_g1"),
            "source_id": self.source_id, "source_version": self.version, "source_family": self.family,
            "executed_method_digest": d("method"), "executed_command_digest": d("command"), "operator_id": "syn-operator",
            "observed_hosts": ["syn-host.invalid"],
            "observed_artifacts": [{k: x[k] for k in ("logical_path", "bytes", "sha256")} for x in artifacts],
            "staging_destination": "/srv/syn-staging/syn-src", "started_at": t("08:03:00"), "ended_at": t("08:04:00"),
            "retrieval_log_digest": d("retrieval-log"), "exit_code": 0, "terminal_status": "succeeded",
        })
        self.seal("manifest", {
            "schema_id": P + "source_artifact_manifest", "schema_version": 1, "manifest_id": "manifest-1",
            "source_id": self.source_id, "source_version": self.version, "source_family": self.family,
            "canonical_locator_ids": ["syn-locator-1"], "acquisition_authorization_digest": a,
            "acquisition_execution_receipt_digest": self.digest("receipt"),
            "artifacts": [{**x, "upstream_checksum": None, "media_type": "application/octet-stream",
                           "role": {"syn/annotations.json": "annotation", "syn/images.tar": "archive",
                                    "syn/terms.txt": "terms"}.get(x["logical_path"], "archive")} for x in artifacts],
            "total_bytes": sum(x["bytes"] for x in artifacts), "retriever_id": "syn-operator",
            "retrieved_at": t("08:04:00"), "retrieval_log_digest": d("retrieval-log"),
        })
        m = self.digest("manifest")
        self.seal("source_candidate", self.source("candidate", "external_quarantine", None, [], t("08:05:00")))
        self.seal("source_quarantined", self.source("quarantined", "external_quarantine", self.digest("source_candidate"),
                                                    ["quarantine_inspection"], t("08:06:00")))
        s1 = self.digest("source_quarantined")
        paths = [x["logical_path"] for x in artifacts]
        self.seal("split_quarantine", {
            "schema_id": P + "split", "schema_version": 1, "split_id": "split-quarantine", "source_digest": s1,
            "source_artifact_manifest_digest": m, "role": "quarantine",
            "record_manifest_digest": canonical.value_digest(paths), "parent_namespace": "artifact_path",
            "parent_ids_digest": canonical.value_digest(paths), "record_ids_digest": canonical.value_digest(paths),
            "construction_rule_digest": canonical.value_digest({"rule": "mmbu.phase1.canonical_path_projection", "version": 1}),
            "created_at": t("08:06:30"),
        })
        self.single("quarantine_authorization", self.authorization(
            "auth-quarantine", "quarantine_inspection", s1, [self.digest("split_quarantine")], [], t("08:07:00")),
            "purpose_authorization_reviewer", ["quarantine_inspection"], "syn-purpose-reviewer", t("08:07:00"))
        qa_auth = self.digest("quarantine_authorization")
        self.seal("registry_g2", self.registry(2, self.digest("registry_g1"), [a],
                                               sorted([self.digest("source_candidate"), s1]), [qa_auth],
                                               {f"{self.source_id}|{self.version}": a}, {self.source_id: s1},
                                               {f"{self.source_id}|quarantine_inspection": qa_auth}, t("08:08:00")))
        self.seal("inventory_lock", self.lock("lock-inventory", "custody_inventory", None, sorted([m, s1]), m, [],
                                              t("08:09:00"), t("08:09:30")))
        il = self.digest("inventory_lock")
        self.seal("inventory_opening", self.opening("opening-inventory", self.get("inventory_lock"), [m], t("08:10:00")))
        io = self.digest("inventory_opening")
        self.seal("opening_g0", self.opening_registry(0, None, [], t("08:08:30")))
        self.seal("opening_g1", self.opening_registry(1, self.digest("opening_g0"),
                                                      [self.head(il, self.get("inventory_opening"))], t("08:09:45")))
        self.single("grouping", {
            "schema_id": P + "grouping_receipt", "schema_version": 1, "receipt_id": "grouping-1",
            "source_artifact_manifest_digest": m, "source_family": self.family, "alias_family_ids": [],
            "strongest_parent_namespace": "patient", "independence_claim": "patient", "parent_map_digest": d("parent-map"),
            "missing_parent_policy": "reject_record", "parent_count": 3, "record_count": 5,
            "duplicate_checks": [{"compared_manifest_digests": [m], "roles": self.proposed, "method_digest": d("dup-method"),
                                  "exact_duplicate_count": 0, "perceptual_candidate_count": 1,
                                  "reviewed_collision_count": 1, "collision_manifest_digest": d("collisions"),
                                  "disposition": "resolved"}],
            "split_construction_rule_digest": d("split-rule"), "reviewed_at": t("08:15:00"),
        }, "grouping_reviewer", self.proposed, "syn-grouping-reviewer", t("08:15:00"))
        self.single("rights", {
            "schema_id": P + "rights_receipt", "schema_version": 1, "receipt_id": "rights-1",
            "source_proposal_digest": s1, "source_artifact_manifest_digest": m, "terms_artifact_digests": [d("terms-bytes")],
            "provenance_locator_ids": ["syn-locator-1"],
            "purpose_findings": [{"purpose": p, "disposition": "compatible", "basis_digests": [d("basis-" + p)],
                                  "limitations_digest": d("rights-limits-" + p)} for p in self.proposed],
            "obligations_digest": d("obligations"), "attribution_text_digest": d("attribution"),
            "reviewed_at": t("08:16:00"), "expires_at": "2027-06-01T00:00:00Z",
        }, "rights_reviewer", self.proposed, "syn-rights-reviewer", t("08:16:00"))
        rows = [
            {"record_id": "rec-1", "parent_id": "pat-1", "artifact_digests": [d("rec-1")], "disposition": "eligible", "exclusion_reason_code": None},
            {"record_id": "rec-2", "parent_id": "pat-1", "artifact_digests": [d("rec-2")], "disposition": "eligible", "exclusion_reason_code": None},
            {"record_id": "rec-3", "parent_id": "pat-2", "artifact_digests": [d("rec-3")], "disposition": "eligible", "exclusion_reason_code": None},
            {"record_id": "rec-4", "parent_id": "pat-3", "artifact_digests": [d("rec-4")], "disposition": "eligible", "exclusion_reason_code": None},
            {"record_id": "rec-5", "parent_id": None, "artifact_digests": [d("rec-5")], "disposition": "excluded", "exclusion_reason_code": "missing_parent"},
        ]
        population = {
            "schema_id": P + "eligible_population_manifest", "schema_version": 1, "population_id": "population-1",
            "source_digest": s1, "source_artifact_manifest_digest": m, "inventory_lock_digest": il,
            "inventory_opening_receipt_digest": io, "converter_digest": d("converter"),
            "exclusion_rule_digest": d("exclusion-rule"), "grouping_receipt_digest": self.digest("grouping"),
            "records": rows, "eligible_record_ids_digest": canonical.value_digest(["rec-1", "rec-2", "rec-3", "rec-4"]),
            "eligible_parent_ids_digest": canonical.value_digest(["pat-1", "pat-2", "pat-3"]),
            "eligible_record_count": 4, "eligible_parent_count": 3, "population_payload_digest": None,
            "lineage_receipt_digest": None, "created_at": t("08:20:00"),
        }
        population = self.apply("population_payload", population)
        omitted = {"population_payload_digest", "lineage_receipt_digest", "created_at", "record_digest"}
        population["population_payload_digest"] = canonical.value_digest(
            {k: v for k, v in population.items() if k not in omitted})
        self.seal("population_lineage", self.lineage(population["population_payload_digest"], "external_quarantine",
                                                     sorted(self.proposed + ["quarantine_inspection"]), t("08:20:00")))
        population["lineage_receipt_digest"] = self.digest("population_lineage")
        self.seal("population", population)
        ep = self.digest("population")
        thresholds = [
            {"threshold_id": "t-overall", "metric_id": "critical_error_rate", "estimand_id": "overall_critical_error",
             "value": 0.1, "unit": "fraction", "direction": "at_most", "underpowered_disposition": "block"},
            {"threshold_id": "t-s1", "metric_id": "critical_error_rate", "estimand_id": "s1", "value": 0.2,
             "unit": "fraction", "direction": "at_most", "underpowered_disposition": "block"},
            {"threshold_id": "t-s2", "metric_id": "critical_error_rate", "estimand_id": "s2", "value": 0.2,
             "unit": "fraction", "direction": "at_most", "underpowered_disposition": "block"},
            {"threshold_id": "t-shortcut-text", "metric_id": "shortcut_probe:text_only", "estimand_id": "shortcut",
             "value": 0.6, "unit": "accuracy", "direction": "at_most", "underpowered_disposition": "block"},
        ]
        multiplicity = {"family_id": "qa-family", "alpha": 0.05, "method": "bonferroni",
                        "hypothesis_ids": [x["threshold_id"] for x in thresholds], "rule_digest": d("qa-multiplicity")}
        strata = [{"stratum_id": "s1", "definition_digest": d("s1"), "eligible_units": 3, "planned_review_units": 2},
                  {"stratum_id": "s2", "definition_digest": d("s2"), "eligible_units": 2, "planned_review_units": 1}]
        self.seal("qa_plan", {
            "schema_id": P + "qa_sampling_plan", "schema_version": 1, "plan_id": "qa-plan-1",
            "eligible_population_manifest_digest": ep, "purposes": self.proposed, "independent_unit_namespace": "patient",
            "method": "stratified", "sampling_function_digest": d("sampler"), "seed_material_digest": d("seed-material"),
            "required_n": 3, "confidence": 0.95, "strata": strata,
            "sample_independent_unit_ids_digest": d("sample-units"), "sample_record_ids_digest": d("sample-records"),
            "sample_independent_unit_count": 3, "thresholds": thresholds, "multiplicity_rule": multiplicity,
            "approval_function_digest": d("approval-fn"), "created_at": t("08:21:00"),
        })
        qp = self.digest("qa_plan")
        groups = [{"group_id": s["stratum_id"], "definition_digest": s["definition_digest"], "parent_unit": "patient",
                   "minimum_parents": s["planned_review_units"], "role": "multiplicity_family",
                   "underpowered_disposition": "block"} for s in strata]
        self.seal("qa_lock", self.lock("lock-qa", "custody_qa", qp, sorted([qp, ep]), ep, groups, t("08:22:00"),
                                       t("08:22:30"), thresholds=thresholds, multiplicity=multiplicity,
                                       seeds=[d("seed-material")], decision_fn=d("approval-fn")))
        ql = self.digest("qa_lock")
        self.seal("qa_opening", self.opening("opening-qa", self.get("qa_lock"), sorted([qp, ep]), t("08:23:00")))
        self.seal("opening_g2", self.opening_registry(2, self.digest("opening_g1"),
                                                      [self.head(il, self.get("inventory_opening")),
                                                       self.head(ql, self.get("qa_opening"))], t("08:22:45")))
        self.multi("qa_receipt", {
            "schema_id": P + "qa_receipt", "schema_version": 1, "receipt_id": "qa-receipt-1",
            "source_artifact_manifest_digest": m, "eligible_population_manifest_digest": ep, "qa_sampling_plan_digest": qp,
            "purposes": self.proposed, "converter_digest": d("converter"), "target_schema_digest": d("target-schema"),
            "eligible_record_manifest_digest": d("eligible-record-manifest"), "source_annex_digest": d("annex"),
            "sample_independent_unit_ids_digest": d("sample-units"), "sample_ids_digest": d("sample-records"),
            "error_counts": {"critical": 0, "major": 1, "minor": 2, "reviewed_independent_units": 3},
            "overall_threshold_id": "t-overall", "critical_error_upper_bound": 0.05, "critical_error_ceiling": 0.1,
            "strata_results": [
                {"stratum_id": "s1", "threshold_id": "t-s1", "eligible_units": 3, "reviewed_units": 2, "critical": 0,
                 "major": 1, "minor": 1, "critical_upper_bound": 0.1, "critical_ceiling": 0.2, "disposition": "pass"},
                {"stratum_id": "s2", "threshold_id": "t-s2", "eligible_units": 2, "reviewed_units": 1, "critical": 0,
                 "major": 0, "minor": 1, "critical_upper_bound": 0.15, "critical_ceiling": 0.2, "disposition": "pass"},
            ],
            "adjudication": {"disagreement_count": 0, "disagreement_manifest_digest": d("disagreements"),
                             "adjudicated_count": 0, "adjudicator_attestation_digest": None, "unresolved_count": 0},
            "annotation_completeness": [{"target_id": "label-a", "eligible_units": 3, "annotated_units": 3,
                                         "not_annotated_units": 0, "negative_units": 1,
                                         "negative_rule_digest": d("negative-rule"), "disposition": "pass"}],
            "shortcut_results": [{"probe_kind": "text_only", "threshold_id": "t-shortcut-text",
                                  "input_manifest_digest": d("probe-input"), "method_digest": d("probe-method"),
                                  "metric_id": "shortcut_probe:text_only", "value": 0.5, "threshold": 0.6,
                                  "disposition": "pass"}],
            "approval_function_digest": d("approval-fn"), "disposition": "approved", "limitations_digest": d("qa-limits"),
            "reviewed_at": t("08:29:00"),
        }, [("clinical", "clinical_qa_reviewer", self.proposed, "syn-clinical-reviewer", "approved"),
            ("visual", "visual_qa_reviewer", self.proposed, "syn-visual-reviewer", "approved")], t("08:29:00"))
        self.multi("custody", {
            "schema_id": P + "custody_summary", "schema_version": 1, "custody_id": "custody-1", "source_digest": s1,
            "quarantine_authorization_digest": qa_auth, "inventory_authorization_registry_digest": self.digest("registry_g2"),
            "inventory_lock_digest": il, "inventory_opening_receipt_digest": io,
            "inventory_opening_receipt_registry_digest": self.digest("opening_g1"),
            "inventory_started_at": t("08:10:00"), "inventory_ended_at": t("08:20:00"),
            "eligible_population_manifest_digest": ep, "qa_sampling_plan_digest": qp,
            "qa_authorization_registry_digest": self.digest("registry_g2"), "qa_lock_digest": ql,
            "qa_opening_receipt_digest": self.digest("qa_opening"),
            "qa_opening_receipt_registry_digest": self.digest("opening_g2"),
            "qa_started_at": t("08:24:00"), "qa_ended_at": t("08:30:00"),
            "eligible_id_manifest_digest": canonical.value_digest(["rec-1", "rec-2", "rec-3", "rec-4"]),
            "exclusion_rule_digest": d("exclusion-rule"), "converter_digest": d("converter"),
            "evaluator_fixture_digest": d("evaluator-fixture"), "eligible_independent_unit_count": 3,
            "rights_receipt_digest": self.digest("rights"), "grouping_receipt_digest": self.digest("grouping"),
            "qa_receipt_digest": self.digest("qa_receipt"), "disposition": "passed", "limitations_digest": d("custody-limits"),
            "created_at": t("08:31:00"),
        }, [("custodian", "custody_reviewer", self.proposed, "syn-custody-reviewer", "approved")], t("08:31:00"))
        inputs = sorted([s1, m, self.digest("rights"), self.digest("grouping"), self.digest("qa_receipt"),
                         self.digest("custody"), *self.extra_admission_input_digests])
        self.admission_decision(inputs)
        approved = self.source("approved", "external_reviewed", s1, self.proposed, t("08:38:00"), reviewed=True)
        self.single("source_approved", approved, "candidate_admission_reviewer", self.proposed, "syn-admission-reviewer",
                    t("08:38:00"), field="approval_attestation_digest", domain="source_approval")
        s2 = self.digest("source_approved")
        self.parent_ids = ["pat-1", "pat-2", "pat-3"]
        self.seal("split_engineering", {
            "schema_id": P + "split", "schema_version": 1, "split_id": "split-engineering", "source_digest": s2,
            "source_artifact_manifest_digest": m, "role": "engineering", "record_manifest_digest": d("eng-records"),
            "parent_namespace": "patient", "parent_ids_digest": canonical.raw_digest(canonical.dumps(self.parent_ids)),
            "record_ids_digest": d("eng-record-ids"), "construction_rule_digest": d("split-rule"),
            "created_at": t("08:39:00"),
        })
        self.seal("root_lineage", {
            "schema_id": P + "lineage_receipt", "schema_version": 1, "lineage_id": "lineage-root",
            "artifact_digest": d("engineering-root"), "origin_class": "external_reviewed", "allowed_purposes": self.proposed,
            "parents": [], "source_version": d("version"), "rights_receipt_digest": self.digest("rights"),
            "grouping_receipt_digest": self.digest("grouping"), "qa_receipt_digest": self.digest("qa_receipt"),
            "created_at": t("08:39:00"),
        })
        self.single("engineering_authorization", self.authorization(
            "auth-engineering", "engineering", s2, [self.digest("split_engineering")], [d("engineering-root")], t("08:40:00")),
            "purpose_authorization_reviewer", ["engineering"], "syn-purpose-reviewer", t("08:40:00"))
        self.seal("registry_g3", self.registry(
            3, self.digest("registry_g2"), [a], sorted([self.digest("source_candidate"), s1, s2]),
            sorted([qa_auth, self.digest("engineering_authorization")]), {f"{self.source_id}|{self.version}": a}, {self.source_id: s2},
            {f"{self.source_id}|quarantine_inspection": qa_auth, f"{self.source_id}|engineering": self.digest("engineering_authorization")},
            t("08:41:00")))

    def admission_decision(self, inputs):
        plan = self.seal("admission_plan", {
            "schema_id": P + "decision_plan", "schema_version": 1, "plan_id": "admission-plan-1",
            "decision_kind": "candidate_admission", "purpose": "quarantine_inspection", "scope": "candidate-admission",
            "subject_ids": [self.source_id], "allowed_input_digests": inputs,
            "forbidden_origin_classes": ["mmbu_derivative", "mmbu_official", "unknown"], "forbidden_root_digests": [],
            "decision_function_digest": d("admission-fn"), "command_digest": d("admission-command"),
            "source_state_digest": d("source-state"), "sandbox_policy_digest": d("sandbox"),
            "planned_opening_event": {"opening_kind": "protected_access", "trigger": "admission-runner",
                                      "not_before": t("08:33:00"), "operator_role": "admission_operator",
                                      "protected_artifact_digests": inputs, "command_template_digest": d("admission-template")},
            "operator_id": "syn-admission-operator", "created_at": t("08:32:00"),
        })
        payload = self.seal("admission_payload", {
            "schema_id": P + "decision_payload", "schema_version": 1, "decision_id": "admission-decision-1",
            "plan_digest": plan["record_digest"], "decision_kind": "candidate_admission", "purpose": "quarantine_inspection",
            "subject_ids": [self.source_id], "selected_subject_ids": [self.source_id],
            "dispositions": [{"subject_id": self.source_id, "status": "selected", "reason_code": "admission_rules_met"}],
            "claim_digests": [self.digest("custody")], "rationale_digest": d("admission-rationale"),
            "created_at": t("08:35:00"),
        })
        out = self.seal("admission_lineage", self.lineage(payload["record_digest"], "external_quarantine",
                                                          ["quarantine_inspection"], t("08:35:00"),
                                                          parents=[(i, "decision") for i in inputs]))
        self.seal("admission_receipt", {
            "schema_id": P + "decision_execution_receipt", "schema_version": 1, "receipt_id": "admission-receipt-1",
            "plan_digest": plan["record_digest"], "decision_payload_digest": payload["record_digest"],
            "rationale_digest": d("admission-rationale"), "output_lineage_receipt_digest": out["record_digest"],
            "source_state_digest": d("source-state"), "command_digest": d("admission-command"),
            "sandbox_policy_digest": d("sandbox"), "mounted_input_digests": inputs, "observed_content_read_digests": inputs,
            "emitted_output_digests": sorted([payload["record_digest"], d("admission-rationale")]),
            "attempted_denied_reads": [], "network_events": [],
            "operator_attestation": {"operator_id": "syn-admission-operator", "no_undeclared_influence": True,
                                     "no_protected_memory_used": True, "attested_at": t("08:37:00"),
                                     "attestation_digest": d("admission-operator")},
            "independent_review": {"reviewer_id": "syn-admission-reviewer-2", "reviewed_plan_digest": plan["record_digest"],
                                   "reviewed_payload_digest": payload["record_digest"],
                                   "reviewed_rationale_digest": d("admission-rationale"), "disposition": "approved",
                                   "reviewed_at": t("08:37:00"), "attestation_digest": d("admission-review")},
            "started_at": t("08:34:00"), "ended_at": t("08:36:00"), "exit_code": 0, "terminal_status": "succeeded",
        })

    def source(self, status, origin, supersedes, allowed, created, reviewed=False):
        return {
            "schema_id": P + "source", "schema_version": 1, "source_id": self.source_id, "source_version": self.version,
            "source_family": self.family, "origin_class": origin, "status": status,
            "artifact_manifest_digest": self.digest("manifest"), "proposed_purposes": list(self.proposed),
            "rights_receipt_digest": self.digest("rights") if reviewed else None,
            "grouping_receipt_digest": self.digest("grouping") if reviewed else None,
            "qa_receipt_digest": self.digest("qa_receipt") if reviewed else None,
            "admission_decision_receipt_digest": self.digest("admission_receipt") if reviewed else None,
            "approval_attestation_digest": None, "allowed_purposes": list(allowed),
            "reviewer_id": "syn-admission-reviewer" if reviewed else None, "created_at": created,
            "reviewed_at": created if reviewed else None, "supersedes_digest": supersedes,
        }

    def authorization(self, auth_id, purpose, source, splits, roots, decided):
        return {
            "schema_id": P + "purpose_authorization", "schema_version": 1, "authorization_id": auth_id,
            "purpose": purpose, "source_digest": source, "split_digests": sorted(splits), "lineage_root_digests": sorted(roots),
            "decision": "allowed", "decision_basis_digests": [d("basis-" + auth_id)], "reviewer_id": "syn-purpose-reviewer",
            "released_checkpoint_digest": None, "validated_model_lineage_digest": None,
            "release_rights_receipt_digest": None, "release_decision_receipt_digest": None, "no_new_data_access": None,
            "decided_at": decided, "expires_at": None, "supersedes_digest": None,
        }

    def lineage(self, artifact, origin, purposes, created, parents=()):
        return {
            "schema_id": P + "lineage_receipt", "schema_version": 1, "lineage_id": "lineage-" + artifact[:12],
            "artifact_digest": artifact, "origin_class": origin, "allowed_purposes": sorted(purposes),
            "parents": sorted(({"parent_digest": p, "edge_role": r} for p, r in parents),
                              key=lambda e: (e["parent_digest"], e["edge_role"])),
            "source_version": None, "rights_receipt_digest": None, "grouping_receipt_digest": None,
            "qa_receipt_digest": None, "created_at": created,
        }

    def registry(self, generation, prior, acquisitions, sources, authorizations, acq_heads, source_heads, auth_heads, as_of):
        return {
            "schema_id": P + "authorization_registry", "schema_version": 1, "registry_id": f"auth-registry-g{generation}",
            "generation": generation, "supersedes_registry_digest": prior, "acquisition_authorization_digests": acquisitions,
            "source_record_digests": sources, "purpose_authorization_digests": authorizations,
            "acquisition_heads": acq_heads, "source_heads": source_heads, "authorization_heads": auth_heads,
            "revoked_digests": [], "as_of": as_of,
        }

    def lock(self, lock_id, phase, qa_plan, inputs, population, groups, created, not_before, thresholds=None,
             multiplicity=None, seeds=None, decision_fn=None):
        return {
            "schema_id": P + "prospective_lock", "schema_version": 1, "lock_id": lock_id,
            "scope": {"scope_id": lock_id, "purpose": "quarantine_inspection", "phase": phase,
                      "primary_estimand_id": "overall_critical_error", "comparison_ids": ["custody"],
                      "analysis_population_digest": population},
            "source_state_digest": d("source-state"), "input_artifact_digests": inputs, "qa_sampling_plan_digest": qa_plan,
            "excluded_result_digests": [], "candidate_ids": [self.source_id], "seed_ids": seeds or [],
            "thresholds": thresholds or [], "groups": groups, "evaluator_digest": d("custody-evaluator"),
            "multiplicity_rule": multiplicity or {"family_id": "inventory", "alpha": 0.05, "method": "none",
                                                  "hypothesis_ids": ["inventory-complete"], "rule_digest": d("inv-rule")},
            "compute_plan_digest": d("compute"), "decision_function_digest": decision_fn or d("inventory-fn"),
            "claim_boundary": {"primary_claim_id": "custody-complete", "allowed_claim_ids": ["custody-complete"],
                               "prohibited_claim_ids": ["model-use"], "failure_claim_id": "custody-failed"},
            "planned_opening_event": {"opening_kind": "protected_access", "trigger": lock_id, "not_before": not_before,
                                      "operator_role": "custody_reviewer", "protected_artifact_digests": inputs,
                                      "command_template_digest": d("custody-template")},
            "retry_policies": [], "created_at": created, "supersedes_digest": None, "amendment_reason": None,
        }

    def opening(self, opening_id, lock, manifests, first_access):
        return {
            "schema_id": P + "opening_receipt", "schema_version": 1, "opening_id": opening_id,
            "lock_digest": lock["record_digest"], "source_state_digest": lock["source_state_digest"],
            "manifest_digests": manifests, "command_digest": d("custody-command"), "environment_digest": d("custody-env"),
            "operator_id": "syn-custody-operator", "opening_kind": "protected_access", "first_access_at": first_access,
            "receipt_generation": 0, "supersedes_receipt_digest": None, "expected_run_ids": [], "observed_failure_ids": [],
            "retries": [],
        }

    def opening_registry(self, generation, prior, heads, created):
        return {
            "schema_id": P + "opening_receipt_registry", "schema_version": 1, "registry_id": f"opening-registry-g{generation}",
            "generation": generation, "supersedes_registry_digest": prior,
            "heads": sorted(heads, key=lambda h: h["lock_digest"]), "created_at": created,
        }

    def head(self, lock_digest, receipt):
        return {"lock_digest": lock_digest, "opening_id": receipt["opening_id"],
                "head_receipt_digest": receipt["record_digest"], "receipt_generation": receipt["receipt_generation"]}


def release_world(overrides=None, extra_contributor=False):
    """A release-proposing admission chain plus training lineage and checkpoint-bound release authority."""
    world = AdmissionWorld(overrides, proposed=["engineering", "release", "train"])
    s2 = world.digest("source_approved")
    world.seal("split_train", {**{k: v for k, v in world.get("split_engineering").items() if k != "record_digest"},
                               "split_id": "split-train", "role": "train", "created_at": t("08:39:30")})
    train_split = world.digest("split_train")
    world.single("train_authorization", world.authorization("auth-train", "train", s2, [train_split],
                                                            [d("engineering-root")], t("08:42:00")),
                 "purpose_authorization_reviewer", ["train"], "syn-purpose-reviewer", t("08:42:00"))
    sources = [s2]
    authorizations = [world.digest("train_authorization")]
    if extra_contributor:
        other = canonical.seal({**{k: v for k, v in world.get("source_approved").items() if k != "record_digest"},
                                "source_id": "syn-src-2"})
        world.extra.append(other)
        world.records["source_other"] = other
        sources.append(other["record_digest"])
        authorizations.append(d("other-train-authorization"))
    experiment = {
        "schema_id": P + "experiment", "schema_version": 1, "experiment_id": "syn-training", "purpose": "train",
        "authorization_registry_digest": world.digest("registry_g3"), "source_record_digests": sorted(sources),
        "purpose_authorization_digests": sorted(authorizations), "source_manifest_digests": [world.digest("manifest")],
        "split_manifest_digests": [train_split], "lineage_root_digests": sorted([world.digest("root_lineage"), d("model-root")]),
        "model_lineage_root_digests": [d("model-root")], "non_model_lineage_root_digests": [world.digest("root_lineage")],
        "decision_execution_receipt_digests": [d("selection-receipt")], "model_selection_receipt_digests": [d("selection-receipt")],
        "non_model_decision_execution_receipt_digests": [], "model_digest": d("checkpoint"),
        "adapted_from_model_digest": d("base-model"), "execution_condition_digest": d("training-condition"),
        "prospective_lock_digest": d("training-lock"), "candidate_ids": ["syn-candidate"],
        "decision_function_digest": d("training-decision-fn"), "created_at": t("08:43:00")}
    world.seal("training_experiment", experiment)
    run = {"schema_id": P + "run", "schema_version": 1, "run_id": "syn-training-run",
           "experiment_digest": world.digest("training_experiment"), "execution_condition_digest": d("training-condition"),
           "reproducibility_record_digest": d("training-repro"), "source_state_digest": d("source-state"),
           "command_digest": d("training-command"), "input_manifest_digests": [d("training-input")],
           "output_manifest_digest": d("training-output"), "started_at": t("08:44:00"), "ended_at": t("08:45:00"),
           "exit_code": 0, "terminal_status": "succeeded", "consumed_experiment_digest": world.digest("training_experiment")}
    world.seal("training_run", run)
    contributors = [{"source_id": source_id, "source_digest": digest, "split_digests": [train_split],
                     "consuming_purposes": ["train"], "purpose_authorization_digests": [auth],
                     "lineage_root_digests": [d("engineering-root")]}
                    for source_id, digest, auth in sorted(
                        [(world.source_id, s2, world.digest("train_authorization"))]
                        + ([("syn-src-2", sources[1], authorizations[1])] if extra_contributor else []))]
    lineage = {"schema_id": P + "model_lineage", "schema_version": 1, "lineage_id": "syn-model-lineage",
               "checkpoint_digest": d("checkpoint"), "base_model_digest": d("base-model"),
               "training_experiment_digests": [world.digest("training_experiment")],
               "training_run_digests": [world.digest("training_run")], "contributing_sources": contributors,
               "source_state_digest": d("source-state"), "created_at": t("08:46:00")}
    world.single("model_lineage", lineage, "release_reviewer", ["release"], "syn-release-reviewer", t("08:46:00"),
                 field="completeness_attestation_digest", domain="model_lineage_completeness")
    model_lineage_lineage = world.lineage(world.digest("model_lineage"), "external_reviewed",
                                          ["release"], t("08:46:30"))
    model_lineage_lineage.update(source_version=d("release-source-version"),
                                 rights_receipt_digest=world.digest("rights"),
                                 grouping_receipt_digest=world.digest("grouping"),
                                 qa_receipt_digest=world.digest("qa_receipt"))
    world.seal("model_lineage_lineage", model_lineage_lineage)
    plan = world.seal("release_plan", {
        "schema_id": P + "decision_plan", "schema_version": 1, "plan_id": "release-plan", "decision_kind": "release",
        "purpose": "release", "scope": "release", "subject_ids": ["syn-candidate"],
        "allowed_input_digests": [world.digest("model_lineage")],
        "forbidden_origin_classes": ["mmbu_derivative", "mmbu_official", "unknown"], "forbidden_root_digests": [],
        "decision_function_digest": d("release-fn"), "command_digest": d("release-command"),
        "source_state_digest": d("source-state"), "sandbox_policy_digest": d("sandbox"),
        "planned_opening_event": {"opening_kind": "protected_access", "trigger": "release-runner",
                                  "not_before": t("08:47:30"), "operator_role": "release_operator",
                                  "protected_artifact_digests": [world.digest("model_lineage")],
                                  "command_template_digest": d("release-template")},
        "operator_id": "syn-release-operator", "created_at": t("08:47:00")})
    payload = world.seal("release_payload", {
        "schema_id": P + "decision_payload", "schema_version": 1, "decision_id": "release-decision",
        "plan_digest": plan["record_digest"], "decision_kind": "release", "purpose": "release",
        "subject_ids": ["syn-candidate"], "selected_subject_ids": ["syn-candidate"],
        "dispositions": [{"subject_id": "syn-candidate", "status": "selected", "reason_code": "release_approved"}],
        "claim_digests": [world.digest("model_lineage")], "rationale_digest": d("release-rationale"),
        "created_at": t("08:48:15")})
    output_lineage_record = world.lineage(payload["record_digest"], "external_reviewed", ["release"],
                                          t("08:48:15"), [(world.digest("model_lineage"), "decision")])
    output_lineage_record.update(source_version=d("release-source-version"),
                                 rights_receipt_digest=world.digest("rights"),
                                 grouping_receipt_digest=world.digest("grouping"),
                                 qa_receipt_digest=world.digest("qa_receipt"))
    output_lineage = world.seal("release_output_lineage", output_lineage_record)
    world.seal("release_receipt", {
        "schema_id": P + "decision_execution_receipt", "schema_version": 1, "receipt_id": "release-receipt",
        "plan_digest": plan["record_digest"], "decision_payload_digest": payload["record_digest"],
        "rationale_digest": d("release-rationale"), "output_lineage_receipt_digest": output_lineage["record_digest"],
        "source_state_digest": d("source-state"), "command_digest": d("release-command"), "sandbox_policy_digest": d("sandbox"),
        "mounted_input_digests": [world.digest("model_lineage")], "observed_content_read_digests": [world.digest("model_lineage")],
        "emitted_output_digests": sorted([payload["record_digest"], d("release-rationale")]), "attempted_denied_reads": [],
        "network_events": [], "operator_attestation": {"operator_id": "syn-release-operator", "no_undeclared_influence": True,
                                                       "no_protected_memory_used": True, "attested_at": t("08:49:00"),
                                                       "attestation_digest": d("release-operator")},
        "independent_review": {"reviewer_id": "syn-release-reviewer-2", "reviewed_plan_digest": plan["record_digest"],
                               "reviewed_payload_digest": payload["record_digest"],
                               "reviewed_rationale_digest": d("release-rationale"), "disposition": "approved",
                               "reviewed_at": t("08:49:00"), "attestation_digest": d("release-review")},
        "started_at": t("08:48:00"), "ended_at": t("08:48:30"), "exit_code": 0, "terminal_status": "succeeded"})
    release = world.authorization("auth-release", "release", s2, [train_split], [d("engineering-root")], t("08:50:00"))
    release.update(released_checkpoint_digest=d("checkpoint"), validated_model_lineage_digest=world.digest("model_lineage"),
                   release_rights_receipt_digest=world.digest("rights"),
                   release_decision_receipt_digest=world.digest("release_receipt"), no_new_data_access=True)
    world.single("release_authorization", release, "release_reviewer", ["release"], "syn-purpose-reviewer", t("08:50:00"))
    return world
