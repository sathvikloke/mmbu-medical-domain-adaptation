#!/usr/bin/env python3
"""Acquire one exact F0 model snapshot without importing a model runtime."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import traceback

from huggingface_hub import HfApi, snapshot_download

from mmbu_phase1 import canonical, model_feasibility
from mmbu_phase1 import fields as f


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_receipt(path: Path, value: dict) -> None:
    f.require(not path.exists() and not path.is_symlink(), "f0.acquisition.receipt", "already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical.dumps(value) + b"\n")


def inventory(root: Path) -> tuple[list[dict], int]:
    rows = []
    total = 0
    for path in sorted((item for item in root.rglob("*") if item.is_file()),
                       key=lambda item: str(item.relative_to(root)).encode("utf-8")):
        size = path.stat().st_size
        total += size
        rows.append({"bytes": size, "path": str(path.relative_to(root))})
    f.require(bool(rows), "f0.acquisition.snapshot", "contains no files")
    return rows, total


def run(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    manifest_raw = manifest_path.read_bytes()
    manifest = model_feasibility.validate_manifest(canonical.loads(manifest_raw))
    candidate = model_feasibility.candidate_by_index(manifest, args.candidate_index)
    destination = Path(args.snapshot_root).resolve() / candidate["candidate_id"]
    receipt = Path(args.receipt_root).resolve() / f"candidate-{args.candidate_index}.json"
    f.require(not destination.exists() and not destination.is_symlink(),
              "f0.acquisition.destination", "already exists")
    started_at = utc_now()
    base = {
        "candidate": candidate,
        "ended_at": None,
        "error": None,
        "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
        "model_loaded": False,
        "schema_id": "mmbu.phase1.model_feasibility_acquisition",
        "schema_version": 1,
        "snapshot": str(destination),
        "started_at": started_at,
        "status": "failed",
    }
    try:
        info = HfApi().model_info(repo_id=candidate["model_id"], revision=candidate["revision"])
        f.literal(info.sha, "f0.acquisition.resolved_revision", candidate["revision"])
        returned = snapshot_download(
            repo_id=candidate["model_id"], revision=candidate["revision"],
            local_dir=str(destination), max_workers=4,
        )
        f.literal(Path(returned).resolve(), "f0.acquisition.returned_path", destination)
        files, total = inventory(destination)
        base.update({
            "ended_at": utc_now(),
            "files": files,
            "resolved_revision": info.sha,
            "status": "passed",
            "total_bytes": total,
        })
        write_receipt(receipt, base)
        return 0
    except Exception as exc:
        base.update({
            "ended_at": utc_now(),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
        })
        write_receipt(receipt, base)
        return 2


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--candidate-index", required=True, type=int)
    parser.add_argument("--snapshot-root", required=True)
    parser.add_argument("--receipt-root", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(arguments()))
