---
id: CUJ-005
schema: 1
title: A journey with no steps
actor: "Returning user with a handful of tasks, opens the app daily"
goal: "Do something unspecified"
criticality: low
entry_point: "/"
preconditions:
  - "App loaded at /"
steps: []
success_criteria:
  - "Something happened"
---

# CUJ-005 — No steps

## Narrative

Invalid fixture: `steps` is empty. A journey with no steps describes no journey, and
`/audit-cuj` would report a vacuous pass.

## Out of scope

Everything — this fixture exists to be rejected.
