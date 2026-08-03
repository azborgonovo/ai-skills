# ai-skills

Skills and tools carefully crafted to enhance **software delivery** capabilities of AI harnesses.

Use them as Claude Plugins or simply clone this repository and symlink skills into your own folders. 

Status reflects the maturity of each skill based on my usage and results I achieved with them:
- **Adopt**: proven on real work, use with confidence
- **Trial**: usable and worth trying, still being validated
- **Draft**: recently authored, not used seriously yet

Invocation reflects [who can trigger a skill](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill):
- **Auto**: Claude invokes it automatically when relevant, and you can still call it directly
- **Manual**: only you invoke it, with `/skill-name`

## Plugins

Each plugin below is installable on its own from the `ai-skills` marketplace (see [Installation](#installation)).

> Note:  Plugins with *hooks* fire on the matching event in every session, wheter or not you use the plugin's skill. That's why hooks are listed in a separate table and shipped as standalone plugins.

### `bdd`

Author, automate, and reconcile behavior specifications in Gherkin, turning system behavior into executable specs.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [/define-behavior](skills/bdd/define-behavior/SKILL.md) | Writes behavior-driven Gherkin features and scenarios as specification by example. | Auto | Adopt |
| [/review-feature-suite](skills/bdd/review-feature-suite/SKILL.md) | Cross-file consistency audit for a Gherkin suite to ensure a well-defined shared language and resolve contradictions. | Auto | Adopt |
| [/implement-scenarios](skills/bdd/implement-scenarios/SKILL.md) | Implements behavior for existing Gherkin scenarios outside-in: classify each scenario to the lowest verifying test level, bind a traceable test, watch it fail, then drive the code to green. | Auto | Trial |

### `code-review`

Structure and carry out code reviews with a consistent, cost-of-change-driven framework and reviewer workflows.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [/code-review-pyramid](skills/code-review/code-review-pyramid/SKILL.md) | Knowledge base for Gunnar Morling's Code Review Pyramid. | Auto | Adopt |
| [/pr-review](skills/code-review/pr-review/SKILL.md) | Reviews a GitLab MR or GitHub PR against its linked tracker ticket and posts inline comments on the diff for you to submit. | Manual | Adopt |

### `decisions`

Explore, capture, and reconstruct the reasoning behind significant decisions as durable, reviewable Decision Records.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [/decide](skills/decisions/decide/SKILL.md) | Collaborative thinking-partner for exploring a problem and its options before arriving at a decision. | Auto | Adopt |
| [/log-decision](skills/decisions/log-decision/SKILL.md) | Captures a structured Decision Record (DR) for significant decisions. | Auto | Adopt |
| [/backfill-decisions](skills/decisions/backfill-decisions/SKILL.md) | Mines a repository's git history for past significant decisions and retroactively writes Decision Records, following the log-decision conventions. | Manual | Trial |

### `agent-docs`

Author and tighten the docs that steer AI coding agents — a single SKILL.md or a repo's full CLAUDE.md/AGENTS.md/editor-rules corpus.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [/review-skill](skills/agent-docs/review-skill/SKILL.md) | Static audit of an existing skill's triggering, scope, structure, prose, and domain accuracy. | Auto | Adopt |
| [/tune-agent-docs](skills/agent-docs/tune-agent-docs/SKILL.md) | Reviews every AI-steering markdown file in a repo (CLAUDE.md, AGENTS.md, Cursor/Cline/Windsurf/Kiro rules, Copilot instructions) together as one corpus and tightens them. | Auto | Trial |

### `engineering-practices`

Guidelines that keep execution aligned with proven engineering practices.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [/standard-first](skills/engineering-practices/standard-first/SKILL.md) | Guides technical implementation to prefer the standard, officially-documented solutions. | Auto | Adopt |

### `planning`

Shape units of work that are well-defined, verifiable, and ready to be executed, and triage existing ones against the codebase.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [/work-item](skills/planning/work-item/SKILL.md) | Drafts work items with verifiable acceptance criteria, and creates them in whatever tracker is connected. | Auto | Adopt |
| [/triage-work-item](skills/planning/triage-work-item/SKILL.md) | Triages a tracker work item end-to-end, including available telemetry access, and post a comment with the root-cause analysis back to the item. | Auto | Adopt |

## Draft skills

Not yet published to the Claude marketplace. These are **not** installable as plugins; consume them via the [link script](#via-the-link-script-symlink-based) or by copying the skill folder into your own project.

| Skill | Description | Invocation | Status |
|---|---|---|---|
| [atlassian-identity-cache](skills/drafts/atlassian-identity-cache/SKILL.md) | Resolves and self-heals a local on-disk cache mapping Jira project-key prefixes to Atlassian cloud IDs, and cloud IDs to tracker account IDs, so Atlassian MCP calls skip re-resolving them every run. | Auto | Trial |
| [/pareto](skills/drafts/pareto/SKILL.md) | Ranks the causes driving most of an outcome, then spends roughly a fifth of the effort on the interventions that address them and reports what that bought. | Manual | Draft |
| [/team-topologies](skills/drafts/team-topologies/SKILL.md) | Knowledge base for Team Topologies: team types, interaction modes, cognitive load, and Conway's Law for organizing teams for fast flow. | Auto | Draft |

## Tools

Tools that use AI harnesses rather than being used by them, like skills.

| Tool | What it does | Status |
|---|---|---|
| [`ralph-loop.py`](tools/ralph-loop/README.md) | Runs a prompt file through the `claude` CLI in a loop until it prints a sentinel value or a max-iteration cap is hit. | Trial |

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
/plugin install agent-docs@ai-skills
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