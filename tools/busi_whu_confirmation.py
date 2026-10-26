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
            result = heldout_confirmation.build_authenticated_randomization_artifacts(
                _load_canonical(args.review_report), _load_canonical(args.source_manifest),
                _store(args.records),
                args.source_admission_digest, args.confirmation_purpose_digest,
                args.created_at,
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
