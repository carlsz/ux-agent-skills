# Skills

**Skills** (`skills/<name>/SKILL.md`) — workflows with steps and exit criteria. *The how.*

Each skill is its own directory containing a `SKILL.md` (YAML frontmatter + Markdown
instructions), plus any optional reference files or scripts it needs.

A skill keeps the references it loads at run time inside its own directory so it stays
self-contained — e.g. `usability-audit/references/nng-ux-heuristics.md` (the 10
heuristics it applies) and `report-contract.md` (the shared `.ux/audits` contract). The
original persona seed, `ux-researcher.md` (the severity-report 0–4 format), remains in
[`../references/`](../references/).

_No skills defined yet — this is a scaffold._
