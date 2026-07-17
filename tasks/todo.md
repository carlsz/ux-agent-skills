# TODO — Usability Auditor

Task list for [`plan.md`](./plan.md). Tasks are grouped by vertical slice. Each delivers
a runnable path; complete them top-to-bottom. `[ ]` = todo, `[~]` = in progress,
`[x]` = done.

Legend — every task carries **Files**, **Acceptance**, **Verify**, **Deps**.

---

## Phase 1 — Walking skeleton (static, Nielsen-only) ⭐

### T1.1 — Define the shared report contract
- [x] Author the `.ux/audits` report contract as a reference doc in this repo.
- **Files:** `skills/usability-audit/references/report-contract.md` (frontmatter schema
  §3.4, report body layout §3.3, `index.md` row format, severity rubric §4).
- **Acceptance:** doc specifies every frontmatter key, the `usability-<YYYYMMDD-HHMMSS>.md`
  naming, the `index.md` table columns, and the 0–4 rubric with "omit sev 0" rule.
- **Verify:** a sample report hand-written against it parses as YAML and reads cleanly.
- **Deps:** none (foundational).

### T1.2 — Minimal persona
- [x] Create the usability-auditor persona (Nielsen scope for now), with the
  render-vs-source honesty rule and findings-only boundary stated explicitly.
- **Files:** `agents/usability-auditor.md` — YAML frontmatter (`name`, `description` with
  trigger phrases: "usability audit", "heuristic evaluation", "UX audit"); role; output
  format = Severity Report (§3.3); rules incl. never-edit-host-code + honesty labeling.
- **Acceptance:** matches ecosystem persona conventions; points to references rather than
  inlining heuristics; states the 0–4 output format.
- **Verify:** frontmatter parses; persona resolvable as a subagent; boundary + honesty
  rule present.
- **Deps:** T1.1.

### T1.3 — Skill: static evaluation path
- [x] Author the skill workflow for static mode: locate host UI source → apply Nielsen's
  10 → produce evidence-backed findings (`file:line`) → write report to `.ux/audits/`.
  Runtime-perception heuristics labeled `potential — unverified` in static mode.
- **Files:** `skills/usability-audit/SKILL.md` (frontmatter + numbered steps + explicit
  exit criteria); reuse `skills/usability-audit/references/nng-ux-heuristics.md`.
- **Acceptance:** creates `.ux/` + `.ux/audits/` if absent; writes a timestamped report;
  every finding has evidence + Nielsen citation + fix + severity; honesty labeling applied.
- **Verify:** dry-run against a small sample component set produces a contract-valid
  report; no files written outside `.ux/audits/`.
- **Deps:** T1.1, T1.2.

### T1.4 — Command wiring
- [x] Thin command that parses `target`/`--scope`/`--mode` and invokes persona + skill.
- **Files:** `commands/usability-audit.md`.
- **Acceptance:** `/ux-agent-skills:usability-audit <path>` triggers a static audit end to
  end; args honored; `--mode live` deferred to Phase 2 (documented as not-yet-supported).
- **Verify:** invoke against a sample repo path → valid report appears in `.ux/audits/`.
- **Deps:** T1.2, T1.3.

> ### ✅ CHECKPOINT A — human review
> Review one real generated report + the contract. Confirm format, severity calibration,
> tone, and honesty labeling BEFORE building breadth. Stop here for sign-off.

---

## Phase 2 — Live & hybrid evidence

### T2.1 — Live browser inspection path
- [x] Add live-mode evidence gathering via browser MCP: navigate target URL, screenshot
  key states, exercise flows, read a11y/DOM tree. Save images to `.ux/audits/assets/`.
- **Files:** `skills/usability-audit/SKILL.md` (live steps); persona note on live evidence.
- **Acceptance:** live findings are *verified* (not `potential`); screenshots referenced
  by relative path; ask-first before starting a server or navigating.
- **Verify:** run against a running sample app → report cites screenshots; runtime
  heuristics marked verified.
- **Deps:** Phase 1 complete (Checkpoint A passed).

### T2.2 — Hybrid auto-mode selection
- [x] Implement auto mode: prefer live when URL/dev-server present, fall back to static;
  use static to locate `file:line` for live findings' fixes. Record actual `mode`.
- **Files:** `skills/usability-audit/SKILL.md`; `commands/usability-audit.md` (`--mode`
  now fully supported).
- **Acceptance:** frontmatter `mode` reflects reality (`live`/`static`/`hybrid`); coverage
  gaps (auth-gated, unreachable) logged in appendix, never silent.
