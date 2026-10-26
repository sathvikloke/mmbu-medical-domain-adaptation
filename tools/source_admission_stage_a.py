#!/usr/bin/env python3
"""Build and verify Stage A source-admission packets without opening data."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from mmbu_phase1 import canonical  # noqa: E402
from mmbu_phase1.source_admission_stage_a import (  # noqa: E402
    build_acquisition_packet,
    load_stage_a_config,
    validate_acquisition_packet,
)


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        raise


def build_packet(args: argparse.Namespace) -> int:
    config = load_stage_a_config(args.config)
    commit = args.repository_commit or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=REPO, text=True
    ).strip()
    now = datetime.now(timezone.utc)
    launch_id = args.launch_id or now.strftime("%Y%m%dT%H%M%SZ-") + str(uuid.uuid4())
    run_root = args.run_root or f"/storage/scr/npl015/mmbu-admission/{launch_id}"
    created_at = args.created_at or now.isoformat(timespec="seconds").replace("+00:00", "Z")
    packet = build_acquisition_packet(config, commit, launch_id, run_root, created_at)
    payload = canonical.dumps(packet)
    _write_new(args.output, payload)
    print(f"canonical_digest={packet['record_digest']}")
    print(f"full_file_sha256={hashlib.sha256(payload).hexdigest()}")
    print(f"launch_id={launch_id}")
    print(f"run_root={run_root}")
    return 0


def verify_packet(args: argparse.Namespace) -> int:
    config = load_stage_a_config(args.config)
    payload = args.packet.read_bytes()
    packet = canonical.loads(payload)
    if canonical.dumps(packet) != payload:
        raise ValueError("packet file is not canonical RFC 8785 JSON")
    validate_acquisition_packet(packet, config)
    print(f"canonical_digest={packet['record_digest']}")
    print(f"full_file_sha256={hashlib.sha256(payload).hexdigest()}")
    return 0


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser()
    sub = cli.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build-packet")
    build.add_argument("--config", type=Path, default=REPO / "config/phase1/source-admission-stage-a.json")
    build.add_argument("--repository-commit")
    build.add_argument("--launch-id")
    build.add_argument("--run-root")
    build.add_argument("--created-at")
    build.add_argument("--output", type=Path, required=True)
    build.set_defaults(func=build_packet)
    verify = sub.add_parser("verify-packet")
    verify.add_argument("--config", type=Path, default=REPO / "config/phase1/source-admission-stage-a.json")
    verify.add_argument("--packet", type=Path, required=True)
    verify.set_defaults(func=verify_packet)
    return cli


def main() -> int:
    args = parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
