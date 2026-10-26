"""Current status, generation-zero registries, and the one bootstrap command."""

import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from mmbu_phase1 import authority, canonical, fields, registries, status
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.store import RecordStore

REPO = Path(__file__).resolve().parents[2]


def temp_contract_root(testcase):
    temp = tempfile.TemporaryDirectory()
    testcase.addCleanup(temp.cleanup)
    root = Path(os.path.realpath(temp.name))
    shutil.copytree(REPO / "docs/phase1", root / "docs/phase1")
    return root


def pins():
    return authority.contract_pins(REPO)


def valid_status():
    return authority.build_authority(pins(), "2026-10-16T12:00:00.000000Z")[authority.STATUS_PATH]


def reseal(record, **changes):
    updated = copy.deepcopy(record)
    updated.update(changes)
    return canonical.seal(updated)


def check_status(record):
    p = pins()
    return status.validate_current_status(
        record,
        contract_revision=p.revision,
        contract_manifest_digest=p.manifest_sha256,
        official_source_hashes=p.official_source_hashes,
    )


class CurrentStatusTests(unittest.TestCase):
    def test_bootstrap_status_is_design_only_with_explicit_unknown_facts(self):
        record = valid_status()
        check_status(record)
        self.assertEqual(record["phase"], "design_only")
        self.assertEqual(record["contract_revision"], "2026-10-15-cycle-46f")
        self.assertEqual(record["contract_manifest_digest"], "15daeff7a4f162a0c6adf1aae4d8d772bcbaa23351ab3120cd284a7ca8835cce")
        self.assertTrue(record["facts"])
        for fact in record["facts"]:
            self.assertIn(fact["status"], {"unknown", "blocked_external"})
            self.assertIsNone(fact["value"])
            self.assertIsNone(fact["unit"])
            self.assertTrue(fact["limitation"])
        ids = {fact["fact_id"] for fact in record["facts"]}
        for required in ("account.mocs_account", "account.mocs_allocation", "account.gpu_allocation",
                         "data.real_source_admission", "runtime.b1_native_admission"):
            self.assertIn(required, ids)

    def test_status_rejects_contract_pin_drift(self):
        record = valid_status()
        mutations = (
            {"contract_revision": "2026-10-15-cycle-46e"},
            {"contract_manifest_digest": "0" * 64},
            {"official_source_hashes": {**record["official_source_hashes"], "MMBU_challenge_update.pdf": "0" * 64}},
            {"official_source_hashes": {"MMBU_challenge_update.pdf": record["official_source_hashes"]["MMBU_challenge_update.pdf"]}},
            {"official_source_hashes": {**record["official_source_hashes"], "extra.pdf": "0" * 64}},
            {"phase": "ready"},
            {"updated_at": "2026-10-16 12:00:00"},
        )
        for mutation in mutations:
            with self.subTest(mutation=sorted(mutation)):
                with self.assertRaises(ContractViolation):
                    check_status(reseal(record, **mutation))

    def test_unmeasured_readiness_cannot_be_asserted(self):
        record = valid_status()
        fact = record["facts"][-1]
        mutations = (
            {**fact, "status": "measured"},
            {**fact, "status": "measured", "value": "ready", "unit": "state"},
            {**fact, "value": "ready"},
            {**fact, "unit": "GPU"},
            {**fact, "limitation": ""},
            {**fact, "limitation": None},
            {**fact, "status": "partial"},
            {**fact, "extra": True},
        )
        for mutated in mutations:
            with self.subTest(mutated=mutated):
                facts = record["facts"][:-1] + [mutated]
                with self.assertRaises(ContractViolation):
                    check_status(reseal(record, facts=facts))

    def test_public_hardware_cannot_become_account_evidence(self):
        record = valid_status()
        public_spec = {
            "fact_id": "public.mocs_gpu_specification",
            "status": "measured",
            "value": 8,
            "unit": "gpu_per_node",
            "evidence_digests": ["a" * 64],
            "limitation": "Public cluster specification only.",
        }
        copied = {
            "fact_id": "account.gpu_allocation",
            "status": "measured",
            "value": 8,
            "unit": "gpu_per_node",
            "evidence_digests": ["a" * 64],
            "limitation": None,
        }
        valid_facts = sorted([f for f in record["facts"]] + [public_spec], key=lambda item: item["fact_id"])
        check_status(reseal(record, facts=valid_facts))
        others = [f for f in record["facts"] if f["fact_id"] != "account.gpu_allocation"]
        forged = sorted(others + [public_spec, copied], key=lambda item: item["fact_id"])
        with self.assertRaises(ContractViolation):
            check_status(reseal(record, facts=forged))
        unknown_with_public_evidence = dict(copied, status="unknown", value=None, unit=None,
                                            limitation="pending allocation evidence")
        forged = sorted(others + [public_spec, unknown_with_public_evidence], key=lambda item: item["fact_id"])
        with self.assertRaises(ContractViolation):
            check_status(reseal(record, facts=forged))

    def test_facts_are_unique_and_utf8_sorted(self):
        record = valid_status()
        with self.assertRaises(ContractViolation):
            check_status(reseal(record, facts=list(reversed(record["facts"]))))
        with self.assertRaises(ContractViolation):
            check_status(reseal(record, facts=record["facts"] + [record["facts"][-1]]))

    def test_stale_digest_unknown_key_and_wrong_schema_reject(self):
        record = valid_status()
        with self.assertRaises(ContractViolation):
            check_status({**record, "phase": "phase1_running"})
        with self.assertRaises(ContractViolation):
            check_status(reseal(record, extra_overlay=True))
        with self.assertRaises(ContractViolation):
            check_status(reseal(record, schema_id="mmbu.phase1.current_status_overlay"))

    def test_blocked_successor_preserves_predecessor_and_classifies_repair_evidence(self):
        predecessor = canonical.loads_canonical(
            (REPO / authority.STATUS_SUCCESSOR_EVIDENCE_REPOSITORY_PATHS[
                "status_successor_predecessor"
            ]).read_bytes()
        )
        successor = status.build_status_successor(
            predecessor,
            predecessor_raw_sha256="a" * 64,
            repaired_revision="1" * 40,
            repair_evidence_digest="b" * 64,
            audit_blockers=[
                "authenticated clinical review has not occurred",
                "real confirmation has not run",
            ],
            updated_at="2026-10-26T08:00:00Z",
        )
        status.validate_status_transition(predecessor, successor)
        facts = {row["fact_id"]: row for row in successor["facts"]}
        self.assertEqual(successor["phase"], "phase1_returned_blocked")
        self.assertEqual(
            facts["authority.current_status_predecessor"]["value"],
            predecessor["record_digest"],
        )
        self.assertEqual(
            facts["repair.busi_whu_decision_integrity"]["value"], "1" * 40,
        )
        self.assertEqual(
            facts["research.busi_whu_evidence_classification"]["value"],
            "exploratory_only",
        )
        self.assertEqual(facts["audit.busi_whu_decision_integrity"]["status"], "blocked_external")

    def test_status_successor_rejects_rollback_in_place_and_historical_mutation(self):
        predecessor = canonical.loads_canonical(
            (REPO / authority.STATUS_SUCCESSOR_EVIDENCE_REPOSITORY_PATHS[
                "status_successor_predecessor"
            ]).read_bytes()
        )

        def built(**changes):
            values = {
                "predecessor_raw_sha256": "a" * 64,
                "repaired_revision": "1" * 40,
                "repair_evidence_digest": "b" * 64,
                "audit_blockers": ["real confirmation has not run"],
                "updated_at": "2026-10-26T08:00:00Z",
            }
            values.update(changes)
            return status.build_status_successor(predecessor, **values)

        with self.assertRaises(ContractViolation):
            status.validate_status_transition(predecessor, predecessor)
        with self.assertRaises(ContractViolation):
            built(updated_at=predecessor["updated_at"])
        successor = built()
        historical = next(
            row for row in successor["facts"] if row["fact_id"] == "runtime.b1_native_admission"
        )
        mutated_facts = [
            {**row, "limitation": "rewritten history"} if row is historical else row
            for row in successor["facts"]
        ]
        with self.assertRaises(ContractViolation):
            status.validate_status_transition(predecessor, reseal(successor, facts=mutated_facts))
        with self.assertRaises(ContractViolation):
            status.validate_status_transition(
                predecessor,
                reseal(successor, phase="design_only"),
            )

    def test_repository_status_reconciles_only_bounded_native_runtime_evidence(self):
        record = authority.load_authority(REPO)[authority.STATUS_PATH]
        facts = {row["fact_id"]: row for row in record["facts"]}
        self.assertEqual(record["phase"], "phase1_returned_blocked")
        for fact_id in ("account.gpu_allocation", "account.mocs_account", "account.mocs_allocation"):
            self.assertEqual(facts[fact_id]["status"], "unknown")
            self.assertIsNone(facts[fact_id]["value"])
            self.assertEqual(facts[fact_id]["evidence_digests"], [])
        self.assertEqual(facts["data.real_source_admission"]["status"], "blocked_external")
        self.assertEqual(facts["runtime.b1_native_admission"]["value"], "synthetic_engineering_only")
        self.assertEqual(facts["runtime.b2_projector_preflight"]["value"], "synthetic_engineering_only")
        self.assertEqual(facts["runtime.b2_dual_objective_preflight"]["value"],
                         "singleton_microbatch_reference_only")
        self.assertIs(facts["runtime.b2_heterogeneous_batch_equivalence"]["value"], False)
        authority.validate_runtime_status_evidence(record, REPO)

    def test_native_runtime_evidence_rejects_authority_and_receipt_mutations(self):
        record = authority.load_authority(REPO)[authority.STATUS_PATH]
        facts = {row["fact_id"]: row for row in record["facts"]}
        cases = []
        b1 = facts["runtime.b1_native_admission"]
        cases.append(reseal(record, facts=sorted([
            *(row for row in record["facts"] if row["fact_id"] != b1["fact_id"]),
            {**b1, "evidence_digests": ["0" * 64]},
        ], key=lambda row: row["fact_id"])))
        account = facts["account.mocs_account"]
        cases.append(reseal(record, facts=sorted([
            *(row for row in record["facts"] if row["fact_id"] != account["fact_id"]),
            {**account, "status": "measured", "value": "usable", "unit": "state",
             "evidence_digests": b1["evidence_digests"], "limitation": None},
        ], key=lambda row: row["fact_id"])))
        source = facts["data.real_source_admission"]
        cases.append(reseal(record, facts=sorted([
            *(row for row in record["facts"] if row["fact_id"] != source["fact_id"]),
            {**source, "status": "measured", "value": "admitted", "unit": "state",
             "evidence_digests": b1["evidence_digests"], "limitation": None},
        ], key=lambda row: row["fact_id"])))
        predecessor = facts["authority.current_status_predecessor"]
        cases.append(reseal(record, facts=sorted([
            *(row for row in record["facts"] if row["fact_id"] != predecessor["fact_id"]),
            {**predecessor, "value": "0" * 64},
        ], key=lambda row: row["fact_id"])))
        for mutated in cases:
            with self.subTest(facts=[row["fact_id"] for row in mutated["facts"]]):
                with self.assertRaises(ContractViolation):
                    authority.validate_runtime_status_evidence(mutated, REPO)

    def test_native_runtime_evidence_rejects_erased_batch_failure(self):
        record = authority.load_authority(REPO)[authority.STATUS_PATH]
        artifacts = authority.runtime_status_evidence_bytes(REPO, record)
        dual = json.loads(artifacts["b2_dual"])
        dual["failed_predecessors"] = dual["failed_predecessors"][1:]
        forged_dual = canonical.dumps(dual)
        forged_digest = canonical.raw_digest(forged_dual)
        facts = []
        for row in record["facts"]:
            if row["fact_id"] in {"runtime.b2_dual_objective_preflight",
                                   "runtime.b2_heterogeneous_batch_equivalence"}:
                row = {**row, "evidence_digests": [forged_digest]}
            facts.append(row)
        forged_status = reseal(record, facts=facts)
        store = RecordStore(artifacts=[
            forged_dual if key == "b2_dual" else data for key, data in artifacts.items()
        ])
        with self.assertRaises(ContractViolation):
            authority.validate_runtime_status_evidence(forged_status, store)

    def test_native_runtime_reconciliation_cannot_be_removed_or_extended(self):
        record = authority.load_authority(REPO)[authority.STATUS_PATH]
        predecessor_id = authority.PREDECESSOR_FACT["fact_id"]
        without_predecessor = reseal(
            record,
            facts=[row for row in record["facts"] if row["fact_id"] != predecessor_id],
        )
        arbitrary_runtime = {
            "fact_id": "runtime.full_training_ready",
            "status": "measured",
            "value": True,
            "unit": "ready",
            "evidence_digests": ["0" * 64],
            "limitation": None,
        }
        extended_bootstrap = reseal(
            valid_status(),
            facts=sorted(valid_status()["facts"] + [arbitrary_runtime], key=lambda row: row["fact_id"]),
        )
        account = next(row for row in record["facts"] if row["fact_id"] == "account.mocs_account")
        changed_limitation = reseal(
            record,
            facts=sorted([
                *[row for row in record["facts"] if row["fact_id"] != account["fact_id"]],
                {**account, "limitation": "Authenticated with full MOCS entitlement."},
            ], key=lambda row: row["fact_id"]),
        )
        for mutated in (without_predecessor, extended_bootstrap, changed_limitation):
            with self.subTest(facts=[row["fact_id"] for row in mutated["facts"]]):
                with self.assertRaises(ContractViolation):
                    authority.validate_runtime_status_evidence(mutated, REPO)
        with self.assertRaises(ContractViolation):
            authority.validate_runtime_status_evidence(valid_status(), RecordStore())
        authority.validate_runtime_status_evidence(valid_status(), RecordStore(), allow_bootstrap=True)

    def test_exact_bootstrap_cannot_replace_reconciled_repository_head(self):
        rollback = reseal(valid_status(), updated_at="2026-10-24T03:00:00.000000Z")
        with self.assertRaises(ContractViolation):
            authority.validate_runtime_status_evidence(rollback, REPO)

    def test_standalone_runtime_validation_enforces_frozen_status_schema(self):
        record = authority.load_authority(REPO)[authority.STATUS_PATH]
        artifacts = authority.runtime_status_evidence_bytes(REPO, record)
        store = RecordStore(artifacts=artifacts.values())
        mutations = (
            {"schema_version": 999},
            {"extra_overlay": True},
            {"facts": record["facts"] + [record["facts"][-1]]},
            {"facts": record["facts"][:-1]},
            {"contract_manifest_digest": "0" * 64},
            {"official_source_hashes": {**record["official_source_hashes"],
                                        "MMBU_challenge_update.pdf": "0" * 64}},
            {"updated_at": "2026-10-23 00:00:00"},
        )
        for mutation in mutations:
            with self.subTest(mutation=sorted(mutation)):
                with self.assertRaises(ContractViolation):
                    authority.validate_runtime_status_evidence(reseal(record, **mutation), store)

    def test_runtime_receipts_are_fixed_independently_of_status_selected_digests(self):
        record = authority.load_authority(REPO)[authority.STATUS_PATH]
        artifacts = authority.runtime_status_evidence_bytes(REPO, record)
        skeletal = canonical.dumps({
            "schema": "mmbu.b2.projector_preflight.evidence_manifest.v1",
            "successful_job_id": "85459",
            "attempt": 2,
            "failed_attempt": {"job_id": "85458", "optimizer_step_executed": False},
        })
        skeletal_digest = canonical.raw_digest(skeletal)
        facts = [
            {**row, "evidence_digests": [skeletal_digest]}
            if row["fact_id"] == "runtime.b2_projector_preflight" else row
            for row in record["facts"]
        ]
        forged_status = reseal(record, facts=facts)
        store = RecordStore(artifacts=[
            skeletal if key == "b2_projector" else data for key, data in artifacts.items()
        ])
        with self.assertRaises(ContractViolation):
            authority.validate_runtime_status_evidence(forged_status, store)

        subordinate_key = "b2_projector_native"
        missing = RecordStore(artifacts=[data for key, data in artifacts.items() if key != subordinate_key])
        with self.assertRaises(ContractViolation):
            authority.validate_runtime_status_evidence(record, missing)


