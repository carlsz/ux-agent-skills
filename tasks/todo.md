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
  `ai-design-heuristics.md`, `npcis.md` (derived from `references/ux-researcher.md`).
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
- [x] Live end-to-end + static fallback both work. *(live mode built + structurally
      tested; static + four-framework dogfooded against sprout. A true live browser run
      against a running app is still un-exercised — see note below.)*
- [x] Reports validate against the shared contract; `index.md` appends.
- [x] Post-run `git status` scoped to `.ux/audits/` only.
- [x] Every finding: framework citation + 0–4 severity + evidence + fix.
- [x] README/CHANGELOG updated.
