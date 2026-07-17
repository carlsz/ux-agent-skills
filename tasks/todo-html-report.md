# TODO — HTML report companion (with image-based CUJ walk-throughs)

> **STATUS: delivered in 0.5.0** (branch `feat/report-walkthrough`, Phases 0–5 committed). All
> phases below are complete: the engine `scripts/render_report_html.py`, the flipbook,
> cuj-pass/provenance banners + evidence gallery, the roll-up dashboard + `index.html`,
> `tests/test_render_html.py`, skill wiring, and the `/ux-review` command + `render-report`
> skill. The full test suite (7 files) is green. Left unchecked below as the historical plan.

Task list for [`plan-html-report.md`](./plan-html-report.md). Grouped by vertical slice; each
delivers an openable HTML path. `[ ]` = todo, `[~]` = in progress, `[x]` = done.

Every task carries **Files**, **Acceptance**, **Verify**, **Deps**. Checkpoints (⛳) are
human-review gates between phases — stop and get sign-off before crossing.

---

## Phase 0 — Skeleton transform (one report → self-contained HTML) ⭐

### T0.1 — `render_report_html.py` scaffold + frontmatter header
- [ ] New script with a CLI: `render_report_html.py <report.md> [<report.md> …]`.
- **Files:** `scripts/render_report_html.py` (new).
- **Acceptance:** imports `_split_frontmatter` from `validate_report.py` (no duplicate YAML
  parsing); emits a valid HTML5 doc with an inline `<style>`; header renders `auditor`, `mode`,
  `date`, `target`, `scope`, and `frameworks` as chips; a severity bar from `summary`
  (`sev4..sev1` + total). Writes `<stem>.html` beside the input `.md`. Exit 0 on success.
- **Verify:** `python3 scripts/render_report_html.py tests/fixtures/valid/accessibility-20260716-090000.md`
  → `<stem>.html` opens in a browser and shows the header + severity bar.
- **Deps:** none (foundational).

### T0.2 — Finding cards with severity badges
- [ ] Parse `### [sevN] <title>` blocks + the five labelled fields into cards.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** reuse `FINDING_RE` from `validate_report.py`; each finding is a card with a
  colour-coded `[sevN]` badge and the five fields (Issue / Framework / Severity / Evidence /
  Recommended Fix); cards ordered as in the body; card count == `summary.total`.
- **Verify:** rendered accessibility fixture shows 4 cards (3×sev2, 1×sev1) matching its summary.
- **Deps:** T0.1.

### T0.3 — Asset → data-URI inliner (Evidence images)
- [ ] Resolve `./assets/*` image refs relative to the report and base64-inline as `data:` URIs.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** every `![alt](./assets/x.png)` in Evidence becomes an inline `<img src="data:…">`;
  a missing file degrades to a labelled placeholder (no crash); non-image refs (e.g. a `.json`
  trace) are linked/skipped, not inlined.
- **Verify:** render the Sprout `accessibility-20260717-204508.md` (read-only) → images embedded;
  output contains no `http(s)://` resource refs; a hand-broken path yields a placeholder.
- **Deps:** T0.1.

> ⛳ **Checkpoint A — base look/feel.** Open the two rendered reports. Sign off on typography,
> severity colours, and card layout before investing in the flipbook.

---

## Phase 1 — Walkthrough flipbook

### T1.1 — Parse `## Walkthrough` into ordered frames
- [ ] Extract frames: `###` heading (title) + inline image (frame) + `>` blockquote (caption).
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** reuse `WALKTHROUGH_RE`/`IMAGE_RE`; frames keep document order; cuj frames group by
  journey prefix (`CUJ-00x · Step n`), usability frames are one state group; a report with no
  `## Walkthrough` yields zero frames (no error).
- **Verify:** `cuj-20260716-120000.md` fixture → 3 frames; Sprout `cuj-20260717-203805.md` → 7
  frames across 3 journey groups.
- **Deps:** T0.3 (data-URI inliner).

### T1.2 — Interactive flipbook UI (inline vanilla JS/CSS)
- [ ] Render the frames as a flipbook: prev/next buttons, ←/→ keyboard nav, a frame counter.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** no external JS/deps; keyboard + button nav work offline; per-group sections
  render (cuj: one flipbook per journey or a grouped strip; usability: state gallery); still
  fully self-contained.
