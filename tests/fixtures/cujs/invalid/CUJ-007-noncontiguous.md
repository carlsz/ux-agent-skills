---
id: CUJ-007
slug: noncontiguous
schema: 1
title: Steps that skip a number
actor: returning-user
actor_description: "Returns daily."
goal: "Capture a task"
criticality: high
entry_point: "/"
preconditions:
  - "App loaded at /"
steps:
  - n: 1
    action: "Click the new-task input"
    expect: "The input takes focus"
  - n: 3
    action: "Press Enter"
    expect: "A new row appears at the top of the list"
success_criteria:
  - "The task persists after reload"
authored:
  date: 2026-07-16T10:00:00Z
  method: manual
  revision: 1
---

# CUJ-007 — Non-contiguous steps

## Narrative

Invalid fixture: steps are numbered 1 and 3. Either step 2 was lost in an edit or the
numbering is decorative — both are ambiguous, and findings cite `step <n>` by number.

## Out of scope

Everything — this fixture exists to be rejected.
