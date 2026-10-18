"""Normalized path rules for repository, evidence, and launch paths."""

from __future__ import annotations

import os
from pathlib import Path
import posixpath
import stat
import unicodedata
from typing import Any, Iterable

from mmbu_phase1.fields import ContractViolation, fail, text


def _common(value: str, path: str) -> None:
    if "\\" in value or "\x00" in value:
        fail(path, "must not contain a backslash or NUL")
    if unicodedata.normalize("NFC", value) != value:
        fail(path, "must be Unicode NFC (normalization alias)")


def relative_path(value: Any, path: str) -> str:
    """A nonempty normalized relative POSIX path with no traversal."""
    text(value, path)
    _common(value, path)
    if value.startswith("/"):
        fail(path, "must be relative")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        fail(path, "must not contain empty, '.', or '..' components")
    if posixpath.normpath(value) != value:
        fail(path, "must equal its lexical normalization")
    return value


def unique_paths(values: Iterable[str], path: str) -> None:
    """Reject exact, Unicode-normalization, and case-fold aliases."""
    seen_exact: set[str] = set()
    seen_folded: dict[str, str] = {}
    for value in values:
        if value in seen_exact:
            fail(path, f"duplicate path {value!r}")
        seen_exact.add(value)
        folded = unicodedata.normalize("NFC", unicodedata.normalize("NFC", value).casefold())
        if folded in seen_folded:
            fail(path, f"case-fold or normalization collision between {seen_folded[folded]!r} and {value!r}")
        seen_folded[folded] = value


def absolute_path(value: Any, path: str) -> str:
    """An absolute normalized POSIX NFC path with no alias components."""
    text(value, path)
    _common(value, path)
    if not value.startswith("/") or value.startswith("//"):
        fail(path, "must be absolute with a single leading slash")
    if value != "/":
        parts = value.split("/")[1:]
        if any(part in {"", ".", ".."} for part in parts):
            fail(path, "must not contain empty, '.', or '..' components")
    if posixpath.normpath(value) != value:
        fail(path, "must equal its lexical normalization")
    return value


def lstat_chain(value: str, path: str = "path") -> list[os.stat_result]:
    """``lstat`` every component from ``/``; any symlink or missing part fails."""
    absolute_path(value, path)
    results = [os.lstat("/")]
    current = ""
    for part in value.split("/")[1:] if value != "/" else []:
        current += "/" + part
        try:
            info = os.lstat(current)
        except OSError as exc:
            fail(path, f"component {current!r} is missing or unreadable ({exc.strerror})")
        if stat.S_ISLNK(info.st_mode):
            fail(path, f"component {current!r} is a symlink")
        results.append(info)
    return results


def member_bytes(root: Path, relative: str, path: str | None = None) -> bytes:
    """Read a regular, non-symlink, non-hard-linked file below ``root``."""
    label = path or relative
    relative_path(relative, label)
    current = Path(root)
    parts = relative.split("/")
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = os.lstat(current)
        except OSError as exc:
            fail(label, f"missing component {part!r} ({exc.strerror})")
        if stat.S_ISLNK(info.st_mode):
            fail(label, f"symlink component {part!r} is forbidden")
        if index < len(parts) - 1 and not stat.S_ISDIR(info.st_mode):
            fail(label, f"ancestor {part!r} is not a directory")
    if not stat.S_ISREG(info.st_mode):
        fail(label, "must be a regular file")
    if info.st_nlink != 1:
        fail(label, "hard-link alias is forbidden (link count must be 1)")
    descriptor = os.open(current, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            fail(label, "file changed between lstat and open")
        chunks = []
        while True:
            chunk = os.read(descriptor, 1 << 20)
            if not chunk:
                break
            chunks.append(chunk)
        finished = os.fstat(descriptor)
        identity = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)  # noqa: E731
        if identity(opened) != identity(finished):
            fail(label, "file changed while it was being read")
        if sum(map(len, chunks)) != opened.st_size:
            fail(label, "bytes read differ from the opened file size")
    finally:
        os.close(descriptor)
    return b"".join(chunks)


__all__ = ["ContractViolation", "absolute_path", "lstat_chain", "member_bytes", "relative_path", "unique_paths"]
