"""Content-addressed evidence root (``mmbu.phase1.evidence_manifest``) and ``mmbu.phase1.source_state``.

The evidence manifest is computed after every other member, never lists itself,
and its RFC 8785 bytes' SHA-256 is the bundle root retained outside the bundle.
Source state binds commit, clean/dirty state, the canonical patch digest, and an
inventory of every Phase 1 source/test/contract file; the three mutable
execution-state authorities are deliberately excluded to avoid provenance cycles.
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
from typing import Any

from mmbu_phase1 import canonical, fields as f, paths

MANIFEST_NAME = "evidence-manifest.json"
MANIFEST_KEYS = ("schema_id", "schema_version", "bundle_id", "members", "created_at")
MEMBER_KEYS = ("path", "bytes", "sha256", "media_type", "schema_id", "schema_version")
RETENTION_KEYS = ("locator_id", "bundle_id", "root_sha256")
SOURCE_STATE_KEYS = ("schema_id", "schema_version", "commit_sha", "dirty", "patch_sha256", "inventory", "created_at",
                     "record_digest")
INVENTORY_KEYS = ("path", "bytes", "sha256", "class")
INVENTORY_CLASSES = ("source", "test", "config", "contract", "lock")
MUTABLE_AUTHORITIES = frozenset({"config/phase1/current-status.json", "config/phase1/authorization-registry.json",
                                 "config/phase1/opening-receipt-registry.json"})
MEDIA_TYPES = {".json": "application/json", ".md": "text/markdown", ".patch": "text/x-diff", ".stdout": "text/plain",
               ".stderr": "text/plain", ".txt": "text/plain"}


def media_type(path: str) -> str:
    return MEDIA_TYPES.get(PurePosixPath(path).suffix, "application/octet-stream")


def schema_of(data: bytes) -> tuple[str | None, int | None]:
    try:
        value = canonical.loads_canonical(data)
    except canonical.CanonicalJSONError:
        return None, None
    if type(value) is dict and type(value.get("schema_id")) is str and value["schema_id"].startswith(f.SCHEMA_PREFIX):
        return value["schema_id"], value.get("schema_version")
    return None, None


def walk_bundle(root: Path) -> list[str]:
    """Every member path; any symlink, special file, or hard link fails closed."""
    root = Path(root)
    members = []
    for directory, dirnames, filenames in os.walk(root, followlinks=False):
        for name in dirnames:
            info = os.lstat(os.path.join(directory, name))
            f.require(not stat.S_ISLNK(info.st_mode), "bundle", f"symlinked directory {name!r} is forbidden")
        for name in filenames:
            full = os.path.join(directory, name)
            info = os.lstat(full)
            relative = os.path.relpath(full, root).replace(os.sep, "/")
            f.require(stat.S_ISREG(info.st_mode), "bundle", f"{relative} is not a regular file")
            f.require(info.st_nlink == 1, "bundle", f"{relative} is a hard-link alias")
            members.append(relative)
    return sorted(members, key=lambda p: p.encode("utf-8"))


def build_evidence_manifest(root: Path, bundle_id: str, created_at: str) -> tuple[dict, str]:
    """Compute the manifest last over every other member and write it; return (manifest, root digest)."""
    root = Path(root)
    f.require(not os.path.lexists(root / MANIFEST_NAME), MANIFEST_NAME, "the evidence manifest is computed exactly once")
    members = []
    for relative in walk_bundle(root):
        paths.relative_path(relative, relative)
        data = paths.member_bytes(root, relative)
        schema_id, version = schema_of(data)
        members.append({"path": relative, "bytes": len(data), "sha256": canonical.raw_digest(data),
                        "media_type": media_type(relative), "schema_id": schema_id, "schema_version": version})
    paths.unique_paths([m["path"] for m in members], "evidence_manifest.members")
    manifest = {"schema_id": f.SCHEMA_PREFIX + "evidence_manifest", "schema_version": 1, "bundle_id": bundle_id,
                "members": members, "created_at": created_at}
    validate_evidence_manifest_record(manifest)
    data = canonical.dumps(manifest)
    descriptor = os.open(root / MANIFEST_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
    return manifest, canonical.raw_digest(data)


def validate_evidence_manifest_record(record: Any, path: str = "evidence_manifest") -> dict:
    f.header(record, "evidence_manifest", path)
    f.closed(record, path, MANIFEST_KEYS)
    f.text(record["bundle_id"], f"{path}.bundle_id")
    members = f.array(record["members"], f"{path}.members", nonempty=True)
    for index, member in enumerate(members):
        label = f"{path}.members[{index}]"
        f.closed(member, label, MEMBER_KEYS)
        paths.relative_path(member["path"], f"{label}.path")
        f.require(member["path"] != MANIFEST_NAME, f"{label}.path", "the manifest never lists itself")
        f.integer(member["bytes"], f"{label}.bytes", minimum=0)
        f.digest(member["sha256"], f"{label}.sha256")
        f.text(member["media_type"], f"{label}.media_type")
        governed = (member["schema_id"] is None, member["schema_version"] is None)
        f.require(governed[0] == governed[1], label, "schema_id and schema_version are both null or both non-null")
        if member["schema_id"] is not None:
            f.text(member["schema_id"], f"{label}.schema_id")
            f.literal(member["schema_version"], f"{label}.schema_version", 1)
    f.sorted_unique(members, f"{path}.members", lambda m: m["path"].encode("utf-8"))
    paths.unique_paths([m["path"] for m in members], f"{path}.members")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def retention_receipt(locator_id: str, bundle_id: str, root_sha256: str) -> dict:
    return {"bundle_id": bundle_id, "locator_id": locator_id, "root_sha256": root_sha256}


def validate_retention_receipt(record: Any, path: str = "retention_receipt") -> dict:
    f.closed(record, path, RETENTION_KEYS)
    f.text(record["locator_id"], f"{path}.locator_id")
    f.text(record["bundle_id"], f"{path}.bundle_id")
    f.digest(record["root_sha256"], f"{path}.root_sha256")
    return record


def verify_bundle_root(root: Path, receipt: dict) -> dict:
    """Validate the completed manifest against the bundle bytes and the external root."""
    root = Path(root)
    validate_retention_receipt(receipt)
    raw = paths.member_bytes(root, MANIFEST_NAME)
    manifest = validate_evidence_manifest_record(canonical.loads_canonical(raw))
    f.require(canonical.raw_digest(raw) == receipt["root_sha256"], "evidence_manifest",
              "bundle root differs from the externally retained root (deletion/replacement/rename/reorder/alias)")
    f.require(manifest["bundle_id"] == receipt["bundle_id"], "evidence_manifest.bundle_id", "differs from retention receipt")
    present = [p for p in walk_bundle(root) if p != MANIFEST_NAME]
    listed = [m["path"] for m in manifest["members"]]
    f.require(present == listed, "evidence_manifest.members", "members must cover every other bundle file exactly once")
    receipt_bytes = canonical.dumps(receipt)
    for member in manifest["members"]:
        data = paths.member_bytes(root, member["path"])
        f.require(len(data) == member["bytes"] and canonical.raw_digest(data) == member["sha256"],
                  "evidence_manifest.members", f"{member['path']} bytes differ from the manifest")
        f.require(schema_of(data) == (member["schema_id"], member["schema_version"]), "evidence_manifest.members",
                  f"{member['path']} schema fields differ from its bytes")
        f.require(data != receipt_bytes, "evidence_manifest.members", "the retention receipt cannot be a bundle member")
    return manifest


# ---------------------------------------------------------------------------
# Source state


def _git(root: Path, *args: str, ok: tuple[int, ...] = (0,)) -> bytes:
    command = ["git", "-c", "core.quotepath=true", "-c", "diff.noprefix=false", "-c", "diff.mnemonicprefix=false",
               "-c", "diff.relative=false", "-c", "diff.renames=false", "-c", "color.ui=false", *args]
    result = subprocess.run(command, cwd=root, capture_output=True, check=False)
    if result.returncode not in ok:
        f.fail("source_state", f"git {' '.join(args)} failed: {result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def canonical_patch(root: Path) -> bytes:
    """Binary diff of tracked staged+unstaged changes against HEAD plus every untracked non-ignored file."""
    root = Path(root)
    patch = _git(root, "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff", "--no-renames",
                 "--src-prefix=a/", "--dst-prefix=b/", "HEAD", "--")
    untracked = [p.decode("utf-8") for p in _git(root, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    for relative in sorted(untracked, key=lambda p: p.encode("utf-8")):
        patch += _git(root, "diff", "--binary", "--full-index", "--no-color", "--no-ext-diff", "--no-index",
                      "--src-prefix=a/", "--dst-prefix=b/", "--", "/dev/null", relative, ok=(0, 1))
    return patch


def inventory_paths(root: Path) -> list[tuple[str, str]]:
    """Every Phase 1 source, test, and binding-contract file (mutable authorities excluded)."""
    root = Path(root)
    found: list[tuple[str, str]] = []
    for base, kind in (("src/mmbu_phase1", "source"), ("tests/phase1", "test"), ("docs/phase1", "contract"),
                       ("config/phase1", "config")):
        for directory, dirnames, filenames in os.walk(root / base):
            dirnames[:] = sorted(d for d in dirnames if d != "__pycache__")
            for name in filenames:
                if name.endswith(".pyc"):
                    continue
                relative = os.path.relpath(os.path.join(directory, name), root).replace(os.sep, "/")
                if relative in MUTABLE_AUTHORITIES:
                    continue
                found.append((relative, kind))
    found.append(("tools/team.py", "source"))
    return sorted(found, key=lambda item: item[0].encode("utf-8"))


def build_inventory(root: Path) -> list[dict]:
    rows = []
    for relative, kind in inventory_paths(root):
        data = paths.member_bytes(Path(root), relative)
        rows.append({"path": relative, "bytes": len(data), "sha256": canonical.raw_digest(data), "class": kind})
    return rows


def build_source_state(root: Path, created_at: str) -> tuple[dict, bytes]:
    root = Path(root)
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all")
    dirty = bool(status.strip())
    patch = canonical_patch(root) if dirty else b""
    record = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "source_state", "schema_version": 1, "commit_sha": commit, "dirty": dirty,
        "patch_sha256": canonical.raw_digest(patch) if dirty else None, "inventory": build_inventory(root),
        "created_at": created_at})
    validate_source_state(record)
    return record, patch


def validate_source_state(record: Any, path: str = "source_state") -> dict:
    f.record(record, "source_state", SOURCE_STATE_KEYS, path)
    commit = f.text(record["commit_sha"], f"{path}.commit_sha")
    f.require(len(commit) == 40 and all(c in "0123456789abcdef" for c in commit), f"{path}.commit_sha",
              "must be 40 lowercase hexadecimal characters")
    dirty = f.boolean(record["dirty"], f"{path}.dirty")
    if dirty:
        f.digest(record["patch_sha256"], f"{path}.patch_sha256")
    else:
        f.require(record["patch_sha256"] is None, f"{path}.patch_sha256", "null exactly when the tree is clean")
    rows = f.array(record["inventory"], f"{path}.inventory", nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}.inventory[{index}]"
        f.closed(row, label, INVENTORY_KEYS)
        paths.relative_path(row["path"], f"{label}.path")
        f.integer(row["bytes"], f"{label}.bytes", minimum=0)
        f.digest(row["sha256"], f"{label}.sha256")
        f.one_of(row["class"], f"{label}.class", INVENTORY_CLASSES)
        f.require(row["path"] not in MUTABLE_AUTHORITIES, f"{label}.path",
                  "mutable execution-state authorities are excluded from source state")
    f.sorted_unique(rows, f"{path}.inventory", lambda row: row["path"].encode("utf-8"))
    paths.unique_paths([row["path"] for row in rows], f"{path}.inventory")
    for required in ("docs/phase1/contract-manifest.json", "tools/team.py"):
        f.require(any(row["path"] == required for row in rows), f"{path}.inventory", f"must cover {required}")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def check_source_state(record: dict, root: Path, patch: bytes | None = None, path: str = "source_state") -> dict:
    """Detect dirty-tree lies, patch-digest changes, inventory omission, and post-evidence drift."""
    validate_source_state(record, path)
    root = Path(root)
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    f.require(record["commit_sha"] == commit, f"{path}.commit_sha", "differs from the checkout HEAD")
    dirty = bool(_git(root, "status", "--porcelain=v1", "--untracked-files=all").strip())
    f.require(record["dirty"] == dirty, f"{path}.dirty", "clean/dirty state is misreported")
    if dirty:
        current = canonical_patch(root)
        f.require(canonical.raw_digest(current) == record["patch_sha256"], f"{path}.patch_sha256",
                  "canonical patch changed after source state was recorded")
        if patch is not None:
            f.require(canonical.raw_digest(patch) == record["patch_sha256"], f"{path}.patch_sha256",
                      "bundled patch bytes differ from the recorded digest")
    f.require(f.same(record["inventory"], build_inventory(root)), f"{path}.inventory",
              "Phase 1 source/test/contract bytes drifted or the inventory omits a file")
    return record
