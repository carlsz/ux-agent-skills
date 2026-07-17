# AGENTS.md

Instructions for AI agents working **on this repo** — how it's laid out, how to author new
components, and which rules the tests actually enforce.

> Working on a *host app* with this plugin installed? You want [README.md](README.md). This file is
> for changing the plugin itself.

This is a Claude Code plugin. It ships no application code — every component is Markdown, and the
Python under [`scripts/`](scripts/) and [`tests/`](tests/) exists to keep that Markdown honest.

## Composition — three layers

This plugin inherits the composition rule from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills):

- **Personas** (`agents/*.md`) — roles with a perspective and an output format. *The who.*
- **Skills** (`skills/<name>/SKILL.md`) — workflows with steps and exit criteria. *The how.*
- **Slash commands** (`commands/*.md`) — user-facing entry points. *The when.*

Keep the layers honest: a persona holds the point of view and never inlines a workflow; a skill holds
the steps and its own `references/`; a command stays thin — parse args, invoke persona + skill,
nothing more. When you're unsure where something belongs, ask which of *who / how / when* it answers.

## Repo layout

```
ux-agent-skills/
├── .claude-plugin/
│   ├── plugin.json         # plugin manifest — metadata only, no component lists
│   └── marketplace.json    # marketplace catalog (self-lists this plugin)
├── agents/                 # personas — the who (usability-auditor, cuj-author, cuj-auditor)
├── skills/                 # skills — the how
│   ├── usability-audit/        # usability audit workflow + framework lenses & report contract
│   ├── ux-audit/               # the suite roll-up (fan-out + normalize + verdict)
│   ├── spec-cuj/               # author critical user journeys by interview (+ cuj-contract)
│   ├── audit-cuj/              # replay journeys, report the step that broke
│   └── render-report/          # render reports to self-contained HTML (the one non-auditor skill)
├── commands/               # slash commands — the when
├── scripts/                # validate_report.py, validate_cuj.py, audit_safety.py, render_report_html.py
├── tests/                  # contract / component / cuj-contract / safety / docs / evals / render-html checks
├── evals/                  # trigger + behavioral evals (Sprout as the target)
└── SPEC.md                 # this repo's design spec (§1–8 usability auditor, §9 CUJs, §10 walk-through + HTML) — what/why
```

**Components are auto-discovered by convention** from `agents/`, `skills/*/SKILL.md`, and
`commands/`. Adding one needs **no `plugin.json` edit** — the manifest carries metadata and
`dependencies` only. Touch it to bump `version`, or to add an external plugin you wrap (mirror any
`dependencies` change into `marketplace.json`).

## Frontmatter by layer

Every component is YAML frontmatter + a Markdown body. The fields are few and the `description` does
real work — it's the **routing corpus** (see [Triggers and routing](#triggers-and-routing)), so write
it for a matcher, not just a reader.

| Layer | Path | Frontmatter |
|-------|------|-------------|
| Persona | `agents/<name>.md` | `name`, `description` |
| Skill | `skills/<name>/SKILL.md` | `name`, `description` |
| Command | `commands/<name>.md` | `name`, `description`, `argument-hint` |

There is no separate `triggers:` key — **trigger phrases live inside `description`**, in prose. Copy
the shape from [`agents/usability-auditor.md`](agents/usability-auditor.md):

```yaml
description: Senior UX auditor that runs expert heuristic evaluation of a host app and writes a
  severity-scored report to .ux/audits. Trigger phrases include "usability audit", "heuristic
  evaluation", "UX audit", "usability review".
```

`name` must match the file (persona/command) or the **directory** (skill) — `test_evals.py` keys off
the skill's directory name, so a mismatch fails CI.

## Adding a new auditor, end to end

The suite is deliberately uniform: every auditor emits the same
[report contract](skills/usability-audit/references/report-contract.md), so a new one is mostly
conformance work. In order:

