"""Entry point for a Phase 1A child launched by ``environment.launch``.

The bootstrap has already captured ``os.environ`` before this module was
imported.  The child refuses to run any payload unless its complete environment
digests to the policy projection the launcher passed on the command line; the
parent independently re-checks the capture, so the child is never trusted to
declare its own environment safe.
"""

from __future__ import annotations

import os
import sys

from mmbu_phase1 import canonical


def environment_digest() -> str:
    rows = sorted(({"name": k, "value": v} for k, v in os.environ.items()), key=lambda r: r["name"].encode("utf-8"))
    return canonical.value_digest(rows)


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[0] != "--expected-environment-digest":
        print("child: usage: --expected-environment-digest DIGEST COMMAND ...", file=sys.stderr)
        return 2
    if environment_digest() != argv[1]:
        print("child: environment differs from the policy projection; payload not executed", file=sys.stderr)
        return 3
    command, rest = argv[2], argv[3:]
    if command == "probe":
        print("child: environment matches the policy projection")
        return 0
    if command == "evaluate":
        from mmbu_phase1.phase1a_child import run

        return run(rest)
    print(f"child: unknown command {command!r}", file=sys.stderr)
    return 2
