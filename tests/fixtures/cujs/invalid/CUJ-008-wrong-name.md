---
id: CUJ-008
slug: a-different-slug
schema: 1
title: Slug that disagrees with the filename
actor: returning-user
actor_description: "Returns daily."
goal: "Capture a task"
criticality: medium
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

# CUJ-008 — Wrong filename

## Narrative

Invalid fixture: `slug` is `a-different-slug` but the file is `CUJ-008-wrong-name.md`. The
generated SPEC.md index links by `<id>-<slug>.md`, so a mismatch produces a dead link.

## Out of scope

Everything — this fixture exists to be rejected.
