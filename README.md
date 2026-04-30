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
| [/grill-me](https://github.com/mattpocock/skills/blob/main/skills/productivity/grill-me/SKILL.md) | Interview the user relentlessly about a plan or design until reaching shared understanding. |
| [/tdd](https://github.com/mattpocock/skills/blob/main/skills/engineering/tdd/SKILL.md) | Test-driven development with red-green-refactor loop. |

## Installation

Clone the repo, then run the link script:

```bash
git clone https://github.com/azborgonovo/agent-skills
./scripts/link-skills.sh
```

The script will:
1. Read `scripts/external-repos.conf` and clone each listed repository into the configured `CLONE_DIR` (or `git pull` if already present)
2. Symlink each local skill from `skills/` into `~/.claude/skills/`
3. Symlink each selected external skill from `scripts/external-skills.md` into `~/.claude/skills/`

Symlinks mean changes in any cloned repo are immediately reflected without re-running the script.

## Configuration

**`scripts/external-skills.conf`** — single file that configures where to clone repos and which skills to symlink:

```
CLONE_DIR=~/Code/github-azborgonovo

https://github.com/mattpocock/skills productivity/grill-me
https://github.com/mattpocock/skills engineering/tdd
```

Each skill entry is `<repo-url> <path-to-skill>`. The local folder name is derived automatically from the URL as `<owner>-<repo>` (e.g. `mattpocock-skills`).

## Updating external repositories

Re-run the link script — it automatically pulls the latest changes for already-cloned repos:

```bash
./scripts/link-skills.sh
```