- **Verify:** three runs — URL only, path only, both — each records correct mode + honest
  coverage.
- **Deps:** T2.1.

---

## Phase 3 — Full four-framework stack

### T3.1 — Author remaining framework references
- [x] Write skill-local references for the other three frameworks.
- **Files:** `skills/usability-audit/references/shneiderman-8.md`,
  `ai-design-heuristics.md`, `npcis.md` (derived from the UX-Heuristic-Bot persona spec).
- **Acceptance:** each lists its rules/dimensions with a one-line evaluation lens, citable
  by name in findings.
- **Verify:** references load; entries are specific enough to attribute a finding to.
- **Deps:** Phase 1 (format locked).

### T3.2 — Expand persona + skill to all four frameworks
- [x] Wire the persona knowledge base and skill evaluation to apply Nielsen +
  Shneiderman + AI heuristics + NPCIS, each finding mapped to its exact citation.
- **Files:** `agents/usability-auditor.md`, `skills/usability-audit/SKILL.md`.
- **Acceptance:** a report can cite any of the four frameworks; `frameworks` frontmatter
  lists all applied.
- **Verify:** full-stack run produces findings attributed across ≥2 frameworks with
  correct citations.
- **Deps:** T3.1.

> ### ✅ CHECKPOINT B — human review
> Review a full-stack live report for finding quality, citation accuracy, and
> false-positive rate. Tune before hardening.

---

## Phase 4 — Contract hardening & suite portability

### T4.1 — Rolling index
- [x] Append one row per run to `.ux/audits/index.md`; create it if absent; never rewrite
  prior rows.
- **Files:** `skills/usability-audit/SKILL.md`.
- **Acceptance:** two consecutive runs yield two index rows + two report files.
- **Verify:** run twice → index has both, older report untouched.
- **Deps:** Phase 2.

### T4.2 — Schema validation & coverage honesty
- [x] Skill self-checks generated frontmatter (required keys present; `summary` counts ==
  findings by severity) and always writes the coverage/appendix section.
- **Files:** `skills/usability-audit/SKILL.md`; `references/report-contract.md`
  (validation rules).
- **Acceptance:** a miscount or missing key is caught before the report is finalized;
  what-was-not-inspected is always listed.
- **Verify:** intentionally skip a route → appendix names it; counts always reconcile.
- **Deps:** T4.1.

### T4.3 — Safety invariant + idempotency test
- [x] Document and exercise: post-run `git status` shows changes only under
  `.ux/audits/`; reruns never overwrite/delete prior reports.
- **Files:** `skills/usability-audit/SKILL.md` (exit criteria); optional
  `tasks/` verification note.
- **Acceptance:** any write outside `.ux/audits/` is a hard failure.
- **Verify:** run in a clean host repo → `git status` scoped to `.ux/audits/` only.
- **Deps:** T4.1.

### T4.4 — Contract portability (mock second auditor)
- [x] Produce a mock `auditor: accessibility` report using the same schema; confirm it
  validates and coexists in `index.md` unchanged.
- **Files:** throwaway sample under scratch (not committed) or a fixture note.
- **Acceptance:** the contract needs no changes to host a different auditor.
- **Verify:** mock report validates against `report-contract.md`; shares one `index.md`.
- **Deps:** T4.2.

---

## Phase 5 — Docs & release

### T5.1 — README + CHANGELOG
- [x] Document the usability auditor and the shared report contract; add a CHANGELOG entry.
- **Files:** `README.md`, `CHANGELOG.md`.
- **Acceptance:** README explains invocation, modes, `.ux/audits` output, and the
  suite-wide contract; CHANGELOG under `[Unreleased]`.
- **Verify:** links resolve; a new user can run the auditor from the README alone.
- **Deps:** Phases 1–4.

### T5.2 — Validate & dogfood
- [x] Run `claude plugin validate .` (if available) and a real dogfood audit against a
  sample flow; confirm findings are genuinely actionable.
- **Files:** none (verification run); capture notes.
- **Acceptance:** plugin validates; dogfood report meets SPEC §7 DoD.
- **Verify:** manual review — findings are true positives worth fixing.
- **Deps:** T5.1.

> ### ✅ CHECKPOINT C — go/no-go
> Dogfood report is useful, DoD (SPEC §7) satisfied, safety invariant holds. Ship or iterate.

---

## Definition of Done (SPEC §7)
- [x] Triad wired per composition rule.
- [x] Four frameworks + 0–4 rubric applied.
- [x] Live end-to-end + static fallback both work. *(live/hybrid dogfooded against a
      running sprout at localhost:3117 — drove add/edit/complete/delete, verified 4
      findings + resolved 1 previously-unverified; static + four-framework also
      dogfooded.)*
