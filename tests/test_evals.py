#!/usr/bin/env python3
"""CI guard for the evals system: Tier 2 must pass, and cases must cover our skills.

Tier 2 (schema, minimums, routing, collisions) is deterministic, so it runs here in the
normal test suite. Behavioral (Tier 3) is token-consuming and runs on demand — see
evals/README.md.

Run: `python3 tests/test_evals.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evals"))

import run_evals  # noqa: E402


def main() -> int:
    failures: list[str] = []

    # Every native skill (skills/*/SKILL.md) must have an eval case.
    skills = {p.parent.name for p in ROOT.glob("skills/*/SKILL.md")}
    cased = {c["skill_name"] for c in run_evals.load_cases()}
    missing = skills - cased
    if missing:
        failures.append(f"skills without an eval case: {sorted(missing)}")

    # Tier 2 must pass (schema, minimums, routing, collisions).
    if run_evals.run_tier2() != 0:
        failures.append("Tier 2 evals failed (see output above)")

    if failures:
        print("FAIL — evals guard:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — evals guard (every skill cased; Tier 2 green)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
