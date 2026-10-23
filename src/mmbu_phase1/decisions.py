"""Decision plan, payload, and execution receipt: the external-only decision firewall.

These validators check declared records and synthetic canaries.  They do not
prove that an operating system restricted mounts, traced every read, or denied
networking; a real hermetic sandbox is outside Phase 1A.
"""

from __future__ import annotations

from typing import Any

from mmbu_phase1 import fields as f, lineage
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import DECISION_KINDS, FORBIDDEN_PROMOTABLE_ORIGINS, ORIGINS, PURPOSES, RUN_TERMINAL_STATUSES

PLAN_KEYS = (
    "schema_id",
    "schema_version",
    "plan_id",
    "decision_kind",
    "purpose",
    "scope",
    "subject_ids",
    "allowed_input_digests",
    "forbidden_origin_classes",
    "forbidden_root_digests",
    "decision_function_digest",
    "command_digest",
    "source_state_digest",
    "sandbox_policy_digest",
    "planned_opening_event",
    "operator_id",
    "created_at",
    "record_digest",
)
OPENING_EVENT_KEYS = (
    "opening_kind",
    "trigger",
    "not_before",
    "operator_role",
    "protected_artifact_digests",
    "command_template_digest",
)
PAYLOAD_KEYS = (
    "schema_id",
    "schema_version",
    "decision_id",
    "plan_digest",
    "decision_kind",
    "purpose",
    "subject_ids",
    "selected_subject_ids",
    "dispositions",
    "claim_digests",
    "rationale_digest",
    "created_at",
    "record_digest",
)
RECEIPT_KEYS = (
    "schema_id",
    "schema_version",
    "receipt_id",
    "plan_digest",
    "decision_payload_digest",
    "rationale_digest",
    "output_lineage_receipt_digest",
    "source_state_digest",
    "command_digest",
    "sandbox_policy_digest",
    "mounted_input_digests",
    "observed_content_read_digests",
    "emitted_output_digests",
    "attempted_denied_reads",
    "network_events",
    "operator_attestation",
    "independent_review",
    "started_at",
    "ended_at",
    "exit_code",
    "terminal_status",
    "record_digest",
)
OPERATOR_KEYS = ("operator_id", "no_undeclared_influence", "no_protected_memory_used", "attested_at", "attestation_digest")
REVIEW_KEYS = (
    "reviewer_id",
    "reviewed_plan_digest",
    "reviewed_payload_digest",
    "reviewed_rationale_digest",
    "disposition",
    "reviewed_at",
    "attestation_digest",
)
DISPOSITION_STATUSES = ("selected", "not_selected", "blocked", "ineligible")
CLEAN_OUTPUT_ORIGINS = frozenset({"external_reviewed", "external_quarantine", "synthetic_engineering"})
CANDIDATE_ADMISSION_INPUT_SCHEMAS = (
    "source",
    "source_artifact_manifest",
    "rights_receipt",
    "grouping_receipt",
    "qa_receipt",
    "qa_sampling_plan",
    "eligible_population_manifest",
    "custody_summary",
    "reviewer_attestation",
    "lineage_receipt",
)


def validate_opening_event(event: Any, path: str) -> dict:
    f.closed(event, path, OPENING_EVENT_KEYS)
    f.one_of(event["opening_kind"], f"{path}.opening_kind", ("first_output", "protected_access"))
    f.text(event["trigger"], f"{path}.trigger")
    f.timestamp(event["not_before"], f"{path}.not_before")
    f.text(event["operator_role"], f"{path}.operator_role")
    f.digest_set(event["protected_artifact_digests"], f"{path}.protected_artifact_digests", nonempty=True)
    f.digest(event["command_template_digest"], f"{path}.command_template_digest")
    return event


