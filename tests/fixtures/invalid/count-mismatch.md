---
auditor: usability
schema: 2
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: /repo/src
mode: static
scope: "settings page"
frameworks:
  - nielsen-10
summary:
  total: 3
  sev4: 0
  sev3: 1
  sev2: 1
  sev1: 0
---

# Usability Audit — settings page

## Findings

### [sev3] No confirmation on destructive "Delete account"

- **Issue Description:** Deletes immediately with no confirm step.
- **Framework Violation:** Nielsen #5 — Error Prevention.
- **Severity:** 3 — major.
- **Evidence:** `src/settings/DangerZone.tsx:20`.
- **Recommended Fix:** add a typed confirmation.

### [sev2] Jargon label "TTL" shown to end users

- **Issue Description:** Uses internal term "TTL".
- **Framework Violation:** Nielsen #2 — Match Between System and Real World.
- **Severity:** 2 — minor.
- **Evidence:** `src/settings/CacheRow.tsx:14`.
- **Recommended Fix:** relabel to "Time before refresh".
