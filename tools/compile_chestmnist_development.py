#!/usr/bin/env python3
"""Compile a frozen ChestMNIST development manifest from official NIH metadata."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.chestmnist_intake import compile_official_development_manifest  # noqa: E402


def _write_new(path: Path, payload: bytes) -> None:
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o444)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while publishing development manifest")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--official-train-val", type=Path, required=True)
    parser.add_argument("--official-test", type=Path, required=True)
    parser.add_argument("--patient-roles", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    result = compile_official_development_manifest(
        arguments.mapping.read_bytes(),
        arguments.official_train_val.read_bytes(),
        arguments.official_test.read_bytes(),
        arguments.patient_roles.read_bytes(),
    )
    _write_new(arguments.output, canonical.dumps(result) + b"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
