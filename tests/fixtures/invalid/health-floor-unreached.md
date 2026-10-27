---
auditor: usability
schema: 3
version: 0.1.0
date: 2026-07-15T14:30:00Z
target: https://localhost:3000/checkout
mode: live
scope: "checkout flow"
frameworks:
  - nielsen-10
summary:
  total: 1
  p0: 1
  p1: 0
  p2: 0
  p3: 0
health:
  rubric: nielsen-10
  score: 8
  max: 8
  pct: 100
  band: Excellent
  items:
    - item: "Visibility of system status"
      score: 4
    - item: "Error prevention"
      score: 4
---

# Usability Audit — checkout flow

A `P0` was filed and the scorecard is flawless: the worst finding landed on no item, so
the dial reports a perfect product over a blocking defect.

## Findings

### [P0] Checkout cannot be completed at all
- **Issue Description:** "Place order" never submits; the cart cannot be converted.
- **Framework Violation:** Nielsen #1 — Visibility of System Status.
- **Priority:** P0 Blocking — fix immediately. No workaround exists (tie-breaker 2).
- **Evidence:** live, verified — `app/checkout/page.tsx:88` never calls the mutation.
- **Recommended Fix:** wire the submit handler to the order mutation.

## Appendix

- **Coverage / not inspected:** nothing out of scope.
