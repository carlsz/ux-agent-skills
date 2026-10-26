---
kind: rollup
schema: 3
version: 0.5.1
date: 2026-07-16T17:20:00Z
target: http://localhost:3000
scope: "demo app — verdict the counts do not support"
verdict: GO
verdict_reason: "shipping anyway; the contrast fix is queued for next sprint"
auditors_ran: [usability, accessibility]
auditors_skipped: []
summary:
  total: 2
  p0: 0
  p1: 1
  p2: 1
  p3: 0
health:
  pct: 83
  band: Good
  method: mean-of-auditors
  trend: []
  auditors:
    - {auditor: usability, pct: 83, band: Good, unit: "Nielsen rubric"}
---

# UX Audit Roll-up — demo app

**Verdict** stated in prose here.

## Per-auditor results

| Auditor | Mode | Sev4 | Sev3 | Sev2 | Sev1 | Total | Result |
|---------|------|------|------|------|------|-------|--------|
| [usability](usability-20260715-143000.md) | hybrid | 0 | 0 | 1 | 0 | 1 | 1 minor |

## Verdict rationale

Stated above.

## Notes

Single-member roll-up used as a test fixture.
