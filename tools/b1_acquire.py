#!/usr/bin/env python3
"""Acquire and verify the exact B1 model and Python runtime without a GPU."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f
from mmbu_phase1 import b1_preflight


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b1-mocs-preflight.json"
PIN_PATH = REPO / "docs/phase1/b1-pin.json"


def _normalized_name(value: str) -> str:
    return value.lower().replace("_", "-").replace(".", "-")


def build_plan(config: Any) -> dict:
    config = b1_preflight.validate_preflight_config(config)
    model = config["model"]
    revision = model["revision"]
    files = [
        {
            "path": name,
            "url": f"https://huggingface.co/{model['model_id']}/resolve/{revision}/{name}",
        }
        for name in model["allowed_files"]
    ]
    requirements = [
        f"accelerate=={config['runtime']['accelerate']}",
        f"numpy=={config['runtime']['numpy']}",
        f"peft=={config['runtime']['peft']}",
        f"pillow=={config['runtime']['pillow']}",
        f"safetensors=={config['runtime']['safetensors']}",
        f"torch=={config['runtime']['torch']}",
        f"torchvision=={config['runtime']['torchvision']}",
        f"transformers=={config['runtime']['transformers']}",
    ]
    return {
        "model_files": files,
        "requirements": requirements,
        "index_url": "https://pypi.org/simple",
        "extra_index_url": config["runtime"]["cuda_wheel_index"],
        "only_binary": True,
        "python": config["runtime"]["python"],
    }


def validate_resolver_report(report: Any, config: Any) -> dict:
    config = b1_preflight.validate_preflight_config(config)
    report = f.closed(report, "resolver_report", ("version", "install"))
    f.text(report["version"], "resolver_report.version")
    installs = f.array(report["install"], "resolver_report.install", nonempty=True)
    requested: dict[str, str] = {}
    for index, item in enumerate(installs):
        path = f"resolver_report.install[{index}]"
        f.require(type(item) is dict, path, "must be an object")
        metadata = item.get("metadata")
        f.require(type(metadata) is dict, path + ".metadata", "must be an object")
        name = f.text(metadata.get("name"), path + ".metadata.name")
        version = f.text(metadata.get("version"), path + ".metadata.version")
        download = item.get("download_info")
        f.require(type(download) is dict, path + ".download_info", "must be an object")
        f.require("vcs_info" not in download, path + ".download_info", "VCS dependencies are forbidden")
        f.require("dir_info" not in download, path + ".download_info", "directory/editable dependencies are forbidden")
        url = f.text(download.get("url"), path + ".download_info.url")
        f.require(url.startswith("https://") and url.endswith(".whl"), path + ".download_info.url", "must be an HTTPS wheel URL")
        archive = download.get("archive_info")
        f.require(type(archive) is dict, path + ".download_info.archive_info", "must be an object")
        digest = archive.get("hash")
        f.require(type(digest) is str and digest.startswith("sha256=") and len(digest) == 71,
                  path + ".download_info.archive_info.hash", "must be one SHA-256 hash")
        f.digest(digest[7:], path + ".download_info.archive_info.hash")
        if item.get("requested") is True:
            key = _normalized_name(name)
            f.require(key not in requested, "resolver_report.install", "duplicate requested package")
            requested[key] = version
    expected = {}
    for requirement in build_plan(config)["requirements"]:
        name, version = requirement.split("==", 1)
        expected[_normalized_name(name)] = version
    f.literal(requested, "resolver_report.requested", expected)
    return report


def _hash(path: Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def inventory_directory(root: str | os.PathLike[str], suffix: str) -> list[dict]:
    root = Path(root)
    f.require(root.is_dir() and not root.is_symlink(), "inventory.root", "must be a real directory")
    rows = []
    for path in sorted(root.iterdir(), key=lambda item: item.name.encode("utf-8")):
        f.require(path.is_file() and not path.is_symlink(), f"inventory.{path.name}", "must be a regular non-symlink file")
        f.require(path.name.endswith(suffix), f"inventory.{path.name}", f"must end in {suffix}")
        rows.append({"path": path.name, "bytes": path.stat().st_size, "sha256": _hash(path)})
    f.require(bool(rows), "inventory", "must not be empty")
    return rows


def verify_inventory(root: str | os.PathLike[str], expected: Any, suffix: str) -> list[dict]:
    f.require(type(expected) is list, "inventory.expected", "must be an array")
    observed = inventory_directory(root, suffix)
    f.literal(observed, "inventory", expected)
    return observed


def _load_pin_projection() -> dict:
    pin = canonical.loads(PIN_PATH.read_bytes())
    return {
        "model_id": pin["model_id"], "model_revision": pin["model_revision"],
        "processor_id": pin["processor_id"], "processor_revision": pin["processor_revision"],
        "upstream_metadata": pin["upstream_metadata"],
        "weight_manifest": {
            key: pin["weight_manifest"][key]
            for key in ("index_path", "index_bytes", "index_sha256", "shards")
        },
    }


def _write_json(path: Path, value: Any) -> None:
    path.write_bytes(canonical.dumps(value) + b"\n")


def _download(url: str, destination: Path) -> None:
    partial = destination.with_name(destination.name + ".partial")
    subprocess.run([
        "curl", "--fail", "--location", "--silent", "--show-error",
        "--retry", "3", "--continue-at", "-", "--output", str(partial), url,
    ], check=True)
    os.replace(partial, destination)


def acquire(config: dict) -> None:
    plan = build_plan(config)
    paths = config["paths"]
    remote_root = Path(paths["remote_root"])
    model_root = Path(paths["model_root"])
    wheelhouse = Path(paths["wheelhouse_root"])
    evidence = Path(paths["evidence_root"])
    venv = Path(paths["venv_root"])
    for directory in (remote_root, model_root, wheelhouse, evidence):
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    for row in plan["model_files"]:
        destination = model_root / row["path"]
        if not destination.exists():
            _download(row["url"], destination)
    model_manifest = b1_preflight.verify_pinned_artifacts(config, _load_pin_projection(), model_root)
    _write_json(evidence / "model-inventory.json", model_manifest)

    subprocess.run([
        sys.executable, "-m", "pip", "download", "--only-binary=:all:",
        "--dest", str(wheelhouse), "--index-url", plan["index_url"],
        "--extra-index-url", plan["extra_index_url"], *plan["requirements"],
    ], check=True)
    wheels = inventory_directory(wheelhouse, ".whl")
    _write_json(evidence / "wheel-inventory.json", wheels)
    subprocess.run([sys.executable, "-m", "venv", str(venv)], check=True)
    report_path = evidence / "resolver-report.json"
    subprocess.run([
        str(venv / "bin/python"), "-m", "pip", "install", "--no-index",
        "--find-links", str(wheelhouse), "--report", str(report_path), *plan["requirements"],
    ], check=True)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    validate_resolver_report({"version": report["version"], "install": report["install"]}, config)


def verify(config: dict) -> None:
    paths = config["paths"]
    evidence = Path(paths["evidence_root"])
    model = b1_preflight.verify_pinned_artifacts(config, _load_pin_projection(), paths["model_root"])
    expected_model = canonical.loads((evidence / "model-inventory.json").read_bytes())
    f.literal(model, "model_inventory", expected_model)
    expected_wheels = canonical.loads((evidence / "wheel-inventory.json").read_bytes())
    verify_inventory(paths["wheelhouse_root"], expected_wheels, ".whl")
    raw_report = json.loads((evidence / "resolver-report.json").read_text(encoding="utf-8"))
    validate_resolver_report({"version": raw_report["version"], "install": raw_report["install"]}, config)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("plan", "acquire", "verify"))
    args = parser.parse_args(argv)
    config = b1_preflight.load_preflight_config(CONFIG_PATH)
    if args.command == "plan":
        sys.stdout.buffer.write(canonical.dumps(build_plan(config)) + b"\n")
    elif args.command == "acquire":
        acquire(config)
    else:
        verify(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
