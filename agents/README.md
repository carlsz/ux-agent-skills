# Personas

**Personas** (`agents/*.md`) — roles with a perspective and an output format. *The who.*

Each file defines a subagent with a point of view (e.g. a senior UX auditor) and a
structured way of reporting. Drop one Markdown file per persona in this directory.

Seed material for the first persona lives in [`../references/`](../references/):
- `ux-researcher.md` — a "Heuristic Evaluator" persona spec (UX-Heuristic-Bot).

The heuristics its reviews cite (`nng-ux-heuristics.md`) live beside the skill that loads
them, in [`../skills/usability-audit/references/`](../skills/usability-audit/references/),
to keep that skill self-contained.

## Personas here

- [`usability-auditor.md`](usability-auditor.md) — senior UX auditor; evaluates against
  Nielsen / Shneiderman / AI-heuristics / NPCIS and emits a 0–4 severity report. Driven by
  the [`usability-audit`](../skills/usability-audit/SKILL.md) skill.
