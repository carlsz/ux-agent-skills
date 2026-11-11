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
    # ...and its evil twin: an all-skipped run, which verified NOTHING, is byte-identical
    # to that clean pass as far as this schema is concerned — same total: 0, same zero
    # findings, equally valid. This fixture asserts that validity, because the honest
    # position is that the validator CANNOT catch this and must not pretend to. Only two
    # things discriminate, and both are prose the auditor writes: the counts
    # ("0/2 journeys passed, 2 skipped") and `frameworks: [cuj-contract]` alone. Phase 10's
    # roll-up reads the latter to avoid scoring a skipped run as a passed one.
    failures += _expect_valid(FIXTURES / "valid" / "cuj-20260716-140000.md")

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
    # Schema 2's `## Walkthrough` section (§10): the cuj and usability valid fixtures above
    # carry a walkthrough of inline `./assets/` embeds and must still validate. A walkthrough
    # whose image is an external URL (or any non-`./assets/` path) is rejected — the light
    # check that keeps the walk-through inside the auditor's write boundary.
    failures += _expect_invalid(FIXTURES / "invalid" / "walkthrough-bad-path.md",
                                "walkthrough image path")

    # --- schema 3: priority is the scored field, severity is reported per finding ---
    # The schema-2 fixtures above are the regression proof that the dispatch did not
    # break the permanent path; these prove the new one works.
    failures += _expect_valid(FIXTURES / "valid" / "usability-20261111-143000.md")

    # Reconciliation, in the new vocabulary.
    failures += _expect_invalid(FIXTURES / "invalid" / "priority-mismatch.md", "P0-P3")
    # There is no rank below P3 and none above P0 — an out-of-range heading is caught
    # explicitly rather than silently going uncounted (which would surface as a confusing
    # total mismatch instead).
    failures += _expect_invalid(FIXTURES / "invalid" / "priority-out-of-range.md",
                                "outside the P0-P3")
    # Schema 3 adds a sixth field; a finding without it is incomplete.
    failures += _expect_invalid(FIXTURES / "invalid" / "missing-priority-field.md",
                                "Priority")
    # --- cross-schema confusion, both directions ---
    # Half-migrated reports are the failure mode a two-vocabulary validator invites, so
    # both halves are asserted: right shape, wrong summary keys...
    failures += _expect_invalid(FIXTURES / "invalid" / "schema-mixed.md",
                                "schema-2 keys")
    # ...and right summary, wrong headings. Built inline rather than as a fixture: it is a
    # one-line mutation of a file already on disk, and a frozen copy would drift from it.
    import tempfile
    for schema, bad_heading, needle in (
        (3, "### [sev3] ", "[sevN] finding headings"),
        (2, "### [P1] ", "[PN] finding headings"),
    ):
        src = ("valid/usability-20261111-143000.md" if schema == 3
               else "valid/usability-20260715-143000.md")
        text = (FIXTURES / src).read_text(encoding="utf-8")
        old_tag = "### [P1] " if schema == 3 else "### [sev3] "
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(text.replace(old_tag, bad_heading, 1))
            tmp = Path(fh.name)
        failures += _expect_invalid(tmp, needle)
        tmp.unlink()

    # A schema nobody implements must fail loudly, not fall through to a default.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write((FIXTURES / "valid" / "usability-20261111-143000.md")
                 .read_text(encoding="utf-8").replace("schema: 3", "schema: 4", 1))
        tmp = Path(fh.name)
    failures += _expect_invalid(tmp, "'schema' must be one of")
    tmp.unlink()

    # --- review findings from PR #20, pinned so they cannot regress ----------------
    # Lowercase summary keys: SPEC's canonical example shipped `p0:` while the validator
    # requires `P0:`, so an auditor copying the spec failed its own self-check every run.
    # The keys are now uppercase everywhere AND the error names casing as the cause --
    # the previous "missing required key: 'P0'" sent the author hunting an absent key.
    import re as _re
    _s3 = (FIXTURES / "valid" / "usability-20261111-143000.md").read_text(encoding="utf-8")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write(_re.sub(r"^  P(\d):", lambda m: f"  p{m.group(1)}:", _s3, flags=_re.M))
        tmp = Path(fh.name)
    failures += _expect_invalid(tmp, "case-sensitive")
    tmp.unlink()

    # `3.0 == 3` and `True == 1` in Python, so a membership test accepted both and then
    # indexed the rating table by something that is not a contract version.
    for bad in ("schema: 3.0", "schema: true"):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
            fh.write(_s3.replace("schema: 3", bad, 1))
            tmp = Path(fh.name)
        failures += _expect_invalid(tmp, "an integer")
        tmp.unlink()

    # index.md: a conforming index passes; a malformed one is rejected.
    failures += _expect_valid_index(FIXTURES / "valid" / "index.md")
    failures += _expect_invalid_index(FIXTURES / "invalid" / "index-badcols.md", "column")
    # The index is append-only and shared, so schema 3 cannot swap its columns. A legacy
    # table with a priority table appended below it is the documented transition (§7), and
    # both must validate in one file.
    failures += _expect_valid_index(FIXTURES / "valid" / "index-dual.md")
    # Header detection keyed on two phrases appearing anywhere in a line, so PROSE about
    # the columns -- which this contract, SPEC and the README all contain -- was parsed as
    # a header row and then rejected for having the wrong columns.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as fh:
        fh.write((FIXTURES / "valid" / "index.md").read_text(encoding="utf-8")
                 + "\nEach row lists Date (UTC), Auditor, Scope and Report.\n")
        tmp = Path(fh.name)
    failures += _expect_valid_index(tmp)
    tmp.unlink()

    if failures:
        print("FAIL — report contract:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — report contract (26 checks, schemas 2 and 3)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
