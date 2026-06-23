---
name: gitlab-jira-mr-review
description: >
  Reviews a GitLab merge request against its linked JIRA ticket, then posts inline comments on
  the diff — you submit. TRIGGER when the user
  invokes /gitlab-jira-mr-review <MR URL>, or asks to review a GitLab MR, code-review a merge
  request, check a GitLab PR, or evaluate MR changes against JIRA requirements. Always use this
  skill instead of attempting a manual MR review — it fetches context, structures the review, and
  posts comments directly to the MR.
argument-hint: "<GitLab MR URL>"
---

# GitLab + JIRA MR Review

Structured code review for GitLab MRs. Fetches JIRA requirements when available, reviews the code and posts inline comments. **You submit the review.**

## Workflow

Work through steps in order. Prioritise reading the diff over full files — fetch full file content
only when the diff lacks enough context to make a confident judgment.

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

**If this first call fails with an auth error** (401, or a "not logged in" message), `glab` isn't
authenticated. Stop and ask the user — don't pre-check auth separately, since this call surfaces
it anyway, and a success here proves auth is good for posting in Step 7 too (same credentials):

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until auth is confirmed.

From the response extract:
- `title`, `description` — scan both for a JIRA key: regex `[A-Z][A-Z0-9]+-\d+`
- `source_branch`, `target_branch`
- `diff_refs.base_sha`, `diff_refs.start_sha`, `diff_refs.head_sha` — needed for inline comment positions
- `web_url` — for the summary note

### Step 3 — Fetch JIRA context (if a ticket was found)

If a JIRA key was found, try to load `mcp__claude_ai_Atlassian__getJiraIssue` via ToolSearch.

**If ToolSearch returns only `mcp__claude_ai_Atlassian__authenticate`** (not `getJiraIssue`), the
Atlassian MCP server needs OAuth. Handle it before continuing:

1. Call `mcp__claude_ai_Atlassian__authenticate` (no parameters needed).
2. Share the returned authorization URL with the user:
   > Atlassian needs authorization. Please open this URL and complete the login: `<url>`
   > Let me know when done.
3. **Pause** — do not proceed until the user confirms.
4. Once confirmed, retry ToolSearch for `mcp__claude_ai_Atlassian__getJiraIssue`. If it's now
   available, call it. If it still isn't, skip JIRA context and note it in the summary.

Once authenticated, call `getJiraIssue` with `issueIdOrKey: "<KEY>"` and
`cloudId: "<org>.atlassian.net"` (e.g. `goodhabitz.atlassian.net`). Extract:
- Summary (the "what")
- Description / acceptance criteria (the "done conditions")
- Issue type (Story / Task / Bug)

If no ticket is found, or the fetch fails for any other reason, continue without requirements
context — note it in the summary at the end.

**Parallelise Steps 3 and 4** — JIRA fetch and diff fetch are independent; issue both in the same
tool call batch.

### Step 4 — Fetch diffs

Use `limit: 150000` to avoid truncation on large MRs:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/changes   (limit: 150000)
```

The response is the full MR object with an additional `changes` array. Each element has:
- `new_path`, `old_path`
- `diff` — unified diff string (the hunks)
- `new_file`, `deleted_file`, `renamed_file` booleans

**Truncation check**: compare `response.changes.length` with `mr.changes_count` from Step 2. If
they differ, the diff is truncated — note "diff truncated — only N of M files reviewed" in the
summary and prioritise the highest-risk files (auth, data access, public API surface).

**Line numbers**: Don't count lines from the diff manually — it's error-prone. After checking out
the branch in Step 5, use a targeted `grep -n '<snippet>' <file>` on the actual file to find exact
line numbers (prefer `grep -n` over `cat -n` of the whole file — it's far cheaper). Use the diff
only to confirm the line was changed in this MR. Anchor-line selection (`+` lines vs context
lines) is covered in Step 7.

### Step 5 — Check out the source branch locally

Repos are cloned under `~/projects/<org-id>/<group/subgroups>/<project>`, mirroring the GitLab
namespace. For example, `https://gitlab.com/acme/platform/my-service` would be at
`~/projects/acme/platform/my-service`.

