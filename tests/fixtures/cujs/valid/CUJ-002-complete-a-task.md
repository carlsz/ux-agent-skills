---
id: CUJ-002
schema: 1
title: Complete a task
actor: "Returning user with 3-10 existing tasks, opens the app daily to clear finished ones"
goal: "Mark a task done and see it leave the active list"
criticality: high
entry_point: "/"
preconditions:
  - "App loaded at / with at least one incomplete task"
steps:
  - n: 1
    action: "Click the checkbox to the left of the 'Buy milk' row"
    expect: "The checkbox fills and the 'Buy milk' text takes a strikethrough"
  - n: 2
    action: "Wait for the list to settle"
    expect: "The 'Buy milk' row leaves the active list and the remaining count decrements by one"
success_criteria:
  - "'Buy milk' is absent from the active list after a full page reload"
---

# CUJ-002 — Complete a task

## Narrative

Completion is what makes the list trustworthy. If a finished task lingers, the list stops
reflecting reality and the user stops believing it — at which point capture (CUJ-001) stops
mattering too.

## Out of scope

Undo, bulk-complete, and the archive view.