- [x] Reports validate against the shared contract; `index.md` appends.
- [x] Post-run `git status` scoped to `.ux/audits/` only.
- [x] Every finding: framework citation + 0–4 severity + evidence + fix.
- [x] README/CHANGELOG updated.

---

## Phase 6 — Suite roll-up (post-plan, user-directed)

Fan-out meta-command (SPEC §8), standardizing on wrapping `web-quality-skills` for the
non-native auditors.

### T6.1 — Roll-up skill + command
- [x] `skills/ux-audit/SKILL.md` — fan out to usability (native) + accessibility +
      web-performance (wrapping `web-quality-skills`), normalize each into the shared
      contract, append the index, write `rollup-<ts>.md` with a go/no-go verdict; skip
      unavailable auditors with disclosure.
- [x] `commands/ux-audit.md` — `/ux-agent-skills:ux-audit` (namespaced to avoid collision).
- **Verify:** `check_rollup_skill()` + `check_rollup_command()` in test_components.

### T6.2 — Docs
- [x] README + CHANGELOG document the roll-up and the web-quality-skills wrap.

### T6.3 — Dogfood the roll-up (optional)
- [ ] Run `/ux-agent-skills:ux-audit` against sprout, invoking the wrapped
      web-quality-skills auditors end-to-end.

---

# TODO — Critical User Journeys (CUJs)

Task list for [`plan.md`](./plan.md) §9–16, implementing [`SPEC.md` §9](../SPEC.md). Same
conventions as above: `[ ]` todo, `[~]` in progress, `[x]` done; every task carries
**Files**, **Acceptance**, **Verify**, **Deps**.

> **Two rules that govern the commit boundaries** (AGENTS.md §"The two test traps"):
> **(1)** A `skills/*/SKILL.md` without `evals/cases/<name>.json` reds CI **immediately** —
> they land in the **same commit**. **(2)** `test_components.py` and `DOC_FILES` are
> hardcoded and fail **silent** — a component's `check_*()` and doc path are acceptance
> criteria of the task that creates it, never a follow-up.

### T0 — Spec (was PS)
- [x] SPEC.md §6 ask-first line (host `SPEC.md` writes) + new §9 (CUJ design spec).
- **Verify:** all five suites green; approved by the user 2026-07-16.

---

## Phase 7 — Foundations (contract, registration, safety)

T7.1–7.3, T7.4, and T7.5 are **three mutually independent tracks**. Each lands green alone
and can be reviewed as its own PR.

### T7.1 — CUJ file contract doc
- [x] Author the `.ux/cujs` file contract as a reference doc, owned by `spec-cuj`.
- **Files:** `skills/spec-cuj/references/cuj-contract.md`; add it to `DOC_FILES` in
  `tests/test_docs.py`.
- **Acceptance:** specifies every frontmatter key per SPEC §9.2; the `^CUJ-\d{3}$` /
  `^[a-z0-9-]+$` patterns; the `<id>-<slug>.md` filename rule; body layout (`## Narrative`,
  `## Out of scope`); the **observable-`expect`** rule; the **no-author** rule; and names
  `scripts/validate_cuj.py` as its executable form, mirroring `report-contract.md:12-14`.
  States explicitly that the body does **not** restate the steps, and why.
- **Verify:** a hand-written sample CUJ parses as YAML and satisfies every stated rule;
  `python3 tests/test_docs.py` green. **Host paths (`.ux/cujs/…`) appear only in backticks
  or fenced blocks — never as markdown links**, which resolve against the plugin repo.
- **Deps:** T0.
- **Note:** creates `skills/spec-cuj/` **without** a `SKILL.md` — safe, since `test_evals.py`
  globs `skills/*/SKILL.md`, so no eval case is owed until T8.2.

### T7.2 — `validate_cuj.py`
- [x] Implement the executable form of the contract + the index generator.
- **Files:** `scripts/validate_cuj.py`.
- **Acceptance:** mirrors `validate_report.py` conventions (`validate()` → list of
  violations, `[]` = valid; `main()` → 0/1/2). Exposes `validate(path)`,
  `validate_dir(dir)`, `render_index(dir)`; CLI `<file>… | --dir | --index`.
  Per-file: the ten required keys, `schema == 1`, `id` pattern, `criticality` vocabulary,
  non-empty `preconditions`/`steps`/`success_criteria`, each step a mapping with
  non-empty `n`/`action`/`expect`, `n` contiguous 1..N, body has both headings.
  **Rejects `author`/`authored`/`by`/`email`** (SPEC §9.7) — deleting the field from the
  schema is not the guarantee. Cross-file: **duplicate `id`**, and a filename whose id
  disagrees with frontmatter (the slug can no longer disagree — the filename carries it).
