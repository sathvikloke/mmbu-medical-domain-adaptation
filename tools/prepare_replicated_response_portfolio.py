#!/usr/bin/env python3
"""Rebuild the external-biomedical portfolio with the frozen successor context task."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import biomedical_sources, canonical, replicated_response


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--busbra", required=True, type=Path)
    result.add_argument("--pathmnist", required=True, type=Path)
    result.add_argument(
        "--portfolio", default=ROOT / "config/phase1/biomedical-source-portfolio.json", type=Path,
    )
    result.add_argument("--output", required=True, type=Path)
    return result


def publish(path: Path, payload: bytes) -> None:
    """Atomically publish once; an existing path is immutable evidence."""
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def build_portfolio(source_config: dict, busbra: dict, pathmnist: dict) -> dict:
    original_rows = busbra["rows"] + pathmnist["rows"]
    rows = [replicated_response.official_context_row(row) for row in original_rows]
    return {
        "context_contract": {
            "busbra": ["body_part", "medical_domain", "modality"],
            "pathmnist": ["medical_domain", "modality", "specimen", "stain"],
        },
        "limitations": [
            "No MMBU public example, label, derivative, embedding, or outcome was used.",
            "This portfolio is exploratory because qualified human source admission is incomplete.",
            "BUS-BRA cases 110 and 536 remain excluded pending near-duplicate provenance review.",
            "PathMNIST does not expose patient identifiers for its train or development patches.",
            "The confirmation partitions remain unopened by this response screen.",
        ],
        "mmbu_public_content_used": False,
        "original_rows_digest": canonical.value_digest(original_rows),
        "portfolio_config_digest": canonical.value_digest(source_config),
        "rows": rows,
        "rows_digest": canonical.value_digest(rows),
        "schema_id": "mmbu.biomedical.compiled_portfolio",
        "schema_version": 1,
        "source_admission_complete": False,
        "source_receipts": [busbra["receipt"], pathmnist["receipt"]],
    }


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        source_config = canonical.loads(args.portfolio.read_bytes())
        declarations = {item["source_id"]: item for item in source_config["sources"]}
        if set(declarations) != {"busbra", "pathmnist"}:
            raise ValueError("portfolio must contain exactly BUS-BRA and PathMNIST")
        busbra = biomedical_sources.compile_busbra(args.busbra, declarations["busbra"])
        pathmnist = biomedical_sources.compile_pathmnist(args.pathmnist, declarations["pathmnist"])
        result = build_portfolio(source_config, busbra, pathmnist)
        publish(args.output, canonical.dumps(result) + b"\n")
    except Exception as exc:
        print(f"replicated response portfolio preparation failed: {exc}", file=sys.stderr)
        return 2
    print(canonical.dumps({
        "output": str(args.output),
        "rows": len(result["rows"]),
        "rows_digest": result["rows_digest"],
        "source_receipts": result["source_receipts"],
    }).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
