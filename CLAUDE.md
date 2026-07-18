# Repository guidelines

Working guidelines for this repository: how to write commits, author skills, and version plugins.

## Conventional commits

Write every commit as a [Conventional Commit](https://www.conventionalcommits.org): `type(scope): subject`, where `type` is `feat`/`fix`/`docs`/`refactor`/`chore`/... and `scope` is the plugin name when the change belongs to one plugin. Mark a breaking change with a `!` after the type (`feat(bdd)!: ...`) or a `BREAKING CHANGE:` line in the body.

The message is the only place the *intent* of a change lives: `git status` shows which files moved but never whether an edit is a feature, a fix, or a breaking change. [Claude plugins versioning](#claude-plugins-versioning) reads that intent to choose each plugin's SemVer bump, so the type you pick has real downstream effect.

## Skill authoring guidelines

This repo holds Claude Code skills. SKILL.md files are read by Claude, not primarily by humans, so formatting should earn its tokens by helping the model parse and weight instructions — not by looking tidy. Apply these rules when creating a new skill or improving an existing one.

### Horizontal rules (`---`)

Don't use `---` as section separators between steps or sections. The `##`/`###` Markdown headers already delimit sections.

The **only** `---` that belong in a SKILL.md are the two YAML frontmatter delimiters at the very top (opening and closing the `name`/`description` block).

### Bold (`**...**`)

Bold is a signal, not decoration — and signal weakens when it's everywhere. Use it purposefully:

- **Keep it for labeled lead-ins** that act as inline sub-headers, e.g. `**Truncation check**:`, `**Why the script**:`. These help the model locate and weight a specific piece of guidance.
- **Keep it for directive anchors** on things that change behavior, e.g. `**Never** approve`, `**Always** post through the script`, `**Critical**`.
- **Drop it when it's purely cosmetic** — bolding a phrase mid-sentence for emphasis it doesn't need just dilutes the bold that does matter.

When in doubt, ask: would the model behave differently if this weren't bold? If not, leave it
plain. Don't strip bold wholesale either — losing the useful lead-ins and directives costs more in
clarity than it saves in tokens.

### Line wrapping

Don't hard-wrap prose in SKILL.md bodies. Write one line per paragraph (and one line per list item) and let the editor soft-wrap visually.

In the YAML frontmatter, a folded `description: >` block may still wrap across indented lines.

### Spelling

Use American English spelling (`behavior`, `normalize`, `canceled`) so terminology stays consistent across skills. The exception is text quoted verbatim from another source — an example string copied from a sibling skill, a real product's wording — where you keep the original rather than "correcting" the quote.

### Counter-examples and negative instructions

Prefer stating what to do over what to avoid. A bare "don't do X" leaves X sitting in context with no positive target to replace it. A clear positive rule with its reasoning is usually enough on its own.

### General principle

Prefer instructions that explain the *why* over rigid `MUST`/`NEVER` walls of formatting, and keep the always-loaded SKILL.md body lean.

Reach for a bundled `scripts/` helper (loaded only when used) when a task is *genuinely deterministic and repeated every run*. Weigh it honestly rather than defaulting to it: much of a skill's value is the model's judgment, which a rigid script can't do and can actively mislead by anchoring the model to the wrong signal; An existing tool (`Grep`/ripgrep, `Glob`) often already covers the deterministic part with no code to maintain
When unsure, stay model-only and let evidence decide — if you watch runs independently re-derive the same helper, that's the cue to extract it into `scripts/`.

## Claude plugins versioning

Each plugin under `skills/<plugin>/` pins an explicit `version` in its `.claude-plugin/plugin.json`. Claude Code treats that string as the update key, so a plugin's version **must** increase whenever any of its skills change — otherwise installed users never receive the change. Versions follow [SemVer](https://semver.org): breaking change → MAJOR, `feat` → MINOR, everything else (`fix`, `docs`, `refactor`, `chore`, ...) → PATCH — the same [Conventional Commit](#conventional-commits) type you write on the commit.

**Before every commit**, check `git status` for changed files under any `skills/<plugin>/` path (drafts under `skills/drafts/` are not plugins and are never versioned). When a plugin's skill files changed, run the bump helper with the exact Conventional Commit message you are about to commit, and include its edits in that same commit:

```
python scripts/upgrade-plugin-versions.py --message "feat(bdd): add scenario linter"
```

The script bumps only the plugins whose skill files changed, updating each one's `plugin.json` version. It is idempotent, so running it again before the commit lands will not double-bump. **Why the message**: the commit does not exist yet, so the script reads the bump level from the message you pass — use `--major`/`--minor`/`--patch` to override when the message type doesn't capture intent.

**When a commit touches more than one plugin**, the single message's level applies to every changed plugin — correct when they share one intent (a repo-wide `docs:` fix or `refactor:` bumps them all the same). When the plugins need *different* levels, prefer splitting into one commit per plugin, since a Conventional Commit describes one logical change. If they genuinely belong together, bump each plugin on its own with `--plugin`:

```
python scripts/upgrade-plugin-versions.py --plugin bdd --minor
python scripts/upgrade-plugin-versions.py --plugin decisions --patch
```

The marketplace-wide `version` in `.claude-plugin/marketplace.json` is separate: bump it by hand only for marketplace-structure changes (adding, removing, or renaming plugins).
