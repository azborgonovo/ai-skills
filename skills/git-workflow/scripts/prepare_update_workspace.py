#!/usr/bin/env python3
"""Pick the working tree in which a branch gets updated with its base branch.

The branch is updated where it is already checked out, when that checkout is clean. When
nothing holds the branch, a sibling worktree is added, so that the main clone keeps its own
branch and its uncommitted work. A dirty checkout, or one with a rebase or merge in progress,
is never touched: the script refuses instead of stashing.

On success, prints "MODE: main-clone", "MODE: existing-worktree", or "MODE: worktree", then
"BASE: origin/<base>" and "WORKSPACE_PATH: <path>" as the last line. Only MODE: worktree is
disposable. On a refusal, prints "STOP: <reason>" and exits non-zero.

Examples:
  prepare_update_workspace.py
  prepare_update_workspace.py --repo-root ~/dev/my-service --branch feat/login --base develop
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run(*cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def git(repo, *args):
    return run("git", "-C", str(repo), *args)


def stop(reason):
    print(f"STOP: {reason}")
    sys.exit(1)


def main_clone_of(path):
    common = git(path, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common.returncode != 0:
        stop(f"{path} is not inside a git repository")
    return Path(common.stdout.strip()).parent


def default_base(repo):
    head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if head.returncode == 0:
        return head.stdout.strip().removeprefix("origin/")
    stop("origin/HEAD is not set, so the base branch is unknown. Ask the user for it and re-run with --base <branch>.")


def rebasing_branch(tree):
    for marker in ("rebase-merge", "rebase-apply"):
        head_name = Path(git(tree, "rev-parse", "--path-format=absolute", "--git-path", f"{marker}/head-name").stdout.strip())
        if head_name.is_file():
            return head_name.read_text().strip().removeprefix("refs/heads/")
    return None


def worktree_holding(repo, branch):
    # A rebase detaches HEAD, so the worktree list no longer names the branch it is rebasing.
    path = None
    for line in git(repo, "worktree", "list", "--porcelain").stdout.splitlines():
        if line.startswith("worktree "):
            path = Path(line[len("worktree "):])
        elif line.strip() == f"branch refs/heads/{branch}":
            return path
        elif line.strip() == "detached" and rebasing_branch(path) == branch:
            return path
    return None


def operation_in_progress(tree):
    for marker in ("rebase-merge", "rebase-apply", "MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD"):
        if Path(git(tree, "rev-parse", "--path-format=absolute", "--git-path", marker).stdout.strip()).exists():
            return marker
    return None


def refuse_if_unsafe(tree, branch):
    in_progress = operation_in_progress(tree)
    if in_progress:
        stop(f"{tree} holds {branch} with an unfinished operation ({in_progress}). Ask the user to finish or abort it.")
    # Untracked files survive a rebase or a merge, so only tracked changes block the update.
    dirty = git(tree, "status", "--porcelain", "--untracked-files=no").stdout.strip()
    if dirty:
        stop(f"{tree} holds {branch} with uncommitted changes:\n{dirty}\nAsk the user to commit or set them aside. Do not stash them yourself.")


def has_unpushed_work(tree):
    if git(tree, "rev-parse", "--abbrev-ref", "@{u}").returncode == 0:
        return bool(git(tree, "log", "@{u}..HEAD", "--oneline").stdout.strip())
    return not git(tree, "branch", "-r", "--contains", "HEAD").stdout.strip()


def own_worktree_path(repo, branch):
    return repo.parent / f"{repo.name}.update-{branch.replace('/', '-')}"


def add_worktree(repo, branch):
    path = own_worktree_path(repo, branch)
    if path.is_dir():
        dirty = git(path, "status", "--porcelain").stdout.strip()
        if dirty or has_unpushed_work(path):
            stop(f"{path} exists and holds uncommitted or unpushed work. Do not delete it. Ask the user how to proceed.")
        remove = git(repo, "worktree", "remove", str(path))
        if remove.returncode != 0:
            stop(f"removing the leftover worktree {path} failed: {remove.stderr.strip()}")

    if git(repo, "rev-parse", "--verify", "--quiet", f"refs/heads/{branch}").returncode == 0:
        add = git(repo, "worktree", "add", str(path), branch)
    elif git(repo, "rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}").returncode == 0:
        add = git(repo, "worktree", "add", "--track", "-b", branch, str(path), f"origin/{branch}")
    else:
        stop(f"no local or remote branch named {branch}")
    if add.returncode != 0:
        stop(f"adding a worktree for {branch} failed: {add.stderr.strip()}")
    return path


def main():
    ap = argparse.ArgumentParser(description="Pick the working tree in which a branch gets updated with its base.")
    ap.add_argument("--repo-root", default=".", help="Any path inside the repository (default: the current directory)")
    ap.add_argument("--branch", help="Branch to update (default: the branch checked out at --repo-root)")
    ap.add_argument("--base", help="Base branch on origin (default: origin/HEAD)")
    args = ap.parse_args()

    start = Path(args.repo_root).expanduser().resolve()
    repo = main_clone_of(start)
    branch = args.branch or git(start, "branch", "--show-current").stdout.strip() or rebasing_branch(start)
    if not branch:
        stop(f"{start} has a detached HEAD. Ask the user which branch to update and re-run with --branch <branch>.")
    base = args.base or default_base(repo)
    if branch == base:
        stop(f"{branch} is the base branch itself. Ask the user which branch to update.")

    fetch = git(repo, "fetch", "origin", base)
    if fetch.returncode != 0:
        stop(f"fetching {base} failed: {fetch.stderr.strip()}")
    git(repo, "fetch", "origin", branch)  # A branch that was never pushed has no remote ref to fetch.
    git(repo, "worktree", "prune")

    holder = worktree_holding(repo, branch)
    if holder:
        refuse_if_unsafe(holder, branch)
        if holder.resolve() == repo.resolve():
            mode = "main-clone"
        elif holder.resolve() == own_worktree_path(repo, branch).resolve():
            mode = "worktree"
        else:
            mode = "existing-worktree"
    else:
        holder, mode = add_worktree(repo, branch), "worktree"

    print(f"MODE: {mode}")
    print(f"BASE: origin/{base}")
    print(f"WORKSPACE_PATH: {holder}")


if __name__ == "__main__":
    main()
