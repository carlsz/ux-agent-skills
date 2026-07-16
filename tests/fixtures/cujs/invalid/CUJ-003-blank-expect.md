---
id: CUJ-003
slug: blank-expect
schema: 1
title: Step with no observable outcome
actor: returning-user
actor_description: "Returns daily."
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
authored:
  date: 2026-07-16T10:00:00Z
  method: manual
  revision: 1
---

# CUJ-003 — Blank expect

## Narrative

Invalid fixture: step 1 declares an action but no observable expected outcome. A step
without an `expect` cannot be verified, so the journey is unfalsifiable.

## Out of scope

Everything — this fixture exists to be rejected.
