#!/usr/bin/env python3
"""CPU-only validator for the sealed BUSI-WHU confirmation protocol."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical, heldout_confirmation
from mmbu_phase1.fields import ContractViolation


def _emit(value: dict) -> None:
    sys.stdout.buffer.write(canonical.dumps(value) + b"\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-spec")
    validate.add_argument("--spec", type=Path, required=True)
    readiness = commands.add_parser("readiness")
    readiness.add_argument("--manifest", type=Path, required=True)
    synthetic = commands.add_parser("synthetic-check")
    synthetic.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-spec":
            heldout_confirmation.load_spec(args.spec)
            _emit({"status": "valid"})
            return 0
        value = canonical.loads(args.manifest.read_bytes())
        result = heldout_confirmation.readiness_status(value)
        if args.command == "synthetic-check":
            result = dict(result, evidence_scope="synthetic_mechanics_only")
        _emit(result)
        return 0 if result["status"] == "ready_for_authorized_execution" else 2
    except (OSError, canonical.CanonicalJSONError, ContractViolation) as exc:
        _emit({"error": str(exc), "status": "invalid"})
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
