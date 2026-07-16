---
schema: 1
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: /repo/src
mode: static
scope: "login page"
frameworks:
  - nielsen-10
summary:
  total: 1
  sev4: 0
  sev3: 0
  sev2: 1
  sev1: 0
---

# Usability Audit — login page

## Findings

### [sev2] Password rules hidden until after a failed submit

- **Issue Description:** Constraints only appear after an error.
- **Framework Violation:** Nielsen #5 — Error Prevention.
- **Severity:** 2 — minor.
- **Evidence:** `src/auth/PasswordField.tsx:31`.
- **Recommended Fix:** show the rules inline before submit.