- **Verify:** `--index` over the same directory twice is **byte-identical**; run against the
  T7.1 sample → clean.
- **Deps:** T7.1.

### T7.3 — CUJ fixtures + `test_cuj_contract.py`
- [x] Mirror `test_report_contract.py` beat for beat.
- **Files:** `tests/test_cuj_contract.py`; `tests/fixtures/cujs/valid/{CUJ-001-add-a-task.md,
  CUJ-002-complete-a-task.md}`; `tests/fixtures/cujs/invalid/` — blank `expect`, bad
  `criticality`, empty `steps`, non-contiguous `n`, filename/frontmatter id mismatch,
  **a stray top-level `author`**, plus a `dupes/` pair sharing an id.
- **Acceptance:** every invalid fixture fails **for the right reason** (needle substring, as
  `test_report_contract.py:58-71` does). Two index assertions: `render_index` twice is
  byte-identical; rows sorted by `id` with the correct columns.
- **Verify:** `python3 tests/test_cuj_contract.py` green — auto-discovered by CI
  (`.github/workflows/tests.yml:24-27`), no wiring needed.
- **Deps:** T7.2.

### T7.4 — Register the `cuj` auditor in the report contract
- [x] Add `cuj` to the shared contract's known auditors, **with fixtures** — an unregistered
  auditor passes silently (`validate_report.py:93-103`), so registration without a fixture
  is untested.
- **Files:** `scripts/validate_report.py:30-34` (`"cuj": {"cuj-contract", "task-completion",
  "success-criteria"}`); `tests/fixtures/valid/cuj-20260716-120000.md` (one sev3, `mode:
  live`, all three frameworks, Framework Violation naming `CUJ-001` step 2);
  `tests/fixtures/valid/cuj-20260716-130000.md` (**`total: 0` clean pass**);
  `tests/fixtures/invalid/cuj-bad-framework.md` (`frameworks: [nielsen-10]`);
  `tests/test_report_contract.py`.
- **Acceptance:** both valid fixtures validate; the bad-framework fixture is rejected
  (needle `unknown to auditor`); check count `(8 checks)` → `(11 checks)` at `:78`. No
  schema, body, or index changes — the contract is auditor-agnostic by design.
- **Verify:** `python3 tests/test_report_contract.py` → PASS (11 checks).
- **Deps:** T0. *(Independent of T7.1–7.3.)*

### T7.5 — `audit_safety.py` allowlist + profiles
- [x] Add opt-in path allowlisting **without weakening the audit invariant**.
- **Files:** `scripts/audit_safety.py`; `tests/test_safety.py`.
- **Acceptance:** `changes_confined_to(repo, prefix=DEFAULT_PREFIX, *, allow=())` — `allow`
  is **keyword-only**, so an allowlist can never be passed where `prefix` was expected.
  `EXTRA_BY_PROFILE = {"audit": (), "authoring": (".ux/cujs/", "SPEC.md")}`. `_allowed()`
  treats a trailing slash as a directory prefix and a bare entry as an **exact match**.
  CLI gains `--profile audit|authoring`; **the output strings at `:56,:60` render the
  effective allowlist** instead of hardcoding `.ux/audits/`, or `--profile authoring` prints
  a lie. **Module docstring rewritten** — "The usability auditor is findings-only" (`:2-15`)
  is false with two profiles, and this file is the canonical statement of the invariant.
  All three existing callers (`test_safety.py:60,64,83`, `run_evals.py:275`, the CLI) are
  byte-identical without modification.
- **Verify:** `python3 tests/test_safety.py` green with four **added** assertions (extend,
  never rewrite): **(1)** the invariant does not weaken — an `audit`-profile call **still
  flags** `.ux/cujs/`; **(2)** `authoring` permits `.ux/cujs/` + `SPEC.md`; **(3)**
  `authoring` still flags `app.tsx`; **(4)** prefix confusion — `SPEC.md.bak` and
  `.ux/cujs-evil/x.md` are **both flagged**.
- **Deps:** T0. *(Independent of T7.1–7.4.)*

> ### ✅ CHECKPOINT D — human review
> Review `cuj-contract.md` and a hand-authored sample CUJ. Confirm the schema, the
> observable-`expect` bar, and `criticality`'s four levels BEFORE any skill is written
> against them. Cheapest point to change the shape. Stop here for sign-off.

