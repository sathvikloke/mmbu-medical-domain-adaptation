"""Phase decision function, bundle generation/validation, and fresh-clone completeness."""

import copy
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from mmbu_phase1 import bundle, canonical, claims as claim_rules, evidence, scope
from mmbu_phase1.fields import ContractViolation

REPO = Path(__file__).resolve().parents[2]


def rows(**overrides):
    status = {rid: "verified" for rid in claim_rules.INPUT_IDS}
    status.update(overrides)
    return [{"requirement_id": rid, "status": status[rid]} for rid in claim_rules.INPUT_IDS]


NONE_FIRED = {name: False for name in claim_rules.REJECTION_PREDICATES}


class DecisionFunctionTests(unittest.TestCase):
    def test_phase_decision_is_derived_without_self_reference(self):
        self.assertEqual(claim_rules.derive_decision(rows(), NONE_FIRED), "accepted")
        self.assertEqual(claim_rules.derive_decision(rows(**{"P1-17b": "blocked_external"}), NONE_FIRED), "accepted")
        self.assertEqual(claim_rules.derive_decision(rows(**{"P1-04": "untested"}), NONE_FIRED), "returned_blocked")
        self.assertEqual(claim_rules.derive_decision(rows(**{"P1-17a": "blocked_external"}), NONE_FIRED), "returned_blocked")
        self.assertEqual(claim_rules.derive_decision(rows(**{"P1-13": "failed"}), NONE_FIRED), "rejected")
        for name in claim_rules.REJECTION_PREDICATES:
            with self.subTest(predicate=name):
                self.assertEqual(claim_rules.derive_decision(rows(), {**NONE_FIRED, name: True}), "rejected")

    def test_input_set_is_exactly_the_22_non_decision_rows(self):
        self.assertEqual(len(claim_rules.INPUT_IDS), 22)
        self.assertNotIn("P1-21", claim_rules.INPUT_IDS)
        with self.assertRaises(ContractViolation):
            claim_rules.derive_decision(rows() + [{"requirement_id": "P1-21", "status": "verified"}], NONE_FIRED)
        with self.assertRaises(ContractViolation):
            claim_rules.derive_decision(rows()[1:], NONE_FIRED)
        with self.assertRaises(ContractViolation):
            claim_rules.derive_decision(rows(), {k: v for k, v in NONE_FIRED.items() if k != "self_reference"})

    def test_stable_behavior_list_matches_the_acceptance_contract(self):
        text = (REPO / "docs/phase1/ACCEPTANCE.md").read_text(encoding="utf-8")
        block = text.split("## Stable behavior names", 1)[1].split("```text", 1)[1].split("```", 1)[0]
        self.assertEqual(tuple(line.strip() for line in block.strip().splitlines()), claim_rules.STABLE_BEHAVIORS)

    def test_scope_rows_cover_inputs_without_overlap(self):
        eligible, validation, deferred = set(scope.ELIGIBLE_ROWS), set(scope.VALIDATION_ONLY_ROWS), set(scope.DEFERRED_ROWS)
        self.assertEqual(eligible | validation | deferred, set(claim_rules.INPUT_IDS))
        self.assertFalse(eligible & validation or eligible & deferred or validation & deferred)
        self.assertEqual(eligible, {"P1-00", "P1-01", "P1-06", "P1-07", "P1-08", "P1-09", "P1-10", "P1-12", "P1-19", "P1-20"})
        self.assertEqual(scope.DEFERRED_ROWS["P1-17b"], "blocked_external")
        for name, (_, _, behaviors, _, _) in scope.ROW_SPECS.items():
            self.assertLessEqual(set(behaviors), set(claim_rules.STABLE_BEHAVIORS), name)


class BundleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = Path(os.path.realpath(tempfile.mkdtemp(prefix="phase1a-bundle-test-")))
        cls.summary = bundle.generate(REPO, cls.temp / "bundle", cls.temp / "retention.json", run_commands=False)
        cls.root = cls.temp / "bundle"

    @classmethod
    def tearDownClass(cls):
        for directory, _, files in os.walk(cls.temp):
            for name in files:
                os.chmod(os.path.join(directory, name), 0o644)
        shutil.rmtree(cls.temp, ignore_errors=True)

    def copy_bundle(self):
        target = Path(os.path.realpath(tempfile.mkdtemp(prefix="phase1a-bundle-copy-")))
        self.addCleanup(shutil.rmtree, target, True)
        shutil.copytree(self.root, target / "bundle")
        shutil.copy2(self.temp / "retention.json", target / "retention.json")
        for directory, _, files in os.walk(target):
            for name in files:
                os.chmod(os.path.join(directory, name), 0o644)
        return target / "bundle", target / "retention.json"

    def rewrite(self, root, relative, record):
        (root / relative).write_bytes(canonical.dumps(canonical.seal(record)))

    def reroot(self, root, retention):
        os.remove(root / evidence.MANIFEST_NAME)
        os.remove(retention)
        manifest, digest = evidence.build_evidence_manifest(root, "rebuilt", "2099-01-01T00:00:00.000000Z")
        retention.write_bytes(canonical.dumps(evidence.retention_receipt("x", "rebuilt", digest)))

    def test_generated_bundle_derives_returned_blocked_without_command_evidence(self):
        self.assertEqual(self.summary["decision"], "returned_blocked")
        statuses = self.summary["statuses"]
        self.assertEqual(statuses["P1-17b"], "blocked_external")
        self.assertTrue(all(statuses[r] == "untested" for r in scope.ELIGIBLE_ROWS))
        self.assertEqual(bundle.validate(self.root, self.temp / "retention.json", REPO), "returned_blocked")

    def test_forged_decision_rejects(self):
        root, retention = self.copy_bundle()
        decision = canonical.loads((root / "phase-decision.json").read_bytes())
        self.rewrite(root, "phase-decision.json", {**decision, "decision": "accepted"})
        self.reroot(root, retention)
        with self.assertRaises(ContractViolation) as caught:
            bundle.validate(root, retention, REPO)
        self.assertIn("forged decision", str(caught.exception))

    def test_invalid_root_rejects(self):
        root, retention = self.copy_bundle()
        (root / "limitations.md").write_text("tampered")
        with self.assertRaises(ContractViolation):
            bundle.validate(root, retention, REPO)

    def test_self_reference_and_verified_without_evidence_reject(self):
        root, retention = self.copy_bundle()
        claims = canonical.loads((root / "claims.json").read_bytes())
        changed = copy.deepcopy(claims)
        row = changed["claims"][0]
        row.update(status="verified", code_paths=["tools/team.py"], test_ids=["missing.Test.test_x"],
                   evidence_paths=["phase-decision.json"], evidence_digests=["0" * 64])
        self.rewrite(root, "claims.json", changed)
        new_claims = canonical.loads((root / "claims.json").read_bytes())
        trace = canonical.loads((root / "requirement-trace.json").read_bytes())
        trace["claims_digest"] = new_claims["record_digest"]
        trace["rows"][0].update(test_ids=["missing.Test.test_x"], evidence_paths=["phase-decision.json"])
        self.rewrite(root, "requirement-trace.json", trace)
        new_trace = canonical.loads((root / "requirement-trace.json").read_bytes())
        decision = canonical.loads((root / "phase-decision.json").read_bytes())
        self.rewrite(root, "phase-decision.json", {**decision, "claims_digest": new_claims["record_digest"],
                                                   "trace_digest": new_trace["record_digest"]})
        self.reroot(root, retention)
        with self.assertRaises(ContractViolation):
            bundle.validate(root, retention, REPO)
    def test_second_status_overlay_or_divergent_copy_rejects(self):
        root, retention = self.copy_bundle()
        status = canonical.loads((root / "authority/current-status.json").read_bytes())
        self.rewrite(root, "authority/current-status-overlay.json", {**status, "updated_at": "2099-01-01T00:00:00.000000Z"})
        self.reroot(root, retention)
        with self.assertRaises(ContractViolation):
            bundle.validate(root, retention, REPO)
        root, retention = self.copy_bundle()
        self.rewrite(root, "authority/current-status.json", {**status, "updated_at": "2099-01-01T00:00:00.000000Z"})
        self.reroot(root, retention)
        with self.assertRaises(ContractViolation):
            bundle.validate(root, retention, REPO)

    def test_second_claims_trace_or_decision_record_rejects(self):
        for source, duplicate in (("claims.json", "zz-claims-overlay.json"),
                                  ("requirement-trace.json", "zz-trace-overlay.json"),
                                  ("phase-decision.json", "zz-decision-overlay.json")):
            with self.subTest(source=source):
                root, retention = self.copy_bundle()
                record = canonical.loads((root / source).read_bytes())
                self.rewrite(root, duplicate, {**record, "created_at": "2099-01-01T00:00:00.000000Z"})
                self.reroot(root, retention)
                with self.assertRaises(ContractViolation):
                    bundle.validate(root, retention, REPO)

    def test_test_inventory_parser_reads_unittest_verbose_output(self):
        text = ("test_a (mod.Class.test_a) ... ok\ntest_b (mod.Class.test_b) ... FAIL\n"
                "test_c (mod.Class.test_c) ... skipped 'x'\n\n=====\nFAIL: test_b (mod.Class.test_b)\n")
        self.assertEqual(bundle.parse_test_inventory(text), [
            {"outcome": "passed", "test_id": "mod.Class.test_a"}, {"outcome": "failed", "test_id": "mod.Class.test_b"},
            {"outcome": "skipped", "test_id": "mod.Class.test_c"}])


