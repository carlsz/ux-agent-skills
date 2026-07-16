---
id: CUJ-010
schema: 1
title: First journey claiming CUJ-010
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
success_criteria:
  - "The task persists after reload"
---

# CUJ-010 — First claim

## Narrative

Valid on its own; invalid as a directory. Paired with `CUJ-010-second-claim.md`, which
claims the same id. A duplicate id breaks the generated index and makes every report's
`CUJ-010 step <n>` citation ambiguous — which is why this is a cross-file check.

## Out of scope

Everything — this fixture exists to be rejected as a pair.
