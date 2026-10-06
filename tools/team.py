#!/usr/bin/env python3
"""Offline team checks. Run with Python 3.11+; installs nothing."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import sys
import unicodedata
import zipfile
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path("outputs/mmbu-precompute")
MANIFEST = "evidence/bundle-manifest.json"
# Fixed historical anchors from the original verification receipts, 2026-10-04.
# Updating these to make an integrity failure disappear would erase the check.
MANIFEST_ANCHOR = {
    "bytes": 42572,
    "sha256": "51db3f2af0177df49a42fda0a942d9e68e5807b8a1d8d61ed2bd0805f1c93f5d",
}
ARCHIVES = (
    ("mmbu-precompute.zip", 146013,
     "85dd05407f1a64da7e7cb09aea8a032bcd9dfa4f2e6764f217b9fc4b58363f51",
     "MMBU-precompute-verification.json", 3331,
     "c25283d169d23d9f1866265f4c060b6f1cbfd5d08b793d78b146f053d304b28f"),
    ("mmbu-precompute-v0.2.zip", 314593,
     "2e80e161c04f2aa5222c748c3d38ae94def7c3f4fdba18ffc9e0d7727a780ad3",
     "MMBU-precompute-v0.2-verification.json", 7622,
     "4376a723c7ba92cb9da84426b026a0a0ba256f9171bfe8f36f145982c00eadb0"),
    ("mmbu-precompute-v0.3.zip", 1025222,
     "5c6b137f889ea3662fbe9a4934bad2884f67a3c5e51627f7cabdec40281398d4",
     "MMBU-precompute-v0.3-verification.json", 4242,
     "12c1bbd383951bd1dc3ac710ab2357d77d66e5307273eeb6c6da9674fff91170"),
)
# Exact reviewed publication changes. The record cannot authorize new paths or
# choose new hashes. Original bytes are intentionally not restored into Git.
PUBLICATION = {
    "outputs/mmbu-precompute/evidence/source-expansion.json": {
        "original_bytes": 40023,
        "original_sha256": "b3d1f700f433dc8dc8d3ec02cc5acab4e9bc25c8842fe937298a1813b641498b",
        "published_bytes": 39613,
        "published_sha256": "c103652682b2ad3d02ae907318f3a28888a9e3629eec88b808e5ff074e2e8aa8",
    },
    "work/source-expansion/retrieval-ledger.json": {
        "original_bytes": 23629,
        "original_sha256": "70cefcac8f861196896f801b6e629e449d99ca5898a519828bf97c9c5785e1e0",
        "published_bytes": 23219,
        "published_sha256": "8488c0c15cae988d94d41584ab8981d0b5388695fe340b5897c94205599abd4c",
    },
    "outputs/mmbu-precompute/evidence/bundle-manifest.json": {
        "original_bytes": 42572,
        "original_sha256": "51db3f2af0177df49a42fda0a942d9e68e5807b8a1d8d61ed2bd0805f1c93f5d",
        "published_bytes": 42572,
        "published_sha256": "c5761ff316edc0ff9dc43017d42ef38f0b619cdead53f7c2e13a1ed1b38c51e8",
    },
    "outputs/mmbu-precompute-v0.3.zip": {
        "original_bytes": 1025222,
        "original_sha256": "5c6b137f889ea3662fbe9a4934bad2884f67a3c5e51627f7cabdec40281398d4",
        "published_bytes": 1042151,
        "published_sha256": "ab872f5908287e8b37f74c35673165273469101881a2f98cb37a80e262db75ba",
    },
}


def publication_anchor(name: str, version: str = "published") -> dict:
    item = PUBLICATION[name]
    return {"bytes": item[f"{version}_bytes"], "sha256": item[f"{version}_sha256"]}


def verify_publication_record(record: dict) -> list[str]:
    """Validate the review record against four fixed changes, never its wishes."""
    if not isinstance(record, dict) or record.get("schema_version") != 1:
        return ["publication-redactions.json: unsupported schema"]
    changes = record.get("transformations")
    if not isinstance(changes, list) or len(changes) != len(PUBLICATION):
        return ["publication-redactions.json: exactly four reviewed transformations required"]
    errors = []
    seen = set()
    for item in changes:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            errors.append("publication-redactions.json: invalid transformation")
            continue
        name = item["path"]
        if name in seen or name not in PUBLICATION:
            errors.append(f"{name}: duplicate or unapproved publication transformation")
            continue
        seen.add(name)
        if set(item) != {"path", "reason", *PUBLICATION[name]}:
            errors.append(f"{name}: invalid transformation fields")
        if any(item.get(key) != value for key, value in PUBLICATION[name].items()):
            errors.append(f"{name}: transformation differs from fixed original/published anchors")
        if not isinstance(item.get("reason"), str) or not item["reason"].strip():
            errors.append(f"{name}: missing publication reason")
    if seen != set(PUBLICATION):
        errors.append("publication-redactions.json: required transformation missing")
    return errors


def verify_published_manifest(original: dict, published: dict) -> list[str]:
    source = "evidence/source-expansion.json"
    full_source = f"{PACKAGE.as_posix()}/{source}"
    entries = original.get("files", {})
    if original.get("version") != "0.3.0" or len(entries) != 275:
        return ["Original v0.3 manifest must contain exactly 275 file entries"]
    if entries.get(source) != publication_anchor(full_source, "original"):
        return ["Original source-expansion anchor does not match the historical manifest"]
    expected = copy.deepcopy(original)
    expected["files"][source] = publication_anchor(full_source)
    if published != expected:
        return ["Published manifest differs beyond the reviewed source-expansion entry"]
    return []


def verify_zip(archive: Path, entries: dict) -> list[str]:
    """Check every archived member without extraction, including duplicate names."""
    errors = []
    expected = {f"mmbu-precompute/{name}": item for name, item in entries.items()}
    with zipfile.ZipFile(archive) as bundle:
        members = bundle.infolist()
        names = [item.filename for item in members]
        if len(set(names)) != len(names):
            errors.append(f"{archive.name}: duplicate ZIP member names")
        for name in sorted(set(names) - set(expected)):
            errors.append(f"{archive.name}: unexpected ZIP member {name}")
        for name in sorted(set(expected) - set(names)):
            errors.append(f"{archive.name}: missing ZIP member {name}")
        for member in members:
            item = expected.get(member.filename)
            if item is None:
                continue
            if member.file_size != item["bytes"]:
                errors.append(f"{member.filename}: ZIP member size differs")
                continue
            with bundle.open(member) as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            if digest != item["sha256"]:
                errors.append(f"{member.filename}: ZIP member SHA-256 differs")
    return errors


def verify_file(root: Path, name: str, expected: dict) -> list[str]:
    """Check a regular file's size and hash without following symlinks."""
    rel = PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts or "\\" in name or not rel.parts:
        return [f"{name}: unsafe historical path"]
    path = root / rel
    if any((root / Path(*rel.parts[:i])).is_symlink() for i in range(1, len(rel.parts) + 1)):
        return [f"{name}: symbolic link is not a historical regular file"]
    if not path.is_file():
        return [f"{name}: missing regular file"]
    errors = []
    if path.stat().st_size != expected.get("bytes"):
        errors.append(f"{name}: size differs from fixed integrity anchor")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != expected.get("sha256"):
        errors.append(f"{name}: SHA-256 differs from fixed integrity anchor")
    return errors


