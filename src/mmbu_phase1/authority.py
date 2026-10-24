"""Bootstrap and validate the three mutable Phase 1 execution-state authorities.

``python3 -m mmbu_phase1.authority bootstrap [--root DIR]`` is the one tested
command that creates ``config/phase1/current-status.json`` plus generation-zero
authorization and opening-receipt registries.  It never overwrites existing
authority, records its actual UTC creation time, and derives every ID and
digest through the canonical kernel.  ``verify`` re-validates the files.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys

from mmbu_phase1 import canonical, fields as f, paths, registries, status
from mmbu_phase1.store import RecordStore
from mmbu_phase1.contract_manifest import (
    EXPECTED_CONTRACT_REVISION,
    EXPECTED_MANIFEST_SHA256,
    verify_contract_manifest,
)

STATUS_PATH = "config/phase1/current-status.json"
AUTHORIZATION_REGISTRY_PATH = "config/phase1/authorization-registry.json"
OPENING_RECEIPT_REGISTRY_PATH = "config/phase1/opening-receipt-registry.json"
AUTHORITY_PATHS = (STATUS_PATH, AUTHORIZATION_REGISTRY_PATH, OPENING_RECEIPT_REGISTRY_PATH)
MANIFEST_PATH = "docs/phase1/contract-manifest.json"

EXPECTED_OFFICIAL_SOURCE_HASHES = {
    "MMBU_challenge_update.pdf": "68fb4c2685d3d3b501da6f92f0906f970d851b596e98fddede26fb6e2b6e4ba0",
    "mmbu-challenge-official-rules.pdf": "30fb3241bd331eeaf0602b4ec24faf66b50f97c5d430cf814fdda80d62b80c8e",
}
RUNTIME_EVIDENCE_REPOSITORY_PATHS = {
    "predecessor": "outputs/status-authority-reconciliation/predecessor-current-status.json",
    "b1": "outputs/B1-native-attempt-85434.json",
    "b2_projector": "outputs/b2-projector-preflight/manifest.json",
    "b2_projector_failed_terminal": "outputs/b2-projector-preflight/attempt-1/terminal-run.json",
    "b2_projector_native": "outputs/b2-projector-preflight/attempt-2/native-preflight.json",
    "b2_projector_reload": "outputs/b2-projector-preflight/attempt-2/offline-reload.json",
    "b2_projector_terminal": "outputs/b2-projector-preflight/attempt-2/terminal-run.json",
    "b2_projector_adapter_config": "outputs/b2-projector-preflight/attempt-2/adapter/adapter_config.json",
    "b2_dual": "outputs/b2-dual-objective-preflight/manifest.json",
    "b2_dual_failed_terminal_1": "outputs/b2-dual-objective-preflight/attempt-1/terminal-run.json",
    "b2_dual_failed_measurement_2": "outputs/b2-dual-objective-preflight/attempt-2/prevalidation-measurement.json",
    "b2_dual_failed_terminal_2": "outputs/b2-dual-objective-preflight/attempt-2/terminal-run.json",
    "b2_dual_native": "outputs/b2-dual-objective-preflight/attempt-3/native-dual-objective.json",
    "b2_dual_measurement": "outputs/b2-dual-objective-preflight/attempt-3/prevalidation-measurement.json",
    "b2_dual_terminal": "outputs/b2-dual-objective-preflight/attempt-3/terminal-run.json",
}
RUNTIME_EVIDENCE_SHA256 = {
    "predecessor": "0d1a94fe20eb20fa6fa713982e7eacca4646b9218f976b2c840693df72cbfc01",
    "b1": "fbb12b04abae2bbacd6830b0727e5dcf393b52bd35a8196eba9859dca4da1990",
    "b2_projector": "9ec4b393f20fc5806a0eecc0844323cfac811c960cb8ad3c542fb98cf102bfce",
    "b2_projector_failed_terminal": "9832b1448e81a7844fe448f8a9c2b3d96a0de376e09137db4d22564670798f46",
    "b2_projector_native": "fba43cb6c0956c2688a9d3ea01c4a67baff3fa73d40e559da036582dcfef30d8",
    "b2_projector_reload": "38c8bb26b662c3d3ba24eee656b65bb69745e69e183f376029e8a54d5c65109f",
    "b2_projector_terminal": "8b0b4a759936b199da769977c5cfaee81ccb877eabe04563c4e4d35f99c6dbb1",
    "b2_projector_adapter_config": "f7df1b5c980b8ed5e5f6301a7a45ec2edabb43737dfc7320eda72c67791f772d",
    "b2_dual": "b96ac373db3d3ba64936444b1254e2aa86305ba46dd4919579e389d12a0eb0e0",
    "b2_dual_failed_terminal_1": "5833b5b614c9994a59a331f7bd23efa75781109d3a3492c0354b0a97502f267f",
    "b2_dual_failed_measurement_2": "6a5e96e15276c82105d4d9b46c47d3e54a751be56a11a7617657ad7df03ac849",
    "b2_dual_failed_terminal_2": "bb74c95337fec9eb7c684fa4b1e9f8c1954bb28ce586dd3131f096fba21ba184",
    "b2_dual_native": "369799a3b8135a22942612bb559d77098636bd71ea6f5bd4eeb1390d409b4b45",
    "b2_dual_measurement": "0b24bd53a78d8d4defe6c40f5a0bde88f07f5327f0f41f078f786f7d36ae07a2",
    "b2_dual_terminal": "fbbd7b9cac51ec844460957ae7ab35ae2ede31ded86ceaaafa2b912e032d6e3c",
}
RUNTIME_EVIDENCE_BUNDLE_PATHS = {
    key: "authority/status-evidence/" + key.replace("_", "-") + ".json"
    for key in RUNTIME_EVIDENCE_REPOSITORY_PATHS
}
RUNTIME_FACTS = {
    "runtime.b1_native_admission": {
        "value": "synthetic_engineering_only",
        "unit": "admission_scope",
        "evidence": "b1",
        "limitation": "Runtime and packaging feasibility only; no biomedical validity or competition performance.",
    },
    "runtime.b2_projector_preflight": {
        "value": "synthetic_engineering_only",
        "unit": "admission_scope",
        "evidence": "b2_projector",
        "limitation": "Projector-plus-language-LoRA mechanism feasibility only; no biomedical effect evidence.",
    },
    "runtime.b2_dual_objective_preflight": {
        "value": "singleton_microbatch_reference_only",
        "unit": "admission_scope",
        "evidence": "b2_dual",
        "limitation": "One synthetic singleton-accumulation step only; no biomedical or competition result.",
    },
    "runtime.b2_heterogeneous_batch_equivalence": {
        "value": False,
        "unit": "passed",
        "evidence": "b2_dual",
        "limitation": "Two prospective heterogeneous concatenated-batch attempts failed; larger-batch equivalence is not established.",
    },
}
PREDECESSOR_FACT = {
    "fact_id": "authority.current_status_predecessor",
    "status": "measured",
    "unit": "record_digest",
    "evidence": "predecessor",
    "limitation": "The transport file contains the exact prior canonical bytes plus one terminal LF; this grants no execution or scientific authority.",
}
PREDECESSOR_RAW_SHA256 = "f564ac0fb931dcfef0c83063f62fb2f1aefd359a8f46e24b5a14fa23765006f9"
EXPECTED_CURRENT_STATUS_DIGEST = "cc162ece6394cdabe18ee889e36c181145dc34dd80da712e2340c5ce91208539"

# Bootstrap facts: everything not measured stays explicit and unclaimed.
BOOTSTRAP_FACTS = (
    ("account.gpu_allocation", "unknown",
     "No GPU was requested, allocated, or measured; Phase 1A is CPU-only and public GPU specifications cannot "
     "support an allocation fact."),
    ("account.mocs_account", "unknown",
     "No MOCS account, credential, or account receipt has been captured or verified."),
    ("account.mocs_allocation", "unknown",
     "No MOCS allocation or scheduler receipt exists; a public cluster specification cannot support this fact."),
    ("data.real_source_admission", "blocked_external",
     "No real biomedical source has acquisition authority, rights, grouping, QA, custody, or purpose "
     "authorization; the required human rights and review authority is external to Phase 1A."),
    ("runtime.b1_native_admission", "unknown",
     "B1 weights and the D1 runtime were not downloaded, installed, loaded, or executed; the B1 native "
     "admission gate in B1_RUNTIME_GATE.md is unexecuted."),
)
RECONCILED_GUARD_FACTS = {
    "account.gpu_allocation": "No account-wide GPU entitlement or future allocation receipt exists; bounded job-level A100 receipts do not establish it.",
    "account.mocs_account": "Completed scheduler jobs establish bounded execution, not VPN/Duo/SSH authentication or durable account entitlement.",
    "account.mocs_allocation": "Per-job scheduler receipts do not establish durable project allocation, quota, storage, or future capacity.",
    "data.real_source_admission": "No real biomedical source has acquisition authority, rights, grouping, QA, custody, or purpose authorization; the required human rights and review authority is external to Phase 1A.",
}


@dataclass(frozen=True)
class ContractPins:
    revision: str
    manifest_sha256: str
    official_source_hashes: dict


def contract_pins(root: Path) -> ContractPins:
    """Verify the exact nine-member contract, then return its pins."""
    root = Path(root)
    errors = verify_contract_manifest(root)
    if errors:
        f.fail("contract", "contract integrity failed: " + "; ".join(errors))
    raw = paths.member_bytes(root, MANIFEST_PATH)
    if canonical.raw_digest(raw) != EXPECTED_MANIFEST_SHA256:
        f.fail("contract", "contract manifest changed after verification")
    manifest = canonical.loads(raw)
    return ContractPins(EXPECTED_CONTRACT_REVISION, EXPECTED_MANIFEST_SHA256, dict(manifest["official_source_hashes"]))


def derived_id(schema_name: str, generation: int, created_at: str) -> str:
    seed = {"created_at": created_at, "generation": generation, "schema_id": f.SCHEMA_PREFIX + schema_name}
    return f"{schema_name}-g{generation}-{canonical.value_digest(seed)[:32]}"


def build_authority(pins: ContractPins, now: str) -> dict[str, dict]:
    f.timestamp(now, "now")
    current = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "current_status",
        "schema_version": 1,
        "contract_revision": pins.revision,
        "contract_manifest_digest": pins.manifest_sha256,
        "official_source_hashes": dict(pins.official_source_hashes),
        "phase": "design_only",
        "facts": [
            {"fact_id": fact_id, "status": state, "value": None, "unit": None, "evidence_digests": [], "limitation": note}
            for fact_id, state, note in BOOTSTRAP_FACTS
        ],
        "updated_at": now,
    })
    authorization = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "authorization_registry",
        "schema_version": 1,
        "registry_id": derived_id("authorization_registry", 0, now),
        "generation": 0,
        "supersedes_registry_digest": None,
        "acquisition_authorization_digests": [],
        "source_record_digests": [],
        "purpose_authorization_digests": [],
        "acquisition_heads": {},
        "source_heads": {},
        "authorization_heads": {},
        "revoked_digests": [],
        "as_of": now,
    })
    opening = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "opening_receipt_registry",
        "schema_version": 1,
        "registry_id": derived_id("opening_receipt_registry", 0, now),
        "generation": 0,
        "supersedes_registry_digest": None,
        "heads": [],
        "created_at": now,
    })
    return {STATUS_PATH: current, AUTHORIZATION_REGISTRY_PATH: authorization, OPENING_RECEIPT_REGISTRY_PATH: opening}


def validate_authority_records(records: dict[str, dict], pins: ContractPins) -> None:
    status.validate_current_status(
        records[STATUS_PATH],
        contract_revision=pins.revision,
        contract_manifest_digest=pins.manifest_sha256,
        official_source_hashes=pins.official_source_hashes,
        path=STATUS_PATH,
    )
    registries.validate_authorization_registry(records[AUTHORIZATION_REGISTRY_PATH], AUTHORIZATION_REGISTRY_PATH)
    registries.validate_opening_receipt_registry(records[OPENING_RECEIPT_REGISTRY_PATH], OPENING_RECEIPT_REGISTRY_PATH)


def runtime_status_evidence_bytes(root: Path, record: dict) -> dict[str, bytes]:
    """Read the exact repository artifacts needed by a reconciled native-runtime status."""
    facts = {row.get("fact_id"): row for row in record.get("facts", []) if type(row) is dict}
    if PREDECESSOR_FACT["fact_id"] not in facts:
        return {}
    result = {}
    for key, relative in RUNTIME_EVIDENCE_REPOSITORY_PATHS.items():
        data = paths.member_bytes(Path(root), relative, relative)
        f.require(canonical.raw_digest(data) == RUNTIME_EVIDENCE_SHA256[key], relative,
                  "bytes differ from the independently pinned status evidence")
        result[key] = data
    return result


def _json_artifact(store: RecordStore, digest: str, path: str) -> dict:
    try:
        value = canonical.loads(store.artifact(digest, path))
    except canonical.CanonicalJSONError as exc:
        f.fail(path, f"is not valid UTF-8 JSON ({exc})")
    if type(value) is not dict:
        f.fail(path, "must be a JSON object")
    return value


def _bootstrap_fact_rows() -> list[dict]:
    return [
        {"fact_id": fact_id, "status": state, "value": None, "unit": None,
         "evidence_digests": [], "limitation": note}
        for fact_id, state, note in BOOTSTRAP_FACTS
    ]


def _pinned_artifacts(store: RecordStore) -> tuple[dict[str, bytes], dict[str, dict]]:
    raw = {key: store.artifact(digest, f"current_status.evidence.{key}")
           for key, digest in RUNTIME_EVIDENCE_SHA256.items()}
    parsed = {key: _json_artifact(store, RUNTIME_EVIDENCE_SHA256[key], f"current_status.evidence.{key}")
              for key in RUNTIME_EVIDENCE_SHA256 if key != "predecessor"}
    return raw, parsed


def _artifact_rows(value: object, path: str) -> dict[str, dict]:
    f.require(type(value) is list, path, "must be an array")
    rows = {}
    for index, row in enumerate(value):
        f.require(type(row) is dict and type(row.get("path")) is str, f"{path}[{index}]", "invalid artifact row")
        f.require(row["path"] not in rows, path, "duplicate artifact path")
        rows[row["path"]] = row
    return rows


def validate_runtime_status_evidence(
    record: dict,
    source: Path | RecordStore,
    *,
    allow_bootstrap: bool = False,
) -> None:
    """Bind a native-runtime status successor to the exact preserved synthetic receipts."""
    status.validate_current_status(
        record,
        contract_revision=EXPECTED_CONTRACT_REVISION,
        contract_manifest_digest=EXPECTED_MANIFEST_SHA256,
        official_source_hashes=EXPECTED_OFFICIAL_SOURCE_HASHES,
    )
    if isinstance(source, RecordStore):
        store = source
    else:
        root = Path(source)
        pins = contract_pins(root)
        f.require(pins.official_source_hashes == EXPECTED_OFFICIAL_SOURCE_HASHES, "contract",
                  "official source pins differ from the frozen validator")
        store = RecordStore(artifacts=runtime_status_evidence_bytes(root, record).values())

    facts = {row["fact_id"]: row for row in record["facts"]}
    predecessor_fact = facts.get(PREDECESSOR_FACT["fact_id"])
    if predecessor_fact is None:
        f.require(allow_bootstrap, "current_status.facts",
                  "bootstrap authority is allowed only in the explicit generation-zero workflow")
        f.require(record["facts"] == _bootstrap_fact_rows(), "current_status.facts",
                  "predecessor-free authority must be the exact closed bootstrap state")
        return
    f.require(record["record_digest"] == EXPECTED_CURRENT_STATUS_DIGEST, "current_status.record_digest",
              "must equal the independently pinned reconciled authority head")
    expected_ids = {row["fact_id"] for row in _bootstrap_fact_rows()} | set(RUNTIME_FACTS) | {
        PREDECESSOR_FACT["fact_id"]
    }
    f.require(set(facts) == expected_ids, "current_status.facts",
              "reconciled authority must contain exactly the closed successor fact set")
    f.literal(record["phase"], "current_status.phase", "design_only")
    for fact_id, limitation in RECONCILED_GUARD_FACTS.items():
        expected = {"fact_id": fact_id,
                    "status": "blocked_external" if fact_id == "data.real_source_admission" else "unknown",
                    "value": None, "unit": None, "evidence_digests": [], "limitation": limitation}
        f.require(facts[fact_id] == expected, f"current_status.{fact_id}",
                  "runtime reconciliation cannot alter account or biomedical-source authority")

    for fact_id, expected in RUNTIME_FACTS.items():
        row = facts.get(fact_id)
        f.require(row is not None, f"current_status.{fact_id}", "required native-runtime fact missing")
        f.require(row["status"] == "measured" and row["value"] == expected["value"] and
                  row["unit"] == expected["unit"] and row["limitation"] == expected["limitation"],
                  f"current_status.{fact_id}", "native-runtime fact exceeds or differs from the bounded receipt")
        key = expected["evidence"]
        f.require(row["evidence_digests"] == [RUNTIME_EVIDENCE_SHA256[key]],
                  f"current_status.{fact_id}.evidence_digests", "must bind the independently pinned receipt")

    predecessor_digests = predecessor_fact["evidence_digests"]
    f.require(predecessor_fact["status"] == PREDECESSOR_FACT["status"] and
              predecessor_fact["unit"] == PREDECESSOR_FACT["unit"] and
              predecessor_fact["limitation"] == PREDECESSOR_FACT["limitation"] and
              predecessor_digests == [RUNTIME_EVIDENCE_SHA256["predecessor"]],
              "current_status.authority.current_status_predecessor",
              "invalid predecessor binding")
    raw, loaded = _pinned_artifacts(store)
    predecessor_transport = raw["predecessor"]
    f.require(predecessor_transport.endswith(b"\n") and not predecessor_transport.endswith(b"\n\n"),
              "current_status.predecessor.evidence", "transport must add exactly one terminal LF")
    predecessor_bytes = predecessor_transport[:-1]
    f.require(canonical.raw_digest(predecessor_bytes) == PREDECESSOR_RAW_SHA256,
              "current_status.predecessor.evidence", "decoded predecessor bytes differ from the frozen authority")
    try:
        predecessor = canonical.loads_canonical(predecessor_bytes)
    except canonical.CanonicalJSONError as exc:
        f.fail("current_status.predecessor.evidence", f"predecessor bytes are not canonical ({exc})")
    status.validate_current_status(
        predecessor,
        contract_revision=EXPECTED_CONTRACT_REVISION,
        contract_manifest_digest=EXPECTED_MANIFEST_SHA256,
        official_source_hashes=EXPECTED_OFFICIAL_SOURCE_HASHES,
        path="current_status.predecessor",
    )
    f.require(predecessor_fact["value"] == predecessor["record_digest"],
              "current_status.authority.current_status_predecessor.value", "does not bind predecessor record")
    f.require(f.timestamp(predecessor["updated_at"], "predecessor.updated_at") <
              f.timestamp(record["updated_at"], "current_status.updated_at"), "current_status.updated_at",
              "must be later than the predecessor")

    b1 = loaded["b1"]
    f.require(b1.get("schema") == "mmbu.b1.attempt_receipt.v1" and b1.get("job_id") == "85434" and
              b1.get("scheduler_state") == "COMPLETED" and b1.get("exit_code") == "0:0" and
              b1.get("optimizer_steps") == 1 and b1.get("scientific_selection_output_observed") is False and
              b1.get("packaging_admission", {}).get("admitted") is True and
              b1.get("offline_reload", {}).get("fresh_process") is True,
              "current_status.runtime.b1_native_admission", "B1 receipt does not prove the bounded admitted path")
    projector = loaded["b2_projector"]
    projector_rows = _artifact_rows(projector.get("artifacts"), "current_status.b2_projector.artifacts")
    expected_projector_rows = {
        "attempt-2/adapter/adapter_config.json": (4188, RUNTIME_EVIDENCE_SHA256["b2_projector_adapter_config"]),
        "attempt-2/native-preflight.json": (93699, RUNTIME_EVIDENCE_SHA256["b2_projector_native"]),
        "attempt-2/offline-reload.json": (863, RUNTIME_EVIDENCE_SHA256["b2_projector_reload"]),
        "attempt-2/terminal-run.json": (1656, RUNTIME_EVIDENCE_SHA256["b2_projector_terminal"]),
    }
    for relative, (size, digest) in expected_projector_rows.items():
        row = projector_rows.get(relative)
        f.require(row is not None and row.get("retained_in_repository") is True and
                  row.get("bytes") == size and row.get("sha256") == digest,
                  f"current_status.b2_projector.artifacts.{relative}", "retained receipt is not exactly bound")
    f.require(projector.get("schema") == "mmbu.b2.projector_preflight.evidence_manifest.v1" and
              projector.get("successful_job_id") == "85459" and projector.get("attempt") == 2 and
              projector.get("failed_attempt", {}).get("job_id") == "85458" and
              projector.get("failed_attempt", {}).get("optimizer_step_executed") is False,
              "current_status.runtime.b2_projector_preflight", "B2-P manifest is incomplete or mismatched")
    projector_failed = loaded["b2_projector_failed_terminal"]
    f.require(projector_failed.get("schema") == "mmbu.b2.projector_terminal_run.v1" and
              projector_failed.get("attempt") == 1 and projector_failed.get("slurm_job_id") == "85458" and
              projector_failed.get("status") == "failed" and projector_failed.get("exit_code") == 2,
              "current_status.runtime.b2_projector_preflight", "failed B2-P predecessor is not preserved")
    projector_native = loaded["b2_projector_native"]
    projector_training = projector_native.get("training", {})
    projector_updates = projector_training.get("update_inventory", {})
    f.require(projector_native.get("schema") == "mmbu.b2.projector_preflight.result.v1" and
              projector_native.get("status") == "native_step_complete_offline_reload_pending" and
              projector_native.get("synthetic_only") is True and projector_native.get("optimizer_steps") == 1 and
              len(projector_updates.get("finite_gradients", [])) == 117 and
              len(projector_updates.get("updated", [])) == 61,
              "current_status.runtime.b2_projector_preflight", "native optimizer receipt is incomplete")
    projector_reload = loaded["b2_projector_reload"]
    f.require(projector_reload.get("schema") == "mmbu.b2.projector_offline_reload.v1" and
              projector_reload.get("status") == "passed" and projector_reload.get("fresh_process") is True and
              projector_reload.get("network_guard_proven") is True and
              projector_reload.get("adapter_local_only") is True and projector_reload.get("base_local_only") is True,
              "current_status.runtime.b2_projector_preflight", "offline reload proof is incomplete")
    projector_terminal = loaded["b2_projector_terminal"]
    terminal_rows = _artifact_rows(projector_terminal.get("evidence_files"),
                                   "current_status.b2_projector.terminal.evidence_files")
    f.require(projector_terminal.get("schema") == "mmbu.b2.projector_terminal_run.v1" and
              projector_terminal.get("attempt") == 2 and projector_terminal.get("slurm_job_id") == "85459" and
              projector_terminal.get("status") == "passed" and projector_terminal.get("exit_code") == 0 and
              terminal_rows.get("native-preflight.json", {}).get("sha256") ==
              RUNTIME_EVIDENCE_SHA256["b2_projector_native"] and
              terminal_rows.get("offline-reload.json", {}).get("sha256") ==
              RUNTIME_EVIDENCE_SHA256["b2_projector_reload"],
              "current_status.runtime.b2_projector_preflight", "terminal receipt is incomplete")
    dual = loaded["b2_dual"]
    failed = dual.get("failed_predecessors")
    successful = _artifact_rows(dual.get("successful_evidence"), "current_status.b2_dual.successful_evidence")
    f.require(dual.get("schema") == "mmbu.b2.dual_objective_evidence_manifest.v1" and
              dual.get("successful_job_id") == "85472" and
              dual.get("successful_condition") == "fixed_singleton_forward_reverse_accumulation" and
              type(failed) is list and [row.get("job_id") for row in failed] == ["85468", "85469"] and
              failed[0].get("terminal_sha256") == RUNTIME_EVIDENCE_SHA256["b2_dual_failed_terminal_1"] and
              failed[1].get("measurement_sha256") == RUNTIME_EVIDENCE_SHA256["b2_dual_failed_measurement_2"] and
              failed[1].get("terminal_sha256") == RUNTIME_EVIDENCE_SHA256["b2_dual_failed_terminal_2"] and
              successful.get("attempt-3/native-dual-objective.json", {}).get("sha256") ==
              RUNTIME_EVIDENCE_SHA256["b2_dual_native"] and
              successful.get("attempt-3/prevalidation-measurement.json", {}).get("sha256") ==
              RUNTIME_EVIDENCE_SHA256["b2_dual_measurement"] and
              successful.get("attempt-3/terminal-run.json", {}).get("sha256") ==
              RUNTIME_EVIDENCE_SHA256["b2_dual_terminal"] and
              "remains failed" in dual.get("known_limitation", ""),
              "current_status.runtime.b2_dual_objective_preflight",
              "dual-objective manifest must preserve both failures and the singleton successor")
    failed_one = loaded["b2_dual_failed_terminal_1"]
    failed_two_measurement = loaded["b2_dual_failed_measurement_2"]
    failed_two_terminal = loaded["b2_dual_failed_terminal_2"]
    f.require(failed_one.get("status") == "failed" and failed_one.get("slurm_job_id") == "85468" and
              failed_two_terminal.get("status") == "failed" and
              failed_two_terminal.get("slurm_job_id") == "85469" and
              failed_two_measurement.get("synthetic_only") is True and
              failed_two_measurement.get("loss_abs_delta", 0) > failed_two_measurement.get("loss_abs_tolerance", 0) and
              failed_two_measurement.get("gradient_relative_l2", 0) >
              failed_two_measurement.get("gradient_relative_l2_tolerance", 0),
              "current_status.runtime.b2_heterogeneous_batch_equivalence",
              "failed heterogeneous-batch evidence is incomplete")
    dual_native = loaded["b2_dual_native"]
    dual_updates = dual_native.get("parameters", {}).get("updates", {})
    dual_equivalence = dual_native.get("objective", {}).get("equivalence", {})
    f.require(dual_native.get("schema") == "mmbu.b2.dual_objective_native_result.v1" and
              dual_native.get("status") == "passed" and dual_native.get("synthetic_only") is True and
              dual_native.get("optimizer_steps") == 1 and
              dual_native.get("claim_boundary") == "engineering_preflight_not_biomedical_or_competition_performance" and
              dual_native.get("objective", {}).get("microbatch_size") == 1 and
              len(dual_updates.get("finite_gradients", [])) == 117 and len(dual_updates.get("updated", [])) == 61 and
              dual_equivalence.get("loss_abs_delta", 1) <= dual_equivalence.get("loss_tolerance", 0) and
              dual_equivalence.get("gradient_relative_l2", 1) <=
              dual_equivalence.get("gradient_relative_l2_tolerance", 0),
              "current_status.runtime.b2_dual_objective_preflight", "successful singleton receipt is incomplete")
    dual_measurement = loaded["b2_dual_measurement"]
    dual_terminal = loaded["b2_dual_terminal"]
    f.require(dual_measurement.get("status") == "measurement_complete_validation_pending" and
              dual_measurement.get("synthetic_only") is True and
              dual_terminal.get("status") == "passed" and dual_terminal.get("slurm_job_id") == "85472" and
              dual_terminal.get("exit_code") == 0,
              "current_status.runtime.b2_dual_objective_preflight", "successful terminal evidence is incomplete")


def bootstrap(root: Path, now: str | None = None) -> dict[str, bytes]:
    """Create the three authorities; refuse to overwrite any existing path."""
    root = Path(root)
    pins = contract_pins(root)
    for relative in AUTHORITY_PATHS:
        if os.path.lexists(root / relative):
            f.fail(relative, "authority already exists; bootstrap never overwrites authority")
    records = build_authority(pins, now or f.utc_now())
    validate_authority_records(records, pins)
    validate_runtime_status_evidence(records[STATUS_PATH], RecordStore(), allow_bootstrap=True)
    payloads = {relative: canonical.dumps(record) for relative, record in records.items()}
    (root / "config/phase1").mkdir(parents=True, exist_ok=True)
    for relative, data in payloads.items():
        descriptor = os.open(root / relative, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
    return payloads


def load_authority(root: Path, *, allow_bootstrap: bool = False) -> dict[str, dict]:
    """Load and validate all three authorities as exact canonical bytes."""
    root = Path(root)
    pins = contract_pins(root)
    records: dict[str, dict] = {}
    for relative in AUTHORITY_PATHS:
        raw = paths.member_bytes(root, relative, relative)
        try:
            records[relative] = canonical.loads_canonical(raw)
        except canonical.CanonicalJSONError as exc:
            f.fail(relative, f"authority bytes are invalid or noncanonical: {exc}")
    validate_authority_records(records, pins)
    validate_runtime_status_evidence(records[STATUS_PATH], root, allow_bootstrap=allow_bootstrap)
    return records


def authority_errors(root: Path, *, allow_bootstrap: bool = False) -> list[str]:
    try:
        load_authority(root, allow_bootstrap=allow_bootstrap)
    except (f.ContractViolation, OSError) as exc:
        return [f"Phase 1 authority: {exc}"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m mmbu_phase1.authority", description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("bootstrap", "verify"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    try:
        if args.command == "bootstrap":
            written = bootstrap(args.root)
            for relative, data in written.items():
                print(f"wrote {relative} ({len(data)} bytes, sha256 {canonical.raw_digest(data)})")
        else:
            for relative in load_authority(args.root):
                print(f"verified {relative}")
    except (f.ContractViolation, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
