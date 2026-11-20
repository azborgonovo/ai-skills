---
name: address-pr-comments
description: >
  Triages every open review thread on a merge request or pull request, then acts on each one. For a
  thread you agree with, it implements a tested fix, replies in-thread with the fixing commit, and
  resolves the thread. For a thread you disagree with, it replies with your reasoning and leaves the
  thread open for the human reviewer to close. It ships with adapters for GitLab and GitHub as the
  code host, and it degrades to any other host that tool discovery can reach. It commits and pushes
  to the source branch of the change. Use when the user wants to work through reviewer feedback on
  a GitLab MR or a GitHub PR, resolve review comments, or address a round of code review, or when
  another skill hands it the URL of a change with open review threads.
argument-hint: "<merge/pull request URL>"
allowed-tools: [Read, Bash, ToolSearch]
---

# Address PR/MR Comments

Two generic terms run through this skill. A "change" is what the host calls a merge request on GitLab, or a pull request on GitHub. A "thread" is a GitLab discussion or a GitHub review thread: a root comment plus its replies, which resolves independently of the rest of the change.

The host mechanics live in adapter files under `references/hosts/`. Read only the adapter that Step 1 picks.

This skill is not a code review. It acts only on threads that reviewers already raised. For a first-pass review that surfaces new findings, use `/pr-review` instead.

## Workflow

### Step 1: Identify the host and load its adapter

Pick the host from the shape of the URL:

- A URL that contains `…/-/merge_requests/<n>` is GitLab. Read `references/hosts/gitlab.md`.
- A URL that matches `github.com/<owner>/<repo>/pull/<n>` is GitHub. Read `references/hosts/github.md`.

Read the adapter now. It is the authority wherever a later step says "per the host adapter".

When no adapter file exists for the host, degrade instead of stopping. Discover the tools with a keyword `ToolSearch`, or with the platform's CLI or API. Make sure that the fetch-metadata, list-threads, reply, and resolve operations exist, then proceed. Tell the user that you run without a dedicated adapter, so host-specific behavior is best-effort.

### Step 2: Fetch change metadata and open threads

Use the metadata call from the host adapter to fetch the title, the source branch, and the web URL of the change.

**If the metadata call fails with an auth error**, which is a 401 or a "not logged in" message, stop. Ask the user to authenticate, and quote the exact command from the adapter.

Use the list-threads call from the host adapter, and keep only the threads that are still open. For each open thread, capture its ID, the file and line it anchors to when it is inline, and the full body of every comment in it. Read the whole exchange, because a later reply from a reviewer often narrows or changes the ask.

When there are no open threads, skip to Step 10 and report that there is nothing to address.

### Step 3: Prepare the fix workspace

This step commits and pushes to the source branch of the change, so the workspace sits on that branch, and never detaches at a SHA. A bundled script picks the workspace. Do not ask the user which one to use. When the user's clone already has the source branch checked out, the script works there. Otherwise it adds a separate worktree. **Never** switch the branch of the user's clone.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}"
python3 "$PLUGIN_ROOT/scripts/setup_workspace.py" --repo-path <repo_path> --source-branch <source_branch> --change-id <id>
```

Use `python` in place of `python3` when `python3` is not on `PATH`. `<repo_path>` is the relative shape that the host adapter states.

On success it prints two lines. `MODE:` is `main-clone` or `worktree`, and Step 9 reads it. `WORKSPACE_PATH: <path>` is the workspace. Use that path for every read, every edit, and every commit from here on.

On a refusal it prints `STOP: <reason>` and exits non-zero. Stop, relay the reason to the user, and follow what it says, instead of working around it.

### Step 4: Classify each thread

Read every comment in each open thread, and put the thread in one of three classes:

- **Already fixed**: the code already does what the thread asks, probably through a later commit in the same change. No code change is needed.
- **Needs fix**: the ask is actionable and you agree with it. Implement it in Step 5.
- **Disagree**: the ask is arguably wrong, out of scope for this change, or based on a misunderstanding. Closing the thread is the reviewer's call, not yours.

### Step 5: Implement fixes

For each thread classified as **needs fix**, implement the fix with a test that fails before the fix. Land each thread's fix as its own commit, so that the reply cites one SHA and the reviewer verifies one fix at a time.

While you work on a thread, run only the tests that cover it, by the test project, file, or name filter that holds the new test. Step 6 runs the full suite once.

Keep build and test output short, here and in Step 6, because every printed line stays in context. Print only the counts and the failures: use the quiet verbosity of the test runner, or pipe through `tail` or `grep`. When a failure needs more detail, rerun only that test with full output.

### Step 6: Run the test suite

Run the full build, plus the unit and integration suites. Report the counts of passed, failed, and skipped tests, which go in the summary.

If anything fails, stop and fix it before you move on. Never push, and never resolve a thread, against a red suite.

### Step 7: Push the branch

```bash
git -C <worktree_path> push origin <source_branch>
```

Push only after Step 6 is green, and only to the source branch of the change. When git rejects the push, for example as non-fast-forward because someone else pushed meanwhile, stop and tell the user what git reported. **Never** force-push, because it can silently discard the work of someone else.

### Step 8: Reply and resolve, per the host adapter

Always post a true threaded reply, tied to the ID of the thread, with the reply call of the host adapter.

For each thread classified as **needs fix**, reply with the short commit SHA and what changed. "Fixed in abc1234 by capping the batch size at 500" tells the reviewer whether to keep reading, and "Fixed in abc1234" does not. Write the SHA as plain text, outside backticks, so that the host autolinks it. For an **already fixed** thread, say where the existing code already covers the ask. Then resolve the thread. When the resolve call fails on permissions, the reply still stands. Note in the summary that the thread needs a resolve by hand.

For each thread classified as **disagree**, reply with your reasoning. **Never** resolve it. End the reply on the reasoning, or on an offer that the reviewer can take up. Do not say that the thread stays open, or who closes it, because the reviewer sees the open state.

End every reply with a trailing 🤖, so that the reviewer knows that an agent wrote it. When the user asks you to post their own message, or gives you the exact text of a reply, post it with no 🤖, because it speaks for the user.

A human reviewer reads every reply. Write short sentences in the active voice, define a term that the reviewer can miss at its first use, and cut filler. Never paraphrase a commit SHA, a file path, or a symbol name. When a plain-English writing skill such as `simple-english` is available, invoke it and apply its rules to the replies.

### Step 9: Remove the worktree

When Step 3 printed `MODE: worktree`, remove that worktree now, even when an earlier step failed partway through. Remove nothing when it printed `MODE: main-clone`, or when it stopped before it printed a path.

```bash
git -C <repo_path> worktree remove <worktree_path>
```

`<worktree_path>` is the `WORKSPACE_PATH` that Step 3 printed, and `<repo_path>` is the clone it came from. If git refuses the removal, leave the worktree in place, and tell the user exactly what git reported.

### Step 10: Output the summary

Summarize directly in the conversation, and post nothing to the change. Give the title and link of the change, plus the test results from Step 6. List the threads that you fixed and resolved, with the commit SHA of each. List the threads that were already fixed and resolved, with where and how. List the threads that you left open, with your reasoning. Give the number of commits pushed to the source branch. Skip a category that holds nothing, instead of noting its absence.
