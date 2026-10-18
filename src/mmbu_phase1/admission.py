"""Real-source admission evidence: closed records plus reference/chronology checks.

Phase 1A exercises these validators only with synthetic canary records; no real
biomedical source is acquired, inspected, or admitted.  Executable sampling,
conversion, and approval functions are bound by digest only, so their outputs
are checked by the deterministic projections stated in ``SCHEMAS.md`` rather
than re-executed.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from mmbu_phase1 import canonical, fields as f, paths
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import PURPOSES

PROPOSABLE_PURPOSES = ("engineering", "train", "adaptive_dev", "confirmation", "release")
REVIEWER_ROLES = (
    "acquisition_reviewer",
    "rights_reviewer",
    "grouping_reviewer",
    "clinical_qa_reviewer",
    "visual_qa_reviewer",
    "adjudicator",
    "candidate_admission_reviewer",
    "purpose_authorization_reviewer",
    "release_reviewer",
    "custody_reviewer",
)
STATEMENT_VERSION = "mmbu-review-attestation-v1"
CANONICAL_PATH_PROJECTION_RULE = {"rule": "mmbu.phase1.canonical_path_projection", "version": 1}
CHECKSUM_LENGTHS = {"md5": 32, "sha1": 40, "sha256": 64, "sha512": 128}
_GLOB = re.compile(r"[*?\[\]]")
_HEX = re.compile(r"[0-9a-f]+")

ATTESTATION_KEYS = ("schema_id", "schema_version", "attestation_id", "payload", "payload_digest", "verification",
                    "record_digest")
ATTESTATION_PAYLOAD_KEYS = ("statement_version", "reviewer_id", "reviewer_role", "subject_digest", "purposes",
                            "disposition", "limitations_digest", "reviewed_at", "declaration_text_digest")
VERIFICATION_KEYS = ("method", "verifier_id", "verified_at", "verification_artifact_digest")
ACQUISITION_KEYS = (
    "schema_id", "schema_version", "authorization_id", "source_id", "source_version", "source_family",
    "canonical_locator_ids", "identity_evidence_digests", "terms_digest", "allowed_artifact_names",
    "intended_purpose", "staging_destination", "retrieval_method_digest", "retrieval_command_digest",
    "operator_id", "network_host_allowlist", "maximum_bytes", "decision", "inspection_prohibited",
    "reviewer_attestation_digest", "authorized_at", "expires_at", "supersedes_digest", "record_digest",
)
ACQUISITION_RECEIPT_KEYS = (
    "schema_id", "schema_version", "receipt_id", "acquisition_authorization_digest",
    "authorization_registry_digest", "source_id", "source_version", "source_family", "executed_method_digest",
    "executed_command_digest", "operator_id", "observed_hosts", "observed_artifacts", "staging_destination",
    "started_at", "ended_at", "retrieval_log_digest", "exit_code", "terminal_status", "record_digest",
)
ARTIFACT_MANIFEST_KEYS = (
    "schema_id", "schema_version", "manifest_id", "source_id", "source_version", "source_family",
    "canonical_locator_ids", "acquisition_authorization_digest", "acquisition_execution_receipt_digest",
    "artifacts", "total_bytes", "retriever_id", "retrieved_at", "retrieval_log_digest", "record_digest",
)
ARTIFACT_KEYS = ("logical_path", "bytes", "sha256", "upstream_checksum", "media_type", "role")
RIGHTS_KEYS = (
    "schema_id", "schema_version", "receipt_id", "source_proposal_digest", "source_artifact_manifest_digest",
    "terms_artifact_digests", "provenance_locator_ids", "purpose_findings", "obligations_digest",
    "attribution_text_digest", "reviewer_attestation_digest", "reviewed_at", "expires_at", "record_digest",
)
FINDING_KEYS = ("purpose", "disposition", "basis_digests", "limitations_digest")
GROUPING_KEYS = (
    "schema_id", "schema_version", "receipt_id", "source_artifact_manifest_digest", "source_family",
    "alias_family_ids", "strongest_parent_namespace", "independence_claim", "parent_map_digest",
    "missing_parent_policy", "parent_count", "record_count", "duplicate_checks", "split_construction_rule_digest",
    "reviewer_attestation_digest", "reviewed_at", "record_digest",
)
DUPLICATE_CHECK_KEYS = ("compared_manifest_digests", "roles", "method_digest", "exact_duplicate_count",
                        "perceptual_candidate_count", "reviewed_collision_count", "collision_manifest_digest",
                        "disposition")
INDEPENDENCE_CLAIMS = ("patient", "study", "slide", "volume", "experiment_compound_field", "image_only", "source_only")
POPULATION_KEYS = (
    "schema_id", "schema_version", "population_id", "source_digest", "source_artifact_manifest_digest",
    "inventory_lock_digest", "inventory_opening_receipt_digest", "converter_digest", "exclusion_rule_digest",
    "grouping_receipt_digest", "records", "eligible_record_ids_digest", "eligible_parent_ids_digest",
    "eligible_record_count", "eligible_parent_count", "population_payload_digest", "lineage_receipt_digest",
    "created_at", "record_digest",
)
POPULATION_ROW_KEYS = ("record_id", "parent_id", "artifact_digests", "disposition", "exclusion_reason_code")
POPULATION_PAYLOAD_OMITTED = frozenset({"population_payload_digest", "lineage_receipt_digest", "created_at", "record_digest"})
QA_PLAN_KEYS = (
    "schema_id", "schema_version", "plan_id", "eligible_population_manifest_digest", "purposes",
    "independent_unit_namespace", "method", "sampling_function_digest", "seed_material_digest", "required_n",
    "confidence", "strata", "sample_independent_unit_ids_digest", "sample_record_ids_digest",
    "sample_independent_unit_count", "thresholds", "multiplicity_rule", "approval_function_digest", "created_at",
    "record_digest",
)
STRATUM_KEYS = ("stratum_id", "definition_digest", "eligible_units", "planned_review_units")
QA_RECEIPT_KEYS = (
    "schema_id", "schema_version", "receipt_id", "source_artifact_manifest_digest",
    "eligible_population_manifest_digest", "qa_sampling_plan_digest", "purposes", "converter_digest",
    "target_schema_digest", "eligible_record_manifest_digest", "source_annex_digest",
    "sample_independent_unit_ids_digest", "sample_ids_digest", "error_counts", "overall_threshold_id",
    "critical_error_upper_bound", "critical_error_ceiling", "strata_results", "adjudication",
    "annotation_completeness", "shortcut_results", "approval_function_digest", "reviewer_attestation_digests",
    "disposition", "limitations_digest", "reviewed_at", "record_digest",
)
STRATUM_RESULT_KEYS = ("stratum_id", "threshold_id", "eligible_units", "reviewed_units", "critical", "major", "minor",
                       "critical_upper_bound", "critical_ceiling", "disposition")
ADJUDICATION_KEYS = ("disagreement_count", "disagreement_manifest_digest", "adjudicated_count",
                     "adjudicator_attestation_digest", "unresolved_count")
COMPLETENESS_KEYS = ("target_id", "eligible_units", "annotated_units", "not_annotated_units", "negative_units",
                     "negative_rule_digest", "disposition")
SHORTCUT_KEYS = ("probe_kind", "threshold_id", "input_manifest_digest", "method_digest", "metric_id", "value",
                 "threshold", "disposition")
CUSTODY_KEYS = (
    "schema_id", "schema_version", "custody_id", "source_digest", "quarantine_authorization_digest",
    "inventory_authorization_registry_digest", "inventory_lock_digest", "inventory_opening_receipt_digest",
    "inventory_opening_receipt_registry_digest", "inventory_started_at", "inventory_ended_at",
    "eligible_population_manifest_digest", "qa_sampling_plan_digest", "qa_authorization_registry_digest",
    "qa_lock_digest", "qa_opening_receipt_digest", "qa_opening_receipt_registry_digest", "qa_started_at",
    "qa_ended_at", "eligible_id_manifest_digest", "exclusion_rule_digest", "converter_digest",
    "evaluator_fixture_digest", "eligible_independent_unit_count", "rights_receipt_digest",
    "grouping_receipt_digest", "qa_receipt_digest", "disposition", "limitations_digest",
    "reviewer_attestation_digests", "created_at", "record_digest",
)
SOURCE_KEYS = (
    "schema_id", "schema_version", "source_id", "source_version", "source_family", "origin_class", "status",
    "artifact_manifest_digest", "proposed_purposes", "rights_receipt_digest", "grouping_receipt_digest",
    "qa_receipt_digest", "admission_decision_receipt_digest", "approval_attestation_digest", "allowed_purposes",
    "reviewer_id", "created_at", "reviewed_at", "supersedes_digest", "record_digest",
)
SPLIT_KEYS = (
    "schema_id", "schema_version", "split_id", "source_digest", "source_artifact_manifest_digest", "role",
    "record_manifest_digest", "parent_namespace", "parent_ids_digest", "record_ids_digest",
    "construction_rule_digest", "created_at", "record_digest",
)
SPLIT_ROLES = ("engineering", "train", "adaptive_dev", "confirmation", "official_audit", "quarantine")
MODEL_LINEAGE_KEYS = (
    "schema_id", "schema_version", "lineage_id", "checkpoint_digest", "base_model_digest",
    "training_experiment_digests", "training_run_digests", "contributing_sources", "source_state_digest",
    "completeness_attestation_digest", "created_at", "record_digest",
)
CONTRIBUTOR_KEYS = ("source_id", "source_digest", "split_digests", "consuming_purposes",
                    "purpose_authorization_digests", "lineage_root_digests")
PURPOSE_AUTHORIZATION_KEYS = (
    "schema_id", "schema_version", "authorization_id", "purpose", "source_digest", "split_digests",
    "lineage_root_digests", "decision", "decision_basis_digests", "reviewer_id", "reviewer_attestation_digest",
    "released_checkpoint_digest", "validated_model_lineage_digest", "release_rights_receipt_digest",
    "release_decision_receipt_digest", "no_new_data_access", "decided_at", "expires_at", "supersedes_digest",
    "record_digest",
)
RELEASE_FIELDS = ("released_checkpoint_digest", "validated_model_lineage_digest", "release_rights_receipt_digest",
                  "release_decision_receipt_digest")
PURPOSE_SPLIT_TABLE = {
    "engineering": {"engineering"},
    "quarantine_inspection": {"quarantine"},
    "train": {"train"},
    "adaptive_dev": {"adaptive_dev"},
    "confirmation": {"confirmation"},
    "official_audit": {"official_audit"},
    "release": {"train", "adaptive_dev", "confirmation"},
}
LEGAL_SOURCE_TRANSITIONS = {
    None: {"candidate", "quarantined", "rejected"},
    "candidate": {"quarantined", "approved", "rejected"},
    "quarantined": {"approved", "rejected"},
    "approved": {"rejected"},
    "rejected": set(),
}

# Phase 1A threshold-role conventions inside the closed lock threshold shape.
OVERALL_ESTIMAND = "overall_critical_error"
SHORTCUT_METRIC_PREFIX = "shortcut_probe:"


def ts(value: Any, path: str) -> int:
    return f.timestamp(value, path)


def _ids(value: Any, path: str, *, nonempty: bool = True) -> list[str]:
    return f.string_set(value, path, nonempty=nonempty)


def _basename(value: Any, path: str) -> str:
    paths.relative_path(value, path)
    f.require("/" not in value and not _GLOB.search(value), path, "must be an exact normalized basename, never a glob")
    return value


# ---------------------------------------------------------------------------
# Reviewer attestation


def validate_reviewer_attestation(record: Any, path: str = "reviewer_attestation") -> dict:
    f.record(record, "reviewer_attestation", ATTESTATION_KEYS, path)
    f.text(record["attestation_id"], f"{path}.attestation_id")
    payload = f.closed(record["payload"], f"{path}.payload", ATTESTATION_PAYLOAD_KEYS)
    f.literal(payload["statement_version"], f"{path}.payload.statement_version", STATEMENT_VERSION)
    f.text(payload["reviewer_id"], f"{path}.payload.reviewer_id")
    f.one_of(payload["reviewer_role"], f"{path}.payload.reviewer_role", REVIEWER_ROLES)
    f.digest(payload["subject_digest"], f"{path}.payload.subject_digest")
    f.string_set(payload["purposes"], f"{path}.payload.purposes", nonempty=True, allowed=PURPOSES)
    f.one_of(payload["disposition"], f"{path}.payload.disposition", ("approved", "rejected", "blocked_external"))
    f.digest(payload["limitations_digest"], f"{path}.payload.limitations_digest")
    f.timestamp(payload["reviewed_at"], f"{path}.payload.reviewed_at")
    f.digest(payload["declaration_text_digest"], f"{path}.payload.declaration_text_digest")
    f.require(record["payload_digest"] == canonical.value_digest(payload), f"{path}.payload_digest",
              "must be the SHA-256 of the RFC 8785 canonical payload")
    verification = f.closed(record["verification"], f"{path}.verification", VERIFICATION_KEYS)
    f.one_of(verification["method"], f"{path}.verification.method", ("manual_identity_check", "cryptographic_signature"))
    f.text(verification["verifier_id"], f"{path}.verification.verifier_id")
    f.timestamp(verification["verified_at"], f"{path}.verification.verified_at")
    f.digest(verification["verification_artifact_digest"], f"{path}.verification.verification_artifact_digest")
    return record


def require_attestation(
    store: RecordStore,
    digest: Any,
    path: str,
    *,
    subject: str,
    roles: Iterable[str],
    purposes: Iterable[str] | None = None,
    reviewer_id: str | None = None,
    approved: bool = True,
) -> dict:
    """Resolve an attestation that names the exact reviewed subject bytes."""
    record = validate_reviewer_attestation(store.get(digest, "reviewer_attestation", path), path)
    payload = record["payload"]
    f.require(payload["subject_digest"] == subject, f"{path}.subject_digest", "attestation reviewed different bytes")
    f.require(payload["reviewer_role"] in set(roles), f"{path}.reviewer_role", f"must be one of {sorted(set(roles))}")
    if purposes is not None:
        f.require(payload["purposes"] == sorted(purposes), f"{path}.purposes", "attestation covers different purposes")
    if reviewer_id is not None:
        f.require(payload["reviewer_id"] == reviewer_id, f"{path}.reviewer_id", "differs from the reviewed record")
    if approved:
        f.require(payload["disposition"] == "approved", f"{path}.disposition", "attestation is not approved")
    return record


# ---------------------------------------------------------------------------
# Acquisition


def validate_acquisition_authorization(record: Any, path: str = "acquisition_authorization") -> dict:
    f.record(record, "acquisition_authorization", ACQUISITION_KEYS, path)
    for name in ("authorization_id", "source_id", "source_version", "source_family", "operator_id"):
        f.text(record[name], f"{path}.{name}")
    f.require("|" not in record["source_id"] and "|" not in record["source_version"], path,
              "source identity cannot contain the registry key separator")
    _ids(record["canonical_locator_ids"], f"{path}.canonical_locator_ids")
    f.digest_set(record["identity_evidence_digests"], f"{path}.identity_evidence_digests", nonempty=True)
    f.digest(record["terms_digest"], f"{path}.terms_digest")
    names = _ids(record["allowed_artifact_names"], f"{path}.allowed_artifact_names")
    for index, name in enumerate(names):
        _basename(name, f"{path}.allowed_artifact_names[{index}]")
    f.literal(record["intended_purpose"], f"{path}.intended_purpose", "quarantine_inspection")
    paths.absolute_path(record["staging_destination"], f"{path}.staging_destination")
    f.digest(record["retrieval_method_digest"], f"{path}.retrieval_method_digest")
    f.digest(record["retrieval_command_digest"], f"{path}.retrieval_command_digest")
    _ids(record["network_host_allowlist"], f"{path}.network_host_allowlist")
    f.integer(record["maximum_bytes"], f"{path}.maximum_bytes", minimum=1)
    f.one_of(record["decision"], f"{path}.decision", ("allowed", "denied", "blocked_external"))
    f.literal(record["inspection_prohibited"], f"{path}.inspection_prohibited", True)
    f.digest(record["reviewer_attestation_digest"], f"{path}.reviewer_attestation_digest")
    authorized = ts(record["authorized_at"], f"{path}.authorized_at")
    f.require(ts(record["expires_at"], f"{path}.expires_at") > authorized, f"{path}.expires_at", "must follow authorization")
    f.nullable(f.digest, record["supersedes_digest"], f"{path}.supersedes_digest")
    return record


def check_acquisition_authorization(store: RecordStore, digest: Any, path: str = "acquisition_authorization") -> dict:
    record = validate_acquisition_authorization(store.get(digest, "acquisition_authorization", path), path)
    require_attestation(store, record["reviewer_attestation_digest"], f"{path}.reviewer_attestation_digest",
                        subject=canonical.subject_digest(record, "single_attestation"),
                        roles=("acquisition_reviewer",), purposes=["quarantine_inspection"])
    if record["supersedes_digest"] is not None:
        prior = check_acquisition_authorization(store, record["supersedes_digest"], f"{path}.supersedes_digest")
        for name in ("source_id", "source_version", "source_family"):
            f.require(prior[name] == record[name], f"{path}.{name}", "a successor preserves source identity")
        f.require(ts(prior["authorized_at"], path) < ts(record["authorized_at"], path), f"{path}.authorized_at",
                  "a successor must follow its predecessor")
    return record


def _registry_unchanged(store: RecordStore, registry: dict, start: int, end: int, path: str) -> None:
    f.require(ts(registry["as_of"], path) <= start, path, "registry generation postdates the governed window start")
    for other in store.records("authorization_registry"):
        if other["generation"] > registry["generation"]:
            f.require(ts(other["as_of"], path) > end, path, "authorization registry changed during the governed window")


def _active_head(registry: dict, heads_name: str, key: str, digest: str, path: str) -> None:
    f.require(registry[heads_name].get(key) == digest, path, f"record is not the active registry head for {key!r}")
    f.require(digest not in registry["revoked_digests"], path, "record is revoked")


def validate_acquisition_execution_receipt(record: Any, path: str = "acquisition_execution_receipt") -> dict:
    f.record(record, "acquisition_execution_receipt", ACQUISITION_RECEIPT_KEYS, path)
    for name in ("receipt_id", "source_id", "source_version", "source_family", "operator_id"):
        f.text(record[name], f"{path}.{name}")
    for name in ("acquisition_authorization_digest", "authorization_registry_digest", "executed_method_digest",
                 "executed_command_digest", "retrieval_log_digest"):
        f.digest(record[name], f"{path}.{name}")
    _ids(record["observed_hosts"], f"{path}.observed_hosts")
    artifacts = f.array(record["observed_artifacts"], f"{path}.observed_artifacts", nonempty=True)
    for index, item in enumerate(artifacts):
        label = f"{path}.observed_artifacts[{index}]"
        f.closed(item, label, ("logical_path", "bytes", "sha256"))
        paths.relative_path(item["logical_path"], f"{label}.logical_path")
        f.integer(item["bytes"], f"{label}.bytes", minimum=0)
        f.digest(item["sha256"], f"{label}.sha256")
    f.sorted_unique(artifacts, f"{path}.observed_artifacts", lambda item: item["logical_path"].encode())
    paths.unique_paths([item["logical_path"] for item in artifacts], f"{path}.observed_artifacts")
    paths.absolute_path(record["staging_destination"], f"{path}.staging_destination")
    started = ts(record["started_at"], f"{path}.started_at")
    ended = ts(record["ended_at"], f"{path}.ended_at")
    f.require(ended >= started, f"{path}.ended_at", "must not precede started_at")
    code = f.integer(record["exit_code"], f"{path}.exit_code")
    status = f.one_of(record["terminal_status"], f"{path}.terminal_status", ("succeeded", "failed"))
    f.require((status == "succeeded") == (code == 0), f"{path}.terminal_status", "succeeded exactly at exit code zero")
    return record


def check_acquisition_execution_receipt(store: RecordStore, digest: Any, path: str = "acquisition_execution_receipt") -> dict:
    from mmbu_phase1.registries import check_authorization_registry_chain

    record = validate_acquisition_execution_receipt(store.get(digest, "acquisition_execution_receipt", path), path)
    authorization = check_acquisition_authorization(store, record["acquisition_authorization_digest"],
                                                    f"{path}.acquisition_authorization_digest")
    registry = check_authorization_registry_chain(store, record["authorization_registry_digest"],
                                                  f"{path}.authorization_registry_digest")
    started, ended = ts(record["started_at"], path), ts(record["ended_at"], path)
    key = f"{authorization['source_id']}|{authorization['source_version']}"
    _active_head(registry, "acquisition_heads", key, record["acquisition_authorization_digest"], f"{path}.acquisition_heads")
    _registry_unchanged(store, registry, started, ended, f"{path}.authorization_registry_digest")
    f.require(authorization["decision"] == "allowed", path, "acquisition authorization is not allowed")
    f.require(started < ts(authorization["expires_at"], path), path, "acquisition authorization expired before start")
    f.require(started >= ts(authorization["authorized_at"], path), path, "acquisition started before authorization")
    pairs = (("executed_method_digest", "retrieval_method_digest"), ("executed_command_digest", "retrieval_command_digest"),
             ("operator_id", "operator_id"), ("source_id", "source_id"), ("source_version", "source_version"),
             ("source_family", "source_family"), ("staging_destination", "staging_destination"))
    for mine, theirs in pairs:
        f.require(record[mine] == authorization[theirs], f"{path}.{mine}", "differs from the acquisition authorization")
    f.require(set(record["observed_hosts"]) <= set(authorization["network_host_allowlist"]), f"{path}.observed_hosts",
              "touched an unlisted host")
    total = sum(item["bytes"] for item in record["observed_artifacts"])
    f.require(total <= authorization["maximum_bytes"], f"{path}.observed_artifacts", "retrieval exceeded the byte cap")
    names = sorted(item["logical_path"].rsplit("/", 1)[-1] for item in record["observed_artifacts"])
    f.require(names == authorization["allowed_artifact_names"], f"{path}.observed_artifacts",
              "artifact basenames must equal the authorized set exactly")
    return record


def validate_source_artifact_manifest(record: Any, path: str = "source_artifact_manifest") -> dict:
    f.record(record, "source_artifact_manifest", ARTIFACT_MANIFEST_KEYS, path)
    for name in ("manifest_id", "source_id", "source_version", "source_family", "retriever_id"):
        f.text(record[name], f"{path}.{name}")
    _ids(record["canonical_locator_ids"], f"{path}.canonical_locator_ids")
    for name in ("acquisition_authorization_digest", "acquisition_execution_receipt_digest", "retrieval_log_digest"):
        f.digest(record[name], f"{path}.{name}")
    artifacts = f.array(record["artifacts"], f"{path}.artifacts", nonempty=True)
    for index, item in enumerate(artifacts):
        label = f"{path}.artifacts[{index}]"
        f.closed(item, label, ARTIFACT_KEYS)
        paths.relative_path(item["logical_path"], f"{label}.logical_path")
        f.integer(item["bytes"], f"{label}.bytes", minimum=0)
        f.digest(item["sha256"], f"{label}.sha256")
        checksum = item["upstream_checksum"]
        if checksum is not None:
            f.closed(checksum, f"{label}.upstream_checksum", ("algorithm", "value"))
            algorithm = f.one_of(checksum["algorithm"], f"{label}.upstream_checksum.algorithm", CHECKSUM_LENGTHS)
            value = f.text(checksum["value"], f"{label}.upstream_checksum.value")
            f.require(bool(_HEX.fullmatch(value)) and len(value) == CHECKSUM_LENGTHS[algorithm],
                      f"{label}.upstream_checksum.value", "must be lowercase hexadecimal of the algorithm length")
        f.text(item["media_type"], f"{label}.media_type")
        f.one_of(item["role"], f"{label}.role", ("archive", "metadata", "annotation", "image", "terms"))
    f.sorted_unique(artifacts, f"{path}.artifacts", lambda item: item["logical_path"].encode())
    paths.unique_paths([item["logical_path"] for item in artifacts], f"{path}.artifacts")
    f.integer(record["total_bytes"], f"{path}.total_bytes", minimum=0)
    f.require(record["total_bytes"] == sum(item["bytes"] for item in artifacts), f"{path}.total_bytes",
              "must equal the summed artifact bytes")
    ts(record["retrieved_at"], f"{path}.retrieved_at")
    return record


def check_source_artifact_manifest(store: RecordStore, digest: Any, path: str = "source_artifact_manifest") -> dict:
    record = validate_source_artifact_manifest(store.get(digest, "source_artifact_manifest", path), path)
    receipt = check_acquisition_execution_receipt(store, record["acquisition_execution_receipt_digest"],
                                                  f"{path}.acquisition_execution_receipt_digest")
    f.require(receipt["terminal_status"] == "succeeded", path, "a failed acquisition receipt creates no manifest")
    f.require(receipt["acquisition_authorization_digest"] == record["acquisition_authorization_digest"],
              f"{path}.acquisition_authorization_digest", "differs from the execution receipt")
    authorization = store.get(record["acquisition_authorization_digest"], "acquisition_authorization", path)
    for name in ("source_id", "source_version", "source_family"):
        f.require(record[name] == receipt[name], f"{path}.{name}", "differs from the execution receipt")
    observed = [{k: item[k] for k in ("logical_path", "bytes", "sha256")} for item in record["artifacts"]]
    f.require(f.same(observed, receipt["observed_artifacts"]), f"{path}.artifacts",
              "artifact paths, byte counts, and SHA-256s must equal the execution receipt exactly")
    f.require(record["canonical_locator_ids"] == authorization["canonical_locator_ids"], f"{path}.canonical_locator_ids",
              "must equal the acquisition authorization")
    f.require(record["retriever_id"] == receipt["operator_id"], f"{path}.retriever_id", "must equal the receipt operator")
    f.require(record["retrieved_at"] == receipt["ended_at"], f"{path}.retrieved_at", "must equal the receipt end time")
    f.require(record["retrieval_log_digest"] == receipt["retrieval_log_digest"], f"{path}.retrieval_log_digest",
              "must equal the receipt log digest")
    return record


# ---------------------------------------------------------------------------
# Source records and transitions


def validate_source(record: Any, path: str = "source") -> dict:
    f.record(record, "source", SOURCE_KEYS, path)
    for name in ("source_id", "source_version", "source_family"):
        f.text(record[name], f"{path}.{name}")
    f.require("|" not in record["source_id"], f"{path}.source_id", "cannot contain the registry key separator")
    status = f.one_of(record["status"], f"{path}.status", ("candidate", "quarantined", "approved", "rejected"))
    origin = record["origin_class"]
    f.digest(record["artifact_manifest_digest"], f"{path}.artifact_manifest_digest")
    proposed = f.string_set(record["proposed_purposes"], f"{path}.proposed_purposes", nonempty=True,
                            allowed=PROPOSABLE_PURPOSES)
    review = ("rights_receipt_digest", "grouping_receipt_digest", "qa_receipt_digest")
    decision = ("admission_decision_receipt_digest", "approval_attestation_digest")
    for name in (*review, *decision, "supersedes_digest"):
        f.nullable(f.digest, record[name], f"{path}.{name}")
    f.nullable(f.text, record["reviewer_id"], f"{path}.reviewer_id")
    f.nullable(f.timestamp, record["reviewed_at"], f"{path}.reviewed_at")
    allowed = f.string_set(record["allowed_purposes"], f"{path}.allowed_purposes", allowed=PURPOSES)
    ts(record["created_at"], f"{path}.created_at")
    nulls = lambda names: all(record[name] is None for name in names)  # noqa: E731
    if status == "candidate":
        f.literal(origin, f"{path}.origin_class", "external_quarantine")
        f.require(nulls((*review, *decision, "reviewer_id", "reviewed_at")), path,
                  "a candidate carries no review, admission, or approval evidence")
        f.require(allowed == [], f"{path}.allowed_purposes", "a candidate has empty allowed purposes")
    elif status == "quarantined":
        f.literal(origin, f"{path}.origin_class", "external_quarantine")
        f.require(nulls(decision), path, "a quarantined source has no admission decision or approval")
        f.require((record["reviewer_id"] is None) == (record["reviewed_at"] is None), path,
                  "reviewer and review time are both null or both present")
        f.require(allowed in ([], ["quarantine_inspection"]), f"{path}.allowed_purposes",
                  "empty or exactly quarantine_inspection")
    elif status == "approved":
        f.literal(origin, f"{path}.origin_class", "external_reviewed")
        f.require(not any(record[name] is None for name in (*review, *decision, "reviewer_id", "reviewed_at")), path,
                  "an approved source binds rights, grouping, QA, admission, approval, reviewer, and review time")
        f.require(bool(allowed) and set(allowed) <= set(proposed), f"{path}.allowed_purposes",
                  "a nonempty reviewed subset of the proposed purposes")
    else:
        f.one_of(origin, f"{path}.origin_class", ("external_quarantine", "external_reviewed"))
        f.require(not any(record[name] is None for name in ("approval_attestation_digest", "reviewer_id", "reviewed_at")),
                  path, "a rejection binds its approval attestation, reviewer, and review time")
        f.require(allowed == [], f"{path}.allowed_purposes", "a rejected source has empty allowed purposes")
    return record


def successor_time(record: dict) -> int:
    return ts(record["reviewed_at"] or record["created_at"], "source.successor_time")


def check_source(store: RecordStore, digest: Any, path: str = "source") -> dict:
    """Validate a source record, its artifact manifest, and its full transition chain."""
    record = validate_source(store.get(digest, "source", path), path)
    manifest = check_source_artifact_manifest(store, record["artifact_manifest_digest"], f"{path}.artifact_manifest_digest")
    for name in ("source_id", "source_version", "source_family"):
        f.require(record[name] == manifest[name], f"{path}.{name}", "differs from the source artifact manifest")
    f.require(ts(record["created_at"], path) >= ts(manifest["retrieved_at"], path), f"{path}.created_at",
              "a source record cannot predate its exact artifact manifest")
    previous_status = None
    if record["supersedes_digest"] is not None:
        prior = check_source(store, record["supersedes_digest"], f"{path}.supersedes_digest")
        previous_status = prior["status"]
        for name in ("source_id", "source_version", "source_family", "artifact_manifest_digest", "proposed_purposes"):
            f.require(f.same(prior[name], record[name]), f"{path}.{name}", "cannot mutate across a source transition")
        f.require(successor_time(prior) < successor_time(record), path, "a successor must follow its predecessor")
        if prior["origin_class"] == "external_reviewed":
            f.require(record["origin_class"] == "external_reviewed", f"{path}.origin_class",
                      "external_reviewed never silently returns to external_quarantine")
        if record["status"] == "rejected":
            f.require(record["origin_class"] == prior["origin_class"], f"{path}.origin_class",
                      "a rejection preserves its predecessor origin")
    elif record["status"] == "rejected":
        f.literal(record["origin_class"], f"{path}.origin_class", "external_quarantine")
    f.require(record["status"] in LEGAL_SOURCE_TRANSITIONS[previous_status], f"{path}.status",
              f"illegal source transition {previous_status} -> {record['status']}")
    if record["status"] == "approved":
        _check_approval(store, record, path)
    return record


def _check_approval(store: RecordStore, record: dict, path: str) -> None:
    from mmbu_phase1 import decisions

    rights = check_rights_receipt(store, record["rights_receipt_digest"], f"{path}.rights_receipt_digest")
    check_grouping_receipt(store, record["grouping_receipt_digest"], f"{path}.grouping_receipt_digest")
    qa = check_qa_receipt(store, record["qa_receipt_digest"], f"{path}.qa_receipt_digest")
    f.require(qa["disposition"] == "approved", f"{path}.qa_receipt_digest", "QA receipt is not approved")
    receipt = decisions.check_decision_receipt(store, record["admission_decision_receipt_digest"],
                                               f"{path}.admission_decision_receipt_digest")
    plan = store.get(receipt["plan_digest"], "decision_plan", path)
    payload = store.get(receipt["decision_payload_digest"], "decision_payload", path)
    f.require(plan["decision_kind"] == "candidate_admission", path, "admission must come from a candidate_admission plan")
    f.require(plan["subject_ids"] == [record["source_id"]], path, "the plan's sole subject must be this source")
    f.require(record["supersedes_digest"] in plan["allowed_input_digests"], path,
              "admission inputs must include the active candidate/quarantined predecessor")
    for name in ("artifact_manifest_digest", "rights_receipt_digest", "grouping_receipt_digest", "qa_receipt_digest"):
        f.require(record[name] in plan["allowed_input_digests"], path, f"admission inputs must include {name}")
    f.require(payload["selected_subject_ids"] == [record["source_id"]], path, "the admission payload must select this source")
    f.require(ts(receipt["ended_at"], path) <= ts(record["reviewed_at"], path), path,
              "runner admission must predate the approval review")
    compatible = {item["purpose"] for item in rights["purpose_findings"] if item["disposition"] == "compatible"}
    expected = sorted(set(record["proposed_purposes"]) & compatible & set(qa["purposes"]))
    f.require(bool(expected) and record["allowed_purposes"] == expected, f"{path}.allowed_purposes",
              "must equal the intersection of proposed, compatible-rights, and approved-QA purposes")
    require_attestation(store, record["approval_attestation_digest"], f"{path}.approval_attestation_digest",
                        subject=canonical.subject_digest(record, "source_approval"),
                        roles=("candidate_admission_reviewer",), reviewer_id=record["reviewer_id"])


# ---------------------------------------------------------------------------
# Rights and grouping


def validate_rights_receipt(record: Any, path: str = "rights_receipt") -> dict:
    f.record(record, "rights_receipt", RIGHTS_KEYS, path)
    f.text(record["receipt_id"], f"{path}.receipt_id")
    for name in ("source_proposal_digest", "source_artifact_manifest_digest", "obligations_digest",
                 "attribution_text_digest", "reviewer_attestation_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.digest_set(record["terms_artifact_digests"], f"{path}.terms_artifact_digests", nonempty=True)
    _ids(record["provenance_locator_ids"], f"{path}.provenance_locator_ids")
    findings = f.array(record["purpose_findings"], f"{path}.purpose_findings", nonempty=True)
    for index, item in enumerate(findings):
        label = f"{path}.purpose_findings[{index}]"
        f.closed(item, label, FINDING_KEYS)
        f.one_of(item["purpose"], f"{label}.purpose", PROPOSABLE_PURPOSES)
        f.one_of(item["disposition"], f"{label}.disposition", ("compatible", "incompatible", "blocked_external"))
        f.digest_set(item["basis_digests"], f"{label}.basis_digests", nonempty=True)
        f.digest(item["limitations_digest"], f"{label}.limitations_digest")
    f.sorted_unique(findings, f"{path}.purpose_findings", lambda item: item["purpose"].encode())
    reviewed = ts(record["reviewed_at"], f"{path}.reviewed_at")
    f.require(ts(record["expires_at"], f"{path}.expires_at") > reviewed, f"{path}.expires_at", "must follow review")
    return record


def check_rights_receipt(store: RecordStore, digest: Any, path: str = "rights_receipt") -> dict:
    record = validate_rights_receipt(store.get(digest, "rights_receipt", path), path)
    proposal = validate_source(store.get(record["source_proposal_digest"], "source", f"{path}.source_proposal_digest"))
    f.require(proposal["status"] in {"candidate", "quarantined"}, f"{path}.source_proposal_digest",
              "rights review targets an active candidate/quarantined source")
    f.require(proposal["artifact_manifest_digest"] == record["source_artifact_manifest_digest"],
              f"{path}.source_artifact_manifest_digest", "reviewed a different artifact manifest")
    purposes = [item["purpose"] for item in record["purpose_findings"]]
    f.require(purposes == proposal["proposed_purposes"], f"{path}.purpose_findings",
              "exactly one finding for every proposed purpose (unbound proposed purposes reject)")
    require_attestation(store, record["reviewer_attestation_digest"], f"{path}.reviewer_attestation_digest",
                        subject=canonical.subject_digest(record, "single_attestation"),
                        roles=("rights_reviewer", "release_reviewer"), purposes=proposal["proposed_purposes"])
    return record


def validate_grouping_receipt(record: Any, path: str = "grouping_receipt") -> dict:
    f.record(record, "grouping_receipt", GROUPING_KEYS, path)
    f.text(record["receipt_id"], f"{path}.receipt_id")
    f.text(record["source_family"], f"{path}.source_family")
    for name in ("source_artifact_manifest_digest", "parent_map_digest", "split_construction_rule_digest",
                 "reviewer_attestation_digest"):
        f.digest(record[name], f"{path}.{name}")
    _ids(record["alias_family_ids"], f"{path}.alias_family_ids", nonempty=False)
    strongest = f.text(record["strongest_parent_namespace"], f"{path}.strongest_parent_namespace")
    claim = f.one_of(record["independence_claim"], f"{path}.independence_claim", INDEPENDENCE_CLAIMS)
    f.require(claim in {strongest, "image_only", "source_only"}, f"{path}.independence_claim",
              "cannot exceed the strongest evidenced parent key")
    f.one_of(record["missing_parent_policy"], f"{path}.missing_parent_policy",
             ("reject_record", "quarantine_record", "source_only_no_independence_claim"))
    parents = f.integer(record["parent_count"], f"{path}.parent_count", minimum=0)
    records = f.integer(record["record_count"], f"{path}.record_count", minimum=0)
    f.require(parents <= records, f"{path}.parent_count", "cannot exceed record count")
    checks = f.array(record["duplicate_checks"], f"{path}.duplicate_checks", nonempty=True)
    for index, item in enumerate(checks):
        label = f"{path}.duplicate_checks[{index}]"
        f.closed(item, label, DUPLICATE_CHECK_KEYS)
        f.digest_set(item["compared_manifest_digests"], f"{label}.compared_manifest_digests", nonempty=True)
        _ids(item["roles"], f"{label}.roles")
        f.digest(item["method_digest"], f"{label}.method_digest")
        f.digest(item["collision_manifest_digest"], f"{label}.collision_manifest_digest")
        for name in ("exact_duplicate_count", "perceptual_candidate_count", "reviewed_collision_count"):
            f.integer(item[name], f"{label}.{name}", minimum=0)
        f.require(item["reviewed_collision_count"] >= item["perceptual_candidate_count"], label,
                  "unreviewed perceptual duplicate candidates")
        f.one_of(item["disposition"], f"{label}.disposition", ("clear", "resolved", "blocked_external"))
    f.sorted_unique(checks, f"{path}.duplicate_checks", lambda item: [d.encode() for d in item["compared_manifest_digests"]])
    ts(record["reviewed_at"], f"{path}.reviewed_at")
    return record


def check_grouping_receipt(store: RecordStore, digest: Any, path: str = "grouping_receipt") -> dict:
    record = validate_grouping_receipt(store.get(digest, "grouping_receipt", path), path)
    manifest = validate_source_artifact_manifest(
        store.get(record["source_artifact_manifest_digest"], "source_artifact_manifest", f"{path}.source_artifact_manifest_digest"))
    f.require(record["source_family"] == manifest["source_family"], f"{path}.source_family", "differs from the manifest")
    f.require(any(record["source_artifact_manifest_digest"] in item["compared_manifest_digests"]
                  for item in record["duplicate_checks"]), f"{path}.duplicate_checks",
              "duplicate checks must cover this source's manifest")
    require_attestation(store, record["reviewer_attestation_digest"], f"{path}.reviewer_attestation_digest",
                        subject=canonical.subject_digest(record, "single_attestation"), roles=("grouping_reviewer",))
    return record


# ---------------------------------------------------------------------------
# Eligible population, QA plan, QA receipt, custody


def population_payload_digest(record: dict) -> str:
    return canonical.value_digest({k: v for k, v in record.items() if k not in POPULATION_PAYLOAD_OMITTED})


def validate_eligible_population_manifest(record: Any, path: str = "eligible_population_manifest") -> dict:
    f.record(record, "eligible_population_manifest", POPULATION_KEYS, path)
    f.text(record["population_id"], f"{path}.population_id")
    for name in ("source_digest", "source_artifact_manifest_digest", "inventory_lock_digest",
                 "inventory_opening_receipt_digest", "converter_digest", "exclusion_rule_digest",
                 "grouping_receipt_digest", "eligible_record_ids_digest", "eligible_parent_ids_digest",
                 "population_payload_digest", "lineage_receipt_digest"):
        f.digest(record[name], f"{path}.{name}")
    rows = f.array(record["records"], f"{path}.records", nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}.records[{index}]"
        f.closed(row, label, POPULATION_ROW_KEYS)
        f.text(row["record_id"], f"{label}.record_id")
        f.nullable(f.text, row["parent_id"], f"{label}.parent_id")
        f.digest_set(row["artifact_digests"], f"{label}.artifact_digests", nonempty=True)
        disposition = f.one_of(row["disposition"], f"{label}.disposition", ("eligible", "excluded"))
        if disposition == "eligible":
            f.require(row["exclusion_reason_code"] is None, f"{label}.exclusion_reason_code", "null exactly for eligible")
            f.require(row["parent_id"] is not None, f"{label}.parent_id", "an eligible record needs a parent")
        else:
            f.text(row["exclusion_reason_code"], f"{label}.exclusion_reason_code")
    f.sorted_unique(rows, f"{path}.records", lambda row: row["record_id"].encode())
    eligible = [row for row in rows if row["disposition"] == "eligible"]
    record_ids = [row["record_id"] for row in eligible]
    parent_ids = sorted({row["parent_id"] for row in eligible}, key=lambda value: value.encode())
    f.require(record["eligible_record_ids_digest"] == canonical.value_digest(record_ids), path,
              "eligible record-ID digest is not the canonical projection of eligible rows")
    f.require(record["eligible_parent_ids_digest"] == canonical.value_digest(parent_ids), path,
              "eligible parent-ID digest is not the canonical projection of eligible rows")
    f.require(record["eligible_record_count"] == len(record_ids) and type(record["eligible_record_count"]) is int,
              f"{path}.eligible_record_count", "must equal the eligible projection")
    f.require(record["eligible_parent_count"] == len(parent_ids) and type(record["eligible_parent_count"]) is int,
              f"{path}.eligible_parent_count", "must equal the eligible projection")
    f.require(record["population_payload_digest"] == population_payload_digest(record),
              f"{path}.population_payload_digest", "does not cover the complete closed population payload")
    ts(record["created_at"], f"{path}.created_at")
    return record


def check_eligible_population_manifest(store: RecordStore, digest: Any, path: str = "eligible_population_manifest") -> dict:
    from mmbu_phase1 import lineage, locks

    record = validate_eligible_population_manifest(store.get(digest, "eligible_population_manifest", path), path)
    source = validate_source(store.get(record["source_digest"], "source", f"{path}.source_digest"))
    f.require(source["status"] == "quarantined", f"{path}.source_digest", "inventory runs under a quarantined source")
    f.require(source["artifact_manifest_digest"] == record["source_artifact_manifest_digest"],
              f"{path}.source_artifact_manifest_digest", "differs from the source")
    grouping = validate_grouping_receipt(store.get(record["grouping_receipt_digest"], "grouping_receipt", path))
    if any(row["parent_id"] is None for row in record["records"]):
        f.require(grouping["missing_parent_policy"] in {"reject_record", "quarantine_record"}, f"{path}.records",
                  "a null parent requires an excluding missing-parent policy")
    lock = locks.validate_prospective_lock(store.get(record["inventory_lock_digest"], "prospective_lock", path))
    f.require(lock["scope"]["phase"] == "custody_inventory", f"{path}.inventory_lock_digest", "not an inventory lock")
    opening = locks.check_opening_receipt_chain(store, record["inventory_opening_receipt_digest"],
                                                f"{path}.inventory_opening_receipt_digest")
    f.require(opening["lock_digest"] == record["inventory_lock_digest"], path, "opening receipt governs another lock")
    f.require(ts(opening["first_access_at"], path) < ts(record["created_at"], path), f"{path}.created_at",
              "the active inventory opening must predate the population")
    manifest = store.get(record["source_artifact_manifest_digest"], "source_artifact_manifest", path)
    f.require(ts(opening["first_access_at"], path) > ts(manifest["retrieved_at"], path), f"{path}.inventory_opening",
              "pre-manifest inspection: protected access began before the exact artifact manifest existed")
    receipt = lineage.validate_lineage_receipt(store.get(record["lineage_receipt_digest"], "lineage_receipt", path))
    f.require(receipt["artifact_digest"] == record["population_payload_digest"], f"{path}.lineage_receipt_digest",
              "lineage artifact must be the population payload digest")
    f.require(receipt["origin_class"] == "external_quarantine", f"{path}.lineage_receipt_digest",
              "population lineage origin is external_quarantine")
    expected = sorted(set(source["proposed_purposes"]) | {"quarantine_inspection"})
    f.require(receipt["allowed_purposes"] == expected, f"{path}.lineage_receipt_digest",
              "declares exactly the proposed purposes plus quarantine_inspection")
    return record


def _threshold_roles(plan: dict, path: str) -> tuple[dict, dict, dict]:
    overall = [t for t in plan["thresholds"] if t["estimand_id"] == OVERALL_ESTIMAND]
    strata = {s["stratum_id"] for s in plan["strata"]}
    by_stratum = {t["estimand_id"]: t for t in plan["thresholds"] if t["estimand_id"] in strata}
    shortcuts = {t["metric_id"][len(SHORTCUT_METRIC_PREFIX):]: t for t in plan["thresholds"]
                 if t["metric_id"].startswith(SHORTCUT_METRIC_PREFIX)}
    f.require(len(overall) == 1, f"{path}.thresholds", "exactly one overall critical-error rule is required")
    f.require(set(by_stratum) == strata, f"{path}.thresholds", "exactly one critical-error rule per stratum")
    f.require(len(plan["thresholds"]) == 1 + len(by_stratum) + len(shortcuts), f"{path}.thresholds",
              "every threshold must be the overall, a stratum, or a shortcut-probe rule")
    f.require(bool(shortcuts), f"{path}.thresholds", "at least one required shortcut-probe rule")
    return overall[0], by_stratum, shortcuts


def validate_qa_sampling_plan(record: Any, path: str = "qa_sampling_plan") -> dict:
    from mmbu_phase1 import locks

    f.record(record, "qa_sampling_plan", QA_PLAN_KEYS, path)
    f.text(record["plan_id"], f"{path}.plan_id")
    for name in ("eligible_population_manifest_digest", "sampling_function_digest", "seed_material_digest",
                 "sample_independent_unit_ids_digest", "sample_record_ids_digest", "approval_function_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.string_set(record["purposes"], f"{path}.purposes", nonempty=True, allowed=PROPOSABLE_PURPOSES)
    f.text(record["independent_unit_namespace"], f"{path}.independent_unit_namespace")
    f.one_of(record["method"], f"{path}.method", ("simple_random", "stratified", "clustered", "stratified_clustered", "census"))
    required = f.integer(record["required_n"], f"{path}.required_n", minimum=1)
    f.number(record["confidence"], f"{path}.confidence", minimum=0, maximum=1, min_exclusive=True, max_exclusive=True)
    strata = f.array(record["strata"], f"{path}.strata", nonempty=True)
    for index, item in enumerate(strata):
        label = f"{path}.strata[{index}]"
        f.closed(item, label, STRATUM_KEYS)
        f.text(item["stratum_id"], f"{label}.stratum_id")
        f.digest(item["definition_digest"], f"{label}.definition_digest")
        eligible = f.integer(item["eligible_units"], f"{label}.eligible_units", minimum=1)
        f.integer(item["planned_review_units"], f"{label}.planned_review_units", minimum=1, maximum=eligible)
    f.sorted_unique(strata, f"{path}.strata", lambda item: item["stratum_id"].encode())
    f.require(sum(item["planned_review_units"] for item in strata) == required, f"{path}.strata",
              "planned review units must sum to required_n")
    f.require(record["sample_independent_unit_count"] == required, f"{path}.sample_independent_unit_count",
              "must equal required_n")
    locks.validate_thresholds(record["thresholds"], f"{path}.thresholds")
    multiplicity = locks.validate_multiplicity(record["multiplicity_rule"], f"{path}.multiplicity_rule")
    _threshold_roles(record, path)
    f.require(multiplicity["hypothesis_ids"] == [t["threshold_id"] for t in record["thresholds"]],
              f"{path}.multiplicity_rule.hypothesis_ids", "must equal all decision-bearing QA threshold IDs")
    ts(record["created_at"], f"{path}.created_at")
    return record


def qa_group_projection(plan: dict) -> list[dict]:
    return [
        {"group_id": s["stratum_id"], "definition_digest": s["definition_digest"],
         "parent_unit": plan["independent_unit_namespace"], "minimum_parents": s["planned_review_units"],
         "role": "multiplicity_family", "underpowered_disposition": "block"}
        for s in plan["strata"]
    ]


def check_qa_sampling_plan(store: RecordStore, digest: Any, path: str = "qa_sampling_plan") -> dict:
    from mmbu_phase1 import locks

    plan = validate_qa_sampling_plan(store.get(digest, "qa_sampling_plan", path), path)
    population = check_eligible_population_manifest(store, plan["eligible_population_manifest_digest"],
                                                    f"{path}.eligible_population_manifest_digest")
    source = store.get(population["source_digest"], "source", path)
    f.require(plan["purposes"] == source["proposed_purposes"], f"{path}.purposes",
              "must equal the source's complete proposed-purpose set")
    inventory_opening = store.get(population["inventory_opening_receipt_digest"], "opening_receipt", path)
    created = ts(plan["created_at"], path)
    f.require(created > ts(population["created_at"], path), f"{path}.created_at", "plan must follow the population")
    f.require(created > ts(inventory_opening["first_access_at"], path), f"{path}.created_at",
              "plan must follow the inventory opening")
    qa_locks = [lock for lock in store.records("prospective_lock") if lock["qa_sampling_plan_digest"] == digest]
    f.require(len(qa_locks) == 1, f"{path}.qa_lock", "exactly one custody-QA lock binds this plan")
    lock = locks.validate_prospective_lock(qa_locks[0])
    f.require(lock["scope"]["phase"] == "custody_qa", f"{path}.qa_lock", "binding lock is not custody_qa")
    f.require(created < ts(lock["created_at"], path), f"{path}.created_at", "plan must predate the QA lock (backdating)")
    f.require({digest, population["record_digest"]} <= set(lock["input_artifact_digests"]), f"{path}.qa_lock",
              "QA lock inputs must include the exact plan and population")
    f.require(lock["seed_ids"] == [plan["seed_material_digest"]], f"{path}.qa_lock.seed_ids",
              "must be exactly the singleton seed_material_digest")
    f.require(f.same(lock["thresholds"], plan["thresholds"]), f"{path}.qa_lock.thresholds", "must equal the plan")
    f.require(f.same(lock["multiplicity_rule"], plan["multiplicity_rule"]), f"{path}.qa_lock.multiplicity_rule",
              "must equal the plan")
    f.require(lock["decision_function_digest"] == plan["approval_function_digest"], f"{path}.qa_lock",
              "decision function must equal the approval function")
    f.require(f.same(lock["groups"], qa_group_projection(plan)), f"{path}.qa_lock.groups",
              "must be the exact stratum projection")
    f.require(lock["scope"]["analysis_population_digest"] == population["record_digest"], f"{path}.qa_lock.scope",
              "analysis population must equal the plan's population")
    for opening in store.records("opening_receipt"):
        if opening["lock_digest"] == lock["record_digest"]:
            f.require({digest, population["record_digest"]} <= set(opening["manifest_digests"]), f"{path}.qa_opening",
                      "QA opening must bind both the plan and population")
            f.require(created < ts(opening["first_access_at"], path), f"{path}.qa_opening", "plan must predate QA opening")
    return plan


def validate_qa_receipt(record: Any, path: str = "qa_receipt") -> dict:
    f.record(record, "qa_receipt", QA_RECEIPT_KEYS, path)
    f.text(record["receipt_id"], f"{path}.receipt_id")
    for name in ("source_artifact_manifest_digest", "eligible_population_manifest_digest", "qa_sampling_plan_digest",
                 "converter_digest", "target_schema_digest", "eligible_record_manifest_digest", "source_annex_digest",
                 "sample_independent_unit_ids_digest", "sample_ids_digest", "approval_function_digest",
                 "limitations_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.string_set(record["purposes"], f"{path}.purposes", nonempty=True, allowed=PROPOSABLE_PURPOSES)
    counts = f.closed(record["error_counts"], f"{path}.error_counts", ("critical", "major", "minor", "reviewed_independent_units"))
    for name, value in counts.items():
        f.integer(value, f"{path}.error_counts.{name}", minimum=0)
    f.text(record["overall_threshold_id"], f"{path}.overall_threshold_id")
    for name in ("critical_error_upper_bound", "critical_error_ceiling"):
        f.number(record[name], f"{path}.{name}", minimum=0, maximum=1)
    strata = f.array(record["strata_results"], f"{path}.strata_results", nonempty=True)
    for index, item in enumerate(strata):
        label = f"{path}.strata_results[{index}]"
        f.closed(item, label, STRATUM_RESULT_KEYS)
        f.text(item["stratum_id"], f"{label}.stratum_id")
        f.text(item["threshold_id"], f"{label}.threshold_id")
        for name in ("eligible_units", "reviewed_units", "critical", "major", "minor"):
            f.integer(item[name], f"{label}.{name}", minimum=0)
        for name in ("critical_upper_bound", "critical_ceiling"):
            f.number(item[name], f"{label}.{name}", minimum=0, maximum=1)
        f.one_of(item["disposition"], f"{label}.disposition", ("pass", "fail", "underpowered"))
    f.sorted_unique(strata, f"{path}.strata_results", lambda item: item["stratum_id"].encode())
    adjudication = f.closed(record["adjudication"], f"{path}.adjudication", ADJUDICATION_KEYS)
    for name in ("disagreement_count", "adjudicated_count", "unresolved_count"):
        f.integer(adjudication[name], f"{path}.adjudication.{name}", minimum=0)
    f.digest(adjudication["disagreement_manifest_digest"], f"{path}.adjudication.disagreement_manifest_digest")
    if adjudication["disagreement_count"]:
        f.digest(adjudication["adjudicator_attestation_digest"], f"{path}.adjudication.adjudicator_attestation_digest")
    else:
        f.nullable(f.digest, adjudication["adjudicator_attestation_digest"], f"{path}.adjudication.adjudicator_attestation_digest")
    completeness = f.array(record["annotation_completeness"], f"{path}.annotation_completeness", nonempty=True)
    for index, item in enumerate(completeness):
        label = f"{path}.annotation_completeness[{index}]"
        f.closed(item, label, COMPLETENESS_KEYS)
        f.text(item["target_id"], f"{label}.target_id")
        for name in ("eligible_units", "annotated_units", "not_annotated_units", "negative_units"):
            f.integer(item[name], f"{label}.{name}", minimum=0)
        f.require(item["annotated_units"] + item["not_annotated_units"] == item["eligible_units"], label,
                  "annotation statuses must exhaust eligible units")
        f.require(item["negative_units"] <= item["annotated_units"], label, "not_annotated never counts as negative")
        f.digest(item["negative_rule_digest"], f"{label}.negative_rule_digest")
        f.one_of(item["disposition"], f"{label}.disposition", ("pass", "fail", "blocked_external"))
    f.sorted_unique(completeness, f"{path}.annotation_completeness", lambda item: item["target_id"].encode())
    shortcuts = f.array(record["shortcut_results"], f"{path}.shortcut_results", nonempty=True)
    for index, item in enumerate(shortcuts):
        label = f"{path}.shortcut_results[{index}]"
        f.closed(item, label, SHORTCUT_KEYS)
        for name in ("probe_kind", "threshold_id", "metric_id"):
            f.text(item[name], f"{label}.{name}")
        for name in ("input_manifest_digest", "method_digest"):
            f.digest(item[name], f"{label}.{name}")
        f.number(item["value"], f"{label}.value")
        f.number(item["threshold"], f"{label}.threshold")
        f.one_of(item["disposition"], f"{label}.disposition", ("pass", "fail", "underpowered"))
    f.sorted_unique(shortcuts, f"{path}.shortcut_results", lambda item: item["probe_kind"].encode())
    f.digest_set(record["reviewer_attestation_digests"], f"{path}.reviewer_attestation_digests", nonempty=True)
    f.one_of(record["disposition"], f"{path}.disposition", ("approved", "rejected", "blocked_external"))
    ts(record["reviewed_at"], f"{path}.reviewed_at")
    return record


def _stratum_disposition(item: dict, planned: int) -> str:
    if item["reviewed_units"] < planned:
        return "underpowered"
    return "pass" if canonical.exact(item["critical_upper_bound"]) <= canonical.exact(item["critical_ceiling"]) else "fail"


def _shortcut_disposition(item: dict, rule: dict) -> str:
    value, bound = canonical.exact(item["value"]), canonical.exact(item["threshold"])
    if rule["direction"] == "at_most":
        return "pass" if value <= bound else "fail"
    if rule["direction"] == "at_least":
        return "pass" if value >= bound else "fail"
    return "pass" if abs(value) <= bound else "fail"


def check_qa_receipt(store: RecordStore, digest: Any, path: str = "qa_receipt") -> dict:
    record = validate_qa_receipt(store.get(digest, "qa_receipt", path), path)
    plan = check_qa_sampling_plan(store, record["qa_sampling_plan_digest"], f"{path}.qa_sampling_plan_digest")
    population = store.get(record["eligible_population_manifest_digest"], "eligible_population_manifest", path)
    f.require(plan["eligible_population_manifest_digest"] == record["eligible_population_manifest_digest"], path,
              "receipt binds a different population than its plan")
    f.require(population["source_artifact_manifest_digest"] == record["source_artifact_manifest_digest"], path,
              "receipt binds a different artifact manifest")
    f.require(record["purposes"] == plan["purposes"], f"{path}.purposes", "must equal the plan's purposes")
    f.require(record["converter_digest"] == population["converter_digest"], f"{path}.converter_digest",
              "must equal the population converter")
    f.require(record["sample_independent_unit_ids_digest"] == plan["sample_independent_unit_ids_digest"]
              and record["sample_ids_digest"] == plan["sample_record_ids_digest"], path,
              "sample digests must equal the frozen plan")
    f.require(record["approval_function_digest"] == plan["approval_function_digest"], f"{path}.approval_function_digest",
              "must equal the plan")
    lock = next(lock for lock in store.records("prospective_lock") if lock["qa_sampling_plan_digest"] == plan["record_digest"])
    openings = [o for o in store.records("opening_receipt") if o["lock_digest"] == lock["record_digest"]]
    f.require(bool(openings), path, "QA review requires a QA opening receipt")
    f.require(ts(record["reviewed_at"], path) > max(ts(o["first_access_at"], path) for o in openings), f"{path}.reviewed_at",
              "QA review must follow the QA opening")
    overall, by_stratum, shortcut_rules = _threshold_roles(plan, f"{path}.plan")
    f.require(record["overall_threshold_id"] == overall["threshold_id"], f"{path}.overall_threshold_id",
              "must resolve the plan's sole overall critical-error rule")
    f.require(canonical.exact(record["critical_error_ceiling"]) == canonical.exact(overall["value"]),
              f"{path}.critical_error_ceiling", "must equal the frozen overall value")
    planned = {s["stratum_id"]: s for s in plan["strata"]}
    f.require([s["stratum_id"] for s in record["strata_results"]] == list(planned), f"{path}.strata_results",
              "must be the exact plan-stratum projection")
    complete = record["error_counts"]["reviewed_independent_units"] == plan["required_n"]
    strata_pass = True
    for item in record["strata_results"]:
        frozen = planned[item["stratum_id"]]
        rule = by_stratum[item["stratum_id"]]
        label = f"{path}.strata_results[{item['stratum_id']}]"
        f.require(item["eligible_units"] == frozen["eligible_units"], label, "eligible units differ from the plan")
        f.require(item["threshold_id"] == rule["threshold_id"], label, "threshold must resolve this stratum's rule")
        f.require(canonical.exact(item["critical_ceiling"]) == canonical.exact(rule["value"]), label,
                  "ceiling must equal the frozen value")
        expected = _stratum_disposition(item, frozen["planned_review_units"])
        f.require(item["disposition"] == expected, label, f"disposition must recompute as {expected}")
        strata_pass &= expected == "pass" and item["reviewed_units"] == frozen["planned_review_units"]
    f.require([r["probe_kind"] for r in record["shortcut_results"]] == sorted(shortcut_rules, key=str.encode),
              f"{path}.shortcut_results", "exactly one result for every planned shortcut rule")
    shortcuts_pass = True
    for item in record["shortcut_results"]:
        rule = shortcut_rules[item["probe_kind"]]
        label = f"{path}.shortcut_results[{item['probe_kind']}]"
        f.require(item["threshold_id"] == rule["threshold_id"] and item["metric_id"] == rule["metric_id"], label,
                  "metric/threshold must equal the frozen rule")
        f.require(canonical.exact(item["threshold"]) == canonical.exact(rule["value"]), label, "threshold value drift")
        expected = _shortcut_disposition(item, rule)
        f.require(item["disposition"] == expected, label, f"disposition must recompute as {expected}")
        shortcuts_pass &= expected == "pass"
    overall_pass = canonical.exact(record["critical_error_upper_bound"]) <= canonical.exact(record["critical_error_ceiling"])
    annotation_pass = all(item["disposition"] == "pass" for item in record["annotation_completeness"])
    adjudication_ok = record["adjudication"]["unresolved_count"] == 0
    if record["disposition"] == "approved":
        f.require(complete and strata_pass and shortcuts_pass and overall_pass and annotation_pass and adjudication_ok,
                  f"{path}.disposition", "approval requires complete review and every frozen rule to pass")
    roles = ("clinical_qa_reviewer", "visual_qa_reviewer", "adjudicator")
    subject = canonical.subject_digest(record, "multi_attestation")
    reviewers = set()
    for attestation_digest in record["reviewer_attestation_digests"]:
        attestation = require_attestation(store, attestation_digest, f"{path}.reviewer_attestation_digests",
                                          subject=subject, roles=roles, purposes=record["purposes"],
                                          approved=record["disposition"] == "approved")
        reviewers.add(attestation["payload"]["reviewer_role"])
    f.require({"clinical_qa_reviewer", "visual_qa_reviewer"} <= reviewers, f"{path}.reviewer_attestation_digests",
              "distinct clinical and visual QA attestations are required")
    if record["adjudication"]["disagreement_count"]:
        f.require(record["adjudication"]["adjudicator_attestation_digest"] in record["reviewer_attestation_digests"],
                  f"{path}.adjudication", "a distinct adjudicator attestation is required when reviewers disagree")
    return record


def validate_custody_summary(record: Any, path: str = "custody_summary") -> dict:
    f.record(record, "custody_summary", CUSTODY_KEYS, path)
    f.text(record["custody_id"], f"{path}.custody_id")
    for name in CUSTODY_KEYS:
        if name.endswith("_digest") and name != "record_digest":
            f.digest(record[name], f"{path}.{name}")
    for name in ("inventory_started_at", "inventory_ended_at", "qa_started_at", "qa_ended_at", "created_at"):
        ts(record[name], f"{path}.{name}")
    f.integer(record["eligible_independent_unit_count"], f"{path}.eligible_independent_unit_count", minimum=0)
    f.one_of(record["disposition"], f"{path}.disposition", ("passed", "failed", "blocked_external"))
    f.digest_set(record["reviewer_attestation_digests"], f"{path}.reviewer_attestation_digests", nonempty=True)
    order = [ts(record[name], path) for name in ("inventory_started_at", "inventory_ended_at")]
    f.require(order[1] >= order[0], f"{path}.inventory_ended_at", "must not precede inventory start")
    f.require(ts(record["qa_ended_at"], path) >= ts(record["qa_started_at"], path), f"{path}.qa_ended_at",
              "must not precede QA start")
    f.require(ts(record["created_at"], path) >= ts(record["qa_ended_at"], path), f"{path}.created_at",
              "summary must follow the QA window")
    return record


def _window_head(store: RecordStore, registry_digest: str, receipt_digest: str, start: int, end: int, path: str) -> None:
    from mmbu_phase1 import locks

    locks.require_registered_head(store, registry_digest, receipt_digest, path)
    receipt = store.get(receipt_digest, "opening_receipt", path)
    f.require(ts(receipt["first_access_at"], path) <= start, path, "protected access began before its opening receipt")
    registry = store.get(registry_digest, "opening_receipt_registry", path)
    f.require(ts(registry["created_at"], path) <= start, path, "opening registry postdates the window")
    for other in store.records("opening_receipt"):
        if other["supersedes_receipt_digest"] == receipt_digest and other["lock_digest"] == receipt["lock_digest"]:
            for successor_registry in store.records("opening_receipt_registry"):
                if any(h["head_receipt_digest"] == other["record_digest"] for h in successor_registry["heads"]):
                    f.require(ts(successor_registry["created_at"], path) > end, path,
                              "the governing opening receipt stopped being head during the window")


def _authority_active(store: RecordStore, registry_digest: str, source_digest: str, authorization_digest: str,
                      start: int, end: int, path: str) -> None:
    from mmbu_phase1.registries import check_authorization_registry_chain

    registry = check_authorization_registry_chain(store, registry_digest, path)
    _registry_unchanged(store, registry, start, end, path)
    source = store.get(source_digest, "source", path)
    authorization = store.get(authorization_digest, "purpose_authorization", path)
    _active_head(registry, "source_heads", source["source_id"], source_digest, f"{path}.source_heads")
    _active_head(registry, "authorization_heads", f"{source['source_id']}|quarantine_inspection", authorization_digest,
                 f"{path}.authorization_heads")
    if authorization["expires_at"] is not None:
        f.require(ts(authorization["expires_at"], path) > end, path, "quarantine authorization expires inside the window")


def check_custody_summary(store: RecordStore, digest: Any, path: str = "custody_summary") -> dict:
    from mmbu_phase1 import locks

    record = validate_custody_summary(store.get(digest, "custody_summary", path), path)
    source = check_source(store, record["source_digest"], f"{path}.source_digest")
    f.require(source["status"] == "quarantined", f"{path}.source_digest", "custody runs under the quarantined source")
    authorization = check_purpose_authorization(store, record["quarantine_authorization_digest"],
                                                f"{path}.quarantine_authorization_digest")
    f.require(authorization["purpose"] == "quarantine_inspection" and authorization["decision"] == "allowed"
              and authorization["source_digest"] == record["source_digest"], f"{path}.quarantine_authorization_digest",
              "requires an allowed quarantine_inspection authorization for this source")
    population = check_eligible_population_manifest(store, record["eligible_population_manifest_digest"], path)
    plan = check_qa_sampling_plan(store, record["qa_sampling_plan_digest"], path)
    qa = check_qa_receipt(store, record["qa_receipt_digest"], path)
    inv = (ts(record["inventory_started_at"], path), ts(record["inventory_ended_at"], path))
    qa_window = (ts(record["qa_started_at"], path), ts(record["qa_ended_at"], path))
    f.require(population["record_digest"] == plan["eligible_population_manifest_digest"] ==
              qa["eligible_population_manifest_digest"], path, "population, plan, and QA receipt disagree")
    f.require(plan["record_digest"] == qa["qa_sampling_plan_digest"], path, "QA receipt binds another plan")
    f.require(ts(population["created_at"], path) >= inv[1], path, "population must follow the inventory window")
    f.require(ts(plan["created_at"], path) > ts(population["created_at"], path), path, "plan must follow population")
    f.require(qa_window[0] > ts(plan["created_at"], path), f"{path}.qa_started_at", "QA must start after the plan")
    f.require(ts(qa["reviewed_at"], path) <= qa_window[1] and ts(qa["reviewed_at"], path) >= qa_window[0], path,
              "QA review falls outside the QA window")
    f.require(record["inventory_lock_digest"] == population["inventory_lock_digest"]
              and record["inventory_opening_receipt_digest"] == population["inventory_opening_receipt_digest"], path,
              "inventory lock/opening differ from the population")
    qa_lock = locks.validate_prospective_lock(store.get(record["qa_lock_digest"], "prospective_lock", path))
    f.require(qa_lock["qa_sampling_plan_digest"] == plan["record_digest"], f"{path}.qa_lock_digest", "QA lock binds another plan")
    qa_opening = store.get(record["qa_opening_receipt_digest"], "opening_receipt", path)
    f.require(qa_opening["lock_digest"] == record["qa_lock_digest"], f"{path}.qa_opening_receipt_digest",
              "QA opening governs another lock")
    _window_head(store, record["inventory_opening_receipt_registry_digest"], record["inventory_opening_receipt_digest"],
                 inv[0], inv[1], f"{path}.inventory_opening")
    _window_head(store, record["qa_opening_receipt_registry_digest"], record["qa_opening_receipt_digest"],
                 qa_window[0], qa_window[1], f"{path}.qa_opening")
    for registry_name, window in (("inventory_authorization_registry_digest", inv), ("qa_authorization_registry_digest", qa_window)):
        _authority_active(store, record[registry_name], record["source_digest"], record["quarantine_authorization_digest"],
                          window[0], window[1], f"{path}.{registry_name}")
    f.require(record["eligible_id_manifest_digest"] == population["eligible_record_ids_digest"], path,
              "eligible-ID manifest must equal the population projection")
    f.require(record["exclusion_rule_digest"] == population["exclusion_rule_digest"]
              and record["converter_digest"] == population["converter_digest"], path, "converter/exclusion rule drift")
    f.require(record["eligible_independent_unit_count"] == population["eligible_parent_count"], path,
              "must equal the population's eligible-parent count")
    f.require(record["grouping_receipt_digest"] == population["grouping_receipt_digest"], path, "grouping receipt drift")
    check_rights_receipt(store, record["rights_receipt_digest"], f"{path}.rights_receipt_digest")
    subject = canonical.subject_digest(record, "multi_attestation")
    reviewers = set()
    for attestation_digest in record["reviewer_attestation_digests"]:
        attestation = require_attestation(store, attestation_digest, f"{path}.reviewer_attestation_digests",
                                          subject=subject, roles=("custody_reviewer",),
                                          approved=record["disposition"] == "passed")
        if record["disposition"] != "passed":
            f.require(attestation["payload"]["disposition"] != "approved", path, "approved only when custody passed")
        reviewers.add(attestation["payload"]["reviewer_id"])
    f.require(len(reviewers) == len(record["reviewer_attestation_digests"]), path, "custody attestations must be distinct")
    return record


# ---------------------------------------------------------------------------
# Split, model lineage, purpose authorization


def canonical_path_projection_digest() -> str:
    return canonical.value_digest(CANONICAL_PATH_PROJECTION_RULE)


def validate_split(record: Any, path: str = "split") -> dict:
    f.record(record, "split", SPLIT_KEYS, path)
    f.text(record["split_id"], f"{path}.split_id")
    f.one_of(record["role"], f"{path}.role", SPLIT_ROLES)
    for name in ("source_digest", "source_artifact_manifest_digest", "record_manifest_digest", "parent_ids_digest",
                 "record_ids_digest", "construction_rule_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.text(record["parent_namespace"], f"{path}.parent_namespace")
    ts(record["created_at"], f"{path}.created_at")
    return record


def check_split(store: RecordStore, digest: Any, path: str = "split") -> dict:
    record = validate_split(store.get(digest, "split", path), path)
    source = validate_source(store.get(record["source_digest"], "source", f"{path}.source_digest"))
    f.require(source["artifact_manifest_digest"] == record["source_artifact_manifest_digest"],
              f"{path}.source_artifact_manifest_digest", "differs from the bound source")
    if record["role"] == "quarantine":
        manifest = validate_source_artifact_manifest(store.get(record["source_artifact_manifest_digest"],
                                                                "source_artifact_manifest", path))
        projection = canonical.value_digest([item["logical_path"] for item in manifest["artifacts"]])
        f.literal(record["parent_namespace"], f"{path}.parent_namespace", "artifact_path")
        for name in ("record_manifest_digest", "record_ids_digest", "parent_ids_digest"):
            f.require(record[name] == projection, f"{path}.{name}", "must be the exact sorted artifact-path projection")
        f.require(record["construction_rule_digest"] == canonical_path_projection_digest(),
                  f"{path}.construction_rule_digest", "must be the canonical path projection")
    else:
        f.require(source["status"] == "approved", f"{path}.source_digest",
                  "non-quarantine splits are constructed only from an approved post-inventory source")
        f.require(record["parent_namespace"] != "artifact_path", f"{path}.parent_namespace",
                  "post-inventory splits use the strongest evidenced parent namespace")
        f.require(ts(record["created_at"], path) >= successor_time(source), f"{path}.created_at",
                  "split cannot predate its source review")
    return record


def check_split_parent_disjointness(store: RecordStore, split_digests: Iterable[str], path: str = "splits") -> None:
    """One biomedical parent cannot cross train/adaptive_dev/confirmation within a source family."""
    seen: dict[tuple[str, str], str] = {}
    for digest in split_digests:
        split = validate_split(store.get(digest, "split", path), path)
        if split["role"] not in {"train", "adaptive_dev", "confirmation"}:
            continue
        family = store.get(split["source_digest"], "source", path)["source_family"]
        parents = canonical.loads(store.artifact(split["parent_ids_digest"], f"{path}.parent_ids_digest"))
        f.string_set(parents, f"{path}.parent_ids")
        for parent in parents:
            previous = seen.get((family, parent))
            f.require(previous in (None, split["role"]), path,
                      f"parent crosses {previous} and {split['role']} in source family {family}")
            seen[(family, parent)] = split["role"]


def validate_model_lineage(record: Any, path: str = "model_lineage") -> dict:
    f.record(record, "model_lineage", MODEL_LINEAGE_KEYS, path)
    f.text(record["lineage_id"], f"{path}.lineage_id")
    for name in ("checkpoint_digest", "base_model_digest", "source_state_digest", "completeness_attestation_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.digest_set(record["training_experiment_digests"], f"{path}.training_experiment_digests", nonempty=True)
    f.digest_set(record["training_run_digests"], f"{path}.training_run_digests", nonempty=True)
    rows = f.array(record["contributing_sources"], f"{path}.contributing_sources", nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}.contributing_sources[{index}]"
        f.closed(row, label, CONTRIBUTOR_KEYS)
        f.text(row["source_id"], f"{label}.source_id")
        f.digest(row["source_digest"], f"{label}.source_digest")
        f.digest_set(row["split_digests"], f"{label}.split_digests", nonempty=True)
        f.string_set(row["consuming_purposes"], f"{label}.consuming_purposes", nonempty=True, allowed=("train", "adaptive_dev"))
        f.digest_set(row["purpose_authorization_digests"], f"{label}.purpose_authorization_digests", nonempty=True)
        f.digest_set(row["lineage_root_digests"], f"{label}.lineage_root_digests", nonempty=True)
    f.sorted_unique(rows, f"{path}.contributing_sources", lambda row: (row["source_id"].encode(), row["source_digest"].encode()))
    ids = [row["source_id"] for row in rows]
    f.require(len(ids) == len(set(ids)), f"{path}.contributing_sources", "a source_id may appear only once")
    ts(record["created_at"], f"{path}.created_at")
    return record


def check_model_lineage(store: RecordStore, digest: Any, path: str = "model_lineage") -> dict:
    from mmbu_phase1.experiment import validate_run

    record = validate_model_lineage(store.get(digest, "model_lineage", path), path)
    experiments = set(record["training_experiment_digests"])
    for run_digest in record["training_run_digests"]:
        run = validate_run(store.get(run_digest, "run", f"{path}.training_run_digests"))
        f.require(run["experiment_digest"] in experiments, f"{path}.training_run_digests",
                  "every training run must bind a named training experiment")
    bound = {run["experiment_digest"] for run in (store.get(d, "run") for d in record["training_run_digests"])}
    f.require(bound == experiments, f"{path}.training_experiment_digests", "every named experiment needs a finalized run")
    influenced: set[str] = set()
    for experiment_digest in record["training_experiment_digests"]:
        experiment = store.get(experiment_digest, "experiment", f"{path}.training_experiment_digests")
        influenced.update(experiment["source_record_digests"])
    contributors = {row["source_digest"] for row in record["contributing_sources"]}
    f.require(contributors == influenced, f"{path}.contributing_sources",
              "contributing sources must equal every real source that influenced the checkpoint")
    for row in record["contributing_sources"]:
        source = store.get(row["source_digest"], "source", path)
        f.require(source["source_id"] == row["source_id"], path, "contributing source ID mismatch")
        authorized_purposes: set[str] = set()
        authorized_splits: set[str] = set()
        authorized_roots: set[str] = set()
        for authorization_digest in row["purpose_authorization_digests"]:
            authorization = check_purpose_authorization(store, authorization_digest,
                                                        f"{path}.purpose_authorization_digests")
            f.require(authorization["source_digest"] == row["source_digest"]
                      and authorization["purpose"] in row["consuming_purposes"]
                      and authorization["decision"] == "allowed", path, "contributor authorization mismatch")
            authorized_purposes.add(authorization["purpose"])
            authorized_splits.update(authorization["split_digests"])
            authorized_roots.update(authorization["lineage_root_digests"])
        f.require(authorized_purposes == set(row["consuming_purposes"]), path,
                  "consuming purposes must equal the contributor authorizations")
        f.require(authorized_splits == set(row["split_digests"]), path,
                  "split digests must equal the contributor authorizations")
        f.require(authorized_roots == set(row["lineage_root_digests"]), path,
                  "lineage roots must equal the contributor authorizations")
    require_attestation(store, record["completeness_attestation_digest"], f"{path}.completeness_attestation_digest",
                        subject=canonical.subject_digest(record, "model_lineage_completeness"), roles=("release_reviewer",))
    return record


def validate_purpose_authorization(record: Any, path: str = "purpose_authorization") -> dict:
    f.record(record, "purpose_authorization", PURPOSE_AUTHORIZATION_KEYS, path)
    f.text(record["authorization_id"], f"{path}.authorization_id")
    purpose = f.one_of(record["purpose"], f"{path}.purpose", PURPOSES)
    f.digest(record["source_digest"], f"{path}.source_digest")
    f.digest_set(record["split_digests"], f"{path}.split_digests", nonempty=True)
    f.digest_set(record["lineage_root_digests"], f"{path}.lineage_root_digests")
    decision = f.one_of(record["decision"], f"{path}.decision", ("allowed", "denied", "blocked_external"))
    f.digest_set(record["decision_basis_digests"], f"{path}.decision_basis_digests", nonempty=True)
    f.text(record["reviewer_id"], f"{path}.reviewer_id")
    f.digest(record["reviewer_attestation_digest"], f"{path}.reviewer_attestation_digest")
    if purpose == "release" and decision == "allowed":
        for name in RELEASE_FIELDS:
            f.digest(record[name], f"{path}.{name}")
        f.literal(record["no_new_data_access"], f"{path}.no_new_data_access", True)
    else:
        f.require(all(record[name] is None for name in (*RELEASE_FIELDS, "no_new_data_access")), path,
                  "release fields are null unless release is allowed")
    decided = ts(record["decided_at"], f"{path}.decided_at")
    if record["expires_at"] is not None:
        f.require(ts(record["expires_at"], f"{path}.expires_at") > decided, f"{path}.expires_at", "must follow decision")
    f.nullable(f.digest, record["supersedes_digest"], f"{path}.supersedes_digest")
    return record


def check_purpose_authorization(store: RecordStore, digest: Any, path: str = "purpose_authorization") -> dict:
    from mmbu_phase1 import lineage

    record = validate_purpose_authorization(store.get(digest, "purpose_authorization", path), path)
    source = validate_source(store.get(record["source_digest"], "source", f"{path}.source_digest"))
    if record["decision"] == "allowed":
        f.require(record["purpose"] in source["allowed_purposes"], f"{path}.purpose",
                  "allowed purpose must be a subset of the source's allowed purposes")
    roles = ("release_reviewer",) if record["purpose"] == "release" else ("purpose_authorization_reviewer",)
    require_attestation(store, record["reviewer_attestation_digest"], f"{path}.reviewer_attestation_digest",
                        subject=canonical.subject_digest(record, "single_attestation"), roles=roles,
                        reviewer_id=record["reviewer_id"])
    for split_digest in record["split_digests"]:
        split = check_split(store, split_digest, f"{path}.split_digests")
        f.require(split["source_digest"] == record["source_digest"], f"{path}.split_digests", "split binds another source")
        f.require(split["role"] in PURPOSE_SPLIT_TABLE[record["purpose"]], f"{path}.split_digests",
                  f"split role {split['role']} is illegal for purpose {record['purpose']}")
    if record["decision"] == "allowed" and record["purpose"] != "quarantine_inspection":
        for root in record["lineage_root_digests"]:
            lineage.require_purpose(store, root, record["purpose"], f"{path}.lineage_root_digests")
    if record["supersedes_digest"] is not None:
        prior = validate_purpose_authorization(store.get(record["supersedes_digest"], "purpose_authorization", path))
        f.require(ts(prior["decided_at"], path) < ts(record["decided_at"], path), path, "successor must follow predecessor")
        prior_source = store.get(prior["source_digest"], "source", path)
        f.require(prior_source["source_id"] == source["source_id"] and prior["purpose"] == record["purpose"], path,
                  "a successor keeps the same source identity and purpose")
    if record["purpose"] == "release" and record["decision"] == "allowed":
        _check_release(store, record, path)
    return record


def _check_release(store: RecordStore, record: dict, path: str) -> None:
    from mmbu_phase1 import decisions

    lineage_record = check_model_lineage(store, record["validated_model_lineage_digest"], f"{path}.validated_model_lineage_digest")
    f.require(record["released_checkpoint_digest"] == lineage_record["checkpoint_digest"], f"{path}.released_checkpoint_digest",
              "must equal the model-lineage checkpoint")
    rows = [row for row in lineage_record["contributing_sources"]
            if row["source_digest"] == record["source_digest"] and row["split_digests"] == record["split_digests"]
            and row["lineage_root_digests"] == record["lineage_root_digests"]]
    f.require(len(rows) == 1, path, "release source/splits/roots must exactly match one contributing-source row")
    rights = check_rights_receipt(store, record["release_rights_receipt_digest"], f"{path}.release_rights_receipt_digest")
    f.require(any(item["purpose"] == "release" and item["disposition"] == "compatible" for item in rights["purpose_findings"]),
              f"{path}.release_rights_receipt_digest", "rights receipt lacks a compatible release finding")
    receipt = decisions.check_decision_receipt(
        store, record["release_decision_receipt_digest"], f"{path}.release_decision_receipt_digest")
    plan = store.get(receipt["plan_digest"], "decision_plan", path)
    f.require(plan["decision_kind"] == "release", f"{path}.release_decision_receipt_digest", "not a runner release decision")
    covered = set()
    for other in store.records("purpose_authorization"):
        if (other["purpose"] == "release" and other["decision"] == "allowed"
                and other["validated_model_lineage_digest"] == record["validated_model_lineage_digest"]):
            f.require(other["released_checkpoint_digest"] == record["released_checkpoint_digest"]
                      and other["release_decision_receipt_digest"] == record["release_decision_receipt_digest"], path,
                      "release authorizations disagree on checkpoint or release decision")
            covered.add(other["source_digest"])
    contributors = {row["source_digest"] for row in lineage_record["contributing_sources"]}
    f.require(covered == contributors, path, "every contributing source needs one matching allowed release authorization")


def require_active_leaf(store: RecordStore, registry: dict, digest: str, kind: str, at_ns: int, path: str) -> dict:
    """An authorization/source record must be the unexpired, unsuperseded registered head at ``at``."""
    if kind == "source":
        record = validate_source(store.get(digest, "source", path), path)
        f.require(digest in registry["source_record_digests"], path, "source record is not registered")
        _active_head(registry, "source_heads", record["source_id"], digest, path)
        successors = [r for r in store.records("source") if r["supersedes_digest"] == digest]
        for successor in successors:
            f.require(successor_time(successor) > at_ns, path, "a valid successor supersedes this source record")
    else:
        record = validate_purpose_authorization(store.get(digest, "purpose_authorization", path), path)
        f.require(digest in registry["purpose_authorization_digests"], path, "authorization is not registered")
        source = store.get(record["source_digest"], "source", path)
        _active_head(registry, "authorization_heads", f"{source['source_id']}|{record['purpose']}", digest, path)
        f.require(record["expires_at"] is None or ts(record["expires_at"], path) > at_ns, path, "authorization expired")
        for successor in store.records("purpose_authorization"):
            if successor["supersedes_digest"] == digest:
                f.require(ts(successor["decided_at"], path) > at_ns, path, "a valid successor supersedes this authorization")
    return record