1. **`agents/<x>-auditor.md`** — the persona. Body must state the findings-only boundary, the
   render-vs-source honesty rule, the 0–4 severity format, and point at its frameworks.
2. **`skills/<x>-audit/SKILL.md`** — the workflow. Numbered steps with **explicit exit criteria**.
   Must cover static/live/hybrid modes, writing under `.ux/audits/`, and the coverage-gap rule.
3. **`skills/<x>-audit/references/`** — the framework lenses, self-contained. Personas point here;
   they don't inline heuristics.
4. **`commands/<x>-audit.md`** — thin entry point. Document `target`, `scope`, `mode`.
5. **`evals/cases/<x>-audit.json`** — **mandatory, see the trap below.** `skill_name` matching the
   directory, ≥3 positive triggers, ≥2 negatives (each naming an `owner` that exists in
   `evals/cases/competitors.json`), ≥1 behavioral eval with `id` / `prompt` / `expected_output` /
   `expectations`.
6. **`tests/test_components.py`** — hand-write a `check_<x>()` and wire it into `main()`.
   **See the trap below.**
7. **`skills/ux-audit/SKILL.md`** — add to the roll-up fan-out if it joins the suite, and update the
   auditor list in `check_rollup_skill()`.
8. **Docs** — add the file to `DOC_FILES` in `tests/test_docs.py` so its links get checked, and
   update the catalog in the relevant subdirectory README.

## The CUJ family (a second triad)

Beside the auditor suite sits the **critical-user-journey** family — two triads, not one. The
**authoring** side (`cuj-author` persona, `spec-cuj` skill, `/ux-spec` command) interviews the
user and writes journey files under the host's `.ux/cujs/`; the **verification** side
(`cuj-auditor` persona, `audit-cuj` skill, `/cuj-audit` command) is an auditor like any other,
reusing the report contract with `auditor: cuj`. Two things to keep straight when you touch it:

- **Authoring writes host docs; auditors don't.** `/ux-spec` may write `.ux/cujs/` and — only
  after asking, only the marker block, always with a diff — the host's `SPEC.md`. That does not
  weaken the findings-only invariant: auditors, `/cuj-audit` included, still write nowhere but
  `.ux/audits/`. The `audit_safety.py` allowlist is keyword-only and authoring-scoped for
  exactly this reason (SPEC.md §9.6–9.7).
- **Two files named `SPEC.md` now exist.** Say **"the host's `SPEC.md`"** (the journey index
  `/ux-spec` regenerates in an adopting app) vs **"this repo's `SPEC.md`"** (the design spec you
  are reading) explicitly — never the bare name. This repo's `SPEC.md` has no CUJ index; it has
  no journeys.
- **`audit-cuj` is a conditional roll-up member.** It joins the `/ux-audit` fan-out only when
  `.ux/cujs/` is non-empty; absent, it is skipped **with a reason**, never a silent pass. Its
  entry in `check_rollup_skill()` uses the literal `"audit-cuj"`, not `"cuj"` (which the
  CUJ-heavy body would match anywhere).

## Visual walk-throughs and the HTML companion

Two capabilities were layered onto the report contract without changing the findings-only
shape. Know both before you touch reporting.

- **The `## Walkthrough` section (report contract schema 2).** Live/hybrid auditors capture
  screenshots — per journey step (cuj), per key state (usability) — into `.ux/audits/assets/`
  with **stable names** (`cuj-<id>-step-<n>.png`, `usability-<scope>-<state>.png`), so a re-run
  overwrites rather than accumulates (prune-to-latest). They're embedded inline and assembled
  into an optional `## Walkthrough` section (after `## Findings`, before `## Appendix`, **live/
  hybrid only**). `validate_report.py` requires `schema == 2` and light-checks that walkthrough
  image paths are relative and under `./assets/`. Full spec: [SPEC.md](SPEC.md) §10.1–10.5.

