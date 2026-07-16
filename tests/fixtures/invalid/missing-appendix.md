---
auditor: usability
schema: 1
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: /repo/src
mode: static
scope: "profile page"
frameworks:
  - nielsen-10
summary:
  total: 1
  sev4: 0
  sev3: 0
  sev2: 1
  sev1: 0
---

# Usability Audit — profile page

## Findings

### [sev2] Save button gives no confirmation

- **Issue Description:** Saving the profile shows no success message.
- **Framework Violation:** Nielsen #1 — Visibility of System Status.
- **Severity:** 2 — minor.
- **Evidence:** `src/profile/SaveButton.tsx:19`. Verified from source.
- **Recommended Fix:** show a success toast after save.
