# Dogfood prompt — suite roll-up against Sprout

A reusable prompt for exercising `/ux-agent-skills:ux-audit` end to end in a **fresh**
Claude session, against the real [Sprout](https://github.com/carlsz/sprout) todo app.

## 1. Launch the session with both plugins

The roll-up needs this plugin (for `/ux-agent-skills:ux-audit`) plus
[`web-quality-skills`](https://github.com/addyosmani/web-quality-skills) (the wrapped
accessibility / web-performance auditors). From a terminal:

```
claude --plugin-dir /Users/carlsz/Development/Projects/ux-agent-skills-v2
```

`web-quality-skills` should already be installed in your environment. If it isn't, the
roll-up will skip accessibility/web-performance and disclose it — which is itself worth
confirming.

## 2. Paste this prompt

```
I want to dogfood the ux-agent-skills suite roll-up against a real app, end to end.

Setup:
1. Clone https://github.com/carlsz/sprout into a temp working dir, run `npm install`,
   then start its dev server (`npm run dev`) in the background and tell me the port.

Run the roll-up:
2. Once the server is up, run:
   /ux-agent-skills:ux-audit http://localhost:<port> --scope "add / edit / complete / delete a task"
3. It should fan out to three auditors — usability (native to ux-agent-skills),
   accessibility, and web performance (both wrapped from web-quality-skills). For each
   AVAILABLE auditor, drive the running app, then write a report normalized into the
   shared .ux/audits contract (0–4 severity) at Sprout/.ux/audits/<auditor>-<timestamp>.md.
   Any auditor whose wrapping skill isn't installed must be SKIPPED and disclosed in the
   roll-up — never silently passed.
4. Append one index.md row per auditor run, and write a rollup-<timestamp>.md with a
   per-auditor severity table, the skipped auditors + reasons, merged top issues, and an
   overall go/no-go verdict.

Report back to me:
5. Which auditors ran vs. were skipped (and why), the path of every report + the rollup,
   and the verdict.
6. Confirm each report validates against the shared contract and that all writes stayed
   under Sprout/.ux/audits/. Note: `npm install` may have modified package-lock.json —
   that's a setup side-effect, not an audit write, so revert it before the safety check.

Rules: findings only — do NOT edit any of Sprout's application code. Ask before doing
anything you'd need my OK for (starting the server, installing a missing skill).
```

## 3. What to verify in the result

- **The wrap works** — `accessibility-*.md` and `web-performance-*.md` reports appear,
  normalized to the 0–4 schema and validating against the shared contract. This is the
  real test of the portable contract.
- **Honest skipping** — if `web-quality-skills` isn't present, the rollup says so instead
  of reporting a clean pass.
- **Safety invariant** — after reverting `package-lock.json`, every write is confined to
  `Sprout/.ux/audits/` (check with `scripts/audit_safety.py`).
- **One roll-up verdict** — `rollup-<timestamp>.md` with the per-auditor table and a
  go/no-go call.
