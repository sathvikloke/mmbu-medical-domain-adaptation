#!/usr/bin/env python3
"""Compile the verified BUS-BRA archive into a patient-safe experiment manifest."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import biomedical_sources, canonical


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--archive", required=True, type=Path)
    result.add_argument("--portfolio", default=ROOT / "config/phase1/biomedical-source-portfolio.json", type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def _publish_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite existing output: {args.output}", file=sys.stderr)
        return 2
    try:
        portfolio = canonical.loads(args.portfolio.read_bytes())
        declarations = [item for item in portfolio["sources"] if item.get("source_id") == "busbra"]
        if len(declarations) != 1:
            raise ValueError("portfolio must contain exactly one BUS-BRA declaration")
        result = biomedical_sources.compile_busbra(args.archive, declarations[0])
        _publish_exclusive(args.output, canonical.dumps(result) + b"\n")
    except Exception as exc:
        print(f"BUS-BRA compilation failed: {exc}", file=sys.stderr)
        return 2
    print(canonical.dumps(result["receipt"]).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