```bash
# 1. Derive the path from the project_path extracted in Step 1
ls ~/projects/<project_path> 2>/dev/null

# 2. If not found, fall back to searching by remote URL
find ~/projects -maxdepth 5 -name ".git" -exec sh -c \
  'git -C "$1/.." remote get-url origin 2>/dev/null' _ {} \; | grep "<project_path>"

# 3. Once found, fetch and checkout
git -C <repo_path> fetch origin
git -C <repo_path> checkout <source_branch> 2>/dev/null || \
  git -C <repo_path> checkout -b <source_branch> origin/<source_branch>

# 4. Verify local HEAD matches the MR's head_sha — the branch may have new commits
#    that aren't reflected in the local tracking branch yet.
LOCAL_HEAD=$(git -C <repo_path> log -1 --format=%H)
if [ "$LOCAL_HEAD" != "<diff_refs.head_sha>" ]; then
  git -C <repo_path> pull origin <source_branch>
fi
```

If the repo isn't found locally, proceed with diff-only review and note the limitation.
If the pull fails, note that local files may not match the MR's head and read with caution.

### Step 6 — Review

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill
tool with `skill: "code-review-pyramid"`) to load the full layer definitions, priority order, and
review principles, then apply all five layers to the MR changes.

If the skill is not available, perform a thorough code review using your own judgment — cover
correctness, edge cases, error handling, security, test coverage, and readability, prioritising
the most impactful findings.

If a JIRA ticket was fetched, use its acceptance criteria as the ground truth for correctness —
map each criterion to the code explicitly and flag any that aren't met.

### Step 7 — Post comments as draft notes

Post each finding as a **draft note** — only you can see them until you submit the review in the
GitLab UI, so you can edit or remove comments before they go live.

The mechanics of posting are deterministic and easy to get subtly wrong, so they live in a
bundled script: **`scripts/post_review_notes.py`** (relative to this SKILL.md). It posts an
arbitrary number of notes, verifies each one anchored to the diff, and falls back gracefully when
it can't. Your job is to produce good findings; the script handles the GitLab plumbing.

1. Write your findings to a JSON array — one object per finding:

```json
// /tmp/mr<iid>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the **new-file** line number (integer). `old_path` defaults to `new_path` — set it
  explicitly only for renamed files (use the pre-rename path).
- Use `"general": true` (or simply omit `new_line`) for a positionless note that publishes as a
  general discussion comment.
- Don't add the `Co-reviewed with :robot:` line yourself — the script appends it if missing.

2. Run the script (it reads `diff_refs` from Step 2 and purges this skill's own prior drafts so
   reruns don't duplicate):

```bash
python3 <skill_dir>/scripts/post_review_notes.py \
  --project <project_path_encoded> --mr <mr_iid> \
  --base-sha <diff_refs.base_sha> --start-sha <diff_refs.start_sha> --head-sha <diff_refs.head_sha> \
  --notes /tmp/mr<iid>_notes.json --purge
```

3. Read the per-note summary it prints. Each line reports `resolved=True/False` or `general=True`.

**Why the script, and what it protects you from:**
- GitLab **always returns HTTP 200** for `draft_notes`, even when it can't resolve the position. An
  unresolvable draft silently never publishes as an inline comment. The script checks for a
  resolved position and, on failure, deletes the draft and re-posts it positionless so the finding
  is never lost — it just lands as a general discussion comment instead of inline.
- `old_path` is required for inline placement; omitting it silently downgrades to a plain note. The
  script always sends it.
- **Prefer `+` lines as anchors**: pick a `new_line` that appears with a `+` prefix in the diff
  (added in this MR) — GitLab resolves those reliably. Context lines inside large-deletion hunks
  often fail to resolve. If no `+` line is near your finding, mark it `general` from the start.

**Comment format** (what goes in each `note` — the script adds the `Co-reviewed with :robot:`
footer for you, so don't write it yourself):
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

### Step 8 — Output the review summary

After posting all inline comments, output the summary directly in the conversation (do **not**
post it to the MR):

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
- **Never** checkout a branch if the local repo has uncommitted changes without warning the user first
- **Always** post comments through `scripts/post_review_notes.py`, which ends every comment with `Co-reviewed with :robot:`. Don't post draft notes by hand. The conversation summary is exempt from the footer.
- **Large diffs (>500 changed lines)**: note the scope in the summary, focus on highest-risk files
  (those touching APIs, auth, data access), and explicitly state not all changes were reviewed
