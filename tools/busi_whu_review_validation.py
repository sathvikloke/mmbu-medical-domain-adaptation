#!/usr/bin/env python3
"""Validate completed BUSI-WHU review evidence without granting admission."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.busi_whu_review_validation import (  # noqa: E402
    authenticate_completed_review,
    completed_review_authority_subject,
    validate_completed_review,
)
from mmbu_phase1.external_trust import verify_external_authority  # noqa: E402
from mmbu_phase1.fields import ContractViolation  # noqa: E402
from mmbu_phase1.store import RecordStore  # noqa: E402


def _load_records(path: Path) -> RecordStore:
    payload = path.read_bytes()
    value = canonical.loads(payload)
    if canonical.dumps(value) != payload:
        raise ValueError(f"{path.name} is not canonical JSON")
    if type(value) is not list:
        raise ValueError(f"{path.name} must contain one record array")
    return RecordStore(value)


def _add_external_arguments(parser: argparse.ArgumentParser) -> None:
    for name in ("policy", "public-key", "revocation", "signature", "verifier"):
        parser.add_argument(f"--external-{name}", type=Path, required=True)
    for name in (
        "policy-pin", "public-key-pin", "revocation-pin", "principal", "signed-at", "verifier-pin",
    ):
        parser.add_argument(f"--external-{name}", required=True)


def _external_authority(args: argparse.Namespace, subject: dict):
    return verify_external_authority(
        policy_bytes=args.external_policy.read_bytes(), policy_pin_sha256=args.external_policy_pin,
        public_key_bytes=args.external_public_key.read_bytes(),
        public_key_pin_sha256=args.external_public_key_pin,
        revocation_bytes=args.external_revocation.read_bytes(),
        revocation_pin_sha256=args.external_revocation_pin,
        signature_bytes=args.external_signature.read_bytes(), subject=subject,
        namespace="mmbu.phase1.busi-whu-completed-review.v1",
        principal=args.external_principal, role="review-board-authority",
        signed_at=args.external_signed_at, verified_at=args.now,
        verifier_path=args.external_verifier, verifier_pin_sha256=args.external_verifier_pin,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--primary-review", type=Path, required=True)
    parser.add_argument("--secondary-review", type=Path, required=True)
    parser.add_argument("--adjudication-review", type=Path, required=True)
    parser.add_argument("--rights-review", type=Path, required=True)
    parser.add_argument("--review-opening", type=Path, required=True)
    parser.add_argument("--expected-packet-receipt-digest", required=True)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--authorization-digest", required=True)
    parser.add_argument("--opening-receipt-digest", required=True)
    parser.add_argument("--review-attestation-digest", action="append", required=True)
    parser.add_argument("--clinical-assessment-digest", required=True)
    parser.add_argument("--custodian-assessment-digest", required=True)
    parser.add_argument("--report-created-at", required=True)
    parser.add_argument("--now", required=True)
    _add_external_arguments(parser)
    args = parser.parse_args(argv)
    try:
        base_report = validate_completed_review(
            args.packet,
            args.primary_review,
            args.secondary_review,
            args.adjudication_review,
            args.rights_review,
            args.review_opening,
            expected_packet_receipt_digest=args.expected_packet_receipt_digest,
        )
        store = _load_records(args.records)
        subject = completed_review_authority_subject(
            base_report, sorted(args.review_attestation_digest),
            args.clinical_assessment_digest, args.custodian_assessment_digest,
            report_created_at=args.report_created_at, authenticated_at=args.now,
        )
        report = authenticate_completed_review(
            base_report, store, args.authorization_digest,
            args.opening_receipt_digest, args.review_attestation_digest,
            args.clinical_assessment_digest, args.custodian_assessment_digest,
            report_created_at=args.report_created_at, now=args.now,
            external_authority=_external_authority(args, subject),
        )
        sys.stdout.buffer.write(canonical.dumps(report) + b"\n")
        return 0
    except (
        OSError, ValueError, TypeError, KeyError, csv.Error, ContractViolation,
        canonical.CanonicalJSONError,
    ) as exc:
        sys.stderr.buffer.write(canonical.dumps({"error": str(exc), "status": "invalid"}) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
