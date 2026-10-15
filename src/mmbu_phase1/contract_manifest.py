"""Strict offline verification for the clone-resident Phase 1 contract."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any


EXPECTED_CONTRACT_REVISION = "2026-10-15-cycle-46b"
EXPECTED_MANIFEST_SHA256 = "4f17eb06c4365da87ecc4c673339a3cdc656cd6e0d28e8662c4c626f8ffe4c16"
EXPECTED_MEMBERS = frozenset(
    {
        "docs/phase1/CONTRACT.md",
        "docs/phase1/ACCEPTANCE.md",
        "docs/phase1/SCHEMAS.md",
        "docs/phase1/REPRODUCIBILITY.md",
        "docs/phase1/B1_RUNTIME_GATE.md",
        "docs/phase1/EVALUATOR_MECHANICS.md",
        "docs/phase1/OFFICIAL_SOURCE_MAP.md",
        "docs/phase1/ORGANIZER_CLARIFICATION.md",
        "docs/phase1/b1-pin.json",
    }
)
EXPECTED_OFFICIAL_SOURCE_NAMES = frozenset(
    {"MMBU_challenge_update.pdf", "mmbu-challenge-official-rules.pdf"}
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_nonfinite(value: str) -> None:
    raise ValueError(f"nonfinite JSON number: {value}")


def _strict_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError(f"nonfinite JSON number: {value}")
    return parsed


def _strict_json(raw: bytes) -> Any:
    return json.loads(
        raw.decode("utf-8"),
        object_pairs_hook=_reject_duplicate_keys,
        parse_constant=_reject_nonfinite,
        parse_float=_strict_float,
    )


def _safe_member_path(value: object) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute()
        and str(path) == value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _safe_regular_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    """Resolve a regular file only when every descendant component is non-symlink."""
    current = root
    parts = PurePosixPath(relative).parts
    for index, part in enumerate(parts):
        current = current / part
        try:
            mode = current.lstat().st_mode
        except OSError as exc:
            return None, f"{relative}: missing or unreadable component {current.relative_to(root)} ({exc})"
        final = index == len(parts) - 1
        if stat.S_ISLNK(mode):
            kind = "file" if final else "ancestor"
            return None, f"{relative}: symlink {kind} is forbidden at {current.relative_to(root)}"
        if final:
            if not stat.S_ISREG(mode):
                return None, f"{relative}: expected a regular non-symlink file"
        elif not stat.S_ISDIR(mode):
            return None, f"{relative}: ancestor is not a directory at {current.relative_to(root)}"
    try:
        if not current.resolve(strict=True).is_relative_to(root):
            return None, f"{relative}: resolved path escapes repository root"
    except OSError as exc:
        return None, f"{relative}: cannot resolve file ({exc})"
    return current, None


def _official_source_map_hashes(root: Path) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    path, error = _safe_regular_file(root, "docs/phase1/OFFICIAL_SOURCE_MAP.md")
    if error:
        return {}, [error]
    assert path is not None
    text = path.read_text(encoding="utf-8")
    found: dict[str, str] = {}
    for name in EXPECTED_OFFICIAL_SOURCE_NAMES:
        matches = re.findall(
            rf"^\|\s*`{re.escape(name)}`\s*\|\s*`([0-9a-f]{{64}})`\s*\|",
            text,
            flags=re.MULTILINE,
        )
        if len(matches) != 1:
            errors.append(f"official source hash mismatch: {name} appears {len(matches)} times in OFFICIAL_SOURCE_MAP.md")
        else:
            found[name] = matches[0]
    return found, errors


def verify_contract_manifest(
    root: Path,
    *,
    expected_manifest_sha256: str = EXPECTED_MANIFEST_SHA256,
) -> list[str]:
    """Return every contract-integrity error without reading outside ``root``."""
    root = Path(root).resolve()
    errors: list[str] = []
    manifest_path, manifest_error = _safe_regular_file(root, "docs/phase1/contract-manifest.json")
    if manifest_error:
        return [f"Phase 1 contract manifest: {manifest_error}"]
    assert manifest_path is not None

    raw = manifest_path.read_bytes()
    actual_manifest_hash = hashlib.sha256(raw).hexdigest()
    if actual_manifest_hash != expected_manifest_sha256:
        errors.append(
            "Phase 1 contract manifest SHA-256 mismatch: "
            f"expected {expected_manifest_sha256}, got {actual_manifest_hash}"
        )
    try:
        manifest = _strict_json(raw)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        errors.append(f"Phase 1 contract manifest is invalid: {exc}")
        return errors

    if not isinstance(manifest, dict):
        return errors + ["Phase 1 contract manifest top level must be an object"]
    expected_top = {
        "schema_version",
        "contract_revision",
        "files",
        "official_source_hashes",
        "inventory_policy",
        "note",
    }
    if set(manifest) != expected_top:
        errors.append("Phase 1 contract manifest top-level keys do not match the closed schema")
    schema_version = manifest.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        errors.append("Phase 1 contract manifest schema_version must be integer 1")
    if manifest.get("contract_revision") != EXPECTED_CONTRACT_REVISION:
        errors.append(
            "Phase 1 contract revision mismatch: "
            f"expected {EXPECTED_CONTRACT_REVISION}, got {manifest.get('contract_revision')!r}"
        )
    if not isinstance(manifest.get("inventory_policy"), str) or not manifest.get("inventory_policy"):
        errors.append("Phase 1 contract inventory_policy must be a nonempty string")
    if not isinstance(manifest.get("note"), str) or not manifest.get("note"):
        errors.append("Phase 1 contract note must be a nonempty string")

    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("Phase 1 contract files must be an object")
        files = {}
    paths = set(files)
    for path in sorted(paths, key=str):
        if not _safe_member_path(path):
            errors.append(f"unsafe manifest path: {path!r}")
    for path in sorted(EXPECTED_MEMBERS - paths):
        errors.append(f"missing manifest member: {path}")
    for path in sorted(paths - EXPECTED_MEMBERS, key=str):
        errors.append(f"extra manifest member: {path}")

    for relative in sorted(EXPECTED_MEMBERS & paths):
        receipt = files[relative]
        if not isinstance(receipt, dict) or set(receipt) != {"bytes", "sha256"}:
            errors.append(f"{relative}: receipt must contain exactly bytes and sha256")
            continue
        expected_bytes = receipt.get("bytes")
        expected_hash = receipt.get("sha256")
        if isinstance(expected_bytes, bool) or not isinstance(expected_bytes, int) or expected_bytes < 0:
            errors.append(f"{relative}: byte count must be a nonnegative integer")
        if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
            errors.append(f"{relative}: SHA-256 receipt must be lowercase hexadecimal")
        member, member_error = _safe_regular_file(root, relative)
        if member_error:
            errors.append(member_error)
            continue
        assert member is not None
        member_raw = member.read_bytes()
        if len(member_raw) != expected_bytes:
            errors.append(f"{relative}: byte count mismatch; expected {expected_bytes}, got {len(member_raw)}")
        actual_hash = hashlib.sha256(member_raw).hexdigest()
        if actual_hash != expected_hash:
            errors.append(f"{relative}: SHA-256 mismatch; expected {expected_hash}, got {actual_hash}")

    official = manifest.get("official_source_hashes")
    if not isinstance(official, dict):
        errors.append("official_source_hashes must be an object")
        official = {}
    if set(official) != EXPECTED_OFFICIAL_SOURCE_NAMES:
        errors.append("official_source_hashes must name exactly the two reviewed official PDFs")
    for name, digest in official.items():
        if not isinstance(name, str) or not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            errors.append(f"official source hash receipt is invalid: {name!r}")

    source_map, map_errors = _official_source_map_hashes(root)
    errors.extend(map_errors)
    for name in sorted(EXPECTED_OFFICIAL_SOURCE_NAMES):
        if name in official and name in source_map and official[name] != source_map[name]:
            errors.append(
                f"official source hash mismatch for {name}: manifest {official[name]}, source map {source_map[name]}"
            )
    return errors
