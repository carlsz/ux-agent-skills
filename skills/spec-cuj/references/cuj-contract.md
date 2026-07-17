# The `.ux/cujs` CUJ File Contract

The file contract for a **critical user journey** — one journey per file, stored in the host
repository and treated as the single source of truth about what that app is *for*.

Two skills share this contract. [`spec-cuj`](../SKILL.md) **produces** journeys through an
interview; [`audit-cuj`](../../audit-cuj/SKILL.md) **consumes** them, replaying each against
the running app and reporting the step that broke. A journey is therefore written once by a human and read many times by a
machine — it has to be precise enough to execute and honest enough to argue with.

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
<id>-<slug>.md          e.g. CUJ-001-add-a-task.md
```

- `id` matches `^CUJ-\d{3}$` and is **unique across the directory**.
- `slug` matches `^[a-z0-9]+(-[a-z0-9]+)*$`.

**The filename carries the slug — there is no `slug` key.** A field whose only job is to be
compared against the filename is ceremony; deleting it deletes the entire class of
slug-vs-filename mismatch rather than validating it.

`id` does stay in frontmatter, because reports cite it (`CUJ-001 step 2`) and it should not
change silently when a file is renamed. So one identity check survives: **the id in the
filename must equal the id in frontmatter.** They are read by different consumers — the
generated index links by *filename*, every finding cites the *frontmatter id* — so when they
disagree the host's spec points at one journey and the report names another.

Journeys are **long-lived and editable**: unlike an audit report, a CUJ is expected to be
revised in place as the product changes. Nothing in the file records that history — see §8.

## 3. Frontmatter schema (required)

Ten keys. The schema is deliberately small: a journey is written by a human answering an
interview, so every required field has to earn its place. Anything derivable from the
filename, from git, or from another field is ceremony — and ceremony is what makes people
stop writing journeys.

```yaml
---
id: CUJ-001                  # ^CUJ-\d{3}$ — unique across .ux/cujs/; must match the filename
schema: 1                    # cuj-contract version — must be 1
title: Add a task to the list
actor: "Returning user with 3-10 existing tasks, opens the app daily to capture new ones"
goal: "Capture a new task from the list view without navigating away"   # outcome, not features
criticality: critical        # critical | high | medium | low — drives severity capping (§6)
entry_point: "/"             # route, URL, or named screen where the journey starts
preconditions:               # non-empty; what must already be TRUE (not what you do — §5)
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
---
```

**Rules**
- All ten keys are required. There is no `slug` (the filename carries it, §2), no
  `actor_description` (one specific `actor` string does that work, §4), and **no provenance
  block at all** (§8).
- `schema` must equal `1`.
- `criticality` ∈ {`critical`, `high`, `medium`, `low`}. Not decoration — `audit-cuj` caps
  finding severity by it (§6), so an unknown level has no defined cap.
- `preconditions`, `steps`, and `success_criteria` are non-empty lists.
- Each step is a mapping with `n`, `action`, and `expect`, all non-empty. **`n` must be
  contiguous `1..N` in order** — findings cite `step <n>` by number, so the numbering has to
  be trustworthy.
- No `author`, `authored`, `by`, or `email` key may appear (§8). Rejected, not ignored.

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
that requires reading English. That judgement lives with the
[`cuj-author`](../../../agents/cuj-author.md) persona, whose job is to refuse it during the
interview. **This is the one contract rule a machine cannot hold the line on** — which is why
the persona states it as a refusal rather than a preference.

The same bar applies to the actor. `actor` is **one specific sentence** — who they are and
what they bring to the journey ("Returning user with 3-10 existing tasks, opens the app daily
to capture new ones"), never "the user". If the honest answer is "everyone", the journey isn't
critical — it's generic, and it belongs in a usability audit instead.

## 5. `preconditions` vs `steps` vs `success_criteria`

Three fields, three questions, and each split earns its keep by making a distinct failure
visible:

- **`preconditions`** — what must already be **true** before the journey starts. Not actions.
- **`steps`** — what the actor **does**, and what they should observe *as they go*.
- **`success_criteria`** — what must be true **after** the journey completes. Evaluated
  separately, once.

**Why `preconditions` isn't just step 0.** If setup folds into the steps, then *failing to
establish the starting state* becomes indistinguishable from *the journey being broken* — and
`audit-cuj` would report a severity 4 catastrophe for what is really "couldn't run this".
Keeping them apart is what lets a run say "skipped, precondition unmet" honestly.

**Why `success_criteria` isn't just the last step.** A journey can pass every step and still
fail its criteria: the row appears, the user believes they succeeded, and it's gone after a
reload. `audit-cuj` grades that at severity 3 rather than 2 for exactly that reason (§6). If
`success_criteria` merely restated the last step's `expect`, this entire class of silent data
loss would be invisible.

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

## 8. No provenance, no author

A CUJ records **nothing about its own history** — no author, no date, no revision, no capture
method. `validate_cuj.py` rejects `author`, `authored`, `by`, and `email` outright.

**Git already answers all of it, and answers it honestly.** Who wrote this journey, when, and
how many times it has been revised are questions `git log .ux/cujs/CUJ-001-*.md` gets right by
construction. Hand-maintained frontmatter gets them right only until the first person forgets
— and an unbumped `revision: 1` on a journey edited four times is worse than no revision at
all, because it lies with confidence. A field that is silently wrong is a liability; a field
you have to remember to update will eventually be silently wrong.

The author field is the sharpest case: it is **PII in a file that ships in the host's repo**.
Removing it means there is no `git config user.email` read, no fallback value, and nothing to
leak when that repo goes public. **No PII in the artifact beats a rule about handling PII in
the artifact.**

Deleting the field from the schema is not by itself the guarantee — nothing stops someone
adding `author:` back by hand — which is why the rejection is executable and has a fixture.
A privacy rule that isn't enforced is a comment.

**What a report cites.** With no `revision`, a finding names the journey and step only
(`CUJ-001 "Add a task" — step 2`). To recover which version of a journey a given report
verified, take the report's `date` and `git log` the CUJ file. That is one more step than
reading `rev: 1` off the page, and it is the step that gives you the true answer.

## 9. Extending the contract

The bar is high, and §3's ten keys are the argument: every field here is one more thing a
human has to answer before they get a journey, and the failure mode of a heavy schema is not
bad journeys — it's **no journeys**.

Before adding a field, check it isn't derivable from the filename, from git, or from another
field. Those are exactly the three sources that already cost `slug`, `authored`, and
`actor_description` their place. Prefer the narrative until a machine genuinely needs to read
it.

If a change is unavoidable: bump `schema`, update
[`scripts/validate_cuj.py`](../../../scripts/validate_cuj.py) and
[`tests/test_cuj_contract.py`](../../../tests/test_cuj_contract.py) in the same change, and
state the migration for journeys already on disk in the host repos that adopted this.
