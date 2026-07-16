# Shared `.ux/audits` Report Contract

The single output contract for the **ux-agent-skills auditor suite**. Every auditor —
usability (this suite's first), and future accessibility, web-performance, and others —
writes reports that conform to this contract, so their outputs are comparable, tracked in
one index, and consumable by a future fan-out meta-command.

Only two things differ between auditors: the `auditor` frontmatter value and the
`frameworks` list. Everything else here is fixed.

- **Schema version:** `1`
- **Machine-checked by:** [`scripts/validate_report.py`](../../../scripts/validate_report.py)
  (the executable form of this document — if the two ever disagree, reconcile them).

---

## 1. Where reports go

Reports are written into the **host** repository (the app being audited), never into the
plugin repo:

```
<host-repo>/
└── .ux/
    └── audits/
        ├── index.md                       # rolling index of every run (all auditors)
        ├── assets/                         # captured screenshots / evidence images
        ├── usability-20260715-143000.md    # one file per run
        └── usability-20260715-160000.md
```

- Create `.ux/`, `.ux/audits/`, and `.ux/audits/assets/` if absent.
- **Never** write outside `.ux/audits/`. This is the auditor's safety invariant.

## 2. File naming

```
<auditor>-<YYYYMMDD>-<HHMMSS>.md
```

Timestamp comes from the runtime clock, UTC. Reports are **append-only**: a new run
creates a new file — it never overwrites or deletes a prior report.

## 3. Frontmatter schema (required)

```yaml
---
auditor: usability          # usability | accessibility | web-performance | …
schema: 1                    # report-contract version — must be 1
version: 0.1.0               # version of the emitting auditor
date: 2026-07-15T14:30:00Z   # ISO-8601, UTC, from the runtime clock
target: https://localhost:3000/checkout   # URL (live) or repo path (static)
mode: hybrid                 # live | static | hybrid — the mode ACTUALLY used
scope: "checkout flow"       # human-readable audit scope
frameworks:                  # knowledge bases actually applied (non-empty)
  - nielsen-10               # usability set: nielsen-10, shneiderman-8,
  - shneiderman-8            #   ai-heuristics, npcis
summary:                     # counts MUST reconcile (see §5)
  total: 2
  sev4: 0                    # catastrophe
  sev3: 1                    # major
  sev2: 1                    # minor
  sev1: 0                    # cosmetic
---
```

**Rules**
- All nine keys are required.
- `schema` must equal `1`.
- `mode` ∈ {`live`, `static`, `hybrid`} and must reflect what actually ran, not what was
  requested.
- `date` must be ISO-8601 (a trailing `Z` is accepted).
- `frameworks` is a non-empty list drawn from the known set for that auditor.
- `summary` contains `total`, `sev4`, `sev3`, `sev2`, `sev1` — all non-negative integers.
  **`sev0` must NOT appear** (see §4).

## 4. Severity rubric (0–4)

From [`references/ux-researcher.md`](../../../references/ux-researcher.md).

| Score | Meaning | Appears in report? |
|-------|---------|--------------------|
| 0 | Not a usability problem | **No — omit entirely.** Not counted, not listed. |
| 1 | Cosmetic issue only | Yes |
| 2 | Minor usability problem | Yes |
| 3 | Major (high priority) | Yes |
| 4 | Catastrophe — must fix before release | Yes, top of the fix list |

Severity 0 is a *non-finding*: never emit a `[sev0]` heading and never add a `sev0`
summary key. Reporting non-problems dilutes the report.

## 5. Body layout

After the frontmatter, in order:

1. **`# <Auditor> Audit — <scope>`** — title.
2. **`## Executive summary`** — 2–4 sentences plus a severity-count table.
3. **`## Prioritized fixes`** — findings listed severity-high → low, each line linking to
   its finding below.
4. **`## Findings`** — one finding per **level-3 heading tagged with its severity**:

   ```markdown
   ### [sevN] <short title>          # N ∈ 1..4
   ```

   Each finding block MUST contain these five labelled fields:
   - **Issue Description:** what is broken or confusing.
   - **Framework Violation:** the exact heuristic / rule / dimension (e.g. "Nielsen #1 —
     Visibility of System Status").
   - **Severity:** the 0–4 score with a one-line justification.
   - **Evidence:** a screenshot path under `./assets/…`, a `file:line`, and/or repro
     steps. See the honesty rule in §6.
   - **Recommended Fix:** specific, actionable guidance.

5. **`## Appendix`** — `mode`, `frameworks applied`, and **`Coverage / not inspected`**:
   everything in scope that was NOT audited (auth-gated screens, unreachable routes),
   named explicitly. Silent gaps are prohibited.

### Count reconciliation
The number of `[sevN]` findings in the body must exactly equal `summary.total`, and the
per-severity body counts must match `summary.sev1..4`. The validator enforces this.

## 6. Render-vs-source honesty rule

A usability claim about what a user *perceives at runtime* — system-status feedback,
error recovery, interaction latency, transitions — cannot be proven by reading source.

- In **live**/**hybrid** mode, such findings observed on the render are stated normally.
- In **static** mode, they must be labelled **`potential — unverified`** inside the
  Evidence field, with the reason (no running app), never asserted as observed fact.
- Never fabricate evidence. If something could not be checked, say so; a `skipped, with
  reason` note beats a false pass.

## 7. `index.md` format

One row appended per run (create the file with this header if absent; never rewrite prior
rows):

```markdown
# Audit index

| Date (UTC) | Auditor | Scope | Sev4 | Sev3 | Sev2 | Sev1 | Report |
|------------|---------|-------|------|------|------|------|--------|
| 2026-07-15T14:30:00Z | usability | checkout flow | 0 | 1 | 1 | 0 | [report](usability-20260715-143000.md) |
```

## 8. Extending the contract for a new auditor

A new suite member (e.g. accessibility) reuses everything above and only:
1. sets its own `auditor` value,
2. defines its own `frameworks` vocabulary,
3. keeps the same severity rubric, body layout, and `index.md` row shape.

If a change to this contract is needed, bump `schema` and update
`scripts/validate_report.py` in the same change.
