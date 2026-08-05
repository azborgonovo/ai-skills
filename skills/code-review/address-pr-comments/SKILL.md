---
name: address-pr-comments
description: >
  Triages every open review thread on a merge/pull request, then does something about each one:
  implements a tested fix, replies in-thread with the fixing commit, and resolves it — or, for a
  thread you disagree with, replies with your reasoning and leaves it open for the human reviewer to
  close. Ships with adapters for GitLab and GitHub as the code host, but degrades gracefully to any
  other host reachable via tool discovery. User-only: runs only when explicitly invoked with
  /address-pr-comments <MR or PR URL>. When the user wants to work through reviewer feedback on a
  GitLab MR or GitHub PR, resolve review comments, or address a round of code review, suggest running
  this command rather than triaging threads by hand.
argument-hint: "<merge/pull request URL>"
allowed-tools: [Read, Bash, ToolSearch]
disable-model-invocation: true
---

# Address PR/MR Comments

Works through every open review thread on a merge or pull request: fixes what needs fixing, then replies and resolves.

Throughout this skill "change" is the generic term for what the host calls a merge request (GitLab) or pull request (GitHub) — the host adapter keeps that host's own word when naming the concrete API object or CLI call. "Thread" is the generic term for a GitLab discussion or a GitHub review thread: a root comment plus its replies, resolvable independently of the rest of the change.

The workflow is host-agnostic; the host-specific mechanics live in adapter files under `references/` and load only when you reach the step that needs them. This keeps the always-loaded body focused on judgment — classifying each thread and fixing the code, which is the same regardless of where the change lives.

This isn't a code review — it only acts on threads reviewers have already raised, and doesn't evaluate the change on its own merits. For a first-pass review that surfaces new findings, use `/pr-review` instead.

## Workflow

Work through steps in order.

### Step 1 — Identify the host and load its adapter

Determine which host the change lives on, primarily from the URL shape:

- `…/-/merge_requests/<n>` → GitLab → read `references/hosts/gitlab.md`
- `github.com/<owner>/<repo>/pull/<n>` → GitHub → read `references/hosts/github.md`

The adapter file is the authority for that host's mechanics: URL parsing, auth check, the exact calls to list threads and fetch metadata, the local-clone path convention, and how to reply to and resolve a thread with that host's own gotchas. Read it now and follow it wherever a later step says "per the host adapter."

