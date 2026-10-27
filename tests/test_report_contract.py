#!/usr/bin/env python3
"""Executable spec for the shared `.ux/audits` report contract.

The human-readable contract lives in
`skills/usability-audit/references/report-contract.md`; this test encodes its
machine-checkable invariants via `scripts/validate_report.py` and asserts that a
conforming report passes while known-malformed reports fail.

Run: `python3 tests/test_report_contract.py` (exit 0 = pass, 1 = fail).
"""
import sys
import tempfile
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
    # Schema 3 inverted the old `sev0` rule. The scale used to have no zero, so a `[sev0]`
    # heading was the error; it now STARTS at zero, so the two failures worth catching are
    # a tag above the top (P4) and frontmatter still counting on the superseded scale.
    failures += _expect_invalid(FIXTURES / "invalid" / "priority-out-of-range.md", "[P4]")
    failures += _expect_invalid(FIXTURES / "invalid" / "stale-severity-scale.md",
                                "superseded severity scale")
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
                                "image path must be relative")

    # --- assets belong to the run that captured them (§1) ---------------------------------
    # Assets live in `./assets/<report-stem>/`, a directory DERIVED from the report's own
    # filename — which is the only reason this is checkable at all. The probe changes nothing
    # but the name of the file: identical bytes validate under the name whose stem matches
    # their embeds and are rejected under any other. Flat `assets/` names (the earlier
    # layout) carried no run identity, so a re-run's `cuj-001-step-1.png` overwrote the image
    # a kept report embedded — every path still resolved, so an existence check saw nothing
    # wrong, and the HTML companion then base64-welded the newer screenshot into the older
    # report. Only the filename can tell those apart.
    _cuj = FIXTURES / "valid" / "cuj-20260716-120000.md"
    _body = _cuj.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as _d:
        _same = Path(_d) / _cuj.name
        _same.write_text(_body, encoding="utf-8")
        failures += _expect_valid(_same)
        # One run earlier, same bytes. Every embed now points into a sibling run's directory.
        _other = Path(_d) / "cuj-20260716-110000.md"
        _other.write_text(_body, encoding="utf-8")
        failures += _expect_invalid(_other, "run's own asset directory")
    # The rule covers the WHOLE body, not just `## Walkthrough` — a finding's `Evidence:`
    # embed is evidence in the strictest sense. The usability fixture cites two of its
    # screenshots inside findings, so a walkthrough-only check would have let those through.
    _use = FIXTURES / "valid" / "usability-20260715-143000.md"
    _mangled = _use.read_text(encoding="utf-8").replace(
        "live capture ![place order idle](./assets/usability-20260715-143000/",
        "live capture ![place order idle](./assets/usability-20260101-000000/", 1)
    with tempfile.TemporaryDirectory() as _d:
        _p = Path(_d) / _use.name
        _p.write_text(_mangled, encoding="utf-8")
        failures += _expect_invalid(_p, "run's own asset directory")

    # --- the suite roll-up (§9) ----------------------------------------------------------
    # A roll-up is a SIBLING document type, not an auditor report: no `auditor`, no `mode`,
    # no `frameworks`, no finding blocks, `## Notes` instead of `## Appendix`. It must
    # validate through its own path rather than being rejected for the keys it correctly
    # lacks — `validate()` dispatches on the `kind: rollup` discriminator.
    failures += _expect_valid(FIXTURES / "valid" / "rollup-20260716-150000.md")
    # ...and the GO case, which also carries three skipped auditors each with its reason.
    failures += _expect_valid(FIXTURES / "valid" / "rollup-20260716-160000.md")

    # The discriminator is `kind: rollup` and nothing else. `report: rollup` is READ as a
    # roll-up so historical files still render (see test_render_html), but writing one is a
    # violation — this fixture is what keeps "tolerated on read" from becoming "allowed".
    failures += _expect_invalid(FIXTURES / "invalid" / "rollup-legacy-kind.md",
                                "kind: rollup")
    # `verdict` is a bare token; prose belongs in `verdict_reason`. This is the shape that
    # made every real roll-up render as a red NO-GO: the renderer tests this value, and
    # "GO — all journeys pass" equals neither verdict.
    failures += _expect_invalid(FIXTURES / "invalid" / "rollup-verdict-prose.md", "verdict")
    # The gate is mechanical: NO-GO iff p0 or p1 is non-zero. A roll-up that declares GO
    # over a P1 is rejected rather than left to the auditor's judgment — two real runs
    # reached opposite verdicts from identical counts before this rule existed.
    failures += _expect_invalid(FIXTURES / "invalid" / "rollup-verdict-mismatch.md",
                                "derive")
    # A skipped auditor without a reason reads as a clean pass; the reason is structural.
    failures += _expect_invalid(FIXTURES / "invalid" / "rollup-skip-no-reason.md", "reason")

    # --- the health scorecard (§4.1) ------------------------------------------------------
    # `score`, `max`, `pct` and `band` are DERIVED, so the headline is checked against the
    # rows it is made of. A number nobody can reconcile with its items is the kind of
    # unfalsifiable claim this suite exists to avoid.
    failures += _expect_invalid(FIXTURES / "invalid" / "health-derived-mismatch.md",
                                "its items derive")
    # A weak score is an assertion until it says what it is based on — the same rule as a
    # skipped auditor needing a reason.
    failures += _expect_invalid(FIXTURES / "invalid" / "health-unexplained-low.md", "note")
    # --- the findings floor (§4.1) --------------------------------------------------------
    # An item's score IS the P-number of the worst finding against it, so the scorecard and
    # the findings are two views of one judgment. Both directions have to be enforced, and
    # a real run failed each of them:
    #   * a scorecard that outruns its findings — two `P0`s filed, 70% `Good` published;
    #   * a scorecard that sinks below them — one cosmetic `P3`, four steps marked `0`,
    #     43% `Poor` published over a product whose journeys all completed.
    # The second is the one that made the dial read backwards against severity, which is
    # worse than a number being merely wrong: a reader who trusts it concludes the opposite
    # of the truth.
    failures += _expect_invalid(FIXTURES / "invalid" / "health-floor-unreached.md",
                                "has to land on one of them")
    failures += _expect_invalid(FIXTURES / "invalid" / "health-below-floor.md",
                                "lowest item score must be 3")
    # --- `pct` is rubric-size independent (§4.1) ------------------------------------------
    # The headline is a priority index over `summary`, not `score / max`, and this is the
    # assertion that says why: take a valid report and GROW its rubric with passing items.
    # Under the old mean-of-rubric formula each one pulled the number toward 100, which is
    # how an accessibility run carrying two P0s read 79% while a usability run carrying
    # none read 50% — the lenses enumerate different numbers of things. Same findings must
    # now mean the same percentage however large the rubric.
    _fix = FIXTURES / "valid" / "usability-20260715-143000.md"
    _src = _fix.read_text(encoding="utf-8")
    _grown = _src.replace(
        '    - item: "Help and documentation"',
        "".join(f'    - item: "Padding heuristic {i}"\n      score: 4\n' for i in range(12))
        + '    - item: "Help and documentation"', 1)
    if _grown == _src:
        failures.append("rubric-size probe: could not grow the fixture's rubric")
    with tempfile.TemporaryDirectory() as _d:
        # Keeps the fixture's own filename: its asset paths are run-scoped to that stem.
        _p = Path(_d) / _fix.name
        # score/max move with the rubric (they are the rubric view); pct must not.
        _p.write_text(_grown.replace("  score: 31\n", "  score: 79\n")
                             .replace("  max: 36\n", "  max: 84\n"), encoding="utf-8")
        _errs = validate(_p)
        if _errs:
            failures.append(f"rubric-size probe: 12 passing items changed the verdict: {_errs}")
    # One 0-4 scale for every auditor is what makes the floor checkable and the percentage
    # comparable; a per-item `of` let a binary rubric mark a cosmetic divergence `0/1`.
    _binary = (FIXTURES / "valid" / "cuj-20260716-130000.md").read_text(encoding="utf-8")
    _binary = _binary.replace("      score: 4\n", "      score: 1\n      of: 1\n")
    with tempfile.TemporaryDirectory() as _d:
        _p = Path(_d) / "binary-of.md"
        _p.write_text(_binary, encoding="utf-8")
        failures += _expect_invalid(_p, "'of' must be 4")
    # The scorecard cannot cite a lens the run never applied.
    failures += _expect_invalid(FIXTURES / "invalid" / "health-rubric-not-applied.md",
                                "not in 'frameworks'")
    # "Unscored" is reserved for a run with nothing gradable; it is not an opt-out.
    failures += _expect_invalid(FIXTURES / "invalid" / "health-false-unscored.md",
                                "Unscored")

    # index.md: a conforming index passes; a malformed one is rejected.
    failures += _expect_valid_index(FIXTURES / "valid" / "index.md")
    failures += _expect_invalid_index(FIXTURES / "invalid" / "index-badcols.md", "column")

    if failures:
        print("FAIL — report contract:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — report contract (26 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
