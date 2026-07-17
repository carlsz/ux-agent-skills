# SPEC — Usability Auditor

> A usability-focused auditor for the **ux-agent-skills** plugin. It inspects a host
> app (live or from source), evaluates it against four usability frameworks, and writes
> a severity-scored report to `.ux/audits/` in the host repo. Findings only — it never
> edits host application code.
>
> This is the **first of a suite** of auditors (accessibility, web performance, …). It
> therefore also defines the **shared `.ux/audits` report contract** every future auditor
> reuses, so their outputs are comparable and discoverable side by side.

- **Status:** Draft — awaiting approval
- **Owner:** Carl Sziebert (carlsz@gmail.com)
- **Date:** 2026-07-15
- **Plugin:** `ux-agent-skills` v0.2.0

---

## 1. Objective

### Problem
Teams ship UI without a repeatable, expert-level usability inspection. Ad-hoc reviews
are inconsistent, uncited, and leave no durable artifact. As the plugin grows into a
*suite* of auditors, each one inventing its own output format would make results
impossible to compare or track over time.

### Goal
Deliver a **usability-auditor** that any host app can invoke on demand to produce a
rigorous, framework-grounded, severity-scored usability report — and establish the
**report contract** the rest of the auditor suite will inherit.

### Target users
- **Product engineers / AI coding agents** working in a host repo who want a usability
  gut-check before shipping a screen or flow.
- **Designers / PMs** who want a durable, prioritized findings artifact to triage.
- **Future auditor authors** (a11y, perf) who need a proven pattern and shared contract.

### Non-goals
- Not a fixer — it does not edit host application code (see §6 Boundaries).
- Not a replacement for live user testing — it is expert heuristic inspection *prior* to
  user testing.
- Not an accessibility or performance auditor — those are separate suite members that
  reuse this spec's report contract but apply their own frameworks.

### Success criteria
1. Running the command against a host app produces a valid report in `.ux/audits/`.
2. Every finding cites a specific framework heuristic, carries a 0–4 severity, is backed
   by concrete evidence (screenshot path, `file:line`, or repro steps), and gives an
   actionable fix.
3. No host application file outside `.ux/audits/` is created or modified.
4. The report validates against the shared contract in §3.4 — i.e. a future a11y auditor
   emitting the same schema slots in with no format changes.

---

## 2. Commands

The auditor ships as the plugin's standard three-layer composition (persona / skill /
command) plus the shared report contract.

| Layer | Path | Role |
|-------|------|------|
| Persona | `agents/usability-auditor.md` | *The who* — senior UX auditor voice, four-framework knowledge base, severity-report output format. |
| Skill | `skills/usability-audit/SKILL.md` | *The how* — evidence-gathering → evaluation → report workflow with exit criteria. |
| Command | `commands/usability-audit.md` | *The when* — user-facing entry point. |

### User-facing invocation
```
/ux-agent-skills:usability-audit [target] [--scope <flows|routes|components>] [--mode live|static]
```

- `target` — a URL (live mode) or a path/glob within the host repo (static mode).
  Optional; if omitted the skill asks or infers from the running dev server / repo root.
- `--scope` — narrows the audit (e.g. a specific flow like "checkout"). Optional.
- `--mode` — force an evaluation mode. Optional; default is auto (see §5 hybrid logic).

### Developer / maintenance commands (this plugin's own repo)
```
claude --plugin-dir .          # load the working copy for local dev
claude plugin validate .       # sanity-check manifest + component wiring (if available)
```

---

## 3. Project structure

### 3.1 Files this spec adds to the plugin repo
```
ux-agent-skills/
├── agents/
│   └── usability-auditor.md          # persona (NEW)
├── skills/
│   └── usability-audit/
│       ├── SKILL.md                  # workflow (NEW)
│       └── references/               # eval material — self-contained with the skill
│           ├── nng-ux-heuristics.md      # Nielsen's 10 (moved here to keep the skill atomic)
│           ├── report-contract.md        # shared .ux/audits contract
│           ├── shneiderman-8.md          # Golden Rules (NEW, Phase 3)
│           ├── ai-design-heuristics.md   # PAIR / Amershi (NEW, Phase 3)
│           └── npcis.md                  # Navigation/Presentation/Content/Interaction/Strategy (NEW, Phase 3)
├── commands/
│   └── usability-audit.md            # slash command (NEW)
└── skills/usability-audit/references/   # eval frameworks + the shared report contract
```
> Skill-local `references/` are the eval frameworks the skill loads at run time. They live
> beside the skill so it is self-contained (atomic). The original seed material
> (`references/ux-researcher.md`, `nng-ux-heuristics.md`) has since been absorbed into the
> persona, skill lenses, and report contract, and removed.

### 3.2 What the auditor writes into the HOST repo
```
<host-repo>/
└── .ux/
    └── audits/
        ├── index.md                       # rolling index of all audit runs (any auditor)
        ├── usability-20260715-143000.md   # one report per run
        └── usability-20260715-160000.md
```

### 3.3 Report file — usability report body
Each run writes `.ux/audits/usability-<YYYYMMDD-HHMMSS>.md`:

1. **YAML frontmatter** — shared schema (§3.4).
2. **Executive summary** — 2–4 sentences + severity counts table.
3. **Prioritized fix list** — findings sorted by severity (4 → 1), each linking to its
   detail below.
