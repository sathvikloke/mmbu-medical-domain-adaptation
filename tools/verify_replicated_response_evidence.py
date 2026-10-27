#!/usr/bin/env python3
"""Cold-review verifier for the portable replicated-response evidence bundle."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical, replicated_response  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    arguments = parser.parse_args()
    receipt = canonical.loads(arguments.receipt.read_bytes())
    summary = replicated_response.verify_portable_evidence_bundle(arguments.bundle, receipt)
    sys.stdout.buffer.write(canonical.dumps(summary) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
