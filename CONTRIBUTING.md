# Contributing

Thanks for considering a contribution. This is a Claude Code plugin — every component is Markdown,
and the Python under [`scripts/`](scripts/) and [`tests/`](tests/) exists to keep that Markdown
honest.

**Authoring reference:** [AGENTS.md](AGENTS.md) is the how-to — repo layout, the three-layer
composition rule, frontmatter per layer, and the end-to-end checklist for adding a new auditor. This
file covers process: what to work on, and what a mergeable PR looks like. Read AGENTS.md before you
write a component; read this before you open a PR.

## Setup

Load the working copy without installing:

```
claude --plugin-dir .
```

Tests need Python 3.12 and `pyyaml` — that's the only dependency.

```
pip install pyyaml
for t in tests/test_*.py; do python3 "$t"; done
```

All five must pass before you push. CI runs the same loop, so a green local run means a green PR.

## What to work on

Good contributions, roughly in order of usefulness:

- **A new auditor** joining the suite — the [AGENTS.md checklist](AGENTS.md#adding-a-new-auditor-end-to-end)
  walks the whole path. Open an issue first; a new auditor is a suite-level decision, and the roll-up
  and its test both hardcode the auditor list.
- **Sharpening an existing skill's workflow** — clearer steps, better exit criteria, fewer ways for
  an agent to go off the rails.
- **Framework references** — corrections or additions under a skill's `references/`.
- **Evals** — more trigger cases, better behavioral expectations. These are cheap to add and directly
  raise confidence in routing.

If you're unsure whether something fits, open an issue before building it. The suite is deliberately
narrow, and a well-argued "no" is faster than a rejected PR.

## The one hard boundary

**This is a findings-only suite.** Auditors write reports under `.ux/audits/` in the host repo and
never edit, refactor, or "fix" host application code. That constraint is load-bearing — it's what
makes the suite safe to point at a repo you care about, and what lets it compose with a maker like
[agent-skills](https://github.com/addyosmani/agent-skills). Several tests assert on it, and
[SPEC.md](SPEC.md) §6 lists the full set of boundaries alongside it (never fabricate findings or
evidence, never overwrite a prior report, never publish one externally).

A PR that erodes this won't be merged, however convenient the shortcut. If you think the boundary is
wrong, argue that in an issue — don't route around it in code.

## Pull requests

- **Branch from `main`** and keep the PR to one concern.
- **Run the tests.** If you added a component, confirm you also wired up its checks — `test_components.py`
  does *not* auto-discover, so an unwired component passes CI while being entirely unverified. See
  [the test traps](AGENTS.md#the-two-test-traps).
- **Add an eval case** for any new skill. `test_evals.py` enforces this and will fail immediately, but
  knowing up front saves you the red build.
- **Update [CHANGELOG.md](CHANGELOG.md)** under `## [Unreleased]`, in the existing
  [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) sections. Write the entry for someone
  deciding whether to upgrade, not for someone reading the diff.
- **Don't bump the version** in your PR — maintainers cut releases (see below).
- **Match the house voice** in docs: second person, bold lead-ins on bullets, em-dashes, concrete
  over abstract. Read a neighbouring file before writing a new one.

## Releases

Maintainers only. The project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Cutting a release means:

1. Bump `version` in [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) — the single source of
   truth for the plugin version. Components are auto-discovered, so nothing else in the manifest
   changes unless a dependency did.
2. Update the plugin version line in [SPEC.md](SPEC.md).
3. Promote `## [Unreleased]` in [CHANGELOG.md](CHANGELOG.md) to the new version with today's date, and
   open a fresh `## [Unreleased]`.

Note the two unrelated version numbers in report frontmatter: `version:` is the **emitting auditor's**
version (tracks the plugin) and `schema:` is the **report-contract** version, which changes only when
the contract itself does — a breaking contract change is a much bigger deal than a release. See the
[report contract](skills/usability-audit/references/report-contract.md).
