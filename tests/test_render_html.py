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

from render_report_html import _slug, render, render_index  # noqa: E402
from validate_report import _split_frontmatter  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "valid"

# A 1x1 transparent PNG — a real image byte payload for the data-URI inlining test.
_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

# Deep-link plumbing: every `id="…"` the page mints, and every `href` that could use one.
_ID_RE = re.compile(r'\sid="([^"]+)"')
_HREF_RE = re.compile(r'<a href="([^"]+)"')

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
  pct: 90
  band: Excellent
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


def render_text(md: str) -> str:
    """Render a report given as a string, for cases no fixture should carry."""
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "usability-20260101-000000.md"
        path.write_text(md, encoding="utf-8")
        return render(path)


_DUP_HEADINGS = """---
auditor: usability
schema: 3
version: 0.7.0
date: 2026-01-01T00:00:00Z
target: http://localhost:3000
mode: static
scope: "temp"
frameworks:
  - nielsen-10
summary:
  total: 2
  p0: 0
  p1: 0
  p2: 2
  p3: 0
health:
  rubric: nielsen-10
  score: 38
  max: 40
  pct: 93
  band: Excellent
  items:
    - {item: "Consistency and standards", score: 2, note: "two findings cite it"}
---

# Usability audit

## Findings

### [P2] The same heading twice

- **Issue Description:** first one.
- **Framework Violation:** Nielsen #4 (nielsen-10).
- **Priority (P2):** minor.
- **Evidence:** `a.tsx:1` — potential, unverified.
- **Recommended Fix:** fix it.

### [P2] The same heading twice

- **Issue Description:** second one, same title.
- **Framework Violation:** Nielsen #4 (nielsen-10).
- **Priority (P2):** minor.
- **Evidence:** `b.tsx:1` — potential, unverified.
- **Recommended Fix:** fix it too.

## Appendix

- Coverage: static only.
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
    # harvested from the bare `(./assets/…)` Evidence path. The path here is FLAT — the
    # layout before assets became per-run — and it still renders, on purpose: the renderer
    # is read-tolerant where the validator is write-strict, and the suite's back-catalogue
    # of reports was all written against the flat layout.
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "assets").mkdir()
        (base / "assets" / "shot.png").write_bytes(_PNG)
        (base / "acc.md").write_text(_ACC_REPORT, encoding="utf-8")
        html = render(base / "acc.md")
        if "data:image/png;base64," not in html:
            failures.append("legacy flat asset path was not inlined as a data: URI")
        if "Evidence gallery" not in html:
            failures.append("no-walkthrough report should surface an evidence gallery")
        failures += [f"temp report: {e}" for e in _self_contained(html)]
    # ...and the layout reports are written in NOW: `./assets/<report-stem>/`. Nothing in
    # the renderer special-cases either shape — it resolves relative to the report's own
    # directory — but a path regex that stopped at the first `/` would silently drop every
    # current report's evidence while the legacy case above stayed green.
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "assets" / "acc").mkdir(parents=True)
        (base / "assets" / "acc" / "shot.png").write_bytes(_PNG)
        (base / "acc.md").write_text(
            _ACC_REPORT.replace("(./assets/shot.png)", "(./assets/acc/shot.png)"),
            encoding="utf-8")
        html = render(base / "acc.md")
        if "data:image/png;base64," not in html:
            failures.append("run-scoped asset path was not inlined as a data: URI")
        failures += [f"run-scoped report: {e}" for e in _self_contained(html)]

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
    if 'aria-label="Health score 73 out of 100, Good"' not in usab:
        failures.append("health dial missing its derived percentage / accessible label")
    if ">73</text>" not in usab:
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

    # --- fields written WITHOUT the markdown bullet ------------------------------------
    # Contract §5 lists the five fields as a bullet list, which reads both as "these are
    # the fields" and as "this is the markup" — and real auditors split on it: given the
    # same §5, a cuj run bulleted its fields while usability and accessibility runs wrote
    # bare bold paragraphs. The validator tests field presence by substring, so bare-bold
    # is contract-VALID; while the renderer required the bullet, such a report produced
    # finding cards with entirely empty bodies — no prose, no rail, no evidence, no fix.
    # Total silent loss on a valid document, so assert the tolerant form directly.
    bare = _ACC_REPORT.replace("\n- **", "\n**")
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "barebold.md"
        path.write_text(bare, encoding="utf-8")
        html = render(path)
    if html.count('<article class="finding p') != 1:
        failures.append("bare-bold fields: the finding card itself went missing")
    if '<div class="prose"></div>' in html:
        failures.append("bare-bold fields: finding body rendered EMPTY (fields dropped)")
    for dt in ("<dt>Framework</dt>", "<dt>Source</dt>", "<dt>Why this grade</dt>"):
        if dt not in html:
            failures.append(f"bare-bold fields: apparatus rail lost {dt}")
    for text in ("WCAG 2.2", "P2 Minor", "fix it"):
        if text not in html:
            failures.append(f"bare-bold fields: dropped field content {text!r}")

    # --- deep links: the fragments the Markdown already writes must land on something ----
    #
    # The suite writes two kinds of deep link and the HTML answered neither: a roll-up's
    # `## Merged top issues` points at `member.md#p1-…`, and a report's own prioritized
    # fixes point at `#p1-…`. The renderer emitted no `id` attribute anywhere, so EVERY one
    # of those was dead on arrival — the click did nothing, which reads as a broken page
    # rather than a missing feature. These checks resolve each fragment against the ids
    # actually present, the same way a browser does.
    rendered = {}
    for name in ("rollup-20260716-150000", "usability-20260715-143000",
                 "accessibility-20260716-090000", "cuj-20260716-120000"):
        rendered[f"{name}.html"] = render(FIX / f"{name}.md")
    ids = {k: set(_ID_RE.findall(v)) for k, v in rendered.items()}
    seen_fragments = 0
    for fname, page in rendered.items():
        for href in _HREF_RE.findall(page):
            if "#" not in href or href.startswith(("http:", "https:")):
                continue
            target, frag = href.split("#", 1)
            seen_fragments += 1
            where = target or fname
            if where not in ids:
                failures.append(f"deep link: {fname} points at unrendered {target}")
            elif frag not in ids[where]:
                failures.append(f"deep link: {fname} -> {href} resolves to nothing")
    # A fixture set with no fragment links would pass the loop above vacuously, which is
    # precisely how this defect survived: nothing linked, so nothing was dead.
    if seen_fragments < 5:
        failures.append(
            f"deep link: only {seen_fragments} fragment links in the fixtures — the "
            "roll-up's merged top issues and a report's prioritized fixes must link to "
            "anchors, or this check proves nothing")

    # Each finding card is the target, not its `<h3>`: the heading sits below the priority
    # chip, so anchoring it would scroll the chip out of view on arrival.
    usab = rendered["usability-20260715-143000.html"]
    if 'id="p1-place-order-gives-no-processing-feedback"' not in usab:
        failures.append("deep link: finding card carries no id")
    if '<article class="finding p1" id="p1-place-order-gives-no-processing-feedback"' not in usab:
        failures.append("deep link: the id must sit on the card, not inside it")

    # The anchor is the slug of the heading AS WRITTEN, tag included. Slugging the displayed
    # title instead would silently drop the `p1-` prefix every link in the suite relies on.
    if 'id="place-order-gives-no-processing-feedback"' in usab:
        failures.append("deep link: card slugged from the display title, not the heading")

    # `## Executive summary` and `## Design health` have no body section — the brief and the
    # scorecard absorbed them — so those two ids have to live on the absorbing blocks or a
    # link into either section is dead by design.
    for absorbed in ('id="executive-summary"', 'id="design-health"'):
        if absorbed not in usab:
            failures.append(f"deep link: absorbed section lost its anchor ({absorbed})")

    # Ids are page-unique: a duplicate is invalid HTML and makes the second target
    # unreachable.
    for page_name, page in rendered.items():
        found = _ID_RE.findall(page)
        if len(found) != len(set(found)):
            dupes = sorted({i for i in found if found.count(i) > 1})
            failures.append(f"deep link: duplicate ids in {page_name}: {dupes}")

    # Slugging is GitHub's, because GitHub is where the canonical Markdown is read. These
    # three cases are the ones real reports produced and a naive slugger gets wrong.
    for heading, want in (
        ('[P1] "Place order" gives no processing feedback',
         "p1-place-order-gives-no-processing-feedback"),
        # An em dash is removed, not replaced, so the spaces around it collapse to two
        # hyphens — the shape every cuj anchor has.
        ("[P1] CUJ-001 — a captured task does not survive a reload",
         "p1-cuj-001--a-captured-task-does-not-survive-a-reload"),
        # A heading written with HTML entities slugs from the DECODED text: a real report's
        # `&lt;body&gt;` anchor is `body`, and entity-blind slugging yields `ltbodygt`.
        ("[P2] Keyboard focus is lost to &lt;body&gt; after editing",
         "p2-keyboard-focus-is-lost-to-body-after-editing"),
    ):
        got = _slug(heading)
        if got != want:
            failures.append(f"deep link: _slug({heading!r}) == {got!r}, want {want!r}")

    # A deep-linked card says which one it is; the scroll alone does not.
    if ".finding:target" not in usab:
        failures.append("deep link: arriving at a card is not visually acknowledged")

    # Every `## ` heading in the source carries its slug in the HTML. The fixtures link to
    # finding anchors but not to section anchors, so without this the section ids could all
    # vanish with the deep-link checks still green.
    for name in ("usability-20260715-143000", "rollup-20260716-150000"):
        md = (FIX / f"{name}.md").read_text(encoding="utf-8")
        page = rendered[f"{name}.html"]
        for heading in re.findall(r"^##\s+(.*)$", md, re.MULTILINE):
            want = _slug(heading)
            if f'id="{want}"' not in page:
                failures.append(f"deep link: {name} section {heading!r} has no id={want!r}")

    # Two findings can share a heading. GitHub gives the second `-1`; emitting the same id
    # twice is invalid HTML and leaves the second one unreachable — and the fixtures have no
    # repeated heading, so only a document written for it can prove the dedupe works.
    dup = render_text(_DUP_HEADINGS)
    dup_ids = _ID_RE.findall(dup)
    if len(dup_ids) != len(set(dup_ids)):
        failures.append("deep link: repeated headings minted duplicate ids")
    for want in ('id="p2-the-same-heading-twice"', 'id="p2-the-same-heading-twice-1"'):
        if want not in dup:
            failures.append(f"deep link: repeated heading did not get {want}")

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
