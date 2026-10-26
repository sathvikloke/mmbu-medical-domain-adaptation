"""Fail-closed BUSI-WHU held-out confirmation mechanics.

This module is CPU-only and performs validation and exact arithmetic. It has
no data acquisition, model, scheduler, network, or accelerator integration.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import random

from mmbu_phase1 import admission, canonical, decisions, rational
from mmbu_phase1.store import RecordStore
from mmbu_phase1.busi_whu_review_validation import validate_authenticated_completed_review
from mmbu_phase1.fields import (
    ContractViolation, boolean, closed, digest, fail, integer, literal, require, text, timestamp,
)


SPEC_DIGEST = "f73f4b6f088ead82d5045145d829abff90cd4dc259585c68678242693d47c75f"
SPEC_KEYS = (
    "authorization", "candidate", "confirmation_id", "gates", "prompts", "resources",
    "schema_id", "schema_version", "source", "statistics", "training",
)


def validate_spec(value: object) -> dict:
    """Validate the one prospectively frozen confirmation protocol exactly."""
    record = closed(value, "heldout_confirmation.spec", SPEC_KEYS)
    try:
        digest = canonical.value_digest(record)
    except (canonical.CanonicalJSONError, TypeError, ValueError) as exc:
        fail("heldout_confirmation.spec", f"is not canonicalizable: {exc}")
    if digest != SPEC_DIGEST:
        fail("heldout_confirmation.spec", "does not match the frozen protocol digest")
    return record


def load_spec(path: Path) -> dict:
    try:
        value = canonical.loads(path.read_bytes())
    except (OSError, canonical.CanonicalJSONError) as exc:
        raise ContractViolation("heldout_confirmation.spec", f"cannot load: {exc}") from None
    return validate_spec(value)


LINEAGE_KEYS = (
    "base_model_id", "base_revision", "expected_parameter_count", "legacy_exploratory_adapter_used",
    "lora_alpha", "lora_dropout", "lora_rank", "lora_target_suffixes", "mmbu_public_content_used",
    "optimizer_updates", "post_admission_retraining", "profile", "runtime_gate_id", "runtime_gate_passed",
    "source_purposes", "training_seed",
)


def validate_checkpoint_lineage(value: object, path: str = "heldout_confirmation.lineage") -> dict:
    """Accept only a newly retrained, fully authorized member of the fixed family."""
    row = closed(value, path, LINEAGE_KEYS)
    expected = {
        "base_model_id": "Qwen/Qwen3.5-9B",
        "base_revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "expected_parameter_count": 9409813744,
        "legacy_exploratory_adapter_used": False,
        "lora_alpha": 16,
        "lora_dropout": 0,
        "lora_rank": 8,
        "lora_target_suffixes": ["q_proj", "v_proj"],
        "mmbu_public_content_used": False,
        "optimizer_updates": 1024,
        "post_admission_retraining": True,
        "profile": "dual",
        "runtime_gate_id": "qwen3.5-9b-successor-native-runtime",
        "runtime_gate_passed": True,
        "source_purposes": {"busbra": "train", "pathmnist": "train"},
    }
    for key, expected_value in expected.items():
        literal(row[key], f"{path}.{key}", expected_value)
    require(type(row["training_seed"]) is int and row["training_seed"] in (20261025, 20261026, 20261027),
            f"{path}.training_seed", "must be one of the three frozen non-boolean integer seeds")
    return row


REVIEW_REPORT_KEYS = (
    "adjudicated_record_count", "adjudication_review_sha256", "confirmation_purposes_ready",
    "duplicate_excluded_record_ids", "duplicate_group_constraints", "eligible_by_task",
    "excluded_record_ids", "independently_reviewed_record_count", "mmbu_public_content_used",
    "model_use_authorized", "packet_manifest_digest", "packet_receipt_digest",
    "opening_authorization_digest", "opening_receipt_digest", "review_authentication",
    "phase1_admission_still_required", "primary_review_sha256", "purpose_decisions", "record_digest",
    "review_evidence_complete", "review_opening_sha256", "reviewed_record_count",
    "reviewer_identity_authenticated", "rights_review_sha256", "schema_id", "schema_version",
    "secondary_review_sha256", "source_admission_authorized", "source_blockers", "training_ready",
    "unresolved_record_ids", "target_map", "target_map_digest", "global_task_manifest_digest",
)
REVIEW_AUTHENTICATION_KEYS = (
    "authenticated_at", "base_review_report_digest", "clinical_assessment_digest",
    "custodian_assessment_digest", "opening_authorization_digest", "opening_receipt_digest",
    "review_attestation_digests",
)
SOURCE_MANIFEST_KEYS = (
    "confirmation_task", "duplicate_disposition_digest", "exclusions_digest",
    "mmbu_public_content_used", "model_use_authorized", "patient_count", "patient_ids",
    "patient_to_records", "purpose_authorization_digest", "record_count", "record_digest",
    "record_ids", "review_validation_digest", "schema_id", "schema_version",
    "source_admission_digest", "source_id", "source_version", "source_role", "training_allowed",
    "target_map", "target_map_digest", "global_task_manifest_digest",
)


def _validate_target_map(value: object, record_ids: list[str], path: str) -> dict[str, str]:
    require(type(value) is dict and set(value) == set(record_ids), path,
            "must name every locked record exactly")
    normalized: dict[str, str] = {}
    for record_id in record_ids:
        label = value[record_id]
        require(type(label) is str and label in ("benign", "malignant"),
                f"{path}.{record_id}", "must be benign or malignant")
        normalized[record_id] = label
    return normalized


def _validated_bridge_inputs(
    review_report: object, store: RecordStore, source_admission_digest: str,
    purpose_authorization_digest: str,
) -> tuple[dict, dict, dict]:
    report = closed(review_report, "heldout_confirmation.review_report", REVIEW_REPORT_KEYS)
    try:
        validate_authenticated_completed_review(report, store)
    except (ContractViolation, ValueError) as exc:
        fail("heldout_confirmation.review_report.review_authentication", str(exc))
    digest(report["record_digest"], "heldout_confirmation.review_report.record_digest")
    literal(report["record_digest"], "heldout_confirmation.review_report.record_digest",
            canonical.record_digest(report))
    literal(report["schema_id"], "heldout_confirmation.review_report.schema_id",
            "mmbu.phase1.busi_whu_review_validation")
    literal(report["schema_version"], "heldout_confirmation.review_report.schema_version", 1)
    literal(report["review_evidence_complete"],
            "heldout_confirmation.review_report.review_evidence_complete", True)
    literal(report["reviewer_identity_authenticated"],
            "heldout_confirmation.review_report.reviewer_identity_authenticated", True)
    authentication = closed(
        report["review_authentication"], "heldout_confirmation.review_report.review_authentication",
        REVIEW_AUTHENTICATION_KEYS,
    )
    for name in (
        "base_review_report_digest", "clinical_assessment_digest", "custodian_assessment_digest",
        "opening_authorization_digest", "opening_receipt_digest",
    ):
        digest(authentication[name], f"heldout_confirmation.review_report.review_authentication.{name}")
    timestamp(authentication["authenticated_at"],
              "heldout_confirmation.review_report.review_authentication.authenticated_at")
    require(
        type(authentication["review_attestation_digests"]) is list
        and len(authentication["review_attestation_digests"]) == 4
        and authentication["review_attestation_digests"]
        == sorted(set(authentication["review_attestation_digests"])),
        "heldout_confirmation.review_report.review_authentication.review_attestation_digests",
        "must contain four unique sorted digests",
    )
    for index, value in enumerate(authentication["review_attestation_digests"]):
        digest(value, f"heldout_confirmation.review_report.review_authentication.review_attestation_digests[{index}]")
    literal(authentication["opening_authorization_digest"],
            "heldout_confirmation.review_report.review_authentication.opening_authorization_digest",
            report["opening_authorization_digest"])
    literal(authentication["opening_receipt_digest"],
            "heldout_confirmation.review_report.review_authentication.opening_receipt_digest",
            report["opening_receipt_digest"])
    literal(report["confirmation_purposes_ready"],
            "heldout_confirmation.review_report.confirmation_purposes_ready", True)
    literal(report["source_blockers"], "heldout_confirmation.review_report.source_blockers", [])
    for name in ("source_admission_authorized", "training_ready", "model_use_authorized",
                 "mmbu_public_content_used"):
        literal(report[name], f"heldout_confirmation.review_report.{name}", False)
    require(isinstance(store, RecordStore), "heldout_confirmation.admission_store",
            "must be a Phase 1 record store")
    source = admission.check_source(store, source_admission_digest,
                                    "heldout_confirmation.source_admission_digest")
    admission_receipt = decisions.check_decision_receipt(
        store, source["admission_decision_receipt_digest"],
        "heldout_confirmation.source_admission_decision_receipt",
    )
    admission_plan = store.get(
        admission_receipt["plan_digest"], "decision_plan",
        "heldout_confirmation.source_admission_plan",
    )
    require(report["record_digest"] in admission_plan["allowed_input_digests"],
            "heldout_confirmation.review_report.record_digest",
            "the source admission decision did not bind this exact review report")
    authorization = admission.check_purpose_authorization(
        store, purpose_authorization_digest,
        "heldout_confirmation.purpose_authorization_digest",
    )
    literal(source["source_id"], "heldout_confirmation.source.source_id", "busi-whu")
    literal(source["source_version"], "heldout_confirmation.source.source_version", "3")
    literal(source["status"], "heldout_confirmation.source.status", "approved")
    require("confirmation" in source["allowed_purposes"], "heldout_confirmation.source.allowed_purposes",
            "must allow confirmation")
    literal(authorization["source_digest"], "heldout_confirmation.authorization.source_digest",
            source_admission_digest)
    literal(authorization["purpose"], "heldout_confirmation.authorization.purpose", "confirmation")
    literal(authorization["decision"], "heldout_confirmation.authorization.decision", "allowed")
    constraints = report["duplicate_group_constraints"]
    require(type(constraints) is list, "heldout_confirmation.review_report.duplicate_group_constraints",
            "must be an array")
    for index, group in enumerate(constraints):
        require(type(group) is dict and type(group.get("patient_ids")) is list,
                f"heldout_confirmation.review_report.duplicate_group_constraints[{index}]",
                "must contain patient IDs")
        require(len(group["patient_ids"]) <= 1,
                f"heldout_confirmation.review_report.duplicate_group_constraints[{index}]",
                "cross-patient duplicate groups cannot enter independent-patient confirmation")
    return report, source, authorization


def build_confirmation_source_manifest(
    review_report: object, store: RecordStore, source_admission_digest: str,
    purpose_authorization_digest: str,
) -> dict:
    """Bridge authenticated review evidence into the existing confirmation population contract."""
    report, _source, _authorization = _validated_bridge_inputs(
        review_report, store, source_admission_digest, purpose_authorization_digest
    )
    eligible = closed(report["eligible_by_task"], "heldout_confirmation.review_report.eligible_by_task", (
        "global_classification", "grounded_classification", "localization", "context_prediction",
    ))["global_classification"]
    eligible = closed(eligible, "heldout_confirmation.review_report.global_classification", (
        "patient_count", "patient_ids", "patient_to_records", "record_count", "record_ids",
    ))
    patient_ids = _validate_patient_ids(
        eligible["patient_ids"], "heldout_confirmation.review_report.global_classification.patient_ids"
    )
    require(eligible["patient_count"] == len(patient_ids),
            "heldout_confirmation.review_report.global_classification.patient_count", "count mismatch")
    record_ids = eligible["record_ids"]
    require(type(record_ids) is list and record_ids == sorted(set(record_ids), key=lambda item: item.encode("utf-8")),
            "heldout_confirmation.review_report.global_classification.record_ids",
            "must be unique and sorted")
    require(eligible["record_count"] == len(record_ids),
            "heldout_confirmation.review_report.global_classification.record_count", "count mismatch")
    target_map = _validate_target_map(
        report["target_map"], record_ids, "heldout_confirmation.review_report.target_map"
    )
    literal(report["target_map_digest"], "heldout_confirmation.review_report.target_map_digest",
            canonical.value_digest(target_map))
    digest(report["global_task_manifest_digest"],
           "heldout_confirmation.review_report.global_task_manifest_digest")
    population = _population_binding(
        patient_ids, eligible["patient_to_records"],
        source_manifest_digest=source_admission_digest,
        exclusions_digest=canonical.value_digest({
            "excluded_record_ids": report["excluded_record_ids"],
            "unresolved_record_ids": report["unresolved_record_ids"],
            "duplicate_excluded_record_ids": report["duplicate_excluded_record_ids"],
        }),
        duplicate_disposition_digest=canonical.value_digest(report["duplicate_group_constraints"]),
        target_map=target_map,
        target_map_digest=report["target_map_digest"],
    )
    require(sorted(record_id for rows in population["patient_to_records"].values() for record_id in rows) == record_ids,
            "heldout_confirmation.review_report.global_classification.patient_to_records",
            "must own every eligible record exactly")
    return canonical.seal({
        "schema_id": "mmbu.confirmation.busi_whu_source_manifest", "schema_version": 1,
        "source_id": "busi-whu", "source_version": "3", "source_role": "confirmation",
        "confirmation_task": "global_classification", "patient_ids": patient_ids,
        "patient_count": len(patient_ids), "record_ids": record_ids, "record_count": len(record_ids),
        "patient_to_records": population["patient_to_records"],
        "exclusions_digest": population["exclusions_digest"],
        "duplicate_disposition_digest": population["duplicate_disposition_digest"],
        "review_validation_digest": report["record_digest"],
        "source_admission_digest": source_admission_digest,
        "purpose_authorization_digest": purpose_authorization_digest,
        "target_map": target_map, "target_map_digest": report["target_map_digest"],
        "global_task_manifest_digest": report["global_task_manifest_digest"],
        "training_allowed": False, "model_use_authorized": False,
        "mmbu_public_content_used": False,
    })


def validate_confirmation_source_manifest(
    value: object, review_report: object, store: RecordStore, source_admission_digest: str,
    purpose_authorization_digest: str,
) -> dict:
    manifest = closed(value, "heldout_confirmation.source_manifest", SOURCE_MANIFEST_KEYS)
    expected = build_confirmation_source_manifest(
        review_report, store, source_admission_digest, purpose_authorization_digest
    )
    require(manifest == expected, "heldout_confirmation.source_manifest",
            "differs from the authenticated review and admission evidence")
    return manifest


ARTIFACT_KEYS = (
    "created_at", "index_matrix", "index_matrix_digest", "patient_ids", "population_binding",
    "population_digest", "sign_matrix", "sign_matrix_digest", "construction_scope", "target_map_digest",
)
RESULT_ROW_KEYS = (
    "condition_id", "output_failed", "patient_id", "post_reload_context_raw_output",
    "post_reload_task_raw_output", "pre_reload_context_raw_output", "pre_reload_task_raw_output",
    "prompt_spec_digest", "record_id", "target_label",
)
CONFIRMATION_LOCK_KEYS = (
    "artifact_digest", "locked_at", "opening_receipt_digest", "population_digest", "record_digest",
    "target_map_digest",
)
CONDITIONS = ("base", "seed-20261025", "seed-20261026", "seed-20261027")
SEED_CONDITIONS = CONDITIONS[1:]


def _validate_patient_ids(value: object, path: str = "heldout_confirmation.patient_ids") -> list[str]:
    if type(value) is not list:
        fail(path, "must be an array")
    if len(value) < 60:
        fail(path, "must contain at least 60 independent patients")
    for index, patient_id in enumerate(value):
        text(patient_id, f"{path}[{index}]")
    expected = sorted(set(value), key=lambda item: item.encode("utf-8"))
    require(value == expected, path, "must be unique and sorted by ascending UTF-8 bytes")
    return value


PROMPT_SPEC_DIGEST = "c75d3bc7c0a46083d5636060edef29ced26b1d740118d36b0f6d1dc7bf782f87"


def _random_matrices(count: int) -> tuple[list[list[int]], list[list[int]]]:
    bootstrap = random.Random(20261025)
    signs = random.Random(20261026)
    return (
        [[bootstrap.randrange(count) for _ in range(count)] for _ in range(10000)],
        [[1 if signs.getrandbits(1) else -1 for _ in range(count)] for _ in range(10000)],
    )


def _population_binding(
    patient_ids: list[str],
    patient_to_records: object,
    *,
    source_manifest_digest: str,
    exclusions_digest: str,
    duplicate_disposition_digest: str,
    target_map: dict[str, str],
    target_map_digest: str,
) -> dict:
    digest(source_manifest_digest, "heldout_confirmation.population.source_manifest_digest")
    digest(exclusions_digest, "heldout_confirmation.population.exclusions_digest")
    digest(duplicate_disposition_digest, "heldout_confirmation.population.duplicate_disposition_digest")
    digest(target_map_digest, "heldout_confirmation.population.target_map_digest")
    require(type(patient_to_records) is dict and set(patient_to_records) == set(patient_ids),
            "heldout_confirmation.population.patient_to_records", "must name every locked patient exactly")
    normalized: dict[str, list[str]] = {}
    record_owner: dict[str, str] = {}
    for patient_id in patient_ids:
        records = patient_to_records[patient_id]
        require(type(records) is list and bool(records),
                f"heldout_confirmation.population.patient_to_records.{patient_id}", "must be nonempty")
        for index, record_id in enumerate(records):
            text(record_id, f"heldout_confirmation.population.patient_to_records.{patient_id}[{index}]")
        require(records == sorted(set(records), key=lambda item: item.encode("utf-8")),
                f"heldout_confirmation.population.patient_to_records.{patient_id}",
                "must be unique and sorted by UTF-8 bytes")
        for record_id in records:
            require(record_id not in record_owner,
                    f"heldout_confirmation.population.patient_to_records.{patient_id}",
                    f"record {record_id!r} is already assigned to patient {record_owner.get(record_id)!r}")
            record_owner[record_id] = patient_id
        normalized[patient_id] = list(records)
    all_records = sorted(record_owner, key=lambda item: item.encode("utf-8"))
    targets = _validate_target_map(target_map, all_records, "heldout_confirmation.population.target_map")
    literal(target_map_digest, "heldout_confirmation.population.target_map_digest",
            canonical.value_digest(targets))
    return {
        "duplicate_disposition_digest": duplicate_disposition_digest,
        "exclusions_digest": exclusions_digest,
        "patient_to_records": normalized,
        "source_manifest_digest": source_manifest_digest,
        "target_map": targets,
        "target_map_digest": target_map_digest,
    }


def build_confirmation_lock(
    artifacts: dict, *, locked_at: str, opening_receipt_digest: str
) -> dict:
    """Create the separate structural lock that binds the complete pre-output artifact."""
    closed(artifacts, "heldout_confirmation.artifacts", ARTIFACT_KEYS)
    timestamp(locked_at, "heldout_confirmation.lock.locked_at")
    digest(opening_receipt_digest, "heldout_confirmation.lock.opening_receipt_digest")
    return canonical.seal({
        "artifact_digest": canonical.value_digest(artifacts),
        "locked_at": locked_at,
        "opening_receipt_digest": opening_receipt_digest,
        "population_digest": artifacts["population_digest"],
        "target_map_digest": artifacts["target_map_digest"],
        "record_digest": "0" * 64,
    })


def _validate_confirmation_lock(
    value: object, artifacts: dict, *, first_output_at: str
) -> dict:
    lock = closed(value, "heldout_confirmation.lock", CONFIRMATION_LOCK_KEYS)
    digest(lock["artifact_digest"], "heldout_confirmation.lock.artifact_digest")
    digest(lock["opening_receipt_digest"], "heldout_confirmation.lock.opening_receipt_digest")
    digest(lock["population_digest"], "heldout_confirmation.lock.population_digest")
    digest(lock["record_digest"], "heldout_confirmation.lock.record_digest")
    literal(lock["record_digest"], "heldout_confirmation.lock.record_digest", canonical.record_digest(lock))
    literal(lock["artifact_digest"], "heldout_confirmation.lock.artifact_digest",
            canonical.value_digest(artifacts))
    literal(lock["population_digest"], "heldout_confirmation.lock.population_digest",
            artifacts["population_digest"])
    literal(lock["target_map_digest"], "heldout_confirmation.lock.target_map_digest",
            artifacts["target_map_digest"])
    created = timestamp(artifacts["created_at"], "heldout_confirmation.artifacts.created_at")
    locked = timestamp(lock["locked_at"], "heldout_confirmation.lock.locked_at")
    first = timestamp(first_output_at, "heldout_confirmation.first_output_at")
    require(created < locked < first, "heldout_confirmation.lock.locked_at",
            "must follow artifact creation and precede the first output")
    return lock


def _build_randomization_artifacts(
    patient_ids: list[str],
    *,
    patient_to_records: dict[str, list[str]],
    source_manifest_digest: str,
    exclusions_digest: str,
    duplicate_disposition_digest: str,
    target_map: dict[str, str],
    target_map_digest: str,
    construction_scope: str,
    created_at: str,
) -> dict:
    """Build the frozen patient bootstrap and sign matrices before outputs exist."""
    patient_ids = list(_validate_patient_ids(patient_ids))
    timestamp(created_at, "heldout_confirmation.artifacts.created_at")
    count = len(patient_ids)
    population = _population_binding(
        patient_ids, patient_to_records,
        source_manifest_digest=source_manifest_digest,
        exclusions_digest=exclusions_digest,
        duplicate_disposition_digest=duplicate_disposition_digest,
        target_map=target_map,
        target_map_digest=target_map_digest,
    )
    index_matrix, sign_matrix = _random_matrices(count)
    return {
        "created_at": created_at,
        "index_matrix": index_matrix,
        "index_matrix_digest": canonical.value_digest(index_matrix),
        "patient_ids": patient_ids,
        "population_binding": population,
        "population_digest": canonical.value_digest(population),
        "construction_scope": construction_scope,
        "target_map_digest": target_map_digest,
        "sign_matrix": sign_matrix,
        "sign_matrix_digest": canonical.value_digest(sign_matrix),
    }


def build_authenticated_randomization_artifacts(
    review_report: object, confirmation_source_manifest: object, store: RecordStore,
    source_admission_digest: str, confirmation_purpose_digest: str, created_at: str,
) -> dict:
    """Build real artifacts only by re-resolving the admitted review chain."""
    manifest = validate_confirmation_source_manifest(
        confirmation_source_manifest, review_report, store, source_admission_digest,
        confirmation_purpose_digest,
    )
    return _build_randomization_artifacts(
        manifest["patient_ids"], patient_to_records=manifest["patient_to_records"],
        source_manifest_digest=manifest["record_digest"],
        exclusions_digest=manifest["exclusions_digest"],
        duplicate_disposition_digest=manifest["duplicate_disposition_digest"],
        target_map=manifest["target_map"], target_map_digest=manifest["target_map_digest"],
        construction_scope="authenticated_real", created_at=created_at,
    )


def build_synthetic_randomization_artifacts(fixture: object, created_at: str) -> dict:
    """Build mechanics-only artifacts from an explicitly synthetic closed fixture."""
    row = closed(fixture, "heldout_confirmation.synthetic_artifact_fixture", (
        "biomedical_content_used", "mmbu_public_content_used", "patient_ids",
        "patient_to_records", "synthetic_only", "target_map",
    ))
    literal(row["synthetic_only"], "heldout_confirmation.synthetic_artifact_fixture.synthetic_only", True)
    literal(row["biomedical_content_used"],
            "heldout_confirmation.synthetic_artifact_fixture.biomedical_content_used", False)
    literal(row["mmbu_public_content_used"],
            "heldout_confirmation.synthetic_artifact_fixture.mmbu_public_content_used", False)
    target_digest = canonical.value_digest(row["target_map"])
    return _build_randomization_artifacts(
        row["patient_ids"], patient_to_records=row["patient_to_records"],
        source_manifest_digest=canonical.value_digest({"synthetic_only": True}),
        exclusions_digest=canonical.value_digest([]),
        duplicate_disposition_digest=canonical.value_digest([]),
        target_map=row["target_map"], target_map_digest=target_digest,
        construction_scope="synthetic_mechanics_only", created_at=created_at,
    )


def _validate_artifacts(value: object, *, first_output_at: str) -> dict:
    artifact = closed(value, "heldout_confirmation.artifacts", ARTIFACT_KEYS)
    patient_ids = _validate_patient_ids(artifact["patient_ids"], "heldout_confirmation.artifacts.patient_ids")
    created = timestamp(artifact["created_at"], "heldout_confirmation.artifacts.created_at")
    first_output = timestamp(first_output_at, "heldout_confirmation.first_output_at")
    require(created < first_output, "heldout_confirmation.artifacts.created_at",
            "must precede the first model output")
    supplied_population = closed(artifact["population_binding"],
                                 "heldout_confirmation.artifacts.population_binding", (
                                     "duplicate_disposition_digest", "exclusions_digest", "patient_to_records",
                                     "source_manifest_digest", "target_map", "target_map_digest",
                                 ))
    population = _population_binding(
        patient_ids, supplied_population["patient_to_records"],
        source_manifest_digest=supplied_population["source_manifest_digest"],
        exclusions_digest=supplied_population["exclusions_digest"],
        duplicate_disposition_digest=supplied_population["duplicate_disposition_digest"],
        target_map=supplied_population["target_map"],
        target_map_digest=supplied_population["target_map_digest"],
    )
    require(artifact["construction_scope"] in ("authenticated_real", "synthetic_mechanics_only"),
            "heldout_confirmation.artifacts.construction_scope", "is not a supported closed scope")
    literal(artifact["target_map_digest"], "heldout_confirmation.artifacts.target_map_digest",
            population["target_map_digest"])
    literal(artifact["population_digest"], "heldout_confirmation.artifacts.population_digest",
            canonical.value_digest(population))
    count = len(patient_ids)
    index_matrix = artifact["index_matrix"]
    sign_matrix = artifact["sign_matrix"]
    require(type(index_matrix) is list and len(index_matrix) == 10000,
            "heldout_confirmation.artifacts.index_matrix", "must contain exactly 10,000 draws")
    require(type(sign_matrix) is list and len(sign_matrix) == 10000,
            "heldout_confirmation.artifacts.sign_matrix", "must contain exactly 10,000 draws")
    for draw_index, draw in enumerate(index_matrix):
        require(type(draw) is list and len(draw) == count,
                f"heldout_confirmation.artifacts.index_matrix[{draw_index}]", "has the wrong patient count")
        require(all(type(position) is int and 0 <= position < count for position in draw),
                f"heldout_confirmation.artifacts.index_matrix[{draw_index}]", "contains an invalid position")
    for draw_index, draw in enumerate(sign_matrix):
        require(type(draw) is list and len(draw) == count,
                f"heldout_confirmation.artifacts.sign_matrix[{draw_index}]", "has the wrong patient count")
        require(all(type(sign) is int and sign in (-1, 1) for sign in draw),
                f"heldout_confirmation.artifacts.sign_matrix[{draw_index}]", "contains an invalid sign")
    literal(artifact["index_matrix_digest"], "heldout_confirmation.artifacts.index_matrix_digest",
            canonical.value_digest(index_matrix))
    literal(artifact["sign_matrix_digest"], "heldout_confirmation.artifacts.sign_matrix_digest",
            canonical.value_digest(sign_matrix))
    expected_indexes, expected_signs = _random_matrices(count)
    require(index_matrix == expected_indexes, "heldout_confirmation.artifacts.index_matrix",
            "does not match the frozen PRNG construction")
    require(sign_matrix == expected_signs, "heldout_confirmation.artifacts.sign_matrix",
            "does not match the frozen PRNG construction")
    return artifact


def _mean(values: list[Fraction], path: str) -> Fraction:
    require(bool(values), path, "must be nonempty")
    return sum(values, Fraction(0)) / len(values)


def _validate_result_row(value: object, index: int) -> dict:
    path = f"heldout_confirmation.rows[{index}]"
    row = closed(value, path, RESULT_ROW_KEYS)
    literal(row["condition_id"], f"{path}.condition_id", row["condition_id"])
    require(type(row["condition_id"]) is str and row["condition_id"] in CONDITIONS,
            f"{path}.condition_id", "must be one frozen condition")
    text(row["patient_id"], f"{path}.patient_id")
    text(row["record_id"], f"{path}.record_id")
    require(type(row["target_label"]) is str and row["target_label"] in ("benign", "malignant"),
            f"{path}.target_label", "must be benign or malignant")
    literal(row["prompt_spec_digest"], f"{path}.prompt_spec_digest", PROMPT_SPEC_DIGEST)
    failed = boolean(row["output_failed"], f"{path}.output_failed")
    if failed:
        for key in ("pre_reload_task_raw_output", "pre_reload_context_raw_output",
                    "post_reload_task_raw_output", "post_reload_context_raw_output"):
            literal(row[key], f"{path}.{key}", None)
        task = Fraction(0)
        grades = {"body_part": 0, "medical_domain": 0, "modality": 0}
        structurally_valid = False
    else:
        task_raw = text(row["pre_reload_task_raw_output"],
                        f"{path}.pre_reload_task_raw_output", allow_empty=True)
        context_raw = text(row["pre_reload_context_raw_output"],
                           f"{path}.pre_reload_context_raw_output", allow_empty=True)
        post_task = text(row["post_reload_task_raw_output"],
                         f"{path}.post_reload_task_raw_output", allow_empty=True)
        post_context = text(row["post_reload_context_raw_output"],
                            f"{path}.post_reload_context_raw_output", allow_empty=True)
        require(task_raw.encode("utf-8") == post_task.encode("utf-8") and
                context_raw.encode("utf-8") == post_context.encode("utf-8"), path,
                "fresh-process task and context raw bytes must match exactly")
        parsed = task_raw.strip().casefold()
        task = Fraction(int(parsed in ("benign", "malignant") and parsed == row["target_label"]))
        context_keys = ("body_part", "medical_domain", "modality")
        target = {"body_part": "breast", "medical_domain": "breast imaging", "modality": "ultrasound"}
        try:
            parsed_context = canonical.loads(context_raw.encode("utf-8"))
        except canonical.CanonicalJSONError:
            parsed_context = None
        structurally_valid = (
            type(parsed_context) is dict
            and list(parsed_context) == list(context_keys)
            and all(type(parsed_context[key]) is str for key in context_keys)
            and context_raw.startswith("{")
            and context_raw.endswith("}")
        )
        grades = {
            key: int(structurally_valid and parsed_context[key] == target[key])
            for key in context_keys
        }
    derived = dict(row)
    derived["_task_grade"] = task
    derived["_context_field_grades"] = grades
    derived["_context_valid"] = structurally_valid
    return derived


def analyze_patient_results(
    rows: list[dict], artifacts: dict, *, confirmation_lock: dict, first_output_at: str
) -> dict:
    """Compute the frozen exact paired patient analysis from complete condition rows."""
    artifact = _validate_artifacts(artifacts, first_output_at=first_output_at)
    _validate_confirmation_lock(confirmation_lock, artifact, first_output_at=first_output_at)
    patient_ids = artifact["patient_ids"]
    patient_set = set(patient_ids)
    if type(rows) is not list:
        fail("heldout_confirmation.rows", "must be an array")
    by_condition: dict[str, dict[str, dict[str, dict]]] = {condition: {} for condition in CONDITIONS}
    output_failures = 0
    for index, raw in enumerate(rows):
        row = _validate_result_row(raw, index)
        require(row["patient_id"] in patient_set, f"heldout_confirmation.rows[{index}].patient_id",
                "is not in the locked population")
        condition_records = by_condition[row["condition_id"]].setdefault(row["patient_id"], {})
        require(row["record_id"] not in condition_records, f"heldout_confirmation.rows[{index}].record_id",
                "duplicates a condition record")
        literal(row["target_label"], f"heldout_confirmation.rows[{index}].target_label",
                artifact["population_binding"]["target_map"].get(row["record_id"]))
        condition_records[row["record_id"]] = row
        output_failures += int(row["output_failed"])

    reference: dict[str, set[str]] = {}
    locked_records = artifact["population_binding"]["patient_to_records"]
    for patient_id in patient_ids:
        reference[patient_id] = set(by_condition["base"].get(patient_id, {}))
        require(reference[patient_id] == set(locked_records[patient_id]),
                f"heldout_confirmation.population.{patient_id}",
                "base records do not match the locked patient-to-record map")
        for condition in SEED_CONDITIONS:
            require(set(by_condition[condition].get(patient_id, {})) == reference[patient_id],
                    f"heldout_confirmation.population.{patient_id}.{condition}",
                    "must contain exactly the same record IDs as base")
            for record_id in reference[patient_id]:
                base_label = by_condition["base"][patient_id][record_id]["target_label"]
                literal(by_condition[condition][patient_id][record_id]["target_label"],
                        f"heldout_confirmation.population.{patient_id}.{condition}.{record_id}.target_label",
                        base_label)

    task_patient: dict[str, dict[str, Fraction]] = {condition: {} for condition in CONDITIONS}
    context_patient: dict[str, dict[str, Fraction]] = {condition: {} for condition in CONDITIONS}
    context_valid_patient: dict[str, dict[str, Fraction]] = {condition: {} for condition in CONDITIONS}
    context_field_patient: dict[str, dict[str, dict[str, Fraction]]] = {
        condition: {field: {} for field in ("body_part", "medical_domain", "modality")}
        for condition in CONDITIONS
    }
    for condition in CONDITIONS:
        for patient_id in patient_ids:
            patient_rows = list(by_condition[condition][patient_id].values())
            task_patient[condition][patient_id] = _mean(
                [row["_task_grade"] for row in patient_rows], "task_patient"
            )
            context_patient[condition][patient_id] = _mean([
                Fraction(sum(row["_context_field_grades"].values()), 3) for row in patient_rows
            ], "context_patient")
            context_valid_patient[condition][patient_id] = _mean([
                Fraction(int(row["_context_valid"])) for row in patient_rows
            ], "context_valid_patient")
            for field in ("body_part", "medical_domain", "modality"):
                context_field_patient[condition][field][patient_id] = _mean([
                    Fraction(row["_context_field_grades"][field]) for row in patient_rows
                ], f"context_field_patient.{field}")

    seed_deltas = {
        condition: _mean([
            task_patient[condition][patient_id] - task_patient["base"][patient_id]
            for patient_id in patient_ids
        ], f"seed_delta.{condition}")
        for condition in SEED_CONDITIONS
    }
    patient_deltas = [
        _mean([task_patient[condition][patient_id] - task_patient["base"][patient_id]
               for condition in SEED_CONDITIONS], f"patient_delta.{patient_id}")
        for patient_id in patient_ids
    ]
    point = _mean(patient_deltas, "point_delta")
    draw_values = [
        _mean([patient_deltas[position] for position in draw], "bootstrap_draw")
        for draw in artifact["index_matrix"]
    ]
    lower = sorted(enumerate(draw_values), key=lambda item: (item[1], item[0]))[999][1]
    null_values = [
        _mean([patient_deltas[index] * sign for index, sign in enumerate(signs)], "sign_draw")
        for signs in artifact["sign_matrix"]
    ]
    sign_p = Fraction(1 + sum(value >= point for value in null_values), 10001)
    condition_task = {
        condition: _mean(list(task_patient[condition].values()), f"condition_task.{condition}")
        for condition in CONDITIONS
    }
    condition_context = {
        condition: _mean(list(context_patient[condition].values()), f"condition_context.{condition}")
        for condition in CONDITIONS
    }
    condition_q = {
        condition: Fraction(4, 5) * condition_task[condition] + Fraction(1, 5) * condition_context[condition]
        for condition in CONDITIONS
    }
    class_diagnostics: dict[str, dict[str, dict]] = {}
    for condition in CONDITIONS:
        class_diagnostics[condition] = {}
        for label in ("benign", "malignant"):
            patient_scores: list[Fraction] = []
            image_count = 0
            for patient_id in patient_ids:
                matching = [row for row in by_condition[condition][patient_id].values()
                            if row["target_label"] == label]
                if matching:
                    image_count += len(matching)
                    patient_scores.append(_mean(
                        [row["_task_grade"] for row in matching],
                        f"class.{condition}.{label}.{patient_id}",
                    ))
            class_diagnostics[condition][label] = {
                "image_count": image_count,
                "patient_count": len(patient_scores),
                "score": rational.to_wire(_mean(patient_scores, f"class.{condition}.{label}")),
            }
    secondary_conditions: dict[str, dict] = {}
    for condition in CONDITIONS:
        failure_count = sum(
            int(row["output_failed"])
            for patients in by_condition[condition].values()
            for row in patients.values()
        )
        record_count = sum(len(records) for records in by_condition[condition].values())
        class_balanced = _mean([
            rational.from_wire(class_diagnostics[condition][label]["score"])
            for label in ("benign", "malignant")
        ], f"class_balanced.{condition}")
        secondary_conditions[condition] = {
            "class_balanced_accuracy": rational.to_wire(class_balanced),
            "context": rational.to_wire(condition_context[condition]),
            "context_fields": {
                field: rational.to_wire(_mean(
                    list(context_field_patient[condition][field].values()),
                    f"context_field.{condition}.{field}",
                ))
                for field in ("body_part", "medical_domain", "modality")
            },
            "context_validity": rational.to_wire(_mean(
                list(context_valid_patient[condition].values()), f"context_validity.{condition}"
            )),
            "output_failure_count": failure_count,
            "output_failure_rate": rational.to_wire(Fraction(failure_count, record_count)),
            "q": rational.to_wire(condition_q[condition]),
            "task": rational.to_wire(condition_task[condition]),
        }
    secondary_seed_mean = {
        key: rational.to_wire(_mean([
            rational.from_wire(secondary_conditions[condition][key]) for condition in SEED_CONDITIONS
        ], f"secondary_seed_mean.{key}"))
        for key in ("class_balanced_accuracy", "context", "context_validity", "output_failure_rate", "q", "task")
    }
    secondary_seed_mean["context_fields"] = {
        field: rational.to_wire(_mean([
            rational.from_wire(secondary_conditions[condition]["context_fields"][field])
            for condition in SEED_CONDITIONS
        ], f"secondary_seed_mean.context_fields.{field}"))
        for field in ("body_part", "medical_domain", "modality")
    }
    return {
        "base": {
            "context": rational.to_wire(condition_context["base"]),
            "q": rational.to_wire(condition_q["base"]),
            "task": rational.to_wire(condition_task["base"]),
        },
        "class_diagnostics": class_diagnostics,
        "lower_bound": rational.to_wire(lower),
        "output_failure_count": output_failures,
        "patient_count": len(patient_ids),
        "point_delta": rational.to_wire(point),
        "reload_mismatch_count": output_failures,
        "secondary": {"conditions": secondary_conditions, "seed_mean": secondary_seed_mean},
        "seed_deltas": {key: rational.to_wire(value) for key, value in seed_deltas.items()},
        "seed_mean": {
            "context": rational.to_wire(_mean([condition_context[key] for key in SEED_CONDITIONS], "seed_context")),
            "q": rational.to_wire(_mean([condition_q[key] for key in SEED_CONDITIONS], "seed_q")),
            "task": rational.to_wire(_mean([condition_task[key] for key in SEED_CONDITIONS], "seed_task")),
        },
        "sign_randomization_p": rational.to_wire(sign_p),
    }


ANALYSIS_KEYS = (
    "base", "class_diagnostics", "lower_bound", "output_failure_count", "patient_count", "point_delta",
    "reload_mismatch_count", "secondary", "seed_deltas", "seed_mean", "sign_randomization_p",
)
EXECUTION_KEYS = (
    "adapted_attempts", "base_attempts", "identity_drift", "mmbu_public_content_used", "source_id",
    "source_version", "source_role",
)
READINESS_KEYS = (
    "attempts_started", "checkpoint_lineages", "chronology", "gate_records", "mmbu_public_content_used",
    "source_id", "source_version", "source_role",
)
SYNTHETIC_FIXTURE_KEYS = (
    "biomedical_content_used", "expected_status", "fixture_id", "lower_bound", "mmbu_public_content_used",
    "patient_count", "point_delta", "seed_deltas", "synthetic_only",
)
GATE_ORDER = (
    "training-source-admission", "successor-runtime", "checkpoint-retraining-lineage",
    "confirmation-source-acquisition", "rights-review", "protected-inventory", "qa-lock-and-review",
    "duplicate-review", "confirmation-purpose-authorization", "eligible-population-lock",
    "hermetic-decision-receipt", "opening-and-execution-lock",
)


def confirmation_decision(analysis: object, execution: object) -> dict:
    """Apply the one non-rescuable primary confirmation decision in frozen order."""
    result = closed(analysis, "heldout_confirmation.analysis", ANALYSIS_KEYS)
    run = closed(execution, "heldout_confirmation.execution", EXECUTION_KEYS)
    blocked: list[str] = []
    if (run["source_id"], run["source_version"], run["source_role"]) != (
        "busi-whu", "3", "confirmation"
    ):
        blocked.append("source_identity_or_role")
    if type(run["mmbu_public_content_used"]) is not bool or run["mmbu_public_content_used"]:
        blocked.append("mmbu_public_content_boundary")
    if blocked:
        return {"reasons": blocked, "status": "blocked"}

    patient_count = integer(result["patient_count"], "heldout_confirmation.analysis.patient_count", minimum=0)
    if patient_count < 60:
        return {"reasons": ["minimum_independent_patients"], "status": "underpowered"}

    reasons: list[str] = []
    if type(run["base_attempts"]) is not int or run["base_attempts"] != 1:
        reasons.append("base_attempt_count")
    attempts = closed(run["adapted_attempts"], "heldout_confirmation.execution.adapted_attempts", SEED_CONDITIONS)
    for condition in SEED_CONDITIONS:
        if type(attempts[condition]) is not int or attempts[condition] != 1:
            reasons.append(f"adapted_attempt_count:{condition}")
    if type(run["identity_drift"]) is not bool or run["identity_drift"]:
        reasons.append("identity_drift")
    if integer(result["reload_mismatch_count"],
               "heldout_confirmation.analysis.reload_mismatch_count", minimum=0) != 0:
        reasons.append("reload_output_mismatch")

    margin = Fraction(1, 20)
    seed_deltas = closed(result["seed_deltas"], "heldout_confirmation.analysis.seed_deltas", SEED_CONDITIONS)
    for condition in SEED_CONDITIONS:
        if rational.from_wire(seed_deltas[condition], f"heldout_confirmation.analysis.seed_deltas.{condition}") <= 0:
            reasons.append(f"nonpositive_seed_delta:{condition}")
    if rational.from_wire(result["point_delta"], "heldout_confirmation.analysis.point_delta") <= margin:
        reasons.append("point_delta_not_above_margin")
    if rational.from_wire(result["lower_bound"], "heldout_confirmation.analysis.lower_bound") <= margin:
        reasons.append("lower_bound_not_above_margin")

    # Validate descriptive exact values but never let them rescue or block the primary claim.
    rational.from_wire(result["sign_randomization_p"], "heldout_confirmation.analysis.sign_randomization_p")
    for name in ("base", "seed_mean"):
        scores = closed(result[name], f"heldout_confirmation.analysis.{name}", ("context", "q", "task"))
        for key in ("context", "q", "task"):
            rational.from_wire(scores[key], f"heldout_confirmation.analysis.{name}.{key}")
    integer(result["output_failure_count"], "heldout_confirmation.analysis.output_failure_count", minimum=0)
    require(type(result["class_diagnostics"]) is dict, "heldout_confirmation.analysis.class_diagnostics",
            "must be an object")
    require(type(result["secondary"]) is dict, "heldout_confirmation.analysis.secondary",
            "must be an object")
    return {"reasons": reasons, "status": "confirmation_failed" if reasons else "confirmation_passed"}


def readiness_status(value: object) -> dict:
    """Validate reference-only pre-execution readiness without opening referenced artifacts."""
    record = closed(value, "heldout_confirmation.readiness", READINESS_KEYS)
    gates = closed(record["gate_records"], "heldout_confirmation.readiness.gate_records", GATE_ORDER)
    for gate in GATE_ORDER:
        reference = gates[gate]
        if reference is None:
            return {"missing": gate, "status": "blocked"}
        digest(reference, f"heldout_confirmation.readiness.gate_records.{gate}")

    literal(record["source_id"], "heldout_confirmation.readiness.source_id", "busi-whu")
    literal(record["source_version"], "heldout_confirmation.readiness.source_version", "3")
    literal(record["source_role"], "heldout_confirmation.readiness.source_role", "confirmation")
    literal(record["mmbu_public_content_used"],
            "heldout_confirmation.readiness.mmbu_public_content_used", False)

    lineages = record["checkpoint_lineages"]
    require(type(lineages) is list and len(lineages) == 3,
            "heldout_confirmation.readiness.checkpoint_lineages", "must contain exactly three checkpoints")
    expected_seeds = (20261025, 20261026, 20261027)
    for index, (lineage, seed) in enumerate(zip(lineages, expected_seeds)):
        validated = validate_checkpoint_lineage(
            lineage, f"heldout_confirmation.readiness.checkpoint_lineages[{index}]"
        )
        literal(validated["training_seed"],
                f"heldout_confirmation.readiness.checkpoint_lineages[{index}].training_seed", seed)

    attempts = closed(record["attempts_started"], "heldout_confirmation.readiness.attempts_started", CONDITIONS)
    for condition in CONDITIONS:
        literal(attempts[condition], f"heldout_confirmation.readiness.attempts_started.{condition}", 0)

    chronology = closed(record["chronology"], "heldout_confirmation.readiness.chronology", (
        "confirmation_lock_at", "first_output_at", "inventory_closed_at", "qa_opened_at", "qa_plan_frozen_at",
    ))
    inventory = timestamp(chronology["inventory_closed_at"],
                          "heldout_confirmation.readiness.chronology.inventory_closed_at")
    qa_plan = timestamp(chronology["qa_plan_frozen_at"],
                        "heldout_confirmation.readiness.chronology.qa_plan_frozen_at")
    qa_opened = timestamp(chronology["qa_opened_at"],
                          "heldout_confirmation.readiness.chronology.qa_opened_at")
    lock = timestamp(chronology["confirmation_lock_at"],
                     "heldout_confirmation.readiness.chronology.confirmation_lock_at")
    require(inventory < qa_plan < qa_opened < lock, "heldout_confirmation.readiness.chronology",
            "must satisfy inventory close < QA plan freeze < QA opening < confirmation lock")
    literal(chronology["first_output_at"], "heldout_confirmation.readiness.chronology.first_output_at", None)
    return {"missing": "external-record-validation", "status": "blocked"}


def validate_synthetic_fixture(value: object) -> dict:
    """Run a closed decision vector that can never count as data or readiness evidence."""
    fixture = closed(value, "heldout_confirmation.synthetic_fixture", SYNTHETIC_FIXTURE_KEYS)
    text(fixture["fixture_id"], "heldout_confirmation.synthetic_fixture.fixture_id")
    literal(fixture["synthetic_only"], "heldout_confirmation.synthetic_fixture.synthetic_only", True)
    literal(fixture["biomedical_content_used"],
            "heldout_confirmation.synthetic_fixture.biomedical_content_used", False)
    literal(fixture["mmbu_public_content_used"],
            "heldout_confirmation.synthetic_fixture.mmbu_public_content_used", False)
    require(fixture["expected_status"] in ("confirmation_passed", "confirmation_failed", "underpowered"),
            "heldout_confirmation.synthetic_fixture.expected_status", "must be a synthetic decision status")
    patient_count = integer(fixture["patient_count"],
                            "heldout_confirmation.synthetic_fixture.patient_count", minimum=0)
    seed_deltas = closed(fixture["seed_deltas"],
                         "heldout_confirmation.synthetic_fixture.seed_deltas", SEED_CONDITIONS)
    for condition in SEED_CONDITIONS:
        rational.from_wire(seed_deltas[condition],
                           f"heldout_confirmation.synthetic_fixture.seed_deltas.{condition}")
    rational.from_wire(fixture["point_delta"], "heldout_confirmation.synthetic_fixture.point_delta")
    rational.from_wire(fixture["lower_bound"], "heldout_confirmation.synthetic_fixture.lower_bound")
    analysis = {
        "base": {"context": rational.to_wire(0), "q": rational.to_wire(0), "task": rational.to_wire(0)},
        "class_diagnostics": {},
        "lower_bound": fixture["lower_bound"],
        "output_failure_count": 0,
        "patient_count": patient_count,
        "point_delta": fixture["point_delta"],
        "reload_mismatch_count": 0,
        "secondary": {"conditions": {}, "seed_mean": {}},
        "seed_deltas": seed_deltas,
        "seed_mean": {"context": rational.to_wire(0), "q": rational.to_wire(0), "task": rational.to_wire(0)},
        "sign_randomization_p": rational.to_wire(1),
    }
    execution = {
        "adapted_attempts": {condition: 1 for condition in SEED_CONDITIONS},
        "base_attempts": 1,
        "identity_drift": False,
        "mmbu_public_content_used": False,
        "source_id": "busi-whu",
        "source_version": "3",
        "source_role": "confirmation",
    }
    decision = confirmation_decision(analysis, execution)
    literal(decision["status"], "heldout_confirmation.synthetic_fixture.expected_status",
            fixture["expected_status"])
    return {
        "decision": decision,
        "evidence_scope": "synthetic_mechanics_only",
        "promotion_eligible": False,
        "readiness_evidence": False,
        "status": decision["status"],
    }


__all__ = [
    "SPEC_DIGEST", "analyze_patient_results", "build_confirmation_lock",
    "build_authenticated_randomization_artifacts", "build_confirmation_source_manifest",
    "build_synthetic_randomization_artifacts", "confirmation_decision",
    "load_spec", "readiness_status", "validate_checkpoint_lineage",
    "validate_confirmation_source_manifest", "validate_spec", "validate_synthetic_fixture",
]

