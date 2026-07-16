---
id: CUJ-009
schema: 1
title: Journey recording an author
actor: "Returning user with a handful of tasks, opens the app daily"
author: "someone@example.com"
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

# CUJ-009 — Author recorded

## Narrative

Invalid fixture: a top-level `author` key carrying an email address. CUJ files record no
author and no provenance block at all (SPEC.md §9.7) — git already answers who wrote this,
when, and through how many revisions, and answers it honestly, unlike hand-maintained
frontmatter that goes stale the moment someone forgets.

Removing the `authored` block from the schema is not by itself a guarantee: nothing stops
someone adding `author:` back by hand. So the rule stays executable. A privacy rule that
isn't enforced is a comment, and this file is what keeps it from becoming one.

## Out of scope

Everything — this fixture exists to be rejected.
