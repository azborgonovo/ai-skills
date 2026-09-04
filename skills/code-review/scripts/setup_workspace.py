#!/usr/bin/env python3
"""Locate a repo's local clone and prepare a workspace for a change — reliably.

"Workspace" rather than "worktree" because the answer isn't always a new worktree: a
clone already sitting on the source branch is the better place to work, and the caller
shouldn't have to care which it got beyond the printed MODE.
Lives at the plugin root rather than inside either skill because both need it:
address-pr-comments needs a workspace it can commit on (on the source branch),
pr-review needs one it only reads (detached at the change's head SHA, which can never
collide with a branch already checked out elsewhere).
Handles locating the clone across common project-root conventions (there's no one
standard location, and hardcoding one breaks for anyone who doesn't use it), and refuses
to clobber a leftover worktree from a prior crashed run unless it's fully pushed. When
the clone itself already has the source branch checked out, it works there instead of
adding a worktree: the user is looking at that directory, and a second checkout of one
branch isn't possible anyway. Uses subprocess argument lists throughout, never a shell —
so there's no bash/PowerShell dialect to get wrong, and no quoting to get subtly right.

Callers resolve this path as "${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f
"<skill_dir>/SKILL.md")")")}/scripts/setup_workspace.py", which covers both install modes:
CLAUDE_PLUGIN_ROOT is set when the skill runs from an installed plugin, and when it
instead runs from a directory symlinked into ~/.claude/skills, resolving the SKILL.md's
own real path is the only anchor that still points here.

On success, prints "MODE: worktree" or "MODE: main-clone", then "WORKSPACE_PATH: <path>"
as the last line. The mode tells the caller whether that path is disposable: only a
worktree gets removed at the end. On any refusal, prints "STOP: <reason>" and exits
non-zero — the calling skill should stop and ask the user how to proceed rather than
working around it.

Examples:
  setup_workspace.py --repo-path acme/platform/my-service --source-branch fix/login --change-id 42
  setup_workspace.py --repo-root ~/dev/my-service --source-branch fix/login --change-id 42
  setup_workspace.py --repo-path acme/my-service --source-branch fix/login --change-id 42 \
      --purpose review --detach-sha 9fceb02 --target-branch main
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


def has_unpushed_work(worktree_path):
    """A leftover worktree may be detached (a prior review run) or on a branch (a prior
    fix run), so ask the question both ways: commits ahead of an upstream, or a HEAD no
    remote branch contains."""
    if run("git", "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "@{u}").returncode == 0:
        return bool(run("git", "-C", str(worktree_path), "log", "@{u}..HEAD", "--oneline").stdout.strip())
    return not run("git", "-C", str(worktree_path), "branch", "-r", "--contains", "HEAD").stdout.strip()


def worktree_holding(repo, branch):
    """Which working tree has <branch> checked out, or None. A branch can be checked out
    in only one, so this decides between reusing that one and creating a new worktree."""
    path = None
    for line in run("git", "-C", str(repo), "worktree", "list", "--porcelain").stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree ") :])
        elif line.strip() == f"branch refs/heads/{branch}":
            return path
    return None


def reuse_main_clone(repo, branch):
    """The clone already holds the branch, so commit there instead of asking. A worktree
    would only move the work somewhere the user is not looking."""
    dirty = run("git", "-C", str(repo), "status", "--porcelain").stdout.strip()
    if dirty:
        stop(
            f"{repo} has {branch} checked out with uncommitted changes:\n{dirty}\n"
            "Per-thread commits would capture edits that are not part of any fix. Ask the "
            "user to commit, stash, or discard them."
        )
    ahead = run("git", "-C", str(repo), "log", f"origin/{branch}..HEAD", "--oneline").stdout.strip()
    if ahead:
        stop(
            f"{repo} holds commits on {branch} that origin doesn't:\n{ahead}\n"
            "Pushing the fixes would push these too. Ask the user to push or drop them."
        )
    ff = run("git", "-C", str(repo), "merge", "--ff-only", f"origin/{branch}")
    if ff.returncode != 0:
        stop(
            f"{branch} in {repo} cannot fast-forward to origin/{branch}: {ff.stderr.strip()}. "
            "The local branch holds commits that the remote does not, or it diverged."
        )
    print("MODE: main-clone")
    print(f"WORKSPACE_PATH: {repo}")


def locate_repo(args):
    if args.repo_root:
        repo = Path(args.repo_root).expanduser()
        if not repo.is_dir():
            stop(f"--repo-root {repo} doesn't exist")
        return repo.resolve()
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
    ap.add_argument("--purpose", default="address", help="Worktree directory suffix label: <repo>.<purpose>-<change-id>")
    ap.add_argument("--detach-sha", help="Create a detached worktree pinned to this SHA instead of checking out the source branch")
    ap.add_argument("--target-branch", help="Also fetch this branch — the diff base a review needs present locally")
    args = ap.parse_args()
    if not args.repo_path and not args.repo_root:
        sys.exit("pass --repo-path (to search) or --repo-root (if already known)")

    repo = locate_repo(args)

    refs = [args.source_branch] + ([args.target_branch] if args.target_branch else [])
    fetch = run("git", "-C", str(repo), "fetch", "origin", *refs)
    if fetch.returncode != 0:
        stop(f"fetching {' and '.join(refs)} failed: {fetch.stderr.strip()}")
    run("git", "-C", str(repo), "worktree", "prune")

    if not args.detach_sha:
        holder = worktree_holding(repo, args.source_branch)
        if holder and holder.resolve() == repo.resolve():
            reuse_main_clone(repo, args.source_branch)
            return
        if holder:
            stop(
                f"{args.source_branch} is checked out at {holder}, which is neither the main "
                f"clone nor a worktree of this run. Another agent likely holds it. Report this "
                "to the user and ask how to proceed."
            )

    worktree_path = repo.parent / f"{repo.name}.{args.purpose}-{args.change_id}"

    if worktree_path.is_dir():
        dirty = run("git", "-C", str(worktree_path), "status", "--porcelain").stdout.strip()
        unpushed = has_unpushed_work(worktree_path)
        if dirty or unpushed:
            stop(
                f"{worktree_path} exists and isn't verifiably clean (uncommitted changes, "
                "or a commit no remote branch has). Do not delete it — report this to the "
                "user and ask how to proceed."
            )
        run("git", "-C", str(repo), "worktree", "remove", str(worktree_path))

    if args.detach_sha:
        add = run("git", "-C", str(repo), "worktree", "add", "--detach", str(worktree_path), args.detach_sha)
    else:
        branch_ff = run("git", "-C", str(repo), "branch", "-f", args.source_branch, f"origin/{args.source_branch}")
        if branch_ff.returncode != 0:
            stop(f"pointing {args.source_branch} at origin/{args.source_branch} failed: {branch_ff.stderr.strip()}")
        add = run("git", "-C", str(repo), "worktree", "add", str(worktree_path), args.source_branch)
    if add.returncode != 0:
        stop(f"creating the worktree failed: {add.stderr.strip()}")

    print("MODE: worktree")
    print(f"WORKSPACE_PATH: {worktree_path}")


if __name__ == "__main__":
    main()