class FreshCloneTests(unittest.TestCase):
    def test_fresh_clone_contains_governing_contract(self):
        tracked = subprocess.run(["git", "ls-files", "docs/phase1"], cwd=REPO, capture_output=True, text=True,
                                 check=True).stdout.split()
        self.assertEqual(sorted(tracked), sorted(f"docs/phase1/{p.name}" for p in (REPO / "docs/phase1").iterdir()))
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(os.path.realpath(tmp)) / "clone"
            subprocess.run(["git", "clone", "-q", "--no-hardlinks", str(REPO), str(fresh)], check=True, capture_output=True)
            head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True, check=True).stdout.strip()
            subprocess.run(["git", "checkout", "-q", head], cwd=fresh, check=True, capture_output=True)
            patch = evidence.canonical_patch(REPO)
            if patch:
                subprocess.run(["git", "apply", "--binary", "-"], cwd=fresh, input=patch, check=True, capture_output=True)
            from mmbu_phase1 import authority, contract_manifest
            self.assertEqual(contract_manifest.verify_contract_manifest(fresh), [])
            self.assertEqual(set(authority.load_authority(fresh)), set(authority.AUTHORITY_PATHS))
            for name in scope.REQUIRED_PHASE1_TEST_MODULES:
                self.assertTrue((fresh / "tests/phase1" / name).is_file(), name)
            self.assertEqual(evidence.build_inventory(fresh), evidence.build_inventory(REPO))

    def test_phase1_code_has_no_parent_workspace_or_chat_path_dependency(self):
        pattern = re.compile(r"/Users/|Documents/Codex|outputs/MMBU-|https-github-com-sathvikloke")
        for path in sorted((REPO / "src/mmbu_phase1").glob("*.py")) + [REPO / "tools/team.py"]:
            with self.subTest(path=path.name):
                self.assertIsNone(pattern.search(path.read_text(encoding="utf-8")), path)

    def test_b1_pin_forbids_floating_revisions(self):
        pin = json.loads((REPO / "docs/phase1/b1-pin.json").read_text(encoding="utf-8"))
        self.assertIs(pin["floating_revision_allowed"], False)
        self.assertIs(pin["trust_remote_code"], False)
        for key in ("model_revision", "processor_revision"):
            self.assertRegex(pin[key], r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
