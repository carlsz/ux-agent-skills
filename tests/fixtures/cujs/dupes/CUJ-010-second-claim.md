---
id: CUJ-010
slug: second-claim
schema: 1
title: Second journey claiming CUJ-010
actor: power-user
actor_description: "Lives in the keyboard shortcuts."
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
authored:
  date: 2026-07-16T10:10:00Z
  method: manual
  revision: 1
---

# CUJ-010 — Second claim

## Narrative

Valid on its own; invalid as a directory. Paired with `CUJ-010-first-claim.md`, which
claims the same id.

## Out of scope

Everything — this fixture exists to be rejected as a pair.
