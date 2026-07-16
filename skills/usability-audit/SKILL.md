---
name: usability-audit
description: Run an expert heuristic usability evaluation of a host app and write a severity-scored report to .ux/audits. Use for "usability audit", "heuristic evaluation", "UX audit", or "usability review".
---

# Usability Audit

Drive the [`usability-auditor`](../../agents/usability-auditor.md) persona through a
complete heuristic evaluation and emit a report that conforms to the
[shared report contract](./references/report-contract.md).

**Frameworks (four):** [Nielsen's 10](./references/nng-ux-heuristics.md),
[Shneiderman's 8](./references/shneiderman-8.md),
[AI Design Heuristics](./references/ai-design-heuristics.md) (AI features only), and
[NPCIS](./references/npcis.md). Findings are **grouped and de-duplicated by framework** —
one issue, one finding, attributed to its primary framework (see step 4).

**Evaluation modes:** `static` (read source), `live` (drive the running app in a
browser), and `hybrid` (both). The modes differ only in how evidence is gathered — the
frameworks, severity rubric, and report format are identical. Mode is auto-selected by
default (see step 1); `--mode` forces one.

---

## Inputs

- `target` — a URL (live mode) or a repo path/glob (static mode). If omitted, infer from
  the running dev server or the repo's UI source.
- `--scope` — narrow the audit to a flow/area (e.g. "checkout"). Optional.
- `--mode static | live | hybrid` — force an evidence-gathering mode. Optional; default is
  auto (see step 1).

## Workflow

1. **Scope the audit and select the mode.** Resolve `target` and `--scope`, and identify
   the host repo root (where `.ux/` will live). Then choose the mode:
   - If `--mode` is given, use it.
   - Otherwise **auto-select**: **prefer live** when a target URL is given or a dev server
     is already running/detectable; **fall back to static** when no running app is
     reachable. Use **hybrid** when both a URL and the source are available — inspect the
     render for runtime behavior and use the source to locate the `file:line` a fix
     belongs to.
   - Record the mode you **actually** used (not the one requested) in the report
     frontmatter and appendix — e.g. a requested `live` that fell back because no server
     was reachable is reported as `static`, with the reason.
   List what you intend to cover.

2. **Read the frameworks.** Load all four lenses —
   [Nielsen's 10](./references/nng-ux-heuristics.md),
   [Shneiderman's 8](./references/shneiderman-8.md),
   [AI Design Heuristics](./references/ai-design-heuristics.md), and
   [NPCIS](./references/npcis.md) — plus the
   [report contract](./references/report-contract.md). Cite the exact rule from the
   reference; don't recite from memory. If the surface has no AI features, mark the AI
   lens not-applicable rather than inventing findings.

3. **Gather evidence** using the selected mode:

   ### Static mode (source)
   Read the in-scope components, markup, routes, and copy. Sweep each framework's rules
   for violations — Nielsen (feedback, real-world language, undo/exit, consistency, error
   prevention, recognition, accelerators, minimalism, error text, help); Shneiderman
   (closure, locus of control, reversal); NPCIS (navigation flow, presentation hierarchy,
   content clarity, and the Strategy/goal-alignment lens); and, if the surface has AI
   features, the AI heuristics (expectation-setting, explainability, correction paths).
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

4. **De-duplicate, attribute, and grade.** The four frameworks overlap, so the same issue
   often surfaces under several (e.g. missing feedback = Nielsen #1 = Shneiderman #3 =
   NPCIS Interaction). Merge those into **one finding**, attributed to the **primary**
   framework, noting the corroborating ones in the Framework Violation field — never file
   a defect four times. Then apply the severity rubric from the contract (**omit severity
   0**) and capture the five fields per finding: Issue Description, Framework Violation
   (primary + corroborating), Severity, Evidence, Recommended Fix. Group findings by
   framework in the report body if it aids readability; the severity ordering in the
   prioritized-fix list still governs.

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

7. **Append to the index.** Add one row for this run to `.ux/audits/index.md` — create the
   file with the contract's header if it doesn't exist. The index is **append-only**: add
   your row, never rewrite or reorder prior rows (they may belong to earlier runs or other
   auditors). The row records date, auditor, scope, and the four severity counts, linking
   to the report file.

8. **Self-check before finishing.** Ensure `summary` counts reconcile with the findings in
   the body and no `[sev0]` appears. Validate the report and index with
   [`scripts/validate_report.py`](../../scripts/validate_report.py) — `validate_report.py
   <report>` and `validate_report.py --index .ux/audits/index.md`. Then confirm the safety
   invariant with [`scripts/audit_safety.py`](../../scripts/audit_safety.py)
   `<host-repo>` — it must report all changes confined to `.ux/audits/`.

## Boundaries

- **Findings only.** Never edit, refactor, or "fix" host application code.
- **Never write outside `.ux/audits/`** in the host repo. That is the auditor's safety
  invariant; any other created/modified file is a failure.
- **Ask first** before starting a dev server, navigating a browser, installing anything,
  or reaching auth-gated screens.
- **Never fabricate** findings, severities, or evidence.

## Exit criteria (done when)

- A timestamped report exists under `.ux/audits/` and validates against the contract.
- One row was appended to `.ux/audits/index.md` (created if absent), with no prior rows
  rewritten.
- Every reported finding has a framework citation (primary + any corroborating), a 0–4
  severity, evidence, and a fix, with no issue filed under more than one finding.
- Runtime-perception findings are `verified` (live) or `potential — unverified` (static),
  matching the mode actually used.
- Live-mode screenshots are saved under `.ux/audits/assets/` and referenced by findings.
- The appendix names all in-scope areas that were not inspected.
- `git status` in the host repo shows changes only under `.ux/audits/`.
