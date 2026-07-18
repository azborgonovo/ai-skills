# ai-skills

A marketplace of software-delivery skills for Claude Code.

Finished skills are grouped into focused **plugins** you can install independently — pick only the ones relevant to you. Draft skills are not published to the marketplace yet; consume them via the link script or by copying them locally.

## Plugins

Each plugin below is installable on its own from the `ai-skills` marketplace (see [Installation](#installation)).

### `decision-records`

Explore, capture, and reconstruct the reasoning behind significant decisions as durable, reviewable Decision Records.

| Skill | Description |
|---|---|
| [/decide](skills/decision-records/decide/SKILL.md) | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. |
| [/log-decision](skills/decision-records/log-decision/SKILL.md) | Captures a structured Decision Record (DR) for significant decisions. |
| [/backfill-decisions](skills/decision-records/backfill-decisions/SKILL.md) | Mines a repository's git history for past significant decisions and retroactively writes Decision Records, following the log-decision conventions. |

### `bdd`

Author, automate, and reconcile behavior specifications in Gherkin, turning system behavior into executable specs.

| Skill | Description |
|---|---|
| [/define-behavior](skills/bdd/define-behavior/SKILL.md) | Writes behavior-driven Gherkin features and scenarios as specification by example. |
| [/review-feature-suite](skills/bdd/review-feature-suite/SKILL.md) | Cross-file consistency audit for a Gherkin suite to ensure a well-defined shared language and resolve contradictions. |
| [/implement-scenarios](skills/bdd/implement-scenarios/SKILL.md) | Implements behavior for existing Gherkin scenarios outside-in: classify each scenario to the lowest verifying test level, bind a traceable test, watch it fail, then drive the code to green. |

### `code-review`

Structure and carry out code reviews with a consistent, cost-of-change-driven framework and reviewer workflows.

| Skill | Description |
|---|---|
| [/code-review-pyramid](skills/code-review/code-review-pyramid/SKILL.md) | Knowledge base for Gunnar Morling's Code Review Pyramid. |
| [/gitlab-jira-mr-review](skills/code-review/gitlab-jira-mr-review/SKILL.md) | Reviews a GitLab merge request against its linked JIRA work item and posts inline comments on the diff for you to submit. |

### `engineering-principles`

Guidelines that keep execution aligned with proven engineering practices.

| Skill | Description |
|---|---|
| [/standard-first](skills/engineering-principles/standard-first/SKILL.md) | Guides technical implementation to prefer the standard, officially-documented solutions. |

### `planning`

Shape units of work that are well-defined, verifiable, and ready to be executed.

| Skill | Description |
|---|---|
| [/work-item](skills/planning/work-item/SKILL.md) | Drafts work items with verifiable acceptance criteria, and creates them in whatever tracker is connected. |

### `authoring-skills`

Craft and sharpen Claude Code skills so they behave reliably.

| Skill | Description |
|---|---|
| [/review-skill](skills/authoring-skills/review-skill/SKILL.md) | Static audit of an existing skill's triggering, scope, structure, prose, and domain accuracy. |

## Draft skills

Not yet published to the Claude marketplace. These are **not** installable as plugins; consume them via the [link script](#via-the-link-script-symlink-based) or by copying the skill folder into your own project.

| Skill | Description |
|---|---|
| [/team-topologies](skills/drafts/team-topologies/SKILL.md) | Knowledge base for Team Topologies: team types, interaction modes, cognitive load, and Conway's Law for organizing teams for fast flow. |

## Installation

### As Claude Code plugins (recommended for repositories)

This repo is a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugins) that exposes each group above as a separate plugin, so you install only what you need.

Add the marketplace once, then install any subset of plugins:

```
/plugin marketplace add azborgonovo/ai-skills

/plugin install decision-records@ai-skills
/plugin install bdd@ai-skills
/plugin install code-review@ai-skills
/plugin install engineering-principles@ai-skills
/plugin install planning@ai-skills
/plugin install authoring-skills@ai-skills
```

Or pin your chosen plugins in a repository's `.claude/settings.json` so every human and agent session gets them automatically (enable only the ones you want):

```json
{
  "extraKnownMarketplaces": {
    "ai-skills": {
      "source": { "source": "github", "repo": "azborgonovo/ai-skills" }
    }
  },
  "enabledPlugins": {
    "decision-records@ai-skills": true,
    "bdd@ai-skills": true
  }
}
```

*Draft and external skills are not part of any plugin. Get them through the link script below.*

### Via the link script (symlink-based)

Clone the repo, then run the link script:

```bash
git clone https://github.com/azborgonovo/ai-skills
python scripts/link-skills.py
```

This links this skills published (nested under `skills/<plugin>/`) and draft (under `skills/drafts/`) — into `~/.claude/skills/`.

Symlinks mean changes in any cloned repo are immediately reflected without re-running the script.