---
id: CUJ-007
schema: 1
title: Steps that skip a number
actor: "Returning user with a handful of tasks, opens the app daily"
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
---

# CUJ-007 — Non-contiguous steps

## Narrative

Invalid fixture: steps are numbered 1 and 3. Either step 2 was lost in an edit or the
numbering is decorative — both are ambiguous, and findings cite `step <n>` by number.

## Out of scope

Everything — this fixture exists to be rejected.
