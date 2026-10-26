"""Fail-closed command-boundary tests for BUSI-WHU review and confirmation."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from mmbu_phase1 import canonical


ROOT = Path(__file__).resolve().parents[2]


def load_tool(name: str):
    spec = importlib.util.spec_from_file_location(f"test_tool_{name}", ROOT / "tools" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write(path: Path, value) -> Path:
    path.write_bytes(canonical.dumps(value))
    return path


class OutputSink:
    def __init__(self):
        self.buffer = io.BytesIO()

    def write(self, value):
        return len(value)

    def flush(self):
        return None


class ReviewCliTests(unittest.TestCase):
    def setUp(self):
        self.module = load_tool("busi_whu_review")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.records = write(self.root / "records.json", [])
        self.inventory = write(self.root / "inventory.json", {"inventory": True})
        self.selection = write(self.root / "selection.json", {"selection": True})
        self.fingerprints = write(self.root / "fingerprints.json", {"inventories": []})

    def tearDown(self):
        self.temp.cleanup()

    def argv(self):
        return [
            "--records", str(self.records),
            "--authorization-digest", "a" * 64,
            "--opening-receipt-digest", "b" * 64,
            "--now", "2026-10-26T07:30:00Z",
            "--metadata-inventory", str(self.inventory),
            "--selection", str(self.selection),
            "--source-fingerprint-inventories", str(self.fingerprints),
        ]

    def test_missing_authority_and_raw_path_bypass_reject_at_parser(self):
        with self.assertRaises(SystemExit):
            self.module.main([
                "--records", str(self.records),
                "--metadata-inventory", str(self.inventory),
                "--selection", str(self.selection),
                "--source-fingerprint-inventories", str(self.fingerprints),
            ])
        with self.assertRaises(SystemExit):
            self.module.main([*self.argv(), "--archive", str(self.root / "payload.zip")])

    def test_real_review_passes_only_validated_capability_and_consumes_one_attempt(self):
        capability = object()
        receipt = {"status": "built"}
        with mock.patch.object(self.module, "validate_busi_whu_review_opening", return_value=capability) as validate:
            with mock.patch.object(self.module, "build_review_packet", side_effect=[receipt, FileExistsError("used")]) as build:
                with mock.patch.object(self.module.sys, "stdout", OutputSink()):
                    self.assertEqual(self.module.main(self.argv()), 0)
                with mock.patch.object(self.module.sys, "stderr", OutputSink()):
                    self.assertEqual(self.module.main(self.argv()), 2)
        validate.assert_has_calls([
            mock.call(mock.ANY, "a" * 64, "b" * 64, "2026-10-26T07:30:00Z"),
            mock.call(mock.ANY, "a" * 64, "b" * 64, "2026-10-26T07:30:00Z"),
        ])
        self.assertIs(build.call_args_list[0].args[0], capability)
        self.assertEqual(build.call_count, 2)


class ConfirmationCliTests(unittest.TestCase):
    def setUp(self):
        self.module = load_tool("busi_whu_confirmation")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.records = write(self.root / "records.json", [])
        self.report = write(self.root / "report.json", {"report": True})
        self.manifest = write(self.root / "manifest.json", {"manifest": True})
        self.fixture = write(self.root / "fixture.json", {"synthetic_only": True})

    def tearDown(self):
        self.temp.cleanup()

    def test_real_route_has_no_arbitrary_patient_map_or_synthetic_fixture(self):
        base = [
            "build-real-artifacts", "--review-report", str(self.report),
            "--source-manifest", str(self.manifest), "--records", str(self.records),
            "--source-admission-digest", "a" * 64,
            "--confirmation-purpose-digest", "b" * 64,
            "--created-at", "2026-10-26T07:30:00Z",
        ]
        with self.assertRaises(SystemExit):
            self.module.main([*base, "--patient-map", str(self.root / "patients.json")])
        with self.assertRaises(SystemExit):
            self.module.main([*base, "--fixture", str(self.fixture)])

    def test_real_and_synthetic_routes_call_only_their_closed_constructors(self):
        with mock.patch.object(
            self.module.heldout_confirmation, "build_authenticated_randomization_artifacts",
            return_value={"construction_scope": "authenticated_real"},
        ) as real:
            with mock.patch.object(
                self.module.heldout_confirmation, "build_synthetic_randomization_artifacts",
                return_value={"construction_scope": "synthetic_mechanics_only"},
            ) as synthetic:
                with mock.patch.object(self.module.sys, "stdout", OutputSink()):
                    self.assertEqual(self.module.main([
                        "build-real-artifacts", "--review-report", str(self.report),
                        "--source-manifest", str(self.manifest), "--records", str(self.records),
                        "--source-admission-digest", "a" * 64,
                        "--confirmation-purpose-digest", "b" * 64,
                        "--created-at", "2026-10-26T07:30:00Z",
                    ]), 0)
                    self.assertEqual(self.module.main([
                        "build-synthetic-artifacts", "--fixture", str(self.fixture),
                        "--created-at", "2026-10-26T07:30:00Z",
                    ]), 0)
        self.assertEqual(real.call_count, 1)
        self.assertEqual(synthetic.call_count, 1)

    def test_synthetic_route_requires_explicit_fixture_and_rejects_real_inputs(self):
        with self.assertRaises(SystemExit):
            self.module.main([
                "build-synthetic-artifacts", "--created-at", "2026-10-26T07:30:00Z",
            ])
        with self.assertRaises(SystemExit):
            self.module.main([
                "build-synthetic-artifacts", "--fixture", str(self.fixture),
                "--created-at", "2026-10-26T07:30:00Z",
                "--review-report", str(self.report),
            ])


class ReviewValidationCliTests(unittest.TestCase):
    def setUp(self):
        self.module = load_tool("busi_whu_review_validation")
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.records = write(self.root / "records.json", [])
        for name in ("packet", "primary", "secondary", "adjudication", "rights", "opening"):
            setattr(self, name, self.root / name)

    def tearDown(self):
        self.temp.cleanup()

    def argv(self):
        return [
            str(self.packet), "--primary-review", str(self.primary),
            "--secondary-review", str(self.secondary),
            "--adjudication-review", str(self.adjudication),
            "--rights-review", str(self.rights), "--review-opening", str(self.opening),
            "--expected-packet-receipt-digest", "1" * 64,
            "--records", str(self.records), "--authorization-digest", "2" * 64,
            "--opening-receipt-digest", "3" * 64,
            "--review-attestation-digest", "4" * 64,
            "--review-attestation-digest", "5" * 64,
            "--review-attestation-digest", "6" * 64,
            "--review-attestation-digest", "7" * 64,
            "--clinical-assessment-digest", "8" * 64,
            "--custodian-assessment-digest", "9" * 64,
            "--report-created-at", "2026-10-26T07:29:00Z",
            "--now", "2026-10-26T07:30:00Z",
        ]

    def test_authentication_chain_is_required_and_base_report_is_never_emitted(self):
        with self.assertRaises(SystemExit):
            self.module.main(self.argv()[:13])
        base = {"record_digest": "a" * 64}
        authenticated = {"reviewer_identity_authenticated": True}
        with mock.patch.object(self.module, "validate_completed_review", return_value=base) as validate:
            with mock.patch.object(self.module, "authenticate_completed_review", return_value=authenticated) as authenticate:
                with mock.patch.object(self.module.sys, "stdout", OutputSink()):
                    self.assertEqual(self.module.main(self.argv()), 0)
        self.assertEqual(validate.call_count, 1)
        self.assertEqual(authenticate.call_count, 1)
        self.assertIs(authenticate.call_args.args[0], base)


if __name__ == "__main__":
    unittest.main()
