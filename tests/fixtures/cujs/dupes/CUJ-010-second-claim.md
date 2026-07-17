---
id: CUJ-010
schema: 1
title: Second journey claiming CUJ-010
actor: "Power user who lives in the keyboard shortcuts"
goal: "Capture a task without touching the mouse"
criticality: medium
entry_point: "/"
preconditions:
  - "App loaded at /"
steps:
  - n: 1
    action: "Press the 'n' key"
    expect: "The new-task input takes focus"
success_criteria:
  - "The task persists after reload"
---

# CUJ-010 — Second claim

## Narrative

Valid on its own; invalid as a directory. Paired with `CUJ-010-first-claim.md`, which
claims the same id.

## Out of scope

Everything — this fixture exists to be rejected as a pair.
