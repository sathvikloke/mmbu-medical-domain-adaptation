"""Fail-closed tests for the clone-resident Phase 1 contract manifest."""

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from mmbu_phase1 import contract_manifest

REPO = Path(__file__).resolve().parents[2]


def canonical_json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n").encode()


class ContractManifestTests(unittest.TestCase):
    def setUp(self):
        self.contract_manifest = contract_manifest
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(REPO / "docs/phase1", self.root / "docs/phase1")

    def manifest_path(self):
        return self.root / "docs/phase1/contract-manifest.json"

    def load_manifest(self):
        return json.loads(self.manifest_path().read_text(encoding="utf-8"))

    def write_manifest(self, manifest):
        raw = canonical_json_bytes(manifest)
        self.manifest_path().write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def verify_with_current_fixture_anchor(self):
        digest = hashlib.sha256(self.manifest_path().read_bytes()).hexdigest()
        return self.contract_manifest.verify_contract_manifest(
            self.root, expected_manifest_sha256=digest
        )

    def test_current_contract_is_accepted(self):
        self.assertEqual(self.contract_manifest.verify_contract_manifest(REPO), [])

    def test_cycle46c_contract_includes_evaluator_mechanics_member(self):
        evaluator_member = "docs/phase1/EVALUATOR_MECHANICS.md"
        self.assertEqual(
            self.contract_manifest.EXPECTED_CONTRACT_REVISION,
            "2026-10-15-cycle-46c",
        )
        self.assertIn(evaluator_member, self.contract_manifest.EXPECTED_MEMBERS)
        manifest = self.load_manifest()
        self.assertEqual(manifest["contract_revision"], "2026-10-15-cycle-46c")
        self.assertEqual(set(manifest["files"]), self.contract_manifest.EXPECTED_MEMBERS)
        self.assertEqual(self.contract_manifest.verify_contract_manifest(REPO), [])

    def test_same_size_member_tampering_is_rejected(self):
        member = self.root / "docs/phase1/SCHEMAS.md"
        raw = member.read_bytes()
        member.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("SCHEMAS.md", errors)
        self.assertIn("SHA-256", errors)

    def test_evaluator_mechanics_member_hash_is_enforced(self):
        member = self.root / "docs/phase1/EVALUATOR_MECHANICS.md"
        raw = member.read_bytes()
        member.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("EVALUATOR_MECHANICS.md", errors)
        self.assertIn("SHA-256", errors)

    def test_cycle46c_mechanics_freeze_closed_rational_pairing_and_geometry_rules(self):
        mechanics = (REPO / "docs/phase1/EVALUATOR_MECHANICS.md").read_text(
            encoding="utf-8"
        )
        required_fragments = (
            '{"denominator":1,"numerator":0}',
            "gcd(abs(numerator), denominator)=1",
            "mmbu.phase1.paired_condition_contract",
            "allowed_difference_fields",
            "A mismatch in any matched field",
            "sets `predicted_boxes_digest`, `prediction_count`, `boxes_valid`, `matched_pairs`, and `row_iou` all null",
            "reason_code=invalid_prediction_box",
            "reason_code=prediction_count_mismatch",
            "reason_code=validation_failure",
            "zero-based integer `prediction_index`",
            "ties choose the lexicographically smallest vector",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, mechanics)

    def test_cycle46c_pairing_contract_has_exact_closed_condition_and_identity_fields(self):
        mechanics = (REPO / "docs/phase1/EVALUATOR_MECHANICS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "Its `matched_conditions` object contains exactly `purpose`, `authorization_registry_digest`, `source_record_digests`",
            mechanics,
        )
        self.assertIn("`execution_condition_digest` resolves the complete closed `mmbu.phase1.execution_condition`", mechanics)
        self.assertIn(
            "`allowed_difference_fields` is exactly the sorted set `adapted_from_model_digest`, `candidate_ids`, `model_digest`, `model_lineage_root_digests`, and `model_selection_receipt_digests`",
            mechanics,
        )

    def test_cycle46c_execution_condition_closes_every_required_dimension(self):
        schemas = (REPO / "docs/phase1/SCHEMAS.md").read_text(encoding="utf-8")
        required_fragments = (
            "## `mmbu.phase1.execution_condition`",
            "`request_set`, `components`, `processor`, `randomness`, `decoding`, `call_isolation`, `failure_retry`, `runtime`, `batching`, `precision_backend`",
            "every environment entry visible to the process",
            "no allowlist or relevance filter",
            "blocks condition creation rather than replacing the value digest with null",
            "`inference_settings_digest` is not an opaque policy handle",
            "`observed_condition` contains exactly `request_set`, `components`, `processor`, `randomness`, `decoding`, `call_isolation`, `failure_retry`, `runtime`, `batching`, and `precision_backend`",
            "`execution_condition_digest` equals the experiment and every raw record",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, schemas)

    def test_cycle46c_geometry_validation_failure_is_closed(self):
        mechanics = (REPO / "docs/phase1/EVALUATOR_MECHANICS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("missing, null, scalar, object, or wrong-type member", mechanics)
        self.assertIn("parsed valid-coordinate array with another invalid field", mechanics)
        self.assertIn("`validation_failure`", mechanics)
        self.assertIn("No prediction artifact or empty array is fabricated", mechanics)

    def test_duplicate_json_key_is_rejected(self):
        raw = self.manifest_path().read_text(encoding="utf-8")
        self.manifest_path().write_text(raw.replace('"schema_version": 1,', '"schema_version": 1,\n  "schema_version": 1,'), encoding="utf-8")
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("duplicate JSON key", errors)

    def test_nonfinite_json_number_is_rejected(self):
        raw = self.manifest_path().read_text(encoding="utf-8")
        self.manifest_path().write_text(raw.replace('"schema_version": 1', '"schema_version": NaN'), encoding="utf-8")
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("nonfinite JSON number", errors)

    def test_overflowing_json_number_is_rejected_as_nonfinite(self):
        raw = self.manifest_path().read_text(encoding="utf-8")
        self.manifest_path().write_text(raw.replace('"schema_version": 1', '"schema_version": 1e9999'), encoding="utf-8")
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("nonfinite JSON number", errors)

    def test_missing_and_extra_members_are_rejected(self):
        manifest = self.load_manifest()
        manifest["files"].pop("docs/phase1/SCHEMAS.md")
        manifest["files"]["docs/phase1/EXTRA.md"] = {"bytes": 1, "sha256": "0" * 64}
        self.write_manifest(manifest)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("missing manifest member", errors)
        self.assertIn("extra manifest member", errors)

    def test_escaping_and_nonnormalized_paths_are_rejected(self):
        for unsafe in ("../SCHEMAS.md", "docs/phase1/../SCHEMAS.md", "/docs/phase1/SCHEMAS.md", "docs\\phase1\\SCHEMAS.md"):
            with self.subTest(unsafe=unsafe):
                manifest = self.load_manifest()
                receipt = manifest["files"].pop("docs/phase1/SCHEMAS.md")
                manifest["files"][unsafe] = receipt
                self.write_manifest(manifest)
                errors = "\n".join(self.verify_with_current_fixture_anchor())
                self.assertIn("unsafe manifest path", errors)
                shutil.copy2(REPO / "docs/phase1/contract-manifest.json", self.manifest_path())

    def test_symlink_member_is_rejected(self):
        member = self.root / "docs/phase1/SCHEMAS.md"
        external = self.root / "external.md"
        external.write_bytes(member.read_bytes())
        member.unlink()
        member.symlink_to(external)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("symlink file", errors)

    def test_symlinked_ancestor_outside_root_is_rejected(self):
        outside = tempfile.TemporaryDirectory()
        self.addCleanup(outside.cleanup)
        external_docs = Path(outside.name) / "docs"
        shutil.copytree(self.root / "docs", external_docs)
        shutil.rmtree(self.root / "docs")
        (self.root / "docs").symlink_to(external_docs, target_is_directory=True)
        errors = "\n".join(self.contract_manifest.verify_contract_manifest(self.root))
        self.assertIn("symlink ancestor", errors)

    def test_symlinked_phase1_ancestor_inside_root_is_rejected(self):
        real_phase1 = self.root / "real-phase1"
        (self.root / "docs/phase1").rename(real_phase1)
        (self.root / "docs/phase1").symlink_to(real_phase1, target_is_directory=True)
        errors = "\n".join(self.contract_manifest.verify_contract_manifest(self.root))
        self.assertIn("symlink ancestor", errors)

    def test_wrong_revision_is_rejected_even_with_refreshed_anchor(self):
        manifest = self.load_manifest()
        manifest["contract_revision"] = "wrong-revision"
        self.write_manifest(manifest)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("contract revision", errors)

    def test_boolean_schema_version_is_not_integer_one(self):
        manifest = self.load_manifest()
        manifest["schema_version"] = True
        self.write_manifest(manifest)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("schema_version must be integer 1", errors)

    def test_float_schema_version_is_not_integer_one(self):
        manifest = self.load_manifest()
        manifest["schema_version"] = 1.0
        self.write_manifest(manifest)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("schema_version must be integer 1", errors)

    def test_member_size_and_hash_receipts_are_both_enforced(self):
        manifest = self.load_manifest()
        receipt = manifest["files"]["docs/phase1/SCHEMAS.md"]
        receipt["bytes"] += 1
        receipt["sha256"] = "0" * 64
        self.write_manifest(manifest)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("byte count", errors)
        self.assertIn("SHA-256", errors)

    def test_official_source_map_must_repeat_exact_manifest_hashes(self):
        source_map = self.root / "docs/phase1/OFFICIAL_SOURCE_MAP.md"
        source_map.write_text(
            source_map.read_text(encoding="utf-8").replace(
                "68fb4c2685d3d3b501da6f92f0906f970d851b596e98fddede26fb6e2b6e4ba0",
                "0" * 64,
                1,
            ),
            encoding="utf-8",
        )
        manifest = self.load_manifest()
        raw = source_map.read_bytes()
        manifest["files"]["docs/phase1/OFFICIAL_SOURCE_MAP.md"] = {
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        self.write_manifest(manifest)
        errors = "\n".join(self.verify_with_current_fixture_anchor())
        self.assertIn("official source hash mismatch", errors)


class RootCommandGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(REPO / "docs/phase1", self.root / "docs/phase1")
        member = self.root / "docs/phase1/SCHEMAS.md"
        raw = member.read_bytes()
        member.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))

        import importlib.util
        spec = importlib.util.spec_from_file_location("team_for_contract_test", REPO / "tools/team.py")
        self.team = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.team)

    def test_every_root_command_rejects_contract_drift_before_other_work(self):
        for command in ("test", "smoke", "verify-evidence", "verify-links"):
            with self.subTest(command=command):
                stdout = io.StringIO()
                stderr = io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    result = self.team.main(["--root", str(self.root), command])
                self.assertNotEqual(result, 0)
                self.assertIn("contract", (stdout.getvalue() + stderr.getvalue()).lower())


if __name__ == "__main__":
    unittest.main()
