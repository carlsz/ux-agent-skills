# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.1] - 2026-07-17

### Changed
- **Docs: sharpened positioning and README structure.** The tagline and intro now read
  "Audit, spec, **and verify**" / "specify, audit, and rigorously verify" — dropping the
  "design and ship" / "generate" wording that overclaimed against the **findings-only**
  boundary. The corrected tagline is synced across `README.md`, `plugin.json`, and
  `marketplace.json` (the marketplace-facing descriptions).
- README restructured for readability: **Installation** moved up front (right after the
  command table), the **shared reporting contract** promoted to a top-level section, the
  **visual walk-through / HTML** section moved ahead of the Sprout example, the roll-up
  heading shortened, command namespacing standardized (`/ux-agent-skills:<name>`), and the
  duplicated repo-layout tree trimmed to a pointer to `AGENTS.md`.
- Documented **[agent-skills](https://github.com/addyosmani/agent-skills) as an optional
  install** in the Dependency section — it sharpens the CUJ-authoring interview via
  `interview-me`, and `/ux-spec` degrades gracefully without it.

## [0.5.0] - 2026-07-17

### Added
- **Self-contained HTML report companion** — `scripts/render_report_html.py` renders any
  `.ux/audits` report into a single offline-openable `.html` beside its Markdown: findings as
  severity-badged cards, the captured screenshots as an **interactive walk-through flipbook**
  (grouped by CUJ journey), the roll-up as a **go/no-go dashboard**, and an `index.html` landing
  page. Everything is inlined (CSS + images as `data:` URIs), so it opens from disk with no
  network access; output is deterministic (no diff churn on re-render).
  - A cuj `total: 0` renders a green **verified-pass** banner (or an amber "nothing verified"
    when frameworks are `cuj-contract` only); web-performance dev-lab and static runs get a
    provenance banner; reports with no walkthrough surface their Evidence screenshots as a
    gallery (harvesting both `![](…)` embeds and the bare `(./assets/…)` paths older reports use).
- **`/ux-review` command** (+ the `render-report` skill) renders existing `.ux/audits` reports
  to HTML on demand — for refreshing the view after pulling a branch or rendering an older run.

### Changed
- The `usability-audit`, `audit-cuj`, and `ux-audit` skills now render the HTML companion as
  their final step (after validation). The Markdown report stays the source of truth; the
  `.html` is a derived view, written under `.ux/audits/`, so the safety invariant is unchanged.

## [0.4.0] - 2026-07-17

### Added
- **Visual walk-through in reports** — the usability and CUJ auditors now turn the screenshots
  they already capture in live mode into a rendered, ordered `## Walkthrough` section: a per-step
  visual record of a CUJ, or a key-states gallery (initial / mid-flow / success / error / empty)
  for a usability flow. Images are embedded inline (`![]()`) so they render in Markdown viewers,
  and referenced with the render-vs-source honesty rule (live/hybrid only; static mode captures
  nothing and emits no walk-through). See SPEC.md §10.
  - **Stable asset naming, prune-to-latest** — screenshots save under `.ux/audits/assets/` with
    deterministic names (`cuj-<id>-step-<n>.png`, `usability-<scope-slug>-<state>.png`) so a
    re-run overwrites rather than accumulates, bounding the committed binary footprint.

### Changed
- **Report contract `schema` 1 → 2** (`skills/usability-audit/references/report-contract.md`).
  Schema 2 adds the optional `## Walkthrough` body section (after `## Findings`, before
  `## Appendix`) and the `assets/` naming convention. `scripts/validate_report.py` now requires
  `schema == 2` and lightly checks that any walkthrough image path is relative and under
  `./assets/` — it never requires the section to exist nor that a file is on disk. Report
  fixtures move to `schema: 2`; the CUJ *journey* file contract is unaffected (still schema 1).

## [0.3.0] - 2026-07-17

### Added
- **Critical User Journeys** — a second capability beside the auditor suite: give a host app a
  durable, machine-checkable definition of the flows it exists for, and an auditor that replays
  them and reports the exact step that broke.
  - **`/ux-spec`** — the `cuj-author` persona (`agents/`) and `spec-cuj` skill (`skills/`)
    interview the user one question at a time to author journeys, write each to `.ux/cujs/`, and
    regenerate the journey index in the host's `SPEC.md` (ask-first, always with a diff). The
    persona's value is **refusal**: it rejects "the user" for a named actor, unobservable
    outcomes, feature-list goals, and criticality inflation, and never invents a step.
  - **`/cuj-audit`** — the `cuj-auditor` persona (`agents/`) and `audit-cuj` skill (`skills/`)
    replay a stored journey and emit an `auditor: cuj` report naming the CUJ id and broken step.
    A passing journey is `total: 0`, and the report leads with
    `P/N journeys passed, S skipped, M of T steps verified` so a clean pass is never confused
    with a run that verified nothing.
  - **CUJ file contract** (`skills/spec-cuj/references/cuj-contract.md`) and its executable form
    `scripts/validate_cuj.py` — ten-key schema, `expect` as the load-bearing observable field,
    idempotent host `SPEC.md` index generation, and **no provenance/PII** (author, date, and
    revision are answered by git, and are rejected outright if present).
- **`audit-cuj` joins the `/ux-audit` roll-up** as a fourth, **conditional** auditor — native
  like usability, run only when `.ux/cujs/` is non-empty, and otherwise skipped with a recorded
  reason rather than counted as a pass.
- **`interview-me` as an optional, undeclared dependency** — `/ux-spec` uses
  [agent-skills](https://github.com/addyosmani/agent-skills)' `interview-me` when installed and
  falls back to its own question set (`references/interview-fallback.md`) with disclosure when
  it isn't. Unlike `web-quality-skills`, it is deliberately **not** in `plugin.json` — the
  capability degrades rather than fails.
- **`audit_safety.py` allowlist** — a keyword-only `allow` parameter with `audit` (unchanged,
  `.ux/audits/` only) and `authoring` (`.ux/audits/`, `.ux/cujs/`, `SPEC.md`) profiles, so CUJ
  authoring can write host docs without weakening the audit safety invariant.
- Test suites `tests/test_cuj_contract.py` (contract + index idempotency + no-PII) and expanded
  docs/eval coverage for the CUJ components.

## [0.2.0] - 2026-07-16

### Added
- **`AGENTS.md`** — how the repo is laid out and how to author new components: the
  three-layer composition rule (moved here from the README), frontmatter per layer, the
  end-to-end checklist for adding an auditor, and the authoring rules the tests enforce.
  `CLAUDE.md` symlinks to it.
- **`CONTRIBUTING.md`** — setup, what to work on, PR expectations, and the release process.
- README section on composing with [agent-skills](https://github.com/addyosmani/agent-skills):
  a report's prioritized-fixes queue feeds `/spec`, `/plan`, or `/build`, then a re-run
  confirms the severity dropped.
- Declared the `web-quality-skills@addy-web-quality-skills` dependency (which the roll-up
  wraps) in `plugin.json` and `marketplace.json`, and added the `$schema` reference to both.
- **Evals system** (`evals/`) — modelled on agent-skills' evals, using Sprout as the
  behavioral target. Tier 2 (trigger routing via stemmed TF-IDF over skill descriptions,
  schema + minimums + collision checks) runs deterministically in CI via
  `tests/test_evals.py`; Tier 3 (behavioral audits against Sprout, graded by
  `evals/run_evals.py --grade`) runs on demand. Replaces the ad-hoc dogfood prompt.
- **Suite roll-up** — `/ux-agent-skills:ux-audit` fans out to usability (native) plus
  accessibility and web performance (wrapped from
  [web-quality-skills](https://github.com/addyosmani/web-quality-skills)), normalizes every
  result into the shared `.ux/audits` contract, and writes a `rollup-<ts>.md` with a
  per-auditor table and a go/no-go verdict. Unavailable auditors are skipped and disclosed.
- **Usability Auditor** — the suite's first auditor: the `usability-auditor` persona
  (`agents/`), the `usability-audit` skill (`skills/`), and the `/usability-audit`
  command (`commands/`).
- Static, live (browser), and hybrid (auto-selecting) evaluation modes, with a
  render-vs-source honesty rule (static-mode runtime claims labeled
  `potential — unverified`).
- Four evaluation frameworks — Nielsen's 10, Shneiderman's 8, AI Design Heuristics, and
  NPCIS — with findings de-duplicated and attributed to a primary framework.
- **Shared `.ux/audits` report contract** every future suite auditor inherits: frontmatter
  schema, 0–4 severity rubric, body layout, rolling `index.md`, and coverage-honesty rule.
- `scripts/validate_report.py` (report + index + coverage validation, per-auditor
  framework vocabularies) and `scripts/audit_safety.py` (safety-invariant check).
- Test suites: contract, component-structure, safety/idempotency, and docs/link checks.
- Moved `nng-ux-heuristics.md` into the skill's `references/` so the skill is self-contained.

## [0.1.0] - 2026-07-15

### Added
- Bootstrap plugin scaffolding: `.claude-plugin/plugin.json` manifest and
  `.claude-plugin/marketplace.json` catalog.
- Component skeleton with placeholder docs: `agents/`, `skills/`, `commands/`.
- MIT `LICENSE`, `.gitignore`, and this changelog.
- `references/` seed material (NN/g heuristics, heuristic-evaluator persona spec).
