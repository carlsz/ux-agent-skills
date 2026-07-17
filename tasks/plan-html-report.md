# PLAN — HTML report companion (with image-based CUJ walk-throughs)

Implementation plan for the deferred follow-up named in [`SPEC.md`](../SPEC.md) §10.1: a
generated, self-contained **HTML companion** for `.ux/audits` reports, rendering the
`## Walkthrough` screenshots as an interactive flipbook.

- **Spec:** [SPEC.md](../SPEC.md) §10 (report contract schema 2 + the HTML-companion follow-up)
- **Contract:** [report-contract.md](../skills/usability-audit/references/report-contract.md)
- **Status:** Draft — awaiting human review (read-only planning artifact; no code changed here)
- **Approach:** vertical slices — each phase delivers one complete, openable HTML path, then
  the next thickens it. No horizontal "parse everything, then render everything" layering.

---

## 1. What we're building

`scripts/render_report_html.py` — a **deterministic Markdown→HTML transform** that renders a
`.ux/audits/*.md` report (and the `rollup-*.md`) into a **self-contained, offline-openable
`<stem>.html`** beside it. The `## Walkthrough` section becomes an interactive **image
flipbook**; findings become severity-badged cards; the rollup becomes a go/no-go dashboard.

**Core invariants (from SPEC §10.1):**

- **Markdown stays the source of truth.** The `.html` is *derived from* the `.md`. The report
  contract, `validate_report.py`, `index.md`, fixtures, and the roll-up are **unchanged**. No
  schema bump. The companion is an additive view, never a replacement.
- **Self-contained & offline.** Inline CSS + vanilla JS; every `./assets/*` image base64-inlined
  as a `data:` URI. No CDN, no external font, no network fetch — it opens from disk.
- **Findings-only, boundary intact.** The `.html` is written under `.ux/audits/`, already on the
  `audit_safety.py` allowlist — **no safety change**. The auditor still edits no host code.

**The transform engine is a script; the on-demand UX is a thin command+skill.** HTML rendering
itself is a mechanical transform with no judgment, so the engine lives as a **script**
(`scripts/render_report_html.py`, like `validate_report.py`/`validate_cuj.py`). It is consumed
two ways:

- **Auto path** — the existing audit skills call the script as their final step (no new component).
- **On-demand path** — a thin **`/ux-review` command** → a small **`render-report` skill** (the
  *how*: locate `.ux/audits/*.md`, run the script, refresh `index.html`, report what was written)
  lets a user (re)render existing reports outside an audit run.

The command+skill are real components, so they must satisfy **both repo test traps**:
`test_evals.py` globs `skills/*/SKILL.md` and requires a matching `evals/cases/render-report.json`;
`test_components.py` hardcodes per-component checks and needs a hand-written `check_*` wired into
`main()`. **No persona** — rendering holds no point of view (unlike the auditors), so the skill has
a command entry but no `agents/` file. Naming follows the existing `command ≠ skill` precedent
(`/ux-spec`→`spec-cuj`, `/cuj-audit`→`audit-cuj`): **command `ux-review` → skill `render-report`**.

## 2. Prior art that shapes the plan — what the reports already give us for free

Grounded in the six Sprout reports under `sprout/.ux/audits/` (a full-suite run) and the schema-2
contract. A generator is *mostly a deterministic transform* because these structures already exist:

| Structure | Where | What it feeds in the HTML |
|-----------|-------|---------------------------|
| Uniform schema-2 frontmatter (`auditor`, `mode`, `date`, `target`, `scope`, `frameworks`, `summary`) | every report | page header, badges, framework chips, severity bar — no prose scraping |
| `## Walkthrough` = `###` + inline `![](./assets/x.png)` + `>` blockquote | usability + cuj reports | **flipbook slides** (title/frame/caption); cuj is ordered per-journey, usability is named states |
| Five-field `### [sevN]` findings (Issue / Framework / Severity / Evidence / Recommended Fix) | usability, a11y, web-perf | uniform finding **cards** + severity badge parsed from `[sevN]`; count-checks against `summary` |
| Shared asset filenames across Evidence ↔ Walkthrough (e.g. `usability-app-mid-flow.png` in both) | usability | cross-link "finding → its flipbook frame" |
| Rollup frontmatter (`verdict`, `auditors_run/skipped`) + per-auditor severity table + merged issues | `rollup-*.md` | **dashboard**: verdict badge, severity matrix linking to each report's `.html` |
| cuj `total: 0` + `frameworks:[cuj-contract, task-completion, success-criteria]` + manifest table | cuj reports | special-case **VERIFIED PASS** banner + manifest table (never an empty "no findings") |
| `mode`/provenance + dev-lab caveats in appendix | web-perf ("dev-mode lab, not production") | **disclaimer banner** so potential/structural findings aren't misread as measured |

