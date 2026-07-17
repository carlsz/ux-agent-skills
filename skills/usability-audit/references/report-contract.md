# Shared `.ux/audits` Report Contract

The single output contract for the **ux-agent-skills auditor suite**. Every auditor —
usability (this suite's first), and future accessibility, web-performance, and others —
writes reports that conform to this contract, so their outputs are comparable, tracked in
one index, and consumable by a future fan-out meta-command.

Only two things differ between auditors: the `auditor` frontmatter value and the
`frameworks` list. Everything else here is fixed.

- **Schema version:** `2`
- **Machine-checked by:** [`scripts/validate_report.py`](../../../scripts/validate_report.py)
  (the executable form of this document — if the two ever disagree, reconcile them).

> **Schema history.** `2` added the optional `## Walkthrough` section (§5) and the
> `assets/` naming convention (§1). A report written by an older auditor at `schema: 1` is
> not rewritten to `2` — `schema` records the contract the report was born under. Only
> freshly emitted reports carry `2`.

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

### Asset naming (screenshots)

Screenshots captured in **live/hybrid** mode are saved under `.ux/audits/assets/` with
**stable, deterministic names** — one canonical name per thing captured, so a re-run
**overwrites** rather than accumulates. This bounds the directory by what a run captures
(journeys × steps, or the key states of a flow), not by the number of runs. Reports are
append-only, but their images are prune-to-latest: an older report references the same
stable path and therefore renders with the most recent run's capture of that thing — the
report *text* is the record of truth; the image is a best-effort current view.

| Auditor | What | Name |
|---------|------|------|
| cuj | a journey step | `cuj-<id>-step-<n>.png` (e.g. `cuj-001-step-2.png`) |
| cuj | criteria / other evidence | `cuj-<id>-<slug>.png` (e.g. `cuj-001-after-reload.png`) |
| usability (and other flow auditors) | a key state | `<auditor>-<scope-slug>-<state>.png` (state ∈ `initial`, `mid-flow`, `success`, `error`, `empty`) |

Reference every image from the body with an **inline embed** — `![alt](./assets/<name>.png)`
— never a bare path, so it renders in Markdown viewers. Paths are always relative and under
`./assets/`.

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
schema: 2                    # report-contract version — must be 2
version: 0.1.0               # the EMITTING PLUGIN's version — read it at run time from
                             # .claude-plugin/plugin.json. Never copy this number.
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
- `schema` must equal `2`.
- **`version` is read from `.claude-plugin/plugin.json` at run time, never copied from this
  document or from a fixture.** It records *what emitted this report*, which is why no
  validator checks it: a report written by 0.1.0 says `0.1.0` forever, and rewriting that
  later would be falsifying a historical fact. The example above and the fixtures under
  `tests/fixtures/valid/` therefore carry the version that emitted *them* — those numbers are
  history, not a template. A live run in 2026-07 caught this the hard way: given only
  `# version of the emitting auditor` and a `0.1.0` sitting beside it, the auditor copied the
  literal while the plugin was at 0.2.0. It did exactly what it was told; the instruction was
  the bug. Fixtures teach, so an example number needs to say where the real one comes from.
- `mode` ∈ {`live`, `static`, `hybrid`} and must reflect what actually ran, not what was
  requested.
- `date` must be ISO-8601 (a trailing `Z` is accepted).
- `frameworks` is a non-empty list drawn from the known set for that auditor.
- `summary` contains `total`, `sev4`, `sev3`, `sev2`, `sev1` — all non-negative integers.
  **`sev0` must NOT appear** (see §4).

## 4. Severity rubric (0–4)

Based on [Nielsen's severity ratings for usability problems](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/).

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

5. **`## Walkthrough`** *(optional; live/hybrid only)* — a rendered visual sequence of the
   captured screenshots. See below.
6. **`## Appendix`** — `mode`, `frameworks applied`, and **`Coverage / not inspected`**:
   everything in scope that was NOT audited (auth-gated screens, unreachable routes),
   named explicitly. Silent gaps are prohibited.

### The `## Walkthrough` section

A visual walk-through of the run, built from the screenshots captured in **live/hybrid**
mode. It is **optional and omitted in static mode** — with no running app there is nothing
to capture, so its absence there is correct, not a coverage gap. Each image is an inline
embed under `./assets/` (see §1 naming). The section carries no severity headings, so it
does not affect finding counts (§ Count reconciliation).

Two shapes, by auditor:

- **cuj** — one `### Step <n> — <action>` per journey step, in `n` order (a step captured
  whether it passed or failed), each with its screenshot and a one-line
  expected-vs-observed:

  ```markdown
  ## Walkthrough

  ### Step 1 — Click the new-task input
  ![CUJ-001 step 1](./assets/cuj-001-step-1.png)
  > Expected: input takes focus, placeholder "What needs doing?". Observed: match.

  ### Step 2 — Type 'Buy milk', press Enter
  ![CUJ-001 step 2](./assets/cuj-001-step-2.png)
  > Expected: row appears at top, input clears. Observed: match.
  ```

- **usability (and other flow auditors)** — one `### <state>` per captured key state
  (`Initial`, `Mid-flow`, `Success`, `Error`, `Empty`):

  ```markdown
  ## Walkthrough

  ### Initial
  ![checkout initial](./assets/usability-checkout-initial.png)
  ```

Every image path in this section must be relative and under `./assets/` — the validator
rejects `http(s)://`, absolute, or `../`-escaping paths. It does **not** require the section
to exist, nor that the file is present on disk.

### Count reconciliation
The number of `[sevN]` findings in the body must exactly equal `summary.total`, and the
per-severity body counts must match `summary.sev1..4`. The validator enforces this.

## 6. Render-vs-source honesty rule

A usability claim about what a user *perceives at runtime* — system-status feedback,
error recovery, interaction latency, transitions — cannot be proven by reading source.

- In **live**/**hybrid** mode, such findings observed on the render are stated normally; a
  captured screenshot — the same image the `## Walkthrough` (§5) embeds — is the preferred
  backing, referenced inline from the Evidence field.
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
2. defines its own `frameworks` vocabulary — register it in `FRAMEWORKS_BY_AUDITOR` in
   [`scripts/validate_report.py`](../../../scripts/validate_report.py) (an unregistered
   auditor still validates, but its frameworks are only checked for non-emptiness),
3. keeps the same severity rubric, body layout, and `index.md` row shape.

Auditors share one `.ux/audits/` directory and one `index.md`; reports from different
auditors coexist and are distinguished by the `auditor` field. If a change to this
contract is needed, bump `schema` and update `scripts/validate_report.py` in the same
change.