4. **Findings** — one section per finding, using the reference's Severity Report format:
   - **Issue Description** — what is broken or confusing.
   - **Framework Violation** — the specific heuristic / rule / NPCIS dimension.
   - **Severity (0–4)** — per the rubric in §4.
   - **Evidence** — an inline screenshot embed (`![alt](./assets/…)`), `file:line`, or repro
     steps.
   - **Recommended Fix** — actionable design guidance.
5. **Walkthrough** *(optional; live/hybrid only)* — the captured key states assembled into a
   visual sequence. See §10.
6. **Appendix** — mode, target, scope, frameworks applied, coverage notes / what was NOT
   inspected (no silent gaps).

### 3.4 Shared report contract (inherited by every future auditor)
All auditors in the suite write to the same `.ux/audits/` directory and share this
frontmatter schema. Only `auditor` and `frameworks` differ between auditors.

```yaml
---
auditor: usability          # usability | accessibility | web-performance | …
schema: 2                    # report-contract version (2 added the Walkthrough section — §10)
version: 0.1.0               # emitting auditor version
date: 2026-07-15T14:30:00Z   # ISO-8601, from runtime clock
target: https://localhost:3000/checkout   # URL or repo path
mode: live                   # live | static | hybrid
scope: "checkout flow"       # human-readable audit scope
frameworks:                  # which knowledge bases were applied
  - nielsen-10
  - shneiderman-8
  - ai-heuristics
  - npcis
summary:                     # counts MUST equal the number of findings by severity
  total: 12
  sev4: 1                    # catastrophe
  sev3: 4                    # major
  sev2: 5                    # minor
  sev1: 2                    # cosmetic
---
```

**`index.md`** — appended (never rewritten) with one row per run:
```
| Date (UTC) | Auditor | Scope | Sev4 | Sev3 | Sev2 | Sev1 | Report |
```

---

## 4. Code / authoring style

Because the deliverables are Markdown persona/skill/command files plus generated reports,
"code style" means authoring and output conventions.

### Component authoring
- **Persona** — second-person role definition, an explicit point of view, and a fixed
  output format. Keep the knowledge base as *pointers* to the skill's `references/`, not
  inlined heuristic text.
- **Skill** — YAML frontmatter (`name`, `description`, trigger cues) + numbered workflow
  with **explicit exit criteria**. Keep steps imperative and verifiable.
- **Command** — thin: parse args, invoke the persona + skill, nothing more.
- Match the existing repo's voice and the composition rule in `README.md`
  (*the who / the how / the when*).

### Evaluation framework stack (all four applied)
| Framework | Lens |
|-----------|------|
| Nielsen's 10 Heuristics | Baseline HCI usability. |
| Shneiderman's 8 Golden Rules | Predictable workflows, data-dense / expert efficiency. |
| AI Design Heuristics (PAIR / Amershi) | Non-deterministic / generative-AI UI: expectation-setting, explainability, correction pathways. |
| NPCIS | Holistic: Navigation, Presentation, Content, Interaction, Strategy. |

### Severity rubric (0–4, Nielsen's severity ratings)
| Score | Meaning | In report? |
|-------|---------|-----------|
| 0 | Not a usability problem | No — omit |
| 1 | Cosmetic only | Yes |
| 2 | Minor usability problem | Yes |
| 3 | Major (high priority) | Yes |
| 4 | Catastrophe — fix before release | Yes, top of list |

### Report output rules
- **Grounded** — every finding needs concrete evidence; no unverifiable claims.
- **Cited** — every finding names the exact heuristic/rule/dimension violated.
- **Actionable** — every finding ends with a specific recommended fix.
- **Honest coverage** — the appendix lists what was NOT inspected (auth-gated screens,
  out-of-scope routes). Silent truncation is prohibited.
- **Deterministic naming** — `usability-<YYYYMMDD-HHMMSS>.md`; timestamps from the
  runtime clock.

---

## 5. Evaluation strategy (how evidence is gathered) & testing strategy

### 5.1 Evaluation mode — hybrid (auto)
1. **Prefer live** when a target URL is given or a dev server is detected/running.
   Drive the rendered app via a browser MCP: navigate the flow, screenshot key states,
   read the accessibility/DOM tree, exercise real interactions.
2. **Fall back to static** when no running app is available: read host components,
   markup, routes, and copy from source and evaluate structurally.
3. **Hybrid** — use live for runtime/interaction heuristics (system status, feedback,
   error recovery) and static to locate the responsible `file:line` for fixes. Record the
   actual mode used in frontmatter.
4. Never start a dev server, navigate, or bypass auth without asking (see §6).

### 5.2 Testing / validation strategy for the auditor itself
Since outputs are agent-generated artifacts, validation focuses on the report contract
and safety invariants:

1. **Schema validation** — generated frontmatter parses as YAML; all required keys
   present; `summary` counts exactly equal findings by severity.
2. **Groundedness spot-check** — sample findings; each must have evidence + a valid
   framework citation + a fix. Reject fabricated or generic findings.
3. **Severity calibration** — apply the rubric to a fixed set of known issues and confirm
   consistent scoring across runs.