def verify_manifest(package: Path, entries: dict) -> list[str]:
    errors = []
    for name, expected in entries.items():
        if not isinstance(expected, dict):
            errors.append(f"{name}: invalid manifest entry")
        else:
            errors.extend(verify_file(package, name, expected))
    actual = {
        p.relative_to(package).as_posix()
        for p in package.rglob("*") if p.is_file() or p.is_symlink()
        if not (not p.is_symlink() and p.suffix == ".pyc" and "__pycache__" in p.relative_to(package).parts)
    }
    unexpected = actual - set(entries) - {MANIFEST}
    errors.extend(f"{name}: unexpected file in historical bundle" for name in sorted(unexpected))
    return errors


def verify_evidence(root: Path) -> list[str]:
    package = root / PACKAGE
    errors = []
    record_path = root / "research/publication-redactions.json"
    if not record_path.is_file() or record_path.is_symlink():
        errors.append("research/publication-redactions.json: missing regular publication record")
    else:
        errors.extend(verify_publication_record(json.loads(record_path.read_text(encoding="utf-8"))))
    original_name = "research/original-bundle-manifest-v0.3.json"
    original_errors = verify_file(root, original_name, MANIFEST_ANCHOR)
    errors.extend(original_errors)
    for name in PUBLICATION:
        errors.extend(verify_file(root, name, publication_anchor(name)))
    manifest_errors = verify_file(package, MANIFEST, publication_anchor(f"{PACKAGE.as_posix()}/{MANIFEST}"))
    if not original_errors and not manifest_errors:
        original = json.loads((root / original_name).read_text(encoding="utf-8"))
        manifest = json.loads((package / MANIFEST).read_text(encoding="utf-8"))
        comparison_errors = verify_published_manifest(original, manifest)
        errors.extend(comparison_errors)
        if not comparison_errors:
            entries = manifest["files"]
            errors.extend(verify_manifest(package, entries))
            archive_name = "outputs/mmbu-precompute-v0.3.zip"
            if not verify_file(root, archive_name, publication_anchor(archive_name)):
                zip_entries = {**entries, MANIFEST: publication_anchor(f"{PACKAGE.as_posix()}/{MANIFEST}")}
                errors.extend(verify_zip(root / archive_name, zip_entries))
    output = root / "outputs"
    for archive, size, digest, receipt, receipt_size, receipt_digest in ARCHIVES:
        if archive != "mmbu-precompute-v0.3.zip":
            errors.extend(verify_file(output, archive, {"bytes": size, "sha256": digest}))
        receipt_errors = verify_file(output, receipt, {"bytes": receipt_size, "sha256": receipt_digest})
        errors.extend(receipt_errors)
        if not receipt_errors:
            record = json.loads((output / receipt).read_text(encoding="utf-8"))
            if record.get("archive_sha256") != digest or record.get("archive_bytes") != size:
                errors.append(f"{receipt}: archive fields disagree with fixed historical anchors")
    return errors


