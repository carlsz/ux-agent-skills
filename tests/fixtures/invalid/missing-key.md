---
schema: 3
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: /repo/src
mode: static
scope: "login page"
frameworks:
  - nielsen-10
summary:
  total: 1
  p0: 0
  p1: 0
  p2: 1
  p3: 0
---

# Usability Audit — login page

## Findings

### [P2] Password rules hidden until after a failed submit

- **Issue Description:** Constraints only appear after an error.
- **Framework Violation:** Nielsen #5 — Error Prevention.
- **Priority:** P2 Minor — fix in the next pass.
- **Evidence:** `src/auth/PasswordField.tsx:31`.
- **Recommended Fix:** show the rules inline before submit.
