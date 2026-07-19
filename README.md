# ai-skills

A marketplace of software-delivery skills for Claude Code.

Finished skills are grouped into focused **plugins** you can install independently — pick only the ones relevant to you. Draft skills are not published to the marketplace yet; consume them via the link script or by copying them locally.

## Plugins

Each plugin below is installable on its own from the `ai-skills` marketplace (see [Installation](#installation)).

The **Invocation** column shows how each skill is triggered. *Model or user* skills auto-trigger when Claude judges them relevant and can also be run with their `/slash-command`. *User-only* skills set `disable-model-invocation: true` — Claude never triggers them on its own, so they run only when you invoke the `/slash-command` explicitly (used for skills with external side effects or heavy operations that shouldn't start unbidden).

### `decisions`

Explore, capture, and reconstruct the reasoning behind significant decisions as durable, reviewable Decision Records.

| Skill | Description | Invocation |
|---|---|---|
| [/decide](skills/decisions/decide/SKILL.md) | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. | Model or user |
| [/log-decision](skills/decisions/log-decision/SKILL.md) | Captures a structured Decision Record (DR) for significant decisions. | Model or user |
| [/backfill-decisions](skills/decisions/backfill-decisions/SKILL.md) | Mines a repository's git history for past significant decisions and retroactively writes Decision Records, following the log-decision conventions. | User-only |

### `bdd`

Author, automate, and reconcile behavior specifications in Gherkin, turning system behavior into executable specs.

| Skill | Description | Invocation |
|---|---|---|
| [/define-behavior](skills/bdd/define-behavior/SKILL.md) | Writes behavior-driven Gherkin features and scenarios as specification by example. | Model or user |
| [/review-feature-suite](skills/bdd/review-feature-suite/SKILL.md) | Cross-file consistency audit for a Gherkin suite to ensure a well-defined shared language and resolve contradictions. | Model or user |
| [/implement-scenarios](skills/bdd/implement-scenarios/SKILL.md) | Implements behavior for existing Gherkin scenarios outside-in: classify each scenario to the lowest verifying test level, bind a traceable test, watch it fail, then drive the code to green. | Model or user |

### `code-review`

Structure and carry out code reviews with a consistent, cost-of-change-driven framework and reviewer workflows.

| Skill | Description | Invocation |
|---|---|---|
| [/code-review-pyramid](skills/code-review/code-review-pyramid/SKILL.md) | Knowledge base for Gunnar Morling's Code Review Pyramid. | Model or user |
| [/gitlab-jira-mr-review](skills/code-review/gitlab-jira-mr-review/SKILL.md) | Reviews a GitLab merge request against its linked JIRA work item and posts inline comments on the diff for you to submit. | User-only |

### `engineering-practices`

Guidelines that keep execution aligned with proven engineering practices.

| Skill | Description | Invocation |
|---|---|---|
| [/standard-first](skills/engineering-practices/standard-first/SKILL.md) | Guides technical implementation to prefer the standard, officially-documented solutions. | Model or user |

### `planning`

Shape units of work that are well-defined, verifiable, and ready to be executed.

| Skill | Description | Invocation |
|---|---|---|
| [/work-item](skills/planning/work-item/SKILL.md) | Drafts work items with verifiable acceptance criteria, and creates them in whatever tracker is connected. | Model or user |

### `authoring-skills`

Craft and sharpen Claude Code skills so they behave reliably.

| Skill | Description | Invocation |
|---|---|---|
| [/review-skill](skills/authoring-skills/review-skill/SKILL.md) | Static audit of an existing skill's triggering, scope, structure, prose, and domain accuracy. | Model or user |

## Draft skills

Not yet published to the Claude marketplace. These are **not** installable as plugins; consume them via the [link script](#via-the-link-script-symlink-based) or by copying the skill folder into your own project.

| Skill | Description | Invocation |
|---|---|---|
| [/team-topologies](skills/drafts/team-topologies/SKILL.md) | Knowledge base for Team Topologies: team types, interaction modes, cognitive load, and Conway's Law for organizing teams for fast flow. | Model or user |

## Installation

### As Claude Code plugins (recommended for repositories)

This repo is a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugins) that exposes each group above as a separate plugin, so you install only what you need.

Add the marketplace once, then install any subset of plugins:

```
/plugin marketplace add azborgonovo/ai-skills

/plugin install decisions@ai-skills
/plugin install bdd@ai-skills
/plugin install code-review@ai-skills
/plugin install engineering-practices@ai-skills
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
    "decisions@ai-skills": true,
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