"""Evidence-manifest root, external retention, and acyclic source state."""

import copy
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from mmbu_phase1 import canonical, evidence, fields
from mmbu_phase1.fields import ContractViolation

REPO = Path(__file__).resolve().parents[2]


def make_bundle(testcase):
    temp = tempfile.TemporaryDirectory()
    testcase.addCleanup(temp.cleanup)
    base = Path(os.path.realpath(temp.name))
    root = base / "bundle"
    (root / "records").mkdir(parents=True)
    record = canonical.seal({"schema_id": "mmbu.phase1.example_manifest", "schema_version": 1, "x": 1})
    (root / "records/example.json").write_bytes(canonical.dumps(record))
    (root / "logs").mkdir()
    (root / "logs/child.stdout").write_bytes(b"synthetic log\n")
    (root / "limitations.md").write_text("# Limits\n")
    manifest, digest = evidence.build_evidence_manifest(root, "bundle-1", fields.utc_now())
    receipt = evidence.retention_receipt("locator-1", "bundle-1", digest)
    return base, root, manifest, receipt


class EvidenceManifestTests(unittest.TestCase):
    def test_root_is_canonical_manifest_digest_and_never_self_lists(self):
        _, root, manifest, receipt = make_bundle(self)
        evidence.verify_bundle_root(root, receipt)
        raw = (root / evidence.MANIFEST_NAME).read_bytes()
        self.assertEqual(canonical.raw_digest(raw), receipt["root_sha256"])
        self.assertEqual(canonical.loads_canonical(raw), manifest)
        self.assertNotIn(evidence.MANIFEST_NAME, [m["path"] for m in manifest["members"]])
        self.assertEqual([m["path"] for m in manifest["members"]], ["limitations.md", "logs/child.stdout", "records/example.json"])
        by_path = {m["path"]: m for m in manifest["members"]}
        self.assertEqual(by_path["records/example.json"]["schema_id"], "mmbu.phase1.example_manifest")
        self.assertIsNone(by_path["logs/child.stdout"]["schema_id"])

    def test_evidence_bundle_root_detects_deletion_and_replacement(self):
        cases = {
            "deletion": lambda root: (root / "logs/child.stdout").unlink(),
            "replacement": lambda root: (root / "limitations.md").write_text("# Other\n"),
            "same_size_replacement": lambda root: (root / "limitations.md").write_text("# Limitz\n"),
            "addition": lambda root: (root / "extra.txt").write_text("x"),
            "rename": lambda root: (root / "limitations.md").rename(root / "limitation.md"),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                _, root, _, receipt = make_bundle(self)
                mutate(root)
                with self.assertRaises(ContractViolation):
                    evidence.verify_bundle_root(root, receipt)

    def test_reordered_or_rewritten_manifest_changes_the_root(self):
        _, root, manifest, receipt = make_bundle(self)
        target = root / evidence.MANIFEST_NAME
        os.chmod(target, 0o644)
        reordered = copy.deepcopy(manifest)
        reordered["members"].reverse()
        target.write_bytes(canonical.dumps(reordered))
        with self.assertRaises(ContractViolation):
            evidence.verify_bundle_root(root, receipt)
        target.write_bytes(canonical.dumps(manifest))
        evidence.verify_bundle_root(root, receipt)
        with self.assertRaises(ContractViolation):
            evidence.verify_bundle_root(root, {**receipt, "root_sha256": "0" * 64})
        with self.assertRaises(ContractViolation):
            evidence.verify_bundle_root(root, {**receipt, "bundle_id": "other"})

    def test_evidence_manifest_rejects_alias_traversal_symlink_and_collision(self):
        _, root, manifest, _ = make_bundle(self)
        member = manifest["members"][0]
        for bad_path in ("../escape.txt", "/abs.txt", "a//b", "./a", "logs\\x", "é.md"):
            with self.subTest(path=bad_path):
                broken = copy.deepcopy(manifest)
                broken["members"] = sorted(broken["members"] + [{**member, "path": bad_path}], key=lambda m: m["path"].encode())
                with self.assertRaises(ContractViolation):
                    evidence.validate_evidence_manifest_record(broken)
        collision = copy.deepcopy(manifest)
        collision["members"] = sorted(collision["members"] + [{**member, "path": "Limitations.md"}],
                                      key=lambda m: m["path"].encode())
        with self.assertRaises(ContractViolation):
            evidence.validate_evidence_manifest_record(collision)
        self_entry = copy.deepcopy(manifest)
        self_entry["members"] = sorted(self_entry["members"] + [{**member, "path": "evidence-manifest.json"}],
                                       key=lambda m: m["path"].encode())
        with self.assertRaises(ContractViolation):
            evidence.validate_evidence_manifest_record(self_entry)
        half = copy.deepcopy(manifest)
        half["members"][0]["schema_id"] = "mmbu.phase1.x"
        with self.assertRaises(ContractViolation):
            evidence.validate_evidence_manifest_record(half)
        for name, make in (("symlink", lambda r: (r / "link.md").symlink_to(r / "limitations.md")),
                           ("hard_link", lambda r: os.link(r / "limitations.md", r / "alias.md")),
                           ("fifo", lambda r: os.mkfifo(r / "pipe"))):
            with self.subTest(member=name):
                base = Path(os.path.realpath(tempfile.mkdtemp()))
                self.addCleanup(shutil.rmtree, base, True)
                (base / "limitations.md").write_text("x")
                make(base)
                with self.assertRaises(ContractViolation):
                    evidence.build_evidence_manifest(base, "b", fields.utc_now())

    def test_retention_receipt_is_closed_and_external(self):
        _, root, _, receipt = make_bundle(self)
        with self.assertRaises(ContractViolation):
            evidence.validate_retention_receipt({**receipt, "extra": 1})
        os.chmod(root / evidence.MANIFEST_NAME, 0o644)
        (root / "receipt.json").write_bytes(canonical.dumps(receipt))
        with self.assertRaises(ContractViolation):
            evidence.verify_bundle_root(root, receipt)


class SourceStateTests(unittest.TestCase):
    def clone(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(os.path.realpath(temp.name)) / "repo"
        root.mkdir()
        for relative in ("src/mmbu_phase1", "tests/phase1", "docs/phase1", "tools"):
            (root / relative).mkdir(parents=True)
        (root / "src/mmbu_phase1/a.py").write_text("A = 1\n")
        (root / "tests/phase1/test_a.py").write_text("pass\n")
        (root / "docs/phase1/contract-manifest.json").write_text("{}\n")
        (root / "tools/team.py").write_text("# team\n")
        (root / "config/phase1").mkdir(parents=True)
        (root / "config/phase1/current-status.json").write_text("{}")
        run = lambda *a: subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)  # noqa: E731
        run("init", "-q")
        run("add", "-A")
        run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")
        return root

    def test_clean_state_has_null_patch_and_excludes_mutable_authority(self):
        root = self.clone()
        (root / "config/phase1/immutable-runtime.json").write_text("{}\n")
        subprocess.run(["git", "add", "config/phase1/immutable-runtime.json"], cwd=root, check=True, capture_output=True)
        subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "config"],
                       cwd=root, check=True, capture_output=True)
        record, patch = evidence.build_source_state(root, fields.utc_now())
        self.assertFalse(record["dirty"])
        self.assertIsNone(record["patch_sha256"])
        self.assertEqual(patch, b"")
        paths = [row["path"] for row in record["inventory"]]
        self.assertNotIn("config/phase1/current-status.json", paths)
        self.assertIn("config/phase1/immutable-runtime.json", paths)
        self.assertEqual({row["class"] for row in record["inventory"]}, {"source", "test", "contract", "config"})
        evidence.check_source_state(record, root)
        with self.assertRaises(ContractViolation):
            evidence.validate_source_state(canonical.seal({**record, "inventory": record["inventory"] + [
                {"path": "config/phase1/current-status.json", "bytes": 2, "sha256": "0" * 64, "class": "config"}]}))

    def test_source_state_detects_dirty_or_post_evidence_drift(self):
        root = self.clone()
        clean, _ = evidence.build_source_state(root, fields.utc_now())
        (root / "src/mmbu_phase1/a.py").write_text("A = 2\n")
        with self.assertRaises(ContractViolation):
            evidence.check_source_state(clean, root)
        dirty, patch = evidence.build_source_state(root, fields.utc_now())
        self.assertTrue(dirty["dirty"])
        self.assertEqual(dirty["patch_sha256"], canonical.raw_digest(patch))
        evidence.check_source_state(dirty, root, patch)
        lie = canonical.seal({**dirty, "dirty": False, "patch_sha256": None})
        with self.assertRaises(ContractViolation):
            evidence.check_source_state(lie, root)
        with self.assertRaises(ContractViolation):
            evidence.check_source_state(dirty, root, patch + b"x")
        (root / "tests/phase1/test_new.py").write_text("pass\n")
        with self.assertRaises(ContractViolation):
            evidence.check_source_state(dirty, root, patch)
        untracked, untracked_patch = evidence.build_source_state(root, fields.utc_now())
        self.assertIn(b"tests/phase1/test_new.py", untracked_patch)
        omitted = canonical.seal({**untracked, "inventory": [r for r in untracked["inventory"]
                                                              if r["path"] != "tests/phase1/test_new.py"]})
        with self.assertRaises(ContractViolation):
            evidence.check_source_state(omitted, root, untracked_patch)

    def test_canonical_patch_reproduces_tracked_and_untracked_changes(self):
        root = self.clone()
        (root / "src/mmbu_phase1/a.py").write_text("A = 3\n")
        (root / "src/mmbu_phase1/b.py").write_bytes(b"\x00binary\xff")
        record, patch = evidence.build_source_state(root, fields.utc_now())
        fresh = root.parent / "fresh"
        subprocess.run(["git", "clone", "-q", str(root), str(fresh)], check=True, capture_output=True)
        subprocess.run(["git", "apply", "--binary", "-"], cwd=fresh, input=patch, check=True, capture_output=True)
        self.assertEqual(evidence.build_inventory(fresh), record["inventory"])


if __name__ == "__main__":
    unittest.main()
