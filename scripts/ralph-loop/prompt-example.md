You are running autonomously. Complete the steps below without asking for confirmation.

1. **Fetch subtasks** — use the `jira-cli` skill to list all subtasks of `PE-112`.
2. **Find the next task** — identify the first subtask with status `"To Do"`.
   - If no subtask is in `"To Do"`, print exactly `FINISHED`, then stop immediately. Do not proceed further.
3. **Start the task** — transition the subtask to `"In Progress"` using the `jira-cli` skill.
4. **Find the repository** — read the subtask title and description to determine which repository under `~/projects/` is relevant.
5. **Create a branch** — in that repository:
   1. Fetch and check out `main`, then pull the latest from origin: `git checkout main && git pull origin main`
   2. Create and check out a new branch from `main` using the pattern: `{JIRA-TASK-NUMBER}-{short-slug}` (e.g. `PE-115-add-sns-publisher`)
6. **Implement the change** — implement the work described in the subtask. Run the test suite after each meaningful change. Keep iterating until all tests pass.
7. **Commit** — commit the changes using Conventional Commits format (see `~/.claude/CLAUDE.md` for the style). Use past tense, explain *why*, keep the subject under 72 characters.
8. **Push** — push the branch to origin.
9. **Create a draft MR** — use the `glab-cli` skill to open a draft Merge Request targeting `main`. Include:
   - A clear title derived from the subtask title
   - The Jira subtask URL in the description
   - The `Draft:` prefix in the MR title
10. **Done** — print exactly
    ```
    RALPH_ITERATION_DONE: {JIRA-TASK-NUMBER}
    ```
