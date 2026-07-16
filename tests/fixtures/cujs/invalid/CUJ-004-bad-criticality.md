---
id: CUJ-004
slug: bad-criticality
schema: 1
title: Criticality outside the vocabulary
actor: returning-user
actor_description: "Returns daily."
goal: "Capture a task"
criticality: blocker
entry_point: "/"
preconditions:
  - "App loaded at /"
steps:
  - n: 1
    action: "Click the new-task input"
    expect: "The input takes focus"
success_criteria:
  - "The task persists after reload"
authored:
  date: 2026-07-16T10:00:00Z
  method: manual
  revision: 1
---

# CUJ-004 — Bad criticality

## Narrative

Invalid fixture: `criticality: blocker` is outside the four-level vocabulary. Severity
clamping reads this field, so an unknown level has no defined cap.

## Out of scope

Everything — this fixture exists to be rejected.
