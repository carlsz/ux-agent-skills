---
name: accessibility-audit
description: Audit a host app against WCAG 2.2 and write a priority-scored accessibility report to .ux/audits. Invokes the accessibility-auditor persona via the accessibility-audit skill.
argument-hint: "[target] [--scope <area>] [--mode static|live|hybrid]"
---

# /accessibility-audit

Run a WCAG 2.2 accessibility inspection and write a durable, priority-scored report to
`.ux/audits/` in the host repo. Thin entry point — the
[`accessibility-audit`](../skills/accessibility-audit/SKILL.md) skill does the work,
driving the [`accessibility-auditor`](../agents/accessibility-auditor.md) persona.

## Arguments

`$ARGUMENTS`:

- **`target`** — a URL (live) or a repo path/glob (static). Omit to infer from the running
  dev server or the repo's UI source. Examples:
  `/accessibility-audit https://localhost:3000`, `/accessibility-audit src/checkout`,
  `/accessibility-audit` (whole app).
- **`--scope <area>`** — narrow the audit to a flow or area, e.g. `--scope checkout`.
- **`--mode static | live | hybrid`** — force an evaluation mode. Optional; the skill
  **auto-selects** by default: prefer `live` when a URL or running dev server is
  available, fall back to `static` otherwise, and use `hybrid` when both the render and
  source are reachable. The mode actually used is recorded in the report.

  **The mode is not cosmetic here.** Most WCAG criteria are runtime properties — contrast
  against the computed background, focus order, focus visibility, target size, live-region
  announcements — so a `static` run finds markup that looks wrong and **cannot establish
  conformance**. It says so in its own appendix. Prefer `live` when you can.

## Behavior

1. Parse `target`, `--scope`, and `--mode` from `$ARGUMENTS`.
2. Invoke the `accessibility-audit` skill with the resolved scope.
3. The skill reads the accessibility tree, tabs the flow, measures what the criteria state
   as numbers, grades each failure (`P0`-`P3`) by **impact on the user it affects** rather
   than by conformance level, scores one `health` item per criterion checked, and writes
   `.ux/audits/accessibility-<timestamp>.md` conforming to the
   [report contract](../skills/usability-audit/references/report-contract.md).
4. Print the report path, the priority roll-up, and the health score.

## Guarantees

- **Findings only** — never edits host application code, however small the fix looks.
- **Writes only under `.ux/audits/`** in the host repo.
- A conformance level is cited as evidence, never used as the priority.
- Every failed criterion appears as a finding, at whatever priority it earned.
- Static-mode findings about runtime behaviour are labeled `potential — unverified`.
- An automated-tool pass is never reported as a conformance claim.
