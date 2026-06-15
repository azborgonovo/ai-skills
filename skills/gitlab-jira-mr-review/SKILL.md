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

Call `mcp__glab__glab_api` (no repo context required — it's a direct HTTP wrapper):

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

If a JIRA key was found, load `mcp__claude_ai_Atlassian__getJiraIssue` via ToolSearch and call it
with `issueIdOrKey: "<KEY>"`. Extract:
- Summary (the "what")
- Description / acceptance criteria (the "done conditions")
- Issue type (Story / Task / Bug)

If no ticket is found, or the fetch fails, continue without requirements context — note it in the
summary at the end.

---

### Step 4 — Fetch diffs

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/diffs
```

Response is an array of file objects. Each has:
- `new_path`, `old_path`
- `diff` — unified diff string (the hunks)
- `new_file`, `deleted_file`, `renamed_file` booleans

**Parse new-file line numbers from the diff.** For each hunk:
1. `@@ -<old_start>,<old_count> +<new_start>,<new_count> @@` → set `new_line = new_start`
2. Context line (` `): `new_line++`
3. Added line (`+`): record `(new_path, new_line)` as commentable, then `new_line++`
4. Deleted line (`-`): skip (line doesn't exist in new file)

Build a map: `file → list of (new_line, content)` for added/modified lines.

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
```

If the repo isn't found locally, proceed with diff-only review and note the limitation.

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

### Step 7 — Post inline comments

For each finding worth commenting on, post an inline comment via `mcp__glab__glab_api`:

```
POST projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions
```

Build the `field` array for the request flags:

```
body=":robot: **[Layer]** <observation. Suggested fix if applicable.>"
position[base_sha]=<diff_refs.base_sha>
position[start_sha]=<diff_refs.start_sha>
position[head_sha]=<diff_refs.head_sha>
position[position_type]=text
position[new_path]=<relative file path>
position[new_line]=<computed new-file line number>
```

**Comment format:**
```
:robot: **[Implementation]** `fetchUser` doesn't handle the case where the DB returns `null` — the `.Name` access on line 47 will panic at runtime. Add a nil check or return an early error.
```

**Posting guidelines:**
- Only comment when there's a genuine issue — not every observation
- Be specific: name the exact symbol/line, explain the problem, suggest a fix
- If a JIRA acceptance criterion isn't met, quote it explicitly
- Avoid style nits unless they cross into real readability problems
- Don't repeat the same finding across multiple files — pick the clearest occurrence
- If the API rejects a position (line outside diff), fall back to a general note quoting the code

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

*Inline comments have been posted to the MR. Please review and submit when ready.*
```

---

## Hard constraints

- **Never** approve, reject, mark as reviewed, or submit the review — only post comments and notes
- **Never** checkout a branch if the local repo has uncommitted changes without warning the user first
- **Always** start every comment and the summary with `:robot:`
- **Large diffs (>500 changed lines)**: note the scope in the summary, focus on highest-risk files
  (those touching APIs, auth, data access), and explicitly state not all changes were reviewed
