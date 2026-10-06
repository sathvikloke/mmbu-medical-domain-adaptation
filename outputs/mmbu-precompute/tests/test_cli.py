import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "mmbu_prep", *args], cwd=ROOT,
                              env=env, text=True, capture_output=True, timeout=20)

    def test_missing_input_is_actionable_nonzero_without_traceback(self):
        result = self.run_cli("score", "does-not-exist.jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))
        self.assertNotIn("Traceback", result.stderr)

    def test_arithmetic_command_retains_failed_predictions(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "grades.jsonl"
            p.write_text(json.dumps({"record_id": "a", "source_id": "s", "group_id": "g", "task": "global_classification", "base_correct": 1, "adapted_correct": 0, "context_correct": {"modality": 1}}) + "\n")
            result = self.run_cli("score", str(p))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["score"]["S"], -.2)
            self.assertFalse(payload["official_evaluation"])

    def test_duplicate_json_keys_and_nonfinite_values_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "invalid.jsonl"
            for raw in ['{"record_id":"a","record_id":"b"}', '{"value":NaN}', '{"record_id":"a","source_id":"s","group_id":"g","task":"global_classification","base_correct":0,"adapted_correct":1,"context_correct":{"modality":1},"unused":1e999}']:
                p.write_text(raw + "\n")
                result = self.run_cli("score", str(p))
                self.assertEqual(result.returncode, 2)
                self.assertIn("error", json.loads(result.stderr))

    def test_demo_is_engineering_only_and_does_not_train(self):
        result = self.run_cli("demo")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["manifest"]["ok"])
        self.assertEqual(payload["kind"], "synthetic_engineering_demo")
        self.assertFalse(payload["official_evaluation"])
        self.assertFalse(payload["model_executed"])

    def test_status_keeps_protocol_and_gpu_unresolved(self):
        result = self.run_cli("status")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["protocol_status"], "unresolved")
        self.assertFalse(payload["training_ready"])
        self.assertEqual(payload["gpu"]["status"], "it_followup_pending")

    def test_unapproved_real_source_returns_structured_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "records.json"
            records = [json.loads(line) for line in (ROOT / "examples/engineering-manifest.jsonl").read_text().splitlines()]
            records[0]["source_id"] = "bbbc039"
            p.write_text(json.dumps(records))
            result = self.run_cli("validate", str(p))
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["ok"])

    def test_split_refuses_to_overwrite_existing_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            registry = {"schema_version": 1, "sources": [{"source_id": "test-only-external", "source_version": "1", "source_family": "test-only", "source_role": "external", "status": "approved", "allowed_purposes": ["train", "dev", "confirmation"], "evidence": ["Synthetic permission fixture for software test; not real data approval"], "reviewed_by": "test", "reviewed_at": "2026-10-03"}]}
            record = {"schema_version": 1, "record_id": "a", "source_id": "test-only-external", "source_version": "1", "source_family": "test-only", "split": "train", "image_path": "a.pgm", "image_sha256": "1" * 64, "parent_image_sha256": None, "group_id": "g", "task": "global_classification", "question": "Test?", "answer": "fixture", "context": {}, "annotation_origin": "software_test", "conversion_version": "1", "review_status": "approved", "synthetic": False}
            (directory / "registry.json").write_text(json.dumps(registry))
            (directory / "records.json").write_text(json.dumps([record]))
            output = directory / "frozen.jsonl"
            output.write_text("existing frozen contents\n")
            result = self.run_cli("split", str(directory / "records.json"), "--registry", str(directory / "registry.json"), "--ratios", '{"train":1}', "--seed", "4", "--output", str(output))
            self.assertEqual(result.returncode, 2)
            self.assertEqual(output.read_text(), "existing frozen contents\n")

    def test_dev_only_split_does_not_require_training_permission(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            registry = {"schema_version": 1, "sources": [{"source_id": "test-dev-only", "source_version": "1", "source_family": "test-only", "source_role": "external", "status": "approved", "allowed_purposes": ["dev"], "evidence": ["Software permission fixture only"], "reviewed_by": "test", "reviewed_at": "2026-10-03"}]}
            record = {"schema_version": 1, "record_id": "a", "source_id": "test-dev-only", "source_version": "1", "source_family": "test-only", "split": "dev", "image_path": "a.pgm", "image_sha256": "1" * 64, "parent_image_sha256": None, "group_id": "g", "task": "global_classification", "question": "Test?", "answer": "fixture", "context": {}, "annotation_origin": "software_test", "conversion_version": "1", "review_status": "approved", "synthetic": False}
            (directory / "registry.json").write_text(json.dumps(registry))
            (directory / "records.json").write_text(json.dumps([record]))
            output = directory / "assigned.jsonl"
            result = self.run_cli("split", str(directory / "records.json"), "--registry", str(directory / "registry.json"), "--ratios", '{"dev":1}', "--seed", "4", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertEqual(json.loads(output.read_text())["split"], "dev")

    def test_training_preflight_rejects_a_confirmation_record(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            registry = {"schema_version": 1, "sources": [{"source_id": "test-heldout", "source_version": "1", "source_family": "test-only", "source_role": "external", "status": "approved", "allowed_purposes": ["train", "confirmation"], "evidence": ["Software fixture only"], "reviewed_by": "test", "reviewed_at": "2026-10-03"}]}
            record = {"schema_version": 1, "record_id": "a", "source_id": "test-heldout", "source_version": "1", "source_family": "test-only", "split": "confirmation", "image_path": "a.pgm", "image_sha256": "1" * 64, "parent_image_sha256": None, "group_id": "g", "task": "global_classification", "question": "Test?", "answer": "fixture", "context": {}, "annotation_origin": "software_test", "conversion_version": "1", "review_status": "approved", "synthetic": False}
            (directory / "registry.json").write_text(json.dumps(registry))
            (directory / "records.json").write_text(json.dumps([record]))
            result = self.run_cli("validate", str(directory / "records.json"), "--registry", str(directory / "registry.json"), "--purpose", "train")
            self.assertEqual(result.returncode, 2)
            self.assertFalse(json.loads(result.stdout)["ok"])

    def test_approved_engineering_intake_can_get_initial_training_split(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            registry = {"schema_version": 1, "sources": [{"source_id": "test-intake", "source_version": "1", "source_family": "test-only", "source_role": "external", "status": "approved", "allowed_purposes": ["engineering", "train"], "evidence": ["Software fixture only"], "reviewed_by": "test", "reviewed_at": "2026-10-03"}]}
            record = {"schema_version": 1, "record_id": "a", "source_id": "test-intake", "source_version": "1", "source_family": "test-only", "split": "engineering", "image_path": "a.pgm", "image_sha256": "1" * 64, "parent_image_sha256": None, "group_id": "g", "task": "global_classification", "question": "Test?", "answer": "fixture", "context": {}, "annotation_origin": "software_test", "conversion_version": "1", "review_status": "approved", "synthetic": False}
            (directory / "registry.json").write_text(json.dumps(registry))
            (directory / "records.json").write_text(json.dumps([record]))
            output = directory / "assigned.jsonl"
            result = self.run_cli("split", str(directory / "records.json"), "--registry", str(directory / "registry.json"), "--ratios", '{"train":1}', "--seed", "4", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(output.read_text())["split"], "train")


if __name__ == "__main__":
    unittest.main()
