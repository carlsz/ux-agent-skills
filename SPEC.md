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
- **Plugin:** `ux-agent-skills` v0.1.0

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
└── references/                       # original seed material (source of truth)
    └── ux-researcher.md                  # severity-report persona spec (0–4 scale)
```
> Skill-local `references/` are the eval frameworks the skill loads at run time. They live
> beside the skill so it is self-contained (atomic); the repo-level `references/` holds the
> original seed material the suite was derived from.

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
   - **Evidence** — screenshot path (`./.ux/audits/assets/…`), `file:line`, or repro steps.
   - **Recommended Fix** — actionable design guidance.
5. **Appendix** — mode, target, scope, frameworks applied, coverage notes / what was NOT
   inspected (no silent gaps).

### 3.4 Shared report contract (inherited by every future auditor)
All auditors in the suite write to the same `.ux/audits/` directory and share this
frontmatter schema. Only `auditor` and `frameworks` differ between auditors.

```yaml
---
auditor: usability          # usability | accessibility | web-performance | …
schema: 1                    # report-contract version
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

### Severity rubric (0–4, from `references/ux-researcher.md`)
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
- Installing anything, or running host build/test scripts.
- Adding `.ux/` to the host's `.gitignore` (recommend, don't do silently).
- Writing outside `.ux/audits/` for any reason (e.g. saving screenshots elsewhere).

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
- **Screenshot assets** — confirm `.ux/audits/assets/` as the standard location for
  captured evidence images.
- **VCS treatment** — leave `.ux/` committed vs. ignored to the host team; auditor only
  recommends.
