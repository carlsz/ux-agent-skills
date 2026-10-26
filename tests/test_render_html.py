#!/usr/bin/env python3
"""Tests for `scripts/render_report_html.py` — the self-contained HTML report companion.

Asserts the invariants that make the companion safe and useful: it opens offline (no external
references; images inlined as `data:` URIs), it is deterministic (no diff churn on re-render),
its flipbook/​findings track the source Markdown, and the cuj verified-pass vs. verified-nothing
distinction survives into the HTML.

Run: `python3 tests/test_render_html.py` (exit 0 = pass, 1 = fail).
"""
from __future__ import annotations

import base64
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from render_report_html import render, render_index  # noqa: E402
from validate_report import _split_frontmatter  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "valid"

# A 1x1 transparent PNG — a real image byte payload for the data-URI inlining test.
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

# An external resource reference: src=/href= to http(s) or protocol-relative //.
EXTERNAL_RE = re.compile(r'(?:src|href)\s*=\s*"(?:https?:)?//', re.IGNORECASE)

_ACC_REPORT = """---
auditor: accessibility
schema: 3
version: 0.5.0
date: 2026-01-01T00:00:00Z
target: http://localhost:3000
mode: live
scope: "temp"
frameworks:
  - wcag-2.2
summary:
  total: 1
  p0: 0
  p1: 0
  p2: 1
  p3: 0
health:
  rubric: wcag-2.2
  score: 1
  max: 2
  pct: 50
  band: Acceptable
  items:
    - item: "2.4.3 Focus order"
      score: 0
      of: 1
      note: "focus jumps past the dialog"
    - item: "1.1.1 Non-text content"
      score: 1
      of: 1
---

# Accessibility Audit — temp

## Executive summary
One issue; the evidence screenshot is cited as a bare path.

## Prioritized fixes
1. [P2] A thing

## Findings

### [P2] A thing is wrong
- **Issue Description:** A thing.
- **Framework Violation:** WCAG 2.2 — 2.4.3 Focus Order.
- **Priority:** P2 Minor — fix in the next pass.
- **Evidence:** live capture (./assets/shot.png).
- **Recommended Fix:** fix it.

## Appendix
- **Coverage / not inspected:** nothing out of scope.
"""

_INDEX_MD = """# Audit index

| Date (UTC) | Auditor | Scope | P0 | P1 | P2 | P3 | Health | Report |
|------------|---------|-------|----|----|----|----|--------|--------|
| 2026-01-01T00:00:00Z | usability | temp | 0 | 0 | 1 | 0 | 50 | [report](usability-20260101-000000.md) |
"""


def _self_contained(html: str) -> list[str]:
    errs: list[str] = []
    if EXTERNAL_RE.search(html):
        errs.append("has an external src/href reference")
    low = html.lower()
    if "<link" in low:
        errs.append("has a <link> tag")
    if "@import" in low:
        errs.append("has an @import")
    if re.search(r"url\(\s*['\"]?https?:", html, re.IGNORECASE):
        errs.append("has a url(http…) reference")
    return errs


def _walkthrough_frames(md_text: str) -> int:
    m = re.search(r"^##\s+Walkthrough\s*$(.*?)(?=^##\s|\Z)", md_text, re.MULTILINE | re.DOTALL)
    return len(re.findall(r"^###\s", m.group(1), re.MULTILINE)) if m else 0


