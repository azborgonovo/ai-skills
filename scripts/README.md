# scripts

Standalone tools for working with this repository or with Claude Code, kept
separate from the `skills/` content they support or complement.

Scripts with their own supporting files (README, example data, ...) live in
their own subfolder; simple single-file scripts sit directly in `scripts/`.

Status uses the same scale as the skills above: **Adopt** (proven, use with
confidence), **Trial** (usable, still being validated), **Draft** (recently
authored, not used seriously yet).

| Script | What it does | Status |
|---|---|---|
| [`link-skills.py`](link-skills.py) | Symlinks this repo's skills (and optionally third-party ones from `personal/external-skills.conf`) into `~/.claude/skills`. See the [Installation](../README.md#via-the-link-script-symlink-based) section of the root README. | Adopt |
| [`upgrade-plugin-versions.py`](upgrade-plugin-versions.py) | Bumps a plugin's SemVer version from a Conventional Commit message before committing skill changes. See the `plugin-versioning` skill. | Adopt |
| [`ralph-loop/`](ralph-loop/README.md) | Runs a prompt file through the `claude` CLI in a loop until it prints a sentinel value or a max-iteration cap is hit. | Trial |

Run any script with `-h`/`--help` for its full option list, or open its
folder's README for background and examples.
