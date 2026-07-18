#!/usr/bin/env python3
"""Bump plugin versions from Conventional Commits when a plugin's skills change.

Run this *before* committing skill changes. It compares the working tree against
HEAD, finds which plugins have changed files under `skills/<plugin>/`, and bumps
each affected plugin's `version` in its `plugin.json` from the Conventional
Commit type of the commit you are about to make.

Bump level (only plugins whose skill files changed are touched):
  - breaking (`type!:` in the subject, or `BREAKING CHANGE` in the body) -> major
  - `feat`                                                               -> minor
  - anything else (fix, docs, refactor, chore, ...)                      -> patch

Pass the message you are about to commit with:

    python scripts/upgrade-plugin-versions.py --message "feat(bdd): add scenario linter"

Or force a level explicitly with --major / --minor / --patch.

The run is idempotent: a plugin whose working-tree version already differs from
HEAD is treated as already bumped this round and is left as-is, so running it
twice before the commit lands will not double-bump. Drafts under `skills/drafts/`
have no plugin.json and are never versioned.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

VER_RE = re.compile(r'("version"\s*:\s*")([^"]+)(")')
BREAKING_SUBJECT_RE = re.compile(r"^[a-zA-Z]+(\([^)]*\))?!:")
TYPE_RE = re.compile(r"^([a-zA-Z]+)(\([^)]*\))?:")

# Files under a plugin dir that are not skill content, so a change to them alone
# should not, on its own, drive a version bump.
NON_SKILL_SUFFIXES = (".claude-plugin/plugin.json", "CHANGELOG.md")


def run_git(args, root=None, check=True):
    result = subprocess.run(
        ["git", *args],
        cwd=str(root) if root else None,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        sys.exit(f"[error] git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def repo_root() -> Path:
    out = run_git(["rev-parse", "--show-toplevel"])
    return Path(out.strip())


def discover_plugins(root: Path) -> dict[str, Path]:
    """Map plugin name -> plugin directory for every skills/<name>/.claude-plugin/plugin.json."""
    plugins = {}
    for manifest in sorted((root / "skills").glob("*/.claude-plugin/plugin.json")):
        plugin_dir = manifest.parent.parent
        plugins[plugin_dir.name] = plugin_dir
    return plugins


def changed_paths(root: Path) -> list[str]:
    """Repo-relative paths that differ from HEAD, including untracked and deletions."""
    paths = []
    for line in run_git(["status", "--porcelain"], root).splitlines():
        if not line.strip():
            continue
        rest = line[3:]
        if " -> " in rest:  # rename/copy: attribute to the destination path
            rest = rest.split(" -> ", 1)[1]
        paths.append(rest.strip().strip('"'))
    return paths


def plugins_with_skill_changes(plugins: dict[str, Path], paths: list[str]) -> set[str]:
    changed = set()
    for name in plugins:
        prefix = f"skills/{name}/"
        for path in paths:
            if not path.startswith(prefix):
                continue
            if any(path.endswith(suffix) for suffix in NON_SKILL_SUFFIXES):
                continue
            changed.add(name)
            break
    return changed


def parse_level(message: str | None, override: str | None) -> str:
    if override:
        return override
    if not message:
        return "patch"
    subject = message.splitlines()[0]
    if "BREAKING CHANGE" in message or BREAKING_SUBJECT_RE.match(subject):
        return "major"
    m = TYPE_RE.match(subject)
    if m and m.group(1).lower() == "feat":
        return "minor"
    return "patch"


def bump(version: str, level: str) -> str:
    try:
        major, minor, patch = (int(p) for p in version.split(".")[:3])
    except ValueError:
        sys.exit(f"[error] cannot parse semantic version {version!r}")
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def read_version(text: str) -> str | None:
    m = VER_RE.search(text)
    return m.group(2) if m else None


def head_version(root: Path, rel: str) -> str | None:
    text = run_git(["show", f"HEAD:{rel}"], root, check=False)
    return read_version(text) if text else None


def set_version(manifest: Path, new_version: str) -> None:
    text = manifest.read_text(encoding="utf-8")
    text, count = VER_RE.subn(rf'\g<1>{new_version}\g<3>', text, count=1)
    if count == 0:
        sys.exit(f"[error] no \"version\" field found in {manifest}")
    manifest.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-m", "--message", help="Conventional Commit message you are about to commit with.")
    level = parser.add_mutually_exclusive_group()
    level.add_argument("--major", action="store_const", dest="level", const="major")
    level.add_argument("--minor", action="store_const", dest="level", const="minor")
    level.add_argument("--patch", action="store_const", dest="level", const="patch")
    parser.add_argument(
        "--plugin",
        action="append",
        metavar="NAME",
        help="Only bump this plugin (repeatable). Use to give plugins different levels "
        "in one commit: run once per plugin with its own level flag.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing.")
    args = parser.parse_args()

    root = repo_root()
    plugins = discover_plugins(root)
    changed = plugins_with_skill_changes(plugins, changed_paths(root))

    if args.plugin:
        unknown = [p for p in args.plugin if p not in plugins]
        if unknown:
            sys.exit(f"[error] unknown plugin(s): {', '.join(unknown)}. Known: {', '.join(sorted(plugins))}")
        selected = set(args.plugin)
        skipped = sorted(selected - changed)
        for name in skipped:
            print(f"  {name:<22} (no skill changes against HEAD; skipped)")
        changed = changed & selected

    if not changed:
        print("No plugin skill changes to bump.")
        return 0

    default_level = parse_level(args.message, args.level)
    bumped = 0

    print(f"Bump level: {default_level}" + (f'  (from --message)' if args.message and not args.level else ""))
    for name in sorted(changed):
        plugin_dir = plugins[name]
        manifest = plugin_dir / ".claude-plugin" / "plugin.json"
        rel = f"skills/{name}/.claude-plugin/plugin.json"
        cur = read_version(manifest.read_text(encoding="utf-8"))
        base = head_version(root, rel)

        if base is None:
            print(f"  {name:<22} {cur}  (new plugin, not in HEAD; left as-is)")
            continue
        if cur != base:
            print(f"  {name:<22} {cur}  (already bumped from {base} this round; left as-is)")
            continue

        new_version = bump(base, default_level)
        print(f"  {name:<22} {base} -> {new_version}")
        if not args.dry_run:
            set_version(manifest, new_version)
        bumped += 1

    if args.dry_run:
        print("\n(dry run -- no files written)")
    elif bumped:
        print(f"\nUpdated {bumped} plugin(s). Review and stage the changes, then commit.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
