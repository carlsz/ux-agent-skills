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
- [`ux-audit/`](ux-audit/SKILL.md) — the suite roll-up: by default fans out to usability +
  accessibility (accessibility wrapping
  [web-quality-skills](https://github.com/addyosmani/web-quality-skills)) plus the conditional
  CUJ auditor, with web-performance (also wrapped) available opt-in via `--only`/`--all`, and
  merges the results into one go/no-go verdict.
- [`spec-cuj/`](spec-cuj/SKILL.md) — author critical user journeys by interview → write each to
  `.ux/cujs/` → regenerate the host `SPEC.md` index. Holds the shared
  [`cuj-contract.md`](spec-cuj/references/cuj-contract.md).
- [`audit-cuj/`](audit-cuj/SKILL.md) — replay a stored journey against the running app and
  report the exact step that broke (`auditor: cuj`).
- [`render-report/`](render-report/SKILL.md) — render existing `.ux/audits` reports into
  self-contained, offline HTML (findings as cards, screenshots as a walk-through flipbook, the
  roll-up as a go/no-go dashboard) via [`render_report_html.py`](../scripts/render_report_html.py).
  A derived view — the Markdown stays the source of truth.
