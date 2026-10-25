#!/usr/bin/env python3
"""Run the closed Competition Lane 1 CPU-only synthetic engineering lane."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical, lane1_trainer


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", required=True, type=Path)
    result.add_argument("--fixture", required=True, type=Path)
    result.add_argument("--config", required=True, type=Path)
    result.add_argument("--output", required=True, type=Path)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.output.exists():
        print(f"refusing to overwrite existing output: {args.output}", file=sys.stderr)
        return 2
    try:
        manifest = canonical.loads_canonical(args.manifest.read_bytes())
        fixture = canonical.loads_canonical(args.fixture.read_bytes())
        config = canonical.loads_canonical(args.config.read_bytes())
        result = lane1_trainer.run_lane1(manifest, fixture, config)
    except Exception as exc:
        print(f"Lane 1 preflight failed: {exc}", file=sys.stderr)
        return 2
    try:
        with args.output.open("xb") as stream:
            stream.write(canonical.dumps(result) + b"\n")
    except FileExistsError:
        print(f"refusing to overwrite existing output: {args.output}", file=sys.stderr)
        return 2
    failed = any(item["status"] != "passed" for item in result["arm_results"])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
