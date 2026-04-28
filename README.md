# agent-skills

A personal directory of agent skills to extend Claude Code's capabilities.

## Skills

### Local

| Skill | Description |
|---|---|
| [/decide](skills/decide/SKILL.md) | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. |
| [/log-decision](skills/log-decision/SKILL.md) | Captures a structured Decision Record (DR) for significant decisions. |
| [/standard-first](skills/standard-first/SKILL.md) | Guides technical implementation to prefer the standard, officially-documented solution — searches built-in framework features, official docs and package registries before writing custom code. |

### External

| Skill | Description |
|---|---|
| [/grill-me](external/mattpocock-skills/skills/productivity/grill-me/SKILL.md) | Interview the user relentlessly about a plan or design until reaching shared understanding. |
| [/tdd](external/mattpocock-skills/skills/engineering/tdd/SKILL.md) | Test-driven development with red-green-refactor loop. |

## Installation

Clone the repo with submodules, then run the link script:

```bash
git clone --recurse-submodules https://github.com/azborgonovo/agent-skills
./scripts/link-skills.sh
```

If you already cloned without `--recurse-submodules`, initialize the submodules first:

```bash
git submodule update --init --recursive
./scripts/link-skills.sh
```

This symlinks each local skill from `skills/` and each selected external skill from `external/`
into `~/.claude/skills/`, so changes in this repo are immediately reflected without re-running.

### Updating external skills

```bash
git submodule update --remote external/mattpocock-skills
```