- **Verify:** open Sprout `usability-20260717-204236.md` and `cuj-20260717-203805.md` renders;
  arrow keys advance frames; counter matches the `###` count.
- **Deps:** T1.1.

> ⛳ **Checkpoint B — flipbook UX.** Review interaction (nav, grouping, caption readability) on a
> real cuj walk-through before adding the special cases.

---

## Phase 2 — cuj-PASS, provenance, and fallback gallery

### T2.1 — cuj verified-pass rendering
- [ ] Special-case cuj `total: 0` (with `task-completion`+`success-criteria` frameworks) as a PASS.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** renders a prominent "N/N journeys passed, M/M steps verified ✅" banner (never an
  empty "no findings" card); renders the CUJ manifest table; a cuj run carrying only
  `[cuj-contract]` is rendered as "verified nothing", not a pass.
- **Verify:** Sprout `cuj-20260717-203805.md` shows the 3/3 · 7/7 PASS banner + manifest.
- **Deps:** T0.2.

### T2.2 — Provenance / mode disclaimer banner
- [ ] Surface `mode` and dev-lab caveats as a banner.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** `mode: hybrid/live/static` shown; when the report is web-performance dev-lab
  (appendix says "dev-mode lab, not production"), a disclaimer banner renders so potential findings
  aren't misread as measured.
- **Verify:** Sprout `web-performance-20260717-204654.md` shows a dev-lab banner.
- **Deps:** T0.1.

### T2.3 — Evidence-image fallback gallery
- [ ] When a report has no `## Walkthrough`, gather Evidence-embedded images into a gallery.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** accessibility/web-perf reports (no walkthrough) render a simple image gallery from
  their Evidence images; reports with a walkthrough are unaffected.
- **Verify:** Sprout `accessibility-20260717-204508.md` shows a gallery of its Evidence captures.
- **Deps:** T0.3, T1.1.

---

## Phase 3 — Rollup dashboard + index landing

### T3.1 — Rollup dashboard
- [ ] Render `rollup-*.md` → dashboard.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** verdict badge (go/🔴 no-go) from `verdict`; per-auditor severity matrix with links
  to each report's generated `.html`; merged top issues; auditors run/skipped; cuj row shown as PASS.
- **Verify:** Sprout `rollup-20260717-204844.md` → red NO-GO badge + table linking the 4 per-report
  HTMLs.
- **Deps:** T0.2 (styling reuse); per-report HTML exists (Phase 0–2).

### T3.2 — `index.html` landing page
- [ ] `render_report_html.py --index [<index.md>]` regenerates a stable `index.html`.
- **Files:** `scripts/render_report_html.py`.
- **Acceptance:** parses `index.md` rows; emits a stable `index.html` (overwritten each run) listing
  every run with links to its `.html`; self-contained.
- **Verify:** run against Sprout `.ux/audits/index.md` → `index.html` lists all runs and links resolve.
- **Deps:** T3.1.

> ⛳ **Checkpoint C — dashboard.** Review the roll-up dashboard + index before wiring the renderer
> into the audit skills (integration changes what every audit run emits).

---

## Phase 4 — Auto path + tests

### T4.1 — Test suite
- [ ] Add `tests/test_render_html.py` (auto-discovered by CI).
- **Files:** `tests/test_render_html.py` (new).
- **Acceptance:** asserts — self-contained (no `http(s)://` refs; every `<img>` is `data:`);
  determinism (same input ⇒ byte-identical output); flipbook frame count == `###` under
  `## Walkthrough`; card count/badges == `summary`; cuj-PASS banner present; missing asset →
  placeholder, no crash. Uses the committed fixtures.
- **Verify:** `python3 tests/test_render_html.py` exits 0; the whole `for t in tests/test_*.py` loop
  stays green.
- **Deps:** Phases 0–3.

### T4.2 — Auto path: skills call the renderer
- [ ] Wire the renderer as the final step of each audit skill, after `validate_report.py`.
- **Files:** `skills/usability-audit/SKILL.md`, `skills/audit-cuj/SKILL.md`,
  `skills/ux-audit/SKILL.md` (rollup renders the dashboard + refreshes `index.html`).
- **Acceptance:** each skill's self-check/finish step invokes `render_report_html.py` on the
  just-written report (and `--index`); prose stays tool-agnostic; the write stays under
  `.ux/audits/` (safety unaffected).
