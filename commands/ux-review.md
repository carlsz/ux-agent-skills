---
name: ux-review
description: Render your existing .ux/audits reports into self-contained HTML — findings as cards, screenshots as an interactive walk-through flipbook, the roll-up as a go/no-go dashboard, plus an index landing page. Invokes the render-report skill.
argument-hint: "[target] [--index]"
---

# /ux-review

Turn the audit reports already sitting in your `.ux/audits/` into **self-contained HTML** you
can open in a browser or share — no server, no build. Findings render as severity-badged cards,
the captured screenshots become an interactive **walk-through flipbook**, the roll-up becomes a
**go/no-go dashboard**, and an `index.html` ties every run together. Thin entry point — the
[`render-report`](../skills/render-report/SKILL.md) skill does the work.

The audit commands already emit this HTML when they run; reach for `/ux-review` to (re)render
reports that already exist — after pulling a branch, to refresh the view, or to render an older
run. Namespaced as `/ux-agent-skills:ux-review` to avoid colliding with `agent-skills`.

## Arguments

`$ARGUMENTS`:

- **`target`** — which reports to render. A single report
  (`/ux-review .ux/audits/cuj-20260717-203805.md`), a glob (`.ux/audits/*.md`), or omit it to
  render **every** report in `.ux/audits/`.
- **`--index`** — also refresh the `index.html` landing page. Implied when rendering the whole
  directory.

## Behavior

1. Parse `target` and `--index` from `$ARGUMENTS`.
2. Locate the Markdown reports under `.ux/audits/`. **If there are none, it stops** — nothing to
   render — and points you at `/usability-audit`, `/cuj-audit`, or `/ux-audit` to produce one.
3. Invoke the `render-report` skill: render each report to a self-contained `<report>.html`
   beside it (roll-up → dashboard), then refresh `index.html`.
4. Report the files written.

## Guarantees

- **Derived view — never changes your reports.** The HTML is generated *from* the Markdown,
  which stays the source of truth. No finding, count, or verdict is altered.
- **Self-contained & offline.** Every image is inlined; the page opens from disk with no network
  access and no external references.
- **Writes only under `.ux/audits/`.** Like every auditor in this suite, it touches nothing
  else — no host application code, ever.
- **Deterministic.** Re-rendering an unchanged report produces a byte-identical page, so there
  is no diff churn.
