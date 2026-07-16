# PLAN — Usability Auditor

Implementation plan for [`SPEC.md`](../SPEC.md). Read-only planning artifact — no code
changes are made by this document.

- **Spec:** [SPEC.md](../SPEC.md)
- **Date:** 2026-07-15
- **Approach:** vertical slices — each phase delivers one complete, runnable path, then
  the next thickens it. No horizontal "build all references, then all personas" layering.

---

## 1. What we're building (recap)

The plugin's standard triad — **persona** (`agents/usability-auditor.md`), **skill**
(`skills/usability-audit/SKILL.md`), **command** (`commands/usability-audit.md`) — plus
the **shared `.ux/audits` report contract** every future suite auditor (a11y, perf)
inherits. Findings-only: it never edits host application code.

## 2. Prior art that shapes the plan

- **v1 sibling repo** (`../ux-agent-skills`) already ships auditor personas
  (`accessibility-auditor`, `performance-auditor`) with YAML frontmatter + trigger
  phrases, and a `/ux-ship` parallel fan-out that merges auditor reports into a go/no-go.
  Our shared contract is what makes that fan-out possible for the suite. We reboot in v2
  rather than copy, but we match the frontmatter and reporting conventions.
- **Render-vs-source honesty rule** (from the ecosystem web-performance-auditor's
  "metric-honesty rule" and v1's `contract-vs-render`): a usability claim about what a
  user *perceives at runtime* (system-status feedback, error recovery, interaction
  latency) cannot be asserted from static source. **In static mode, such findings are
  labeled `potential — unverified` and the report says why.** This is a first-class
  requirement, folded into Slice 1 and enforced in Slice 4.

## 3. Dependency graph

```
                 ┌─────────────────────────┐
                 │ Report contract (§3.4)  │  ← foundational, shared by whole suite
                 └───────────┬─────────────┘
                             │
   references/ (Nielsen ✓)   │
        │                    │
        ▼                    ▼
   ┌─────────┐        ┌──────────────┐        ┌──────────────┐
   │ Persona │◄───────│    Skill     │◄───────│   Command    │
   └─────────┘        └──────────────┘        └──────────────┘
        ▲                    ▲
        │                    │
   3 more framework refs     hybrid live-mode + index + validation
   (Shneiderman, AI, NPCIS)  (Slices 2 & 4)
        (Slice 3)
                             │
                             ▼
                     ┌──────────────┐
                     │ Docs/Release │  ← depends on everything
                     └──────────────┘
```

**Leaf inputs:** the report contract + Nielsen reference (already in `references/`).
**Everything downstream** builds on those. Command is the last wiring step per slice.

## 4. Vertical slices (phases)

Each slice is independently demoable end-to-end.

### Phase 1 — Walking skeleton (static, Nielsen-only) ⭐ MVP
The thinnest complete path: `/ux-agent-skills:usability-audit <repo-path>` reads host
source, applies **Nielsen's 10** only, and writes ONE valid report to `.ux/audits/`
conforming to the shared contract — including the render-vs-source honesty labeling.
Proves the contract, the write location, and the safety invariant before any breadth.

**Delivers:** report contract doc, minimal persona, static-path skill, command wiring,
a real report file. **Frameworks:** Nielsen only. **Mode:** static only.

→ **CHECKPOINT A** — human reviews a real generated report + the contract before we
  invest in breadth. Cheapest point to correct format/severity/tone.

### Phase 2 — Live & hybrid evidence
Add browser-MCP live inspection: navigate a target URL, screenshot key states into
`.ux/audits/assets/`, exercise flows, read the a11y/DOM tree. Implement the hybrid
auto-selection logic and record actual `mode` in frontmatter. Runtime heuristics now get
*verified* (not `potential`) findings. Ask-first gates on server start / navigation.

**Delivers:** live + hybrid skill paths, asset capture, mode detection.

### Phase 3 — Full four-framework stack
Author the three remaining skill-local references (`shneiderman-8`,
`ai-design-heuristics`, `npcis`) and expand persona knowledge base + skill evaluation to
apply all four, mapping every finding to its exact framework citation.

**Delivers:** complete framework coverage per SPEC §4.

→ **CHECKPOINT B** — human reviews a full-stack live report for finding quality,
  framework attribution accuracy, and false-positive rate.

### Phase 4 — Contract hardening & suite portability
Rolling `index.md` append; frontmatter schema validation (counts == findings);
coverage/appendix honesty (no silent gaps); idempotency (new file, never overwrite);
the safety invariant test; and a mock second auditor (`auditor: accessibility`) proving
the contract is portable across the suite.

**Delivers:** the guarantees in SPEC §5.2 + §3.4 index behavior.

### Phase 5 — Docs & release
README section (auditor + shared report contract), CHANGELOG entry, `plugin validate`,
and a dogfood run against a real sample flow.

→ **CHECKPOINT C** — go/no-go: dogfood report is genuinely useful; DoD (SPEC §7) met.

## 5. Slicing rationale

- **Contract first, in Phase 1** — it's the suite-wide interface; getting it wrong later
  is expensive. Phase 1 already emits a report, so we validate the contract immediately.
- **Static before live** — static is the zero-dependency path (no running app, no browser
  gating), so it's the fastest route to a demoable report and to locking the format.
- **Breadth (frameworks) after depth (one working path)** — avoids authoring four
  reference files before we know the report shape is right.
- **Hardening after behavior** — validation/index/portability are meaningful only once
  reports actually exist.

## 6. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| Report format churns after references exist → rework | Lock format at Checkpoint A, before Phase 3 breadth. |
| Auditor edits host code (violates findings-only) | Safety-invariant test in Phase 4; boundary stated in persona + skill from Phase 1. |
| Static-mode findings over-assert runtime behavior | Render-vs-source honesty rule enforced from Phase 1; verified in Phase 4. |
| Browser gating (auth, no dev server) blocks live mode | Hybrid auto-fallback to static; ask-first gates; coverage gaps logged, never silent. |
| Contract not actually reusable by a11y/perf | Mock-second-auditor portability test in Phase 4. |
| Over-copying v1 instead of a clean v2 reboot | Treat v1 as pattern reference only; author fresh against this spec. |

## 7. Verification spine (applies every phase)

After any phase that runs an audit: `git status` in the host repo shows changes **only**
under `.ux/audits/`. Report frontmatter parses; `summary` counts equal findings by
severity. Every finding has evidence + framework citation + fix. No fabricated findings.

## 8. Out of scope (deferred to future suite work)

Meta-command fan-out (`/ux-agent-skills:audit` running all auditors), report
diffing/regression tracking across runs, retention/pruning. The contract enables all
three later; none are built now.
