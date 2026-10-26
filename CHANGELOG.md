# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Severity `sev4`–`sev1` is now priority `P0`–`P3`, everywhere — report contract
  `schema: 3`.** The old scale said how bad a finding was; the new one says **what to do
  about it**: `P0` Blocking (fix immediately), `P1` Major (fix before release), `P2` Minor
  (fix in the next pass), `P3` Polish (fix if time allows). The migration is
  `sev4 → P0 … sev1 → P3`, and it touches the frontmatter keys, the `### [PN]` finding
  tags and their anchors, the `index.md` columns, the roll-up gate, both auditor personas,
  four skills, the commands and the eval cases. Reports already written at `schema: 1` or
  `2` keep their `sevN` vocabulary — `schema` records the contract a report was born
  under, and rewriting it would falsify a historical record.
- **The scale now carries tie-breakers, so a re-run lands in the same place.** A judgment
  scale drifts: *if a user would contact support about it, it is at least `P1`*; no
  workaround at all is `P0`, not merely difficult; a defect on a journey in `.ux/cujs/`
  rises a level; something only visible by reading source is at most `P2`. Where two rules
  disagree the higher priority wins and the Priority field names the rule that decided it.
- **The `criticality` clamp inverted with the scale, and that is the dangerous part of this
  migration.** Under 0–4 it was a ceiling (`medium → max 3`); under `P0`–`P3` the worst
  value is the *lowest* number, so the same rule is now a floor (`medium → never P0`). A
  component that still says "max" has carried the old direction across and will clamp
  backwards — silently, and only on the journeys that matter least. `test_components.py`
  now asserts the floor wording specifically.
- **The old `sev0` invariant inverted too.** The scale used to have no zero, so a `[sev0]`
  heading was the error; it now *starts* at zero. `tests/fixtures/invalid/sev0-present.md`
  is replaced by two fixtures that catch what can actually go wrong now: a tag above the
  top (`[P4]`) and frontmatter still counting on the superseded scale.
- **`index.md` gains a `Health` column**, so the index carries the trend the roll-up reads.
  A report with no scorecard writes an em dash.

### Added
- **The `health` scorecard (contract §4.1) — every auditor, in its own idiom.** A findings
  list is silent about everything that works, so a clean audit had nothing to show and the
  suite looked best when the app was broken. Each report now grades its own framework into
  `health`: `score`, `max`, `pct`, `band` (Excellent / Good / Acceptable / Poor / Critical)
  and one `items` row per graded item. **`of` is what lets one block serve four auditors
  without pretending they share a scale** — Nielsen grades 0–4, a WCAG criterion 0–1, a
  journey step 0–1 — while the percentage stays comparable across all of them.
- **The scorecard's headline is derived and validated against its own rows.** `score`,
  `max`, `pct` and `band` are all recomputed from `items`; a hand-written number that
  cannot be reconciled with what it is made of is rejected. Same discipline as the derived
  go/no-go verdict.
- **A weak or n/a item must carry a `note`.** An unexplained 2/4 is an assertion, not a
  finding — the same rule that makes a skipped auditor state its reason.
- **`band: Unscored` for a run with nothing gradable.** A static or all-skipped CUJ run has
  no item it can grade, and both obvious defaults lie: `0%` reads as catastrophic, `100%`
  as a clean pass. It now says so explicitly, and the roll-up can refuse to average it in.
- **A suite scorecard on the roll-up** — the mean of its members, each member's band, and a
  `trend` of prior runs. `trend` holds **prior** runs only and **must degrade to `[]`**: an
  authenticated run is advised to gitignore `.ux/audits/` wholesale, so in those repos
  there is no history to read and the trend cannot be load-bearing.
- **The HTML renders the scorecard from frontmatter and skips the body's `## Design health`
  section.** The Markdown keeps the table for its own readers; printing the same numbers
  twice in one view is the duplication the contract now rules out.
- **Priority badges that pass WCAG contrast.** The old ramp put white text on `#ef4444`
  (3.76:1) and `#f97316` (2.80:1) — the two badges meaning *this is serious* were the two
  that failed, on an accessibility auditing tool. The `P0`–`P3` ramp clears 4.5:1
  throughout.

