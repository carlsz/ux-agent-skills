---
name: usability-audit
description: Run an expert heuristic usability evaluation of a host app and write a severity-scored report to .ux/audits. Use for "usability audit", "heuristic evaluation", "UX audit", or "usability review".
---

# Usability Audit

Drive the [`usability-auditor`](../../agents/usability-auditor.md) persona through a
complete heuristic evaluation and emit a report that conforms to the
[shared report contract](./references/report-contract.md).

**Phase 1 scope:** static (source-only) evaluation against
[Nielsen's 10 heuristics](./references/nng-ux-heuristics.md). Live/hybrid inspection
and the other three frameworks arrive in later phases — a `--mode live` request is
acknowledged as not-yet-supported and run as static.

---

## Inputs

- `target` — a path or glob within the host repo (static mode). If omitted, infer from
  the repo's UI source (components, routes, templates).
- `--scope` — narrow the audit to a flow/area (e.g. "checkout"). Optional.
- `--mode` — `static` only in Phase 1. `live`/`hybrid` are acknowledged but downgraded to
  static with a note in the report appendix.

## Workflow

1. **Scope the audit.** Resolve `target` and `--scope`. Identify the host repo root
   (where `.ux/` will live) and the UI source to inspect. List what you intend to cover.

2. **Read the frameworks.** Load [Nielsen's 10](./references/nng-ux-heuristics.md) and
   the [report contract](./references/report-contract.md). Do not recite heuristics from
   memory — cite the numbered heuristic from the reference.

3. **Inspect the source.** Read the in-scope components, markup, routes, and copy. For
   each Nielsen heuristic, look for violations: missing system-status feedback, jargon vs.
   real-world language, no undo/exit on destructive actions, inconsistency, missing error
   prevention, recall-over-recognition, no accelerators, clutter, unhelpful error text,
   absent help.

4. **Grade findings (0–4).** Apply the severity rubric from the contract. **Omit
   severity 0** — non-problems are not reported. For each real finding, capture the five
   fields: Issue Description, Framework Violation (exact Nielsen #), Severity, Evidence
   (`file:line`), Recommended Fix.

5. **Apply the render-vs-source honesty rule.** In static mode you are reading source, not
   a render. Any finding about *runtime perception* — system-status feedback, error
   recovery, interaction latency, transitions — must be labeled **`potential —
   unverified`** in its Evidence field, stating that no running app was observed. Never
   assert an unobserved runtime behavior as fact. If you cannot verify something, record
   it as skipped with the reason.

6. **Write the report.** Create `.ux/`, `.ux/audits/`, and `.ux/audits/assets/` in the
   host repo if absent. Write `.ux/audits/usability-<YYYYMMDD>-<HHMMSS>.md` (UTC clock)
   with the frontmatter schema, executive summary, prioritized fixes, findings, and an
   appendix. The appendix records `mode: static`, the frameworks applied, any downgraded
   `--mode` request, and — honestly — everything in scope you did **not** inspect.

7. **Self-check before finishing.** Ensure `summary` counts reconcile with the findings in
   the body and no `[sev0]` appears. Reports can be validated with
   [`scripts/validate_report.py`](../../scripts/validate_report.py).

## Boundaries

- **Findings only.** Never edit, refactor, or "fix" host application code.
- **Never write outside `.ux/audits/`** in the host repo. That is the auditor's safety
  invariant; any other created/modified file is a failure.
- **Ask first** before starting a dev server, navigating a browser, installing anything,
  or reaching auth-gated screens. (These matter more once live mode lands.)
- **Never fabricate** findings, severities, or evidence.

## Exit criteria (done when)

- A timestamped report exists under `.ux/audits/` and validates against the contract.
- Every reported finding has a Nielsen citation, a 0–4 severity, evidence, and a fix.
- Runtime-perception findings are labeled `potential — unverified` (static mode).
- The appendix names all in-scope areas that were not inspected.
- `git status` in the host repo shows changes only under `.ux/audits/`.
