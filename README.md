# ai-skills

Skills, rules, and tools that improve how AI harnesses do **software delivery** work.

Install the skills as Claude plugins, or clone this repository and symlink them into your own folders.

Status shows how mature each skill is:
- *Adopt*: proven on real work, use it with confidence
- *Trial*: usable and worth a try, still under validation
- *Draft*: written recently, not used on real work yet

Invocation shows [who can trigger a skill](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill):
- *Auto*: Claude runs it when the task fits, and you can still call it directly
- *Manual*: only you run it, with `/skill-name`

## Plugins

You install each plugin below on its own, from the `ai-skills` marketplace (see [Installation](#installation)).

### `bdd`

Author, automate, and reconcile behavior specifications in Gherkin, turning system behavior into executable specs.

- **[/define-behavior](skills/bdd/define-behavior/SKILL.md)** — Writes behavior-driven Gherkin features and scenarios as specification by example. *Auto · Adopt*
- **[/implement-scenarios](skills/bdd/implement-scenarios/SKILL.md)** — Implements the behavior for Gherkin scenarios that exist, from the outside in. It puts each scenario at the lowest test level that verifies it, and binds a traceable test to it. The test fails first, then the code makes it pass. *Auto · Trial*
- **[/review-feature-suite](skills/bdd/review-feature-suite/SKILL.md)** — Audits a Gherkin suite across files, so the suite keeps one shared language, and resolves the contradictions it finds. *Auto · Adopt*

### `code-review`

Structure and carry out code reviews with a consistent, cost-of-change-driven framework and reviewer workflows.

- **[/code-review-pyramid](skills/code-review/code-review-pyramid/SKILL.md)** — Knowledge base for Gunnar Morling's Code Review Pyramid. *Auto · Adopt*
- **[/review-changes](skills/code-review/review-changes/SKILL.md)** — Reviews the diff since a fixed point against the Code Review Pyramid, then reports one verdict: approved, approved with suggestions, or request changes. *Auto · Trial*
- **[/pr-review](skills/code-review/pr-review/SKILL.md)** — Reviews a merge request on GitLab, or a pull request on GitHub, against its linked work item with `/review-changes`. It then posts the findings as inline comments, and approves or requests changes to match the verdict. The `draft` and `comments-only` modes hold back one half or the other. *Manual · Adopt*
- **[/address-pr-comments](skills/code-review/address-pr-comments/SKILL.md)** — Triages every open review thread on a merge request or a pull request. It fixes (or push backon) what the thread asks for, then replies to the thread and resolves it. *Manual · Trial*

### `decisions`

Explore, capture, and reconstruct the reasoning behind significant decisions as durable, reviewable Decision Records.

- **[/decide](skills/decisions/decide/SKILL.md)** — Works as a thinking partner. It explores a problem and the options for it, before you make a decision. *Auto · Adopt*
- **[/log-decision](skills/decisions/log-decision/SKILL.md)** — Captures a structured Decision Record (DR) for a significant decision. *Auto · Adopt*
- **[/backfill-decisions](skills/decisions/backfill-decisions/SKILL.md)** — Mines the git history of a repository for significant decisions from the past. It then writes a Decision Record for each one, with the log-decision conventions. *Manual · Trial*

### `agent-docs`

Author and tighten the docs that steer AI coding agents — a single SKILL.md or a repo's full CLAUDE.md/AGENTS.md/editor-rules corpus.

- **[/review-skill](skills/agent-docs/review-skill/SKILL.md)** — Audits a skill that exists, for its triggering, scope, structure, prose, and domain accuracy. *Auto · Adopt*
- **[/tune-agent-docs](skills/agent-docs/tune-agent-docs/SKILL.md)** — Reviews every markdown file that steers an AI agent in a repository as one corpus, then tightens them. That covers CLAUDE.md, AGENTS.md, the Cursor, Cline, Windsurf, and Kiro rules, and the Copilot instructions. *Auto · Trial*

### `engineering-practices`

Guidelines that keep execution aligned with proven engineering practices.

- **[/standard-first](skills/engineering-practices/standard-first/SKILL.md)** — Guides technical implementation to prefer the standard, officially documented solution. *Auto · Adopt*

### `planning`

Shape units of work that are well-defined, verifiable, and ready to be executed, and triage existing ones against the codebase.

- **[/work-item](skills/planning/work-item/SKILL.md)** — Drafts a work item with verifiable acceptance criteria, and creates it in whatever tracker is connected. *Auto · Adopt*
- **[/triage-work-item](skills/planning/triage-work-item/SKILL.md)** — Triages a work item in the tracker from end to end, and reads the telemetry it can reach. It then posts the root-cause analysis back to the item as a comment. *Auto · Adopt*

## Draft skills

These skills are not on the Claude marketplace yet, so you cannot install them as plugins. Use the [link script](#via-the-link-script-symlink-based) instead, or copy the skill folder into your own project.

- **[/pareto](skills/drafts/pareto/SKILL.md)** — Ranks the causes behind most of an outcome. It then spends about a fifth of the effort on the actions that address those causes, and reports what the effort bought. *Manual · Draft*
- **[/team-topologies](skills/drafts/team-topologies/SKILL.md)** — Knowledge base for Team Topologies: team types, interaction modes, cognitive load, and Conway's Law, to organize teams for fast flow. *Auto · Draft*

## Rules

A rule is a standing instruction and can only be installed via [symlink](#via-the-link-script-symlink-based). It loads into every session, and you do not invoke it like a skill. A rule holds a
convention that must be in context *before* the model writes the first line, because a skill arrives too late.

A rule with `paths` frontmatter loads only when the harness touches a file that matches.

- **[`code-comments.md`](rules/code-comments.md)** — Sets the default to no comment, and allows one only for the
  non-obvious *why*, on the line that is easy to get wrong. The rule also sets scope and volume. It allows a
  documentation comment on public API only, and no comment at all on tests. It asks for the constraint instead of the
  reasoning that reached it. A comment is one or two lines, and the density stays at the level of the code around it.
  *All files*
- **[`csharp-xml-docs.md`](rules/csharp-xml-docs.md)** — Covers the C# mechanics only, for a documentation comment that
  the comments rule allows. It gives the tags that Microsoft recommends, and starts the comment at `<summary>`. It
  prefers `<inheritdoc/>` over a restatement of the interface, and holds `<remarks>` to contract detail. *`**/*.cs`*

## Tools

These tools use AI harnesses. A skill works the other way around, because a harness uses the skill.

- **[`ralph_loop.py`](tools/ralph-loop/README.md)** — Runs a prompt file through the `claude` CLI in a loop. The loop stops when the agent prints a sentinel value, or when it reaches the maximum number of iterations. *Trial*

## Installation

### Skills

#### As Claude Code plugins

This repository is a Claude Code [plugin marketplace](https://code.claude.com/docs/en/plugins). Each group above is a separate plugin, so you install only what you need.

Add the marketplace one time, then install the plugins you want:

```
/plugin marketplace add azborgonovo/ai-skills

/plugin install decisions@ai-skills
/plugin install bdd@ai-skills
/plugin install code-review@ai-skills
/plugin install engineering-practices@ai-skills
/plugin install planning@ai-skills
/plugin install agent-docs@ai-skills
```

You can also pin the plugins you want in the `.claude/settings.json` file of a repository. Every session, human or agent, then loads them:

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

#### Via the link script (symlink-based)

Clone the repository, then run the link script:

```bash
git clone https://github.com/azborgonovo/ai-skills
python scripts/link_claude_extensions.py
```

The script links every skill into `~/.claude/skills/`, both the published ones under `skills/<plugin>/` and the drafts
under `skills/drafts/`. It links every rule under `rules/` into `~/.claude/rules/`.

The links point back at your clone, so a change in the clone applies at once. You do not run the script again.

### Rules

Rules ship through the link script above only, because no plugin carries a rule. The script links them file by file
into `~/.claude/rules/`, where they apply to every project on the machine. It does not touch a rule that you wrote by
hand in the same folder.

To apply a rule to one project instead of every project, link it into the `.claude/rules/` folder of that project:

```bash
ln -s ~/code/github-azborgonovo/ai-skills/rules/csharp-xml-docs.md .claude/rules/csharp-xml-docs.md
```

### Tools

A tool is a plain script that you run from a clone. It is not a plugin, and the link script does not touch it.
Clone the repository, then run the script of the tool with its interpreter:

```bash
git clone https://github.com/azborgonovo/ai-skills
python tools/ralph-loop/ralph_loop.py
```

For usage and requirements, read the README of the tool, for example [`tools/ralph-loop/README.md`](tools/ralph-loop/README.md).
