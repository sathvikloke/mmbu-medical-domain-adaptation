#!/usr/bin/env python3
"""Freeze a label-blind ChestMNIST patient-role allocation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.chestmnist_intake import freeze_official_patient_roles  # noqa: E402


def _stage(parent: Path, prefix: str, payload: bytes) -> Path:
    descriptor, name = tempfile.mkstemp(prefix=prefix, dir=parent)
    staged = Path(name)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short write while publishing ChestMNIST split evidence")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.chmod(staged, 0o444)
    return staged


def _publish_pair(roles_path: Path, roles: bytes, receipt_path: Path, receipt: bytes) -> None:
    if roles_path.parent != receipt_path.parent:
        raise ValueError("roles and receipt outputs must share one parent directory")
    parent = roles_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if roles_path.exists() or roles_path.is_symlink() or receipt_path.exists() or receipt_path.is_symlink():
        raise FileExistsError("both output paths must be new")
    staged_roles = _stage(parent, ".chestmnist-roles-", roles)
    staged_receipt = _stage(parent, ".chestmnist-receipt-", receipt)
    roles_published = False
    try:
        os.link(staged_roles, roles_path, follow_symlinks=False)
        roles_published = True
        try:
            os.link(staged_receipt, receipt_path, follow_symlinks=False)
        except BaseException:
            if roles_published and roles_path.stat(follow_symlinks=False).st_ino == staged_roles.stat().st_ino:
                roles_path.unlink()
            raise
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        staged_roles.unlink(missing_ok=True)
        staged_receipt.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--official-train-val", type=Path, required=True)
    parser.add_argument("--official-test", type=Path, required=True)
    parser.add_argument("--roles-output", type=Path, required=True)
    parser.add_argument("--receipt-output", type=Path, required=True)
    arguments = parser.parse_args()
    if arguments.roles_output == arguments.receipt_output:
        raise ValueError("roles and receipt outputs must be different paths")
    roles, receipt = freeze_official_patient_roles(
        arguments.official_train_val.read_bytes(),
        arguments.official_test.read_bytes(),
    )
    _publish_pair(
        arguments.roles_output,
        roles,
        arguments.receipt_output,
        canonical.dumps(receipt) + b"\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
