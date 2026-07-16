# The `.ux/cujs` CUJ File Contract

The file contract for a **critical user journey** — one journey per file, stored in the host
repository and treated as the single source of truth about what that app is *for*.

Two skills share this contract. `spec-cuj` **produces** journeys through an interview;
`audit-cuj` **consumes** them, replaying each against the running app and reporting the step
that broke. A journey is therefore written once by a human and read many times by a machine —
it has to be precise enough to execute and honest enough to argue with.

- **Schema version:** `1`
- **Machine-checked by:** [`scripts/validate_cuj.py`](../../../scripts/validate_cuj.py)
  (the executable form of this document — if the two ever disagree, reconcile them).
- **Specified by:** [`SPEC.md`](../../../SPEC.md) §9.2.

---

## 1. Where CUJs live

Journeys are written into the **host** repository (the app being described), never into the
plugin repo:

```
<host-repo>/
├── .ux/
│   └── cujs/
│       ├── CUJ-001-add-a-task.md
│       └── CUJ-002-complete-a-task.md
└── SPEC.md          # gets a GENERATED index of the above — see §7
```

- Create `.ux/` and `.ux/cujs/` if absent. No need to ask.
- `.ux/cujs/` is **canonical**. The host's `SPEC.md` carries only a generated index pointing
  here — never the journey text itself. One source, no drift.

## 2. File naming

```
<id>-<slug>.md
```

- `id` matches `^CUJ-\d{3}$` and is **unique across the directory**.
- `slug` matches `^[a-z0-9]+(-[a-z0-9]+)*$`.
- The filename must equal `<id>-<slug>.md` exactly. The generated index links by this name,
  so a mismatch is a dead link in the host's spec.

Journeys are **long-lived and editable** — unlike an audit report, a CUJ is expected to be
revised in place as the product changes. Bump `authored.revision` when you do.

## 3. Frontmatter schema (required)

```yaml
---
id: CUJ-001                  # ^CUJ-\d{3}$ — unique across .ux/cujs/
slug: add-a-task             # ^[a-z0-9-]+$ — filename MUST equal <id>-<slug>.md
schema: 1                    # cuj-contract version — must be 1
title: Add a task to the list
actor: returning-user        # a NAMED persona — never "the user" (§4)
actor_description: "Has 3-10 existing tasks, returns daily to capture new ones."
goal: "Capture a new task from the list view without navigating away"   # outcome, not features
criticality: critical        # critical | high | medium | low — drives severity capping (§6)
entry_point: "/"             # route, URL, or named screen where the journey starts
preconditions:               # non-empty; what must already be true
  - "App loaded at / with at least one existing task"
steps:                       # non-empty, ordered; n contiguous 1..N
  - n: 1
    action: "Click the new-task input at the top of the list"
    expect: "The input takes focus and shows the placeholder 'What needs doing?'"
  - n: 2
    action: "Type 'Buy milk' and press Enter"
    expect: "A row reading 'Buy milk' appears at the top of the list and the input clears"
success_criteria:            # evaluated AFTER the steps complete (§5)
  - "'Buy milk' is still present after a full page reload"
authored:                    # provenance only — records no author (§8)
  date: 2026-07-16T10:00:00Z # ISO-8601, UTC
  method: interview          # interview | interview-fallback | manual | imported
  revision: 1                # bump on every material edit
---
```

**Rules**
- All thirteen keys are required.
- `schema` must equal `1`.
- `criticality` ∈ {`critical`, `high`, `medium`, `low`}. Not decoration — `audit-cuj` caps
  finding severity by it (§6), so an unknown level has no defined cap.
- `preconditions`, `steps`, and `success_criteria` are non-empty lists.
- Each step is a mapping with `n`, `action`, and `expect`, all non-empty. **`n` must be
  contiguous `1..N` in order** — findings cite `step <n>` by number, so the numbering has to
  be trustworthy.
- `authored` carries `date` (ISO-8601), `method`, and `revision` (a positive integer), and
  **must not carry an author** (§8).

## 4. The observable-`expect` rule

`expect` is the load-bearing field of the whole contract. **It must name something a person
or a browser can observe:** a visible element, a specific string, a URL change, a count, a
value that survives a reload.

| Rejected | Why | Instead |
|----------|-----|---------|
| "It works" | Names no observation. Unfalsifiable. | "A row reading 'Buy milk' appears at the top of the list" |
| "The state updates" | Internal, not perceivable. | "The remaining count decrements by one" |
| "It saves" | Conflates the act with the evidence. | "'Buy milk' is still present after a full page reload" |

