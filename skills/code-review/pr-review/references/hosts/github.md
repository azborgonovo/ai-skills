# Host adapter: GitHub

Mechanics for reviewing a GitHub pull request. Read this when Step 1 identifies the host as GitHub (URL shape `https://github.com/<owner>/<repo>/pull/<number>`).

**Status**: the read-side calls below (`gh pr view`, `gh api .../pulls/<n>/files`) were run live against a real repo/PR (v2.89.0, authenticated) and returned the fields documented here. The posting mechanics (pending-review creation, line validation) follow the current GitHub REST API docs but weren't fired against a real PR, to avoid creating a live review as a side effect of writing this adapter — treat the happy path as reliable and the fallback path (below) as the safety net for the rare case it isn't.

## Tooling

Use the `gh` CLI over Bash — no separate MCP connector needed once `gh auth status` shows you're logged in. If `gh` isn't installed or authenticated, fall back to the graceful-degradation path in Step 1 (discover MCP GitHub tools via `ToolSearch`), or ask the user to `gh auth login`.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,body,baseRefName,headRefName,baseRefOid,headRefOid,changedFiles,statusCheckRollup,url
```

Extract:
- `title`, `body` — scan both for a ticket reference (Step 3)
- `baseRefName`, `headRefName`
- `baseRefOid`, `headRefOid` — these are the `base_sha`/`head_sha` equivalents used for inline comment positions
- `statusCheckRollup` — the CI signal handed to review-changes, so the review reports test status from GitHub's own checks rather than building the PR locally
- `url` — for the summary note

## Fetch diffs (Step 4, diff-only fallback)

Only needed when Step 4 can't create a worktree — with one, the review reads the diff from git in the worktree, which has neither GitHub's per-file cap nor its pagination to work around.

```
gh api repos/<owner>/<repo>/pulls/<number>/files --paginate
```

Each element has:
- `filename`, `previous_filename` (renames only)
- `status` (`added`/`removed`/`modified`/`renamed`)
- `patch` — unified diff string (the hunks). **Absent for binary files and for files GitHub considers too large to diff** — treat those as diff-unavailable and skip line-anchored comments on them.

**Truncation check**: `--paginate` handles GitHub's page size limit, but very large PRs can still hit GitHub's own per-file diff cap (files over ~3000 lines return no `patch`). Note in the summary "diff unavailable for N large/binary files — reviewed by reading the file directly" when this happens, and prioritize the highest-risk files (auth, data access, public API surface).

## Repo path shape (Step 4)

`<repo_path>` is `<owner>/<repo>` (GitHub has no nested subgroup concept, unlike GitLab). For example, `https://github.com/acme/my-service` → `acme/my-service`. This is a relative shape, not an absolute location — Step 4's script searches for it rather than assuming a fixed clone root.

## Post comments as a pending review (Step 6)

GitHub's equivalent of a draft note is a **pending review**: a review created via the API with no `event` field stays in `PENDING` state, visible only to you, until the user submits it from the GitHub UI. Unlike GitLab, GitHub validates every inline comment's `line`/`path` against the diff **atomically** — if even one comment in the batch doesn't land on a line that's actually part of the diff, the whole review-creation call is rejected (HTTP 422) and *none* of the comments are created. The bundled script handles this by validating anchors locally before ever calling the API, so a bad anchor downgrades just that one finding instead of failing the whole batch.

The script is **`scripts/post_review_notes_github.py`** (relative to the SKILL.md). It fetches the PR's diff itself to validate anchors, posts one pending review containing all the inline comments plus a body listing anything it couldn't anchor, and purges this skill's own prior pending review before reposting so reruns don't duplicate.

1. Write findings to a JSON array — same shape as the GitLab adapter, so the note-drafting step doesn't change based on host:

```json
// /tmp/pr<number>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the **new-file** line number (integer). Only lines that appear with a `+` prefix in the file's `patch` are valid anchors — the script checks this itself, but anchoring to a `+` line in the first place (same rule as the GitLab adapter) means it's very unlikely to get downgraded.
- Use `"general": true` (or omit `new_line`) for a positionless note — it gets folded into the pending review's own body text instead of an inline thread.
- Don't mark the comments yourself — the script appends a trailing 🤖 to each inline comment, and sets the review body to an attribution line for the review as a whole ("Code reviewed using Sonnet 5 (high) 🤖"), which is where GitHub shows a review's single non-inline comment.
- Pass `--model "<name>"` and optionally `--effort "<level>"`, same convention as the GitLab adapter.

2. Run the script:

```bash
python3 <skill_dir>/scripts/post_review_notes_github.py \
  --owner <owner> --repo <repo> --pr <number> --head-sha <headRefOid> \
  --notes /tmp/pr<number>_notes.json --model "<your model name>" [--effort "<level>"] --purge
```

3. Read the summary it prints: how many comments were posted inline, how many were folded into the review body (no valid anchor), and the review's URL.

**Why the script, and what it protects you from:**
- GitHub has **no endpoint to add a comment to an already-created pending review** — every inline comment must be supplied together in the one review-creation call, and one bad anchor fails the entire call. Validating locally against the fetched `patch` text before posting is the only reliable way to avoid losing the whole batch to a single bad line.
- `side: "RIGHT"` (new-file side) is set on every inline comment automatically — the script only ever anchors to added (`+`) lines, matching the GitLab adapter's own anchor policy, so behavior is consistent regardless of which host the change lives on.
- If the API call somehow still fails after local validation (e.g. a stale `head_sha`), the script retries with all comments folded into the review body rather than losing the review entirely.

## Submit instructions (Step 8)

A pending review has been created. Open the PR on GitHub, go to **Files changed → Review changes**, confirm the draft comments, then submit the review to publish it.

## Markup dialect (Step 6, when quoting a ticket in a comment)

GitHub-flavored Markdown. Fenced code blocks, headings, and `#`/`@` autolinks all render. Emoji shortcodes (`:robot:`) render.