def without_code(text: str, *, inline: bool = True) -> str:
    """Remove fenced and inline code while retaining line positions."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= len(fence):
                fence = None
            lines.append("\n")
        elif match:
            fence = match[1]
            lines.append("\n")
        else:
            lines.append(line)
    result = "".join(lines)
    return re.sub(r"(`+)(.*?)\1", "", result) if inline else result


def anchors(text: str) -> set[str]:
    # GitHub-style ATX heading slugs plus explicit HTML id/name anchors.
    clean = without_code(text, inline=False)
    result = set(re.findall(r'<[^>]+\b(?:id|name)=["\']([^"\']+)["\']', clean))
    counts = {}
    for heading in re.findall(r"^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", clean, re.MULTILINE):
        heading = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", heading)
        heading = re.sub(r"<[^>]*>", "", heading).lower()
        slug = "".join(c for c in heading if c in " -_" or unicodedata.category(c)[0] in "LN").replace(" ", "-")
        number = counts.get(slug, 0)
        counts[slug] = number + 1
        result.add(f"{slug}-{number}" if number else slug)
    return result


def markdown_links(text: str):
    clean = without_code(text)
    definitions = {}
    for match in re.finditer(r"^ {0,3}\[([^]]+)\]:\s*(<[^>]+>|\S+)", clean, re.MULTILINE):
        definitions[match[1].casefold()] = match[2].strip("<>")
        yield match.start(), match[2].strip("<>")
    for match in re.finditer(r"!?\[[^]\n]*\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)", clean):
        yield match.start(), match[1].strip("<>")
    for match in re.finditer(r"!?\[([^]\n]+)\]\[([^]\n]*)\]", clean):
        label = (match[2] or match[1]).casefold()
        if label not in definitions:
            yield match.start(), f"undefined-reference:{label}"


def verify_links(root: Path) -> list[str]:
    """Check maintained Markdown paths/anchors offline, never historical prose."""
    root = root.resolve()
    sources = sorted(set(root.glob("*.md")) | set((root / "docs/team").rglob("*.md")))
    if not sources:
        return ["No maintained Markdown documents found"]
    errors = []
    for source in sources:
        text = source.read_text(encoding="utf-8")
        clean = without_code(text)
        for offset, target in markdown_links(text):
            label = f"{source.relative_to(root)}:{clean[:offset].count(chr(10)) + 1}: {target}"
            parsed = urlsplit(target)
            if parsed.scheme in {"http", "https", "mailto"} or target.startswith("//"):
                continue
            if parsed.scheme:
                errors.append(f"{label}: unsupported or undefined local reference")
                continue
            relative = unquote(parsed.path)
            destination = (source.parent / relative).resolve() if relative else source.resolve()
            if Path(relative).is_absolute() or not destination.is_relative_to(root):
                errors.append(f"{label}: path escapes the repository")
            elif not destination.exists():
                errors.append(f"{label}: missing local target")
            elif parsed.fragment and destination.suffix.lower() == ".md":
                available = anchors(destination.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in available:
                    errors.append(f"{label}: missing Markdown anchor")
    return errors


def run_commands(commands: list[list[str]], cwd: Path, env: dict | None = None) -> int:
    """Stream child output and stop on the first failure, retaining its exit code."""
    for command in commands:
        print(f"+ ({cwd}) {shlex.join(command)}", flush=True)
        result = subprocess.run(command, cwd=cwd, env=env, check=False)
        if result.returncode:
            return result.returncode if result.returncode > 0 else 128 - result.returncode
    return 0


def package_environment(root: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / PACKAGE / "src")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this script's parent repository)")
    sub = parser.add_subparsers(dest="command", required=True)
    test = sub.add_parser("test", help="run historical package tests and repository tooling tests")
    test.add_argument("--images", action="store_true", help="require an already installed Pillow >=12.3,<13; never install it")
    sub.add_parser("smoke", help="run offline status, demo, toy comparison and toy diagnostics")
    sub.add_parser("verify-evidence", help="verify historical bytes, hashes and file inventory")
    sub.add_parser("verify-links", help="check maintained root/docs/team Markdown paths and anchors offline")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        if args.command in {"verify-evidence", "verify-links"}:
            errors = verify_evidence(root) if args.command == "verify-evidence" else verify_links(root)
            if errors:
                for error in errors:
                    print(f"ERROR: {error}", file=sys.stderr)
                return 1
            if args.command == "verify-evidence":
                print("Verified 275 published v0.3 files and all ZIP members against the anchored original manifest plus four fixed publication transformations.")
                print("Verified unchanged v0.1/v0.2 ZIPs and all three original receipts; the v0.3 ZIP is the explicitly recorded sanitized publication.")
                print("Artifact integrity only; no claim of scientific validity, medical truth or training results.")
            else:
                print("Maintained root/docs/team Markdown local paths and supported anchors verified; external URLs not fetched.")
            return 0
        package = root / PACKAGE
        if not (package / "src/mmbu_prep/__main__.py").is_file():
            parser.error(f"missing preparation package: {package}")
        env = package_environment(root)
        python = sys.executable
        if args.command == "test":
            if args.images:
                try:
                    import PIL
                    version = tuple(int(part) for part in PIL.__version__.split(".")[:2])
                    if not (12, 3) <= version < (13, 0):
                        raise ValueError(PIL.__version__)
                except (ImportError, ValueError) as exc:
                    print(f"ERROR: --images requires Pillow >=12.3,<13 in this interpreter ({exc}). Install it explicitly in your virtual environment.", file=sys.stderr)
                    return 2
            result = run_commands([[python, "-m", "unittest", "discover", "-s", "tests", "-v"]], package, env)
            if result:
                return result
            if not (root / "tests/test_team_tools.py").is_file():
                parser.error("missing repository tooling tests")
            return run_commands([[python, "-m", "unittest", "discover", "-s", "tests", "-v"]], root, env)
        common = ["examples/candidate-grades-toy.json", "--bootstrap", "25", "--seed", "17"]
        commands = [[python, "-m", "mmbu_prep", *parts] for parts in
                    (["status"], ["demo"], ["compare", *common], ["diagnose", *common])]
        return run_commands(commands, package, env)
    except (OSError, ValueError, TypeError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
