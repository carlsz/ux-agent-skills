---
id: CUJ-001
schema: 1
title: Add a task to the list
actor: "Returning user with 3-10 existing tasks, opens the app daily to capture new ones"
goal: "Capture a new task from the list view without navigating away"
criticality: critical
entry_point: "/"
preconditions:
  - "App loaded at / with at least one existing task"
  - "No authentication required"
steps:
  - n: 1
    action: "Click the new-task input at the top of the list"
    expect: "The input takes focus and shows the placeholder 'What needs doing?'"
  - n: 2
    action: "Type 'Buy milk' and press Enter"
    expect: "A row reading 'Buy milk' appears at the top of the list and the input clears"
success_criteria:
  - "'Buy milk' is still present after a full page reload"
  - "No full-page navigation occurred during the journey"
---

# CUJ-001 — Add a task

## Narrative

Capturing a task is the whole product. A returning user opens the app with something in
their head and needs it recorded before the thought evaporates — if that takes more than a
few seconds or a page load, they use paper instead and never come back.

## Out of scope

Bulk import, adding a task with a due date or tag, the keyboard-only path, and the offline
queue. Each is a separate journey.