### Fixed
- **Every finding card had lost its Priority row — and not to a blank.** The HTML
  renderer's field pattern still listed the schema-2 name `Severity` and not `Priority`,
  and a field name absent from that pattern is absent from its lookahead too, so the
  priority line was swallowed into `Framework Violation`'s value: the rationale for the
  tag disappeared while the card count, the only thing `test_render_html.py` asserted,
  stayed correct. Both names are now matched (`Severity` for append-only history) and the
  row is titled by what the scale is today. Tests assert each of the five fields reaches
  its own row, and that none of them absorbs the next.
- **Two instruction files still mapped onto the 0–4 numbers, which inverts under `P0`–`P3`.**
  `audit-cuj/SKILL.md` graded "4 blocked / 3 workaround / … / 0 match" and clamped with
  `medium max 3` — the ceiling direction this migration reverses, in the one file the
  auditor actually follows; the cuj-auditor *persona* had been migrated and the skill had
  not, and no check covered it. `ux-audit/SKILL.md` normalized wrapped tools under the
  heading "map each tool's severity onto the `P0`-`P3` scale" while its targets stayed bare
  numbers, so "blocker → 3–4" read as `P3`–`P2`: the most serious findings in the suite
  filed as polish. `test_components.py` now asserts the floor wording on the skill as well
  as the persona, and that the normalization map names its targets as tags.
- **The suite roll-up dashboard, which had never rendered.** `render_report_html.py`
  dispatched on a `rollup` frontmatter key that no roll-up ever wrote, so every roll-up fell
  through to the generic auditor-report path. One missed branch produced four visible
  symptoms: the go/no-go banner was absent (its CSS had never been exercised), the lead
  verdict paragraph was dropped entirely (the generic path emits only `## ` sections), the
  eyebrow and browser title read "report audit", and the header announced **`0 findings`**
  above a table totalling five — because the generic severity bar reads `summary.total`, a
  key the roll-up did not carry. Dispatch now goes through a shared
  `is_rollup()` in [`validate_report.py`](scripts/validate_report.py).
- **A second bug that would have survived fixing the first.** The verdict test was
  `verdict.lower() == "go"`, but every real roll-up wrote the token and its justification as
  one string — `verdict: "GO — all 3 journeys pass"`. That equals neither verdict, so every
  passing run would have rendered as a **red NO-GO** the moment the dashboard came back.
  The renderer now splits the leading token, and the contract moves the prose into
  `verdict_reason`.
- **A severity bar of zeros over a document listing issues.** The bar now derives `total`
  from the per-severity counts when absent, reads the legacy `totals:` spelling, and renders
  **nothing at all** when a report carries no counts — a row of zeros is not a neutral
  default, it asserts "nothing found".

### Added
- **Roll-up frontmatter is now specified** — [report contract](skills/usability-audit/references/report-contract.md)
  §9, the schema's second document type. It was unspecified until now, and the agent
  improvised it per run: five consecutive runs of the same app produced three different
  discriminators (`kind:`, `report:`, none), three different count keys (`summary:`,
  `totals:`, none), and verdict strings that mixed the token with its prose. `kind: rollup`
  is the spelling; the other two are **read** so append-only history keeps rendering, and
  **rejected on write** so the drift cannot re-accumulate.
- **The go/no-go verdict is derived, not judged:** `NO-GO` if `sev4 > 0` or `sev3 > 0`, else
  `GO`. `validate_report.py` recomputes it from the merged counts and fails a mismatch. The
  gate previously lived in prose — *"any auditor reports a sev3 blocker"* — leaving the
  auditor to decide what counted as a blocker; two runs reached **opposite verdicts from
  identical counts**, and a third invented "GO with required fixes" as a third value.
- **`validate_rollup()`** — roll-ups validate through their own path instead of being
  rejected for the `auditor`, `mode`, and `frameworks` keys they correctly lack. Every
  entry in `auditors_skipped` must carry a `reason`, making the suite's "a skipped auditor
  never reads as a clean pass" rule structural rather than advisory.
- **A contested verdict renders amber.** A roll-up predating the derived gate can state a
  verdict its own counts do not support — a `GO` over a `sev3`. The renderer does not
  overrule the document (it is an append-only record of what that run concluded), but it no
  longer presents the claim as settled: the banner turns amber, names the verdict the counts
  derive, and says the roll-up stated rather than derived its verdict. Green is reserved for
  a `GO` the numbers agree with.
- **Six roll-up fixtures and the tests that use them** — the dashboard had no fixture in
  `tests/test_render_html.py`, which is why a dead code path stayed green. Coverage now
  includes the read-tolerant/write-strict asymmetry and the legacy prose verdict.

## [0.6.0] - 2026-08-24

