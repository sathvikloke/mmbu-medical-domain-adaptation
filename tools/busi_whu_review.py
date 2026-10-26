#!/usr/bin/env python3
"""Build a one-shot BUSI-WHU protected human-review packet."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.busi_whu_authority import validate_busi_whu_review_opening  # noqa: E402
from mmbu_phase1.busi_whu_review import build_review_packet  # noqa: E402
from mmbu_phase1.fields import ContractViolation  # noqa: E402
from mmbu_phase1.store import RecordStore  # noqa: E402


def _load(path: Path) -> dict:
    payload = path.read_bytes()
    value = canonical.loads(payload)
    if canonical.dumps(value) != payload:
        raise ValueError(f"{path.name} is not canonical JSON")
    if type(value) is not dict:
        raise ValueError(f"{path.name} must contain one object")
    return value


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
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--authorization-digest", required=True)
    parser.add_argument("--opening-receipt-digest", required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--metadata-inventory", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--source-fingerprint-inventories", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        capability = validate_busi_whu_review_opening(
            _load_records(args.records), args.authorization_digest,
            args.opening_receipt_digest, args.now,
        )
        receipt = build_review_packet(
            capability,
            _load(args.metadata_inventory),
            _load(args.selection),
            _load(args.source_fingerprint_inventories),
        )
        sys.stdout.buffer.write(canonical.dumps(receipt) + b"\n")
        return 0
    except (
        OSError, ValueError, TypeError, ContractViolation,
        canonical.CanonicalJSONError, zipfile.BadZipFile,
    ) as exc:
        sys.stderr.buffer.write(canonical.dumps({"error": str(exc), "status": "invalid"}) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
