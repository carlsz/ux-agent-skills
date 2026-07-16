# UX Agent Skills

**Audit, spec, design, and ship production-grade experiences for humans and agents alike.**

**[ux-agent-skills](https://github.com/carlsz/ux-agent-skills)** equips AI agents with structured workflows to specify, generate, and rigorously verify interfaces against critical user journeys, bringing production-grade UX discipline to AI-driven development. It ships personas, skills, and slash commands as a UX-focused complement to [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

## Composition — three layers

This plugin inherits the composition rule from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills):

- **Personas** (`agents/*.md`) — roles with a perspective and an output format. *The who.*
- **Skills** (`skills/<name>/SKILL.md`) — workflows with steps and exit criteria. *The how.*
- **Slash commands** (`commands/*.md`) — user-facing entry points. *The when.*

## Usability Auditor

The first auditor in the suite. It runs an expert **heuristic evaluation** of a host app
and writes a severity-scored report into that app's repo — findings only, it never edits
your code.

```
/usability-audit [target] [--scope <area>] [--mode static|live|hybrid]
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
├── assets/                        # captured screenshots
└── usability-20260715-143000.md   # one report per run
```

### Shared report contract

Every auditor in this suite (usability today; accessibility, web-performance next) emits
the same [report contract](skills/usability-audit/references/report-contract.md) — one
`.ux/audits/` directory, one frontmatter schema, one severity scale, one rolling index —
so their outputs are comparable and can be rolled up together. Only the `auditor` value and
framework vocabulary differ. Reports self-validate via
[`scripts/validate_report.py`](scripts/validate_report.py); the safety invariant (writes
stay under `.ux/audits/`) is checked by [`scripts/audit_safety.py`](scripts/audit_safety.py).

## Suite roll-up

One command runs every available auditor against a single target and merges the results:

```
/ux-agent-skills:ux-audit [target] [--scope <area>] [--only usability,accessibility,web-performance]
```

It fans out to the **usability** auditor (native) plus **accessibility** and **web
performance** — the latter two wrapped from
[web-quality-skills](https://github.com/addyosmani/web-quality-skills), the same-author
companion to `agent-skills`. Every result is **normalized into the shared contract**
(0–4 severity), so all reports land in one `.ux/audits/` directory, share one `index.md`,
and are summarized in a `rollup-<timestamp>.md` with a per-auditor table and an overall
**go/no-go verdict**. Auditors whose wrapping skill isn't installed are skipped and
disclosed — never silently treated as a pass. See the
[roll-up skill](skills/ux-audit/SKILL.md).

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

## Repo layout

```
ux-agent-skills/
├── .claude-plugin/
│   ├── plugin.json         # plugin manifest
│   └── marketplace.json    # marketplace catalog (self-lists this plugin)
├── agents/                 # personas — the who (usability-auditor)
├── skills/                 # skills — the how
│   └── usability-audit/
│       ├── SKILL.md            # the audit workflow
│       └── references/         # framework lenses + the shared report contract
├── commands/               # slash commands — the when (/usability-audit)
├── scripts/                # validate_report.py, audit_safety.py
├── tests/                  # contract / component / safety / docs checks
└── references/             # original seed material (persona spec)
```

Run the checks with `python3 tests/test_report_contract.py` (and the sibling
`test_components.py`, `test_safety.py`, `test_docs.py`).
