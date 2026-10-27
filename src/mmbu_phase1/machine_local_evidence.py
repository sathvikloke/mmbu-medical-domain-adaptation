"""Closed identity for evidence that exists only in one machine-local checkout."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mmbu_phase1 import canonical, fields as f, paths


MANIFEST_KEYS = (
    "schema_id", "schema_version", "classification", "excluded_patterns",
    "roots", "record_digest",
)
ROOT_KEYS = (
    "path", "file_count", "total_bytes", "inventory_digest", "authority",
)
EXCLUDED_PATTERNS = ["**/__pycache__/**", "**/*.pyc"]


def _validate_manifest(value: Any, path: str = "machine_local_evidence_roots") -> dict:
    f.record(value, "machine_local_evidence_roots", MANIFEST_KEYS, path)
    f.literal(value["classification"], f"{path}.classification", "machine_local_unversioned")
    f.literal(value["excluded_patterns"], f"{path}.excluded_patterns", EXCLUDED_PATTERNS)
    roots = f.array(value["roots"], f"{path}.roots", nonempty=True)
    for index, row in enumerate(roots):
        label = f"{path}.roots[{index}]"
        f.closed(row, label, ROOT_KEYS)
        paths.relative_path(row["path"], f"{label}.path")
        f.integer(row["file_count"], f"{label}.file_count", minimum=1)
        f.integer(row["total_bytes"], f"{label}.total_bytes", minimum=1)
        f.digest(row["inventory_digest"], f"{label}.inventory_digest")
        f.literal(row["authority"], f"{label}.authority", "none")
    f.sorted_unique(roots, f"{path}.roots", lambda row: row["path"].encode("utf-8"))
    return value


def load_manifest(path: Path) -> dict:
    payload = path.read_bytes()
    value = canonical.loads(payload)
    canonical_payload = canonical.dumps(value)
    f.require(
        payload in (canonical_payload, canonical_payload + b"\n"),
        str(path),
        "must contain canonical JSON with at most one terminal LF",
    )
    return _validate_manifest(value, str(path))


def _inventory(root: Path) -> tuple[int, int, str]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        payload = path.read_bytes()
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "bytes": len(payload),
            "sha256": canonical.raw_digest(payload),
        })
    return len(rows), sum(row["bytes"] for row in rows), canonical.value_digest(rows)


def verify_machine_local_roots(manifest: Any, checkout_root: Path) -> list[dict]:
    manifest = _validate_manifest(manifest)
    statuses = []
    for row in manifest["roots"]:
        root = checkout_root / row["path"]
        if not root.exists():
            statuses.append({"path": row["path"], "status": "absent", "authority": "none"})
            continue
        f.require(root.is_dir() and not root.is_symlink(), row["path"], "must be one local directory")
        file_count, total_bytes, inventory_digest = _inventory(root)
        f.require(file_count == row["file_count"], row["path"], "file count differs from recorded root")
        f.require(total_bytes == row["total_bytes"], row["path"], "byte count differs from recorded root")
        f.require(inventory_digest == row["inventory_digest"], row["path"], "inventory digest differs")
        statuses.append({"path": row["path"], "status": "matched", "authority": "none"})
    return statuses


__all__ = ["load_manifest", "verify_machine_local_roots"]
