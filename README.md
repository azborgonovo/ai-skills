# agent-skills

A personal directory of agent skills to extend Claude Code's capabilities.

## Skills

### Local

| Skill | Description |
|---|---|
| [/backfill-decisions](skills/backfill-decisions/SKILL.md) | Mines a repository's git history for past architecturally significant decisions and retroactively writes Decision Records, following the log-decision conventions. |
| [code-review-pyramid](skills/code-review-pyramid/SKILL.md) | Knowledge base for the Code Review Pyramid — structuring reviews across five layers prioritised by cost-of-change. |
| [/decide](skills/decide/SKILL.md) | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. |
| [/define-behavior](skills/define-behavior/SKILL.md) | Writes behavior-driven Gherkin features and scenarios as specification by example — domain-level, one behavior per scenario, observable outcomes. |
| [/gitlab-jira-mr-review](skills/gitlab-jira-mr-review/SKILL.md) | Reviews a GitLab merge request against its linked JIRA ticket and posts inline comments on the diff for you to submit. |
| [/log-decision](skills/log-decision/SKILL.md) | Captures a structured Decision Record (DR) for significant decisions. |
| [/review-skill](skills/review-skill/SKILL.md) | Static audit of an existing skill's triggering, scope, structure, prose, and domain accuracy — severity-ranked findings applied on approval. |
| [/standard-first](skills/standard-first/SKILL.md) | Guides technical implementation to prefer the standard, officially-documented solution — checks built-in framework features, official docs, and package registries before writing custom code. |
| [team-topologies](skills/team-topologies/SKILL.md) | Knowledge base for Team Topologies — team types, interaction modes, cognitive load, and Conway's Law for organizing teams for fast flow. |

### External

Configured in [`scripts/external-skills.conf`](scripts/external-skills.conf) and symlinked by the link script.

| Skill | Source |
|---|---|
| grilling | [mattpocock/skills](https://github.com/mattpocock/skills) `productivity/grilling` |
| handoff | [mattpocock/skills](https://github.com/mattpocock/skills) `productivity/handoff` |
| writing-great-skills | [mattpocock/skills](https://github.com/mattpocock/skills) `productivity/writing-great-skills` |
| tdd | [mattpocock/skills](https://github.com/mattpocock/skills) `engineering/tdd` |
| improve-codebase-architecture | [mattpocock/skills](https://github.com/mattpocock/skills) `engineering/improve-codebase-architecture` |

## Installation

Clone the repo, then run the link script:

```bash
git clone https://github.com/azborgonovo/agent-skills
./scripts/link-skills.sh
```

The script will:
1. Read `scripts/external-skills.conf` and clone each listed repository into the configured `CLONE_DIR` (or `git pull` if already present)
2. Symlink each local skill from `skills/` into `~/.claude/skills/`
3. Symlink each external skill listed in `scripts/external-skills.conf` into `~/.claude/skills/`

Symlinks mean changes in any cloned repo are immediately reflected without re-running the script.

## Configuration

[`scripts/external-skills.conf`](scripts/external-skills.conf) — single file that configures where to clone repos and which external skills to symlink:

```
CLONE_DIR=~/Code/github-azborgonovo

https://github.com/mattpocock/skills productivity/grilling
https://github.com/mattpocock/skills engineering/tdd
```

Each skill entry is `<repo-url> <path-to-skill>`. The local clone folder name is derived automatically from the URL as `<owner>-<repo>` (e.g. `mattpocock-skills`).

## Updating external repositories

Re-run the link script — it automatically pulls the latest changes for already-cloned repos:

```bash
./scripts/link-skills.sh
```
