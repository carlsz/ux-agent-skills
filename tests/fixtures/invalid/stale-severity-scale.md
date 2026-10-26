---
auditor: usability
schema: 3
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: https://localhost:3000/checkout
mode: static
scope: "checkout flow"
frameworks:
  - nielsen-10
summary:
  total: 1
  sev2: 1
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

# Usability Audit — checkout flow

## Findings

### [P2] Promo-code error is vague

- **Issue Description:** Invalid promo code shows only "Error".
- **Framework Violation:** Nielsen #9 — Help Users Recognize, Diagnose, and Recover from Errors.
- **Priority:** P2 — recoverable but frustrating.
- **Evidence:** `src/checkout/PromoField.tsx:88`.
- **Recommended Fix:** state the specific reason.

## Appendix

- **Coverage / not inspected:** nothing out of scope.
