"""Offline tests for the public protocol-revision drift guard."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("protocol_drift", REPO / "tools/protocol_drift.py")
protocol_drift = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(protocol_drift)


class ProtocolDriftTests(unittest.TestCase):
    def setUp(self):
        self.pin = {
            "schema_id": "mmbu.public_protocol_revision_pin",
            "schema_version": 1,
            "dataset_id": "mmbu/mmbu-public",
            "expected_revision": "d11326436d37a9a560549156bf205ef1b120aa36",
            "expected_gated": "auto",
            "expected_private": False,
            "observed_at_utc": "2026-10-23T22:10:00Z",
            "scope": "repository metadata only; no dataset rows or files",
        }
        self.snapshot = {
            "id": "mmbu/mmbu-public",
            "sha": self.pin["expected_revision"],
            "gated": "auto",
            "private": False,
            "lastModified": "2026-10-21T16:59:39.000Z",
            "siblings": [{"rfilename": "README.md"}],
        }

    def test_matching_snapshot_is_current_without_opening_dataset_files(self):
        result = protocol_drift.compare(self.pin, self.snapshot)
        self.assertEqual(result["status"], "current")
        self.assertEqual(result["errors"], [])
        self.assertNotIn("siblings", result)

    def test_revision_gating_or_identity_drift_fails_closed(self):
        mutations = [
            {"sha": "0" * 40},
            {"gated": False},
            {"private": True},
            {"id": "other/dataset"},
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                result = protocol_drift.compare(self.pin, {**self.snapshot, **mutation})
                self.assertEqual(result["status"], "drift")
                self.assertTrue(result["errors"])

    def test_malformed_pin_and_snapshot_are_rejected(self):
        for pin in ({**self.pin, "extra": 1}, {**self.pin, "expected_revision": "main"}):
            with self.subTest(pin=pin):
                with self.assertRaises(ValueError):
                    protocol_drift.compare(pin, self.snapshot)
        for snapshot in ({**self.snapshot, "sha": None}, {k: v for k, v in self.snapshot.items() if k != "sha"}):
            with self.subTest(snapshot=snapshot):
                with self.assertRaises(ValueError):
                    protocol_drift.compare(self.pin, snapshot)

    def test_cli_uses_offline_snapshot_and_returns_one_on_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pin_path = root / "pin.json"
            snapshot_path = root / "snapshot.json"
            pin_path.write_text(json.dumps(self.pin), encoding="utf-8")
            snapshot_path.write_text(json.dumps(self.snapshot), encoding="utf-8")
            command = [sys.executable, str(REPO / "tools/protocol_drift.py"), "--pin", str(pin_path),
                       "--api-json", str(snapshot_path)]
            current = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(current.returncode, 0, current.stderr)
            self.assertEqual(json.loads(current.stdout)["status"], "current")

            self.snapshot["sha"] = "0" * 40
            snapshot_path.write_text(json.dumps(self.snapshot), encoding="utf-8")
            drift = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(drift.returncode, 1, drift.stderr)
            self.assertEqual(json.loads(drift.stdout)["status"], "drift")


if __name__ == "__main__":
    unittest.main()
