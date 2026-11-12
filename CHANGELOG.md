# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] - 2026-11-12

### Fixed
- **The safety baseline no longer lives at one fixed path in `/tmp`.** `audit-cuj` step 1
  said `--snapshot > /tmp/ux-baseline.json` and step 8 read that same name back: one
  filename in a world-writable directory, shared by every run on the machine.

  **It was a correctness bug in the check that enforces findings-only, not untidiness.**
  Two audits at once — two repos, or one repo in two worktrees — overwrite each other's
  baseline, and the footprint check then measures this repo against that one's tree. Both
  directions reproduce. A user's own uncommitted work gets reported as the agent's
  violation; and, far worse, when the other repo happened to have the same path dirty, an
  agent writing to **host application code** was reported as `safe`. The check had no
  symptom either way — it printed a confident verdict about the wrong tree.

  `scripts/audit_safety.py` now derives the path itself from the host repo: `--snapshot`
  saves it (and still prints the JSON, so `> file` plus `--baseline <path>` keeps working),
  and `--baseline auto` recomputes the same path to read it back. Neither step names a
  file, which is the point — a skill's steps are separate tool calls and shell state does
  not survive between them, so `$(mktemp)` would have been a regression rather than a fix.
  One file per repo, named by digest, in a per-user directory refused if it turns out to
  be a symlink — `mkdir(exist_ok=True)` is satisfied by a symlink to a directory, so a
  mode alone would be decoration. The directory is brought to `0o700` when it already
  exists rather than only when created (`mkdir(mode=...)` applies the mode on creation
  only, so one left by an earlier version, a permissive umask or a user's own `mkdir -p`
  kept it), and the baseline file is written `0o600` instead of inheriting the umask. Both
  matter because the baseline decides which dirty paths are forgiven: a baseline any local
  user can replace is one that can be planted to make an agent's edit to a host source
  file read as `safe`. `--baseline auto` with nothing saved exits 2 rather than quietly
  running unbaselined, which would restore the false positive the baseline exists to
  remove. There is also no `/tmp` on Windows.

  Nothing ties a baseline to the run that took it, so two further cases are handled
  explicitly. A **failed save deletes any leftover baseline** before warning: baselines
  are never cleaned up, so one from an earlier run of this repo is normally already there,
  and `auto` would otherwise read it and answer about the wrong point in time — the user's
  own uncommitted work reported as the agent's violation, or a real escape forgiven.
  Removing it makes the warning true, and `auto` exits 2. And **one audit at a time per
  path** is now stated rather than assumed: a second run against the same path overwrites
  the first's baseline and records its report as pre-existing dirt, so the first is told it
  wrote nothing. Separate worktrees remain the supported way to audit one project twice at
  once. Reading a baseline now prints which one and how old it is, so a stale read leaves a
  trace in the audit transcript even where it is not fatal.

  A new `check_no_hardcoded_temp_paths()` sweep keeps a fixed temp path out of every
  persona, skill, command and reference. A component is a prompt, so "use a unique temp
  path" would be improvised differently every run; the path has to be derived in the
  script or it is not derived at all.

## [0.7.0] - 2026-11-11

Reports are now ranked by **priority**, with NN/g severity retained per finding as the stated
input. One scored scale, not two: the reader of a findings-only report asks *what do I fix
first*, so the report answers that with one number and shows the reasoning underneath.

### Changed
- **`P0`-`P3` priority replaces `sev0`-`sev4` as the scored scale.** Finding headings are
  `### [PN] <title>`, `summary` carries `P0`-`P3`, and the index gains priority columns. P0
  blocks the task with no workaround; P1 needs fixing before release (a costly or non-obvious
  workaround, a silent failure, or a WCAG AA failure); P2 has an obvious workaround; P3 is
  cosmetic. A non-problem is omitted entirely, as before.
- **Severity survives as NN/g severity, reported per finding and never aggregated.** Each
  finding carries an `S1`-`S4` severity whose justification must name Nielsen's three
  derivation factors - frequency, impact, persistence. It is not a second badge, not an index
  column, and not summed: it exists so a reader can check the priority call and overrule it.
  Nielsen designed those ratings to be averaged across 3-5 evaluators, and a single auditor
  has no such smoothing - stating the factors is what keeps the citation honest.
- **Report contract schema 3.** `validate_report.py` dispatches on `schema`; **schema 2 keeps
  validating forever**, because a report records the contract it was born under and is never
  rewritten. Half-migrated reports are rejected in both directions - schema-2 summary keys
  under a `[PN]` body, and the reverse.
- **The roll-up's go/no-go verdict is gone, not renamed.** `rollup-*.md` now leads with the
  priority distribution (`1 x P0 - 4 x P1 - 7 x P2`) plus the highest-priority finding named,
  and states that it makes no ship call: that needs release context the suite does not have
  and SPEC 6 forbids it from inventing. Forcing a binary onto a borderline judgement was what
  made the old verdict misleading. Roll-up frontmatter replaces `verdict` with `priorities`
  and `auditors_skipped`; it sits outside the report contract, so this cost no schema bump.
- **An empty distribution is not automatically a pass.** With any auditor skipped, the
  dashboard warns rather than passing - `0 x P0` across one auditor of four says almost
  nothing about the product. Same discriminator the cuj reports already draw between a
  verified pass and a run that verified nothing.
- **A journey's `criticality` now floors priority instead of capping severity.** `medium` and
  `low` journeys cannot reach the top of the ladder, which is correct for urgency; capping
  *severity* had falsified an observation, recording a genuine catastrophe on a low-criticality
  journey as a 2. Severity is rated independently and never clamped.
