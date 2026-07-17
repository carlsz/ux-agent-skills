---
auditor: usability
schema: 2
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: https://localhost:3000/checkout
mode: static
scope: "checkout flow"
frameworks:
  - nielsen-10
summary:
  total: 1
  sev4: 0
  sev3: 0
  sev2: 1
  sev1: 0
  sev0: 1
---

# Usability Audit — checkout flow

## Findings

### [sev2] Promo-code error is vague

- **Issue Description:** Invalid promo code shows only "Error".
- **Framework Violation:** Nielsen #9.
- **Severity:** 2 — minor.
- **Evidence:** `src/checkout/PromoField.tsx:88`.
- **Recommended Fix:** state the specific reason.

### [sev0] Button corner radius is 3px not 4px

- **Issue Description:** Not a usability problem.
- **Framework Violation:** none.
- **Severity:** 0 — not a usability problem.
- **Evidence:** `src/ui/Button.tsx:12`.
- **Recommended Fix:** none needed; should have been omitted.