- **The HTML companion (`scripts/render_report_html.py`).** A **deterministic, derived** view:
  it renders any report `.md` into a self-contained `.html` beside it (findings as cards, the
  walkthrough as an interactive flipbook, a `rollup-*.md` as a go/no-go dashboard, `index.md` as
  a landing page) — everything inlined, opens offline. The audit skills call it as their final
  step; `/ux-review` → the `render-report` skill render on demand. **The Markdown stays the
  source of truth**; the `.html` is never validated against or in place of it. Full spec: §10.6.

**`render-report` is the suite's one non-auditor skill** — so the "adding an auditor" recipe
above does *not* apply to it: no persona (a mechanical transform holds no point of view), no
`references/`, no frameworks, no findings. Its `check_render_report_skill()` asserts the
*derived-view* invariants (Markdown is canonical, output self-contained, writes confined to
`.ux/audits/`), not auditor conformance. It still trips **both test traps** like any skill: it
needs `evals/cases/render-report.json` (the loud glob) and a hand-wired `check_*` in
`test_components.py` (the silent one).

## The two test traps

The authoring rules aren't written down anywhere except the tests — and the two most important ones
fail in **opposite** directions. Know both before you add a skill.

**`test_evals.py` globs, and fails loud.** It computes `skills/*/SKILL.md` against the eval cases on
disk and requires the set difference to be empty. The moment a new `SKILL.md` exists without a
matching `evals/cases/<name>.json`, **CI goes red** — before you've written a line of the workflow.
Author the eval case alongside the skill, not after.

**`test_components.py` does not glob, and fails silent.** Every check is a hardcoded function —
`check_persona()`, `check_skill()`, `check_command()`, `check_references()`, `check_rollup_skill()`,
`check_rollup_command()` — composed by name in `main()`. A new auditor is **not** covered until you
hand-write its `check_*()` and add it there. Nothing warns you; the suite just passes while your
component goes unverified. This is the quieter and more dangerous of the two.

The same shape shows up in `test_docs.py`: `DOC_FILES` is a hardcoded list, and a path that doesn't
exist is silently skipped rather than flagged. It link-checks what it's told about — no more.

## Triggers and routing

Tier 2 evals build a stemmed TF-IDF corpus from **each `SKILL.md`'s frontmatter `description`** plus
`competitors.json`, then assert that every positive prompt ranks its own skill within `top_k` (3 by
default) and no negative prompt ranks it first. Descriptions must also stay distinct from each other:
**≥0.75 similarity is an error, ≥0.50 warns**.

Practical consequence: if a new skill's `description` reads too much like an existing one, routing
collides and CI fails. Differentiate on the vocabulary users actually type. If a negative trigger
names an `owner` not yet in `competitors.json`, add a description for it there.

## Running the checks

```
python3 tests/test_report_contract.py    # the report contract vs fixtures
python3 tests/test_components.py         # persona / skill / command / references conformance
python3 tests/test_safety.py             # writes stay under .ux/audits/
python3 tests/test_docs.py               # README literals + relative links resolve
python3 tests/test_evals.py              # every skill has a case; Tier 2 routing passes
python3 tests/test_render_html.py        # HTML companion: self-contained, deterministic, flipbook
```

CI loops over `tests/test_*.py` on Python 3.12 with `pyyaml` as the only dependency — **any new
`tests/test_*.py` is picked up automatically.** Tier 3 (behavioral, token-consuming) runs on demand
against [Sprout](https://github.com/carlsz/sprout); see [evals/README.md](evals/README.md).

Load the working copy without installing:

```
claude --plugin-dir .
```

## Boundaries

The full list lives in [SPEC.md](SPEC.md) §6. The one that governs every component here: this is a
**findings-only** suite. Auditors write reports under `.ux/audits/` in the host repo and never edit,
refactor, or "fix" host application code — the handoff to a maker is the user's call. Preserve that
boundary in anything you author; several tests assert on it, and it's the reason the suite composes
cleanly with `agent-skills`.
