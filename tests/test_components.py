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


def check_skill() -> list[str]:
    errs: list[str] = []
    path = ROOT / "skills" / "usability-audit" / "SKILL.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "skill: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(bool(str(fm.get("name", "")).strip()),
                 "skill: frontmatter needs a 'name'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "skill: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    _require(".ux/audits" in low,
             "skill: must document writing reports to .ux/audits", errs)
    _require("report-contract" in low,
             "skill: must reference the shared report-contract", errs)
    _require("nielsen" in low, "skill: must apply Nielsen's heuristics", errs)
    _require("static" in low, "skill: must describe the static evaluation mode", errs)
    _require("unverified" in low,
             "skill: static-mode runtime findings must be labeled unverified", errs)
    _require("exit" in low or "done when" in low or "acceptance" in low,
             "skill: must state explicit exit criteria", errs)
    # Safety invariant restated at the workflow level.
    _require("never" in low and "outside" in low,
             "skill: must forbid writing outside .ux/audits", errs)
    # Phase 2 — live evidence gathering.
    _require("live" in low, "skill: must describe the live evaluation mode", errs)
    _require("screenshot" in low, "skill: live mode must capture screenshots", errs)
    _require("assets" in low, "skill: screenshots go under .ux/audits/assets", errs)
    _require("navigate" in low or "browser" in low,
             "skill: live mode must drive a browser (navigate the app)", errs)
    _require("ask" in low and ("server" in low or "navigat" in low),
             "skill: must require asking before starting a server / navigating", errs)
    _require("verified" in low,
             "skill: live-mode runtime findings are verified (vs static's unverified)", errs)
    # T2.2 — hybrid auto mode-selection.
    _require("hybrid" in low, "skill: must describe hybrid mode", errs)
    _require("prefer" in low and "live" in low,
             "skill: hybrid must prefer live when a URL / dev server is available", errs)
    _require("fall" in low and "back" in low,
             "skill: hybrid must fall back to static when no live target", errs)
    _require("actual" in low or "actually" in low,
             "skill: must record the mode actually used (not the one requested)", errs)
    _require("gap" in low or "not inspected" in low,
             "skill: must log coverage gaps, never silently", errs)
    return errs


def check_command() -> list[str]:
    errs: list[str] = []
    path = ROOT / "commands" / "usability-audit.md"
    if not path.exists():
        return [f"missing {path.relative_to(ROOT)}"]
    fm, body = _frontmatter(path)
    _require(isinstance(fm, dict), "command: frontmatter must parse to a mapping", errs)
    if isinstance(fm, dict):
        _require(bool(str(fm.get("name", "")).strip()),
                 "command: frontmatter needs a 'name'", errs)
        _require(bool(str(fm.get("description", "")).strip()),
                 "command: frontmatter needs a non-empty 'description'", errs)
    low = body.lower()
    # Thin wiring: routes to the skill / persona.
    _require("usability-audit" in low or "usability-auditor" in low,
             "command: must invoke the usability-audit skill / persona", errs)
    # Documents its arguments.
    for arg in ("target", "scope", "mode"):
        _require(arg in low, f"command: must document the {arg!r} argument", errs)
    # T2.2 — all three modes supported (no longer static-only).
    for mode in ("static", "live", "hybrid"):
        _require(mode in low, f"command: must document the {mode!r} mode", errs)
    return errs


def main() -> int:
    failures = check_persona() + check_skill() + check_command()
    if failures:
        print("FAIL — components:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — components (persona, skill, command)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
