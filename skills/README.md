# Skills

**Skills** (`skills/<name>/SKILL.md`) — workflows with steps and exit criteria. *The how.*

Each skill is its own directory containing a `SKILL.md` (YAML frontmatter + Markdown
instructions), plus any optional reference files or scripts it needs.

A skill keeps the references it loads at run time inside its own directory so it stays
self-contained — e.g. `usability-audit/references/nng-ux-heuristics.md` (the 10
heuristics it applies) and `report-contract.md` (the shared `.ux/audits` contract).

## Skills here

- [`usability-audit/`](usability-audit/SKILL.md) — the usability heuristic-evaluation
  workflow (static / live / hybrid). Also holds the framework lenses and the shared
  [`report-contract.md`](usability-audit/references/report-contract.md).
- [`ux-audit/`](ux-audit/SKILL.md) — the suite roll-up: fans out to usability +
  accessibility + web-performance (wrapping
  [web-quality-skills](https://github.com/addyosmani/web-quality-skills)) and merges the
  results into one go/no-go verdict.
