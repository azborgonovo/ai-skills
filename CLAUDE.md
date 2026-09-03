# Repository guidelines

Working guidelines for this repository: how work lands, how to write commits, author skills and rules, and version plugins.

## Trunk-based development

Work lands directly on `main`. Commit to `main` rather than opening a feature branch, and push when the work is ready. There is no pull request and no review gate.

This overrides the usual reflex to branch before committing. This is a single-maintainer repository, so a branch adds a merge step and delays publishing without buying review. Create a branch only when the user asks for one, or when the work genuinely cannot land in a releasable state in one go.

**What that asks of each commit**: `main` is the published state, so every commit on it must stand on its own. That means one logical change, tests or scripts exercised, any plugin version already bumped, and the README already updated to match. See [Claude plugins versioning](#claude-plugins-versioning) and [Keeping the README in sync](#keeping-the-readme-in-sync). Split unrelated work into separate commits rather than a branch.

## Conventional commits

Write every commit as a [Conventional Commit](https://www.conventionalcommits.org), in the shape `type(scope): subject`. The `type` is `feat`, `fix`, `docs`, `refactor`, `chore`, or another standard type. The `scope` is the plugin name when the change belongs to one plugin. Mark a breaking change with a `!` after the type, as in `feat(bdd)!: ...`, or with a `BREAKING CHANGE:` line in the body.

The message is the only place the *intent* of a change lives. `git status` shows which files moved, and never whether an edit is a feature, a fix, or a breaking change. [Claude plugins versioning](#claude-plugins-versioning) reads that intent to choose each plugin's SemVer bump, so the type you pick has real downstream effect.

## Plain English in agent-facing markdown

Every markdown file in this repository that an agent reads as instruction is written in plain English, in the spirit of ASD-STE100 Simplified Technical English. That covers this file, `rules/`, and every `SKILL.md` with its reference and asset files. Keep sentences under 25 words, use simple tenses and active voice, and use no contractions, no semicolons, and no em-dash that splices two statements. Use `must` for a requirement, and avoid `should`, `may`, `might`, `could`, and `would`.

Two things stay exactly as they are. The first is quoted material, such as an example string, a command, or the wording of another author. The second is a `description` field, which is retrieval text held to its 1024-character cap rather than to a sentence limit.

## Skill authoring guidelines

See the `skill-authoring` skill for the conventions to apply when creating a new skill or improving an existing one. It also carries the `check_skills.py` validator to run before committing.

## Claude plugins versioning

See the `plugin-versioning` skill for how to bump a plugin's SemVer version before committing changes under `skills/<plugin>/`.

## Keeping the README in sync

`README.md` is the only listing a user reads to discover what a plugin offers. Nothing regenerates it from the `skills/` tree, so a skill that exists in code and not in the README is invisible to them.

Whenever a skill is added, removed, or renamed under `skills/<plugin>/`, update that plugin's entry in the same commit. It sits in the [Plugins](README.md#plugins) section of the README. Use the [Draft skills](README.md#draft-skills) section instead for anything under `skills/drafts/`. Each entry carries the one-line description, the `Auto` or `Manual` invocation, and the `Draft`, `Trial`, or `Adopt` status.

The same applies to `rules/`. Whenever a rule is added, removed, or renamed there, update its entry in the same commit, in the [Rules](README.md#rules) section of the README. That entry carries the one-line description and the paths that the rule is scoped to.

## Shared helpers inside a plugin

When two skills in the same plugin need the same deterministic helper, it goes in `scripts/` at the *plugin* root, which is `skills/<plugin>/scripts/`. Both skills resolve it as `${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}/scripts/<helper>`.

That expression covers both install modes. [Claude Code copies a plugin's entire directory into its cache](https://code.claude.com/docs/en/plugins-reference), so anything at the plugin root ships. The fallback covers the other mode. There, `scripts/link_claude_extensions.py` symlinks each skill directory on its own into `~/.claude/skills`, so only the resolved real path of the SKILL.md still points at the plugin root.

Sharing a helper *across* plugins does not work. A path that traverses outside the plugin root is not copied to the cache, so it breaks once installed. A second plugin that needs the same helper gets its own copy.

## Rules vs skills

Put guidance in `rules/` when it has to be in context *before* the harness acts. That covers a convention the harness violates on its first edit, where no prompt along the way makes it reach for a skill. Put guidance in `skills/` when a prompt or a task kicks it off.

Rules cost context in every session, so scope anything language-specific or stack-specific with `paths` frontmatter, and keep each file short. Rules cannot ship as a plugin, because [a plugin contributes context only through skills, agents, and hooks](https://code.claude.com/docs/en/plugins-reference). They reach other machines through `scripts/link_claude_extensions.py`, which symlinks them into `~/.claude/rules/`.
