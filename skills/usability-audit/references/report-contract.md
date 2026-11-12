# Shared `.ux/audits` Report Contract

The single output contract for the **ux-agent-skills auditor suite**. Every auditor —
usability (this suite's first), and future accessibility, web-performance, and others —
writes reports that conform to this contract, so their outputs are comparable, tracked in
one index, and consumable by a future fan-out meta-command.

Only two things differ between auditors: the `auditor` frontmatter value and the
`frameworks` list. Everything else here is fixed.

- **Schema version:** `3` (schema `2` remains valid — see below)
- **Machine-checked by:** [`scripts/validate_report.py`](../../../scripts/validate_report.py)
  (the executable form of this document — if the two ever disagree, reconcile them).

> **Schema history.** `2` added the optional `## Walkthrough` section (§5) and the
> `assets/` naming convention (§1). `3` changed the *scored* field from severity to
> **priority**: `summary` counts `P0..P3`, findings are headed `### [PN]`, and a
> `Priority` field joins the five. Severity did not go away — it is still assessed by §4's
> three factors and still reported per finding; it is no longer what the report is ordered
> and counted by.
>
> A report is **never rewritten to a later schema** — `schema` records the contract it was
> born under, so a `2` stays a `2` forever and the validator keeps a permanent schema-2
> path. Only freshly emitted reports carry `3`.

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
- A derived, self-contained `<report>.html` companion may sit beside each `<report>.md`
  (rendered by [`render_report_html.py`](../../../scripts/render_report_html.py); see SPEC §10.6).
  The Markdown remains the source of truth — this contract governs the `.md`, and the `.html` is
  a view of it, never validated against or in place of it.

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
  P0: 0                      # blocks the task
  P1: 1                      # significant difficulty / WCAG AA
  P2: 1                      # workaround exists
  P3: 0                      # no effect on completion
---
```

**Rules**
- All nine keys are required.
- `schema` must equal `3` for a freshly emitted report. `2` is still accepted and still
  validated, in its own vocabulary — see *Schema history* above.
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
- `summary` contains `total`, `P0`, `P1`, `P2`, `P3` — all non-negative integers. Mixing
  the two vocabularies is rejected: `sevN` keys in a schema-3 summary, or `PN` keys in a
  schema-2 one, are a half-migrated report and fail validation.
  *(Schema 2: `total`, `sev4`, `sev3`, `sev2`, `sev1`, and **`sev0` must NOT appear** — §4.)*

## 4. Rating: priority is scored, severity is its input

A finding carries two ratings, doing different jobs. **Priority** (`P0`–`P3`) is the scored
one — it orders the report, fills `summary`, and is what the finding heading carries.
**Severity** (`0`–`4`) is the assessment of the defect itself, reported per finding so a
reader can check the call and overrule it, but never aggregated.

> *Schema 2 scored severity and had no priority. That contract is unchanged and still
> validated; everywhere below that names `PN`, a schema-2 report reads `sevN`.*

### Priority (P0–P3) — the scored scale

| Rank | Criterion | When to fix |
|------|-----------|-------------|
| **P0** | Blocks the task — no workaround exists | Immediately |
| **P1** | A workaround is required but costly or non-obvious; the flow appears to succeed but doesn't; or a WCAG AA failure | Before release |
| **P2** | An obvious workaround exists; task completion is unaffected | Next improvement pass |
| **P3** | No effect on task completion — cosmetic | After higher priorities |

There is no rank below `P3`. A problem that changes no user behaviour is **not filed at
all**, which is the severity rubric's job to determine — see the 0-vs-1 test below.

### Severity (0–4) — the reported input

Based on [Nielsen's severity ratings for usability problems](https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/).

| Score | Meaning | Appears in report? |
|-------|---------|--------------------|
| 0 | Not a usability problem | **No — omit entirely.** Not counted, not listed. |
| 1 | Cosmetic issue only | Yes |
| 2 | Minor usability problem | Yes |
| 3 | Major (high priority) | Yes |
| 4 | Catastrophe — must fix before release | Yes, top of the fix list |

#### How to land on a score

The table says what the scores *mean*. These three factors are how you *derive* one — Nielsen's
rating is a blend of them, not a single impression. Rate each, then combine:

- **Frequency** — how many users meet this, and how often? The same defect on the one path
  everyone takes outranks it on a path few reach.
- **Impact** — how hard is it to overcome once met? Blocked with no workaround sits at the top
  of this factor; "annoying, but obvious what to do instead" sits at the bottom.
- **Persistence** — a one-time obstacle a user learns around, or one that bites on every visit?

**The Severity field's justification must name these factors**, not merely assert a number.
`S3 — major` is not a justification. `S3 — every keyboard user meets it (frequency), there
is no way around it (impact), and it recurs on every visit (persistence)` is.

> **Why the method is load-bearing.** Nielsen's ratings were designed to be *averaged across
> 3–5 independent evaluators*, and that averaging is what smooths the margins — three raters at
> 0, 1, 0 produce 0.33, a soft signal rather than a verdict. A single auditor has no smoothing
> and must pick a side, so the factors have to do the work the averaging used to do. Without
> them the margin is a coin-flip, and two runs over the same app disagree.

**The 0-vs-1 test.** Severity 1 means a user *notices*. Severity 0 means **no user behaviour
changes** — if you cannot name what a user does differently because of it, it is a 0.

Severity 0 is a *non-finding*: it is never filed, at any priority. In a schema-2 report, never
emit a `[sev0]` heading and never add a `sev0` summary key. Reporting non-problems dilutes the
report.

### Two rules that keep the scale usable

- **Keep the bottom of the scored scale short.** A long tail of cosmetic findings buries the
  ones that matter. `P3` (schema 2: `sev1`) is for what genuinely warrants a reader's attention
  — not for everything that survived the 0-vs-1 test. A report whose bulk is `P3` has spent the
  reader's attention before they reach the findings that needed it.
- **The top of the scale is rare.** Catastrophe is the rarest rating, not the default for
  anything serious. A report where most findings are `P0` (schema 2: `sev4`) has mis-rated
  rather than found a pile of catastrophes — re-derive each from the three factors, and
  re-check the P ladder's criterion, before filing it.

## 5. Body layout

After the frontmatter, in order:

1. **`# <Auditor> Audit — <scope>`** — title.
2. **`## Executive summary`** — 2–4 sentences plus a priority-count table.
3. **`## Prioritized fixes`** — findings listed `P0` → `P3`, one line each, linking to the
   finding below:

   ```markdown
   - **P1** — [Seeding a blank task fails silently](#p1-seeding-a-blank-task-fails-silently)
   ```

   The link **text** may name the fix (that is this section's subject); the **anchor** is
   always the finding heading's slug — lowercased, spaces to hyphens, everything else
   dropped: `### [P1] Seeding a blank task fails silently` becomes
   `#p1-seeding-a-blank-task-fails-silently`. `[[P1] <title>](#anchor)` is equivalent and
   also renders; it is spelled out here because the link *was* the one thing fixtures kept
   leaving out, and because a link whose text carries brackets went unparsed by the HTML
   companion until 0.7.0 — so an auditor following the contract got raw Markdown in the
   one section built from links. With no findings, the section reads `None — no findings.`
4. **`## Findings`** — one finding per **level-3 heading tagged with its priority**:

   ```markdown
   ### [PN] <short title>            # N ∈ 0..3   (schema 2: ### [sevN], N ∈ 1..4)
   ```

   Each finding block MUST contain these six labelled fields:
   - **Issue Description:** what is broken or confusing.
   - **Framework Violation:** the exact heuristic / rule / dimension (e.g. "Nielsen #1 —
     Visibility of System Status").
   - **Priority:** the `P0`–`P3` rank with the ladder criterion it met — see §4.
   - **Severity:** the 0–4 score with a justification that names the three factors
     (frequency / impact / persistence) it was derived from — see §4.
   - **Evidence:** a screenshot path under `./assets/…`, a `file:line`, and/or repro
     steps. See the honesty rule in §6.
   - **Recommended Fix:** specific, actionable guidance.

   *(A schema-2 report carries five fields — the same list without `Priority`.)*

5. **`## Walkthrough`** *(optional; live/hybrid only)* — a rendered visual sequence of the
   captured screenshots. See below.
6. **`## Appendix`** — `mode`, `frameworks applied`, **`Coverage / not inspected`**, and —
   when the run met a login wall — one **`Access:`** line.

   `Coverage / not inspected` names everything in scope that was NOT audited (unreachable
   routes, gated screens that stayed unreached), explicitly. Silent gaps are prohibited.

   **A gated screen that was reached via the auth handoff is not a coverage gap** and must
   not be listed as one — it was audited. What the reader needs instead is *how access was
   obtained*, which is the `Access:` line. Record the **rung, never the account**: no
   `account:` key, no email, no profile or vault item name (SPEC §9.7's `author:`
   precedent — PII in a file that ships in the host's repo).

   ```markdown
   ## Appendix
   - Access: auth-gated; satisfied at L3 (user handoff). Account not recorded.
   ```

   Other outcomes take the same shape — `declined by user`, or
   `handoff unavailable — no attended browser surface` (which is *not* a decline; nobody
   was asked). Those two leave the gated screens in `Coverage / not inspected`.
   Full procedure: [`auth-handoff.md`](./auth-handoff.md).

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
The number of `[PN]` findings in the body must exactly equal `summary.total`, and the
per-priority body counts must match `summary.P0..P3`. *(Schema 2: `[sevN]` headings against
`summary.sev1..4`.)* The validator enforces this.

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

| Date (UTC) | Auditor | Scope | P0 | P1 | P2 | P3 | Report |
|------------|---------|-------|----|----|----|----|--------|
| 2026-11-11T14:30:00Z | usability | checkout flow | 0 | 1 | 1 | 0 | [report](usability-20261111-143000.md) |
```

**Transitioning an index that predates schema 3.** The index is append-only and shared by
every run and every auditor, so its columns cannot be swapped — that would mean rewriting
rows whose counts were recorded in a different vocabulary. An index therefore **keeps the
shape it was created with**. When the first schema-3 run meets a severity-shaped index, it
leaves that table untouched and starts a second one below it:

```markdown
# Audit index

| Date (UTC) | Auditor | Scope | Sev4 | Sev3 | Sev2 | Sev1 | Report |
|------------|---------|-------|------|------|------|------|--------|
| 2026-07-15T14:30:00Z | usability | checkout flow | 0 | 1 | 1 | 0 | [report](usability-20260715-143000.md) |

## Schema 3 — priority

| Date (UTC) | Auditor | Scope | P0 | P1 | P2 | P3 | Report |
|------------|---------|-------|----|----|----|----|--------|
| 2026-11-11T09:00:00Z | accessibility | checkout flow | 1 | 0 | 2 | 0 | [report](accessibility-20261111-090000.md) |
```

Both shapes validate, and a file carrying both validates. Never translate a row from one
vocabulary to the other: a `sev4` count is not a `P0` count, and pretending otherwise
falsifies the record.

## 8. Extending the contract for a new auditor

A new suite member (e.g. accessibility) reuses everything above and only:
1. sets its own `auditor` value,
2. defines its own `frameworks` vocabulary — register it in `FRAMEWORKS_BY_AUDITOR` in
   [`scripts/validate_report.py`](../../../scripts/validate_report.py) (an unregistered
   auditor still validates, but its frameworks are only checked for non-emptiness),
3. keeps the same priority ladder, severity rubric, body layout, and `index.md` row
   shape.

Auditors share one `.ux/audits/` directory and one `index.md`; reports from different
auditors coexist and are distinguished by the `auditor` field. If a change to this
contract is needed, bump `schema` and update `scripts/validate_report.py` in the same
change.
