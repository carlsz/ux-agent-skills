---
auditor: cuj
schema: 2
version: 0.1.0
date: 2026-07-16T14:00:00Z
target: http://localhost:3000
mode: live
scope: "CUJ-001"
frameworks:
  - nielsen-10
summary:
  total: 1
  sev4: 0
  sev3: 0
  sev2: 1
  sev1: 0
---

# CUJ Audit — CUJ-001

## Executive summary

Invalid fixture: a `cuj` report citing `nielsen-10`. The CUJ auditor holds no heuristics —
the host's own journey files are its only standard. A finding citing Nielsen from this
auditor is either a mis-set `auditor` field or an auditor that wandered out of its lane;
either way the report is not what it claims to be.

This fixture proves the `cuj` vocabulary is actually registered in
`FRAMEWORKS_BY_AUDITOR`. Without it, registration is untested: an unregistered auditor
passes silently, checked only for non-emptiness.

| Severity | Count |
|----------|-------|
| 4 — Catastrophe | 0 |
| 3 — Major | 0 |
| 2 — Minor | 1 |
| 1 — Cosmetic | 0 |

## Prioritized fixes

1. [sev2] CUJ-001 — placeholder finding

## Findings

### [sev2] CUJ-001 — placeholder finding

- **Issue Description:** Placeholder; this fixture exists to be rejected on its frameworks.
- **Framework Violation:** CUJ-001 "Add a task" — step 1.
- **Severity:** 2 — placeholder.
- **Evidence:** placeholder.
- **Recommended Fix:** placeholder.

## Appendix

- **Mode:** live.
- **Frameworks applied:** nielsen-10.
- **Coverage / not inspected:** nothing — placeholder fixture.