4. **Safety invariant (critical)** — after a run, `git status` in the host repo shows
   changes **only** under `.ux/audits/`. Any other modified/created file is a failure.
5. **Idempotency** — re-running never overwrites or deletes a prior report; it creates a
   new timestamped file and appends one `index.md` row.
6. **Command wiring** — `/ux-agent-skills:usability-audit` resolves and invokes the
   persona + skill; args (`target`, `--scope`, `--mode`) are honored.
7. **Contract portability** — a mock second auditor (`auditor: accessibility`) emitting
   the §3.4 schema validates and coexists in the same `index.md` unchanged.
8. **Dogfood** — run against a real sample flow (e.g. a scaffold app) and manually
   confirm findings are true positives worth acting on.

---

## 6. Boundaries

### Always (no need to ask)
- Read host source, markup, routes, and copy freely.
- Create `.ux/` and `.ux/audits/` in the host repo root if absent, and write reports there.
- Produce only severity-scored, evidence-backed, framework-cited findings.
- Record actual mode, scope, and coverage gaps in every report.

### Ask first
- Starting or restarting the host dev server, or navigating a browser to any URL.
- Reaching auth-gated screens (the user must supply access; the auditor won't authenticate).
- **Resetting host app state** to establish a CUJ precondition — clearing localStorage, logging out,
  starting a fresh session — and **only when the journey file names the reset** (§9.4). This destroys
  state the user may care about, so it is gated like a server start rather than treated as ordinary
  navigation. A reset the journey does not name is not available at any price.
- Installing anything, or running host build/test scripts.
- Adding `.ux/` to the host's `.gitignore` (recommend, don't do silently).
- Writing outside `.ux/audits/` for any reason (e.g. saving screenshots elsewhere).
- **Writing the host's `SPEC.md`** — only `/ux-spec` may, and only to splice the generated CUJ index
  block, showing the diff first (§9.3). Auditors never write it.

### Never
- **Edit, refactor, or "fix" host application code** — this is a findings-only auditor.
- Fabricate findings, severities, or evidence; report anything not actually observed.
- Enter credentials, bypass authentication, or defeat bot/CAPTCHA gates to reach screens.
- Delete or overwrite prior audit reports (append / new-file only).
- Publish, post, or send a report to any external service.
- Silently skip in-scope areas without noting the gap in the report appendix.

---

## 7. Acceptance criteria (Definition of Done)

- [ ] `agents/usability-auditor.md`, `skills/usability-audit/SKILL.md`, and
      `commands/usability-audit.md` exist and are wired per the composition rule.
- [ ] The skill loads all four framework references and applies the 0–4 rubric.
- [ ] `/ux-agent-skills:usability-audit <url>` runs live mode end-to-end and writes a
      valid report to `.ux/audits/`.
- [ ] Static-mode fallback works with no running app.
- [ ] Report validates against the §3.4 shared contract; `index.md` gets one appended row.
- [ ] Post-run `git status` in the host repo shows changes only under `.ux/audits/`.
- [ ] Every finding: cites a framework, carries a 0–4 severity, has evidence, has a fix.
- [ ] README/CHANGELOG updated to reflect the auditor and the shared report contract.

---

## 8. Open questions / future suite work

- **Report retention** — should old reports be pruned, or diffed run-over-run to show
  regressions/fixes? (Deferred; `index.md` enables this later.)
- **Suite orchestration** — a future `/ux-agent-skills:audit` meta-command that fans out
  usability + a11y + perf auditors and merges results. (Out of scope here; contract enables it.)
- **Screenshot assets** — *resolved (§10, schema 2)*: `.ux/audits/assets/` is the standard
  location; images use stable names so re-runs overwrite (prune-to-latest), and are embedded
  inline as a `## Walkthrough` visual sequence.
- **VCS treatment** — leave `.ux/` committed vs. ignored to the host team; auditor only
  recommends. (Committing keeps the walk-through images rendering on GitHub; stable naming
  bounds the binary footprint.)

---

# 9. Critical User Journeys (CUJs)

> A second capability in the same plugin: author a host app's critical user journeys through an
> interview, store them as canonical files under `.ux/cujs/`, and verify them against the running app
> as a member of the audit suite defined above.
>
> Sections 1–8 specify the **usability auditor** and the shared report contract. This section reuses
> both and does not change either.

- **Status:** Draft — awaiting approval
- **Date:** 2026-07-16
- **Adds:** `/ux-spec`, `/cuj-audit`; personas `cuj-author`, `cuj-auditor`; skills `spec-cuj`,
  `audit-cuj`; the CUJ file contract; `auditor: cuj` reports.

## 9.1 Objective

### Problem
The suite audits an app against *generic* frameworks. Nielsen's 10 heuristics will tell you a button
has poor affordance; they will not tell you that the one flow the business depends on is broken. The
plugin has no representation of what the app is **for**, so it cannot regress-test the things that
actually matter. [`README.md`](README.md) already promises agents that "rigorously verify interfaces
against **critical user journeys**" — today that promise is unbacked.

### Goal
Give a host app a durable, machine-checkable definition of its critical journeys, and an auditor that
replays them and reports the exact step that broke. The suite then answers both *"is this
well-designed?"* (heuristics) and *"does the thing users came for still work?"* (journeys).

