---
name: gitlab-jira-mr-review
description: >
  Reviews a GitLab merge request against its linked JIRA ticket, then posts inline comments on the
  diff for you to submit — it fetches the MR and ticket context, structures the review, and writes
  the comments directly to the MR. User-only: runs only when explicitly invoked with
  /gitlab-jira-mr-review <MR URL>. When the user wants to review a GitLab MR, code-review a merge
  request, check a GitLab PR, or evaluate MR changes against JIRA requirements, suggest running this
  command rather than doing a manual review.
argument-hint: "<GitLab MR URL>"
allowed-tools: [Read, Bash, Skill, Write, ToolSearch]
disable-model-invocation: true
---

# GitLab + JIRA MR Review

Structured code review for GitLab MRs. Fetches JIRA requirements when available, reviews the code and posts inline comments. **You submit the review.**

## Workflow

Work through steps in order. Prioritize reading the diff over full files — fetch full file content only when the diff lacks enough context to make a confident judgment.

### Step 1 — Parse the URL

From the URL (e.g. `https://gitlab.com/acme/my-service/-/merge_requests/42`) extract:
- `project_path`: e.g. `acme/my-service`
- `project_path_encoded`: URL-encode `/` as `%2F` → `acme%2Fmy-service`
- `mr_iid`: the MR number (`42`)

### Step 2 — Fetch MR metadata

`mcp__glab__glab_api` is a deferred tool — load its schema first:

```
ToolSearch: select:mcp__glab__glab_api
```

Then call it:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

**If this first call fails with an auth error** (401, or a "not logged in" message), `glab` isn't authenticated. Stop and ask the user — don't pre-check auth separately, since this call surfaces it anyway, and a success here proves auth is good for posting in Step 7 too (same credentials):

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until auth is confirmed.

From the response extract:
- `title`, `description` — scan both for a JIRA key: regex `[A-Z][A-Z0-9]+-\d+`
- `source_branch`, `target_branch`
- `diff_refs.base_sha`, `diff_refs.start_sha`, `diff_refs.head_sha` — needed for inline comment positions
- `web_url` — for the summary note

### Step 3 — Fetch JIRA context (if a ticket was found)

