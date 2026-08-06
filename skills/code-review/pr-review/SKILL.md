---
name: pr-review
description: >
  Reviews a merge/pull request against its linked tracker ticket, then posts inline comments on the
  diff for you to submit — it fetches the change and ticket context, structures the review, and
  writes the comments directly to the host's draft/pending-review mechanism. Ships with adapters for
  GitLab and GitHub as the code host, and JIRA and GitHub Issues as the tracker, but degrades
  gracefully to any other host or tracker reachable via tool discovery. User-only: runs only when
  explicitly invoked with /pr-review <MR or PR URL>. When the user wants to review a GitLab MR or
  GitHub PR, code-review a merge/pull request, or evaluate a change's diff against its linked ticket,
  suggest running this command rather than doing a manual review.
argument-hint: "<merge/pull request URL>"
allowed-tools: [Read, Bash, Skill, Write, ToolSearch]
disable-model-invocation: true
---

# PR/MR Review

Structured code review for a merge or pull request. Fetches ticket requirements when available, reviews the code and posts inline comments. **You submit the review.**

Throughout this skill "change" is the generic term for what the host calls a merge request (GitLab) or pull request (GitHub, Bitbucket) — the host adapter keeps that host's own word when naming the concrete API object or CLI call. Likewise "ticket" is the generic term for whatever the tracker holds (a JIRA issue, a GitHub issue).

The workflow is host- and tracker-agnostic; the host-specific and tracker-specific mechanics live in adapter files under `references/` and load only when you reach the step that needs them. This keeps the always-loaded body focused on judgment — the review itself, which is the same regardless of where the code and the ticket happen to live.

## Workflow

Work through steps in order. Prioritize reading the diff over full files — fetch full file content only when the diff lacks enough context to make a confident judgment.

### Step 1 — Identify the host and load its adapter

Determine which host the change lives on, primarily from the URL shape:

- `…/-/merge_requests/<n>` → GitLab → read `references/hosts/gitlab.md`
- `github.com/<owner>/<repo>/pull/<n>` → GitHub → read `references/hosts/github.md`

The adapter file is the authority for that host's mechanics: URL parsing, auth check, the exact calls to fetch metadata/diffs, the local-clone path convention, and how to post comments (draft note vs. pending review) with that host's own gotchas. Read it now and follow it wherever a later step says "per the host adapter."