### Target users
- **Product engineers / AI coding agents** who want to know a refactor didn't break the money flow.
- **Designers / PMs** who want the team's assumptions about *who does what, and why it matters*
  written down and testable rather than tribal.
- **The existing auditors**, which gain a scope signal: a CUJ names the flows worth auditing.

### Non-goals
- **Not a test framework.** CUJs are prose journeys verified by an agent, not Playwright specs. They
  describe what a *person* is trying to do; they do not replace E2E tests, and `/cuj-audit` is not a
  CI gate.
- **Not a fixer.** `/cuj-audit` reports broken steps; it never repairs them (§9.7).
- **Not user research.** A CUJ records what the team believes is critical. It is not evidence that
  users agree — that still takes talking to users.

### Success criteria
1. `/ux-spec` produces `.ux/cujs/<id>-<slug>.md` files that validate against the §9.2 contract, with
   every step carrying an **observable** expected outcome.
2. The host's `SPEC.md` gains a CUJ index that regenerates byte-identically and never clobbers
   surrounding prose — and is only ever written after asking.
3. `/cuj-audit` replays a stored journey and emits a report valid against the §3.4 contract with
   `auditor: cuj`, each finding naming the CUJ id and the step that broke.
4. Breaking a journey in a real app produces a severity-4 finding that names the right step. Detection,
   not narration.
5. The audit safety invariant is **unchanged**: an audit run that touches anything outside
   `.ux/audits/` — including `.ux/cujs/` — is still a violation.

## 9.2 The CUJ file contract

Canonical location in the **host** repo, one file per journey:

```
<host-repo>/
└── .ux/
    └── cujs/
        ├── CUJ-001-add-a-task.md
        └── CUJ-002-complete-a-task.md
```

Contract document: `skills/spec-cuj/references/cuj-contract.md`, owned by **spec-cuj** and linked by
`audit-cuj`. This mirrors the report contract's precedent — the contract lives with the skill that
*produces* the artifact, consumers link across. Machine-checked by `scripts/validate_cuj.py`, which is
the executable form of that document; if the two disagree, reconcile them.

**Ten keys**, and the smallness is a requirement rather than an accident. A journey is written
by a human answering an interview, so every field is one more thing to answer before they get
any value — and the failure mode of a heavy schema isn't bad journeys, it's *no journeys*.
Anything derivable from the filename, from git, or from another field is ceremony and is
excluded.

```yaml
---
id: CUJ-001                  # ^CUJ-\d{3}$ — unique; must match the filename's id
schema: 1                    # cuj-contract version
title: Add a task to the list
actor: "Returning user with 3-10 existing tasks, opens the app daily to capture new ones"
goal: "Capture a new task from the list view without navigating away"   # an outcome, not features
criticality: critical        # critical | high | medium | low
entry_point: "/"             # route, URL, or named screen
preconditions:               # non-empty; what must already be TRUE (not what you do)
  - "App loaded at / with at least one existing task"
steps:                       # non-empty, ordered, n contiguous 1..N
  - n: 1
    action: "Click the new-task input at the top of the list"
    expect: "The input takes focus and shows the placeholder 'What needs doing?'"
  - n: 2
    action: "Type 'Buy milk' and press Enter"
    expect: "A row reading 'Buy milk' appears at the top of the list and the input clears"
success_criteria:            # evaluated AFTER the steps complete
  - "'Buy milk' is still present after a full page reload"
---
```

Body: `## Narrative` (2–4 sentences: why this journey exists, what breaks for the business if it
breaks) and `## Out of scope` (what this journey deliberately does not cover).

**What is deliberately absent**, and why each was cut:

| Not a field | Because |
|-------------|---------|
| `slug` | The filename carries it. A field whose only job is to be compared against the filename is ceremony — removing it removes the whole mismatch class instead of validating it. `id` stays (reports cite it), so the filename's id must match frontmatter. |
| `actor_description` | One specific `actor` sentence does the same work. Splitting it across two keys bought nothing. |
| `authored` / `revision` / `author` | Git answers who, when, and how many revisions — honestly, and without a field anyone can forget to bump. An unbumped `revision: 1` on a journey edited four times is worse than no revision, because it lies with confidence. See §9.7. |

**Why `preconditions` survives** the same cut: if setup folds into step 1, then *failing to
establish the starting state* becomes indistinguishable from *the journey being broken*, and
`/cuj-audit` would report a severity-4 catastrophe for what is really "couldn't run this".

**`expect` is the load-bearing field.** It must be *observable*: a visible element, a specific string,
a URL change, a persisted value. "It works", "the state updates", "it saves" are not expected outcomes
— they are the absence of one. The validator rejects an empty `expect`; the `cuj-author` persona
rejects an unobservable one, since that judgement cannot be made statically.

**The body does not restate the steps.** This departs from the report contract (§3.3), where the body
restates the frontmatter and the validator reconciles the two. That works for a report because a
report is written once and never edited. A CUJ is a living document a human maintains, so duplicating
the steps into prose would guarantee drift and reduce the reconciliation check to a nag. Frontmatter
is the single source; the narrative carries what YAML cannot.

## 9.3 The host `SPEC.md` index

Every host app that adopts CUJs gets one generated index section in **its own** `SPEC.md` — not the
full journey text, which stays in `.ux/cujs/`:

