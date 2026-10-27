"""Synthetic conformance tests for the offline BUS-BRA train review UI."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from mmbu_phase1.busbra_train_qa import VISUAL_FIELDS, build_train_qa_packet
from mmbu_phase1.busbra_train_review_ui import build_review_ui

from tests.phase1 import test_busbra_train_qa as train_qa_tests


PNG = b"\x89PNG\r\n\x1a\nsynthetic-review-fixture"


class BusbraTrainReviewUiTests(unittest.TestCase):
    def setUp(self):
        train_qa_tests.BusbraTrainQaBuildTests.setUp(self)
        self.packet = self.root / "train-qa"
        self.receipt = build_train_qa_packet(self.predecessor, self.packet)
        for path in self.packet.glob("assets/*/*.png"):
            path.write_bytes(PNG + path.as_posix().encode("utf-8"))
        self._reseal()
        self.output = self.root / "review.html"

    def tearDown(self):
        self.temp.cleanup()

    def _reseal(self) -> None:
        receipt_path = self.packet / "packet-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["members"] = []
        for path in sorted(
            (path for path in self.packet.rglob("*")
             if path.is_file() and path != receipt_path),
            key=lambda path: path.relative_to(self.packet).as_posix().encode(),
        ):
            payload = path.read_bytes()
            receipt["members"].append({
                "path": path.relative_to(self.packet).as_posix(),
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            })
        manifest = json.loads((self.packet / "train-qa-manifest.json").read_text())
        receipt["manifest_digest"] = manifest["manifest_digest"]
        receipt.pop("receipt_digest", None)
        receipt["receipt_digest"] = train_qa_tests.canonical_digest(receipt)
        receipt_path.write_text(json.dumps(receipt, sort_keys=True) + "\n", encoding="utf-8")
        self.receipt = receipt

    def _rewrite_manifest(self, mutate) -> None:
        path = self.packet / "train-qa-manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest.pop("manifest_digest")
        mutate(manifest)
        manifest["manifest_digest"] = train_qa_tests.canonical_digest(manifest)
        path.write_text(json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8")
        self._reseal()

    def test_builds_verified_self_contained_offline_reviewer(self):
        result = build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        payload = self.output.read_text(encoding="utf-8")

        self.assertEqual(result["schema"], "mmbu.busbra.train_review_ui_receipt.v1")
        self.assertEqual(result["packet_receipt_digest"], self.receipt["receipt_digest"])
        self.assertEqual(result["record_count"], self.receipt["record_count"])
        self.assertEqual(result["output_sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertFalse(result["review_complete"])
        self.assertFalse(result["source_admission_authorized"])
        self.assertFalse(result["training_ready"])
        self.assertFalse(result["model_use_authorized"])
        self.assertIn("default-src 'none'", payload)
        self.assertIn("img-src data:", payload)
        self.assertNotIn("http://", payload)
        self.assertNotIn("https://", payload)
        self.assertIn("data:image/png;base64,", payload)
        self.assertIn("bus_0001-l", payload)
        self.assertIn("mmbu.busbra.train_review_draft.v1", payload)
        self.assertIn(json.dumps(list(VISUAL_FIELDS), separators=(",", ":")), payload)
        self.assertIn("receiptDigest", payload)
        self.assertIn("validateDraft", payload)
        self.assertIn("validateForExport", payload)
        self.assertIn("needsNotes", payload)
        self.assertIn("exportCsv", payload)
        self.assertIn("No source admission, training, model-use, release, upload, or submission authority", payload)

    def test_escapes_frozen_values_before_embedding_in_html(self):
        attack = "</script><script>globalThis.pwned=true</script>"
        self._rewrite_manifest(lambda manifest: manifest["records"][0].update(pathology=attack))

        build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        payload = self.output.read_text(encoding="utf-8")

        self.assertNotIn(attack, payload)
        self.assertNotIn("<script>globalThis.pwned", payload)
        self.assertIn("\\u003c/script\\u003e", payload)

    def test_rejects_wrong_receipt_before_writing_output(self):
        with self.assertRaisesRegex(ValueError, "receipt digest mismatch"):
            build_review_ui(self.packet, "0" * 64, self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_symlinked_asset_before_writing_output(self):
        image = next(self.packet.glob("assets/*/image.png"))
        target = self.root / "outside.png"
        target.write_bytes(image.read_bytes())
        image.unlink()
        image.symlink_to(target)

        with self.assertRaisesRegex(ValueError, "symbolic link"):
            build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        self.assertFalse(self.output.exists())

    def test_rejects_receipt_bound_non_png_asset(self):
        image = next(self.packet.glob("assets/*/image.png"))
        image.write_bytes(b"not a PNG")
        self._reseal()

        with self.assertRaisesRegex(ValueError, "PNG signature"):
            build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        self.assertFalse(self.output.exists())

    def test_refuses_to_overwrite_existing_output(self):
        self.output.write_text("competitor", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "competitor")

    def test_output_created_during_publish_wins_race(self):
        real_link = __import__("os").link

        def competitor_wins(source, destination, *, follow_symlinks=False):
            Path(destination).write_text("competitor", encoding="utf-8")
            return real_link(source, destination, follow_symlinks=follow_symlinks)

        with mock.patch(
            "mmbu_phase1.busbra_train_review_ui.os.link", side_effect=competitor_wins,
        ):
            with self.assertRaises(FileExistsError):
                build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "competitor")

    def test_embeds_closed_validator_vocabularies_and_guards(self):
        build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        payload = self.output.read_text(encoding="utf-8")

        for value in (
            "uncertain", "overlay", "caliper", "crop", "text", "panel", "other",
            "pathology_classification", "birads_classification", "mask_context",
            "eligible", "exclude", "escalate",
        ):
            self.assertIn(value, payload)
        self.assertIn("Foreign or incomplete draft", payload)
        self.assertIn("Notes are required", payload)
        self.assertIn("Eligible records require at least one training target", payload)
        self.assertIn("Excluded records may not retain training targets", payload)
        self.assertIn("Invalid closed-vocabulary value", payload)
        self.assertIn("Eligible records require usable image and modality evidence", payload)

    @unittest.skipUnless(shutil.which("node"), "Node.js is optional")
    def test_embedded_javascript_is_syntactically_valid(self):
        build_review_ui(self.packet, self.receipt["receipt_digest"], self.output)
        payload = self.output.read_text(encoding="utf-8")
        scripts = re.findall(r'<script(?: [^>]*)?>(.*?)</script>', payload, flags=re.DOTALL)
        self.assertEqual(len(scripts), 2)
        script = self.root / "review-ui.js"
        script.write_text(scripts[1], encoding="utf-8")
        result = subprocess.run(
            [shutil.which("node"), "--check", str(script)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
