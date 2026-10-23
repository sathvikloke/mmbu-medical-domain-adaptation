#!/usr/bin/env python3
"""Write a terminal receipt for the one-shot B2-P Slurm run."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import socket
import stat
import sys
from typing import Any

from mmbu_phase1 import b2_preflight
from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b2-mocs-preflight.json"
SOURCE_PATHS = (
    "config/phase1/b1-mocs-preflight.json",
    "config/phase1/b2-mocs-preflight.json",
    "docs/phase1/b1-pin.json",
    "src/mmbu_phase1/b2_preflight.py",
    "tools/b1_native_preflight.py",
    "tools/b2_finalize.py",
    "tools/b2_native_preflight.py",
    "tools/b2_native_preflight.sbatch",
    "tools/b2_offline_reload.py",
)


def _inventory(root: Path, relative_paths: list[str], label: str) -> list[dict]:
    rows = []
    for relative in sorted(relative_paths, key=lambda value: value.encode("utf-8")):
        path = root / relative
        info = path.lstat()
        f.require(stat.S_ISREG(info.st_mode), f"{label}.{relative}", "must be a regular unaliased file")
        raw = path.read_bytes()
        after = path.lstat()
        before_identity = (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
        after_identity = (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
        f.require(after_identity == before_identity, f"{label}.{relative}", "changed while being inventoried")
        rows.append({"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return rows


def build_terminal_record(
    exit_code: Any, job_id: Any, hostname: Any, started_at: Any, finished_at: Any,
    source_files: Any, evidence_files: Any,
) -> dict:
    exit_code = f.integer(exit_code, "b2.terminal.exit_code", minimum=0, maximum=255)
    job_id = f.text(job_id, "b2.terminal.slurm_job_id")
    f.require(job_id.isdecimal(), "b2.terminal.slurm_job_id", "must contain decimal digits only")
    hostname = f.text(hostname, "b2.terminal.hostname")
    f.timestamp(started_at, "b2.terminal.started_at")
    f.timestamp(finished_at, "b2.terminal.finished_at")
    source_files = f.array(source_files, "b2.terminal.source_files", nonempty=True)
    evidence_files = f.array(evidence_files, "b2.terminal.evidence_files")
    names = [row.get("path") for row in evidence_files if type(row) is dict]
    if exit_code == 0:
        for required in ("native-preflight.json", "offline-reload.json"):
            f.require(required in names, f"b2.terminal.evidence_files.{required}", "missing from successful run")
    return {
        "schema": "mmbu.b2.projector_terminal_run.v1",
        "status": "passed" if exit_code == 0 else "failed",
        "exit_code": exit_code,
        "slurm_job_id": job_id,
        "hostname": hostname,
        "started_at": started_at,
        "finished_at": finished_at,
        "attempt": 2,
        "source_files": source_files,
        "evidence_files": evidence_files,
    }


def run(exit_code: int) -> None:
    config = b2_preflight.load_preflight_config(CONFIG_PATH)
    evidence_root = Path(config["paths"]["evidence_root"])
    evidence_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    evidence_names = [
        path.name for path in evidence_root.iterdir()
        if path.name != "terminal-run.json"
        and not (path.name.startswith("slurm-") and path.suffix in (".out", ".err"))
        and path.is_file() and not path.is_symlink()
    ]
    record = build_terminal_record(
        exit_code, os.environ.get("SLURM_JOB_ID"), socket.gethostname(),
        os.environ.get("B2_STARTED_UTC"),
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        _inventory(REPO, list(SOURCE_PATHS), "b2.terminal.source_files"),
        _inventory(evidence_root, evidence_names, "b2.terminal.evidence_files"),
    )
    (evidence_root / "terminal-run.json").write_bytes(canonical.dumps(record) + b"\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: b2_finalize.py EXIT_CODE")
    run(int(sys.argv[1]))
