---
id: CUJ-006
slug: missing-provenance
schema: 1
title: A journey with no provenance
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
success_criteria:
  - "The task persists after reload"
---

# CUJ-006 — Missing provenance

## Narrative

Invalid fixture: the `authored` block is absent, so nothing records when this journey was
written, how, or at which revision. Reports cite `authored.revision` to say which version
of a journey they verified.

## Out of scope

Everything — this fixture exists to be rejected.
