# agent-skills

A personal directory of agent skills to extend Claude Code's capabilities.

| Skill | Description |
|---|---|
| [/decide](skills/decide/SKILL.md) | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. |
| [/log-decision](skills/log-decision/SKILL.md) | Captures a structured Decision Record (DR) for significant decisions. |
| [/docs-first](skills/docs-first/SKILL.md) | Guides technical implementation to prefer the simplest, officially-documented solution — searches official docs and package registries before writing custom code. |

## Installation

Skills live in `~/.claude/skills/`. Run the sync script to copy all skills from this repo:

```bash
python sync-claude-skills.py
```

This copies each subdirectory under `skills/` into `~/.claude/skills/`, overwriting existing files.
