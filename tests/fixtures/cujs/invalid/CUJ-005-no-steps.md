---
id: CUJ-005
slug: no-steps
schema: 1
title: A journey with no steps
actor: returning-user
actor_description: "Returns daily."
goal: "Do something unspecified"
criticality: low
entry_point: "/"
preconditions:
  - "App loaded at /"
steps: []
success_criteria:
  - "Something happened"
authored:
  date: 2026-07-16T10:00:00Z
  method: manual
  revision: 1
---

# CUJ-005 — No steps

## Narrative

Invalid fixture: `steps` is empty. A journey with no steps describes no journey, and
`/audit-cuj` would report a vacuous pass.

## Out of scope

Everything — this fixture exists to be rejected.
