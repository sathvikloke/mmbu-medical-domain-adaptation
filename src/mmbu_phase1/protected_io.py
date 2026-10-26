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


def _required_open_flag(name: str) -> int:
    value = getattr(os, name, None)
    f.require(type(value) is int and value != 0, "protected_io.platform",
              f"secure descriptor opening requires {name}")
    return value


def _directory_flags() -> int:
    return (
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | _required_open_flag("O_NOFOLLOW")
        | _required_open_flag("O_DIRECTORY")
    )


def _open_directory(parent_fd: int, component: str, path: str) -> int:
    try:
        descriptor = os.open(component, _directory_flags(), dir_fd=parent_fd)
    except OSError as exc:
        raise f.ContractViolation("protected_io.path", f"cannot securely open directory {path}: {exc}") from exc
    try:
        f.require(stat.S_ISDIR(os.fstat(descriptor).st_mode), "protected_io.path",
                  f"ancestor is not a directory: {path}")
        return descriptor
    except Exception:
        os.close(descriptor)
        raise


def _open_authorized_parent(root: Path, bound_path: str) -> tuple[int, str]:
    """Retain every directory by descriptor so ancestor replacement cannot redirect lookup."""
    try:
        current_fd = os.open(root.anchor, _directory_flags())
    except OSError as exc:
        raise f.ContractViolation("protected_io.input_root", f"cannot securely open filesystem root: {exc}") from exc
    current_path = root.anchor
    try:
        for component in root.parts[1:]:
            next_path = str(Path(current_path) / component)
            next_fd = _open_directory(current_fd, component, next_path)
            os.close(current_fd)
            current_fd = next_fd
            current_path = next_path
        components = Path(bound_path).parts
        for component in components[:-1]:
            next_path = str(Path(current_path) / component)
            next_fd = _open_directory(current_fd, component, next_path)
            os.close(current_fd)
            current_fd = next_fd
            current_path = next_path
        return current_fd, components[-1]
    except Exception:
        os.close(current_fd)
        raise


class ProtectedArtifact:
    """An open authorized descriptor that revalidates identity on every read."""

    def __init__(
        self, fd: int, parent_fd: int, final_name: str, path: Path,
        sha256: str, size: int, pre_stat: StatProof,
    ):
        self._fd = fd
        self._parent_fd = parent_fd
        self._final_name = final_name
        self._path = path
        self.sha256 = sha256
        self.size = size
        self.pre_stat = pre_stat
        self.post_stat = pre_stat
        self._closed = False
        self._failed = False

    def _path_proof(self) -> StatProof:
        try:
            value = os.stat(self._final_name, dir_fd=self._parent_fd, follow_symlinks=False)
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
            os.close(self._parent_fd)
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
    f.require(capability.external_authority_evidence_digest is not None,
              "protected_io.capability", "requires independently verified external opening authority")
    f.digest(capability.external_authority_evidence_digest,
             "protected_io.capability.external_authority_evidence_digest")
    f.text(capability.external_authority_principal,
           "protected_io.capability.external_authority_principal")
    paths.relative_path(logical_path, "protected_io.logical_path")
    f.text(role, "protected_io.role")
    matches = [row for row in capability.artifact_bindings if row[0] == logical_path]
    f.require(len(matches) == 1, "protected_io.logical_path", "path is not uniquely authorized")
    bound_path, bound_role, expected_size, expected_hash = matches[0]
    f.require(role == bound_role, "protected_io.role", "role differs from authorization")

    root = Path(capability.input_root)
    f.require(root.is_absolute(), "protected_io.input_root", "must be absolute")
    target = root.joinpath(*Path(bound_path).parts)
    parent_fd, final_name = _open_authorized_parent(root, bound_path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | _required_open_flag("O_NOFOLLOW")
    try:
        fd = os.open(final_name, flags, dir_fd=parent_fd)
    except OSError as exc:
        os.close(parent_fd)
        raise f.ContractViolation("protected_io.path", f"cannot securely open authorized artifact: {exc}") from exc
    try:
        proof = _proof(os.fstat(fd))
        f.require(stat.S_ISREG(proof.mode), "protected_io.path", "artifact must be a regular file")
        f.require(proof.links == 1, "protected_io.path", "artifact must have exactly one hard link")
        f.require(proof.size == expected_size, "protected_io.size", "artifact size differs from authorization")
        artifact = ProtectedArtifact(fd, parent_fd, final_name, target, expected_hash, expected_size, proof)
        artifact.verify_stable()
        return artifact
    except Exception:
        os.close(fd)
        os.close(parent_fd)
        raise


__all__ = ["ProtectedArtifact", "StatProof", "open_authorized_artifact"]
