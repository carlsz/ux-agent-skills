# UX Agent Skills

**Audit, spec, and verify production-grade experiences for humans and agents alike.**

**[ux-agent-skills](https://github.com/carlsz/ux-agent-skills)** equips AI agents with structured workflows to specify, audit, and rigorously verify interfaces against critical user journeys, bringing production-grade UX discipline to AI-driven development. It ships personas, skills, and slash commands as a UX-focused complement to [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

## Commands

Slash commands that map to the UX design and software development lifecycle. Each one activates the right skills automatically. Every command is namespaced `/ux-agent-skills:<name>` to avoid colliding with `agent-skills`; the short forms in the table work when the name is unambiguous.

| What you're doing | Command | Key principle |
|-------------------|---------|---------------|
| Define critical user journeys | `/ux-spec` | Author CUJs by interview |
| Audit your UX | `/usability-audit` | Expert usability heuristic audit |
| Verify critical user journeys | `/cuj-audit` | Replay journeys using live browser sessions, report the step that broke |
| End-to-end UX audit | `/ux-audit` | Usability + accessibility + web perf + CUJs |
| View reports in a browser | `/ux-review` | Self-contained HTML — findings + screenshot walk-through flipbook |

**Composing with agent-skills.** The auditor stops at findings by design — which is exactly what
makes it compose with [agent-skills](https://github.com/addyosmani/agent-skills): hand a report's
`## Prioritized fixes` queue straight to `/spec`, `/plan`, or `/build`, since every finding already
carries a `file:line` and a concrete Recommended Fix. Then re-run
`/ux-agent-skills:usability-audit` to confirm the severity actually dropped — audit here, make
there, verify here.

## Installation

Via the marketplace:

```
/plugin marketplace add carlsz/ux-agent-skills
/plugin install ux-agent-skills@ux-agent-skills
```

Or install the plugin directly from the repo:

```
/plugin install carlsz/ux-agent-skills
```

For local development, load the working copy without installing:

```
claude --plugin-dir .
```

### Dependencies

The suite roll-up wraps [web-quality-skills](https://github.com/addyosmani/web-quality-skills)
for its accessibility and web-performance auditors, so it's declared as a dependency
(`web-quality-skills@addy-web-quality-skills`) in the plugin manifest. The usability
auditor works without it; if it isn't installed, the roll-up simply skips those two
auditors and says so.

**Optional:** installing [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)
improves the CUJ-authoring interview — `/ux-spec` uses its `interview-me` skill when present
for a sharper one-question-at-a-time flow. It's *not* a manifest dependency, so nothing breaks
without it: `/ux-spec` falls back to its own question set and tells you it did (see
[the note above](#critical-user-journeys)).

## Usability Audits

Senior UX auditor that runs an expert **heuristic evaluation** of a host app
and writes a severity-scored report into that app's repo — findings only, it never edits
your code.

```
/ux-agent-skills:usability-audit [target] [--scope <area>] [--mode static|live|hybrid]
```

- **`target`** — a URL (live) or a repo path/glob (static). Omit to infer from the running
  dev server or the repo's UI source.
- **`--scope`** — narrow to a flow or area, e.g. `--scope checkout`.
- **`--mode`** — force `static` (read source), `live` (drive the running app in a browser),
  or `hybrid` (both). Default is **auto**: prefer live when a URL/dev server is reachable,
  fall back to static, use hybrid when both are available. The mode actually used is
  recorded in the report.

**Frameworks:** Nielsen's 10 Heuristics, Shneiderman's 8 Golden Rules, AI Design Heuristics
(when the app has AI features), and NPCIS — findings de-duplicated and attributed to a
primary framework. **Severity** is scored 0–4 (0 = not a problem, omitted; 4 = catastrophe).

Reports land in the host repo under **`.ux/audits/`**:

```
<host-repo>/.ux/audits/
├── index.md                       # rolling index of every run (all auditors)
├── index.html                     # the same index, as a browsable landing page
├── assets/                        # captured screenshots (embedded as a visual walk-through)
├── usability-20260715-143000.md   # one report per run
└── usability-20260715-143000.html # its self-contained HTML companion (open in a browser)
```

In **live/hybrid** mode the auditor screenshots each key state (and every CUJ step) and
assembles them into a `## Walkthrough` in the report — a visual record of the flow, not just
failure evidence. Every report also renders to a **self-contained HTML page** beside it (see
[Visual walk-throughs](#visual-walk-throughs-and-shareable-html-reports) below).

## Critical User Journeys

Heuristics tell you a button has poor affordance; they can't tell you that the one flow your
business depends on is broken. **Critical user journeys (CUJs)** capture what your app is
*for* — as durable, machine-checkable files an auditor can replay.

**Author them by interview** with `/ux-spec`. It asks one question at a time, guessing the
descriptive parts (who the actor is, where they start, what they do) and pushing back on the
parts a verifier is graded against — each step's *observable* outcome, the success criteria,
and how critical the journey really is. Each answer becomes a file under `.ux/cujs/`, and the
journey index in your `SPEC.md` is regenerated — **ask-first, always with a diff**.

```
/ux-agent-skills:ux-spec [--cuj <id>]
```

**Verify them** with `/cuj-audit`. It replays each journey against your running app and
reports the exact step that broke, as an `auditor: cuj` report under `.ux/audits/` — the same
shared contract every other auditor emits.

```
/ux-agent-skills:cuj-audit [target] [--cuj <id|all|critical>] [--mode static|live|hybrid]
```

A passing run is `total: 0` — unusual for an auditor, so every report leads with
`P/N journeys passed, S skipped, M of T steps verified` rather than letting an empty report
read as "found nothing". A journey it couldn't replay stays counted as skipped, never folded
into a pass; a static run traces source but **cannot** produce a verified pass. Journeys live
in the host repo beside the audits:

```
<host-repo>/.ux/cujs/
├── CUJ-001-add-a-task.md
└── CUJ-002-complete-a-task.md
```

> **The interview uses [`interview-me`](https://github.com/addyosmani/agent-skills) when it's
> installed** — but that dependency is **optional and undeclared**. Unlike the roll-up's
> `web-quality-skills` (a manifest dependency), `interview-me` is *not* in `plugin.json`: if
> it's absent, `/ux-spec` falls back to its own question set, tells you it did, and offers to
> install it rather than auto-installing. The capability degrades; it never fails.

## The roll-up — every auditor, one verdict

One command runs the default auditors against a single target and merges the results:

```
/ux-agent-skills:ux-audit [target] [--scope <area>] [--only usability,accessibility,web-performance,cuj] [--all]
```

By default it fans out to the **usability**, **accessibility**, and **critical-user-journeys**
auditors — usability and CUJ native, accessibility wrapped from
[web-quality-skills](https://github.com/addyosmani/web-quality-skills), the same-author
companion to `agent-skills`. **Web performance** (also wrapped from `web-quality-skills`) is
**opt-in** — its metrics are usually dev-mode / localhost lab numbers rather than production
Core Web Vitals, so it runs only when you add `--only web-performance` or `--all`, and is
otherwise disclosed as skipped. Every result is **normalized into the shared contract**
(0–4 severity), so all reports land in one `.ux/audits/` directory, share one `index.md`,
and are summarized in a `rollup-<timestamp>.md` with a per-auditor table and an overall
**go/no-go verdict**. Auditors whose wrapping skill isn't installed are skipped and
disclosed — and the CUJ auditor is **conditional**, running only when you've authored
journeys under `.ux/cujs/` and otherwise skipped with a reason. A skip is never silently
treated as a pass. See the [roll-up skill](skills/ux-audit/SKILL.md).

## Shared reporting contract

Every auditor in this suite — usability (native), plus accessibility and web-performance
(wrapped, see the roll-up above) — emits the same
[report contract](skills/usability-audit/references/report-contract.md) — one
`.ux/audits/` directory, one frontmatter schema, one severity scale, one rolling index —
so their outputs are comparable and can be rolled up together. Only the `auditor` value and
framework vocabulary differ. Reports self-validate via
[`scripts/validate_report.py`](scripts/validate_report.py); the safety invariant (writes
stay under `.ux/audits/`) is checked by [`scripts/audit_safety.py`](scripts/audit_safety.py).

## Visual walk-throughs and shareable HTML reports

Every audit is also a **self-contained HTML page** you can open in a browser or hand to a
teammate — no server, no build, no network. Alongside each `report.md`, the auditor writes a
`report.html` (and refreshes `index.html`) with:

- **Findings as severity-badged cards** and a per-severity summary.
- **An interactive walk-through flipbook** — the screenshots the auditor captured while
  driving your app, in order: every CUJ step, or a usability flow's key states (initial /
  mid-flow / success / error / empty). Click through or use the arrow keys.
- **A go/no-go dashboard** for the roll-up, with a per-auditor severity matrix linking to each
  report, and an `index.html` landing page tying every run together.

The HTML is a **derived view** — the Markdown report stays the source of truth, so nothing you
rely on changes. Images are inlined, so the page renders offline and on GitHub alike.

The audit commands emit this HTML automatically. To (re)render reports that already exist —
after pulling a branch, or to view an older run — use `/ux-review`:

```
> /ux-agent-skills:ux-review          # render every report in .ux/audits to HTML
> /ux-agent-skills:ux-review .ux/audits/cuj-20260715-143000.md
```

## Example — auditing a real app (Sprout)

[Sprout](https://github.com/carlsz/sprout) is a small Next.js todo app. From inside its
repo, just ask in plain language — the trigger phrases route to the right skill:

```
> Do a usability audit of Sprout's task flows.
```

or invoke the command directly, pointing at a running dev server for a live pass:

```
> /ux-agent-skills:usability-audit http://localhost:3000 --scope "add / edit / complete / delete"
```

The auditor drives the flow in a browser, then writes a severity-scored report to
`Sprout/.ux/audits/usability-<timestamp>.md` — for example:

```markdown
### [sev2] Edit save/cancel is invisible and blur commits silently
- Framework Violation: Nielsen #6 — Recognition Rather than Recall (primary);
  corroborating Shneiderman #7 — Keep Users in Control.
- Evidence: Verified live — entered edit mode; the row showed only the text field with
  no Save/Cancel control or hint. Source: components/todo/TodoItem.tsx:41-62.
- Recommended Fix: add visible Save / Cancel controls or an "Enter to save · Esc to
  cancel" hint, and commit on blur only when the value changed.
```

To run the **default suite** (usability + accessibility + cuj) before shipping — add `--all`
to also include the opt-in web-performance auditor:

```
> Run a full UX audit of Sprout before launch.
> /ux-agent-skills:ux-audit http://localhost:3000
```

That writes one normalized report per auditor plus a `rollup-<timestamp>.md` with a
per-auditor severity table and a go/no-go verdict — all under `Sprout/.ux/audits/`, and
nothing else in the repo is touched.

## Contributing

Working on the plugin itself? See [AGENTS.md](AGENTS.md) for the repo layout, the
three-layer composition model (personas / skills / commands), and the recipe for adding a
component. Run the test suite with `python3 tests/test_*.py` — contract, components, safety,
docs, evals, and render-html checks; the [evals system](evals/README.md) covers trigger
routing (Tier 2, in CI) and behavioral audits against Sprout (Tier 3, on demand).