---

## Phase 8 — Authoring path (`/ux-spec`) ⭐

**T8.2 + T8.3 must land in the same commit** (the loud trap). T8.1/T8.4/T8.5 ride along.

### T8.1 — `cuj-author` persona
- [x] The persona whose value is **refusal**.
- **Files:** `agents/cuj-author.md`; `DOC_FILES`.
- **Acceptance:** frontmatter `name: cuj-author` matching the filename; `description` carries
  trigger phrases in prose (no `triggers:` key). Body states every refusal from SPEC §9.5:
  reject "the user" (demand a named actor); reject unobservable outcomes; reject feature-list
  goals; split bundled steps; reject criticality inflation; and **never invent a step the
  user didn't state** — record the gap and stop. States the ask-first gate on the host's
  `SPEC.md`.
- **Verify:** frontmatter parses; `check_cuj_author_persona()` green (T8.5).
- **Deps:** CHECKPOINT D.

### T8.2 — `spec-cuj` skill + fallback question set
- [x] The authoring workflow, with numbered steps and explicit exit criteria.
- **Files:** `skills/spec-cuj/SKILL.md`; `skills/spec-cuj/references/interview-fallback.md`;
  `DOC_FILES`.
- **Acceptance:** `name` matches the **directory**. Workflow: validate `.ux/cujs` first
  (never author onto a broken directory) → compute next free `id` → drive
  `agent-skills:interview-me`, **or** fall back to `interview-fallback.md` + **disclose** +
  offer-but-never-auto-install + record `method: interview-fallback` → read the draft back
  for confirmation → write → self-check with `validate_cuj.py` → **regenerate the index via
  `validate_cuj.py --index` and ASK, showing the diff, before splicing** → confirm footprint
  with `audit_safety.py --profile authoring`. Fallback set ≈9 questions per SPEC §9.5.
  Description: the string already shipped in `skills/spec-cuj/SKILL.md` frontmatter —
  measured against the real corpus; re-run `evals/run_evals.py` if reworded.
- **Verify:** `python3 tests/test_evals.py` green (requires T8.3 in the same commit);
  `python3 evals/run_evals.py` → **all four skills**, no collision ≥0.50, no regression to
  `usability-audit`/`ux-audit`'s existing `top_k: 1` positives.
- **Deps:** T7.1, T7.2, T7.5, T8.1.

### T8.3 — `spec-cuj` eval case
- [x] **Same commit as T8.2.**
- **Files:** `evals/cases/spec-cuj.json`.
- **Acceptance:** `skill_name: "spec-cuj"` matching the directory; ≥3 positives, ≥2 negatives
  each with an `owner`, ≥1 behavioral with `id`/`prompt`/`expected_output`/`expectations`;
  `behavioral_target` = Sprout. **`competitors.json` needs no new entries** — `audit-cuj` and
  `usability-audit` are native owners already in the corpus (the `ux-audit.json:10`
  precedent).
- **Verify:** `python3 tests/test_evals.py` green.
- **Deps:** T8.2.

### T8.4 — `/ux-spec` command
- [x] Thin entry point — parse args, invoke persona + skill, nothing more.
- **Files:** `commands/ux-spec.md`; `DOC_FILES`.
- **Acceptance:** frontmatter `name`, `description`, `argument-hint`; documents `--cuj <id>`;
  names the skill and persona it invokes.
- **Verify:** `check_ux_spec_command()` green.
- **Deps:** T8.2.

### T8.5 — Component checks + doc wiring (the silent trap)
- [x] Hand-write the checks; nothing warns you if you don't.
- **Files:** `tests/test_components.py` — `check_cuj_author_persona()`,
  `check_spec_cuj_skill()`, `check_ux_spec_command()`, `check_cuj_references()`, **each
  wired into the `main()` concatenation at `:240-241`**; `tests/test_docs.py` `DOC_FILES`.
- **Acceptance:** checks assert the load-bearing prose, not mere presence — the skill's
  `interview-me` + fallback disclosure, the ask + `spec.md` gate, `validate_cuj`, the marker
  block, and exit criteria; the references cover `actor`/`precondition`/`step`/`expect`/
  `success criteria`/`criticality`.
