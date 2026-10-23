"""Behavior checks for the repository helper; no package installation required."""

import importlib.util
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("team", REPO / "tools/team.py")
team = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(team)


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.file = self.root / "sample.txt"
        self.file.write_bytes(b"abc")
        self.receipt = {
            "bytes": 3,
            "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        }

    def test_valid_bytes_are_accepted(self):
        self.assertEqual(team.verify_file(self.root, "sample.txt", self.receipt), [])

    def test_same_size_tampering_is_rejected(self):
        self.file.write_bytes(b"abd")
        self.assertIn("SHA-256", "\n".join(team.verify_file(self.root, "sample.txt", self.receipt)))

    def test_truncation_is_rejected(self):
        self.file.write_bytes(b"ab")
        self.assertIn("size", "\n".join(team.verify_file(self.root, "sample.txt", self.receipt)))

    def test_symlink_is_not_accepted_as_historical_file(self):
        (self.root / "alias.txt").symlink_to(self.file)
        self.assertTrue(team.verify_file(self.root, "alias.txt", self.receipt))

    def test_manifest_detects_addition_and_missing_file(self):
        manifest = {"sample.txt": self.receipt}
        self.assertEqual(team.verify_manifest(self.root, manifest), [])
        (self.root / "unrecorded.txt").write_text("unrecorded")
        self.file.unlink()
        errors = "\n".join(team.verify_manifest(self.root, manifest))
        self.assertIn("unrecorded.txt", errors)
        self.assertIn("sample.txt", errors)

    def test_manifest_ignores_only_generated_python_cache(self):
        cache = self.root / "__pycache__"
        cache.mkdir()
        (cache / "sample.cpython-312.pyc").write_bytes(b"generated")
        self.assertEqual(team.verify_manifest(self.root, {"sample.txt": self.receipt}), [])
        (cache / "hidden-evidence.json").write_text("{}")
        self.assertTrue(team.verify_manifest(self.root, {"sample.txt": self.receipt}))

    def test_path_outside_bundle_is_rejected(self):
        self.assertTrue(team.verify_file(self.root, "../sample.txt", self.receipt))


class PublicationIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.record = json.loads((REPO / "research/publication-redactions.json").read_text())

    def test_published_snapshot_and_original_receipts_verify_together(self):
        self.assertEqual(team.verify_evidence(REPO), [])

    def test_extra_transformation_is_not_an_escape_hatch(self):
        extra = copy.deepcopy(self.record["transformations"][0])
        extra["path"] = "outputs/mmbu-precompute/README.md"
        self.record["transformations"].append(extra)
        self.assertTrue(team.verify_publication_record(self.record))

    def test_duplicate_transformation_is_rejected(self):
        self.record["transformations"][1] = self.record["transformations"][0]
        self.assertTrue(team.verify_publication_record(self.record))

    def test_receipt_cannot_choose_a_new_published_hash(self):
        self.record["transformations"][0]["published_sha256"] = "0" * 64
        self.assertTrue(team.verify_publication_record(self.record))

    def test_receipt_cannot_rewrite_the_original_hash(self):
        self.record["transformations"][0]["original_sha256"] = "0" * 64
        self.assertTrue(team.verify_publication_record(self.record))

    def test_only_source_expansion_manifest_entry_can_change(self):
        original = json.loads((REPO / "research/original-bundle-manifest-v0.3.json").read_text())
        published = json.loads((REPO / "outputs/mmbu-precompute/evidence/bundle-manifest.json").read_text())
        self.assertEqual(team.verify_published_manifest(original, published), [])
        published["files"]["README.md"]["sha256"] = "0" * 64
        self.assertTrue(team.verify_published_manifest(original, published))

    def test_zip_rejects_changed_extra_and_duplicate_members(self):
        entries = {"sample.txt": {"bytes": 3, "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}}
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "fixture.zip"
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("mmbu-precompute/sample.txt", b"abc")
            self.assertEqual(team.verify_zip(archive, entries), [])
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("mmbu-precompute/sample.txt", b"abd")
            self.assertIn("SHA-256", "\n".join(team.verify_zip(archive, entries)))
            with zipfile.ZipFile(archive, "a") as bundle:
                bundle.writestr("mmbu-precompute/extra.txt", b"x")
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    bundle.writestr("mmbu-precompute/sample.txt", b"abc")
            errors = "\n".join(team.verify_zip(archive, entries))
            self.assertIn("extra.txt", errors)
            self.assertIn("duplicate", errors)


class LinkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "docs/team").mkdir(parents=True)

    def write(self, path, text):
        (self.root / path).write_text(text, encoding="utf-8")

    def test_broken_path_and_anchor_are_reported(self):
        self.write("README.md", "# Read me\n[Missing](missing.md)\n[Bad anchor](#absent)\n")
        errors = "\n".join(team.verify_links(self.root))
        self.assertIn("missing.md", errors)
        self.assertIn("#absent", errors)

    def test_relative_links_encoded_spaces_and_duplicate_headings(self):
        self.write("README.md", "# Intro\n[Guide](docs/team/Guide%20One.md#setup-1)\n")
        self.write("docs/team/Guide One.md", "# Setup\n# Setup\n[Home](../../README.md#intro)\n")
        self.assertEqual(team.verify_links(self.root), [])

    def test_reference_links_and_explicit_html_anchor(self):
        self.write("README.md", '[Guide][guide]\n[guide]: docs/team/guide.md#start "Title"\n')
        self.write("docs/team/guide.md", '<a id="start"></a>\n# Guide\n')
        self.assertEqual(team.verify_links(self.root), [])
        self.write("docs/team/guide.md", "# Guide\n")
        self.assertTrue(team.verify_links(self.root))

    def test_examples_and_external_urls_are_not_fetched(self):
        self.write("README.md", "# Read me\n```md\n[Example](missing.md)\n```\n"
                   "`[Example](also-missing.md)`\n[External](https://invalid.example/a#b)\n")
        self.assertEqual(team.verify_links(self.root), [])

    def test_historical_markdown_is_not_scanned(self):
        (self.root / "outputs").mkdir()
        self.write("outputs/history.md", "[Old workspace](/old/absolute/path)\n")
        self.write("README.md", "[History](outputs/history.md)\n")
        self.assertEqual(team.verify_links(self.root), [])

    def test_outside_repository_link_is_rejected(self):
        self.write("README.md", "[Outside](../outside.md)\n")
        self.assertTrue(team.verify_links(self.root))

    def test_inline_code_in_heading_contributes_to_anchor(self):
        self.write("README.md", "# Run `test` now\n[Jump](#run-test-now)\n")
        self.assertEqual(team.verify_links(self.root), [])

    def test_symlink_cache_cannot_hide_an_unrecorded_file(self):
        cache = self.root / "__pycache__"
        cache.mkdir()
        self.write("README.md", "# Root\n")
        (cache / "hidden.pyc").symlink_to(self.root / "README.md")
        errors = team.verify_manifest(self.root, {})
        self.assertIn("__pycache__/hidden.pyc", "\n".join(errors))


class HandoffPacketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "config").mkdir()
        (self.root / "docs/team").mkdir(parents=True)
        self.member = self.root / "docs/team/member.md"
        self.member.write_bytes(b"abc")

    def write_packet(self, approval_status="pending_human_digest_acknowledgement"):
        member = {
            "bytes": 3,
            "media_type": "text/markdown; charset=utf-8",
            "path": "docs/team/member.md",
            "role": "normative_dependency",
            "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        }
        unsigned = {
            "created_at_utc": "2026-10-18T00:00:00Z",
            "members": [member],
            "schema_id": "mmbu.claude_handoff_dependency_manifest",
            "schema_version": 1,
        }
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        manifest = dict(unsigned, canonical_digest=hashlib.sha256(canonical).hexdigest())
        manifest_bytes = (json.dumps(manifest, separators=(",", ":")) + "\n").encode()
        (self.root / "config/claude-handoff-dependencies.json").write_bytes(manifest_bytes)
        receipt = {
            "approval_status": approval_status,
            "approved_package_scope": [] if approval_status != "approved" else ["A"],
            "approving_authority_id": None if approval_status != "approved" else "human::fixture-reviewer",
            "manifest_canonical_digest": manifest["canonical_digest"],
            "manifest_file_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "manifest_member_count": 1,
            "manifest_path": "config/claude-handoff-dependencies.json",
            "note": "fixture",
            "schema_id": "mmbu.claude_handoff_launch_receipt",
            "schema_version": 1,
            "trusted_acknowledgement_digest": None if approval_status != "approved" else "1" * 64,
        }
        (self.root / "config/claude-handoff-launch-receipt.json").write_text(
            json.dumps(receipt) + "\n", encoding="utf-8"
        )

    def test_valid_packet_with_pending_receipt_is_verified_but_not_authorized(self):
        self.assertTrue(hasattr(team, "verify_handoff_packet"), "verify_handoff_packet API missing")
        self.write_packet()
        result = team.verify_handoff_packet(self.root, requested_package="A")
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["packet_valid"])
        self.assertFalse(result["launch_authorized"])
        self.assertEqual(result["launch_status"], "pending_human_digest_acknowledgement")

    def test_member_tampering_invalidates_packet_and_launch(self):
        self.assertTrue(hasattr(team, "verify_handoff_packet"), "verify_handoff_packet API missing")
        self.write_packet("approved")
        self.member.write_bytes(b"abd")
        result = team.verify_handoff_packet(self.root, requested_package="A")
        self.assertFalse(result["packet_valid"])
        self.assertFalse(result["launch_authorized"])
        self.assertIn("SHA-256", "\n".join(result["errors"]))

    def test_authorization_verifier_python_can_be_bound_in_packet(self):
        self.write_packet()
        verifier = self.root / "tools/team.py"
        verifier.parent.mkdir()
        verifier.write_bytes(b"# trusted verifier\n")
        manifest_path = self.root / "config/claude-handoff-dependencies.json"
        manifest = json.loads(manifest_path.read_text())
        raw = verifier.read_bytes()
        manifest["members"].append({
            "bytes": len(raw),
            "media_type": "text/x-python; charset=utf-8",
            "path": "tools/team.py",
            "role": "authorization_verifier",
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
        unsigned = dict(manifest)
        unsigned.pop("canonical_digest")
        manifest["canonical_digest"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        manifest_bytes = (json.dumps(manifest, separators=(",", ":")) + "\n").encode()
        manifest_path.write_bytes(manifest_bytes)
        receipt_path = self.root / "config/claude-handoff-launch-receipt.json"
        receipt = json.loads(receipt_path.read_text())
        receipt["manifest_canonical_digest"] = manifest["canonical_digest"]
        receipt["manifest_file_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
        receipt["manifest_member_count"] = 2
        receipt_path.write_text(json.dumps(receipt) + "\n")

        result = team.verify_handoff_packet(self.root, requested_package="A")

        self.assertEqual(result["errors"], [])
        self.assertTrue(result["packet_valid"])

    def test_exact_approved_receipt_authorizes_only_its_declared_scope(self):
        self.write_packet("approved")
        unanchored = team.verify_handoff_packet(self.root, requested_package="A")
        self.assertTrue(unanchored["packet_valid"])
        self.assertFalse(unanchored["launch_authorized"])

        result = team.verify_handoff_packet(
            self.root, requested_package="A", trusted_acknowledgement_digest="1" * 64
        )
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["packet_valid"])
        self.assertTrue(result["launch_authorized"])
        self.assertEqual(result["launch_status"], "approved")
        self.assertEqual(result["authorized_package_scope"], ["A"])

        for package in ("D", "F", "G", "I"):
            with self.subTest(package=package):
                denied = team.verify_handoff_packet(
                    self.root, requested_package=package, trusted_acknowledgement_digest="1" * 64
                )
                self.assertTrue(denied["packet_valid"])
                self.assertFalse(denied["launch_authorized"])

    def test_exact_approved_receipt_can_authorize_package_i(self):
        self.write_packet("approved")
        path = self.root / "config/claude-handoff-launch-receipt.json"
        receipt = json.loads(path.read_text())
        receipt["approved_package_scope"] = ["I"]
        path.write_text(json.dumps(receipt) + "\n")

        result = team.verify_handoff_packet(
            self.root, requested_package="I", trusted_acknowledgement_digest="1" * 64
        )

        self.assertEqual(result["errors"], [])
        self.assertTrue(result["packet_valid"])
        self.assertTrue(result["launch_authorized"])
        self.assertEqual(result["authorized_package_scope"], ["I"])

    def test_approved_receipt_rejects_unknown_duplicate_or_untrusted_scope(self):
        self.write_packet("approved")
        path = self.root / "config/claude-handoff-launch-receipt.json"
        receipt = json.loads(path.read_text())
        for scope in (["Z"], ["A", "A"]):
            with self.subTest(scope=scope):
                receipt["approved_package_scope"] = scope
                path.write_text(json.dumps(receipt) + "\n")
                result = team.verify_handoff_packet(self.root, requested_package="A")
                self.assertFalse(result["packet_valid"])
                self.assertFalse(result["launch_authorized"])
        receipt["approved_package_scope"] = ["A"]
        receipt["approving_authority_id"] = None
        receipt["trusted_acknowledgement_digest"] = None
        path.write_text(json.dumps(receipt) + "\n")
        result = team.verify_handoff_packet(self.root, requested_package="A")
        self.assertFalse(result["packet_valid"])
        self.assertFalse(result["launch_authorized"])


class ProcessTests(unittest.TestCase):
    def test_child_exit_code_is_preserved_and_later_commands_do_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "should-not-exist"
            result = team.run_commands([
                [sys.executable, "-c", "raise SystemExit(7)"],
                [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"],
            ], Path(tmp))
            self.assertEqual(result, 7)
            self.assertFalse(marker.exists())

    def test_empty_checkout_returns_nonzero_instead_of_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(REPO / "tools/team.py"), "--root", tmp, "verify-evidence"],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
