#!/usr/bin/env python3
"""Check the auditor's safety invariant: host-repo changes stay under `.ux/audits/`.

The usability auditor is findings-only — the only files it may create or modify in the
host repo live under `.ux/audits/`. Run this after an audit to prove nothing else was
touched:

    python3 scripts/audit_safety.py <host-repo-dir>

Exit 0 = confined (safe); 1 = a change escaped `.ux/audits/`; 2 = usage/other error.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

DEFAULT_PREFIX = ".ux/audits/"


def changes_confined_to(repo: str | Path, prefix: str = DEFAULT_PREFIX) -> list[str]:
    """Return host-repo paths changed OUTSIDE `prefix` ([] = invariant holds).

    Uses `git status --porcelain -uall` so untracked files are listed individually
    (a whole new `.ux/` dir would otherwise collapse to one summary line).
    """
    repo = Path(repo)
    proc = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "-uall"],
        check=True, capture_output=True, text=True,
    )
    violations: list[str] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        # Porcelain v1: 2 status chars, a space, then the path (handle "R old -> new").
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip().strip('"')
        if not path.startswith(prefix):
            violations.append(path)
    return violations


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: audit_safety.py <host-repo-dir>", file=sys.stderr)
        return 2
    violations = changes_confined_to(argv[0])
    if violations:
        print("SAFETY VIOLATION — changes outside .ux/audits/:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print("safe: all changes confined to .ux/audits/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
