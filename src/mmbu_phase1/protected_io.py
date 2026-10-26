"""Descriptor-stable reads for artifacts named by a review capability."""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
from typing import BinaryIO, Iterator

from mmbu_phase1 import fields as f, paths
from mmbu_phase1.busi_whu_authority import ReviewOpeningCapability


@dataclass(frozen=True)
class StatProof:
    device: int
    inode: int
    mode: int
    links: int
    size: int
    modified_ns: int
    changed_ns: int

    @property
    def identity(self) -> tuple[int, int, int, int, int, int, int]:
        return (
            self.device, self.inode, self.mode, self.links, self.size,
            self.modified_ns, self.changed_ns,
        )


def _proof(value: os.stat_result) -> StatProof:
    return StatProof(
        device=value.st_dev,
        inode=value.st_ino,
        mode=value.st_mode,
        links=value.st_nlink,
        size=value.st_size,
        modified_ns=value.st_mtime_ns,
        changed_ns=value.st_ctime_ns,
    )


def _require_safe_ancestors(root: Path, target: Path) -> None:
    current = Path(target.anchor)
    for component in target.parts[1:-1]:
        current = current / component
        info = os.lstat(current)
        f.require(not stat.S_ISLNK(info.st_mode), "protected_io.path", f"symlink ancestor: {current}")
        f.require(stat.S_ISDIR(info.st_mode), "protected_io.path", f"ancestor is not a directory: {current}")
    root_info = os.lstat(root)
    f.require(not stat.S_ISLNK(root_info.st_mode) and stat.S_ISDIR(root_info.st_mode),
              "protected_io.input_root", "input root must be a real directory")


class ProtectedArtifact:
    """An open authorized descriptor that revalidates identity on every read."""

    def __init__(self, fd: int, path: Path, sha256: str, size: int, pre_stat: StatProof):
        self._fd = fd
        self._path = path
        self.sha256 = sha256
        self.size = size
        self.pre_stat = pre_stat
        self.post_stat = pre_stat
        self._closed = False
        self._failed = False

    def _path_proof(self) -> StatProof:
        try:
            value = os.lstat(self._path)
        except OSError as exc:
            raise f.ContractViolation("protected_io.path", f"authorized path is unavailable: {exc}") from exc
        f.require(not stat.S_ISLNK(value.st_mode), "protected_io.path", "authorized path became a symlink")
        return _proof(value)

    def _verify_identity(self, after: StatProof) -> None:
        f.require(after.identity == self.pre_stat.identity, "protected_io.descriptor",
                  "artifact descriptor changed during access")
        f.require(self._path_proof().identity == self.pre_stat.identity, "protected_io.path",
                  "authorized path no longer names the opened artifact")

    def _scan(self, *, retain: bool) -> bytes:
        try:
            f.require(not self._closed, "protected_io.descriptor", "artifact is closed")
            f.require(not self._failed, "protected_io.descriptor", "artifact already failed integrity verification")
            os.lseek(self._fd, 0, os.SEEK_SET)
            digest = hashlib.sha256()
            chunks: list[bytes] = []
            while True:
                block = os.read(self._fd, 1024 * 1024)
                if not block:
                    break
                digest.update(block)
                if retain:
                    chunks.append(block)
            after = _proof(os.fstat(self._fd))
            self._verify_identity(after)
            f.require(after.size == self.size, "protected_io.size", "artifact size differs from authorization")
            f.require(digest.hexdigest() == self.sha256, "protected_io.sha256",
                      "artifact hash differs from authorization")
            self.post_stat = after
            os.lseek(self._fd, 0, os.SEEK_SET)
            return b"".join(chunks)
        except Exception:
            self._failed = True
            raise

    def read(self) -> bytes:
        return self._scan(retain=True)

    @contextmanager
    def stream(self) -> Iterator[BinaryIO]:
        """Yield a duplicate stream and verify descriptor/path stability on exit."""
        self.verify_stable()
        stream = os.fdopen(os.dup(self._fd), "rb", closefd=True)
        try:
            yield stream
        finally:
            stream.close()
            self.verify_stable()

    def verify_stable(self) -> None:
        self._scan(retain=False)

    def close(self) -> None:
        if self._closed:
            return
        try:
            if not self._failed:
                self.verify_stable()
        finally:
            os.close(self._fd)
            self._closed = True

    def __enter__(self) -> "ProtectedArtifact":
        return self

    def __exit__(self, exc_type, exc, traceback) -> bool:
        try:
            self.close()
        except Exception:
            if exc_type is None:
                raise
        return False


def open_authorized_artifact(
    capability: ReviewOpeningCapability,
    logical_path: str,
    role: str,
) -> ProtectedArtifact:
    """Open, hash, and retain exactly one capability-bound regular file."""
    f.require(type(capability) is ReviewOpeningCapability, "protected_io.capability",
              "requires a validated BUSI-WHU review capability")
    paths.relative_path(logical_path, "protected_io.logical_path")
    f.text(role, "protected_io.role")
    matches = [row for row in capability.artifact_bindings if row[0] == logical_path]
    f.require(len(matches) == 1, "protected_io.logical_path", "path is not uniquely authorized")
    bound_path, bound_role, expected_size, expected_hash = matches[0]
    f.require(role == bound_role, "protected_io.role", "role differs from authorization")

    root = Path(capability.input_root)
    f.require(root.is_absolute(), "protected_io.input_root", "must be absolute")
    target = root.joinpath(*Path(bound_path).parts)
    _require_safe_ancestors(root, target)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        raise f.ContractViolation("protected_io.path", f"cannot securely open authorized artifact: {exc}") from exc
    try:
        proof = _proof(os.fstat(fd))
        f.require(stat.S_ISREG(proof.mode), "protected_io.path", "artifact must be a regular file")
        f.require(proof.links == 1, "protected_io.path", "artifact must have exactly one hard link")
        f.require(proof.size == expected_size, "protected_io.size", "artifact size differs from authorization")
        artifact = ProtectedArtifact(fd, target, expected_hash, expected_size, proof)
        artifact.verify_stable()
        return artifact
    except Exception:
        os.close(fd)
        raise


__all__ = ["ProtectedArtifact", "StatProof", "open_authorized_artifact"]
