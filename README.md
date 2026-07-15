# UX Agent Skills

**Audit, spec, design, and ship production-grade experiences for humans and agents alike.**

**[ux-agent-skills](https://github.com/carlsz/ux-agent-skills)** equips AI agents with structured workflows to specify, generate, and rigorously verify interfaces against critical user journeys, bringing production-grade UX discipline to AI-driven development. It ships personas, skills, and slash commands as a UX-focused complement to [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills).

## Composition — three layers

This plugin inherits the composition rule from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills):

- **Personas** (`agents/*.md`) — roles with a perspective and an output format. *The who.*
- **Skills** (`skills/<name>/SKILL.md`) — workflows with steps and exit criteria. *The how.*
- **Slash commands** (`commands/*.md`) — user-facing entry points. *The when.*
