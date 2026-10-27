#!/usr/bin/env python3
"""Executable spec for the shared `.ux/audits` report contract.

The human-readable contract lives in
`skills/usability-audit/references/report-contract.md`; this test encodes its
machine-checkable invariants via `scripts/validate_report.py` and asserts that a
conforming report passes while known-malformed reports fail.

Run: `python3 tests/test_report_contract.py` (exit 0 = pass, 1 = fail).
"""
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from validate_report import (PRIORITY_KEYS, derive_verdict, priority_index,  # noqa: E402
                             validate, validate_index)

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



CONTRACT = ROOT / "skills" / "usability-audit" / "references" / "report-contract.md"


def _fenced_blocks(text: str) -> list[str]:
    """Every ```-fenced block body in `text`, outermost fences only."""
    blocks, cur = [], None
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            if cur is None:
                cur = []
            else:
                blocks.append("\n".join(cur))
                cur = None
            continue
        if cur is not None:
            cur.append(line)
    return blocks


def _check_contract_examples() -> list[str]:
    """The contract's OWN examples must obey the contract.

    This exists because five of them stopped obeying it and nothing noticed. Two semantic
    changes landed without their examples following: `pct` became a priority index while
    the §4.1 example kept printing a `score / max` number, and assets became run-scoped
    while the §5 walkthrough examples kept their flat paths. Both produced a document that
    reads as authoritative and teaches a report the validator rejects — and an auditor
    copying an example is the single most likely thing an auditor does.

    The contract itself records why this matters, in the `version` field's note: an auditor
    once copied the literal `0.1.0` from an example and "did exactly what it was told; the
    instruction was the bug". That lesson was written down and then not applied to the
    examples around it.

    Three probes, each one a defect a real run hit:

    1. Every image embed is run-scoped. A flat `./assets/<name>.png` is what §1 forbids.
    2. The prescriptive `score / max` formula for `pct` appears nowhere. Prose that
       *negates* it ("why not `score / max`") is the point and stays legal; it is the
       formula written as an instruction that sent a run to a rejected report — and, on a
       narrow rubric, to a different band.
    3. The §4.1 health example's `pct` equals the priority index over the §3 `summary`
       example. Scoped to the AUDITOR health block (the one with a `rubric:`), because the
       §9 roll-up's `pct` is a mean of its members and obeys a different rule.

    Probe 3 assumes one `summary:` example and one `rubric:`-bearing `health:` example. Add
    a second and this needs to pair them deliberately rather than by document order.
    """
    import re

    if not CONTRACT.exists():
        return [f"missing the contract: {CONTRACT}"]
    text = CONTRACT.read_text(encoding="utf-8")
    errors: list[str] = []

    # 1. Run-scoped embeds.
    for path in (m.group(1).strip() for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", text)):
        rel = path[2:] if path.startswith("./") else path
        if not rel.startswith("assets/"):
            errors.append(f"contract example embeds a non-./assets/ path: {path!r}")
        elif rel.count("/") < 2:
            errors.append(
                f"contract example embeds a FLAT asset path: {path!r} — §1 requires "
                f"./assets/<report-stem>/<name>, and the validator rejects this")

    # 2. No prescriptive score/max formula for pct.
    if "round(100 * score / max)" in text:
        errors.append(
            "contract still prescribes `round(100 * score / max)` for `pct`; §4.1 makes it "
            "the priority index over `summary`, and the validator enforces that")

    # 3. The example numbers agree with the rule.
    blocks = _fenced_blocks(text)
    summaries = [b for b in blocks if re.search(r"^\s*summary:", b, re.MULTILINE)]
    healths = [b for b in blocks
               if re.search(r"^\s*rubric:", b, re.MULTILINE)
               and re.search(r"^\s*pct:", b, re.MULTILINE)]
    if not summaries:
        errors.append("contract has no `summary:` example to check `pct` against")
    elif not healths:
        errors.append("contract has no auditor `health:` example (one with a `rubric:`)")
    else:
        counts = {}
        for key in PRIORITY_KEYS:
            m = re.search(rf"^\s*{key}:\s*(\d+)", summaries[0], re.MULTILINE)
            counts[key] = int(m.group(1)) if m else 0
        shown = int(re.search(r"^\s*pct:\s*(\d+)", healths[0], re.MULTILINE).group(1))
        want = priority_index(counts)
        if shown != want:
            errors.append(
                f"contract's health example prints pct: {shown}, but the priority index "
                f"over its own summary example ({counts}) is {want} — copying the example "
                f"produces a report the validator rejects")

    # The bundle's default members are not "future".
    if "future accessibility" in text:
        errors.append("contract still calls accessibility 'future'; it is a default member "
                      "of the /ux-audit bundle")
    return errors


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

    # --- a `success_criteria` failure needs an item of its own (§4.1) ---------------------
    # The `cuj` auditor's proudest failure class is the silent-data-loss `P1`: every step
    # matched, and then the data did not persist. `success_criteria` are explicitly NOT
    # steps — they are evaluated once, after the journey completes — so while items were
    # steps only, that report was UNWRITABLE. The floor demanded an item at 1 and no step
    # had failed, and all three ways out were falsehoods: invent a non-step item,
    # re-attribute the failure to a step that passed, or soften the P1.
    #
    # The suite shipped the second one. THIS fixture used to score `CUJ-001 step 2` a `1`
    # for a finding whose Framework Violation field reads `success-criteria` and whose text
    # says "Steps 1 and 2 both passed". So asserting it validates is not enough — validity
    # is exactly what the misattribution bought. The ATTRIBUTION is what this pins.
    _cuj = (FIXTURES / "valid" / "cuj-20260716-120000.md").read_text(encoding="utf-8")
    _items = re.findall(r'- item: "([^"]+)"\n\s+score: (\d+|null)', _cuj)
    if not _items:
        failures.append("criteria-item probe: could not parse the cuj fixture's items")
    else:
        _crit = [(n, v) for n, v in _items if "success criteria" in n.lower()]
        _steps = [(n, v) for n, v in _items if " step " in n.lower()]
        if not _crit:
            failures.append(
                "the cuj fixture files a success-criteria P1 but carries no "
                "'<journey> success criteria' item for it to land on")
        if any(v != "4" for _, v in _steps):
            failures.append(
                f"a criteria failure must not mark a STEP down — these steps passed and "
                f"are scored below 4: {[n for n, v in _steps if v != '4']}")
        if not any(v == "1" for _, v in _crit):
            failures.append(
                f"the P1 must land on the criteria item, got {_crit}")

    # ...and the dead end itself: the same report with the criteria item removed must be
    # rejected, and the message must name the way out. Without the hint an auditor's only
    # visible options are the three falsehoods above — which is how the fixture got written.
    _stripped = _cuj.replace("""    - item: "CUJ-001 success criteria"
      score: 1
      note: "P1 - the captured task does not survive a reload; both steps passed"
""", "").replace("  score: 21", "  score: 20").replace("  max: 24", "  max: 20")
    if _stripped == _cuj:
        failures.append("criteria-hint probe: could not strip the criteria item")
    with tempfile.TemporaryDirectory() as _d:
        _p = Path(_d) / "cuj-20260716-120000.md"
        _p.write_text(_stripped, encoding="utf-8")
        failures += _expect_invalid(_p, "success criteria` item, not on a step that passed")

    # --- a finding attributed outside the rubric needs an item too (§4.1) ----------------
    # The same hole, in the auditor that carries four lenses. The usability persona reserves
    # standalone citations for what Shneiderman, the AI heuristics and NPCIS uniquely
    # express, and then grades ten NIELSEN heuristics — so a finding attributed to
    # Shneiderman has no row. It is invisible in the scorecard, and if it is the worst
    # finding the floor cannot be met at all.
    #
    # A real run hit this and resolved it the wrong way: its P1 belonged to Shneiderman #7
    # locus of control, no Nielsen item could carry the 1, so it re-filed the finding under
    # Nielsen #1. The schema steered the attribution. This fixture is that run done honestly
    # — the P1 stays on Shneiderman and brings its own item — and the assertions pin the
    # ATTRIBUTION, not the validity, because validity is exactly what re-filing bought.
    _xfix = FIXTURES / "valid" / "usability-20260718-110000.md"
    _xf = _xfix.read_text(encoding="utf-8")
    failures += _expect_valid(_xfix)
    _xitems = re.findall(r'- item: "([^"]+)"\n\s+score: (\d+|null)', _xf)
    _outside = [(n, v) for n, v in _xitems if "shneiderman" in n.lower()]
    if not _outside:
        failures.append(
            "the cross-framework fixture files a Shneiderman-attributed P1 but carries no "
            "Shneiderman item for it to land on")
    elif not any(v == "1" for _, v in _outside):
        failures.append(f"the P1 must land on the Shneiderman item, got {_outside}")
    if any(v == "1" for n, v in _xitems if "shneiderman" not in n.lower()):
        failures.append(
            "a Shneiderman-attributed P1 must not mark a NIELSEN item down to 1 — that is "
            "the re-attribution this fixture exists to rule out")

    # The dead end: remove the out-of-rubric item and the report is unwritable again.
    _target = ('    - item: "Shneiderman #7 - locus of control"\n'
               '      score: 1\n'
               '      note: "P1 - the user is the responder to an autosave they cannot '
               'initiate or stop"\n')
    _xstripped = (_xf.replace(_target, "")
                     .replace("  score: 39", "  score: 38")
                     .replace("  max: 44", "  max: 40"))
    if _xstripped == _xf:
        failures.append("cross-framework probe: could not strip the Shneiderman item")
    with tempfile.TemporaryDirectory() as _d:
        _p = Path(_d) / _xfix.name
        _p.write_text(_xstripped, encoding="utf-8")
        failures += _expect_invalid(_p, "lowest item score must be 1")
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

    # --- the contract's own examples (they are the most-copied text in the repo) ---
    failures += _check_contract_examples()

    # --- a conformance level is not a priority (§4) --------------------------------
    #
    # `ux-audit` normalized external accessibility findings with a lookup: "Level AA
    # (e.g. 1.4.3 contrast) -> `P1`". Since essentially every real web app fails some AA
    # criterion, and §9's gate blocks on any `P1`, that line made `GO` unreachable for
    # real apps while grading on a different axis from every other auditor.
    contract = (ROOT / "skills" / "usability-audit" / "references"
                / "report-contract.md").read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", contract).lower()
    for probe in ("a conformance level is not a priority",
                  "evidence, not input",
                  # The reachability consequence, kept because without it the rule reads
                  # like style and the lookup looks like a harmless simplification.
                  "unreachable in practice",
                  # And the half that stops the fix becoming a way to publish less.
                  "always a finding"):
        if probe not in flat:
            failures.append(f"contract §4: must state {probe!r}")
    # §9 must send a disproportionate NO-GO back to the grades, not to a third verdict.
    if "grading problem, not a gate problem" not in flat:
        failures.append("contract §9: a disproportionate NO-GO must point at the grades")

    # The gate is REACHABLE with real conformance failures present. Two AA failures priced
    # by impact derive `GO`; the same two priced off their level derive `NO-GO`. This is
    # the whole defect in four lines.
    by_impact = {"total": 2, "p0": 0, "p1": 0, "p2": 1, "p3": 1}
    by_level = {"total": 2, "p0": 0, "p1": 2, "p2": 0, "p3": 0}
    if derive_verdict(by_impact) != "GO":
        failures.append("gate: AA failures graded by impact must still be able to reach GO")
    if derive_verdict(by_level) != "NO-GO":
        failures.append("gate: a P1 must still block — the gate is not what was wrong")

    # The accessibility fixture is the worked example, and it diverges from a level lookup
    # in BOTH directions: its Level AA contrast failure is `P0` because the primary action
    # is unreadable, and its Level A name-role-value failure is `P2` because the field it
    # affects is optional. Priority tracks impact, not the letter.
    acc = (FIXTURES / "valid" / "accessibility-20260716-090000.md").read_text(encoding="utf-8")
    for heading, level, want in (
        ("### [P0] \"Place order\" button text fails contrast", "Level AA", "P0"),
        ("### [P2] Promo-code input has no programmatic label", "Level A", "P2"),
    ):
        if heading not in acc:
            failures.append(f"conformance fixture: lost {want} finding {heading!r}")
            continue
        block_text = acc.split(heading, 1)[1].split("\n### ", 1)[0]
        if level not in block_text:
            failures.append(f"conformance fixture: {want} finding must cite {level}")
    if "Level A." not in acc or "Level AA." not in acc:
        failures.append("conformance fixture: must carry both an A and an AA citation, so "
                        "the two gradings can disagree with a level lookup")

    # index.md: a conforming index passes; a malformed one is rejected.
    failures += _expect_valid_index(FIXTURES / "valid" / "index.md")
    failures += _expect_invalid_index(FIXTURES / "invalid" / "index-badcols.md", "column")

    if failures:
        print("FAIL — report contract:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — report contract (39 checks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
