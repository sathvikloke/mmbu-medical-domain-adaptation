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
    validate_completed_review,
)
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
        report = authenticate_completed_review(
            base_report, _load_records(args.records), args.authorization_digest,
            args.opening_receipt_digest, args.review_attestation_digest,
            args.clinical_assessment_digest, args.custodian_assessment_digest,
            report_created_at=args.report_created_at, now=args.now,
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
