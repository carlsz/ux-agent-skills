---
id: CUJ-009
slug: authored-by
schema: 1
title: Provenance carrying an author
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
authored:
  date: 2026-07-16T10:00:00Z
  by: "someone@example.com"
  method: interview
  revision: 1
---

# CUJ-009 — Author recorded

## Narrative

Invalid fixture: `authored.by` carries an email address. CUJ files record no author by
design (SPEC.md §9.7) — git history answers "who decided this mattered" more honestly than
a self-reported field, and no PII in the artifact beats a rule about handling PII in it.
The rule is enforced here rather than merely documented.

## Out of scope

Everything — this fixture exists to be rejected.
