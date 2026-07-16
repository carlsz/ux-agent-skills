# UX Agent Skills

**Audit, spec, design, and ship production-grade experiences for humans and agents alike.**

**[ux-agent-skills](https://github.com/carlsz/ux-agent-skills)** equips AI agents with structured workflows to specify, generate, and rigorously verify interfaces against critical user journeys, bringing production-grade UX discipline to AI-driven development. It ships personas, skills, and slash commands as a UX-focused complement to [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

## Composition — three layers

This plugin inherits the composition rule from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills):

- **Personas** (`agents/*.md`) — roles with a perspective and an output format. *The who.*
- **Skills** (`skills/<name>/SKILL.md`) — workflows with steps and exit criteria. *The how.*
- **Slash commands** (`commands/*.md`) — user-facing entry points. *The when.*

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
├── agents/                 # personas — the who
├── skills/                 # skills — the how
├── commands/               # slash commands — the when
└── references/             # source material (NN/g heuristics, persona specs)
```

> **Status:** scaffolding only. The component directories hold placeholder docs;
> personas, skills, and commands are authored from the `references/` seed material next.
