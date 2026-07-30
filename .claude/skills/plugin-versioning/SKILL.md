---
name: plugin-versioning
description: How to bump a plugin's SemVer version in .claude-plugin/plugin.json before committing changes under skills/<plugin>/. Use before every commit that touches a plugin's skill files (drafts under skills/drafts/ are exempt), and when a commit spans multiple plugins that need different bump levels.
---

Each plugin under `skills/<plugin>/` pins an explicit `version` in its `.claude-plugin/plugin.json`. Claude Code treats that string as the update key, so a plugin's version **must** increase whenever any of its skills change — otherwise installed users never receive the change. Versions follow [SemVer](https://semver.org): breaking change → MAJOR, `feat` → MINOR, everything else (`fix`, `docs`, `refactor`, `chore`, ...) → PATCH — the same Conventional Commit type you write on the commit.

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

**Working across several commits on an unmerged branch**: the script bumps relative to HEAD, so calling it once per commit compounds — each new commit's HEAD already includes the previous bump, so a branch with three `feat`-sized commits ends up three versions higher than it needs to, since none of those intermediate versions were ever released (`main` never saw them; only the version present when the branch finally merges is real). Bump once for the whole branch instead, sized to the highest-order Conventional Commit type across all its commits — a single `feat` anywhere means MINOR for the branch as a whole, even if other commits on it are `fix`/`docs`/`chore`. If you already bumped per-commit before noticing, collapse it: reset `version` back to what it was before the branch started, then bump once at that level.
