#!/usr/bin/env python3
"""Executable spec for the shared `.ux/audits` report contract.

The human-readable contract lives in
`skills/usability-audit/references/report-contract.md`; this test encodes its
machine-checkable invariants via `scripts/validate_report.py` and asserts that a
conforming report passes while known-malformed reports fail.

Run: `python3 tests/test_report_contract.py` (exit 0 = pass, 1 = fail).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_report import validate  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


def _expect_valid(path: Path) -> list[str]:
    errors = validate(path)
    if errors:
        return [f"expected VALID but got errors: {path.name}: {errors}"]
    return []


def _expect_invalid(path: Path, needle: str) -> list[str]:
    errors = validate(path)
    if not errors:
        return [f"expected INVALID but passed: {path.name}"]
    if not any(needle in e for e in errors):
        return [f"{path.name}: expected an error mentioning {needle!r}, got {errors}"]
    return []


def main() -> int:
    failures: list[str] = []

    # A fully conforming report must validate cleanly.
    failures += _expect_valid(FIXTURES / "valid" / "usability-20260715-143000.md")

    # Each malformed report must be rejected for the right reason.
    failures += _expect_invalid(FIXTURES / "invalid" / "sev0-present.md", "sev0")
    failures += _expect_invalid(FIXTURES / "invalid" / "count-mismatch.md", "summary")
    failures += _expect_invalid(FIXTURES / "invalid" / "missing-key.md", "auditor")

    if failures:
        print("FAIL — report contract:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — report contract (4 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
