#!/usr/bin/env python3
"""Audit a local ChestMNIST public mapping without opening labels or pixels."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.chestmnist_intake import audit_mapping_bytes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--train-count", type=int, required=True)
    parser.add_argument("--val-count", type=int, required=True)
    parser.add_argument("--test-count", type=int, required=True)
    parser.add_argument("--patient-count", type=int)
    arguments = parser.parse_args()
    result = audit_mapping_bytes(
        arguments.mapping.read_bytes(),
        expected_split_counts={
            "train": arguments.train_count,
            "val": arguments.val_count,
            "test": arguments.test_count,
        },
        expected_patient_count=arguments.patient_count,
    )
    sys.stdout.buffer.write(canonical.dumps(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
