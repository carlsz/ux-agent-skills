#!/usr/bin/env python3
"""Docs checks: the README documents the auditor, and no relative link is broken.

A new user should be able to run the auditor from the README alone, and the move-prone
web of relative links across our markdown must resolve. Broken links are how docs rot.

Run: `python3 tests/test_docs.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
# Fenced code blocks hold illustrative examples, not real links — strip before scanning.
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
# Files whose relative links we resolve.
DOC_FILES = [
    "README.md", "AGENTS.md", "CONTRIBUTING.md", "SPEC.md", "CHANGELOG.md",
    "agents/usability-auditor.md",
    "agents/cuj-author.md",
    "commands/usability-audit.md",
    "skills/usability-audit/SKILL.md",
    "skills/ux-audit/SKILL.md",
    "skills/usability-audit/references/report-contract.md",
    "skills/spec-cuj/references/cuj-contract.md",
    "commands/ux-audit.md",
    "agents/README.md", "skills/README.md", "commands/README.md",
    "evals/README.md",
]


def check_readme() -> list[str]:
    errs: list[str] = []
    text = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    needed = {
        "usability-audit": "the command / skill name",
        ".ux/audits": "where reports are written",
        "report contract": "the shared suite contract",
        "static": "static mode",
        "live": "live mode",
        "hybrid": "hybrid mode",
    }
    for term, why in needed.items():
        if term not in text:
            errs.append(f"README must document {term!r} ({why})")
    return errs


def check_links() -> list[str]:
    errs: list[str] = []
    for rel in DOC_FILES:
        path = ROOT / rel
        if not path.exists():
            continue
        content = FENCE_RE.sub("", path.read_text(encoding="utf-8"))
        for m in LINK_RE.finditer(content):
            href = m.group(1).split()[0]  # drop any title after the URL
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            target = href.split("#", 1)[0]
            if not target:
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errs.append(f"{rel}: broken link -> {href}")
    return errs


def main() -> int:
    failures = check_readme() + check_links()
    if failures:
        print("FAIL — docs:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — docs (README + links)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