If there's no adapter file for the host you're facing, degrade gracefully rather than stopping: discover the relevant tools with a keyword `ToolSearch` (or the platform's own CLI/API), confirm the fetch-metadata/list-threads/reply/resolve operations you need exist, and proceed. Tell the user you're running without a dedicated adapter so they know host-specific behavior is best-effort.

### Step 2 — Fetch change metadata and open threads

Using the metadata call from the host adapter, fetch the change's title, source branch, and web URL — Step 10's summary needs all three, and the source branch drives the worktree in Step 3.

**If the metadata call fails with an auth error** (401, or a "not logged in" message), the host adapter's CLI/tool isn't authenticated — stop and ask the user to authenticate (the adapter states the exact command).

Using the list-threads call from the host adapter, fetch every thread, then keep only the ones still open (unresolved). For each open thread, capture: its ID (needed to reply and resolve), the file/line it's anchored to if inline, and the full body of every comment in it — you need the whole exchange, not just the first comment, since a reviewer's later reply often narrows or changes the ask.

If there are no open threads, skip straight to Step 10 and report there's nothing to address — no worktree needed.

### Step 3 — Create a fix worktree

Checking out the branch in the user's main clone would switch what's checked out from under them. A disposable worktree gives the fix work its own directory instead, so the main checkout is never touched.

Unlike a read-only review, this worktree needs to hold real commits that get pushed back to the change's own source branch — so it's checked out on that branch, not detached at a SHA.

```bash
# 1. Locate the local clone (per the host adapter's convention)
ls ~/projects/<repo_path> 2>/dev/null

# 2. Fallback: search by remote URL
find ~/projects -maxdepth 5 -name ".git" -exec sh -c \
  'git -C "$1/.." remote get-url origin 2>/dev/null' _ {} \; | grep "<repo_path>"

# 3. Fetch the source branch
git -C <repo_path> fetch origin <source_branch>
git -C <repo_path> worktree prune

WORKTREE_PATH="<repo_path>.address-<id>"

# 4. A worktree may already sit at this path — e.g. left behind by a prior run of this
#    skill that crashed before Step 9 cleanup. It's only safe to replace if every commit
#    on it has already reached its upstream; otherwise it may hold unpushed fix work.
if [ -d "$WORKTREE_PATH" ]; then
  DIRTY=$(git -C "$WORKTREE_PATH" status --porcelain 2>&1)
  UNPUSHED=$(git -C "$WORKTREE_PATH" log '@{u}..HEAD' --oneline 2>&1)
  if [ -n "$DIRTY" ] || [ -n "$UNPUSHED" ]; then
    echo "STOP: $WORKTREE_PATH exists and is not verifiably clean (uncommitted changes, or commits ahead of its upstream). Do not delete it. Report this to the user and ask how to proceed."
    exit 1
  else
    git -C <repo_path> worktree remove "$WORKTREE_PATH"
  fi
fi

# 5. Point the local branch at the freshly fetched origin ref, creating it if it doesn't
#    exist yet — otherwise a stale local branch would defeat the fetch in step 3. This
#    refuses (non-zero exit) if the branch is checked out anywhere else, e.g. the user's
#    main clone — exactly the collision that should stop the run rather than force past it.
if ! git -C <repo_path> branch -f <source_branch> "origin/<source_branch>"; then
  echo "STOP: <source_branch> is already checked out elsewhere (likely the user's main clone). Report this to the user and ask how to proceed."
  exit 1
fi
git -C <repo_path> worktree add "$WORKTREE_PATH" <source_branch>
```

If the repo isn't found locally, stop and tell the user — unlike a read-only review, there's no diff-only fallback for implementing fixes.

Use `$WORKTREE_PATH` for every read, edit, and commit from here on.

### Step 4 — Classify each thread

For each open thread, read every comment in it and classify:

- **Already fixed** — the code already does what the thread asks, likely from a later commit in the same change. Reply explaining where/how, then resolve — no code change needed.
- **Needs fix** — the ask is actionable and you agree with it. Implement it in Step 5.
- **Disagree** — the ask is arguably wrong, out of scope for this change, or based on a misunderstanding. Reply explaining your reasoning, but leave the thread open (Step 8) — closing a thread the reviewer raised is the reviewer's call, not something to decide unilaterally on their behalf.

### Step 5 — Implement fixes

For each thread classified **needs fix**, implement it with a test that would have failed before the fix, as one atomic commit per thread. Keep each thread's fix isolated in its own commit — it's what lets you cite a single commit SHA when replying in Step 8, and lets the reviewer verify one thread's fix without reading through another's.

### Step 6 — Run the test suite

Run the full build plus unit and integration suites. Report the counts (passed/failed/skipped) — this is what tells you the fixes are safe to push, and it goes in the summary either way.

If anything fails, stop and fix it before moving on — don't push or resolve threads against a red suite.

### Step 7 — Push the branch

```bash
git -C "$WORKTREE_PATH" push origin <source_branch>
```

Push only after Step 6 is green, and only ever to the change's own source branch — never anywhere else. If the push is rejected (e.g. non-fast-forward because someone else pushed to the branch meanwhile), stop and tell the user what git reported rather than force-pushing; force-pushing someone else's branch can silently discard their work.

### Step 8 — Reply and resolve, per the host adapter

For each thread classified **needs fix** or **already fixed**: reply with the commit SHA and a short description of what changed (or, for already-fixed, where the existing code already covers it), then resolve the thread. The host adapter states the exact reply/resolve calls — always a true threaded reply tied to the thread's ID, never a new standalone/general comment.

For each thread classified **disagree**: reply with your reasoning. Do not resolve it.

### Step 9 — Remove the worktree

If a worktree was created in Step 3, remove it now — even if an earlier step failed partway through. If Step 3 hit its STOP check and left a pre-existing worktree untouched, this run never created one — don't remove it here either:

```bash
git -C <repo_path> worktree remove "$WORKTREE_PATH"
```

If removal is refused, leave the worktree in place and tell the user exactly what git reported.

### Step 10 — Output the summary

Output directly in the conversation:

```
## Addressed Review Threads

**Change**: [<title>](<web_url>)
**Tests**: <pass/fail/skip counts from Step 6>

**Fixed and resolved** (<N>):
- `<file>:<line>` (or "general") — <one-line description> — <commit SHA>

**Already fixed and resolved** (<N>):
- `<file>:<line>` (or "general") — <where/how it was already handled>

**Left open — needs your call** (<N>):
- `<file>:<line>` (or "general") — <your reasoning for disagreeing>
*(omit this section entirely when N is 0)*

<N> commit(s) pushed to `<source_branch>`.
```

## Hard constraints

- **Never** resolve a thread classified as disagree — reply, then leave it for the reviewer to close
- **Never** check out the change's branch in the user's main clone — always work from the isolated worktree created in Step 3
- **Never** force-remove the fix worktree (Step 3's replacement check, Step 9's cleanup) — if it isn't verifiably clean, stop and tell the user instead of overriding
- **Never** force-push — if the push in Step 7 is rejected, stop and ask the user how to proceed
- **Always** run the full test suite (Step 6) and confirm it's green before pushing or resolving anything
- **Always** remove the worktree before finishing (Step 9), even if the run is aborted or fails partway
- **Always** reply through the host adapter's true threaded-reply call, tied to the thread's ID — never a standalone/general comment
