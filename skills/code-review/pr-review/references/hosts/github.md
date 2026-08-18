# Host adapter: GitHub

Mechanics for reviewing a GitHub pull request. Read this when Step 1 identifies the host as GitHub (URL shape `https://github.com/<owner>/<repo>/pull/<number>`).

**Status**: the read-side calls below (`gh pr view`, `gh api .../pulls/<n>/files`) were run live against a real repo/PR (v2.89.0, authenticated) and returned the fields documented here. The posting mechanics (comment creation, line validation, review events) follow the current GitHub REST API docs and are exercised by the bundled script's own test path, but weren't fired against a real PR, to avoid creating a live review as a side effect of writing this adapter — treat the happy path as reliable and the fallback paths (below) as the safety net for the rare case it isn't.

## Tooling

Use the `gh` CLI over Bash — no separate MCP connector needed once `gh auth status` shows you're logged in. If `gh` isn't installed or authenticated, fall back to the graceful-degradation path in Step 1 (discover MCP GitHub tools via `ToolSearch`), or ask the user to `gh auth login`.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,body,author,baseRefName,headRefName,baseRefOid,headRefOid,changedFiles,statusCheckRollup,url
```

Extract:
- `title`, `body` — scan both for a work-item reference (Step 3)
- `author.login` — compare against `gh api user`'s `login` to detect a self-authored PR (Step 2)
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

## Post the findings and act on the verdict (Step 6)

GitHub's review-creation call is **atomic**: if even one inline comment's `line`/`path` doesn't land on a line that's actually part of the diff, the whole call is rejected (HTTP 422) and *none* of the comments are created. It also **requires a `body`** for the `COMMENT` and `REQUEST_CHANGES` events. Those two facts are why the two modes use different endpoints, and why the mechanics live in a bundled script — **`scripts/post_review_notes_github.py`** (relative to the SKILL.md) — which fetches the PR's diff and validates every anchor locally before posting anything:

| Mode | How comments land | Verdict |
|---|---|---|
| `--mode direct` | one `POST .../pulls/<n>/comments` per anchored finding, one `POST .../issues/<n>/comments` per unanchored one — a bad anchor costs only that finding | one bodyless `POST .../pulls/<n>/reviews` with `event: APPROVE`, or with `event: REQUEST_CHANGES` plus the summary body GitHub demands |
| `--mode draft` (the script's own default) | one `PENDING` review holding every inline comment, unanchorable findings folded into its body — visible only to the user until they submit it | none |

1. Write findings to a JSON array — same shape as the GitLab adapter, so the note-drafting step doesn't change based on host:

```json
// ${TMPDIR:-/tmp}/pr<number>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the **new-file** line number (integer). Only lines that appear with a `+` prefix in the file's `patch` are valid anchors — the script checks this itself, but anchoring to a `+` line in the first place (same rule as the GitLab adapter) means it's very unlikely to get downgraded.
- Use `"general": true` (or omit `new_line`) for a finding with no line anchor.
- Leave the marking to the script: it appends a trailing 🤖 to each one, and that marker is how it recognizes its own work on a rerun.

2. Run the script for the mode this run is in:

```bash
# default mode — publish the comments, then approve
python3 <skill_dir>/scripts/post_review_notes_github.py \
  --owner <owner> --repo <repo> --pr <number> --head-sha <headRefOid> \
  --notes ${TMPDIR:-/tmp}/pr<number>_notes.json \
  --mode direct --verdict approve

# default mode, Request changes verdict — GitHub requires the body for this event
python3 ... --mode direct --verdict request-changes --summary-file ${TMPDIR:-/tmp}/pr<number>_summary.md

# comments-only mode — publish the comments, record no verdict
python3 ... --mode direct

# draft mode — one pending review for the user to submit
python3 ... --purge
```

3. Read the summary it prints: how many comments went inline, how many went to the conversation, which findings were skipped as already posted, and the verdict result. Carry the skipped list and the verdict result into Step 8's output.

**Approving**: GitHub rejects approving or requesting changes on your **own** PR (422, "Can not approve your own pull request"), which is why Step 2 compares `author.login` against `gh api user` and drops to comments-only mode when they match. The script reports the rejection rather than failing the run if it happens anyway.

**Why the script, and what it protects you from:**
- In draft mode, every inline comment must be supplied together in the one review-creation call, and one bad anchor fails the entire call. Validating locally against the fetched `patch` text before posting is the only reliable way to avoid losing the whole batch to a single bad line; if the call still fails, the script retries with every finding folded into the review body rather than losing the review.
- `side: "RIGHT"` (new-file side) is set on every inline comment automatically — the script only ever anchors to added (`+`) lines, matching the GitLab adapter's own anchor policy, so behavior is consistent regardless of which host the change lives on.
- In direct mode the script reads the PR's existing review and conversation comments first and skips a finding this account already published — matched by the same `path`/`line`, or by identical text anywhere on the PR. It never deletes a published comment, so a thread the author replied to stays intact.
- `--purge` applies to draft mode only, where the target is an unpublished pending review. It finds its own by the 🤖 marker in the review body *or* in any of its inline comments, so a pending review whose findings all anchored (leaving the body empty) is still recognized.

## Closing lines (Step 8)

- **Draft mode**: "A pending review has been created. Open the PR on GitHub, go to **Files changed → Review changes**, confirm the draft comments, then submit the review to publish it."
- **Approved**: name the PR and say how to reverse it — a later review supersedes an earlier one, so `gh pr review <number> --request-changes --body "<reason>"` overrides the approval. Dismissing it outright (`PUT .../reviews/<review_id>/dismissals`) needs dismissal permission on the branch, so don't offer that as the first option.
- **Request changes**: state that the comments and the summary are published and the PR is marked as requesting changes; `gh pr review <number> --approve` reverses it.

## Markup dialect (Step 6, when quoting a work item in a comment)

GitHub-flavored Markdown. Fenced code blocks, headings, and `#`/`@` autolinks all render. Emoji shortcodes (`:robot:`) render.