- **The HTML companion renders both schemas.** P ranks ride the existing positional colour
  ramp, so a `P0` card is the hottest colour a `sev4` card was and the stylesheet is unchanged
  in substance; the banner classes `.nogo`/`.verdict`/`.go` became `.alert`/`.headline` (`.go`
  duplicated `.pass`), since a class named `nogo` cannot outlive the call it named.

### Added
- **`tests/test_charset.py`.** Fails on any foreign-script letter or invisible/format
  character in a tracked text file - homoglyphs, zero-width and non-breaking spaces, and the
  bidirectional overrides of Trojan Source (CVE-2021-42574). The product here is prose, so a
  stray character in `agents/*.md` ships as a defect; it globs `git ls-files` deliberately, and
  its own firing is self-checked. It found three pre-existing zero-width spaces, now removed.
- **Roll-up fixtures.** `_render_rollup()` had no test coverage at all, and it showed: with
  `verdict` absent it emitted a red alarm banner with an empty `<b></b>`. Two fixtures now
  cover the normal shape and the empty-with-skips hazard.

### Fixed
- **`check_rollup_skill()` asserted nothing about the verdict.** Its probe was
  `"roll-up" or "rollup" or "go/no-go" or "verdict"`, and the first two alternatives match the
  file's own subject matter - so it stayed green however the output changed, including when the
  verdict it guarded was deleted outright. Replaced with probes on the distribution, the named
  top finding, the no-ship-call statement, and the empty-is-not-a-pass rule.
- **The `cuj-auditor` passing-step rule read "severity 0 is never as a finding"** - broken
  grammar held in place by a test probe demanding that exact string. The prose is fixed and the
  probe now matches the substantive rule instead of a heading fragment.
- Component `description` fields still advertised "severity-scored" reports, and the
  "Running the checks" block in AGENTS.md was missing `test_cuj_contract.py`.

- **The HTML companion dropped every hard-wrapped bullet's continuation line.** The block
  renderer took lists one line at a time and stopped at the first line that did not start
  with a bullet - so a continuation fell *outside* the `<ul>` and rendered as a stray
  paragraph beneath it, reading as a separate claim, and nested sub-lists were flattened up
  to the parent's level. This repo hard-wraps prose at ~95 columns and the contract's own
  Appendix example nests, so it was the default shape, not an edge case: a live run against
  a host app had 45 of 61 bullets affected, breaking every Appendix and every roll-up
  Coverage section. Lists are now parsed as blocks, with an indent tree.
- **Three further gaps in the same renderer, all found by that run.** A link whose text
  carries brackets went unparsed - which is *the* shape schema 3 produces, since findings
  are headed `### [PN] <title>` and `## Prioritized fixes` is built from links to them, so
  that section rendered as raw Markdown. A `###` heading inside a blockquote emitted its
  hashes literally, which is what the roll-up skill's "quote the worst finding" instruction
  produces. And `*emphasis*` was never implemented (only `**bold**`), so single asterisks
  reached the page; the new rule declines to open a span on a lone asterisk, so `a * b * c`
  and a glob stay put.
- **The roll-up was unvalidated, and `rollup: true` was documented nowhere.** The key is
  the renderer's only discriminator, and omitting it is **silent**: the file still renders,
  as an ordinary report, minus the headline banner naming the highest-priority finding and
  warning about skipped auditors. The whole signal was a 26-byte difference in the output.
  No persona, skill, command or reference had ever named the key - it existed only in
  fixtures and in `render_report_html.py` - so an agent following `ux-audit/SKILL.md` could
  not have known to write it. The skill now specifies the full roll-up frontmatter, and
  `validate_report.py --rollup` checks it: the key, the `priorities` totals, the ran and
  skipped lists, the two required sections, and the absence of a reinstated `verdict`.
- **Step 7 told the auditor to "validate every report", which the roll-up cannot pass.** A
  roll-up carries no `auditor`, `mode`, `frameworks` or findings, so the bare validator
  answers with ten confident errors about missing keys. That was by design - the roll-up
  sits outside the report contract - but the instruction never said so, so the first thing
  a reader does produces a page of false failures. Step 7 now names the three modes.
- **The contract required `## Prioritized fixes` to link to each finding, and no fixture
  did.** Fixtures teach, so the one that teaches schema 3 now carries the links, with
  anchors that resolve to its own headings, and the contract spells out the line shape and
  where the anchor comes from.

### Known
- **`docs/images/audit-review.png` is a 0.6.1 capture.** It still shows the go/no-go banner and
  `sev`-badged cards. Re-capturing needs a live `/ux-audit` run against a host app; the README
  marks it as such until then.

## [0.6.1] - 2026-11-10

### Fixed
- **Two phantom components removed.** `agents/README.md` and `commands/README.md` were being
  discovered as a persona named "README" and a stray `/README` command — `agents/` and
  `commands/` are swept wholesale, so every `.md` in them is a component whether or not it has
  frontmatter — and both sat in the always-on token budget of every session. The three layer
  catalogs now live in `docs/` (`agents.md`, `commands.md`, `skills.md`); `skills/README.md` was
  never discovered and moved only to keep them together. A new globbing `check_discovery_dirs()`
  in `tests/test_components.py` fails if a non-component file reappears in either directory, and
  AGENTS.md step 8 now says to put catalogs in `docs/` rather than beside the components.
  Reported by the published-directory review as "no frontmatter block"; recorded as a known,
  unfixed repo-structure decision since 0.3.0.

### Added
- **A plugin icon.** `icon.svg` at the plugin root (inline SVG, no external references),
  referenced as `"icon": "./icon.svg"` from `.claude-plugin/plugin.json`.

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
