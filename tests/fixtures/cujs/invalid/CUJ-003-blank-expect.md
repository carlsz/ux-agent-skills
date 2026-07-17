---
id: CUJ-003
schema: 1
title: Step with no observable outcome
actor: "Returning user with a handful of tasks, opens the app daily"
goal: "Reach a state the CUJ never describes"
criticality: medium
entry_point: "/"
preconditions:
  - "App loaded at /"
steps:
  - n: 1
    action: "Click the save button"
    expect: "   "
success_criteria:
  - "The task persists after reload"
---

# CUJ-003 — Blank expect

## Narrative

Invalid fixture: step 1 declares an action but no observable expected outcome. A step
without an `expect` cannot be verified, so the journey is unfalsifiable.

## Out of scope

Everything — this fixture exists to be rejected.
