#!/usr/bin/env python3
"""Preserve terminal evidence for the one-shot dual-objective preflight."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys

from mmbu_phase1 import b2_dual_preflight, canonical
from mmbu_phase1 import fields as f


REPO = Path(__file__).resolve().parents[1]
CONFIG = REPO / "config/phase1/b2-dual-objective-preflight.json"
SOURCES = (
    "config/phase1/b2-dual-objective-preflight.json", "src/mmbu_phase1/b2_dual_preflight.py",
    "src/mmbu_phase1/dual_objective.py", "tools/b1_native_preflight.py",
    "tools/b2_native_preflight.py", "tools/b2_dual_objective_preflight.py",
    "tools/b2_dual_finalize.py", "tools/b2_dual_objective_preflight.sbatch",
)


def inventory(path: Path, relative: str) -> dict:
    raw = path.read_bytes()
    return {"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def run(exit_code: int) -> None:
    config = b2_dual_preflight.load_preflight_config(CONFIG)
    evidence = Path(config["paths"]["evidence_root"])
    result_path = evidence / "native-dual-objective.json"
    passed = exit_code == 0 and result_path.is_file()
    if passed:
        result = canonical.loads(result_path.read_bytes())
        f.literal(result.get("status"), "result.status", "passed")
    terminal = {
        "schema": "mmbu.b2.dual_objective_terminal.v1", "attempt": 3,
        "status": "passed" if passed else "failed", "exit_code": exit_code,
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"), "hostname": os.uname().nodename,
        "started_at": os.environ.get("B2_DUAL_STARTED_UTC"),
        "finished_at": f.utc_now(),
        "source_files": [inventory(REPO / name, name) for name in SOURCES],
        "evidence_files": [inventory(path, path.name) for path in sorted(evidence.glob("*.json"))
                           if path.name != "terminal-run.json" and path.is_file() and not path.is_symlink()],
    }
    (evidence / "terminal-run.json").write_bytes(canonical.dumps(terminal) + b"\n")


if __name__ == "__main__":
    run(int(sys.argv[1]))