def validate_decision_plan(record: Any, path: str = "decision_plan") -> dict:
    f.record(record, "decision_plan", PLAN_KEYS, path)
    f.text(record["plan_id"], f"{path}.plan_id")
    kind = f.one_of(record["decision_kind"], f"{path}.decision_kind", DECISION_KINDS)
    purpose = f.one_of(record["purpose"], f"{path}.purpose", PURPOSES)
    f.text(record["scope"], f"{path}.scope")
    subjects = f.string_set(record["subject_ids"], f"{path}.subject_ids", nonempty=True)
    f.digest_set(record["allowed_input_digests"], f"{path}.allowed_input_digests", nonempty=True)
    forbidden = f.string_set(record["forbidden_origin_classes"], f"{path}.forbidden_origin_classes", allowed=ORIGINS)
    if purpose != "official_audit":
        f.require(
            tuple(forbidden) == FORBIDDEN_PROMOTABLE_ORIGINS,
            f"{path}.forbidden_origin_classes",
            "must be exactly mmbu_derivative, mmbu_official, unknown",
        )
    f.digest_set(record["forbidden_root_digests"], f"{path}.forbidden_root_digests")
    for name in ("decision_function_digest", "command_digest", "source_state_digest", "sandbox_policy_digest"):
        f.digest(record[name], f"{path}.{name}")
    event = validate_opening_event(record["planned_opening_event"], f"{path}.planned_opening_event")
    f.text(record["operator_id"], f"{path}.operator_id")
    created = f.timestamp(record["created_at"], f"{path}.created_at")
    f.require(created < f.timestamp(event["not_before"], path), f"{path}.created_at", "plan must predate its opening event")
    if kind == "candidate_admission":
        f.require(purpose == "quarantine_inspection", f"{path}.purpose", "candidate admission is quarantine_inspection only")
        f.require(len(subjects) == 1, f"{path}.subject_ids", "candidate admission has exactly one subject")
    return record


def validate_decision_payload(record: Any, path: str = "decision_payload") -> dict:
    f.record(record, "decision_payload", PAYLOAD_KEYS, path)
    f.text(record["decision_id"], f"{path}.decision_id")
    f.digest(record["plan_digest"], f"{path}.plan_digest")
    f.one_of(record["decision_kind"], f"{path}.decision_kind", DECISION_KINDS)
    f.one_of(record["purpose"], f"{path}.purpose", PURPOSES)
    subjects = f.string_set(record["subject_ids"], f"{path}.subject_ids", nonempty=True)
    selected = f.string_set(record["selected_subject_ids"], f"{path}.selected_subject_ids")
    f.require(set(selected) <= set(subjects), f"{path}.selected_subject_ids", "must be a subset of subject_ids")
    dispositions = f.array(record["dispositions"], f"{path}.dispositions")
    for index, item in enumerate(dispositions):
        label = f"{path}.dispositions[{index}]"
        f.closed(item, label, ("subject_id", "status", "reason_code"))
        f.text(item["subject_id"], f"{label}.subject_id")
        f.one_of(item["status"], f"{label}.status", DISPOSITION_STATUSES)
        f.text(item["reason_code"], f"{label}.reason_code")
    f.sorted_unique(dispositions, f"{path}.dispositions", lambda item: item["subject_id"].encode())
    f.require([d["subject_id"] for d in dispositions] == subjects, f"{path}.dispositions", "one disposition per subject")
    f.require(
        [d["subject_id"] for d in dispositions if d["status"] == "selected"] == selected,
        f"{path}.selected_subject_ids",
        "must equal the subjects whose disposition is selected",
    )
    f.digest_set(record["claim_digests"], f"{path}.claim_digests", nonempty=True)
    f.digest(record["rationale_digest"], f"{path}.rationale_digest")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def validate_decision_execution_receipt(record: Any, path: str = "decision_execution_receipt") -> dict:
    f.record(record, "decision_execution_receipt", RECEIPT_KEYS, path)
    f.text(record["receipt_id"], f"{path}.receipt_id")
    for name in (
        "plan_digest",
        "decision_payload_digest",
        "rationale_digest",
        "output_lineage_receipt_digest",
        "source_state_digest",
        "command_digest",
        "sandbox_policy_digest",
    ):
        f.digest(record[name], f"{path}.{name}")
    f.digest_set(record["mounted_input_digests"], f"{path}.mounted_input_digests", nonempty=True)
    f.digest_set(record["observed_content_read_digests"], f"{path}.observed_content_read_digests")
    f.digest_set(record["emitted_output_digests"], f"{path}.emitted_output_digests", nonempty=True)
    f.array(record["attempted_denied_reads"], f"{path}.attempted_denied_reads")
    f.array(record["network_events"], f"{path}.network_events")
    operator = f.closed(record["operator_attestation"], f"{path}.operator_attestation", OPERATOR_KEYS)
    f.text(operator["operator_id"], f"{path}.operator_attestation.operator_id")
    f.boolean(operator["no_undeclared_influence"], f"{path}.operator_attestation.no_undeclared_influence")
    f.boolean(operator["no_protected_memory_used"], f"{path}.operator_attestation.no_protected_memory_used")
    f.timestamp(operator["attested_at"], f"{path}.operator_attestation.attested_at")
    f.digest(operator["attestation_digest"], f"{path}.operator_attestation.attestation_digest")
    review = f.closed(record["independent_review"], f"{path}.independent_review", REVIEW_KEYS)
    f.text(review["reviewer_id"], f"{path}.independent_review.reviewer_id")
    for name in ("reviewed_plan_digest", "reviewed_payload_digest", "reviewed_rationale_digest", "attestation_digest"):
        f.digest(review[name], f"{path}.independent_review.{name}")
    f.one_of(review["disposition"], f"{path}.independent_review.disposition", ("approved", "rejected"))
    f.timestamp(review["reviewed_at"], f"{path}.independent_review.reviewed_at")
    started = f.timestamp(record["started_at"], f"{path}.started_at")
    ended = f.timestamp(record["ended_at"], f"{path}.ended_at")
    f.require(ended >= started, f"{path}.ended_at", "must not precede started_at")
    f.integer(record["exit_code"], f"{path}.exit_code")
    f.one_of(record["terminal_status"], f"{path}.terminal_status", RUN_TERMINAL_STATUSES)
    return record


