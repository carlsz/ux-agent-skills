---
name: usability-audit
description: Run an expert heuristic usability audit of a host app and write a severity-scored report to .ux/audits. Invokes the usability-auditor persona via the usability-audit skill.
argument-hint: "[target] [--scope <area>] [--mode static]"
---

# /usability-audit

Run a heuristic usability evaluation and write a durable, severity-scored report to
`.ux/audits/` in the host repo. Thin entry point — the
[`usability-audit`](../skills/usability-audit/SKILL.md) skill does the work, driving the
[`usability-auditor`](../agents/usability-auditor.md) persona.

## Arguments

`$ARGUMENTS`:

- **`target`** — a repo path or glob to audit (static mode). Omit to infer the host app's
  UI source from the repo. Examples: `/usability-audit src/checkout`,
  `/usability-audit` (whole app).
- **`--scope <area>`** — narrow the audit to a flow or area, e.g. `--scope checkout`.
- **`--mode static`** — evaluation mode. **Phase 1 supports `static` only**; a `live` or
  `hybrid` request is acknowledged and downgraded to static, with a note in the report
  appendix. (Live/hybrid inspection lands in a later phase.)

## Behavior

1. Parse `target`, `--scope`, and `--mode` from `$ARGUMENTS`.
2. Invoke the `usability-audit` skill with the resolved scope.
3. The skill applies Nielsen's 10 heuristics to the in-scope source, grades findings
   (0–4, omitting sev 0), and writes `.ux/audits/usability-<timestamp>.md` conforming to
   the [report contract](../skills/usability-audit/references/report-contract.md).
4. Print the report path and the severity roll-up.

## Guarantees

- **Findings only** — never edits host application code.
- **Writes only under `.ux/audits/`** in the host repo.
- Static-mode findings about runtime perception are labeled `potential — unverified`.
