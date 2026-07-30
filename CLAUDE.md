# Repository guidelines

Working guidelines for this repository: how work lands, how to write commits, author skills, and version plugins.

## Trunk-based development

Work lands directly on `main`. Commit to `main` rather than opening a feature branch, and push when the work is ready — no pull request, no review gate.

This overrides the usual reflex to branch before committing: here a branch adds a merge step and delays publishing without buying review, since this is a single-maintainer repository. Create a branch only when explicitly asked, or when the work genuinely cannot land in a releasable state in one go.

**What that asks of each commit**: `main` is the published state, so every commit on it should stand on its own — one logical change, tests or scripts exercised, and any plugin version already bumped in the same commit (see [Claude plugins versioning](#claude-plugins-versioning)). Split unrelated work into separate commits rather than a branch.

## Conventional commits

Write every commit as a [Conventional Commit](https://www.conventionalcommits.org): `type(scope): subject`, where `type` is `feat`/`fix`/`docs`/`refactor`/`chore`/... and `scope` is the plugin name when the change belongs to one plugin. Mark a breaking change with a `!` after the type (`feat(bdd)!: ...`) or a `BREAKING CHANGE:` line in the body.

The message is the only place the *intent* of a change lives: `git status` shows which files moved but never whether an edit is a feature, a fix, or a breaking change. [Claude plugins versioning](#claude-plugins-versioning) reads that intent to choose each plugin's SemVer bump, so the type you pick has real downstream effect.

## Skill authoring guidelines

See the `skill-authoring-style` skill for formatting and prose conventions to apply when creating a new skill or improving an existing one.

## Claude plugins versioning

See the `plugin-versioning` skill for how to bump a plugin's SemVer version before committing changes under `skills/<plugin>/`.
