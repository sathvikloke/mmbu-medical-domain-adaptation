#!/usr/bin/env python3
"""Verify and compile both external biomedical sources into one immutable row manifest."""

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
    result.add_argument("--busbra", required=True, type=Path)
    result.add_argument("--pathmnist", required=True, type=Path)
    result.add_argument("--portfolio", default=ROOT / "config/phase1/biomedical-source-portfolio.json", type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def _publish(path: Path, payload: bytes) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing output: {path}")
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
    try:
        portfolio = canonical.loads(args.portfolio.read_bytes())
        by_id = {item["source_id"]: item for item in portfolio["sources"]}
        if set(by_id) != {"busbra", "pathmnist"}:
            raise ValueError("portfolio must contain exactly BUS-BRA and PathMNIST")
        busbra = biomedical_sources.compile_busbra(args.busbra, by_id["busbra"])
        pathmnist = biomedical_sources.compile_pathmnist(args.pathmnist, by_id["pathmnist"])
        rows = busbra["rows"] + pathmnist["rows"]
        result = {
            "limitations": [
                "No MMBU public example, label, derivative, embedding, or outcome was used.",
                "BUS-BRA cases 110 and 536 are excluded pending near-duplicate provenance review.",
                "PathMNIST development patches do not expose patient IDs; only its external-center test partition may be confirmation evidence.",
            ],
            "mmbu_public_content_used": False,
            "portfolio_config_digest": canonical.value_digest(portfolio),
            "rows": rows,
            "rows_digest": canonical.value_digest(rows),
            "schema_id": "mmbu.biomedical.compiled_portfolio",
            "schema_version": 1,
            "source_receipts": [busbra["receipt"], pathmnist["receipt"]],
        }
        _publish(args.output, canonical.dumps(result) + b"\n")
    except Exception as exc:
        print(f"biomedical portfolio preparation failed: {exc}", file=sys.stderr)
        return 2
    print(canonical.dumps({
        "output": str(args.output),
        "rows": len(rows),
        "rows_digest": result["rows_digest"],
        "source_receipts": result["source_receipts"],
    }).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
