---
name: ux-audit
description: Run the default UX auditor suite (usability + accessibility + cuj) against one target — web performance is opt-in — normalize into the shared .ux/audits contract, and produce one combined go/no-go roll-up. Invokes the ux-audit skill.
argument-hint: "[target] [--scope <area>] [--only usability,accessibility,web-performance,cuj] [--all] [--mode static|live|hybrid]"
---

# /ux-audit

Fan out every available UX auditor against one target and merge the results into a single
roll-up. Thin entry point — the [`ux-audit`](../skills/ux-audit/SKILL.md) skill does the
orchestration.

Namespaced as `/ux-agent-skills:ux-audit` to avoid colliding with `agent-skills`.

## Arguments

`$ARGUMENTS`:

- **`target`** — a URL (preferred — accessibility and web performance need a render) or a
  repo path. Omit to infer from the running dev server / repo.
- **`--scope <area>`** — narrow all auditors to a flow or area, e.g. `--scope checkout`.
- **`--only <list>`** — run a subset of auditors, e.g.
  `--only usability,accessibility`. Default (no `--only`): usability, accessibility, and
  cuj — **web performance is opt-in** and runs only when you name `web-performance` here.
- **`--all`** — run every available auditor, **including web performance**. If both `--only`
  and `--all` are given, `--only` wins.
- **`--mode static | live | hybrid`** — passed through to auditors that support it
  (usability).

## Behavior

1. Discover available auditors — usability (native), accessibility (wrapping
   [`web-quality-skills`](https://github.com/addyosmani/web-quality-skills)), and critical
   user journeys (native `cuj`, **conditional** on a non-empty `.ux/cujs/`). Web performance
   (also wrapping `web-quality-skills`) is **opt-in** — it runs only via
   `--only web-performance` or `--all`, and is otherwise disclosed as skipped. Skip any that
   aren't available — a wrapped skill not installed, no CUJs authored, or web performance not
   opted into — and disclose it in the roll-up; a skipped auditor is never treated as a pass.
2. **Auth pre-flight — once, before any auditor runs.** If the target sits behind a login
   wall, hand off so *you* can sign in, then every auditor inherits that one session
   ([`auth-handoff.md`](../skills/usability-audit/references/auth-handoff.md)). Doing this
   up front means one interruption before the work starts, rather than a prompt arriving
   partway through a multi-auditor run. Decline and the run proceeds unauthenticated, with
   the gated screens disclosed as coverage gaps — it is never a reason to skip the audit.
3. Invoke the `ux-audit` skill, which runs each auditor, normalizes every result into a
   contract report under `.ux/audits/`, appends the index, and writes
   `rollup-<timestamp>.md`.
4. Print the roll-up verdict and the paths of every report written.

## Guarantees

- **Findings only** — no auditor edits host application code.
- **Writes only under `.ux/audits/`** in the host repo.
- **Never enters credentials.** Behind a login wall you sign in yourself; the auditor waits,
  confirms the session, and never records which account you used. An authenticated run
  recommends gitignoring `.ux/audits/` before it captures anything.
- A skipped auditor is disclosed, never silently treated as a pass.