def check_decision_plan(store: RecordStore, plan: dict, path: str = "decision_plan") -> dict:
    """Every allowlisted input resolves before the plan to an eligible lineage."""
    validate_decision_plan(plan, path)
    created = f.timestamp(plan["created_at"], path)
    if plan["decision_kind"] == "candidate_admission":
        # Closed preapproval exception: only the subject's admission evidence may be read.
        for digest in plan["allowed_input_digests"]:
            store.get(digest, CANDIDATE_ADMISSION_INPUT_SCHEMAS, f"{path}.allowed_input_digests")
        return plan
    for digest in plan["allowed_input_digests"]:
        label = f"{path}.allowed_input_digests[{digest[:12]}]"
        if lineage.is_official_rule_summary(store, digest):
            continue  # governance constraint; never enters the purpose intersection
        lineage.require_purpose(store, digest, plan["purpose"], label, not_after_ns=created)
        for receipt in lineage.walk(store, digest, label):
            f.require(receipt["origin_class"] not in plan["forbidden_origin_classes"], label, "forbidden origin class")
            f.require(receipt["artifact_digest"] not in plan["forbidden_root_digests"], label, "forbidden decision root")
    return plan


def check_decision_receipt(
    store: RecordStore,
    receipt_digest: Any,
    path: str = "decision_execution_receipt",
    *,
    official_hash_index: frozenset[str] = frozenset(),
) -> dict:
    """Full eligibility of one decision execution for experiment binding."""
    receipt = validate_decision_execution_receipt(store.get(receipt_digest, "decision_execution_receipt", path), path)
    plan = check_decision_plan(store, store.get(receipt["plan_digest"], "decision_plan", f"{path}.plan_digest"))
    payload = validate_decision_payload(
        store.get(receipt["decision_payload_digest"], "decision_payload", f"{path}.decision_payload_digest")
    )
    started = f.timestamp(receipt["started_at"], path)
    ended = f.timestamp(receipt["ended_at"], path)
    f.require(f.timestamp(plan["created_at"], path) < started, f"{path}.started_at", "plan must exist before execution")
    f.require(
        started >= f.timestamp(plan["planned_opening_event"]["not_before"], path),
        f"{path}.started_at",
        "execution started before the planned opening event",
    )
    for name in ("command_digest", "source_state_digest", "sandbox_policy_digest"):
        f.require(receipt[name] == plan[name], f"{path}.{name}", "differs from the decision plan")
    mounted = receipt["mounted_input_digests"]
    f.require(mounted == plan["allowed_input_digests"], f"{path}.mounted_input_digests", "must equal the complete allowlist")
    f.require(
        set(receipt["observed_content_read_digests"]) <= set(mounted),
        f"{path}.observed_content_read_digests",
        "sandbox recorded an unallowlisted read",
    )
    f.require(not receipt["attempted_denied_reads"], f"{path}.attempted_denied_reads", "denied-read attempt recorded")
    f.require(not receipt["network_events"], f"{path}.network_events", "network activity recorded")
    hits = lineage.hash_index_hits([*mounted, *receipt["observed_content_read_digests"]], official_hash_index)
    f.require(hits == 0, f"{path}.mounted_input_digests", "an input matches the restricted official hash index")
    f.require(
        receipt["emitted_output_digests"] == sorted([receipt["decision_payload_digest"], receipt["rationale_digest"]]),
        f"{path}.emitted_output_digests",
        "must be exactly the payload and rationale digests",
    )
    f.require(receipt["rationale_digest"] not in mounted, f"{path}.rationale_digest", "undeclared copied rationale")
    expected = {
        "plan_digest": receipt["plan_digest"],
        "decision_kind": plan["decision_kind"],
        "purpose": plan["purpose"],
        "subject_ids": plan["subject_ids"],
        "rationale_digest": receipt["rationale_digest"],
    }
    for name, value in expected.items():
        f.require(f.same(payload[name], value), f"{path}.decision_payload.{name}", "payload differs from plan/receipt")
    f.require(set(payload["claim_digests"]) <= set(mounted), f"{path}.decision_payload.claim_digests",
              "claims must resolve to allowlisted inputs")
    created = f.timestamp(payload["created_at"], path)
    f.require(started <= created <= ended, f"{path}.decision_payload.created_at", "payload created outside the runner")
    output = lineage.validate_lineage_receipt(
        store.get(receipt["output_lineage_receipt_digest"], "lineage_receipt", f"{path}.output_lineage_receipt_digest")
    )
    f.require(output["artifact_digest"] == receipt["decision_payload_digest"], f"{path}.output_lineage", "wrong artifact")
    f.require(output["origin_class"] in CLEAN_OUTPUT_ORIGINS, f"{path}.output_lineage", "output origin is not clean")
    parent_digests = [edge["parent_digest"] for edge in output["parents"]]
    f.require(sorted(parent_digests) == mounted and len(parent_digests) == len(set(parent_digests)),
              f"{path}.output_lineage.parents", "direct parents must equal the complete mounted input set")
    for edge in output["parents"]:
        expected_role = "governance" if lineage.is_official_rule_summary(store, edge["parent_digest"]) else "decision"
        f.require(edge["edge_role"] == expected_role, f"{path}.output_lineage.parents", "wrong decision edge role")
    operator = receipt["operator_attestation"]
    f.require(operator["operator_id"] == plan["operator_id"], f"{path}.operator_attestation", "operator differs from plan")
    f.require(operator["no_undeclared_influence"] is True and operator["no_protected_memory_used"] is True,
              f"{path}.operator_attestation", "operator attestation does not exclude undeclared influence/memory")
    review = receipt["independent_review"]
    f.require(review["reviewer_id"] not in {plan["operator_id"], operator["operator_id"]},
              f"{path}.independent_review", "decision operator cannot self-review")
    f.require(review["reviewed_plan_digest"] == receipt["plan_digest"]
              and review["reviewed_payload_digest"] == receipt["decision_payload_digest"]
              and review["reviewed_rationale_digest"] == receipt["rationale_digest"],
              f"{path}.independent_review", "review covers different bytes")
    f.require(review["disposition"] == "approved", f"{path}.independent_review", "independent review did not approve")
    f.require(f.timestamp(review["reviewed_at"], path) >= ended, f"{path}.independent_review", "review predates output")
    f.require(receipt["exit_code"] == 0 and receipt["terminal_status"] == "succeeded",
              f"{path}.terminal_status", "decision execution did not succeed")
    if plan["purpose"] != "official_audit" and plan["decision_kind"] != "candidate_admission":
        # Candidate admission is the closed preapproval exception: it grants no model-use purpose.
        lineage.require_purpose(store, receipt["decision_payload_digest"], plan["purpose"], f"{path}.output_lineage")
    return receipt
