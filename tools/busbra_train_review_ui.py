#!/usr/bin/env python3
"""Generate a verified self-contained BUS-BRA train-review HTML file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from mmbu_phase1.busbra_train_review_ui import build_review_ui


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet_dir", type=Path)
    parser.add_argument("--expected-receipt-digest", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        receipt = build_review_ui(
            args.packet_dir, args.expected_receipt_digest, args.output,
        )
    except (FileExistsError, KeyError, OSError, TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