def main() -> int:
    failures: list[str] = []
    reports = [
        "usability-20260715-143000", "cuj-20260716-120000",
        "cuj-20260716-130000", "cuj-20260716-140000",
        "accessibility-20260716-090000",
    ]

    # Every fixture report renders self-contained and deterministically.
    for name in reports:
        path = FIX / f"{name}.md"
        first, second = render(path), render(path)
        if first != second:
            failures.append(f"{name}: render is not deterministic")
        failures += [f"{name}: {e}" for e in _self_contained(first)]

    # Finding cards reconcile with summary.total.
    for name in reports:
        md = (FIX / f"{name}.md").read_text(encoding="utf-8")
        fm, _ = _split_frontmatter(md)
        total = (fm.get("summary") or {}).get("total", 0)
        cards = render(FIX / f"{name}.md").count('<article class="finding p')
        if cards != total:
            failures.append(f"{name}: {cards} finding cards, summary.total is {total}")

    # --- the apparatus rail (SPEC §10.7) ----------------------------------------------
    # Every finding keeps its framework citation, source location and grading rationale in
    # a column of their own. This is the design's one structural promise, so it is asserted
    # per card rather than per page: a rail that silently drops a field still looks right.
    usab_cards = render(FIX / "usability-20260715-143000.md")
    for dt in ("<dt>Framework</dt>", "<dt>Source</dt>", "<dt>Why this grade</dt>"):
        if usab_cards.count(dt) != 2:
            failures.append(f"apparatus rail: {dt} should appear once per finding")
    if usab_cards.count('class="fix"') != 2:
        failures.append("finding cards: each should carry its Recommended fix block")
    if "P1 Major — fix before release" not in usab_cards:
        failures.append("finding card: the grading rationale did not reach the rail")
    # `Priority` was once missing from FINDING_FIELD_RE, and the failure was not a blank
    # row: a name absent from the pattern is absent from its lookahead too, so the priority
    # line was swallowed into the preceding field's value. Both halves are asserted.
    for dd in re.findall(r"<dt>Framework</dt><dd>(.*?)</dd>", usab_cards, re.DOTALL):
        if "Priority" in dd:
            failures.append("finding card: Priority was swallowed into Framework Violation")
    # The Evidence screenshot does not belong in a 204px column; it is split out of the
    # rail and rendered beside the prose, while the `file:line` citation stays.
    for dd in re.findall(r"<dt>Source</dt><dd>(.*?)</dd>", usab_cards, re.DOTALL):
        if "<img" in dd or "class=\"missing\"" in dd:
            failures.append("apparatus rail: an Evidence image was left in the rail")
        if "PlaceOrderButton" not in dd and "PromoField" not in dd:
            failures.append("apparatus rail: the file:line citation was lost with the image")

    # A schema-2 report labels that field `Severity`. It still renders — reports are
    # append-only history — in the row the scale carries now.
    legacy_field = _ACC_REPORT.replace("**Priority:**", "**Severity:**")
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "acc.md").write_text(legacy_field, encoding="utf-8")
        html = render(base / "acc.md")
        if "<dt>Why this grade</dt>" not in html:
            failures.append("legacy 'Severity:' field should render in the rail")
        if "P2 Minor — fix in the next pass" not in html:
            failures.append("legacy 'Severity:' field value was dropped")

    # --- read tolerance: a report written before schema 3 ------------------------------
    # Its findings are tagged `[sev4]`..`[sev1]` and its counts are keyed `sevN`. The
    # validator rejects both on write; the RENDERER has to read them, or every report the
    # suite produced before the migration publishes as "No findings" over a full document.
    legacy_scale = (_ACC_REPORT
                    .replace("schema: 3", "schema: 2")
                    .replace("  p2: 1", "  sev2: 1")
                    .replace("  total: 1", "  total: 1")
                    .replace("1. [P2] A thing", "1. [sev2] A thing")
                    .replace("### [P2] A thing is wrong", "### [sev2] A thing is wrong"))
    for key in ("  p0: 0", "  p1: 0", "  p3: 0"):
        legacy_scale = legacy_scale.replace(key, key.replace("p", "sev"))
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "legacy.md").write_text(legacy_scale, encoding="utf-8")
        html = render(base / "legacy.md")
        if html.count('<article class="finding p2"') != 1:
            failures.append("legacy [sev2] finding did not render as a P2 card")
        if "No findings." in html:
            failures.append("legacy report rendered as having no findings")
        # sev2 -> p2, so the brief's chips and lockup are built from the old counts.
        if '1 &times; P2 Minor' not in html:
            failures.append("legacy sevN summary counts did not reach the brief")

    # Flipbook frame count tracks the `### ` frames under `## Walkthrough`.
    for name in ["usability-20260715-143000", "cuj-20260716-120000"]:
        md = (FIX / f"{name}.md").read_text(encoding="utf-8")
        want = _walkthrough_frames(md)
        got = render(FIX / f"{name}.md").count('<figure class="frame')
        if want == 0 or want != got:
            failures.append(f"{name}: {got} flipbook frames, expected {want}")

    # cuj total:0 discriminates verified-pass from verified-nothing.
    if "banner pass" not in render(FIX / "cuj-20260716-130000.md"):
        failures.append("cuj clean pass: missing the verified-pass banner")
    if "banner warn" not in render(FIX / "cuj-20260716-140000.md"):
        failures.append("cuj all-skipped: missing the 'nothing verified' banner")

    # A referenced-but-absent asset degrades to a placeholder without crashing.
    if 'class="missing"' not in render(FIX / "usability-20260715-143000.md"):
        failures.append("absent asset should render a placeholder, not crash")

    # A real asset inlines as a data: URI; a no-walkthrough report shows an evidence gallery
    # harvested from the bare `(./assets/…)` Evidence path.
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "assets").mkdir()
        (base / "assets" / "shot.png").write_bytes(_PNG)
        (base / "acc.md").write_text(_ACC_REPORT, encoding="utf-8")
        html = render(base / "acc.md")
        if "data:image/png;base64," not in html:
            failures.append("real asset was not inlined as a data: URI")
        if "Evidence gallery" not in html:
            failures.append("no-walkthrough report should surface an evidence gallery")
        failures += [f"temp report: {e}" for e in _self_contained(html)]

    # --- the suite roll-up dashboard (contract §9) ----------------------------------------
    # This whole block exists because the dashboard never rendered once. `render()` looked
    # for a `rollup` frontmatter key that no roll-up ever wrote, so every real roll-up fell
    # through to the generic report path and published a header reading "0 findings" above a
    # table of five, with the verdict paragraph silently dropped. Nothing caught it: there
    # was no roll-up fixture in this file to catch it with.
    ROLLUPS = {"rollup-20260716-150000": "nogo", "rollup-20260716-160000": "go"}
    for name, want in ROLLUPS.items():
        path = FIX / f"{name}.md"
        first, second = render(path), render(path)
        if first != second:
            failures.append(f"{name}: render is not deterministic")
        failures += [f"{name}: {e}" for e in _self_contained(first)]
        # It routes to the roll-up renderer, not the generic report path.
        if "UX audit roll-up" not in first:
            failures.append(f"{name}: did not route to the roll-up renderer")
        # The verdict banner exists and carries the right colour.
        if f'class="banner verdict {want}"' not in first:
            failures.append(f"{name}: missing the '{want}' verdict banner")
        # The lead paragraph between the H1 and the first `## ` must survive — the generic
        # path drops it, and it is the dashboard's opening line.
        if "Verdict:" not in first:
            failures.append(f"{name}: lead verdict paragraph was dropped")
        # Member links are repointed to their .html companions.
        if '.md"' in first.split("</header>")[-1]:
            failures.append(f"{name}: a member link still points at .md")

    # The counts come from `summary`, not from a default of 0, and the brief suppresses
    # the zeros instead of dimming them — four cells reading 0 crowd out the one that does
    # not. The merged total and every non-zero level must survive that.
    nogo = render(FIX / "rollup-20260716-150000.md")
    if '<span class="chip total">5 findings</span>' not in nogo:
        failures.append("rollup: the brief does not show the merged total of 5")
    for chip in ("1 &times; P0 Blocking", "2 &times; P1 Major", "2 &times; P2 Minor"):
        if chip not in nogo:
            failures.append(f"rollup: the brief is missing its {chip} chip")
    if "P3 Polish" in nogo:
        failures.append("rollup: a zero count was rendered instead of suppressed")
    # How much of the suite ran is read from `auditors_ran` — the contract's spelling, and
    # the only one any fixture uses. Reading `auditors_run` reported 0 ran, every time.
    if "3 ran, 1 skipped" not in nogo:
        failures.append("rollup: the auditors-ran count is wrong (key spelling?)")

    # Legacy tolerance, asserted in the direction that matters: `report: rollup` still
    # RENDERS as a roll-up (reports are append-only history), while test_report_contract
    # asserts the same fixture fails validation. Read-tolerant, write-strict.
    legacy = render(ROOT / "tests" / "fixtures" / "invalid" / "rollup-legacy-kind.md")
    if "UX audit roll-up" not in legacy:
        failures.append("legacy 'report: rollup' no longer renders as a roll-up")

    # A legacy verdict that jams the token into its prose renders GO, not a red NO-GO.
    # Equality against "go" was the second bug: it would have survived the dispatch fix.
    prose = render(ROOT / "tests" / "fixtures" / "invalid" / "rollup-verdict-prose.md")
    if 'class="banner verdict go"' not in prose:
        failures.append("legacy prose verdict 'GO — …' should render GO, not NO-GO")

    # A legacy roll-up whose stated verdict its own counts do not support renders AMBER —
    # neither a green GO that misleads at a glance, nor the renderer overruling an
    # append-only record. Fresh roll-ups cannot reach this state (validate_rollup rejects
    # them), so this fixture lives under invalid/ and is rendered, not validated, here.
    contested = render(ROOT / "tests" / "fixtures" / "invalid" / "rollup-verdict-mismatch.md")
    if 'class="banner verdict warn"' not in contested:
        failures.append("a GO over a P1 should render contested (amber), not green")
    if "derive" not in contested or "<code>NO-GO</code>" not in contested:
        failures.append("contested banner should name the verdict the counts derive")
    # ...and an honest verdict is never flagged.
    for name, cls in [("rollup-20260716-150000", "nogo"), ("rollup-20260716-160000", "go")]:
        if f'class="banner verdict {cls}"' not in render(FIX / f"{name}.md"):
            failures.append(f"{name}: an honest verdict was flagged as contested")

    # --- the health scorecard (contract §4.1) ---------------------------------------------
    # Rendered from FRONTMATTER, and the body's own `## Design health` section is skipped:
    # printing the same numbers twice in one view is the duplication the contract rules out.
    usab = render(FIX / "usability-20260715-143000.md")
    if usab.count(">Design health<") != 1:
        failures.append("scorecard should render exactly once (frontmatter, not the body)")
    # The score is the brief's dial. It carries a text label as well as the arc, so it is
    # not encoded in geometry alone.
    if 'aria-label="Health score 83 out of 100, Good"' not in usab:
        failures.append("health dial missing its derived percentage / accessible label")
    if ">83</text>" not in usab:
        failures.append("health dial missing its visible percentage")
    # The executive summary is the brief's prose and must not also appear as a body
    # section: one screen stating the same thing twice is what this design removed.
    if usab.count(">Executive summary<") != 0:
        failures.append("the executive summary should be absorbed into the brief")
    if usab.count("The checkout flow completes") != 1:
        failures.append("the executive summary was rendered twice")
    # A run with nothing gradable says so rather than showing 0% or 100%.
    unscored = render(FIX / "cuj-20260716-140000.md")
    if "Unscored" not in unscored:
        failures.append("an unscored run must render as Unscored, not as a percentage")
    if "<text" in unscored:
        failures.append("an unscored run must not draw a score dial at all")
    if "UNVERIFIED" not in unscored:
        failures.append("a cuj run that verified nothing must say so in the brief")
    if "nothing met the bar" in unscored:
        failures.append("a run that verified nothing must not read as a clean sweep")

    # A hard-wrapped list item is one item, not one per source line. These reports wrap at
    # ~95 columns, so treating every line as an item split one list into several, each
    # restarting at 1., with the wrapped remainder stranded as a paragraph between them.
    if unscored.count("<ol>") != 1:
        failures.append("a hard-wrapped ordered list was split into several lists")
    if "<li>" in unscored and "cannot quietly leave the report" not in unscored:
        failures.append("a list item's continuation line was dropped or stranded")

    # The index landing repoints run links from .md to .html and stays self-contained.
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "index.md").write_text(_INDEX_MD, encoding="utf-8")
        html = render_index(base / "index.md")
        if 'href="usability-20260101-000000.html"' not in html:
            failures.append("index: run link not repointed to .html")
        failures += [f"index: {e}" for e in _self_contained(html)]

    if failures:
        print("FAIL — render_html:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("PASS — render_html (self-contained, deterministic, flipbook, findings, cuj banners, rollup dashboard, health)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
