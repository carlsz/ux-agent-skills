---
name: usability-audit
description: Run an expert heuristic usability evaluation of a host app and write a severity-scored report to .ux/audits. Use for "usability audit", "heuristic evaluation", "UX audit", or "usability review".
---

# Usability Audit

Drive the [`usability-auditor`](../../agents/usability-auditor.md) persona through a
complete heuristic evaluation and emit a report that conforms to the
[shared report contract](./references/report-contract.md).

**Framework scope:** [Nielsen's 10 heuristics](./references/nng-ux-heuristics.md). (The
other three frameworks — Shneiderman, AI heuristics, NPCIS — arrive in a later phase.)

**Evaluation modes:** `static` (read source) and `live` (drive the running app in a
browser). Pick with `--mode`; hybrid auto-selection lands in a follow-up task. The two
modes differ only in how evidence is gathered — the frameworks, severity rubric, and
report format are identical.

---

## Inputs

- `target` — a URL (live mode) or a repo path/glob (static mode). If omitted, infer from
  the running dev server or the repo's UI source.
- `--scope` — narrow the audit to a flow/area (e.g. "checkout"). Optional.
- `--mode static | live` — how to gather evidence. Default `static`.

## Workflow

1. **Scope the audit.** Resolve `target`, `--scope`, and `--mode`. Identify the host repo
   root (where `.ux/` will live). List what you intend to cover.

2. **Read the frameworks.** Load [Nielsen's 10](./references/nng-ux-heuristics.md) and the
   [report contract](./references/report-contract.md). Cite the numbered heuristic from
   the reference — don't recite from memory.

3. **Gather evidence** using the selected mode:

   ### Static mode (source)
   Read the in-scope components, markup, routes, and copy. For each Nielsen heuristic look
   for violations: missing system-status feedback, jargon vs. real-world language, no
   undo/exit on destructive actions, inconsistency, missing error prevention,
   recall-over-recognition, no accelerators, clutter, unhelpful error text, absent help.
   Capture `file:line` for each.

   ### Live mode (render)
   Inspect the running app through a browser (browser MCP). **Ask the user first** before
   starting or restarting a dev server and before navigating the browser to any URL — do
   not launch a server or navigate unprompted.
   - **Navigate** to the target URL and walk the in-scope flow step by step.
   - **Screenshot** each key state (initial, mid-flow, success, error, empty) and save the
     images under `.ux/audits/assets/`; reference them by relative path in findings.
   - **Exercise** real interactions — submit forms, trigger errors, click destructive
     actions — and observe the actual response and timing.
   - **Read the accessibility / DOM tree** to confirm labels, roles, and focus order.
   - Do not enter credentials or bypass auth to reach gated screens; record those as
     skipped with the reason.

4. **Grade findings (0–4).** Apply the severity rubric from the contract. **Omit severity
   0.** For each real finding capture the five fields: Issue Description, Framework
   Violation (exact Nielsen #), Severity, Evidence, Recommended Fix.

5. **Apply the render-vs-source honesty rule.** A claim about what a user *perceives at
   runtime* — system-status feedback, error recovery, interaction latency, transitions —
   is only as strong as the evidence behind it:
   - In **live** mode, such a finding observed on the render is stated as **verified**,
     backed by a screenshot or observed interaction.
   - In **static** mode, it must be labeled **`potential — unverified`** in the Evidence
     field, stating that no running app was observed. Never assert an unobserved runtime
     behavior as fact. If something couldn't be checked, record it as skipped with the
     reason — a false pass is worse than an honest gap.

6. **Write the report.** Create `.ux/`, `.ux/audits/`, and `.ux/audits/assets/` in the
   host repo if absent. Write `.ux/audits/usability-<YYYYMMDD>-<HHMMSS>.md` (UTC clock)
   with the frontmatter schema, executive summary, prioritized fixes, findings, and an
   appendix. The appendix records the `mode` used, the frameworks applied, and — honestly
   — everything in scope you did **not** inspect.

7. **Self-check before finishing.** Ensure `summary` counts reconcile with the findings in
   the body and no `[sev0]` appears. Validate with
   [`scripts/validate_report.py`](../../scripts/validate_report.py).

## Boundaries

- **Findings only.** Never edit, refactor, or "fix" host application code.
- **Never write outside `.ux/audits/`** in the host repo. That is the auditor's safety
  invariant; any other created/modified file is a failure.
- **Ask first** before starting a dev server, navigating a browser, installing anything,
  or reaching auth-gated screens.
- **Never fabricate** findings, severities, or evidence.

## Exit criteria (done when)

- A timestamped report exists under `.ux/audits/` and validates against the contract.
- Every reported finding has a Nielsen citation, a 0–4 severity, evidence, and a fix.
- Runtime-perception findings are `verified` (live) or `potential — unverified` (static),
  matching the mode actually used.
- Live-mode screenshots are saved under `.ux/audits/assets/` and referenced by findings.
- The appendix names all in-scope areas that were not inspected.
- `git status` in the host repo shows changes only under `.ux/audits/`.
