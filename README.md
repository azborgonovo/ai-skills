# agent-skills

A personal directory of agent skills to extend Claude Code's capabilities.

| Skill | Description | |
|---|---|---|
| `/decide` | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. | [SKILL.md](skills/decide/SKILL.md) |
| `/log-decision` | Captures a structured Decision Record (DR) for significant decisions. | [SKILL.md](skills/log-decision/SKILL.md) |

## Installation

Skills live in `~/.claude/skills/`. Run the sync script to copy all skills from this repo:

```bash
python sync-claude-skills.py
```

This copies each subdirectory under `skills/` into `~/.claude/skills/`, overwriting existing files.