- **Verify:** `python3 tests/test_components.py` + `python3 tests/test_docs.py` green;
  deliberately break one asserted string → the check **fails** (proves it's wired).
- **Deps:** T8.1–T8.4.

> ### ✅ CHECKPOINT E — human review
> Author a real CUJ against Sprout by answering the interview yourself. Review: is `expect`
> genuinely observable on every step? Did it refuse your vague answers? Did it **ask** before
> writing Sprout's `SPEC.md`, and does declining leave it untouched? Is the spliced block
> byte-identical on re-run, with prose above/below preserved? This is the interview's tone and
> rigor — the part a spec can't pin down. **Stop here for sign-off.**

---

## Phase 9 — Verification path (`/cuj-audit`)

**T9.2 + T9.3 in one commit.**

### T9.1 — `cuj-auditor` persona
- [x] The inverse of `usability-auditor`: **holds no heuristics, offers no opinions.**
- **Files:** `agents/cuj-auditor.md`; `DOC_FILES`.
- **Acceptance:** `name: cuj-auditor`. Body states: *you execute the contract, you do not
  evaluate the design*; the **two-stage** 0–4 mapping (classify, then clamp by
  `criticality`); the `<CUJ-id> step <n>` Framework Violation format; render-vs-source
  honesty; findings-only / never edit host code; and that **passing steps go in the Appendix,
  never as sev0**.
- **Verify:** `check_cuj_auditor_persona()` green.
- **Deps:** CHECKPOINT E.

### T9.2 — `audit-cuj` skill
- [x] Select → validate → replay → grade → report.
- **Files:** `skills/audit-cuj/SKILL.md`; `DOC_FILES`.
- **Acceptance:** `name` matches the directory. **Empty/absent `.ux/cujs/` → stop and say so**
  ("no CUJs authored; run `/ux-spec`"), never an empty pass. Malformed CUJ → skip + disclose,
  never half-walk. Prefer live; ask before server start / navigation; screenshots to
  `.ux/audits/assets/`; evaluate `success_criteria` after the steps. **Static mode traces
  source only** → findings labeled `potential — unverified`, `frameworks: [cuj-contract]`
  only, and steps not observed go in the Appendix — **a static run cannot produce a verified
  pass**. **One report per run, not per CUJ** (keeps `index.md` rows 1:1 with runs).
  Executive summary **leads with "N/N journeys passed, M steps verified"** (SPEC §9.4).
  Self-check under the **default `audit` profile** — `audit-cuj` writes only to `.ux/audits/`.
- **Frontmatter `description` — use this string verbatim.** It was measured against the real
  TF-IDF corpus (worst pair spec-cuj↔audit-cuj = 0.373, well under the 0.50 warn line). Any
  reword re-rolls IDF for all four skills, so re-run `python3 evals/run_evals.py` if you
  touch it:
  > Verify a stored critical user journey by replaying it step by step against the running
  > app, and report the exact step that broke as a cuj report in .ux/audits. Use for "verify
  > my CUJs", "do the journeys still work", "journey regression check", "which step broke".

  Note it leads with *"Verify"* though the skill is named `audit-cuj` — deliberate. Only
  `description` text enters the routing corpus, never the skill name, and "verify my CUJs" is
  what users type. Keeping "audit" out also keeps it clear of `usability-audit`/`ux-audit`.
- **Verify:** `python3 tests/test_evals.py` + `python3 evals/run_evals.py` green (four skills).
- **Deps:** T7.1–T7.4, T9.1.

### T9.3 — `audit-cuj` eval case
- [x] **Same commit as T9.2.**
- **Files:** `evals/cases/audit-cuj.json`.
- **Acceptance:** as T8.3. Negatives: one owned by `spec-cuj`, one ("write Playwright E2E
  tests") resolving against the **existing** `agent-skills:test-driven-development` entry —
  that's the real-world confusion worth guarding.
- **ALSO restore spec-cuj's deferred negative.** `evals/cases/spec-cuj.json` carries a
  `_note` explaining that its `{"prompt": "Verify my CUJs still pass against the running
  app", "owner": "audit-cuj"}` negative had to be dropped: routing is corpus-relative, and
  until `audit-cuj` has a description it has no vector to outrank spec-cuj with. **The moment
  T9.2 lands, add it back and delete the `_note`.** Then `run_evals.py` must still be green
  for all four skills.
- **Verify:** `python3 tests/test_evals.py` green.
- **Deps:** T9.2.
- **Known:** this behavioral eval is **non-hermetic** — Sprout has no `.ux/cujs/`, so Tier 3
  must run `/ux-spec` first, chaining spec-cuj → audit-cuj. A spec-cuj regression will surface
  as an audit-cuj failure. The T7.3 fixture CUJs remain the deterministic path.

### T9.4 — `/cuj-audit` command
- [x] Thin entry point.
- **Files:** `commands/cuj-audit.md`; `DOC_FILES`.
- **Acceptance:** documents `target`, `--cuj <id|all|critical>`, `--mode static|live|hybrid`.
- **Verify:** `check_cuj_audit_command()` green.
- **Deps:** T9.2.

### T9.5 — Component checks + doc wiring
- [x] **Files:** `tests/test_components.py` — `check_cuj_auditor_persona()`,
  `check_audit_cuj_skill()`, `check_cuj_audit_command()`, wired into `main()`;
  `tests/test_docs.py` `DOC_FILES`.
- **Verify:** both suites green; break an asserted string → check fails.
- **Deps:** T9.1–T9.4.

### T9.0 — SPEC reconciliation (added during Phase 9)
- [x] SPEC §9.4's mandated lead line could not express a skip: a run that verified CUJ-001 and
  skipped CUJ-002 read "1/1 journeys passed". Amended to
  `P/N journeys passed, S skipped, M of T steps verified`, with **N = journeys selected, never
  journeys run**. SPEC §6 gained the journey-named state reset as an ask-first item (ladder
  rung L2.5).
- **Files:** `SPEC.md` §9.4 + §6; `tests/fixtures/valid/cuj-20260716-130000.md` (lead line).

### The inherited open question — ANSWERED
**"How does a verifier establish a precondition?"** A five-rung **precondition ladder**: L0
observe (records the baseline), L1 replay a setup journey, L2 improvise via the UI, L2.5 a
journey-named reset (ask first), L3 ask the user. Hard stop below L3 — no `evaluate_script`
injection, because injected state is state no user can reach, so a journey verified against it
proves nothing.

Two rules carry the weight, and both guard a false PASS:
- **L1 establishes a precondition only if the setup journey "passed its own
  `success_criteria`"** — not merely its steps. Otherwise CUJ-001's silent-data-loss bug
  establishes CUJ-002's precondition and CUJ-002 passes *because* the app is broken (its
  criterion is an *absence*). The app may not supply the evidence for its own verification.
- **The no-alibi rule.** CUJ-001's precondition ("at least one existing task") is reachable
  only through the add-task flow CUJ-001 exists to test. A naive ladder turns Checkpoint F's
  deliberate break into a *skip* and the sev4 vanishes. A **self-referential** precondition is
  never a skip: grade it from a bare `entry_point`.

> ### ✅ CHECKPOINT F — the detection test — **PASSED 2026-07-16**
> Live against Sprout, three runs + safety, all pass. The tool detects: given a silently
> broken add-task it produced an unprompted sev4 naming the exact step and quoting the
> journey's verbatim `expect`, from a fresh agent never told anything was wrong. It
> reproduced the failure twice (programmatic fill, then real keystrokes) to rule out its own
> harness before calling it a finding, and pinned `AddTodo.tsx:15` while clearing two other
> candidates. Run 1's L0 baseline found the app not in its precondition state and recorded
> that verbatim rather than assuming; run 3 traced a code path, found no defect, and refused
> to count it — "this is not a pass — it is an unverified trace of a journey that never ran."
>
> **Two acceptance criteria were NOT exercised. Both remain unproven:**
> - **The no-alibi rule never fired.** The interview produced a first-time-evaluator actor, so
>   the real CUJ-001's precondition is "empty list" — not self-referential. Both auditors
>   reasoned about the rule and correctly concluded it didn't apply. It is still the tool's
>   most likely silent failure. Note `tests/fixtures/cujs/valid/CUJ-001-add-a-task.md` DOES
>   carry a self-referential precondition ("at least one existing task" on the add-task
>   journey) and that fixture is **not** a defect — its actor is a returning user, and
>   cuj-author's bar (reachable from a fresh install, re-establishable on a second run) is
>   met by simply adding a task. Returning-user journeys are a legitimate, common shape, and
>   they are exactly what no-alibi guards. The rule wants a targeted eval; it has a fixture
>   demonstrating the shape but nothing that runs it.
> - **The vacuous-pass guard never fired.** Sprout's success criteria are all presence-shaped,
>   so no absence criterion exists to be vacuously true. Run 3 said so explicitly.
>
> The journeys were deliberately NOT reshaped to fire either — bending the actor to fit the
> test would have made the checker the author of its own rubric.
>
> Deferred, found here: run 1 wrote `version: 0.1.0` while runs 2-3 wrote `0.2.0`. Run 1 was
> following the report contract, which showed a literal `0.1.0`. Fixed in the contract.
> Recorded: the installed plugin cache pinned at d7106b5 contained no audit-cuj skill at all;
> `claude plugin marketplace update` refreshed metadata WITHOUT reinstalling. `claude plugin
> details` confirmed the live directory-source load. **Verify what is actually loaded before
> trusting any live run** — the update command is not sufficient.

> ### ✅ CHECKPOINT F — the detection test
> Run `/cuj-audit` against unmodified Sprout → journeys pass, `total: 0`, steps in the
> Appendix and **not** as sev0. Then **break a journey deliberately** (e.g. make the add-task
> input a no-op) → require a **sev4 naming `CUJ-001` step 2**. A verifier that only ever
> passes is worthless; this is the only check that proves detection over narration.
> Also run `--mode static` → `potential — unverified`, `frameworks: [cuj-contract]` only.

---

## Phase 10 — Suite roll-up

### T10.1 — Wire `audit-cuj` into `/ux-audit` ✅
- [x] Add the fourth, **conditional** suite member.
- **Files:** `skills/ux-audit/SKILL.md` (4th auditor-table row; step 1 discovery; step 2
  fan-out; step 3 native/`total: 0` caveat; step 5 verdict); `commands/ux-audit.md`
  (`argument-hint` + `--only cuj` + discovery note); `tests/test_components.py` tuple (loop
  at line ~185, not `:172` — that's the existence guard) → `("usability", "accessibility",
  "web-performance", "audit-cuj")`.
- **Acceptance:** `audit-cuj` is native but **conditional** on a non-empty `.ux/cujs/` —
  absent → **skipped with the reason recorded**, never a silent pass, and the go/no-go must
  not read a *skipped* run as a *passed* one. Use **`"audit-cuj"`, not `"cuj"`**, in the
  tuple: it's a bare substring check, so `"cuj"` would match the word anywhere in the body
  and assert essentially nothing.
- **Verify:** `python3 tests/test_components.py` green; `/ux-audit` against Sprout shows cuj
  in the roll-up; delete `.ux/cujs/` and re-run → **skipped with a reason**.
- **Deps:** CHECKPOINT F.

---

## Phase 11 — Docs & release

### T11.1 — README + AGENTS + sub-READMEs
- [ ] **Files:** `README.md` (`/ux-spec` + `/cuj-audit` rows, a CUJ section, repo layout, and
  a note that `interview-me` is **optional and undeclared**, unlike `web-quality-skills`);
  `AGENTS.md` (repo layout + a CUJ-family note beside the auditor checklist);
  `agents/README.md`, `skills/README.md`, `commands/README.md` catalogs.
- **Acceptance:** a new user can author and verify a CUJ from the README alone. Adopt **"the
  host's `SPEC.md`" vs "this repo's `SPEC.md`"** throughout — two files now share the name.
- **Verify:** `python3 tests/test_docs.py` green; all links resolve.
- **Deps:** Phases 7–10.

### T11.2 — CHANGELOG + version
- [ ] **Files:** `CHANGELOG.md` (`[Unreleased]` → `### Added`); `.claude-plugin/plugin.json`
  `version` 0.2.0 → 0.3.0, keywords `+ "cuj"`, `"journeys"`.
- **Acceptance:** **no `dependencies` change → no `marketplace.json` change** (it carries no
  version, only dependencies).
- **Verify:** full suite green.
- **Deps:** T11.1.

> ### ✅ CHECKPOINT G — go/no-go
> SPEC §9.8 DoD satisfied; all five suites + `run_evals.py` green; the audit invariant still
> flags `.ux/cujs/` under the default profile. Ship or iterate.

---

## Definition of Done (SPEC §9.8)
- [ ] Both triads exist and are wired per the composition rule.
- [ ] `cuj-contract.md` and `validate_cuj.py` agree.
- [ ] `/ux-spec` authors a valid CUJ via interview; degrades with disclosure when
      `interview-me` is absent.
- [ ] Every authored step carries an observable `expect`.
- [ ] Host `SPEC.md` index regenerates byte-identically, preserves surrounding prose, is
      written only after asking, and declining leaves it untouched.
- [ ] `/cuj-audit` emits a §3.4-valid `auditor: cuj` report naming the CUJ id + broken step;
      a passing journey yields `total: 0` with steps in the Appendix.
- [ ] Static mode labels findings `potential — unverified`, `frameworks: [cuj-contract]` only.
- [ ] **A deliberately broken journey produces a sev4 naming the correct step.**
- [ ] `audit_safety.py` **still flags** `.ux/cujs/` and `SPEC.md` under the default `audit`
      profile.
- [ ] `audit-cuj` appears in the `/ux-audit` roll-up; skipped **with a reason** when no CUJs
      exist.
- [ ] README / AGENTS / CHANGELOG updated; `plugin.json` at 0.3.0.
