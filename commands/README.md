# Slash commands

**Slash commands** (`commands/*.md`) — user-facing entry points. *The when.*

Each Markdown file becomes a `/ux-agent-skills:<name>` command that invokes a persona
or skill on demand. Keep them thin — a command wires a user request to the workflow
that does the work.

## Commands here

- [`usability-audit.md`](usability-audit.md) — `/ux-agent-skills:usability-audit`: run the
  usability auditor against one target.
- [`ux-audit.md`](ux-audit.md) — `/ux-agent-skills:ux-audit`: the suite roll-up across
  every available auditor.
- [`ux-spec.md`](ux-spec.md) — `/ux-agent-skills:ux-spec`: interview the user to author
  critical user journeys under `.ux/cujs/` and regenerate the host `SPEC.md` index.
- [`cuj-audit.md`](cuj-audit.md) — `/ux-agent-skills:cuj-audit`: replay the stored journeys
  and report the step that broke.
