---
name: update-branch
description: >
  Brings a branch up to date with its base branch, usually main. It rebases onto origin/<base>, or
  merges when the user agrees, then builds and runs the relevant tests. It pushes on its own when it
  resolved every conflict without doubt and every test passed, and asks first when not. It never
  uses a plain --force, and it never disturbs uncommitted work: a clone on another branch gets a
  separate git worktree.
argument-hint: "[branch] [--base <branch>] [merge]"
disable-model-invocation: true
---

# Update Branch

The branch defaults to the current branch. The base defaults to `origin/HEAD`. The argument `merge` selects a merge.

## Step 1: Pick the workspace

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}"
python3 "$PLUGIN_ROOT/scripts/prepare_update_workspace.py" [--branch <branch>] [--base <base>]
```

The helper fetches, then prints `MODE:`, `BASE:`, and `WORKSPACE_PATH:`. Run every later command in that path, with `git -C <workspace_path>` for git. On `STOP: <reason>`, show the reason and stop. **Never** stash, reset, or discard work to get past a refusal.

## Step 2: Protect the remote commits

Record `origin/<branch>` as the lease for Step 6. If `origin/<branch>` does not exist, skip the rest of this step.

A rebase and a forced push delete the commits in `<branch>..origin/<branch>` from the remote. If the local branch has no commits past `origin/<branch>`, fast-forward to it. Otherwise show both sides and ask.

## Step 3: Choose rebase or merge

Rebase unless the user asked for a merge. Propose a merge and wait for the answer in these cases:

- `<BASE>..origin/<branch>` holds commits by another author than `git config user.email`.
- The repository docs ask for merge commits.

## Step 4: Update the branch

Read the conflict conventions in the repository docs first. For each conflict, read the base commit that touched the same lines. Resolve a conflict on your own only when one answer in the code keeps the intent of both sides. Otherwise stop and ask. Record each resolution for the report, including any edit outside the conflict markers.

If the same lines conflict in commit after commit, abort the rebase and offer a merge.

## Step 5: Build and test

Build the projects in `git diff --name-only <BASE>...HEAD`, and run their unit and integration tests. When a shared library changed, also test its dependents. Take the commands from the repository docs and build files. If you find none, ask.

## Step 6: Push and report

Push without asking only when you resolved every conflict on your own and every build and test from Step 5 passed. Otherwise report the reason and the exact push command, then ask.

After a rebase, push with the lease from Step 2:

```bash
git -C <workspace_path> push --force-with-lease=<branch>:<lease> origin <branch>
```

If the lease fails, stop and report it. Do not retry with a new lease. After a merge, run `git push`, with `-u` for a branch that was never pushed. **Never** use `--force`, `-f`, or a `+<refspec>`.

Then report the strategy, the new base commit, each conflict resolution, the build and test results, and the push result.

## Step 7: Clean up

For `MODE: worktree` only, remove the worktree with the helper after the push. **Never** use `git worktree remove`, because it removes a clean worktree with unpushed commits.

```bash
python3 "$PLUGIN_ROOT/scripts/prepare_update_workspace.py" --remove <workspace_path>
```

If there was no push, or the helper prints `STOP:`, keep the worktree and give the user its path.
