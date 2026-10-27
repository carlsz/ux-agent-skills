---
auditor: usability
schema: 3
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: /repo/src
mode: static
scope: "settings page"
frameworks:
  - nielsen-10
summary:
  total: 3
  p0: 0
  p1: 1
  p2: 1
  p3: 0
health:
  rubric: nielsen-10
  score: 4
  max: 4
  pct: 100
  band: Excellent
  items:
    - item: "Visibility of system status"
      score: 4
---

# Usability Audit — settings page

## Findings

### [P1] No confirmation on destructive "Delete account"

- **Issue Description:** Deletes immediately with no confirm step.
- **Framework Violation:** Nielsen #5 — Error Prevention.
- **Priority:** P1 Major — fix before release.
- **Evidence:** `src/settings/DangerZone.tsx:20`.
- **Recommended Fix:** add a typed confirmation.

### [P2] Jargon label "TTL" shown to end users

- **Issue Description:** Uses internal term "TTL".
- **Framework Violation:** Nielsen #2 — Match Between System and Real World.
- **Priority:** P2 Minor — fix in the next pass.
- **Evidence:** `src/settings/CacheRow.tsx:14`.
- **Recommended Fix:** relabel to "Time before refresh".
