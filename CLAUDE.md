# Repository guidelines

Working guidelines for this repository: how work lands, how to write commits, author skills and rules, and version plugins.

## Trunk-based development

Work lands directly on `main`. Commit to `main` rather than opening a feature branch, and push when the work is ready — no pull request, no review gate.

This overrides the usual reflex to branch before committing: here a branch adds a merge step and delays publishing without buying review, since this is a single-maintainer repository. Create a branch only when explicitly asked, or when the work genuinely cannot land in a releasable state in one go.

**What that asks of each commit**: `main` is the published state, so every commit on it should stand on its own — one logical change, tests or scripts exercised, any plugin version already bumped (see [Claude plugins versioning](#claude-plugins-versioning)), and the README already updated to match (see [Keeping the README in sync](#keeping-the-readme-in-sync)). Split unrelated work into separate commits rather than a branch.

## Conventional commits

Write every commit as a [Conventional Commit](https://www.conventionalcommits.org): `type(scope): subject`, where `type` is `feat`/`fix`/`docs`/`refactor`/`chore`/... and `scope` is the plugin name when the change belongs to one plugin. Mark a breaking change with a `!` after the type (`feat(bdd)!: ...`) or a `BREAKING CHANGE:` line in the body.

The message is the only place the *intent* of a change lives: `git status` shows which files moved but never whether an edit is a feature, a fix, or a breaking change. [Claude plugins versioning](#claude-plugins-versioning) reads that intent to choose each plugin's SemVer bump, so the type you pick has real downstream effect.

## Skill authoring guidelines

See the `skill-authoring-style` skill for formatting and prose conventions to apply when creating a new skill or improving an existing one.

## Claude plugins versioning

See the `plugin-versioning` skill for how to bump a plugin's SemVer version before committing changes under `skills/<plugin>/`.

## Keeping the README in sync

`README.md` is the only listing a user actually reads to discover what a plugin offers — nothing regenerates it from the `skills/` tree, so a skill that exists in code but not in the README is invisible to them. Whenever a skill is added, removed, or renamed under `skills/<plugin>/`, update that plugin's entry in the README's [Plugins](README.md#plugins) section in the same commit (or the [Draft skills](README.md#draft-skills) section for anything under `skills/drafts/`): the one-line description, its `Auto`/`Manual` invocation, and its `Draft`/`Trial`/`Adopt` status.

The same applies to `rules/`: whenever a rule is added, removed, or renamed there, update its entry in the README's [Rules](README.md#rules) section in the same commit — the one-line description and the paths it is scoped to.

## Shared helpers inside a plugin

When two skills in the same plugin need the same deterministic helper, it goes in `scripts/` at the *plugin* root — `skills/<plugin>/scripts/`. Both skills resolve it as `${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}/scripts/<helper>`. [Claude Code copies a plugin's entire directory into its cache](https://code.claude.com/docs/en/plugins-reference), so anything at the plugin root ships; that fallback covers the other install mode, where `scripts/link_claude_extensions.py` symlinks each skill directory on its own into `~/.claude/skills` and only the SKILL.md's resolved real path still points at the plugin root.

Sharing a helper *across* plugins doesn't work: a path traversing outside the plugin root isn't copied to the cache, so it breaks once installed. A second plugin that needs the same helper gets its own copy.

## Rules vs skills

Put guidance in `rules/` when it has to be in context *before* the harness acts: conventions it would otherwise violate on its first edit, with no prompt along the way that would make it reach for a skill. Put guidance in `skills/` when a prompt or a task kicks it off.

Rules cost context in every session, so scope anything language- or stack-specific with `paths` frontmatter and keep each file short. Rules cannot ship as a plugin — [a plugin contributes context only through skills, agents, and hooks](https://code.claude.com/docs/en/plugins-reference) — so they reach other machines through `scripts/link_claude_extensions.py`, which symlinks them into `~/.claude/rules/`.