### Added
- **Authenticated audits — the auth handoff.** Auditors can now reach screens behind a login
  wall. The auditor observes the wall, asks once, **you sign in yourself** in the browser it
  is driving, and it re-observes to confirm the session before resuming. The agent never
  types, reads, or stores a credential, so the *"never enter credentials"* boundary is
  preserved verbatim rather than carved out. Declining still produces an honest skip; a
  headless run records `handoff unavailable — no attended browser surface`, which is **not**
  a decline (nobody was asked). New shared reference
  `skills/usability-audit/references/auth-handoff.md`, cited by `usability-audit`,
  `audit-cuj`, and `ux-audit` — no new component, no schema change.
- **A vendor-neutral capability test** for what may satisfy the handoff: (a) the secret never
  enters agent context, and (b) the session lands in a context isolated from the user's daily
  profile. Clause (b) is the discriminating one — it is why agent-mediated password-manager
  autofill is rejected (it exists to drive the user's *real* browser), and it is written as a
  test so future mechanisms are measured rather than relitigated.
- **`audit_safety.writes_under()`** — observes the run's own writes under a prefix even when
  that prefix is gitignored, so the safety invariant cannot be satisfied by a run that wrote
  nothing. Pathspec-scoped by design: a repo-wide `--ignored` scan would read every
  `node_modules/` as an escape and fail every audit. **Wired into the CLI**, which is the
  only form auditors invoke: `audit_safety.py <repo>` now exits **1** when nothing escaped
  but nothing was written either, and prints the observed writes when it passes.
  `--allow-no-writes` opts out for a run genuinely expected to write nothing.
- **`changes_confined_to()` now catches an escape hidden behind an ignore rule.** A host
  that gitignores `.ux/` wholesale — which the artifact posture nudges authenticated runs
  toward — also hid `.ux/cujs/`, so an auditor writing there (the mechanical form of "never
  repair the journey you are grading") passed silently. A second, pathspec-scoped pass over
  every profile's paths makes an ignored `.ux/cujs/` behave exactly like a non-ignored one.
  Deliberately *not* a repo-wide `--ignored` scan, which would read every `node_modules/` as
  an escape; the residual gap (ignored paths no profile names) is documented rather than
  implied away.
- Both halves of the invariant now take the same content-addressed `baseline`, and
  `snapshot()` sweeps the profile's write prefixes with `writes_under()`. Under an ignored
  `.ux/audits/`, prior runs' reports never leave the working tree — without this they would
  answer "were writes observed?" for every later run.
- **Roll-up auth pre-flight** — `/ux-audit` runs the handoff **once, before the fan-out**, so
  a multi-auditor run interrupts you a single time instead of once per auditor.

### Changed
- **The artifact posture for authenticated runs.** Behind a login wall the *capture* is the
  leak, not the credential: screenshots carry the account's name and email, and reports quote
  real records. An authenticated run now recommends gitignoring `.ux/audits/` **wholesale**
  (the HTML companion base64-embeds images, so ignoring `assets/` alone does nothing) and
  warns when `.ux/audits/` is already tracked, since an ignore rule does not untrack files.
  Reports describe user data structurally and **never record which account was used** — the
  `author:` precedent from §9.7.
- **A gated screen reached via the handoff is no longer a coverage gap.** The report contract's
  Appendix gains an `Access:` line recording the *rung*, and lists only screens that stayed
  unreached under *Coverage / not inspected*.
- SPEC §5.2's safety invariant now requires **both** halves — nothing escaped **and** writes
  were observed — so an empty change set can no longer satisfy it. Every skill's exit
  criteria were swept off the old *"`git status` shows changes only under `.ux/audits/`"*
  phrasing, which is trivially true once that directory is ignored.
- `audit_safety.py` parses `git status` and `git ls-files` with `-z`. The two commands
  C-quote *different* subsets of awkward paths, so the newline forms spelled one file two
  ways — and the escaped spelling matches nothing on disk, so `_digest()` read it as absent
  and the baseline forgave it silently.
- **The `/ux-audit` auth pre-flight is skipped for runs that never open a browser** — a
  repo-path target or `--mode static` has no page to probe and is not owed a dev server.
- **`audit-cuj` asks once per *wall*, not once per run.** The pre-flight only probes
  `entry_point`s, so a journey that starts public and authenticates partway through
  (catalogue → checkout) shows it nothing. Reaching that wall at L3 now runs the handoff
  instead of recording a decline the user never made.

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