class GenerationZeroRegistryTests(unittest.TestCase):
    def setUp(self):
        built = authority.build_authority(pins(), "2026-10-16T12:00:00.000000Z")
        self.auth = built[authority.AUTHORIZATION_REGISTRY_PATH]
        self.opening = built[authority.OPENING_RECEIPT_REGISTRY_PATH]

    def test_generation_zero_registries_authorize_nothing(self):
        registries.validate_authorization_registry(self.auth)
        registries.validate_opening_receipt_registry(self.opening)
        self.assertEqual(self.auth["generation"], 0)
        self.assertIsNone(self.auth["supersedes_registry_digest"])
        for key in ("acquisition_authorization_digests", "source_record_digests", "purpose_authorization_digests",
                    "revoked_digests"):
            self.assertEqual(self.auth[key], [])
        for key in ("acquisition_heads", "source_heads", "authorization_heads"):
            self.assertEqual(self.auth[key], {})
        self.assertEqual(self.opening["generation"], 0)
        self.assertIsNone(self.opening["supersedes_registry_digest"])
        self.assertEqual(self.opening["heads"], [])
        store = registries_store(self.auth, self.opening)
        registries.check_authorization_registry_chain(store, self.auth["record_digest"])
        registries.check_opening_receipt_registry_chain(store, self.opening["record_digest"])

    def test_generation_rules_reject_predecessor_and_type_drift(self):
        cases = (
            (self.auth, {"supersedes_registry_digest": "0" * 64}),
            (self.auth, {"generation": -1}),
            (self.auth, {"generation": True}),
            (self.auth, {"acquisition_heads": {"src|v1": "0" * 64}}),
            (self.auth, {"source_heads": {"src": "0" * 64}}),
            (self.auth, {"authorization_heads": {"src|development": "0" * 64}}),
            (self.auth, {"revoked_digests": ["0" * 64]}),
            (self.auth, {"source_record_digests": ["1" * 64, "0" * 64]}),
            (self.opening, {"supersedes_registry_digest": "0" * 64}),
            (self.opening, {"heads": [{"lock_digest": "0" * 64}]}),
            (self.opening, {"generation": 1}),
        )
        for record, mutation in cases:
            with self.subTest(schema=record["schema_id"], mutation=sorted(mutation)):
                mutated = reseal(record, **mutation)
                with self.assertRaises(ContractViolation):
                    if record is self.auth:
                        registries.validate_authorization_registry(mutated)
                        registries.check_authorization_registry_chain(registries_store(mutated), mutated["record_digest"])
                    else:
                        registries.validate_opening_receipt_registry(mutated)
                        registries.check_opening_receipt_registry_chain(registries_store(mutated), mutated["record_digest"])

    def test_successor_must_increment_and_bind_predecessor(self):
        successor = reseal(self.auth, generation=1, supersedes_registry_digest=self.auth["record_digest"],
                           registry_id="authorization-registry-g1", as_of="2026-10-16T12:00:01.000000Z")
        registries.check_authorization_registry_chain(registries_store(self.auth, successor), successor["record_digest"])
        skipped = reseal(successor, generation=2)
        with self.assertRaises(ContractViolation):
            registries.check_authorization_registry_chain(registries_store(self.auth, skipped), skipped["record_digest"])
        omitted = reseal(successor, supersedes_registry_digest="0" * 64)
        with self.assertRaises(ContractViolation):
            registries.check_authorization_registry_chain(registries_store(omitted), omitted["record_digest"])
        backward = reseal(successor, as_of="2026-10-16T11:00:00.000000Z")
        with self.assertRaises(ContractViolation):
            registries.check_authorization_registry_chain(registries_store(self.auth, backward), backward["record_digest"])
        opening_successor = reseal(self.opening, generation=1, supersedes_registry_digest=self.opening["record_digest"],
                                   created_at="2026-10-16T12:00:01.000000Z")
        registries.check_opening_receipt_registry_chain(registries_store(self.opening, opening_successor),
                                                        opening_successor["record_digest"])
        with self.assertRaises(ContractViolation):
            registries.check_opening_receipt_registry_chain(registries_store(opening_successor),
                                                            opening_successor["record_digest"])


