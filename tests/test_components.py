#!/usr/bin/env python3
"""Structural checks for the usability-auditor triad (persona / skill / command).

These files ARE the auditor's behavior — their instructions are the product — so the
"tests" assert that the safety-critical invariants and wiring are present and can't be
silently dropped. Prose quality is a human-review concern; this guards structure.

Run: `python3 tests/test_components.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _frontmatter(path: Path) -> tuple[dict | None, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    return yaml.safe_load(parts[1]), parts[2]


def _require(cond: bool, msg: str, bucket: list[str]) -> None:
    if not cond:
        bucket.append(msg)


def check_persona() -> list[str]:
    errs: list[str] = []
    path = ROOT / "agents" / "usability-auditor.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "persona: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(fm.get("name") == "usability-auditor",
                 "persona: frontmatter 'name' must be 'usability-auditor'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "persona: frontmatter needs a non-empty 'description'", errs)
        desc = str(fm.get("description", "")).lower()
        _require(any(t in desc for t in ["usability", "heuristic", "ux audit"]),
                 "persona: description should carry a trigger phrase "
                 "(usability / heuristic / UX audit)", errs)
    low = body.lower()
    # Safety-critical boundary: findings-only, never edits host code.
    _require("never" in low and ("edit" in low or "modif" in low) and "host" in low,
             "persona: must state the never-edit-host-code boundary", errs)
    # Render-vs-source honesty rule.
    _require("unverified" in low or "render" in low,
             "persona: must state the render-vs-source honesty rule", errs)
    # Output format = 0-4 severity report.
    _require("severity" in low and "0" in body and "4" in body,
             "persona: must define the 0-4 severity output format", errs)
    # Nielsen scope for Phase 1.
    _require("nielsen" in low, "persona: must reference Nielsen's heuristics", errs)
    return errs


def main() -> int:
    failures = check_persona()
    if failures:
        print("FAIL — components:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — components (persona)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
