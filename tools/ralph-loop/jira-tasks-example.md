You are running autonomously. Complete the steps below without asking for confirmation.

Use the Atlassian MCP tools (`getJiraIssue`, `searchJiraIssuesUsingJql`, `getTransitionsForJiraIssue`, `transitionJiraIssue`, `editJiraIssue`) for the tracker, and the `glab` MCP tools (`glab_mr_create`, `glab_api`) for the repo host.

Resolve your tracker identity cache-first, so every iteration after the first skips the lookup entirely: cloud ID from `$HOME/.claude/atlassian-cloud-id` (if missing, call `getAccessibleAtlassianResources`, take the returned site's `id`, and write it to that file); account ID from `$HOME/.claude/atlassian-account-id` (if missing, call `lookupJiraAccountId` with your tracker username and write the result to that file).

1. **Fetch tasks** — call `searchJiraIssuesUsingJql` with `key in (PROJ-101, PROJ-102, PROJ-103)`, requesting only the fields you need (`status`, `summary`, `description`) in that single batched query rather than one `getJiraIssue` call per task.
2. **Find the next task** — identify the first task with status `"To Do"`.
   - If no task is in `"To Do"`, print exactly `FINISHED`, then stop immediately. Do not proceed further.
3. **Start the task** — look up the transition ID via `getTransitionsForJiraIssue` and call `transitionJiraIssue` to move the task to `"In Progress"`.
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