```markdown
## Critical User Journeys

<!-- BEGIN ux-agent-skills:cuj-index — generated from .ux/cujs/; edit the CUJ files, not this table -->
| ID | Journey | Actor | Criticality | Goal | File |
|----|---------|-------|-------------|------|------|
| CUJ-001 | Add a task | returning-user | critical | Capture a new task from the list view | [.ux/cujs/CUJ-001-add-a-task.md](.ux/cujs/CUJ-001-add-a-task.md) |
<!-- END ux-agent-skills:cuj-index -->
```

Rules:
- **The block is a pure function of `.ux/cujs/`.** Every cell derives from frontmatter; nothing in it
  is user-authored. That is what makes idempotent regeneration achievable rather than aspirational —
  there is nothing to preserve.
- Rows sort by `id`. Regenerating with no CUJ changes produces **byte-identical** output.
- **Only bytes between the markers are replaced.** Prose above and below is untouched.
- Generated by `python3 scripts/validate_cuj.py --index .ux/cujs`, **never** by improvising the table
  in prose. An agent rewriting a table from memory is not idempotent.
- Markers absent, or the host has no `SPEC.md` → **ask** before inserting or creating, showing the
  diff. If declined, the CUJ files stand alone; the index is a convenience, not the source of truth.
- This plugin's own `SPEC.md` — the file you are reading — gets **no** CUJ index. It has no journeys.
  Throughout this section, "the host's `SPEC.md`" and "this repo's `SPEC.md`" are distinguished
  explicitly.

## 9.4 CUJ verification and the report contract

`/cuj-audit` is an auditor like any other: it reuses the §3.4 contract unchanged, writing
`.ux/audits/cuj-<YYYYMMDD>-<HHMMSS>.md` — **one report per run, not per CUJ**, so `index.md` rows stay
1:1 with runs.

- `auditor: cuj`
- **Framework Violation** carries the journey and the step: `CUJ-001 "Add a task" — step 2
  (cuj-contract); expected "…"`.
- The CUJ manifest (ids verified, steps verified, steps not observed) goes
  in the **Appendix**, not in new frontmatter keys. The frontmatter stays at the shared nine. Adding
  auditor-specific keys to a *shared* contract is how comparability erodes.

### Severity mapping (0–4)

Two stages: classify the failure, then clamp by the journey's own `criticality`.

| Score | Class |
|-------|-------|
| **4** | **Journey blocked** — the expected outcome never occurs and the actor cannot reach `goal` by any route. No workaround. |
| **3** | **Workaround required, or success criteria fail while the flow appears to succeed** — includes the silent-data-loss class: every step passed, then the task didn't persist. Rated 3 rather than 2 because the user *believes* they succeeded. |
| **2** | **Observable mismatch, journey unaffected** — the goal is met, but `expect` is not what happened. |
| **1** | **Cosmetic divergence** — label, copy, or ordering of a non-load-bearing element differs. |
| **0** | **Match — omit.** Passing steps are listed in the Appendix, never as findings. |

Then cap by `criticality`: `critical` / `high` → uncapped; `medium` → max 3; `low` → max 2. A blocked
journey is only a *catastrophe* if the journey matters, and the author already ranked that — reusing
their ranking is why `criticality` is mandatory. Each finding's justification names both stages.

Severity 0 stays a non-finding, exactly as §4 requires. **A passing journey is `total: 0`** — unique
in the suite, where empty normally means "found nothing". The executive summary must therefore lead
with the counts, because the schema has no way to distinguish a clean pass from a run that checked
nothing:

```
P/N journeys passed, S skipped, M of T steps verified.
```

**`N` is the number of journeys *selected*, never the number run.** A journey that could not be
replayed stays in the denominator, so `1/2 journeys passed, 1 skipped` is the honest report of a run
that verified one journey and skipped another. Were `N` to count only what ran, the same run would
read `1/1 journeys passed` — a lie by omission, and precisely the failure this lead line exists to
prevent. A skipped journey never leaves the denominator, which is what keeps muting visible.

When `S == N`, say so plainly: *"0/N journeys passed — every journey was skipped; nothing was
verified."* That run also emits `frameworks: [cuj-contract]` alone (see below), so a reader and the
roll-up both have a signal that `total: 0` is **not** a pass here.

### `frameworks` vocabulary

```
cuj: cuj-contract | task-completion | success-criteria
```

The sibling auditors cite external standards (nielsen-10, wcag-2.2). CUJ verification has none — the
standard *is* the host's own journey files. So this vocabulary names which lens actually ran:

| Value | Meaning |
|-------|---------|
| `cuj-contract` | The journey file is the rubric. Always present; a report without it isn't a CUJ verification. |
| `task-completion` | The goal-reachability lens — did the actor reach `goal`, with or without a workaround? Separates sev4 from sev3. **Only claimable when the run actually completed (or failed to complete) the journey — live/hybrid only.** |
| `success-criteria` | The post-steps check. Separable because a journey can pass every step and still fail its criteria. |

This makes the list a machine-readable statement of *how much the run could prove*: a static run
honestly emits `frameworks: [cuj-contract]` only — it traced source, it did not complete the task, it
did not observe persistence. That is the render-vs-source honesty rule (§6 of the report contract)
expressed in frontmatter.

