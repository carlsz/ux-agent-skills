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
- **The report page now opens with a brief that stands on its own.** The companion used to
  render the Markdown in the Markdown's own order, which is a faithful transform and a poor
  document: the counts, the verdict and the score each appeared two or three times on one
  screen. The top of every page is now a single shareable summary — a lockup (the roll-up's
  `GO`/`NO-GO`, or for one auditor the worst priority it found and the action that priority
  prescribes), the health score as a dial with the band beside it, the executive summary as
  its prose, and the non-zero counts as chips. **An auditor report never shows a go/no-go**:
  that gate is the suite's, derived across auditors, and one auditor must not appear to
  issue it.
- **A permanent apparatus rail on every finding.** The framework citation, the source
  location and the grading rationale get their own 204px column beside the prose, so the
  apparatus is prominent by *position* rather than by colour — which is what lets it stay at
  full strength without shouting over the finding it supports. An `Evidence` field carrying
  both a screenshot and a `file:line` is split: the citation stays in the rail, the
  screenshot renders beside the prose. Below 700px the rail becomes a band above it.
- **Zeros are suppressed rather than dimmed.** Four cells reading `0` crowd out the one
  reading `2`. The brief shows only the levels actually found; the index, which cannot drop
  a column, dims its zero cells instead.
- **A binary scorecard item reads `pass` / `fail`.** A WCAG criterion and a journey step
  are pass/fail, not a grade, and one filled dot out of one was a weak way to say so — and
  left the state encoded in colour alone.
- **The brief absorbs `## Executive summary` as well as `## Design health`.** Same rule as
  before, extended: the HTML builds both from frontmatter and the body skips them, so one
  screen never states the same numbers twice. The Markdown still carries both in full — it
  has a different reader.
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

### Fixed
- **The health score was anti-correlated with severity, and the index made it plain.** The
  scorecard and the findings list were two independent judgments of one app, so they could
  disagree — and did, in both directions at once. A `cuj` run whose only finding was a `P3`
  scored four journey steps `0` and published **43% · Poor**, while an accessibility run
  carrying two `P0`s published **70% · Good**: the auditor that found a single word of
  divergent copy scored worst, the one that found blocking defects scored best. A reader
  trusting the dial drew the opposite of the truth. **An item's `score` is now derived —
  it is the P-number of the worst finding filed against it** (`4` when none is), bridged by
  the *Framework Violation* field every finding already carries, which names the heuristic,
  criterion or step the item stands for. One observation, graded once. `validate_report.py`
  enforces both halves: the lowest item score must equal the worst priority in `summary`, so
  a report cannot file a `P0` and show a flawless scorecard, nor sink below what it found.
  On the same three reports the scores become 86% / 50% / 79% — the cosmetic run now reads
  best rather than worst. **Known limit:** the number is still diluted by rubric size, so a
  22-criterion accessibility run and a 10-heuristic usability run are not yet comparable to
  each other; within a report the score is now a strict function of the findings.
- **One 0–4 scale for every auditor.** `of` was per-item, so a binary rubric could mark a
  step `0/1` — the worst available mark — for a divergence the same run graded `P3`, the
  least severe. Every item is `of: 4` now, whatever the idiom: the *items* stay each
  auditor's own (Nielsen heuristic, WCAG criterion, journey step, metric), the *scale* is
  shared, which is what the percentage needs to mean anything. A pass/fail rubric still
  grades 0–4 here, because the item records how badly the criterion failed, not whether it
  normatively conforms.
- **A report written before schema 3 rendered as having no findings at all.** Its findings
  are tagged `[sev4]`..`[sev1]` and its counts keyed `sevN:`; the renderer read neither, so
  every report the suite produced before the migration published the words *"No findings"*
  over a full document, with an empty brief above it. Both are translated on read now
  (`sev4 → P0` …), joining the `Severity:` field name, `totals:` and `report: rollup` on the
  read-tolerant side of the line the validator keeps write-strict.
- **The roll-up dashboard reported `0 ran` however much of the suite had run.** It read
  `auditors_run`, a spelling that appears nowhere in the contract, the validator or any
  fixture — the key is `auditors_ran`.
- **A hard-wrapped list item rendered as several.** These reports wrap at ~95 columns, so
  most list items span two or three source lines; treating each line as its own item split
  one list into several, each restarting at `1.`, with the wrapped remainder stranded as a
  paragraph between them. Continuation lines now fold into the item they belong to.
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

The five below were found by running the suite against a real app — three auditors reading
only these instructions, with no knowledge of what the migration intended. Every one of them
produced valid-looking output, and the test suite was green over all five.

- **A contract-valid report could render as findings with entirely empty bodies.** §5
  introduces the five labelled fields as a markdown bullet list, which reads both as "these
  are the fields" and as "this is the markup" — and real auditors split on it: given the same
  §5, the `cuj` run bulleted its fields while the `usability` and `accessibility` runs wrote
  bare `**Field:**` paragraphs. §7's field check is a substring test, so bare bold *validates*;
  the HTML companion's field pattern required the bullet, so every field of such a finding was
  dropped — no prose, no apparatus rail, no evidence, no recommended fix — under a correct
  title and priority chip. Fifteen of this run's sixteen findings were affected. The renderer
  reads both forms now (reports are append-only history), and §5 states the canonical one.
- **The roll-up skill told agents to write a roll-up its own validator rejects.** Step 6 says
  to copy its YAML template "exactly", and that template still read `schema: 2` after the
  migration took the validator and the contract to `3`. The validator's required version is
  now a named `SCHEMA` constant, and `test_components.py` parses the template out of the skill
  and compares it against that constant and `ROLLUP_REQUIRED_KEYS`, so the two cannot drift.
- **A third instruction file still graded on the 0–4 numbers — and no grep could have found
  it.** `audit-cuj/SKILL.md` step 6 said a `success_criteria` failure "grades **3, not 2**".
  The sentence names no scale, so it survived both the `sev[0-4]` sweep and the `0–4` sweep
  that caught its siblings, while under `P0`–`P3` it reads exactly backwards — `P3` is the
  least severe grade. Bare-number grades are now banned outright rather than translated case
  by case, because the defect is that the reader cannot tell which scale is meant.
- **§4's tie-breakers contradicted each other, and all three auditors hit it.** Rule 3 raises
  anything touching a journey in `.ux/cujs/` by one level, and "the higher priority wins"
  resolved the clash in favour of the absurd reading: the accessibility run graded two AA
  contrast failures `P0` — "Prevents the task entirely" — for text that is merely hard to
  read, and the usability run admitted lowering its *base* grade until the raise landed
  somewhere defensible, which is the drift these rules exist to stop. Rule 2 is now a ceiling
  as well as a floor (`P0` requires impossibility), and rule 3 is scoped to the auditors that
  are not `cuj` — whose findings are *all* about a journey by construction, so the rule fired
  on every one of them and double-counted the weighting the `criticality` clamp already
  applies.
- **`validate_report.py .ux/audits/*.md` reported a valid index as `INVALID`.** That glob is
  how the skills tell an agent to validate a run, and it necessarily sweeps up `index.md` —
  a table with no frontmatter by design (§7) — which then failed as a malformed report. The
  CLI dispatches on the name now, so the documented command exits 0 on a good run.
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