**Gaps the generator must own (also observed in these reports):**

- **Images aren't in the `.md`** — only relative `./assets/*.png` (and a `webperf-trace-cold.json`).
  The renderer reads them off disk relative to the report and base64-inlines them. The validator
  already guarantees walkthrough paths are relative under `./assets/`, so resolution is safe.
- **Not every report has a walkthrough.** In this run only usability + cuj do; accessibility and
  web-perf carry images only in **Evidence** fields. Fallback: when there's no `## Walkthrough`,
  gather Evidence images into a plain gallery rather than a flipbook.
- **cuj `0` ≠ empty.** Must render as PASS, not a blank card.
- **Large assets.** Inline images; do **not** inline a large trace `.json` — link or omit it.

## 3. Design decisions

1. **One script, stdlib + pyyaml only** (pyyaml is already a repo dependency; the other scripts use
   nothing more). Zero new runtime deps keeps CI (`pyyaml` only) unchanged.
2. **Reuse, don't duplicate parsing.** Import `_split_frontmatter`, `FINDING_RE`, `WALKTHROUGH_RE`,
   `IMAGE_RE` from `validate_report.py`. If reuse grows, extract a shared `scripts/report_parse.py`
   both import (noted as a refactor option, not required up front).
3. **Output naming.** `<report-stem>.html` beside `<report-stem>.md`. Report stems are timestamped
   and append-only, so each `.html` is 1:1 with its `.md` (also append-only — not overwritten).
   Assets remain prune-to-latest (stable names, already true). A single **stable `index.html`**
   landing page is regenerated from `index.md` as a live view of all runs.
4. **Determinism.** Identical `.md` (+ assets) ⇒ **byte-identical `.html`**. No timestamps, no
   randomness, sorted attribute order — so re-rendering an unchanged report produces no diff churn.
   Enforced by a test.
5. **Self-contained is the load-bearing invariant.** A test asserts the output contains no
   `http://`/`https://` resource references and that every `<img>` is a `data:` URI.
6. **Invocation — both ways (confirmed).** (a) Auto: the audit skills call the script as their
   final step, after `validate_report.py` succeeds, so a report and its HTML view never drift.
   (b) On demand: `python3 scripts/render_report_html.py <report.md> …` / `--index`, fronted by the
   `/ux-review` command → `render-report` skill for users who want to (re)render existing reports.
7. **Version — `0.5.0` (confirmed).** A distinct new capability ⇒ minor bump from 0.4.0.

## 4. Dependency graph

```
        ┌─────────────────────────────────────────────┐
        │  CORE  (Slice 0)                             │
        │  frontmatter+findings parse · page shell/CSS │
        │  · asset→data:URI inliner · <stem>.html out  │
        └───────────────┬───────────────┬─────────────┘
                        │               │
          ┌─────────────▼───┐   ┌───────▼──────────────────────┐
          │ Walkthrough      │   │ cuj-PASS banner ·            │
          │ flipbook (Slice1)│   │ provenance banner ·          │
          │ JS/keyboard nav  │   │ Evidence fallback gallery    │
          └─────────────┬───┘   │ (Slice 2)                    │
                        │       └───────┬──────────────────────┘
                        └───────┬───────┘
                        ┌───────▼───────────────────┐
                        │ Rollup dashboard +         │
                        │ index.html landing (Slice3)│  (links to per-report .html)
                        └───────┬───────────────────┘
                                │
                        ┌───────▼───────────────────┐
                        │ Integration · tests        │
                        │ (Slice 4): skills call the  │
                        │ script · test_render_html   │
                        └───────┬────────────────────┘
                                │
                        ┌───────▼────────────────────────────┐
                        │ /ux-review command + render-report  │
                        │ skill + eval case + component checks│
                        │ (Slice 5) · then docs/spec/version  │
                        └─────────────────────────────────────┘
```

