#!/usr/bin/env python3
"""Locate a repo's local clone and prepare an isolated fix worktree — reliably.

Replaces the inline bash that used to live in SKILL.md Step 3. Handles locating the
clone across common project-root conventions (there's no one standard location, and
hardcoding one breaks for anyone who doesn't use it), refuses to clobber a leftover
worktree from a prior crashed run unless it's fully pushed, and refuses to build on a
branch that's checked out somewhere else (e.g. the user's main clone) rather than
forcing past either collision. Uses subprocess argument lists throughout, never a
shell — so there's no bash/PowerShell dialect to get wrong, and no quoting to get
subtly right.

On success, prints "WORKTREE_PATH: <path>" as the last line. On any refusal, prints
"STOP: <reason>" and exits non-zero — the calling skill should stop and ask the user
how to proceed rather than working around it.

Examples:
  setup_worktree.py --repo-path acme/platform/my-service --source-branch fix/login --change-id 42
  setup_worktree.py --repo-root ~/dev/my-service --source-branch fix/login --change-id 42
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

COMMON_ROOTS = ["~/projects", "~/code", "~/Code", "~/dev", "~/src", "~/Developer", "~/workspace"]
PRUNE_DIRS = {"node_modules", "Library", "AppData", ".cache", ".Trash", ".npm"}
MAX_SEARCH_DEPTH = 6


def run(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def stop(reason):
    print(f"STOP: {reason}")
    sys.exit(1)


def find_by_common_roots(repo_path):
    for root in COMMON_ROOTS:
        candidate = Path(root).expanduser() / repo_path
        if candidate.is_dir():
            return candidate
    return None


def find_by_remote_url(repo_path):
    """Bounded walk from $HOME, matching by remote URL — holds regardless of this
    machine's own folder-naming convention, unlike guessing a root."""
    home = Path.home()
    for dirpath, dirnames, _ in os.walk(home):
        depth = len(Path(dirpath).relative_to(home).parts)
        if depth >= MAX_SEARCH_DEPTH:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS and not d.startswith(".")]
        if (Path(dirpath) / ".git").is_dir():
            proc = run("git", "-C", dirpath, "remote", "get-url", "origin")
            if proc.returncode == 0 and repo_path in proc.stdout.strip():
                return Path(dirpath)
    return None


def locate_repo(args):
    if args.repo_root:
        repo = Path(args.repo_root).expanduser()
        if not repo.is_dir():
            stop(f"--repo-root {repo} doesn't exist")
        return repo
    repo = find_by_common_roots(args.repo_path) or find_by_remote_url(args.repo_path)
    if not repo:
        stop(
            f"couldn't locate a local clone of {args.repo_path} under any common project "
            "root or by remote-URL search. Ask the user for the local clone path and "
            "re-run with --repo-root <path>."
        )
    return repo


def main():
    ap = argparse.ArgumentParser(description="Locate a clone and prepare an isolated fix worktree.")
    ap.add_argument("--repo-path", help="Relative repo path shape, e.g. acme/platform/my-service (per the host adapter)")
    ap.add_argument("--repo-root", help="Explicit local clone path, if already known — skips the search")
    ap.add_argument("--source-branch", required=True)
    ap.add_argument("--change-id", required=True, help="MR iid or PR number, used for the worktree directory suffix")
    args = ap.parse_args()
    if not args.repo_path and not args.repo_root:
        sys.exit("pass --repo-path (to search) or --repo-root (if already known)")

    repo = locate_repo(args)

    fetch = run("git", "-C", str(repo), "fetch", "origin", args.source_branch)
    if fetch.returncode != 0:
        stop(f"fetching {args.source_branch} failed: {fetch.stderr.strip()}")
    run("git", "-C", str(repo), "worktree", "prune")

    worktree_path = repo.parent / f"{repo.name}.address-{args.change_id}"

    if worktree_path.is_dir():
        dirty = run("git", "-C", str(worktree_path), "status", "--porcelain").stdout.strip()
        unpushed = run("git", "-C", str(worktree_path), "log", "@{u}..HEAD", "--oneline").stdout.strip()
        if dirty or unpushed:
            stop(
                f"{worktree_path} exists and isn't verifiably clean (uncommitted changes, "
                "or commits ahead of its upstream). Do not delete it — report this to the "
                "user and ask how to proceed."
            )
        run("git", "-C", str(repo), "worktree", "remove", str(worktree_path))

    branch_ff = run("git", "-C", str(repo), "branch", "-f", args.source_branch, f"origin/{args.source_branch}")
    if branch_ff.returncode != 0:
        stop(
            f"{args.source_branch} is checked out elsewhere (likely the user's main clone): "
            f"{branch_ff.stderr.strip()}"
        )

    add = run("git", "-C", str(repo), "worktree", "add", str(worktree_path), args.source_branch)
    if add.returncode != 0:
        stop(f"creating the worktree failed: {add.stderr.strip()}")

    print(f"WORKTREE_PATH: {worktree_path}")


if __name__ == "__main__":
    main()
