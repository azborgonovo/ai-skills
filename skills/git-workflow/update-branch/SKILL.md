---
name: update-branch
description: >
  Brings a branch up to date with its base branch, usually main. It rebases the branch onto
  origin/<base>, or merges origin/<base> into it when a rebase is not an option and the user agrees.
  It then builds and runs the tests for the projects that the branch touches, and asks before it
  pushes with --force-with-lease after a rebase or a plain push after a merge. It never uses a plain
  --force. It never disturbs staged or uncommitted work: when the clone sits on another branch, it
  works in a separate git worktree. This skill is user-only: it runs only when the user invokes
  /update-branch [branch] [--base <branch>] [merge]. When the user wants to update a branch with
  main, rebase onto main, catch a feature branch up with the base branch, or resolve "branch is
  behind main" before a merge, suggest this command.
argument-hint: "[branch] [--base <branch>] [merge]"
disable-model-invocation: true
---

# Update Branch

This skill updates one branch with its base branch. It proves that the result builds and passes its tests, and it pushes only after the user agrees. A rebase rewrites published history, so every step that can lose work has a check in front of it.

The arguments are optional. The branch defaults to the branch checked out in the current directory. The base defaults to `origin/HEAD`, which is `main` in most repositories. The word `merge` asks for a merge in place of a rebase.

## Step 1: Pick the workspace

Run the helper. It fetches the base and the branch, then picks the working tree for the update:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}"
python3 "$PLUGIN_ROOT/scripts/prepare_update_workspace.py" [--branch <branch>] [--base <base>]
```

When `python3` is not on `PATH`, use `python` in its place.

The helper prints three lines on success:

- `MODE:` tells you who owns the workspace. `main-clone` is the clean main clone of the user. `existing-worktree` is another clean worktree that holds the branch. `worktree` is a worktree that the helper added for this run.
- `BASE:` is the remote base ref, such as `origin/main`.
- `WORKSPACE_PATH:` is the directory to work in.

Run every git command after this step as `git -C <workspace_path>`, and every build and test command from that directory. The shell still starts in the directory of the user.

On a refusal, the helper prints `STOP: <reason>` and exits non-zero. Show the reason to the user and stop. It refuses a checkout with uncommitted tracked changes, and a rebase or merge in progress. **Never** stash, reset, or discard the work of the user to get past a refusal.

## Step 2: Make sure that no remote commit gets lost

Record the remote tip of the branch now. Step 7 uses it as the lease:

```bash
git -C <workspace_path> rev-parse --verify --quiet origin/<branch>
```

When the branch has no remote ref, it was never pushed. Skip the rest of this step, and use a rebase.

List the commits that the remote holds and the local branch does not:

```bash
git -C <workspace_path> log --format='%h %an <%ae> %s' <branch>..origin/<branch>
```

A rebase onto the base drops these commits, and the push in Step 7 then deletes them from the remote. When the list is not empty, integrate them first:

- If the local branch has no commits of its own past `origin/<branch>`, run `git -C <workspace_path> merge --ff-only origin/<branch>`.
- Otherwise the two diverged. Show both sides to the user and ask how to reconcile them. Do not continue on your own.

## Step 3: Choose rebase or merge

Use a rebase by default. It keeps the history linear, and most merge request workflows expect it.

When one of these is true, propose a merge, explain why, and wait for the answer:

- The commits between `<BASE>` and `origin/<branch>` include an author other than `git config user.email`. A rebase rewrites their commits, and their local copies then diverge.
- The `CLAUDE.md`, `AGENTS.md`, or contributing guide of the repository asks for merge commits.
- The user asked for a merge.

The first check reads:

```bash
git -C <workspace_path> log --format='%an <%ae>' <BASE>..origin/<branch> | sort -u
```

**Never** switch from rebase to merge without consent. A silent switch changes the shape of the history that the user agreed to.

## Step 4: Update the branch

For a rebase, run `git -C <workspace_path> rebase <BASE>`. For a merge, run `git -C <workspace_path> merge --no-edit <BASE>`.

When git stops on a conflict, read the conflict conventions of the repository first, in its `CLAUDE.md`, `AGENTS.md`, or contributing guide. Then resolve each conflicted file:

- Keep the intent of both sides. Read the commit on the base that changed the same lines, so that you know what it was for.
- Stage the result with `git add`, then continue with `GIT_EDITOR=true git -C <workspace_path> rebase --continue`, or with `git -C <workspace_path> commit --no-edit` for a merge.
- Record each resolution in one line for the report in Step 6.

Some conflicts are semantic, such as two changes to the same business rule. If the code does not make the right answer clear, stop and ask. Show both sides and your proposed resolution.

When the rebase hits conflicts in several commits, and the same lines conflict again and again, run `git -C <workspace_path> rebase --abort`. Then offer a merge, which resolves the conflicts one time. That is a new choice for the user, as in Step 3.

## Step 5: Build and run the relevant tests

Find the projects that the branch touches:

```bash
git -C <workspace_path> diff --name-only <BASE>...HEAD
```

Take the build and test commands from the repository. Look in the `CLAUDE.md` or `AGENTS.md` file first, then the README, then the build files. Examples of build files are a solution file, `package.json`, `pom.xml`, `pyproject.toml`, `go.mod`, and a `Makefile`. Build the touched projects and run their unit and integration tests. When a touched project is a shared library, also run the tests of the projects that depend on it.

When the repository names no command that you can find, ask the user for it. Do not guess one.

## Step 6: Report

Report these items in a short list:

- The strategy, rebase or merge, and why.
- The number of commits on the branch, and the new base commit.
- Each conflict and how you resolved it.
- The build result and the test result. Name each failing test.

If the build or a test fails, stop here. Do not offer the push. If it is cheap to check, say whether the failure also happens on `<BASE>` alone.

## Step 7: Ask, then push

**Always** ask the user before the push, and show the exact command. Push only after a clear yes.

After a rebase, use the lease from Step 2:

```bash
git -C <workspace_path> push --force-with-lease=<branch>:<remote_tip> origin <branch>
```

If anyone pushed to the branch after Step 2, the explicit lease fails. It fails even after a background fetch updated `origin/<branch>`. When the push fails on the lease, stop and report it. Do not retry with a fresh lease.

After a merge, use `git -C <workspace_path> push origin <branch>`. For a branch that was never pushed, use `git -C <workspace_path> push -u origin <branch>`.

**Never** use `--force`, `-f`, or a `+<refspec>`. Each one overwrites the remote with no check of what it held.

## Step 8: Clean up

When Step 1 printed `MODE: worktree` and the push succeeded, remove that worktree:

```bash
git -C <workspace_path> worktree remove <workspace_path>
```

If the user declined the push, the updated branch holds work that the remote does not have. Keep the worktree, and tell the user its path. **Never** remove a worktree with uncommitted or unpushed work. Leave `main-clone` and `existing-worktree` in place, because they belong to the user.
