# Plan — report design: P0–P3, Design Health, and the HTML redesign

Status: step 1 landed (`d6ea39f`), step 2 decided. This file is the input step 3 consumes.

## Confirmed intent

Audit reports become documents worth sending. The Markdown stays canonical and agent-facing;
the HTML becomes a human document for peers and stakeholders reading cold. The expert
apparatus stays at **full strength and in the reading path** — it is the credibility.

- **Out of scope:** no new auditors, frameworks or lenses; the Markdown does not become
  human-facing; no PDF, no hosted site, no build step. Stdlib Python emitting one inlined file.
- **Unchanged invariants:** findings-only, writes confined to `.ux/audits/`, deterministic
  render, six test suites green.

## Chosen direction

**C (Briefing) as the base, with A's permanent apparatus column for findings.** Prototypes in
the session scratchpad under `lab/` (`d-report.html`, `d-rollup.html`); A/B/C kept for
comparison.

- **Hero:** verdict lockup — `GO`, score ring, trend — sized so a screenshot of the top of the
  page is a defensible summary on its own.
- **Findings:** a 204px rail carries *Heuristic*, *Source*, *Why this grade* beside the prose.
  The apparatus is prominent **by position**, which is what lets it stay at full strength
  without competing with the finding itself.
- **Palette/type:** cool paper, institutional teal, humanist display (Optima/Candara stack).
  Verdict colour is reserved for the verdict. **System font stacks only** — no webfont, so the
  output stays self-contained.
- **Zero suppression:** severity levels with no findings are not rendered at all. A clean run
  shows the verdict, a full ring and "no findings" — the good-looking page, which is the fix
  for "the suite looks best when the app is broken".

## Schema 3 — the data shape the design needs

### Priority replaces severity

| Old | New | Name | Action |
|-----|-----|------|--------|
| `sev4` | `P0` | Blocking | Fix immediately |
| `sev3` | `P1` | Major | Fix before release |
| `sev2` | `P2` | Minor | Fix in the next pass |
| `sev1` | `P3` | Polish | Fix if time allows |

Finding headings become `### [P2] <title>`; anchors follow (`#p2-<slug>`); `summary` keys become
`p0..p3`; index columns become `P0 | P1 | P2 | P3`; the roll-up gate becomes **NO-GO if `p0 > 0`
or `p1 > 0`**.

**The sev0 invariant inverts.** The old scale had no zero and `tests/fixtures/invalid/
sev0-present.md` asserted it; the new scale *starts* at zero, so the fixture is rewritten to
assert the new bound (no `P4`, no non-`P` token).

Disambiguation rules go in the contract so the scale survives a re-run — starting with: *if a
user would contact support about it, it is at least P1.*

### `health` — one block, each auditor in its own idiom

```yaml
health:
  rubric: nielsen-10        # which framework the items come from; must appear in `frameworks`
  score: 30                 # sum of item scores
  max: 36                   # sum of item `of` values, n/a items excluded
  pct: 83                   # round(100 * score / max)
  band: Good                # Excellent >=90, Good >=70, Acceptable >=50, Poor >=30, else Critical
  items:
    - item: "Visibility of system status"
      score: 4              # null = not applicable: excluded from BOTH score and max
      of: 4                 # optional, defaults to 4
      note: "aria-live task count; immediate garden feedback"
```

`of` is what makes one block serve four auditors without pretending they share a scale:
usability grades 0–4 against Nielsen; accessibility emits `score: 0, of: 1` per WCAG criterion;
cuj emits one item per journey step; web-performance one per metric. `score`/`max`/`pct` are
derived and **validator-checked against `items`**, so the headline number can never drift from
what it is made of.

**A weak or n/a item must carry a `note`.** Same spirit as a skipped auditor needing a reason:
an unexplained 2/4 is an assertion, not a finding.

### Roll-up `health`

```yaml
health:
  pct: 88
  band: Good
  method: mean-of-auditors
  trend: [71, 76, 79, 81, 83]   # oldest -> newest, prior runs only; [] when no history
  auditors:
    - {auditor: cuj, pct: 100, band: Excellent, unit: "steps verified"}
```

`trend` is read from prior reports in `.ux/audits/`. **It must degrade to `[]`**, not to a
broken chart: an authenticated run is advised to gitignore `.ux/audits/` wholesale, so in those
repos there is no history to read. The trend is a nice-to-have and cannot be load-bearing.

### Where it renders

A `## Design health` section in the body keeps the Markdown readable for agents. **The HTML
renders the scorecard from frontmatter and skips that body section** — this is the fix for the
critique's "says everything three times", applied as a rule rather than a one-off.

## Sequence from here

1. ~~Roll-up contract fix~~ — landed, `d6ea39f`.
2. ~~Visual directions~~ — decided: C + A's rail.
3. **Schema 3, one migration:** P0–P3 and `health` together. Both rewrite `report-contract.md`,
   both touch every fixture, both ripple through `validate_report.py`, the index columns, the
   roll-up table, two personas, four skills, the commands, `SPEC.md` / `README` / `AGENTS.md`.
   Doing them separately pays the fixture-and-docs tax twice.
   - Trap check: no new skill, so `test_evals.py` stays quiet. `test_components.py`'s
     `check_*()` functions assert the "0–4 severity format" in the personas and must be
     rewritten in the same pass, or they pass while verifying a contract that no longer exists.
4. **Build the chosen direction** in `render_report_html.py` against schema 3.