def registries_store(*records):
    from mmbu_phase1.store import RecordStore
    return RecordStore(records)


class BootstrapCommandTests(unittest.TestCase):
    def test_one_command_bootstraps_canonical_authority_files_with_actual_time(self):
        root = temp_contract_root(self)
        before = fields.timestamp(fields.utc_now(), "before")
        result = subprocess.run(
            [sys.executable, "-m", "mmbu_phase1.authority", "bootstrap", "--root", str(root)],
            capture_output=True, text=True, env={**os.environ, "PYTHONPATH": str(REPO / "src")}, check=False,
        )
        after = fields.timestamp(fields.utc_now(), "after")
        self.assertEqual(result.returncode, 0, result.stderr)
        loaded = authority.load_authority(root, allow_bootstrap=True)
        self.assertEqual(set(loaded), set(authority.AUTHORITY_PATHS))
        for relative in authority.AUTHORITY_PATHS:
            raw = (root / relative).read_bytes()
            self.assertEqual(canonical.dumps(canonical.loads(raw)), raw, relative)
        status_record = loaded[authority.STATUS_PATH]
        created = fields.timestamp(status_record["updated_at"], "updated_at")
        self.assertLessEqual(before, created)
        self.assertLessEqual(created, after)
        auth = loaded[authority.AUTHORIZATION_REGISTRY_PATH]
        self.assertEqual(auth["as_of"], status_record["updated_at"])
        self.assertEqual(auth["registry_id"], authority.derived_id("authorization_registry", 0, auth["as_of"]))
        opening = loaded[authority.OPENING_RECEIPT_REGISTRY_PATH]
        self.assertEqual(opening["registry_id"], authority.derived_id("opening_receipt_registry", 0, opening["created_at"]))

    def test_bootstrap_refuses_to_overwrite_existing_authority(self):
        root = temp_contract_root(self)
        authority.bootstrap(root)
        original = {p: (root / p).read_bytes() for p in authority.AUTHORITY_PATHS}
        with self.assertRaises(ContractViolation):
            authority.bootstrap(root)
        self.assertEqual({p: (root / p).read_bytes() for p in authority.AUTHORITY_PATHS}, original)

    def test_bootstrap_requires_the_exact_contract(self):
        root = temp_contract_root(self)
        member = root / "docs/phase1/SCHEMAS.md"
        raw = member.read_bytes()
        member.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        with self.assertRaises(ContractViolation):
            authority.bootstrap(root)
        self.assertFalse((root / "config").exists())

    def test_load_rejects_missing_symlinked_noncanonical_or_invalid_authority(self):
        for relative in authority.AUTHORITY_PATHS:
            with self.subTest(missing=relative):
                root = temp_contract_root(self)
                authority.bootstrap(root)
                (root / relative).unlink()
                with self.assertRaises(ContractViolation):
                    authority.load_authority(root)
        root = temp_contract_root(self)
        authority.bootstrap(root)
        target = root / authority.STATUS_PATH
        raw = target.read_bytes()
        target.write_bytes(json.dumps(json.loads(raw), indent=2).encode())
        with self.assertRaises(ContractViolation):
            authority.load_authority(root)
        target.write_bytes(raw)
        moved = root / "status-elsewhere.json"
        target.rename(moved)
        target.symlink_to(moved)
        with self.assertRaises(ContractViolation):
            authority.load_authority(root)

    def test_repository_authority_files_validate(self):
        loaded = authority.load_authority(REPO)
        self.assertEqual(loaded[authority.STATUS_PATH]["phase"], "phase1_returned_blocked")
        self.assertEqual(loaded[authority.AUTHORIZATION_REGISTRY_PATH]["generation"], 0)
        self.assertEqual(loaded[authority.OPENING_RECEIPT_REGISTRY_PATH]["heads"], [])


if __name__ == "__main__":
    unittest.main()
