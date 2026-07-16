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
├── agents/                 # personas — the who
├── skills/                 # skills — the how
│   ├── usability-audit/
│   │   ├── SKILL.md            # the usability audit workflow
│   │   └── references/         # framework lenses + the shared report contract
│   └── ux-audit/
│       └── SKILL.md            # the suite roll-up (fan-out + normalize + verdict)
├── commands/               # slash commands — the when
├── scripts/                # validate_report.py, audit_safety.py
├── tests/                  # contract / component / safety / docs / evals checks
├── evals/                  # trigger + behavioral evals (Sprout as the target)
└── SPEC.md                 # design spec for the usability auditor (what/why, not how-to)
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
