#!/usr/bin/env python3
"""CPU-only validator for the sealed BUSI-WHU confirmation protocol."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical, heldout_confirmation
from mmbu_phase1.busi_whu_review_validation import resolve_completed_review_authority_subject
from mmbu_phase1.external_trust import verify_external_authority
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.store import RecordStore


def _emit(value: dict) -> None:
    sys.stdout.buffer.write(canonical.dumps(value) + b"\n")


def _load(path: Path):
    return canonical.loads(path.read_bytes())


def _load_canonical(path: Path):
    payload = path.read_bytes()
    value = canonical.loads(payload)
    if canonical.dumps(value) != payload:
        raise ValueError(f"{path.name} is not canonical JSON")
    return value


def _store(path: Path) -> RecordStore:
    records = _load_canonical(path)
    if type(records) is not list:
        raise ValueError(f"{path.name} must contain one record array")
    return RecordStore(records)


def _add_external_arguments(parser: argparse.ArgumentParser, prefix: str = "external") -> None:
    for name in ("policy", "public-key", "revocation", "signature", "verifier"):
        parser.add_argument(f"--{prefix}-{name}", type=Path, required=True)
    for name in (
        "policy-pin", "public-key-pin", "revocation-pin", "principal", "signed-at",
        "verified-at", "verifier-pin",
    ):
        parser.add_argument(f"--{prefix}-{name}", required=True)


def _external_authority(
    args: argparse.Namespace, subject: dict, *, prefix: str = "external",
    namespace: str = "mmbu.phase1.busi-whu-completed-review.v1",
    role: str = "review-board-authority",
):
    def value(name: str):
        return getattr(args, f"{prefix}_{name.replace('-', '_')}")

    return verify_external_authority(
        policy_bytes=value("policy").read_bytes(), policy_pin_sha256=value("policy-pin"),
        public_key_bytes=value("public-key").read_bytes(),
        public_key_pin_sha256=value("public-key-pin"),
        revocation_bytes=value("revocation").read_bytes(),
        revocation_pin_sha256=value("revocation-pin"),
        signature_bytes=value("signature").read_bytes(), subject=subject,
        namespace=namespace, principal=value("principal"), role=role,
        signed_at=value("signed-at"), verified_at=value("verified-at"),
        verifier_path=value("verifier"), verifier_pin_sha256=value("verifier-pin"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-spec")
    validate.add_argument("--spec", type=Path, required=True)
    readiness = commands.add_parser("readiness")
    readiness.add_argument("--manifest", type=Path, required=True)
    synthetic = commands.add_parser("synthetic-check")
    synthetic.add_argument("--manifest", type=Path, required=True)
    real_artifacts = commands.add_parser("build-real-artifacts")
    real_artifacts.add_argument("--review-report", type=Path, required=True)
    real_artifacts.add_argument("--source-manifest", type=Path, required=True)
    real_artifacts.add_argument("--records", type=Path, required=True)
    real_artifacts.add_argument("--source-admission-digest", required=True)
    real_artifacts.add_argument("--confirmation-purpose-digest", required=True)
    real_artifacts.add_argument("--created-at", required=True)
    _add_external_arguments(real_artifacts)
    _add_external_arguments(real_artifacts, "confirmation-external")
    synthetic_artifacts = commands.add_parser("build-synthetic-artifacts")
    synthetic_artifacts.add_argument("--fixture", type=Path, required=True)
    synthetic_artifacts.add_argument("--created-at", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-spec":
            heldout_confirmation.load_spec(args.spec)
            _emit({"status": "valid"})
            return 0
        if args.command == "synthetic-check":
            result = heldout_confirmation.validate_synthetic_fixture(
                _load(args.manifest)
            )
            _emit(result)
            return 0
        if args.command == "build-real-artifacts":
            report = _load_canonical(args.review_report)
            store = _store(args.records)
            external = _external_authority(
                args, resolve_completed_review_authority_subject(report, store),
            )
            confirmation_external = _external_authority(
                args,
                heldout_confirmation.confirmation_authority_subject(
                    report, args.source_admission_digest, args.confirmation_purpose_digest,
                ),
                prefix="confirmation_external",
                namespace="mmbu.phase1.busi-whu-confirmation.v1",
                role="confirmation-authority",
            )
            result = heldout_confirmation.build_authenticated_randomization_artifacts(
                report, _load_canonical(args.source_manifest), store,
                args.source_admission_digest, args.confirmation_purpose_digest,
                args.created_at, external_authority=external,
                confirmation_external_authority=confirmation_external,
            )
            _emit(result)
            return 0
        if args.command == "build-synthetic-artifacts":
            result = heldout_confirmation.build_synthetic_randomization_artifacts(
                _load_canonical(args.fixture), args.created_at,
            )
            _emit(result)
            return 0
        value = _load(args.manifest)
        result = heldout_confirmation.readiness_status(value)
        _emit(result)
        return 2
    except (OSError, ValueError, TypeError, canonical.CanonicalJSONError, ContractViolation) as exc:
        _emit({"error": str(exc), "status": "invalid"})
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
