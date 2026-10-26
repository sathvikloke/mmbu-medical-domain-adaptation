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
from mmbu_phase1.busi_whu_review import build_review_packet  # noqa: E402


def _load(path: Path) -> dict:
    payload = path.read_bytes()
    value = canonical.loads(payload)
    if canonical.dumps(value) != payload:
        raise ValueError(f"{path.name} is not canonical JSON")
    if type(value) is not dict:
        raise ValueError(f"{path.name} must contain one object")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--metadata-inventory", type=Path, required=True)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = build_review_packet(
            args.archive,
            args.workbook,
            _load(args.metadata_inventory),
            _load(args.selection),
            args.output,
        )
        sys.stdout.buffer.write(canonical.dumps(receipt) + b"\n")
        return 0
    except (OSError, ValueError, TypeError, canonical.CanonicalJSONError, zipfile.BadZipFile) as exc:
        sys.stderr.buffer.write(canonical.dumps({"error": str(exc), "status": "invalid"}) + b"\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