The validator rejects an **empty** `expect`; it cannot judge an *unobservable* one, since
that requires reading English. That judgement lives with the `cuj-author` persona, whose job
is to refuse it during the interview. **This is the one contract rule a machine cannot hold
the line on** — which is why the persona states it as a refusal rather than a preference.

The same bar applies to the actor. `actor` is a named persona (`returning-user`,
`first-time-visitor`, `admin`), never "the user". If the honest answer is "everyone", the
journey isn't critical — it's generic, and it belongs in a usability audit instead.

## 5. `steps` vs `success_criteria`

They answer different questions, and the split is what makes the silent-data-loss class
detectable at all:

- **`steps`** — what the actor does, and what they should observe *as they go*.
- **`success_criteria`** — what must be true *after the journey completes*. Evaluated
  separately, once.

A journey can pass every step and still fail its criteria: the task appears in the list,
the user believes they succeeded, and it's gone after a reload. `audit-cuj` grades that at
severity 3 rather than 2 for exactly that reason (§6). If `success_criteria` merely restated
the last step's `expect`, this whole class of failure would be invisible.

## 6. Body layout

After the frontmatter, in order:

1. **`# <id> — <title>`** — title.
2. **`## Narrative`** — 2–4 sentences: why this journey exists, and **what breaks for the
   business if it breaks**. This is what justifies `criticality`, and it's the part a
   reviewer argues with.
3. **`## Out of scope`** — what this journey deliberately does *not* cover (bulk actions, the
   keyboard-only path, offline). Each of those is a separate journey; naming them here stops
   scope creep in the interview and stops `audit-cuj` inventing coverage it never had.

### The body does NOT restate the steps

A deliberate departure from the [report contract](../../usability-audit/references/report-contract.md),
where the body restates the frontmatter counts and the validator reconciles the two.

That works for a report because a report is written once and never edited. **A CUJ is a
living document a human maintains** — duplicating the steps into a prose table would
guarantee drift, and the reconciliation check would decay into a nag that people work around.
Frontmatter is the single source; the narrative carries what YAML cannot.

## 7. The generated `SPEC.md` index

The host's `SPEC.md` gets one generated block listing every journey:

```markdown
## Critical User Journeys

<!-- BEGIN ux-agent-skills:cuj-index — generated from .ux/cujs/; edit the CUJ files, not this table -->
| ID | Journey | Actor | Criticality | Goal | File |
|---|---|---|---|---|---|
| CUJ-001 | Add a task to the list | returning-user | critical | Capture a new task from the list view without navigating away | [.ux/cujs/CUJ-001-add-a-task.md](.ux/cujs/CUJ-001-add-a-task.md) |
<!-- END ux-agent-skills:cuj-index -->
```

**Generate it with `python3 scripts/validate_cuj.py --index .ux/cujs`. Never write this table
by hand or from memory.**

The block is a **pure function of `.ux/cujs/`** — every cell derives from frontmatter and rows
sort by `id`, so regeneration is byte-identical. That is the entire reason splicing it into a
file the user owns is safe: *nothing between the markers is user-authored, so there is nothing
to lose.* An agent re-rendering the table from memory breaks that guarantee silently, which is
why the generator is a script and this rule is not a suggestion.

Splicing rules:
- Replace **only** the bytes between the markers. Prose above and below is untouched.
- Markers absent, or the host has no `SPEC.md` → **ask first, showing the diff** (SPEC §6).
  If declined, stop: the CUJ files stand alone and the index is a convenience, not the source
  of truth.
- Never reorder or rewrite anything else in the host's `SPEC.md`.

## 8. Provenance records no author

`authored` carries `date`, `method`, and `revision`. It carries **no author, email, or
handle**, and `validate_cuj.py` rejects `by` / `author` / `email` outright.

This is a privacy decision with a practical edge. Git history already answers *"who decided
this journey mattered"*, and answers it more honestly than a self-reported field that goes
stale the moment someone else edits the file. **No PII in the artifact beats a rule about
handling PII in the artifact** — so there is no `git config user.email` read, no fallback
value, and nothing to leak when the host repo goes public.

`method` records *how* the journey was captured, which is the part that affects how much you
should trust it: `interview` (via `agent-skills:interview-me`), `interview-fallback` (the
built-in question set, because `interview-me` wasn't installed), `manual`, or `imported`.

## 9. Extending the contract

Adding a field means every existing CUJ becomes invalid unless the field is optional — so
prefer the narrative until a machine genuinely needs to read it.

If a change is unavoidable: bump `schema`, update
[`scripts/validate_cuj.py`](../../../scripts/validate_cuj.py) and
[`tests/test_cuj_contract.py`](../../../tests/test_cuj_contract.py) in the same change, and
state the migration for journeys already on disk in the host repos that adopted this.
