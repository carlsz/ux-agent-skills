---
name: audit-cuj
description: Replay your stored critical user journeys against the running app and report the exact step that broke, as a severity-scored cuj report in .ux/audits. Invokes the cuj-auditor persona via the audit-cuj skill.
argument-hint: "[target] [--cuj <id|all|critical>] [--mode static|live|hybrid]"
---

# /audit-cuj

Check whether your app still does what it's **for**. This replays the journeys in `.ux/cujs/`
against your running app and tells you the exact step that broke. Thin entry point — the
[`audit-cuj`](../skills/audit-cuj/SKILL.md) skill does the work, driving the
[`cuj-auditor`](../agents/cuj-auditor.md) persona.

Journeys come from [`/ux-spec`](./ux-spec.md). Namespaced as `/ux-agent-skills:audit-cuj` to
avoid colliding with `agent-skills`.

## Arguments

`$ARGUMENTS`:

- **`target`** — a URL or repo path, e.g. `/audit-cuj http://localhost:3000`. Omit to use the
  current repo and auto-detect the dev server.
- **`--cuj <id|all|critical>`** — which journeys to replay. `all` (default), one journey
  (`--cuj CUJ-001`), or `critical` for every journey you rated `critical`.
- **`--mode static|live|hybrid`** — force an evaluation mode. Omit to auto-select.

## Behavior

1. Parse `target`, `--cuj`, and `--mode` from `$ARGUMENTS`.
2. Select the journeys from `.ux/cujs/` and validate them. **If there are none, it stops** —
   *"no CUJs authored; run `/ux-spec`"* — and writes no report.
3. Invoke the `audit-cuj` skill: establish each journey's preconditions, replay its steps
   against the app, then evaluate its success criteria separately.
4. Grade each failure — classify it, then clamp by that journey's own `criticality`.
5. Write one report per run to `.ux/audits/cuj-<timestamp>.md`, append the index row, and
   print the counts.

## What the modes actually prove

- **live** (preferred) — drives the real app. The only mode that can produce a verified pass.
- **static** — traces the route, handler, or component behind each step and asks whether the
  expected outcome is plausible. Everything it finds is labelled `potential — unverified`,
  and **it cannot pass a journey** — reading source is not watching the app work.
- **hybrid** — live where reachable, static elsewhere, reported per step.

It records the mode it *actually* used. A requested `live` that fell back for want of a
running app is reported as `static`, with the reason.

## Guarantees

- **Findings only — never edits your application code.** It reports the broken step; fixing
  it is your call.
- **Writes only under `.ux/audits/`.** Your journeys are read-only to it: an auditor that
  edits the journey it's grading is grading its own homework, so `.ux/cujs/` is a violation
  here even though `/ux-spec` may write there.
- **An empty `.ux/cujs/` stops the run rather than passing it.** "Every journey passed" is
  trivially true when there are no journeys, and a clean report you can't trust is worse than
  no report.
- **A passing run is `total: 0`** — unusual, and the reason every report leads with
  `P/N journeys passed, S skipped, M of T steps verified`. `N` counts the journeys it
  selected, not the ones it managed to run, so a journey it couldn't replay can never quietly
  disappear into a pass.
- **Ask-first** before starting a dev server, navigating a browser, or resetting app state.