If there's no adapter file for the host you're facing, degrade gracefully rather than stopping: discover the relevant tools with a keyword `ToolSearch` (or the platform's own CLI/API), confirm the fetch-metadata/fetch-diff/post-comment operations you need exist, and proceed. Tell the user you're running without a dedicated adapter so they know host-specific behavior is best-effort.

### Step 2 — Fetch change metadata

Using the metadata call from the host adapter, fetch the change's title, description, source/target branch, the SHAs needed for inline comment positions, and its web URL.

**If the metadata call fails with an auth error** (401, or a "not logged in" message), the host adapter's CLI/tool isn't authenticated — stop and ask the user to authenticate (the adapter states the exact command), rather than pre-checking auth separately. A success here also proves auth is good for posting in Step 7, since it's the same credentials.

### Step 3 — Identify the ticket, load its tracker adapter, and fetch it

Scan the title and description for a ticket reference:

- A JIRA key (regex `[A-Z][A-Z0-9]+-\d+`), bare or in a full `…atlassian.net/browse/<KEY>` URL → read `references/trackers/jira.md`
- A GitHub issue reference — a full `github.com/<owner>/<repo>/issues/<n>` URL, a cross-repo `<owner>/<repo>#<n>`, or a bare `#<n>` when the change itself is on GitHub in the same repo → read `references/trackers/github.md`

A full URL is unambiguous about which tracker it names; prefer it over a bare key/number if both somehow appear. The tracker is independent of the code host — a GitLab MR can reference a GitHub issue for requirements, and vice versa.

The tracker adapter is the authority for fetching that ticket: how to load or authenticate its tools (if needed), the exact call to fetch it, and what fields to extract (summary, description/acceptance criteria, issue type). Read it now and follow it as "per the tracker adapter."

If there's no adapter for the tracker you're facing, degrade gracefully the same way as Step 1. If no ticket reference is found at all, or the fetch fails for any reason, continue the review without requirements context — note it in the summary at the end (Step 9).

**Parallelize Steps 3 and 4** — the ticket fetch and the diff fetch are independent; issue both in the same tool call batch.

### Step 4 — Fetch diffs

Using the diff call from the host adapter, fetch every changed file's diff.

**Truncation check**: the host adapter states how to detect a truncated or partial diff (a file-count mismatch, a per-file size cap, etc.). If it's truncated, note "diff truncated — only N of M files reviewed" in the summary and prioritize the highest-risk files (auth, data access, public API surface).

**Line numbers**: Don't count lines from the diff manually — it's error-prone. After creating the worktree in Step 5, use a targeted `grep -n '<snippet>' <file>` on the actual file to find exact line numbers (prefer `grep -n` over `cat -n` of the whole file — it's far cheaper). Use the diff only to confirm the line was changed in this change. Anchor-line selection (`+` lines vs context lines) is covered in Step 7.

### Step 5 — Create a review worktree

Checking out the branch in the user's main clone would switch what's checked out from under them — disrupting whatever branch or uncommitted work they have there. A disposable worktree gives the review its own directory instead, so the main checkout is never touched.

The host adapter states the repo path's relative shape (it varies slightly — GitLab's namespace can nest subgroups, GitHub's is always exactly `<owner>/<repo>`) — there's no single standard clone root across users, so it's found by search rather than assumed.

```bash
# 1. Try common project-root conventions first
for ROOT in ~/projects ~/code ~/Code ~/dev ~/src ~/Developer ~/workspace ~/source/repos; do
  [ -d "$ROOT/<repo_path>" ] && break
done

# 2. Not found under any common root — search more broadly, matching by remote URL
#    rather than an assumed folder name, since the URL holds regardless of this
#    machine's own naming convention
find ~ -maxdepth 6 -name ".git" -type d 2>/dev/null -exec sh -c \
  'git -C "$1/.." remote get-url origin 2>/dev/null' _ {} \; | grep "<repo_path>"

# 3. Once found, fetch the source branch
WORKTREE_PATH="<repo_path>.review-<id>"
git -C <repo_path> fetch origin <source_branch>
git -C <repo_path> worktree prune

# 4. A worktree may already sit at this path — e.g. left behind by a prior run of
#    this skill that crashed before Step 8 cleanup. It's only safe to replace if it's
#    clean; it may otherwise hold uncommitted or unpushed work someone did there directly.
if [ -d "$WORKTREE_PATH" ]; then
  DIRTY=$(git -C "$WORKTREE_PATH" status --porcelain 2>&1)
  ON_REMOTE=$(git -C "$WORKTREE_PATH" branch -r --contains HEAD 2>/dev/null)
  if [ -n "$DIRTY" ] || [ -z "$ON_REMOTE" ]; then
    echo "STOP: $WORKTREE_PATH exists and is not verifiably clean (uncommitted changes, or HEAD isn't on any remote branch — possible unpushed commit). Do not delete it. Report this to the user and ask how to proceed."
    exit 1
  else
    git -C <repo_path> worktree remove "$WORKTREE_PATH"
  fi
fi

# 5. Add a detached worktree pinned to the head SHA
git -C <repo_path> worktree add --detach "$WORKTREE_PATH" <head_sha>
```

Pin to the exact head SHA rather than the branch name — it guarantees the worktree matches what the change actually contains, and it never collides with a worktree add if the user happens to already have that same branch checked out elsewhere (git refuses to check out a branch that's already checked out in another worktree; a commit SHA has no such restriction).

If the repo isn't found locally, proceed with diff-only review and note the limitation. If the fetch or worktree creation fails — including the STOP case above — note that local files aren't available and read with caution. Never force past the STOP check, and never fall back to checking out the branch in the user's main clone.

Use `$WORKTREE_PATH` (not the repo's main path) for every file read and `grep` in Step 6 onward.

### Step 6 — Review

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill tool with `skill: "code-review-pyramid"`) to load the full layer definitions, priority order, and review principles, then apply all five layers to the changes.

If the skill is not available, perform a thorough code review using your own judgment — cover correctness, edge cases, error handling, security, test coverage, and readability, prioritizing the most impactful findings.

If a ticket was fetched, use its acceptance criteria as the ground truth for correctness — map each criterion to the code explicitly and flag any that aren't met.

**While you're at it, track each changed file's Pyramid layer** — this is a side effect of the review you're already doing, not extra work. You'll use it in Step 9 to tell the human where their own attention is best spent, independent of how many (if any) inline comments you posted there:

- **Layer 1 (API Semantics)** and **Layer 2 (Implementation Semantics)** — flag a file here if it defines or changes a public contract other code depends on (an interface, an exported type, a method signature callers rely on), or if it implements business-rule logic: conditional branches encoding a business decision, state transitions, orchestration across multiple domain concerns. These are the files where getting it wrong is expensive to unwind later, so they deserve independent human judgment regardless of what the AI found.
- **Layers 3-5 (lower priority for this list)** — thin controllers/handlers that just forward a call with no branching of their own, repositories/DAOs doing straightforward parameterized CRUD with no business logic, test files (already gated by CI pass/fail), docs-only changes, and pure formatting/rename diffs.

This is architecture-agnostic — it's about the *role* a file plays (contract vs. business logic vs. plumbing), not its language or folder naming convention. In a C#/.NET codebase, Layer 1-2 candidates typically look like `I*.cs` interfaces and their `Domain`/`Application` implementations; Layers 3-5 typically look like `Controllers/`, `Repositories/`/`Persistence`, and test projects — but read the actual diff hunk, not just the path, since a controller with real branching logic of its own can still rank high, and a "domain" file that's pure boilerplate doesn't automatically rank high just because of where it lives.

Be selective, not exhaustive — most changes, even large ones, should surface a short list. Don't cap it at an arbitrary number; let the criteria above do the filtering.

### Step 7 — Post comments per the host adapter

Post each finding as a draft (GitLab draft note, GitHub pending-review comment) — only you can see them until the user submits the review, so they can edit or remove comments before they go live.

The host adapter names the bundled script that handles the posting mechanics (`scripts/post_review_notes_gitlab.py` or `scripts/post_review_notes_github.py`, relative to this SKILL.md) and the exact invocation. Both scripts share the same notes-file JSON shape — one object per finding, with `new_path`/`new_line` for an inline anchor or `"general": true` for a positionless note — so drafting findings doesn't change based on which host you're on; only the script and its extra flags differ.

Both also mark each comment with a trailing 🤖 and add one positionless comment attributing the review as a whole ("Code reviewed using Sonnet 5 (high) 🤖"). Leave both to the script — writing the marker into a note yourself only risks it landing twice.

**Comment format** (what goes in each `note`): default to 2-4 sentences of continuous prose — name the symbol/line, state the concrete problem, then the fix:
```
`fetchUser` doesn't handle the case where the DB returns `null` — the `.Name` access on line 47 will panic at runtime. Add a nil check or return an early error.
```

Don't restate context already visible in the diff — fold the impact into the same flow of sentences. It's fine to run longer than 4 sentences when the failure mechanism itself genuinely needs the room (concurrency races, security, a scope change spanning multiple callers) — but even then keep it one tight paragraph.

When the finding is a clear-cut bug, assert it and prescribe the fix, as above. When the intent behind the code might be deliberate — a scope decision, a naming choice, a spec deviation that could be intentional — end with a direct question instead of a directive:
```
`PersonMatchOutcome.MatchedAndAdvanced`/`MatchedNoChange` are referenced in this doc but don't exist on the enum (only `Created`, `Matched`, `RejectedActiveMatch` do) — leftover from an earlier draft? Worth fixing since this is the domain layer's public contract.
```

**Posting guidelines:**
- Only comment when there's a genuine issue — not every observation
- Be specific and brief: name the exact symbol/line, state the concrete problem, then the fix or a direct question — skip a forensic walkthrough of exactly how it would trigger
- If a ticket acceptance criterion isn't met, quote it explicitly (the quote doesn't count against the sentence budget)
- Avoid style nits unless they cross into real readability problems
- Don't repeat the same finding across multiple files — pick the clearest occurrence
- Pass `--model "<your model name>"` to the script so the attribution comment names the reviewing model — you always know this from your environment context, so always pass it. Add `--effort "<level>"` only when you have a concrete, known effort/thinking-level setting for this session — never guess one just to fill the field.

### Step 8 — Remove the worktree

If a worktree was created in Step 5, remove it now — do this even if earlier steps failed partway (e.g. posting comments errored out) or the review was diff-only and no worktree exists. If Step 5 hit its STOP check and left a pre-existing worktree in place untouched, this run never created one — don't remove it here either:

```bash
git -C <repo_path> worktree remove "$WORKTREE_PATH"
```

If removal is refused, leave the worktree in place and tell the user exactly what git reported, so they can decide what to do with it.

### Step 9 — Output the review summary

After posting all inline comments, output the summary directly in the conversation (do **not** post it to the change):

```
## Code Review Summary

**Change**: [<title>](<web_url>)
**Ticket**: [PROJ-123](<ticket_url>) — <ticket summary>
*(or "No ticket linked — reviewed without requirements context")*

**Findings** (<N> posted, most important first):
- <finding 1>
- <finding 2>
*(when N is 0, replace the list with one line: "None — <one-clause why, e.g. "tightly-scoped one-line fix, verified against the backend contract">.")*

**Worth your own look** (Layers 1-2 — independent of whether the AI commented there):
- `<file>`[, `<file>`, ...] — <one-clause reason; group files sharing the same reason into one line>
*(omit this whole section when no file rises to Layer 1-2 — don't replace it with a note about what's lower priority)*

**Coverage**: <comma-joined list of only the layers with >0 comments, e.g. "2 Implementation Semantics, 1 Tests"> *(or "no comments posted" when N is 0)*

*(only when N > 0)* Draft comments have been posted. <submit instructions from the host adapter>
```

## Hard constraints

- **Never** approve, reject, mark as reviewed, or submit the review — only post comments and notes
- **Never** check out the change's branch in the user's main clone — always review from the isolated worktree created in Step 5
- **Never** force-delete or force-remove the review worktree (Step 5's replacement check, Step 8's cleanup) — if it isn't verifiably clean, stop and tell the user instead of overriding
- **Always** remove the worktree before finishing (Step 8), even if the review is aborted or fails partway
- **Always** post comments through the host adapter's bundled script — don't post drafts by hand
- **Large diffs (>500 changed lines)**: note the scope in the summary, focus on highest-risk files (those touching APIs, auth, data access), and explicitly state not all changes were reviewed
