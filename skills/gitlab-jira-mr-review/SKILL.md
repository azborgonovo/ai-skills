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

---

### Step 1 — Parse the URL

From the URL (e.g. `https://gitlab.com/acme/my-service/-/merge_requests/42`) extract:
- `project_path`: e.g. `acme/my-service`
- `project_path_encoded`: URL-encode `/` as `%2F` → `acme%2Fmy-service`
- `mr_iid`: the MR number (`42`)

---

### Step 2 — Fetch MR metadata

`mcp__glab__glab_api` is a deferred tool — load its schema first:

```
ToolSearch: select:mcp__glab__glab_api
```

**Check glab authentication first** — run this before any API call:

```bash
glab auth status
```

If it exits non-zero or prints "You are not logged in", stop and ask the user to authenticate:

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until auth is confirmed.

Then call it:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

From the response extract:
- `title`, `description` — scan both for a JIRA key: regex `[A-Z][A-Z0-9]+-\d+`
- `source_branch`, `target_branch`
- `diff_refs.base_sha`, `diff_refs.start_sha`, `diff_refs.head_sha` — needed for inline comment positions
- `web_url` — for the summary note

---

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

---

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
the branch in Step 5, use `grep -n` or `cat -n` on the actual file to find exact line numbers for
your findings. Use the diff only to confirm the line was changed in this MR.

**Prefer `+` lines as comment anchors**: When picking a line to anchor an inline comment, prefer
a line that appears with a `+` prefix in the diff (newly added in this MR). GitLab resolves these
positions reliably. Anchoring to a context line (an unchanged line that survived inside a hunk
with large deletions) can silently fail at submit time — the draft is accepted but never publishes.
If there is no `+` line close to your finding, post a general note instead (see Step 7).

---

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

---

### Step 6 — Review

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill
tool with `skill: "code-review-pyramid"`) to load the full layer definitions, priority order, and
review principles, then apply all five layers to the MR changes.

If the skill is not available, perform a thorough code review using your own judgment — cover
correctness, edge cases, error handling, security, test coverage, and readability, prioritising
the most impactful findings.

If a JIRA ticket was fetched, use its acceptance criteria as the ground truth for correctness —
map each criterion to the code explicitly and flag any that aren't met.

---

### Step 7 — Post comments as draft notes

Post each finding as a **draft note** — only you can see them until you submit the review in the
GitLab UI. This lets you remove or edit comments before they become visible to others.

1. Write the JSON body to a temp file (one file per note):

```json
// /tmp/mr<iid>_note<n>.json
{
  "note": "<observation>\n\n<suggested fix if applicable>\n\nCo-reviewed with :robot:",
  "position": {
    "base_sha": "<diff_refs.base_sha>",
    "start_sha": "<diff_refs.start_sha>",
    "head_sha": "<diff_refs.head_sha>",
    "position_type": "text",
    "new_path": "<relative file path>",
    "old_path": "<old file path — same as new_path unless the file was renamed>",
    "new_line": <new-file line number as an integer, not a quoted string>
  }
}
```

2. Post via Bash:

```bash
glab api --method POST \
  --header "Content-Type: application/json" \
  --input /tmp/mr<iid>_note<n>.json \
  "projects/<project_path_encoded>/merge_requests/<mr_iid>/draft_notes"
```

**Before posting — purge stale drafts**: List existing draft notes and delete any that duplicate
what you're about to post. This prevents leftover drafts from a previous review run appearing as
duplicates to the author.

```bash
# List existing drafts and their IDs
glab api "projects/<project_path_encoded>/merge_requests/<mr_iid>/draft_notes" \
  | python3 -c "import sys,json; [print(f'id={n[\"id\"]} | {n[\"note\"][:80]}') for n in json.load(sys.stdin)]"

# Delete a stale draft by ID
glab api --method DELETE \
  "projects/<project_path_encoded>/merge_requests/<mr_iid>/draft_notes/<draft_id>"
```

Post notes sequentially and verify each one was accepted with a resolved position:

```bash
for i in 1 2 3 4 5; do
  response=$(glab api --method POST --header "Content-Type: application/json" \
    --input /tmp/mr<iid>_note$i.json \
    "projects/<project_path_encoded>/merge_requests/<mr_iid>/draft_notes" 2>&1)
  if [ $? -eq 0 ]; then
    echo "$response" | python3 -c "
import sys, json
d = json.load(sys.stdin)
pos = d.get('position')
print(f'note $i: id={d[\"id\"]} position_resolved={pos is not None}')
" 2>/dev/null || echo "note $i posted (could not parse response)"
  else
    echo "note $i failed: $response"
  fi
done
```

**Critical**: GitLab **always returns HTTP 200** for `draft_notes`, even when the position cannot
be resolved. A draft with an unresolvable position will silently remain as a draft at submit time
— it will never publish as an inline comment. Check `position_resolved=True` in the response
above. If you see `position_resolved=False`, delete that draft immediately and re-post without a
position (as a general discussion note):

```bash
# Delete the failed draft
glab api --method DELETE \
  "projects/<project_path_encoded>/merge_requests/<mr_iid>/draft_notes/<id>"

# Re-post as a positionless draft note — stays in the review queue, publishes as
# a general discussion when the user hits Submit (no position field)
glab api --method POST \
  --header "Content-Type: application/json" \
  --field "note=<note text>" \
  "projects/<project_path_encoded>/merge_requests/<mr_iid>/draft_notes"
```

**`position.old_path` is required for inline placement.** GitLab silently falls back to a plain
discussion note (not inline on the diff) if it is omitted. For new and unmodified files use the
same value as `new_path`. For renamed files use the path before renaming.

**Comment format:**
```
`fetchUser` doesn't handle the case where the DB returns `null` — the `.Name` access on line 47 will panic at runtime.

Add a nil check or return an early error.

Co-reviewed with :robot:
```

**Posting guidelines:**
- Only comment when there's a genuine issue — not every observation
- Be specific: name the exact symbol/line, explain the problem, suggest a fix
- If a JIRA acceptance criterion isn't met, quote it explicitly
- Avoid style nits unless they cross into real readability problems
- Don't repeat the same finding across multiple files — pick the clearest occurrence

---

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

---

## Hard constraints

- **Never** approve, reject, mark as reviewed, or submit the review — only post comments and notes
- **Never** checkout a branch if the local repo has uncommitted changes without warning the user first
- **Always** end every inline comment with `Co-reviewed with :robot:` as the last line (see comment format above). The summary is conversation-only and is exempt.
- **Large diffs (>500 changed lines)**: note the scope in the summary, focus on highest-risk files
  (those touching APIs, auth, data access), and explicitly state not all changes were reviewed