### Evaluation modes
Prefer **live**, as §5.1 specifies. In **static** mode `/cuj-audit` can only trace the route, handler,
or component behind each step and assess whether `expect` is plausible — every such finding is labeled
`potential — unverified`. A static run also **cannot produce a verified pass**: steps it could not
observe go in the Appendix "not observed" list, never as a silent pass.

## 9.5 Components

| Layer | Path | Role |
|-------|------|------|
| Persona | `agents/cuj-author.md` | *The who* — a UX researcher who thinks in journeys and **refuses vague ones**. |
| Persona | `agents/cuj-auditor.md` | *The who* — executes the contract; does not evaluate the design. |
| Skill | `skills/spec-cuj/SKILL.md` | *The how* — interview → draft → write → validate → ask → splice the index. |
| Skill | `skills/audit-cuj/SKILL.md` | *The how* — select → validate → replay → grade → report. |
| Command | `commands/ux-spec.md` | *The when* — `/ux-spec [--cuj <id>]`. |
| Command | `commands/cuj-audit.md` | *The when* — `/cuj-audit [target] [--cuj <id\|all\|critical>] [--mode static\|live\|hybrid]`. |

`cuj-author`'s value is **refusal**, and the persona states the refusals explicitly: reject "the user"
(demand a named actor); reject unobservable outcomes; reject feature-list goals; split bundled steps;
reject criticality inflation (if every CUJ is critical, none are); and **never invent a step the user
didn't state** — an incomplete CUJ marked incomplete beats a fabricated one, inheriting the suite's
never-fabricate rule.

`cuj-auditor`'s point of view is the inverse of `usability-auditor`'s: **it holds no heuristics and
offers no opinions.** The CUJ says what should happen; the auditor reports whether it did, and at which
step.

