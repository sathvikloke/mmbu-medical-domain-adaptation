"""Provenance and receipt tests use local synthetic files; no model is run."""

import copy
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import tempfile
import unittest

try:
    experiments = importlib.import_module("mmbu_prep.experiments")
except ModuleNotFoundError:
    experiments = None


def fixture(root, purpose="confirmation"):
    directory = root / "inputs"
    directory.mkdir(exist_ok=True)
    names = ("baseline", "candidate", "protocol", "processor", "grading", "sources",
             "weights", "comparison", "execution", "code", "environment", "manifest", "selection")
    artifacts = {}
    for name in names:
        path = directory / (name + ".txt")
        path.write_text("synthetic " + name + "\n", encoding="utf-8")
        artifacts[name] = {"path": path.relative_to(root).as_posix(),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return {
        "schema_version": 1, "record_kind": "pre_run_experiment", "experiment_id": "toy-01",
        "owner": "fixture-owner", "created_at_utc": "2026-10-04T10:00:00Z", "purpose": purpose,
        "hypothesis": "Prespecified synthetic comparison; no scientific inference.",
        "baseline": {"model_id": "toy-base", "revision": "commit-base", "checkpoint_artifact": "baseline"},
        "candidate": {"model_id": "toy-adapter", "revision": "commit-candidate", "checkpoint_artifact": "candidate"},
        "seeds": {"training": 7, "inference": 8, "bootstrap": 9},
        "artifact_scope": ["inputs"], "artifacts": artifacts,
        "protocol": {"revision": "local-v1", "profile": "brief_json", "artifact": "protocol"},
        "processor": {"revision": "processor-commit", "artifact": "processor"},
        "grading": {"judge_model_id": "toy-judge", "judge_revision": "judge-commit", "policy_artifact": "grading"},
        "source": {"revision": "registry-v1", "registry_artifact": "sources"},
        "weights": {"mode": "explicit_uniform", "artifact": "weights"},
        "comparison": {"estimand": "paired adaptation-score difference", "multiplicity_policy": "one predeclared comparison",
                       "practical_gain_threshold": 0.02, "max_task_regression": 0.01, "artifact": "comparison"},
        "execution": {"configuration_artifact": "execution", "code_artifact": "code",
                      "environment_artifact": "environment", "python_version": "3.11.9"},
        "evaluation_manifest_artifact": "manifest",
        "confirmation": {"set_id": "external-confirmation-01", "selected_on": "external_development_only",
                         "selection_decision_artifact": "selection", "mechanical_failure_rule": "Record failure; do not select another checkpoint."}
        if purpose == "confirmation" else None,
    }


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(experiments, "experiments module is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def freeze(self):
        record = fixture(self.root)
        result = experiments.freeze_confirmation(record, self.root, self.root / "ledgers",
                                                frozen_at_utc="2026-10-04T10:01:00Z")
        return record, result, Path(result["ledger_path"])

    def opened(self):
        record, frozen, ledger = self.freeze()
        event = experiments.open_confirmation(ledger, self.root,
                    expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=frozen["event_sha256"],
                    opened_at_utc="2026-10-04T10:02:00Z")
        return record, frozen, ledger, event

    def test_complete_record_is_copied_without_defaults_or_mutation(self):
        record = fixture(self.root, purpose="engineering")
        result = experiments.validate_experiment_record(record)
        self.assertEqual(result, record)
        result["candidate"]["revision"] = "changed"
        self.assertEqual(record["candidate"]["revision"], "commit-candidate")

    def test_missing_provenance_fields_and_identity_are_rejected(self):
        for path in (("baseline", "revision"), ("candidate", "model_id"), ("protocol", "artifact"),
                     ("source", "revision"), ("processor", "revision"), ("grading", "judge_revision"),
                     ("seeds", "inference"), ("weights",), ("comparison", "multiplicity_policy"),
                     ("execution", "configuration_artifact"), ("purpose",)):
            record = fixture(self.root)
            parent = record if len(path) == 1 else record[path[0]]
            del parent[path[-1]]
            with self.subTest(path=path), self.assertRaises(ValueError):
                experiments.validate_experiment_record(record)

    def test_templates_unresolved_revisions_and_implicit_weights_are_rejected(self):
        for field, value in (("purpose", "pending"), ("record_kind", "template_not_executable_training_configuration")):
            record = fixture(self.root)
            record[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                experiments.validate_experiment_record(record)
        for value in (None, "", "main", "latest", "pending", "unresolved", "TBD"):
            record = fixture(self.root)
            record["baseline"]["revision"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                experiments.validate_experiment_record(record)
        record = fixture(self.root)
        record["weights"]["mode"] = "automatic"
        with self.assertRaises(ValueError):
            experiments.validate_experiment_record(record)

    def test_missing_artifact_reference_and_duplicate_paths_fail(self):
        record = fixture(self.root)
        record["protocol"]["artifact"] = "absent"
        with self.assertRaises(ValueError):
            experiments.validate_experiment_record(record)
        record = fixture(self.root)
        record["artifacts"]["duplicate"] = copy.deepcopy(record["artifacts"]["protocol"])
        with self.assertRaises(ValueError):
            experiments.validate_experiment_record(record)

    def test_bad_hash_seed_number_time_and_unknown_fields_fail(self):
        edits = [("artifacts", "protocol", "sha256", "x" * 64), ("seeds", "training", True),
                 ("comparison", "practical_gain_threshold", float("nan")),
                 ("comparison", "max_task_regression", -0.1), ("created_at_utc", "2026-10-04"),
                 ("schema_version", True), ("surprise", 1)]
        for *path, value in edits:
            record = fixture(self.root)
            parent = record
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                experiments.validate_experiment_record(record)

    def test_development_record_can_verify_local_files_without_freezing_confirmation(self):
        self.assertTrue(hasattr(experiments, "verify_experiment_record"), "local record verification is not implemented")
        record = fixture(self.root, purpose="development")
        verified = experiments.verify_experiment_record(record, self.root)
        self.assertTrue(verified["ok"])
        self.assertEqual(verified["artifact_count"], 13)
        self.assertFalse((self.root / "ledgers").exists())
        (self.root / "inputs/protocol.txt").write_text("wrong protocol")
        with self.assertRaises(ValueError):
            experiments.verify_experiment_record(record, self.root)

    def test_receipt_uses_real_bytes_and_requires_external_digest(self):
        (self.root / "files").mkdir()
        (self.root / "files/a.txt").write_bytes(b"abc")
        result = experiments.create_artifact_receipt(self.root, ["files"], self.root / "receipt.json")
        self.assertEqual(result["artifacts"], [{"path": "files/a.txt", "size_bytes": 3,
                         "sha256": "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"}])
        self.assertTrue(experiments.verify_artifact_receipt(self.root, result,
                        expected_receipt_sha256=result["receipt_sha256"])["ok"])
        with self.assertRaises(ValueError):
            experiments.verify_artifact_receipt(self.root, result, expected_receipt_sha256="0" * 64)

    def test_receipt_is_deterministic_and_existing_output_is_preserved(self):
        fixture(self.root)
        first = experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "one.json")
        second = experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "two.json")
        self.assertEqual(first, second)
        original = (self.root / "one.json").read_bytes()
        with self.assertRaises(FileExistsError):
            experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "one.json")
        self.assertEqual((self.root / "one.json").read_bytes(), original)

    def test_receipt_reports_missing_extra_and_changed_artifacts(self):
        fixture(self.root)
        receipt = experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "receipt.json")
        (self.root / "inputs/baseline.txt").unlink()
        (self.root / "inputs/candidate.txt").write_text("tampered")
        (self.root / "inputs/new.txt").write_text("extra relevant file")
        (self.root / "outside.txt").write_text("outside declared scope")
        result = experiments.verify_artifact_receipt(self.root, receipt, expected_receipt_sha256=receipt["receipt_sha256"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["missing"], ["inputs/baseline.txt"])
        self.assertEqual(result["changed"], ["inputs/candidate.txt"])
        self.assertEqual(result["extra"], ["inputs/new.txt"])

    def test_tampered_receipt_cannot_be_reanchored_with_its_own_new_digest(self):
        fixture(self.root)
        receipt = experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "receipt.json")
        expected = receipt["receipt_sha256"]
        receipt["artifacts"][0]["sha256"] = "0" * 64
        payload = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
        receipt["receipt_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                                         ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        with self.assertRaises(ValueError):
            experiments.verify_artifact_receipt(self.root, receipt, expected_receipt_sha256=expected)

    def test_symlinks_escape_duplicate_scope_and_self_receipt_are_rejected(self):
        fixture(self.root)
        for scope in (["../outside"], ["/absolute"], ["inputs", "inputs/protocol.txt"], ["inputs", "inputs"], []):
            with self.subTest(scope=scope), self.assertRaises(ValueError):
                experiments.create_artifact_receipt(self.root, scope, self.root / "bad.json")
        with self.assertRaises(ValueError):
            experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "inputs/receipt.json")
        (self.root / "inputs/link.txt").symlink_to(self.root / "inputs/protocol.txt")
        with self.assertRaises(ValueError):
            experiments.create_artifact_receipt(self.root, ["inputs"], self.root / "bad.json")

    def test_freeze_checks_declared_hashes_before_creating_ledger(self):
        record = fixture(self.root)
        record["artifacts"]["protocol"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            experiments.freeze_confirmation(record, self.root, self.root / "ledgers", frozen_at_utc="2026-10-04T10:01:00Z")
        self.assertFalse((self.root / "ledgers").exists())

    def test_freeze_rejects_undeclared_scope_files_and_nonconfirmation_purpose(self):
        record = fixture(self.root)
        (self.root / "inputs/extra.txt").write_text("not declared")
        with self.assertRaises(ValueError):
            experiments.freeze_confirmation(record, self.root, self.root / "ledgers", frozen_at_utc="2026-10-04T10:01:00Z")
        record = fixture(self.root, purpose="development")
        with self.assertRaises(ValueError):
            experiments.freeze_confirmation(record, self.root, self.root / "ledgers", frozen_at_utc="2026-10-04T10:01:00Z")

    def test_frozen_unopened_record_has_fixed_candidate_and_cannot_be_overwritten(self):
        record, frozen, ledger = self.freeze()
        self.assertEqual(frozen["status"], "frozen_unopened")
        self.assertEqual(frozen["record"]["candidate"], record["candidate"])
        original = (ledger / "00-frozen.json").read_bytes()
        record["candidate"]["revision"] = "other-candidate-commit"
        with self.assertRaises(FileExistsError):
            experiments.freeze_confirmation(record, self.root, self.root / "ledgers", frozen_at_utc="2026-10-04T10:01:00Z")
        self.assertEqual((ledger / "00-frozen.json").read_bytes(), original)

    def test_open_checks_artifact_drift_and_preserves_unopened_state_on_failure(self):
        _, frozen, ledger = self.freeze()
        (self.root / "inputs/processor.txt").write_text("drift")
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                          expected_latest_sha256=frozen["event_sha256"],
                                          opened_at_utc="2026-10-04T10:02:00Z")
        self.assertEqual(sorted(p.name for p in ledger.iterdir()), ["00-frozen.json"])

    def test_open_requires_correct_anchor_and_cannot_reopen(self):
        _, frozen, ledger = self.freeze()
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root, expected_freeze_sha256="0" * 64,
                                          expected_latest_sha256=frozen["event_sha256"],
                                          opened_at_utc="2026-10-04T10:02:00Z")
        opened = experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                              expected_latest_sha256=frozen["event_sha256"],
                                              opened_at_utc="2026-10-04T10:02:00Z")
        self.assertEqual(opened["status"], "opened")
        self.assertEqual(opened["previous_sha256"], frozen["event_sha256"])
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                          expected_latest_sha256=opened["event_sha256"],
                                          opened_at_utc="2026-10-04T10:03:00Z")

    def test_results_require_open_state_and_preserve_exact_result_file(self):
        _, frozen, ledger = self.freeze()
        result_path = self.root / "result.json"
        result_path.write_text('{"score": -0.25, "outcome": "disappointing"}\n')
        before = result_path.read_bytes()
        with self.assertRaises(ValueError):
            experiments.record_confirmation_result(ledger, self.root, "result.json",
                        expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=frozen["event_sha256"],
                        recorded_at_utc="2026-10-04T10:03:00Z")
        opened = experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                      expected_latest_sha256=frozen["event_sha256"],
                                      opened_at_utc="2026-10-04T10:02:00Z")
        result = experiments.record_confirmation_result(ledger, self.root, "result.json",
                        expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"],
                        recorded_at_utc="2026-10-04T10:03:00Z")
        self.assertEqual(result["status"], "result_recorded")
        self.assertEqual(result["result"]["sha256"], hashlib.sha256(before).hexdigest())
        self.assertEqual(result_path.read_bytes(), before)
        with self.assertRaises(ValueError):
            experiments.record_confirmation_result(ledger, self.root, "result.json",
                        expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=result["event_sha256"],
                        recorded_at_utc="2026-10-04T10:04:00Z")

    def test_result_informed_change_retires_set_and_forbids_reselection(self):
        record, frozen, ledger, opened = self.opened()
        (self.root / "result.txt").write_text("negative result")
        result = experiments.record_confirmation_result(ledger, self.root, "result.txt",
                    expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"],
                    recorded_at_utc="2026-10-04T10:03:00Z")
        retired = experiments.retire_confirmation(ledger, expected_freeze_sha256=frozen["event_sha256"],
                    expected_latest_sha256=result["event_sha256"],
                    reason="Result informed the next prompt", retired_at_utc="2026-10-04T10:04:00Z")
        self.assertEqual(retired["status"], "retired_to_development")
        self.assertTrue(retired["result_informed_changes"])
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                          expected_latest_sha256=retired["event_sha256"],
                                          opened_at_utc="2026-10-04T10:05:00Z")
        with self.assertRaises(FileExistsError):
            experiments.freeze_confirmation(record, self.root, self.root / "ledgers", frozen_at_utc="2026-10-04T10:05:00Z")

    def test_ledger_tampering_extra_events_and_duplicate_json_keys_fail(self):
        _, frozen, ledger, opened = self.opened()
        event_path = ledger / "01-opened.json"
        original = event_path.read_bytes()
        for payload in (original.replace(b'"opened"', b'"result_recorded"'), b'{"status":"opened","status":"opened"}'):
            event_path.write_bytes(payload)
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                experiments.retire_confirmation(ledger, expected_freeze_sha256=frozen["event_sha256"],
                    expected_latest_sha256=opened["event_sha256"],
                    reason="change", retired_at_utc="2026-10-04T10:04:00Z")
        event_path.write_bytes(original)
        (ledger / "02-unrecognized.json").write_text("{}")
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                          expected_latest_sha256=opened["event_sha256"],
                                          opened_at_utc="2026-10-04T10:04:00Z")

    def test_backdated_transition_and_retirement_before_result_fail(self):
        _, frozen, ledger = self.freeze()
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root, expected_freeze_sha256=frozen["event_sha256"],
                                          expected_latest_sha256=frozen["event_sha256"],
                                          opened_at_utc="2026-10-04T09:59:00Z")
        with self.assertRaises(ValueError):
            experiments.retire_confirmation(ledger, expected_freeze_sha256=frozen["event_sha256"],
                    expected_latest_sha256=frozen["event_sha256"],
                    reason="change", retired_at_utc="2026-10-04T10:04:00Z")

    def test_latest_anchor_detects_rewritten_tail_and_deleted_history(self):
        self.assertTrue(hasattr(experiments, "verify_confirmation"), "anchored history verification is not implemented")
        _, frozen, ledger, opened = self.opened()
        verified = experiments.verify_confirmation(ledger, self.root,
                    expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"])
        self.assertTrue(verified["ok"])
        self.assertEqual(verified["status"], "opened")
        path = ledger / "01-opened.json"
        value = json.loads(path.read_text())
        value["time_utc"] = "2026-10-04T10:02:01Z"
        payload = {k: v for k, v in value.items() if k != "event_sha256"}
        value["event_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                                        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            experiments.verify_confirmation(ledger, self.root,
                    expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"])
        path.unlink()
        with self.assertRaises(ValueError):
            experiments.verify_confirmation(ledger, self.root,
                    expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"])

    def test_verification_detects_changed_or_missing_result_bytes(self):
        self.assertTrue(hasattr(experiments, "verify_confirmation"), "result byte verification is not implemented")
        _, frozen, ledger, opened = self.opened()
        path = self.root / "result.txt"
        path.write_text("negative result")
        result = experiments.record_confirmation_result(ledger, self.root, "result.txt",
                    expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"],
                    recorded_at_utc="2026-10-04T10:03:00Z")
        anchors = {"expected_freeze_sha256": frozen["event_sha256"], "expected_latest_sha256": result["event_sha256"]}
        self.assertTrue(experiments.verify_confirmation(ledger, self.root, **anchors)["ok"])
        path.write_text("positive result")
        verified = experiments.verify_confirmation(ledger, self.root, **anchors)
        self.assertFalse(verified["ok"])
        self.assertEqual(verified["result"]["changed"], ["result.txt"])
        path.unlink()
        verified = experiments.verify_confirmation(ledger, self.root, **anchors)
        self.assertFalse(verified["ok"])
        self.assertEqual(verified["result"]["missing"], ["result.txt"])

    def test_mutations_require_latest_anchor_and_cannot_advance_rewritten_or_truncated_tail(self):
        for name in ("open_confirmation", "record_confirmation_result", "retire_confirmation"):
            self.assertIn("expected_latest_sha256", inspect.signature(getattr(experiments, name)).parameters,
                          "Every mutation must accept and validate the retained latest anchor")
        _, frozen, ledger, opened = self.opened()
        (self.root / "result.txt").write_text("negative result")
        path = ledger / "01-opened.json"
        value = json.loads(path.read_text())
        value["time_utc"] = "2026-10-04T10:02:01Z"
        payload = {k: v for k, v in value.items() if k != "event_sha256"}
        value["event_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"),
                                                        ensure_ascii=False, allow_nan=False).encode()).hexdigest()
        path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            experiments.record_confirmation_result(ledger, self.root, "result.txt",
                expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"],
                recorded_at_utc="2026-10-04T10:03:00Z")
        self.assertFalse((ledger / "02-result.json").exists())
        path.unlink()
        with self.assertRaises(ValueError):
            experiments.open_confirmation(ledger, self.root,
                expected_freeze_sha256=frozen["event_sha256"], expected_latest_sha256=opened["event_sha256"],
                opened_at_utc="2026-10-04T10:03:00Z")
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
