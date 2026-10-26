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
from mmbu_phase1.busi_whu_review_validation import validate_completed_review  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("--primary-review", type=Path, required=True)
    parser.add_argument("--secondary-review", type=Path, required=True)
    parser.add_argument("--adjudication-review", type=Path, required=True)
    parser.add_argument("--rights-review", type=Path, required=True)
    parser.add_argument("--review-opening", type=Path, required=True)
    parser.add_argument("--expected-packet-receipt-digest", required=True)
    args = parser.parse_args(argv)
    try:
        report = validate_completed_review(
            args.packet,
            args.primary_review,
            args.secondary_review,
            args.adjudication_review,
            args.rights_review,
            args.review_opening,
            expected_packet_receipt_digest=args.expected_packet_receipt_digest,
        )
        sys.stdout.buffer.write(canonical.dumps(report) + b"\n")
        return 0
    except (OSError, ValueError, TypeError, KeyError, csv.Error, canonical.CanonicalJSONError) as exc:
        sys.stderr.buffer.write(canonical.dumps({"error": str(exc), "status": "invalid"}) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
