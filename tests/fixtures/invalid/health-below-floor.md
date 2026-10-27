---
auditor: cuj
schema: 3
version: 0.1.0
date: 2026-07-16T12:00:00Z
target: https://localhost:3000
mode: live
scope: "CUJ-001"
frameworks:
  - cuj-contract
  - task-completion
summary:
  total: 1
  p0: 0
  p1: 0
  p2: 0
  p3: 1
health:
  rubric: task-completion
  score: 4
  max: 8
  pct: 50
  band: Acceptable
  items:
    - item: "CUJ-001 step 1 - seed a task"
      score: 0
      note: "the hint copy differed by one word"
    - item: "CUJ-001 step 2 - the row persists"
      score: 4
---

# CUJ Audit — CUJ-001

The only finding is a `P3`, yet a step is scored `0` — the worst mark available — so the
scorecard reads far harsher than the run's own grading of the same observation.

## Findings

### [P3] Hint copy differs from the journey by one word
- **Issue Description:** The journey expects a "4 to bloom" hint; the app renders
  "4 more to bloom". The count, the stage and the progress bar all matched.
- **Framework Violation:** CUJ-001 "Seed a task" — step 1 `expect` (cuj-contract).
- **Priority:** P3 Polish — fix if time allows. Cosmetic copy divergence on a
  non-load-bearing hint; the step's outcome was achieved.
- **Evidence:** live, verified — hint text read back from the DOM at step 1.
- **Recommended Fix:** align the hint copy with the journey, or update the journey.

## Appendix

- **Coverage / not inspected:** nothing out of scope.