Everything roots on the CORE transform. The flipbook and the cuj/provenance/fallback work are
independent siblings on top of core (can proceed in parallel). The dashboard reuses core styling
and *links to* per-report HTML, so it comes after both. Slice 4 wires the auto path + tests; Slice
5 adds the on-demand command/skill (the trap-sensitive component work) and closes docs/spec/version.

## 5. Vertical slices & checkpoints

Each slice ends with an openable HTML artifact you can eyeball. Checkpoints are human-review gates.

- **Slice 0 — Skeleton transform.** One report (no walkthrough) → self-contained HTML: header
  from frontmatter, severity bar, finding cards with `[sevN]` badges, Evidence images inlined.
  → **Checkpoint A: review base look/feel before building the flipbook.**
- **Slice 1 — Walkthrough flipbook.** Parse `## Walkthrough` → interactive flipbook (prev/next,
  ←/→ keys, counter), grouped per-journey (cuj) / per-state (usability).
  → **Checkpoint B: review flipbook UX.**
- **Slice 2 — cuj-PASS + provenance + fallback gallery.** cuj `total:0` renders as VERIFIED PASS +
  manifest table; mode/dev-lab disclaimer banner; Evidence-image gallery when no walkthrough.
- **Slice 3 — Rollup dashboard + index landing.** `rollup-*.md` → verdict dashboard + severity
  matrix linking per-report `.html`; regenerate stable `index.html` from `index.md`.
  → **Checkpoint C: review dashboard before wiring into skills.**
- **Slice 4 — Auto path + tests.** `tests/test_render_html.py`; wire the renderer into
  usability-audit / audit-cuj / ux-audit as their final step.
- **Slice 5 — On-demand command + docs.** `/ux-review` command → `render-report` skill +
  `evals/cases/render-report.json` + hand-wired `check_*` in `test_components.py`; flip SPEC §10.1
  to delivered, tick §10.5 DoD, CHANGELOG, bump `plugin.json` to `0.5.0`.
  → **Checkpoint D (final): full suite green + e2e re-render of the Sprout reports.**

## 6. Verification strategy

- **Fixtures first, real reports second.** Drive the transform on the committed fixtures
  (`tests/fixtures/valid/*` — two now carry walkthroughs) and, read-only, on the six Sprout reports
  under `sprout/.ux/audits/` (a genuine full-suite run incl. a rollup and a green cuj pass).
- **Automated (`tests/test_render_html.py`, auto-discovered by CI):**
  - self-contained: output has no `http(s)://` resource refs; every `<img>` is `data:`.
  - determinism: same input ⇒ byte-identical output.
  - flipbook frame count == number of `###` under `## Walkthrough`.
  - finding-card count == `summary.total`; per-severity badges match `summary.sevN`.
  - cuj `total:0` renders the PASS banner, not an empty findings area.
  - a referenced-but-missing asset degrades to a placeholder without crashing.
- **Manual at each checkpoint:** open the generated `.html` in a browser (double-click, offline).
- **Boundary:** after wiring, `git status` in a host repo (Sprout) shows only `.ux/audits/`
  additions; `python3 tests/test_safety.py` stays green.

## 7. Risks & boundaries

- **Offline/self-contained is the invariant to protect** — the one thing that most easily regresses
  (a stray font/CDN link). The test gates it.
- **Diff churn** on append-only reports if output isn't deterministic — hence the byte-identical test.
- **Auditor-stays-findings-only** — the `.html` is derived output under `.ux/audits/`, not host
  code; keep the renderer a pure transform invoked *after* the report is written, never mutating it.
- **Asset bloat** — base64 images enlarge the `.html`; acceptable for portability. Do not inline
  large trace JSON; link or omit.
- **Zero new deps** — stdlib + existing pyyaml only, so CI's dependency set is untouched.

## 8. Decisions (resolved with the human)

1. **Plan file location** — ✅ keep feature-scoped `tasks/plan-html-report.md` /
   `tasks/todo-html-report.md`; the committed Usability-Auditor `tasks/plan.md`/`todo.md` stay as
   history.
2. **Invocation** — ✅ **both**: auto (skills call the script as their final step) + on-demand
   (standalone script fronted by the `/ux-review` command).
3. **Version** — ✅ **`0.5.0`**.
4. **Command** — ✅ **ship now**, named **`/ux-review`** (→ `render-report` skill, no persona).

*Open naming nit to sanity-check during Slice 5:* `/ux-review` reads as "review" rather than
"render report to HTML"; kept as chosen, flag if a clearer verb is wanted before the command ships.
