You are running autonomously. Complete the steps below without asking for confirmation.

Use Atlassian's `twg` CLI for the tracker, and the `glab` MCP tools (`glab_mr_create`, `glab_api`) for the repo host. If the shell reports `command not found` for `twg`, use `$HOME/.local/bin/twg`; treat an auth or command error as a twg problem to report, not a missing binary.

`twg` holds the site and your identity in `~/.config/twg/auth.conf` from `twg login`, so no per-iteration identity lookup is needed. Confirm a command's flags with `twg help describe "<exact path>"` rather than guessing — the command surface moves between releases.

1. **Fetch tasks** — run `twg jira workitem bulk-get PROJ-101 PROJ-102 PROJ-103 --fields status,summary,description --expand renderedFields -o json --output-summary stats` to hydrate all three in one call rather than one `get` per task. `--expand renderedFields` matters: without it the description arrives as raw ADF JSON instead of prose. Read the payload with `jq -r '.data.items[].data | {key, summary, status: .status.name, description: .renderedFields.description}'` against `output_files.stdout` — the compact file drops the description you need in step 4.
2. **Find the next task** — identify the first task with status `"To Do"`.
   - If no task is in `"To Do"`, print exactly `FINISHED`, then stop immediately. Do not proceed further.
3. **Start the task** — discover the transition ID with `twg jira workitem transitions query --id {TASK-NUMBER} -o json`, then move the task to `"In Progress"` with `twg jira workitem transition --id {TASK-NUMBER} --transition-id <id>`. Discover the ID rather than hardcoding one — transition IDs differ per project workflow.
4. **Find the repository** — read the task title and description to determine which repository under `~/projects/` is relevant.
5. **Create a worktree** — in that repository, give this task its own working directory off the shared clone, so this iteration never fights another agent (or a parallel loop) over a single checked-out branch:
   1. Fetch the latest from origin and prune any stale worktree entries left behind by earlier iterations: `git fetch origin main && git worktree prune`
   2. Add a new worktree for the branch off `origin/main`, using the pattern `{TASK-NUMBER}-{short-slug}` for both the branch name and the worktree directory: `git worktree add ~/projects/.worktrees/{repo}/{TASK-NUMBER}-{short-slug} -b {TASK-NUMBER}-{short-slug} origin/main` (e.g. `~/projects/.worktrees/my-service/PROJ-103-add-user-auth`)
   3. Run every remaining step below — implementation, tests, commit, push — from inside that worktree directory, not the shared clone.
6. **Implement the change** — implement the work described in the task. Run the test suite after each meaningful change. Keep iterating until all tests pass.
7. **Commit and push** — commit the changes, then push the branch to origin.
8. **Create a draft MR** — call `glab_mr_create` with an explicit `--repo`/`-R <group>/<project>` argument (remote auto-detection isn't reliable here). If it still fails to resolve the project, fall back to `glab_api` with a direct `POST projects/<url-encoded group%2Fproject>/merge_requests` call instead of retrying `glab_mr_create` blind. The draft MR must target `main` and include:
   - A clear title derived from the task title
   - The tracker task URL in the description
   - The `Draft:` prefix in the title
9. **Clean up the worktree** — now that the branch is pushed and the MR exists, remove the worktree (`git worktree remove <path>`) so the shared clone doesn't accumulate stale directories across iterations.
10. **Done** — print exactly
    ```
    RALPH_ITERATION_DONE: {TASK-NUMBER}
    ```