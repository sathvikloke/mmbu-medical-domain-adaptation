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
        self.policy = self.root / "policy.json"; self.policy.write_bytes(b"policy")
        self.public_key = self.root / "public.pem"; self.public_key.write_bytes(b"key")
        self.revocation = self.root / "revocation.json"; self.revocation.write_bytes(b"revocation")
        self.signature = self.root / "signature.bin"; self.signature.write_bytes(b"signature")
        self.verifier = self.root / "verifier"; self.verifier.write_bytes(b"verifier")

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
            "--external-policy", str(self.policy), "--external-policy-pin", "c" * 64,
            "--external-public-key", str(self.public_key), "--external-public-key-pin", "d" * 64,
            "--external-revocation", str(self.revocation), "--external-revocation-pin", "e" * 64,
            "--external-signature", str(self.signature),
            "--external-namespace", "mmbu.phase1.busi-whu-opening.v1",
            "--external-principal", "rights-authority", "--external-role", "data-rights-authority",
            "--external-signed-at", "2026-10-26T07:29:00Z",
            "--external-verifier", str(self.verifier), "--external-verifier-pin", "f" * 64,
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
        mechanics = object()
        external = object()
        capability = object()
        authorization = {"record_digest": "a" * 64}
        store = mock.Mock()
        store.get.return_value = authorization
        receipt = {"status": "built"}
        with mock.patch.object(self.module, "_load_records", return_value=store):
            with mock.patch.object(self.module, "verify_external_authority", return_value=external) as verify:
                with mock.patch.object(self.module, "validate_busi_whu_review_opening", return_value=mechanics) as validate:
                    with mock.patch.object(self.module, "bind_external_review_opening", return_value=capability) as bind:
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
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(bind.call_count, 2)
        self.assertIs(bind.call_args_list[0].args[0], mechanics)
        self.assertIs(bind.call_args_list[0].args[1], external)
        self.assertIs(bind.call_args_list[0].args[2], authorization)


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

    def external_args(self):
        review = [
            "--external-policy", str(self.records), "--external-policy-pin", "1" * 64,
            "--external-public-key", str(self.records), "--external-public-key-pin", "2" * 64,
            "--external-revocation", str(self.records), "--external-revocation-pin", "3" * 64,
            "--external-signature", str(self.records), "--external-principal", "external-review-board",
            "--external-signed-at", "2026-10-26T07:20:00Z",
            "--external-verified-at", "2026-10-26T07:29:00Z",
            "--external-verifier", str(self.records), "--external-verifier-pin", "4" * 64,
        ]
        confirmation = [
            "--confirmation-external-policy", str(self.records),
            "--confirmation-external-policy-pin", "5" * 64,
            "--confirmation-external-public-key", str(self.records),
            "--confirmation-external-public-key-pin", "6" * 64,
            "--confirmation-external-revocation", str(self.records),
            "--confirmation-external-revocation-pin", "7" * 64,
            "--confirmation-external-signature", str(self.records),
            "--confirmation-external-principal", "external-confirmation-board",
            "--confirmation-external-signed-at", "2026-10-26T07:25:00Z",
            "--confirmation-external-verified-at", "2026-10-26T07:29:00Z",
            "--confirmation-external-verifier", str(self.records),
            "--confirmation-external-verifier-pin", "8" * 64,
        ]
        return [*review, *confirmation]

    def test_real_route_has_no_arbitrary_patient_map_or_synthetic_fixture(self):
        base = [
            "build-real-artifacts", "--review-report", str(self.report),
            "--source-manifest", str(self.manifest), "--records", str(self.records),
            "--source-admission-digest", "a" * 64,
            "--confirmation-purpose-digest", "b" * 64,
            "--created-at", "2026-10-26T07:30:00Z",
            *self.external_args(),
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
                with mock.patch.object(
                    self.module, "resolve_completed_review_authority_subject", return_value={"subject": True}
                ), mock.patch.object(
                    self.module.heldout_confirmation, "confirmation_authority_subject",
                    return_value={"confirmation": True},
                ), mock.patch.object(
                    self.module, "verify_external_authority", side_effect=[object(), object()],
                ) as verify, \
                        mock.patch.object(self.module.sys, "stdout", OutputSink()):
                    self.assertEqual(self.module.main([
                        "build-real-artifacts", "--review-report", str(self.report),
                        "--source-manifest", str(self.manifest), "--records", str(self.records),
                        "--source-admission-digest", "a" * 64,
                        "--confirmation-purpose-digest", "b" * 64,
                        "--created-at", "2026-10-26T07:30:00Z",
                        *self.external_args(),
                    ]), 0)
                    self.assertEqual(self.module.main([
                        "build-synthetic-artifacts", "--fixture", str(self.fixture),
                        "--created-at", "2026-10-26T07:30:00Z",
                    ]), 0)
        self.assertEqual(real.call_count, 1)
        self.assertEqual(synthetic.call_count, 1)
        self.assertEqual(verify.call_count, 2)
        self.assertEqual(
            verify.call_args_list[1].kwargs["namespace"],
            "mmbu.phase1.busi-whu-confirmation.v1",
        )
        self.assertEqual(verify.call_args_list[1].kwargs["role"], "confirmation-authority")

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
            "--external-policy", str(self.records), "--external-policy-pin", "1" * 64,
            "--external-public-key", str(self.records), "--external-public-key-pin", "2" * 64,
            "--external-revocation", str(self.records), "--external-revocation-pin", "3" * 64,
            "--external-signature", str(self.records), "--external-principal", "external-review-board",
            "--external-signed-at", "2026-10-26T07:25:00Z",
            "--external-verifier", str(self.records), "--external-verifier-pin", "4" * 64,
        ]

    def test_authentication_chain_is_required_and_base_report_is_never_emitted(self):
        with self.assertRaises(SystemExit):
            self.module.main(self.argv()[:13])
        base = {"record_digest": "a" * 64}
        authenticated = {"reviewer_identity_authenticated": True}
        with mock.patch.object(self.module, "validate_completed_review", return_value=base) as validate:
            with mock.patch.object(self.module, "completed_review_authority_subject", return_value={"subject": True}), \
                    mock.patch.object(self.module, "verify_external_authority", return_value=object()), \
                    mock.patch.object(self.module, "authenticate_completed_review", return_value=authenticated) as authenticate:
                with mock.patch.object(self.module.sys, "stdout", OutputSink()):
                    self.assertEqual(self.module.main(self.argv()), 0)
        self.assertEqual(validate.call_count, 1)
        self.assertEqual(authenticate.call_count, 1)
        self.assertIs(authenticate.call_args.args[0], base)


if __name__ == "__main__":
    unittest.main()
