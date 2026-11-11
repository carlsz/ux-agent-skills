#!/usr/bin/env python3
"""Tests for `scripts/render_report_html.py` — the self-contained HTML report companion.

Asserts the invariants that make the companion safe and useful: it opens offline (no external
references; images inlined as `data:` URIs), it is deterministic (no diff churn on re-render),
its flipbook/findings track the source Markdown, and the cuj verified-pass vs. verified-nothing
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
schema: 2
version: 0.5.0
date: 2026-01-01T00:00:00Z
target: http://localhost:3000
mode: live
scope: "temp"
frameworks:
  - wcag-2.2
summary:
  total: 1
  sev4: 0
  sev3: 0
  sev2: 1
  sev1: 0
---

# Accessibility Audit — temp

## Executive summary
One issue; the evidence screenshot is cited as a bare path.

## Prioritized fixes
1. [sev2] A thing

## Findings

### [sev2] A thing is wrong
- **Issue Description:** A thing.
- **Framework Violation:** WCAG 2.2 — 2.4.3 Focus Order.
- **Severity:** 2 — minor.
- **Evidence:** live capture (./assets/shot.png).
- **Recommended Fix:** fix it.

## Appendix
- **Coverage / not inspected:** nothing out of scope.
"""

_INDEX_MD = """# Audit index

| Date (UTC) | Auditor | Scope | Sev4 | Sev3 | Sev2 | Sev1 | Report |
|------------|---------|-------|------|------|------|------|--------|
| 2026-01-01T00:00:00Z | usability | temp | 0 | 0 | 1 | 0 | [report](usability-20260101-000000.md) |
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
        # schema 3 — priority-scored. Its presence here is what makes the
        # cards-vs-summary.total check cover the vocabulary the suite now emits.
        "usability-20261111-143000",
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
        cards = render(FIX / f"{name}.md").count('<article class="finding sev')
        if cards != total:
            failures.append(f"{name}: {cards} finding cards, summary.total is {total}")

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

    # --- schema 3 renders in its own vocabulary, on the shared colour ramp ----------
    # The CSS ramp is positional (4 hottest, 1 coolest) and the stylesheet knows nothing
    # about priority, so the class must stay `sev{N}` while the badge text follows the
    # schema. Both halves are asserted: a renderer that emitted `class="finding P1"` would
    # lose every colour, and one that emitted a `sev1` badge would lie about the rank.
    s3 = render(FIX / "usability-20261111-143000.md")
    for badge, ramp in (("P1", "sev3"), ("P2", "sev2"), ("P3", "sev1")):
        if f'<span class="badge {ramp}">{badge}</span>' not in s3:
            failures.append(f"schema 3: {badge} should render on the {ramp} ramp")
    if s3.count("<dt>Priority</dt>") != 3:
        failures.append("schema 3: every finding must render its Priority row")
    for label in ("P0 · Blocks the task", "P3 · No effect"):
        if label not in s3:
            failures.append(f"schema 3: rating bar missing {label!r}")

    # Schema 2 is permanent, so its rendering must not drift.
    s2 = render(FIX / "usability-20260715-143000.md")
    for badge in ("sev3", "sev2"):
        if f'<span class="badge {badge}">{badge}</span>' not in s2:
            failures.append(f"schema 2: {badge} badge should be unchanged")
    if "<dt>Priority</dt>" in s2:
        failures.append("schema 2: a schema-2 card must not grow a Priority row")

    # --- the roll-up dashboard ------------------------------------------------------
    # Before this slice NO rollup fixture existed, so `_render_rollup()` was entirely
    # untested -- and it showed: with `verdict` absent it emitted a red alarm banner with an
    # empty <b></b>. Two fixtures now cover the shape and the hazard.
    rollups = ["rollup-20261111-150000", "rollup-20261111-160000"]
    for name in rollups:
        path = FIX / f"{name}.md"
        first, second = render(path), render(path)
        if first != second:
            failures.append(f"{name}: rollup render is not deterministic")
        failures += [f"{name}: {e}" for e in _self_contained(first)]

    found = render(FIX / f"{rollups[0]}.md")
    # The distribution is the headline, on the hottest ramp because a P0 is present.
    if '<div class="banner alert headline">' not in found:
        failures.append("rollup: a P0 present must headline on the alert ramp")
    for part in ("1 × P0", "4 × P1", "7 × P2", "2 × P3"):
        if part not in found:
            failures.append(f"rollup: distribution missing {part!r}")
    if "3 auditors ran, 1 skipped" not in found:
        failures.append("rollup: coverage must sit beside the counts")
    if "not a ship call" not in found:
        failures.append("rollup: the dashboard must say it is not a ship call")

    # The hazard: an empty distribution from a partial run must NOT read as a pass. This is
    # the same discriminator the cuj banners draw, applied to the suite.
    empty = render(FIX / f"{rollups[1]}.md")
    if '<div class="banner warn headline">' not in empty:
        failures.append("rollup: all-zero WITH skipped auditors must warn, not pass")
    if "banner pass" in empty:
        failures.append("rollup: all-zero with 3 of 4 auditors skipped must not render a pass")
    if "not a clean bill of health" not in empty:
        failures.append("rollup: the partial-coverage warning must say so in words")

    # The dropped verdict must leave no trace: a class literally named `nogo`, or a GO/NO-GO
    # word, would reinstate the call the suite no longer makes.
    for html_out, label in ((found, "rollup"), (empty, "empty rollup")):
        for stale in ('banner verdict', 'nogo', 'banner go"', "suite verdict"):
            if stale in html_out:
                failures.append(f"{label}: stale verdict artifact {stale!r} still rendered")

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
    print("PASS — render_html (self-contained, deterministic, flipbook, findings, cuj banners, rollup dashboard)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
