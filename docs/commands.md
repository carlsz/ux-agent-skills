# Slash commands

**Slash commands** (`commands/*.md`) — user-facing entry points. *The when.*

> **Why this catalog lives in `docs/`, not in `commands/README.md`.** Every `.md` file under
> `commands/` is registered as a command, frontmatter or not — a catalog there became a stray
> `/README`. Same discovery rule as `agents/`, same remedy, same guard:
> `check_discovery_dirs()` in [`../tests/test_components.py`](../tests/test_components.py).

Each Markdown file becomes a `/ux-agent-skills:<name>` command that invokes a persona
or skill on demand. Keep them thin — a command wires a user request to the workflow
that does the work.

## Commands here

- [`usability-audit.md`](../commands/usability-audit.md) — `/ux-agent-skills:usability-audit`:
  run the usability auditor against one target.
- [`accessibility-audit.md`](../commands/accessibility-audit.md) —
  `/ux-agent-skills:accessibility-audit`: run the accessibility auditor against one target.
- [`ux-audit.md`](../commands/ux-audit.md) — `/ux-agent-skills:ux-audit`: the suite roll-up.
  Default fans out to usability + accessibility + cuj; web-performance is opt-in
  (`--only`/`--all`).
- [`ux-spec.md`](../commands/ux-spec.md) — `/ux-agent-skills:ux-spec`: interview the user to
  author critical user journeys under `.ux/cujs/` and regenerate the host `SPEC.md` index.
- [`cuj-audit.md`](../commands/cuj-audit.md) — `/ux-agent-skills:cuj-audit`: replay the stored
  journeys and report the step that broke.
- [`ux-review.md`](../commands/ux-review.md) — `/ux-agent-skills:ux-review`: render existing
  `.ux/audits` reports into self-contained HTML (findings as cards, screenshots as a
  walk-through flipbook, the roll-up as a dashboard).
