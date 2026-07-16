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

from validate_report import validate, validate_index  # noqa: E402

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


def _expect_valid_index(path: Path) -> list[str]:
    errors = validate_index(path)
    if errors:
        return [f"expected VALID index but got errors: {path.name}: {errors}"]
    return []


def _expect_invalid_index(path: Path, needle: str) -> list[str]:
    errors = validate_index(path)
    if not errors:
        return [f"expected INVALID index but passed: {path.name}"]
    if not any(needle in e for e in errors):
        return [f"{path.name}: expected an index error mentioning {needle!r}, got {errors}"]
    return []


def main() -> int:
    failures: list[str] = []

    # A fully conforming report must validate cleanly.
    failures += _expect_valid(FIXTURES / "valid" / "usability-20260715-143000.md")
    # Portability: a DIFFERENT auditor (accessibility/WCAG) shares the same contract.
    failures += _expect_valid(FIXTURES / "valid" / "accessibility-20260716-090000.md")
    # Portability again, for an auditor whose standard is the host's own journey files
    # rather than an external framework.
    failures += _expect_valid(FIXTURES / "valid" / "cuj-20260716-120000.md")
    # For `cuj`, an empty report is the SUCCESS state (every journey passed), not the
    # "found nothing" state. total: 0 with no findings must validate.
    failures += _expect_valid(FIXTURES / "valid" / "cuj-20260716-130000.md")

    # Each malformed report must be rejected for the right reason.
    failures += _expect_invalid(FIXTURES / "invalid" / "sev0-present.md", "sev0")
    failures += _expect_invalid(FIXTURES / "invalid" / "count-mismatch.md", "summary")
    failures += _expect_invalid(FIXTURES / "invalid" / "missing-key.md", "auditor")
    # Coverage honesty: a report with no appendix / not-inspected section is rejected.
    failures += _expect_invalid(FIXTURES / "invalid" / "missing-appendix.md", "coverage")
    # Proves `cuj` is actually REGISTERED in FRAMEWORKS_BY_AUDITOR: an unregistered
    # auditor's frameworks are only checked for non-emptiness, so without this fixture
    # the registration would be untested and a typo in it would pass silently.
    failures += _expect_invalid(FIXTURES / "invalid" / "cuj-bad-framework.md",
                                "unknown to auditor")

    # index.md: a conforming index passes; a malformed one is rejected.
    failures += _expect_valid_index(FIXTURES / "valid" / "index.md")
    failures += _expect_invalid_index(FIXTURES / "invalid" / "index-badcols.md", "column")

    if failures:
        print("FAIL — report contract:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — report contract (11 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