- **Verify:** `python3 tests/test_components.py` green; `python3 tests/test_safety.py` green.
- **Deps:** T4.1.

---

## Phase 5 — On-demand command + docs

### T5.1 — `render-report` skill (the on-demand *how*)
- [ ] Author a small skill that locates `.ux/audits/*.md`, runs the renderer, refreshes
      `index.html`, and reports what was written. No persona (rendering holds no point of view).
- **Files:** `skills/render-report/SKILL.md` (new; `name: render-report` matching the dir).
- **Acceptance:** frontmatter `name`/`description`; body has numbered steps + exit criteria; the
  `description` is a routing corpus distinct from the audit skills (**< 0.75 similarity**, or CI
  fails); writes stay under `.ux/audits/`.
- **Verify:** `python3 tests/test_evals.py` green (see T5.3); reads cleanly.
- **Deps:** T4.1 (script feature-complete).

### T5.2 — `/ux-review` command (the *when*)
- [ ] Thin entry point that parses which reports to render and invokes the `render-report` skill.
- **Files:** `commands/ux-review.md` (new; `name`, `description`, `argument-hint`).
- **Acceptance:** documents args (a report path / glob / whole `.ux/audits` dir, `--index`); stays
  thin (parse + invoke, no inlined workflow). *(Naming nit: confirm `ux-review` vs a render-ish
  verb before finalizing — plan §8.)*
- **Verify:** `python3 tests/test_components.py` green (see T5.4).
- **Deps:** T5.1.

### T5.3 — Eval case (mandatory — `test_evals.py` glob trap)
- [ ] Add the eval case the moment `skills/render-report/SKILL.md` exists (CI goes red otherwise).
- **Files:** `evals/cases/render-report.json` (new); possibly `evals/cases/competitors.json`
  (add a `description` for any new negative-trigger `owner`).
- **Acceptance:** `skill_name: render-report`; ≥3 positive triggers, ≥2 negatives (each `owner`
  present in competitors.json); ≥1 behavioral eval (`id`/`prompt`/`expected_output`/`expectations`);
  Tier-2 routing ranks it top-k and no negative ranks it first.
- **Verify:** `python3 tests/test_evals.py` green (routing + minimums + no collision).
- **Deps:** T5.1.

### T5.4 — Component checks (mandatory — `test_components.py` hardcoded trap)
- [ ] Hand-write `check_render_report_skill()` and a `check_command()` call for `ux-review`, wired
      into `main()` (nothing auto-covers a new component).
- **Files:** `tests/test_components.py`.
- **Acceptance:** the new checks assert the skill/command conform (frontmatter, thin command,
  writes-boundary language) and run in `main()`; suite count updated.
- **Verify:** `python3 tests/test_components.py` green and actually exercises the new component.
- **Deps:** T5.2.

### T5.5 — Docs, spec, version
- [ ] Flip SPEC §10.1 "HTML companion deferred" → delivered; tick the §10.5 DoD line; CHANGELOG
      entry; bump `plugin.json` to **0.5.0**; note the HTML view in the report contract; add the
      new command/skill to the relevant subdirectory READMEs and `DOC_FILES` in `tests/test_docs.py`.
- **Files:** `SPEC.md`, `CHANGELOG.md`, `.claude-plugin/plugin.json`,
  `skills/usability-audit/references/report-contract.md`, `commands/README.md`,
  `skills/README.md`, `tests/test_docs.py`.
- **Acceptance:** SPEC/CHANGELOG reflect the delivered companion + `/ux-review`; version `0.5.0`;
  new doc paths added to `DOC_FILES`; `tests/test_docs.py` green.
- **Verify:** full suite green; render all six Sprout reports read-only; `git status` in Sprout
  shows only `.ux/audits/` additions.
- **Deps:** T5.3, T5.4.

> ⛳ **Checkpoint D (final) — done when:** the full `tests/test_*.py` loop is green; every Sprout
> report + the rollup + `index.html` render self-contained and open offline; `/ux-review` renders
> existing reports on demand; the auditor still writes nowhere but `.ux/audits/`.

---

## Decisions (resolved — see plan §8)

- [x] **Plan file names** — keep `tasks/plan-html-report.md` / `todo-html-report.md`.
- [x] **Invocation** — both auto + on-demand.
- [x] **Version** — `0.5.0`.
- [x] **Command** — ship now as `/ux-review` (→ `render-report` skill, no persona).
