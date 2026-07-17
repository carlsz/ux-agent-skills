---
id: CUJ-042
schema: 1
title: Frontmatter id that disagrees with the filename
actor: "Returning user with a handful of tasks, opens the app daily"
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
---

# CUJ-042 — Wrong filename

## Narrative

Invalid fixture: the file is named `CUJ-008-wrong-name.md` but frontmatter declares
`id: CUJ-042`. There is no `slug` key to disagree — the filename carries the slug — but the
id still lives in frontmatter because reports cite it, so this is the one identity mismatch
that survives.

It matters because the two are read by different consumers: the generated SPEC.md index
links by *filename*, while every finding cites the *frontmatter id*. When they disagree the
host's spec points at one journey and the report names another.

## Out of scope

Everything — this fixture exists to be rejected.
