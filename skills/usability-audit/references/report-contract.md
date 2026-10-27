# Shared `.ux/audits` Report Contract

The single output contract for the **ux-agent-skills auditor suite**. Every auditor —
usability (this suite's first), and future accessibility, web-performance, and others —
writes reports that conform to this contract, so their outputs are comparable, tracked in
one index, and consumable by a future fan-out meta-command.

Only two things differ between auditors: the `auditor` frontmatter value and the
`frameworks` list. Everything else here is fixed.

The contract governs **two document types**: the per-run **auditor report** (§1-§6), and the
**suite roll-up** a fan-out writes to combine them (§9). They share the directory, the
schema version, and the severity rubric; they differ in frontmatter, because a roll-up has
no single auditor, mode, or framework.

- **Schema version:** `3`
- **Machine-checked by:** [`scripts/validate_report.py`](../../../scripts/validate_report.py)
  (the executable form of this document — if the two ever disagree, reconcile them).

> **Schema history.** `2` added the optional `## Walkthrough` section (§5) and the
> `assets/` naming convention (§1). `3` replaced the 0–4 severity scale with **P0–P3**
> (§4) and added the **`health` scorecard** (§4.1). A report written by an older auditor at
> `schema: 1` or `2` is not rewritten — `schema` records the contract the report was born
> under, and its `sev4..sev1` counts stay as that run wrote them. Only freshly emitted
> reports carry `3`.

---

## 1. Where reports go

Reports are written into the **host** repository (the app being audited), never into the
plugin repo:

```
<host-repo>/
└── .ux/
    └── audits/
        ├── index.md                       # rolling index of every run (all auditors)
        ├── usability-20260715-143000.md    # one file per run
        ├── usability-20260715-160000.md
        └── assets/                         # captured screenshots / evidence images
            ├── usability-20260715-143000/  # one directory per run (§1, below)
            └── usability-20260715-160000/
```

- Create `.ux/`, `.ux/audits/`, and `.ux/audits/assets/` if absent.
- **Never** write outside `.ux/audits/`. This is the auditor's safety invariant.
- A derived, self-contained `<report>.html` companion may sit beside each `<report>.md`
  (rendered by [`render_report_html.py`](../../../scripts/render_report_html.py); see SPEC §10.6).
  The Markdown remains the source of truth — this contract governs the `.md`, and the `.html` is
  a view of it, never validated against or in place of it.

### Asset naming (screenshots)

Screenshots captured in **live/hybrid** mode go in a **per-run directory** named after the
report that cites them — the report's filename without its `.md`:

```
.ux/audits/
├── cuj-20260716-120000.md
└── assets/
    └── cuj-20260716-120000/      # this run's captures, and only this run's
        ├── cuj-001-step-1.png
        └── cuj-001-step-2.png
```

**The directory name is derived, not chosen**, which is what makes it checkable: the
validator computes the expected directory from the name of the file it is validating, so a
report that cites another run's captures is rejected on write rather than discovered later.
Within the directory, names only have to be unique *to that run* — nothing from another run
shares the directory, so no naming convention has to be agreed across runs or auditors:

| Auditor | What | Name |
|---------|------|------|
| cuj | a journey step | `cuj-<id>-step-<n>.png` (e.g. `cuj-001-step-2.png`) |
| cuj | criteria / other evidence | `cuj-<id>-<slug>.png` (e.g. `cuj-001-after-reload.png`) |
| usability (and other flow auditors) | a key state | `<auditor>-<scope-slug>-<state>.png` (state ∈ `initial`, `mid-flow`, `success`, `error`, `empty`) |

Reference every image from the body with an **inline embed** —
`![alt](./assets/<report-stem>/<name>.png)` — never a bare path, so it renders in Markdown
viewers. Paths are always relative and under `./assets/`.

**Why per-run, when a flat directory is smaller.** Earlier revisions of this contract put
every capture in `assets/` directly under one stable name per thing captured, so a re-run
**overwrote** rather than accumulated. That bounded the directory by what a single run
captures rather than by the number of runs — but it bought that bound by mutating the
evidence under reports nobody had deleted. Reports are append-only; their images were
prune-to-latest, and the two cannot both be true of one document. A `cuj-001-step-2.png`
written this morning replaced the image last week's report embeds — silently, and
undetectably, because the path still resolves and an image still renders. The HTML companion
makes it permanent: it base64-embeds whatever is on disk at render time, so re-rendering an
older report welds a later run's screenshots into it. Per-run directories spend the disk the
overwrite was saving, and buy back the only thing a finding cannot do without — that its
evidence is its own.

So **retention is a whole-run operation**: dropping an old run means deleting its report and
its asset directory together. That is a pruning policy the host can apply, by hand or by
script, without touching a report it keeps — which is precisely what the flat layout made
impossible.

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
schema: 3                    # report-contract version — must be 3
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
  p0: 0                      # blocking
  p1: 1                      # major
  p2: 1                      # minor
  p3: 0                      # polish
health:                      # the scorecard — see §4.1
  rubric: nielsen-10
  score: 30
  max: 36
  pct: 83
  band: Good
  items:
    - item: "Visibility of system status"
      score: 4
      note: "aria-live task count; immediate feedback on every action"
    - item: "Help and documentation"
      score: null
      note: "n/a — single-screen app, no help surface"
---
```

**Rules**
- All ten keys are required.
- `schema` must equal `3`.
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
- `summary` contains `total`, `p0`, `p1`, `p2`, `p3` — all non-negative integers. A level
  outside `P0..P3` must not appear (see §4).
- `health` is the scorecard (§4.1). Its `score`, `max` and `pct` are **derived from `items`
  and validated against them**, so the headline number can never drift from what it is
  made of.

## 4. Priority rubric (P0–P3)

Every finding carries a priority that says **what to do about it**, not merely how bad it
is. The action column is the point: a reader should not have to infer the next step from an
adjective.

| Tag | Name | Meaning | Action |
|-----|------|---------|--------|
| `P0` | Blocking | Prevents the task entirely | Fix immediately |
| `P1` | Major | Causes significant difficulty | Fix before release |
| `P2` | Minor | Irritating, but a workaround exists | Fix in the next pass |
| `P3` | Polish | Little real user impact | Fix if time allows |

A non-problem is a *non-finding*: it is never emitted, never counted, and has no tag.
Reporting non-problems dilutes the report. What a run did well belongs in `health` (§4.1),
which is where positive observations become legible without inflating the finding count.

### Keeping the scale reproducible

A scale applied by judgment alone drifts between runs — the same app, audited twice, gets
two different answers. These rules are tie-breakers, applied in order, and exist to make a
re-run land in the same place:

1. **If a user would contact support about it, it is at least P1.**
2. **If the user cannot complete the task at all — no workaround, no way around it — it is
   P0.** Difficulty is P1; impossibility is P0. **This rule is a ceiling as well as a
   floor: `P0` requires impossibility, so no raise from rule 3 may reach `P0` for a defect
   the user can work around.** Without that clause rule 3 escalates a merely difficult
   defect on a declared journey to "Blocking — fix immediately", contradicting this rule
   while "the higher priority wins" resolves in favour of the absurd reading. The way out
   is not to lower the base grade until the raise lands somewhere defensible — that is
   reverse-engineering the input to fix the output, exactly the drift these tie-breakers
   exist to stop.
3. **If it affects a journey in `.ux/cujs/`, raise it one level** (to a maximum of P0). A
   defect on a path the host has declared critical is not a minor defect. **This rule is
   for the auditors that are not `cuj`.** The `cuj` auditor's findings are *all* about a
   journey in `.ux/cujs/` by construction, so applying it there fires on every finding —
   nothing could ever be graded `P3` — and it double-counts the weighting that auditor
   already applies through its `criticality` clamp. It exists to pull *other* lenses'
   findings onto declared-critical paths, not to re-weigh the journey auditor's own.
4. **If it is only visible to the auditor** — found by reading source, never surfaced to a
   user — it is at most P2, and the Evidence field says so.

Where two rules disagree, the higher priority wins and the Priority field says which rule
decided it.

### Migrating from schema 2

`sev4 → P0`, `sev3 → P1`, `sev2 → P2`, `sev1 → P3`. Reports already written at `schema: 2`
keep their `sevN` vocabulary — they are historical records, not drafts (see the schema
history note above).

## 4.1 The `health` scorecard

A findings list says what is broken and is silent about everything else, so a clean run has
nothing to show. `health` is the other half: a graded pass over the auditor's own framework,
which makes a good result legible and a trend possible.

```yaml
health:
  rubric: nielsen-10        # which framework the items come from; must appear in `frameworks`
  score: 30                 # sum of item scores
  max: 36                   # sum of item `of` values; n/a items excluded from BOTH
  pct: 83                   # round(100 * score / max)
  band: Good                # see the band table below
  items:
    - item: "Visibility of system status"
      score: 4              # DERIVED: the P-number of the worst finding citing this item,
                            # 4 when none cites it. null = not applicable
      of: 4                 # optional; always 4 — see "one 0-4 scale" below
      note: "aria-live task count; immediate feedback on every action"
```

| `pct` | Band |
|-------|------|
| ≥ 90 | Excellent |
| ≥ 70 | Good |
| ≥ 50 | Acceptable |
| ≥ 30 | Poor |
| < 30 | Critical |

### `pct` is a priority index, not `score / max`

**The two numbers answer different questions and are computed differently.** `score` / `max`
are the rubric view — how much of *this* lens is healthy, and `items` says where. `pct` is
the headline, and it is derived from the **findings alone**:

| | Deduction |
|---|---|
| the single **worst** finding | `P0` 55 · `P1` 25 · `P2` 10 · `P3` 3 |
| **each other** finding | `P0` 15 · `P1` 6 · `P2` 2 · `P3` 1 |

`pct = max(0, 100 - total deduction)`, and a run with no findings is `100`. The worst
finding sets the floor; every additional one adds to it.

> **Why not `score / max`.** Because that number is a function of how many items the rubric
> happens to hold. A finding costs `(4 - score) / 4N`, so the same defect is worth twice as
> much on a ten-heuristic rubric as on a twenty-two-criterion one — and the index and the
> roll-up both put those side by side as though they were one scale. On one real run an
> accessibility audit carrying two `P0`s read **79%** while a usability audit carrying none
> read **50%**, purely because WCAG enumerates more criteria than Nielsen. A percentage
> whose meaning depends on the size of the yardstick cannot be compared across auditors or
> trended across a rubric change. This one depends only on what was found and how bad it
> was, so it means the same thing on every report in the directory.

Both are still mechanical and both are still checked: `score`/`max` against `items`, `pct`
against `summary`. A reader who divides `score` by `max` will not get `pct`, and should
not — the scorecard locates the damage, the index measures it.

### The score is derived from the findings, never judged beside them

**An item's `score` is the P-number of the worst finding filed against it.** Nothing else
decides it:

| Worst finding citing this item | `score` |
|---|---|
| none | 4 |
| `P3` Polish | 3 |
| `P2` Minor | 2 |
| `P1` Major | 1 |
| `P0` Blocking | 0 |

The bridge is already in every finding: §5 requires a **Framework Violation** field naming
the exact heuristic, criterion or step the finding is about — and that is the `health` item
it deducts from. One observation, graded once, shown two ways: the findings list says what
broke, the scorecard says where.

> **Why this is mechanical and not a matter of taste.** Grading the rubric and filing the
> findings used to be two independent passes over the same app, so they could disagree —
> and did, in opposite directions at once. In one real run the `cuj` auditor scored four
> journey steps `0`, the worst available mark, for a divergence it had itself graded `P3`,
> the *least* severe; the same run's index put it at 43% **Poor** for one word of copy,
> while an accessibility run carrying two `P0`s read 70% **Good**. The number was
> anti-correlated with severity: the auditor that found the least scored the worst. A
> reader taking the dial at face value draws the opposite of the truth. Deriving the score
> removes the second judgment, so the two halves cannot contradict each other.

**One 0–4 scale, four idioms.** Every item is `of: 4` whatever the auditor: usability one
per Nielsen heuristic, accessibility one per WCAG criterion checked, `cuj` one per journey
step verified, web performance one per metric measured. The *items* carry each auditor's
idiom; the *scale* is shared, which is what makes the percentage comparable. A pass/fail
rubric like WCAG still grades 0–4 here, because the item records how badly the criterion
failed, not whether it normatively conforms — and a `P2` contrast defect genuinely is not
a `P0` one.

**Rules**
- **`score` is derived**, per the table above; `of` is `4`. A deduction with no finding
  behind it is not allowed — if an item is worth marking down, say what is wrong and file
  it.
- **Any item scoring below `4`, and any n/a item, carries a `note` naming the finding that
  took it down** (its title, or its `F`-number where the run uses them). Without finding
  ids in the schema, that note is the only thread a reader can follow from a low row back
  to the reason for it.
- **The worst finding must land somewhere.** The lowest non-null item score must equal the
  P-number of the report's worst finding — so a report carrying a `P0` has an item at `0`,
  and a report whose worst finding is `P3` has no item below `3`. A clean run
  (`total: 0`) scores every applicable item `4`. `validate_report.py` recomputes this and
  fails the run on a mismatch, exactly as it does the roll-up verdict.
- An item marked n/a (`score: null`) carries no findings; a finding citing it is a
  contradiction the run must resolve before writing.
- `score` = sum of non-null item scores; `max` = sum of `of` for non-null items; `pct` =
  `round(100 * score / max)`; `band` follows the table. **All four are validated against
  `items`** — a hand-written headline that disagrees with its own rows is rejected.
- `score: null` means *not applicable*: excluded from both `score` and `max`, so marking an
  item n/a never silently penalises the result.
- **An item scoring at or below half its `of`, or marked n/a, MUST carry a `note`.** An
  unexplained low score is an assertion, not a finding. (This mirrors §9's rule that a
  skipped auditor must carry a reason.)
- `rubric` names a framework that appears in `frameworks`, so the scorecard cannot cite a
  lens the run did not apply.
- `health` covers what was **inspected**, not what exists: items the run could not reach are
  `null` with a note, and the gap is repeated in `Coverage / not inspected` (§5).

## 5. Body layout

After the frontmatter, in order:

1. **`# <Auditor> Audit — <scope>`** — title.
2. **`## Executive summary`** — 2–4 sentences plus a priority-count table.
3. **`## Design health`** — the scorecard (§4.1) as a readable table: one row per item with
   its score and note, then the `score / max · pct · band` line.

> **Both of these sections are for the Markdown reader.** The HTML companion builds its
> brief from frontmatter — the counts as chips, the score as a dial, the executive summary
> as the brief's prose — and therefore **skips `## Executive summary` and `## Design
> health` in the body**, so the same numbers are never printed twice in one view. Write
> both sections in full regardless: the Markdown is the canonical artifact and the agent
> reading it has no brief.
4. **`## Prioritized fixes`** — findings listed P0 → P3, each line linking to its finding
   below.
5. **`## Findings`** — one finding per **level-3 heading tagged with its priority**:

   ```markdown
   ### [PN] <short title>           # N ∈ 0..3
   ```

   Each finding block MUST contain these five labelled fields, each written as a markdown
   **list item** — `- **Field:** value`, the literal shape of the list below, with any
   continuation lines indented two spaces under their bullet:

   ```markdown
   - **Issue Description:** what is broken, in enough detail to act on without
     re-auditing.
   ```

   > **Write the bullet.** This list is both the roster of fields and the markup for them,
   > and that double duty has already cost a real defect: given this section, a `cuj` run
   > bulleted its fields while `usability` and `accessibility` runs wrote bare `**Field:**`
   > paragraphs. Bare bold still *validates* — §7's check is a substring test — so the
   > divergence was invisible until the HTML companion rendered those findings as cards
   > with completely empty bodies. `render_report_html.py` now reads both forms, because
   > reports are append-only history; emit the bulleted one.

   - **Issue Description:** what is broken or confusing.
   - **Framework Violation:** the exact heuristic / rule / dimension (e.g. "Nielsen #1 —
     Visibility of System Status").
   - **Priority:** the P-level, its action, and a one-line justification — naming the
     tie-breaker rule (§4) when one decided it.
   - **Evidence:** a screenshot path under `./assets/…`, a `file:line`, and/or repro
     steps. See the honesty rule in §6.
   - **Recommended Fix:** specific, actionable guidance.

6. **`## Walkthrough`** *(optional; live/hybrid only)* — a rendered visual sequence of the
   captured screenshots. See below.
7. **`## Appendix`** — `mode`, `frameworks applied`, **`Coverage / not inspected`**, and —
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
embed under `./assets/` (see §1 naming). The section carries no priority headings, so it
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
per-priority body counts must match `summary.p0..p3`. The validator enforces this.

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

| Date (UTC) | Auditor | Scope | P0 | P1 | P2 | P3 | Health | Report |
|------------|---------|-------|----|----|----|----|--------|--------|
| 2026-07-15T14:30:00Z | usability | checkout flow | 0 | 1 | 1 | 0 | 83 | [report](usability-20260715-143000.md) |
```

`Health` is the report's `health.pct` as a bare integer, so the index carries the trend the
roll-up reads (§9). A report with no scorecard writes `—`.

## 8. Extending the contract for a new auditor

A new suite member (e.g. accessibility) reuses everything above and only:
1. sets its own `auditor` value,
2. defines its own `frameworks` vocabulary — register it in `FRAMEWORKS_BY_AUDITOR` in
   [`scripts/validate_report.py`](../../../scripts/validate_report.py) (an unregistered
   auditor still validates, but its frameworks are only checked for non-emptiness),
3. keeps the same priority rubric, body layout, and `index.md` row shape,
4. scores its own framework into `health` (§4.1) using `of` to declare its native scale —
   it does not have to grade 0–4.

Auditors share one `.ux/audits/` directory and one `index.md`; reports from different
auditors coexist and are distinguished by the `auditor` field. If a change to this
contract is needed, bump `schema` and update `scripts/validate_report.py` in the same
change.

## 9. The suite roll-up (`rollup-*.md`)

A fan-out (`/ux-audit`) writes one roll-up beside the member reports it summarizes. It is a
**sibling document type**, not an auditor report: it owns no findings — it links to the
member reports that do.

```
rollup-<YYYYMMDD>-<HHMMSS>.md
```

### Frontmatter

```yaml
---
kind: rollup                 # the discriminator — REQUIRED, exactly this spelling
schema: 3
version: 0.5.1               # the emitting plugin's version (§3 rules apply)
date: 2026-07-19T04:39:28Z
target: http://localhost:3000
scope: "Sprout — full UX auditor suite"
verdict: GO                  # GO | NO-GO — a bare token, nothing else
verdict_reason: "all 3 critical journeys pass live; 5 minor issues, no P0 or P1"
auditors_ran: [cuj, usability, accessibility, web-performance]
auditors_skipped:            # [] when none; every entry carries its reason
  - auditor: web-performance
    reason: "opt-in; run with --only web-performance or --all"
summary:                     # the MERGED counts across every member report
  total: 5
  p0: 0
  p1: 0
  p2: 4
  p3: 1
health:                      # the suite scorecard
  pct: 88
  band: Good
  method: mean-of-auditors
  trend: [71, 76, 79, 81, 83]   # PRIOR runs, oldest → newest; [] when no history
  auditors:
    - {auditor: cuj, pct: 100, band: Excellent, unit: "steps verified"}
    - {auditor: usability, pct: 83, band: Good, unit: "Nielsen rubric"}
---
```

**Rules**

- All twelve keys are required. A roll-up carries **no** `auditor`, `mode`, or `frameworks`
  key — it has no single value for any of them.
- `kind` must be exactly `rollup`. Two other spellings — `report: rollup`, and `rollup: true`
  — are *read* by the renderer and `is_rollup()` so that roll-ups written before this
  section keep rendering, but writing either is a violation. Tolerated on read, never
  blessed on write.
- **`verdict` is a bare token: `GO` or `NO-GO`.** The justification goes in
  `verdict_reason`. This is not stylistic — the HTML renderer tests this value to colour
  the go/no-go banner, so `verdict: "GO — all journeys pass"` is not a `GO` to a machine.
- **The verdict is derived, not judged:** `NO-GO` if `p0 > 0` or `p1 > 0`, else `GO`. The
  validator recomputes it from `summary` and rejects a mismatch. Nuance belongs in
  `verdict_reason` — never in a third verdict value. (The gate reads straight off the
  rubric: P0 is *fix immediately* and P1 is *fix before release*, so either one blocks.)
- `summary` holds the **merged** counts across all members and reconciles the same way as
  §3: `total` equals the sum of `p0..p3`.
- `health.pct` is the mean of the member `health.pct` values, rounded; `band` follows §4.1's
  table; `auditors` carries one entry per member that ran. **`trend` holds PRIOR runs only**
  — the current run's score is `pct`, not the last element — and it **must degrade to `[]`**
  rather than to a broken chart: an authenticated run is advised to gitignore `.ux/audits/`
  wholesale (see `auth-handoff.md` §6), so in those repos there is no history to read.
- `auditors_skipped` is required even when empty, and **every entry carries a `reason`**.
  The suite's rule is that a skipped auditor never reads as a clean pass; making the
  reason structural is what enforces it.

> **Why this section exists.** The roll-up's frontmatter was unspecified until now, and the
> agent improvised it per run. Five consecutive runs of the same app produced five different
> shapes — three different discriminators (`kind:`, `report:`, none), three different count
> keys (`summary:`, `totals:`, none), and verdict strings that mixed the token with its prose.
> The HTML renderer looked for a key none of them wrote, so **the roll-up dashboard never
> rendered once**: every run fell through to the generic report path and published a header
> reading `0 findings` above a table of five. Two of those runs reached opposite verdicts
> from identical counts, because the gate lived in prose and left "is this sev3 a blocker?"
> to the auditor. An unspecified contract is not a flexible one — it is a broken one that
> fails quietly.

### Body layout

1. **`# UX Audit Roll-up — <scope>`** — title.
2. A lead paragraph stating the verdict in prose. *(The HTML renderer shows everything
   between the title and the first `## ` heading, so this paragraph is the dashboard's
   opening line — do not omit it.)*
3. **`## Per-auditor results`** — one row per member: auditor, mode, per-priority counts,
   total, health percentage and band, and a one-line result. Link each auditor name to its
   report.
4. **`## Auditors that ran vs. skipped`** — prose mirroring `auditors_ran` /
   `auditors_skipped`, with the reason for every skip.
5. **`## Merged top issues`** — findings across all members, `P0` → `P3`, each
   linking to its finding anchor in the member report.
6. **`## Verdict rationale`** — why the gate landed where it did.
7. **`## Notes`** — provenance, target caveats, and links to the member reports. A roll-up
   has **no `## Appendix`**: coverage honesty is each member report's own obligation
   (§5), and the roll-up inherits it by linking to them.

### What a roll-up is not

It is not validated as an auditor report: no `[PN]` finding blocks, no five-field
finding bodies, no `## Appendix` coverage check. `validate_report.py` dispatches on the
discriminator and applies `validate_rollup` instead.
