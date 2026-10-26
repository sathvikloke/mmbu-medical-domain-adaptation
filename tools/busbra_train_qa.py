#!/usr/bin/env python3
"""Build or validate a BUS-BRA train-only visual-QA packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1.busbra_train_qa import build_train_qa_packet


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("packet", type=Path)
    build.add_argument("--output", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            value = build_train_qa_packet(args.packet, args.output)
        else:  # pragma: no cover - argparse closes the command vocabulary
            raise ValueError("unknown command")
    except (OSError, TypeError, ValueError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(value, indent=2, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