If a JIRA key was found, fetch the ticket with `mcp__claude_ai_Atlassian__getJiraIssue` (a deferred tool — load it via ToolSearch first). Read the cloudId from `$HOME/.claude/atlassian-cloud-id` (use the expanded absolute path — `~` isn't expanded by file tools), then call `getJiraIssue` with `issueIdOrKey: "<KEY>"` and that `cloudId`. Extract:
- Summary (the "what")
- Description / acceptance criteria (the "done conditions")
- Issue type (Story / Task / Bug)

**First run, or auth not yet established?** If ToolSearch returns only `mcp__claude_ai_Atlassian__authenticate` (not `getJiraIssue`), or the cloudId cache file is missing, complete the one-time Atlassian OAuth and cloudId setup in [reference/jira-setup.md](reference/jira-setup.md) before calling `getJiraIssue`. Once done, both are cached and this step stays on the fast path above.

If no ticket is found, or the fetch fails for any other reason, continue without requirements context — note it in the summary at the end.

**Parallelize Steps 3 and 4** — JIRA fetch and diff fetch are independent; issue both in the same tool call batch.

### Step 4 — Fetch diffs

Use `limit: 150000` to avoid truncation on large MRs:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/changes   (limit: 150000)
```

The response is the full MR object with an additional `changes` array. Each element has:
- `new_path`, `old_path`
- `diff` — unified diff string (the hunks)
- `new_file`, `deleted_file`, `renamed_file` booleans

**Truncation check**: compare `response.changes.length` with `mr.changes_count` from Step 2. If they differ, the diff is truncated — note "diff truncated — only N of M files reviewed" in the summary and prioritize the highest-risk files (auth, data access, public API surface).

**Line numbers**: Don't count lines from the diff manually — it's error-prone. After creating the worktree in Step 5, use a targeted `grep -n '<snippet>' <file>` on the actual file to find exact line numbers (prefer `grep -n` over `cat -n` of the whole file — it's far cheaper). Use the diff only to confirm the line was changed in this MR. Anchor-line selection (`+` lines vs context lines) is covered in Step 7.

### Step 5 — Create a review worktree

Checking out the branch in the user's main clone would switch what's checked out from under them — disrupting whatever branch or uncommitted work they have there. A disposable worktree gives the review its own directory instead, so the main checkout is never touched.

Repos are cloned under `~/projects/<org-id>/<group/subgroups>/<project>`, mirroring the GitLab namespace. For example, `https://gitlab.com/acme/platform/my-service` would be at `~/projects/acme/platform/my-service`.

```bash
# 1. Derive the path from the project_path extracted in Step 1
ls ~/projects/<project_path> 2>/dev/null

# 2. If not found, fall back to searching by remote URL
find ~/projects -maxdepth 5 -name ".git" -exec sh -c \
  'git -C "$1/.." remote get-url origin 2>/dev/null' _ {} \; | grep "<project_path>"

# 3. Once found, fetch the source branch
WORKTREE_PATH="<repo_path>.mr<mr_iid>-review"
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

# 5. Add a detached worktree pinned to head_sha
git -C <repo_path> worktree add --detach "$WORKTREE_PATH" <diff_refs.head_sha>
```

Pin to the exact `head_sha` rather than the branch name — it guarantees the worktree matches what the MR actually contains, and it never collides with a worktree add if the user happens to already have that same branch checked out elsewhere (git refuses to check out a branch that's already checked out in another worktree; a commit SHA has no such restriction).

If the repo isn't found locally, proceed with diff-only review and note the limitation. If the fetch or worktree creation fails — including the STOP case above — note that local files aren't available and read with caution. Never force past the STOP check, and never fall back to checking out the branch in the user's main clone.

Use `$WORKTREE_PATH` (not the repo's main path) for every file read and `grep` in Step 6 onward.

### Step 6 — Review

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill tool with `skill: "code-review-pyramid"`) to load the full layer definitions, priority order, and review principles, then apply all five layers to the MR changes.

If the skill is not available, perform a thorough code review using your own judgment — cover correctness, edge cases, error handling, security, test coverage, and readability, prioritizing the most impactful findings.

If a JIRA ticket was fetched, use its acceptance criteria as the ground truth for correctness — map each criterion to the code explicitly and flag any that aren't met.

### Step 7 — Post comments as draft notes

Post each finding as a **draft note** — only you can see them until you submit the review in the GitLab UI, so you can edit or remove comments before they go live.

The mechanics of posting are deterministic and easy to get subtly wrong, so they live in a bundled script: **`scripts/post_review_notes.py`** (relative to this SKILL.md). It posts an arbitrary number of notes, verifies each one anchored to the diff, and falls back gracefully when it can't. Your job is to produce good findings; the script handles the GitLab plumbing.

1. Write your findings to a JSON array — one object per finding:

```json
// /tmp/mr<iid>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the **new-file** line number (integer). `old_path` defaults to `new_path` — set it explicitly only for renamed files (use the pre-rename path).
- Use `"general": true` (or simply omit `new_line`) for a positionless note that publishes as a general discussion comment.
- Don't add the `Co-reviewed with :robot:` line yourself — the script appends it to every note if missing (the conversation summary in Step 8 is exempt).

2. Run the script (it reads `diff_refs` from Step 2 and purges this skill's own prior drafts so reruns don't duplicate):

```bash
python3 <skill_dir>/scripts/post_review_notes.py \
  --project <project_path_encoded> --mr <mr_iid> \
  --base-sha <diff_refs.base_sha> --start-sha <diff_refs.start_sha> --head-sha <diff_refs.head_sha> \
  --notes /tmp/mr<iid>_notes.json --purge
```

3. Read the per-note summary it prints. Each line reports `resolved=True/False` or `general=True`.

**Why the script, and what it protects you from:**
- GitLab **always returns HTTP 200** for `draft_notes`, even when it can't resolve the position. The real indicator is the `line_code` field in the response — GitLab only populates it when the position actually anchored to the diff. An unresolvable draft (`line_code` null) silently never publishes as an inline comment. The script detects this, deletes the draft, and re-posts it positionless so the finding is never lost — it just lands as a general discussion comment instead.
- `old_path` is required for inline placement; omitting it silently downgrades to a plain note. The script always sends it.
- **Prefer `+` lines as anchors**: pick a `new_line` that appears with a `+` prefix in the diff (added in this MR) — GitLab resolves those reliably. **Context lines (unchanged lines) are unreliable anchors even when they appear inside the hunk** — GitLab often fails to set `line_code` for them. If your finding is on an unchanged line (e.g. a function signature the MR didn't touch), anchor to the nearest `+` line nearby, or mark it `general` from the start.

**Comment format** (what goes in each `note`):
```
`fetchUser` doesn't handle the case where the DB returns `null` — the `.Name` access on line 47 will panic at runtime.

Add a nil check or return an early error.
```

**Posting guidelines:**
- Only comment when there's a genuine issue — not every observation
- Be specific: name the exact symbol/line, explain the problem, suggest a fix
- If a JIRA acceptance criterion isn't met, quote it explicitly
- Avoid style nits unless they cross into real readability problems
- Don't repeat the same finding across multiple files — pick the clearest occurrence

### Step 8 — Remove the worktree

If a worktree was created in Step 5, remove it now — do this even if earlier steps failed partway (e.g. posting comments errored out) or the review was diff-only and no worktree exists. If Step 5 hit its STOP check and left a pre-existing worktree in place untouched, this run never created one — don't remove it here either:

```bash
git -C <repo_path> worktree remove "$WORKTREE_PATH"
```

If removal is refused, leave the worktree in place and tell the user exactly what git reported, so they can decide what to do with it.

### Step 9 — Output the review summary

After posting all inline comments, output the summary directly in the conversation (do **not** post it to the MR):

```
## Code Review Summary

**MR**: [<title>](<web_url>)
**JIRA**: [PROJ-123](<jira_url>) — <ticket summary>
*(or "No JIRA ticket linked — reviewed without requirements context")*

**Key findings** (most important first):
- <finding 1>
- <finding 2>
- <finding 3>

**Pyramid coverage:**
| Layer | Comments posted |
|---|---|
| API Semantics | N |
| Implementation Semantics | N |
| Documentation | N |
| Tests | N |
| Code Style | N |

*Draft comments have been posted. Open the MR in GitLab, review the inline notes, then hit **Submit review** to publish.*
```

## Hard constraints

- **Never** approve, reject, mark as reviewed, or submit the review — only post comments and notes
- **Never** check out the MR branch in the user's main clone — always review from the isolated worktree created in Step 5
- **Never** force-delete or force-remove the review worktree (Step 5's replacement check, Step 8's cleanup) — if it isn't verifiably clean, stop and tell the user instead of overriding
- **Always** remove the worktree before finishing (Step 8), even if the review is aborted or fails partway
- **Always** post comments through `scripts/post_review_notes.py` — don't post draft notes by hand
- **Large diffs (>500 changed lines)**: note the scope in the summary, focus on highest-risk files (those touching APIs, auth, data access), and explicitly state not all changes were reviewed
