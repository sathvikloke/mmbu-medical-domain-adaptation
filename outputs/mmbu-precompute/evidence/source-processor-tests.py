"""Focused offline safeguards for the source processor engineering probe."""
from contextlib import redirect_stderr
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import source_processor_probe as probe


class SourceProcessorSafeguards(unittest.TestCase):
    def test_percentiles_use_type7_and_totals_include_each_observation_once(self):
        result = probe.summarize([9, 1, 5, 3])
        self.assertEqual((result["n"], result["min"], result["max"], result["total"]), (4, 1, 9, 18))
        self.assertEqual(result["mean"], 4.5)
        self.assertEqual(result["p50"], 4)
        self.assertAlmostEqual(result["p90"], 7.8)
        self.assertAlmostEqual(result["p95"], 8.4)
        self.assertIsNone(probe.summarize([]))

    def test_strict_json_rejects_duplicates_constants_and_exponent_overflow(self):
        for text in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}',
                     '{"a":-Infinity}', '{"a":[1e999]}', '{"a":-1e999}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                probe.strict_json(text)
        self.assertEqual(probe.strict_json('{"a":1e300}'), {"a": 1e300})

    def test_bounded_read_consumes_only_limit_plus_one(self):
        stream = Mock()
        stream.read.return_value = b"abcde"
        context = Mock()
        context.__enter__ = Mock(return_value=stream)
        context.__exit__ = Mock(return_value=False)
        path = Mock()
        path.open.return_value = context
        with self.assertRaisesRegex(ValueError, "byte bound"):
            probe.bounded_read(path, limit=4)
        stream.read.assert_called_once_with(5)

    def test_bounded_read_accepts_exact_bound(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bytes"
            path.write_bytes(b"abcd")
            self.assertEqual(probe.bounded_read(path, limit=4), b"abcd")
            path.write_bytes(b"abcde")
            with self.assertRaises(ValueError):
                probe.bounded_read(path, limit=4)

    def test_network_entry_points_fail_before_connection(self):
        with probe.denied_network() as attempts:
            with self.assertRaisesRegex(RuntimeError, "forbidden"):
                socket.create_connection(("this-name-is-never-resolved.invalid", 443))
            with self.assertRaisesRegex(RuntimeError, "forbidden"):
                socket.getaddrinfo("this-name-is-never-resolved.invalid", 443)
            self.assertEqual(len(attempts), 2)

    def test_existing_output_is_preserved_before_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            output.write_bytes(b"original")
            with patch.object(probe, "run", side_effect=AssertionError("must not run")), redirect_stderr(io.StringIO()):
                code = probe.main(["--manifest", "absent", "--image-root", "absent",
                                   "--artifacts", "absent", "--output", str(output)])
            self.assertEqual(code, 2)
            self.assertEqual(output.read_bytes(), b"original")

    def test_missing_dependency_returns_two_without_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            with patch.object(probe, "run", side_effect=ImportError("synthetic missing dependency")), redirect_stderr(io.StringIO()) as errors:
                code = probe.main(["--manifest", "absent", "--image-root", "absent",
                                   "--artifacts", "absent", "--output", str(output)])
            self.assertEqual(code, 2)
            self.assertFalse(output.exists())
            self.assertEqual(json.loads(errors.getvalue())["error_type"], "ImportError")

    def rejection_fixture(self, mode="RGB", wrong_hash=False, pending=True):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            png = root / "sample.png"
            Image.new(mode, (40, 32)).save(png)
            row = {"record_id": "sample", "source_id": "synthetic", "split": "engineering",
                   "image_path": "sample.png", "image_sha256": "0" * 64 if wrong_hash else probe.sha256(png.read_bytes()),
                   "image_width": 40, "image_height": 32,
                   "review_status": "pending" if pending else "approved", "allowed_purposes": []}
            manifest = root / "manifest.jsonl"
            manifest.write_text(json.dumps(row) + "\n")
            args = SimpleNamespace(manifest=manifest, image_root=root, registry=root / "absent-registry.json",
                                   artifacts=root / "absent-cache", expected_records=1, include_common_bound=False)
            with patch.object(probe.helpers, "artifacts", side_effect=AssertionError("must not load processors")):
                probe.run(args)

    def test_wrong_image_hash_rejected_before_processor_loading(self):
        with self.assertRaisesRegex(ValueError, "image_hash_mismatch"):
            self.rejection_fixture(wrong_hash=True)

    def test_non_rgb_rejected_before_processor_loading(self):
        with self.assertRaisesRegex(ValueError, "RGB PNG"):
            self.rejection_fixture(mode="L")

    def test_approved_record_rejected_before_processor_loading(self):
        with self.assertRaisesRegex(ValueError, "pending rows"):
            self.rejection_fixture(pending=False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
