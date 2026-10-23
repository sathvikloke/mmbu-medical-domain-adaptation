#!/usr/bin/env python3
"""Fail closed when the public MMBU repository revision or access state drifts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PIN = ROOT / "config/mmbu-public-revision-pin.json"
PIN_FIELDS = {
    "schema_id", "schema_version", "dataset_id", "expected_revision", "expected_gated",
    "expected_private", "observed_at_utc", "scope",
}
HEX40 = re.compile(r"[0-9a-f]{40}")


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_bytes(raw: bytes) -> dict:
    try:
        value = json.loads(
            raw.decode("utf-8"), object_pairs_hook=_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-finite JSON: {value}")),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("top-level JSON must be an object")
    return value


def load_json(path: Path) -> dict:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"not a regular JSON file: {path}")
    return load_json_bytes(path.read_bytes())


def validate_pin(pin: dict) -> None:
    if set(pin) != PIN_FIELDS:
        raise ValueError("revision pin must contain exactly the closed schema fields")
    if pin["schema_id"] != "mmbu.public_protocol_revision_pin" or pin["schema_version"] != 1:
        raise ValueError("unsupported revision-pin schema")
    if pin["dataset_id"] != "mmbu/mmbu-public":
        raise ValueError("revision pin targets an unexpected dataset")
    if not isinstance(pin["expected_revision"], str) or not HEX40.fullmatch(pin["expected_revision"]):
        raise ValueError("expected_revision must be a lowercase 40-hex commit")
    if pin["expected_gated"] != "auto" or pin["expected_private"] is not False:
        raise ValueError("revision pin must retain the reviewed public-gated access state")
    for field in ("observed_at_utc", "scope"):
        if not isinstance(pin[field], str) or not pin[field].strip():
            raise ValueError(f"{field} must be a nonempty string")


def validate_snapshot(snapshot: dict) -> None:
    required = {"id", "sha", "gated", "private", "lastModified"}
    if not required.issubset(snapshot):
        raise ValueError("API snapshot is missing a required repository-metadata field")
    if not isinstance(snapshot["id"], str):
        raise ValueError("API dataset id must be a string")
    if not isinstance(snapshot["sha"], str) or not HEX40.fullmatch(snapshot["sha"]):
        raise ValueError("API revision must be a lowercase 40-hex commit")
    if snapshot["gated"] not in {False, "auto", "manual"}:
        raise ValueError("API gated state is invalid")
    if not isinstance(snapshot["private"], bool):
        raise ValueError("API private state must be boolean")
    if not isinstance(snapshot["lastModified"], str) or not snapshot["lastModified"].strip():
        raise ValueError("API lastModified must be a nonempty string")


def compare(pin: dict, snapshot: dict) -> dict:
    validate_pin(pin)
    validate_snapshot(snapshot)
    errors = []
    checks = (
        ("dataset_id", pin["dataset_id"], snapshot["id"]),
        ("revision", pin["expected_revision"], snapshot["sha"]),
        ("gated", pin["expected_gated"], snapshot["gated"]),
        ("private", pin["expected_private"], snapshot["private"]),
    )
    for name, expected, observed in checks:
        if observed != expected:
            errors.append(f"{name} drift: expected {expected!r}, observed {observed!r}")
    return {
        "schema_id": "mmbu.public_protocol_drift_result",
        "schema_version": 1,
        "dataset_id": snapshot["id"],
        "expected_revision": pin["expected_revision"],
        "observed_revision": snapshot["sha"],
        "observed_last_modified": snapshot["lastModified"],
        "status": "drift" if errors else "current",
        "errors": errors,
        "scope": pin["scope"],
    }


def fetch_snapshot(dataset_id: str, timeout: float) -> dict:
    url = f"https://huggingface.co/api/datasets/{dataset_id}"
    request = Request(url, headers={"User-Agent": "mmbu-protocol-drift-check/1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError(f"metadata API returned HTTP {response.status}")
            raw = response.read(2_000_001)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise ValueError(f"metadata API unavailable: {exc}") from exc
    if len(raw) > 2_000_000:
        raise ValueError("metadata API response exceeds 2,000,000-byte cap")
    return load_json_bytes(raw)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pin", type=Path, default=DEFAULT_PIN)
    parser.add_argument("--api-json", type=Path,
                        help="offline API snapshot fixture; omit to query repository metadata only")
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args(argv)
    try:
        if not (0 < args.timeout <= 60):
            raise ValueError("timeout must be in (0, 60]")
        pin = load_json(args.pin)
        validate_pin(pin)
        snapshot = load_json(args.api_json) if args.api_json else fetch_snapshot(pin.get("dataset_id", ""), args.timeout)
        result = compare(pin, snapshot)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if result["status"] == "drift" else 0


if __name__ == "__main__":
    raise SystemExit(main())