### Interview
`/ux-spec` drives [`agent-skills:interview-me`](https://github.com/addyosmani/agent-skills) one
question at a time. It is an **optional, undeclared dependency** — the same degrade-and-disclose
pattern the roll-up already uses for `web-quality-skills`. If it isn't installed, `spec-cuj` falls back to
its own question set in `references/interview-fallback.md`, **says so**, offers to install without
auto-installing, and says so in its summary. It is not added to `plugin.json`
`dependencies`: the capability degrades rather than fails, so a hard dependency would overstate it.

**Guessing is scoped, not banned.** `interview-me`'s method is a guess attached to each question,
and its own documented risk is a polite user agreeing to be agreeable. That risk is only costly on
the fields something downstream is **graded** against — each step's `expect` and the
`success_criteria` (`audit-cuj`'s pass/fail oracle) and `criticality` (the severity clamp). So the
persona **guesses the description and elicits the oracle**: it leads with a guess on the seven
descriptive fields (`actor`, `goal`, `title`, `entry_point`, `preconditions`, each step's `action`,
narrative), and asks the three graded fields **open**, refusing a bare "yes". A blanket no-guess
rule was tried first (Checkpoint E) and made the interview laborious without buying safety the
scoped rule doesn't; the scope is the same line the persona already drew for source —
*"source checks the answer, it never supplies the `expect`."*

### Suite membership
`audit-cuj` joins the `/ux-audit` fan-out as a fourth auditor. It is native but **conditional**: it
needs a non-empty `.ux/cujs/`. Absent → skipped with the reason recorded ("no CUJs authored; run
`/ux-spec`"), never a silent pass. The roll-up's go/no-go must not read a *skipped* CUJ run as a
*passed* one.

## 9.6 Testing / validation strategy

Extends §5.2; the invariants there continue to hold unchanged.

1. **CUJ contract validation** — `scripts/validate_cuj.py` checks each file (required keys, id/slug
   patterns, `criticality` vocabulary, non-empty `preconditions`/`steps`/`success_criteria`,
   contiguous step numbering, non-empty `action`/`expect`) and the directory as a
   whole (**duplicate ids**, **filename ≠ `<id>-<slug>.md`**). The cross-file checks are the ones that
   actually break things: a duplicate id corrupts the index *and* every report's violation reference.
2. **Index idempotency** — `render_index` over the same directory twice is **byte-identical**, and
   splicing preserves prose outside the markers.
3. **No PII** — a CUJ carrying `author` / `authored` / `by` / `email` is **rejected**, so the rule in
   §9.7 is executable rather than merely documented. Deleting the field from the schema is not the
   guarantee; nothing stops someone adding it back by hand.
4. **Report portability** — `auditor: cuj` fixtures (a sev3 report, and a `total: 0` clean pass)
   validate against the §3.4 contract; a `cuj` report citing `nielsen-10` is rejected.
5. **The audit invariant does not weaken (critical)** — after an audit run, `.ux/cujs/` and `SPEC.md`
   changes are **still violations**. The allowlist below is opt-in and applies to authoring only.
6. **Detection, not narration** — the end-to-end test breaks a journey deliberately in a real app and
   requires a sev4 naming the correct step. A tool that only ever passes is not a verifier.

### The safety allowlist
`scripts/audit_safety.py` grows a keyword-only `allow` parameter and two profiles:

```
audit      → .ux/audits/                  # unchanged, byte-for-byte
authoring  → .ux/audits/, .ux/cujs/, SPEC.md
```

Keyword-only is the point: an allowlist cannot be passed positionally where the prefix was expected,
so the audit invariant cannot be widened by accident. Matching distinguishes directory prefixes
(`.ux/cujs/`) from exact files (`SPEC.md`) — a bare prefix test would also permit `SPEC.md.bak` and
`.ux/cujs-evil/`, which is precisely what an allowlist must not enable.

## 9.7 Boundaries

Section 6 governs the auditors and is unchanged. CUJ authoring adds the following, and the
reconciliation must be stated plainly rather than left implicit:

> **Findings-only means never editing host *application code*.** `.ux/cujs/` and the host's `SPEC.md`
> are documentation the user authors *through* the agent — they are the user's own words, captured.
> `/ux-spec` is not an auditor. Auditors remain findings-only and write nowhere but `.ux/audits/`.

### Always (no need to ask)
- Create `.ux/cujs/` in the host repo root and write CUJ files there.
- Read existing CUJs, and validate them before authoring or verifying.

### Ask first
- **Writing the host's `SPEC.md`** — only to splice the generated index block, and only after showing
  the diff. If declined, the CUJ files stand alone.
- Everything already listed in §6 (dev server, navigation, installing — including a missing
  `interview-me`: offer, never auto-install).

### Never
- **Edit, refactor, or "fix" host application code.** `/cuj-audit` reports the broken step; repairing
  it is the user's call.
- **Record a CUJ's own provenance — author, date, revision, or capture method.** There is no
  `authored` block, and `author` / `authored` / `by` / `email` are rejected outright. No `git config`
  read, no fallback value. Git answers who, when, and how many revisions, and answers it honestly;
  a hand-maintained field is right only until the first person forgets, and an unbumped `revision: 1`
  on a journey edited four times is worse than no revision because it lies with confidence. For the
  author specifically this is also PII in a file that ships in the host's repo: **no PII in the
  artifact beats a rule about handling PII in the artifact.**
- Invent a step, an actor, or a criticality the user did not state — record the gap and stop.
- Report a journey as passing when it was not observed to pass (see the static-mode rule in §9.4).
- Rewrite or reorder anything in the host's `SPEC.md` outside the marker block.

## 9.8 Acceptance criteria (Definition of Done)

- [ ] `agents/cuj-author.md`, `agents/cuj-auditor.md`, `skills/spec-cuj/`, `skills/audit-cuj/`,
      `commands/ux-spec.md`, and `commands/cuj-audit.md` exist and are wired per the composition rule.
- [ ] `skills/spec-cuj/references/cuj-contract.md` and `scripts/validate_cuj.py` agree.
- [ ] `/ux-spec` authors a valid CUJ end-to-end via interview, degrading to the fallback question set
      with disclosure when `interview-me` is absent.
- [ ] Every authored step carries an observable `expect`.
- [ ] The host's `SPEC.md` index regenerates byte-identically and preserves surrounding prose; it is
      written only after asking, and declining leaves it untouched.
- [ ] `/cuj-audit` emits a §3.4-valid report with `auditor: cuj`, each finding naming the CUJ id and
      broken step; a passing journey yields `total: 0` with steps listed in the Appendix.
- [ ] Static mode labels findings `potential — unverified` and emits `frameworks: [cuj-contract]` only.
- [ ] A deliberately broken journey produces a sev4 naming the correct step.
- [ ] `audit_safety.py` still flags `.ux/cujs/` and `SPEC.md` under the default `audit` profile.
- [ ] `audit-cuj` appears in the `/ux-audit` roll-up, and is skipped **with a reason** when no CUJs
      exist.
- [ ] README / AGENTS / CHANGELOG updated; `plugin.json` at 0.3.0.

---

# 10. Visual walk-through (report contract schema 2)

> An additive extension to the shared report contract (§3.4). Turns the screenshots the
> usability and CUJ auditors already capture in live mode into a rendered, ordered
> walk-through embedded in the report. Bumps the contract `schema` from `1` to `2`.

- **Status:** Approved
- **Date:** 2026-07-17
- **Adds:** the optional `## Walkthrough` report section; the `.ux/audits/assets/` naming
  convention; inline-embed evidence. No new frontmatter keys, no new components.

## 10.1 Objective

**Problem.** Auditors screenshot key states (usability) and journey steps (CUJ) during live
runs, but the images are used only as failure *evidence* — a bare path in a finding — and
passing steps capture nothing. There is no visual record of a journey that *worked*, and the
images do not render (bare path, not an embed).

**Goal.** Give the usability and CUJ reports a `## Walkthrough`: an ordered, rendered
sequence of the captured screenshots — a per-step visual record of a CUJ, or a key-states
gallery for a usability flow — that a human can scan to *see* what the auditor saw.

**Non-goals.** Not a format change: Markdown stays the canonical, validated, indexed report.
Not for accessibility / web-performance / the roll-up (this change is usability + cuj only).
A richer interactive HTML companion (flipbook/lightbox) — **delivered in 0.5.0, see §10.6** —
*derives* from the Markdown and leaves this contract untouched.

## 10.2 The `## Walkthrough` section

Optional; **live/hybrid only** — static mode has no running app to capture, so the section's
absence there is correct, not a coverage gap (it reinforces the render-vs-source honesty rule
in §3.4 / the contract §6). Placed after `## Findings` and before `## Appendix`. It carries no
`[sevN]` headings, so it never perturbs the finding counts.

- **cuj shape** — one `### Step <n> — <action>` per journey step, in `n` order, each step
  captured whether it passed or failed, each embedding its screenshot inline with a one-line
  expected-vs-observed.
- **usability shape** — one `### <state>` per captured key state (Initial / Mid-flow /
  Success / Error / Empty).

## 10.3 Asset naming — stable, prune-to-latest

Screenshots live under `.ux/audits/assets/` (already permitted by the `audit_safety.py`
allowlist — no change) with **stable, deterministic names**, so a re-run overwrites rather
than accumulates: the directory is bounded by (journeys × steps) or a flow's key states, not
by run count.

| Auditor | What | Name |
|---------|------|------|
| cuj | a journey step | `cuj-<id>-step-<n>.png` |
| cuj | criteria / other evidence | `cuj-<id>-<slug>.png` |
| usability | a key state | `usability-<scope-slug>-<state>.png` |

Reports are append-only but their images are prune-to-latest: an older report references the
same stable path and so renders with the most recent capture. The report *text* is the record
of truth; the image is a best-effort current view. Every reference is an inline embed
(`![alt](./assets/…)`), always relative and under `./assets/`.

## 10.4 Enforcement — instruct + light validation

The skills mandate the capture and assembly; `validate_report.py` adds only light checks
(`schema == 2`, and — *if* a `## Walkthrough` section exists — every image path is relative
and under `./assets/`). It does **not** require the section to exist, nor that a file is on
disk: a missing PNG never fails a run. This matches the suite's "no silent gaps" ethic without
being brittle against the fixtures, which carry no real images.

## 10.5 Acceptance criteria (Definition of Done)

- [ ] The report contract (§3.4 / `report-contract.md`) is at `schema: 2` with the
      `## Walkthrough` section and asset-naming rule documented; `validate_report.py` requires
      `schema == 2` and light-checks walkthrough image paths.
- [ ] `audit-cuj` captures every replayed step in live/hybrid mode with the stable name and
      assembles a `## Walkthrough`; static runs emit none.
- [ ] `usability-audit` names its key-state captures by the convention, embeds them inline,
      and assembles a `## Walkthrough` in live/hybrid mode.
- [ ] Both personas describe inline-embed + walk-through assembly.
- [ ] Fixtures validate at `schema: 2`; at least one cuj and one usability fixture carry a
      `## Walkthrough`; a walkthrough with a non-`./assets/` image path is rejected.
- [ ] `audit_safety.py` is unchanged and still confines writes to `.ux/audits/`.
- [ ] README / AGENTS / CHANGELOG updated; `plugin.json` at 0.4.0.

## 10.6 The HTML companion (delivered, 0.5.0)

> The richer view deferred in §10.1. A **derived** HTML rendering of the Markdown reports —
> the contract, `validate_report.py`, `index.md`, and the roll-up are unchanged; **no schema
> bump.** The engine is a script (`scripts/render_report_html.py`); the on-demand UX is a thin
> command + skill.

**What it produces.** For each `.ux/audits/*.md`, a self-contained `<stem>.html` beside it:
a frontmatter header, a severity-cell summary, findings as severity-badged cards, and — for a
report with a `## Walkthrough` — an **interactive flipbook** (prev/next, keyboard, dots),
grouped per CUJ journey. A `rollup-*.md` renders as a **go/no-go dashboard** (verdict banner +
per-auditor severity matrix, links repointed to the `.html` views); `index.md` renders as a
stable `index.html` landing page. Special cases: a cuj `total: 0` renders a verified-pass (or
"nothing verified") banner; dev-lab/static runs get a provenance banner; a report with no
walkthrough surfaces its Evidence screenshots (embeds **and** bare `(./assets/…)` paths) as a
gallery.

**Invariants.** *Self-contained* — inline CSS + images as `data:` URIs, no external references,
opens offline (a test asserts it). *Deterministic* — identical input ⇒ byte-identical output,
so re-rendering never churns a diff. *Derived* — the Markdown is the source of truth; the
renderer never edits a report, the contract, or host code. *Confined* — the `.html` is written
under `.ux/audits/`, so `audit_safety.py` is untouched.

**Components.** The engine `scripts/render_report_html.py` (auto path: the audit skills call it
as their final step). The on-demand path: `/ux-review` command → `render-report` skill (no
persona — a mechanical transform holds no point of view), with `evals/cases/render-report.json`
and hand-wired `check_render_report_skill` / `check_ux_review_command` in `tests/test_components.py`.

### 10.6 Acceptance criteria (Definition of Done)

- [ ] `scripts/render_report_html.py` renders each report/roll-up/index to a self-contained,
      deterministic `.html`; `tests/test_render_html.py` asserts self-contained + deterministic +
      flipbook/findings tracking + the cuj pass-vs-nothing banners.
- [ ] The `usability-audit`, `audit-cuj`, and `ux-audit` skills render the companion as their
      final step; writes stay under `.ux/audits/` (safety unaffected).
- [ ] `/ux-review` + the `render-report` skill render existing reports on demand; both are
      covered by an eval case (routing green) and a hand-wired component check.
- [ ] README / CHANGELOG updated; `plugin.json` at **0.5.0**.
