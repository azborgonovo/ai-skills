# Host adapter: GitHub

Mechanics for the review of a GitHub pull request. Read this file when Step 1 identifies the host as GitHub. The URL has the shape `https://github.com/<owner>/<repo>/pull/<number>`.

**Status**: the read calls below are `gh pr view` and `gh api .../pulls/<n>/files`. Both ran live against a real repo and PR, on version 2.89.0, authenticated. Both returned the fields documented here. The posting mechanics are comment creation, line validation, and review events. They follow the current GitHub REST API documentation, and the test path of the bundled script exercises them. They were never fired against a real PR, to prevent a live review as a side effect of writing this adapter. Treat the happy path as reliable, and treat the fallback paths below as the safety net for the rare case where it is not.

## Tooling

Use the `gh` CLI over Bash. No separate MCP connector is needed once `gh auth status` shows that you are logged in. When `gh` is absent or unauthenticated, fall back to the graceful-degradation path in Step 1, which discovers MCP GitHub tools through `ToolSearch`. You can also ask the user to run `gh auth login`.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,body,author,baseRefName,headRefName,baseRefOid,headRefOid,changedFiles,statusCheckRollup,url
```

Extract these fields:
- `title` and `body`. Scan both for a work-item reference, which Step 3 needs.
- `author.login`. Compare it against the `login` from `gh api user`, to detect a self-authored PR in Step 2.
- `baseRefName` and `headRefName`.
- `baseRefOid` and `headRefOid`. These are the equivalents of `base_sha` and `head_sha`, and inline comment positions use them.
- `statusCheckRollup`. This is the CI signal handed to review-changes. The review then reports the test status from the checks of GitHub, instead of building the PR locally.
- `url`, for the summary note.

## Fetch diffs (Step 4, diff-only fallback)

You need this call only when Step 4 cannot create a worktree. With a worktree, the review reads the diff from git, which has neither the per-file cap of GitHub nor its pagination to work around.

```
gh api repos/<owner>/<repo>/pulls/<number>/files --paginate
```

Each element carries:
- `filename`, and `previous_filename` for a rename.
- `status`, which is `added`, `removed`, `modified`, or `renamed`.
- `patch`, which is the unified diff string that holds the hunks. **It is absent for a binary file, and for a file that GitHub considers too large to diff.** Treat such a file as diff-unavailable, and skip line-anchored comments on it.

**Truncation check**: `--paginate` handles the page size limit of GitHub. A very large PR can still hit the per-file diff cap of GitHub, where a file over roughly 3000 lines returns no `patch`. When that happens, note in the summary "diff unavailable for N large or binary files, reviewed by reading the file directly". Then prioritize the files with the highest risk, which are auth, data access, and the public API surface.

## Repo path shape (Step 4)

`<repo_path>` is `<owner>/<repo>`, because GitHub has no nested subgroup concept, unlike GitLab. For example, `https://github.com/acme/my-service` gives `acme/my-service`. This is a relative shape, and not an absolute location. So the script in Step 4 searches for the clone, instead of assuming a fixed clone root.

## Post the findings and act on the verdict (Step 6)

The review-creation call of GitHub is **atomic**. One inline comment with a `line` or `path` outside the diff fails the whole call. GitHub rejects it with HTTP 422. It then creates *none* of the comments. The call also **requires a `body`** for the `COMMENT` and `REQUEST_CHANGES` events. Those two facts are why the two modes use different endpoints, and why the mechanics live in a bundled script: **`scripts/post_review_notes_github.py`**, relative to the SKILL.md. The script fetches the diff of the PR and validates every anchor locally before it posts anything.

| Mode | How comments land | Verdict |
|---|---|---|
| `--mode direct` | one `POST .../pulls/<n>/comments` per anchored finding, and one `POST .../issues/<n>/comments` per unanchored one, so a bad anchor costs only that finding | one bodyless `POST .../pulls/<n>/reviews` with `event: APPROVE`, or with `event: REQUEST_CHANGES` plus the summary body that GitHub demands |
| `--mode draft` (the script's default) | one `PENDING` review that holds every inline comment, with unanchorable findings folded into its body, visible only to the user until they submit it | none |

1. Write the findings to a JSON array. The shape matches the GitLab adapter, so the note-drafting step does not change with the host:

```json
// ${TMPDIR:-/tmp}/pr<number>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the line number in the **new file**, as an integer. Only a line that appears with a `+` prefix in the `patch` of the file is a valid anchor. The script checks this itself, and an anchor placed on a `+` line from the start is very unlikely to get downgraded. This is the same rule as the GitLab adapter.
- Use `"general": true`, or omit `new_line`, for a finding with no line anchor.
- Leave the marking to the script. It appends a trailing 🤖 to each note, and that marker is how it recognizes its own work on a rerun.

2. Run the script for the mode of this run:

```bash
# default mode: publish the comments, then approve
python3 <skill_dir>/scripts/post_review_notes_github.py \
  --owner <owner> --repo <repo> --pr <number> --head-sha <headRefOid> \
  --notes ${TMPDIR:-/tmp}/pr<number>_notes.json \
  --mode direct --verdict approve

# default mode with a Request changes verdict: GitHub requires the body for this event
python3 ... --mode direct --verdict request-changes --summary-file ${TMPDIR:-/tmp}/pr<number>_summary.md

# comments-only mode: publish the comments, record no verdict
python3 ... --mode direct

# draft mode: one pending review for the user to submit
python3 ... --purge
```

3. Read the summary that the script prints. It reports how many comments went inline, how many went to the conversation, which findings it skipped as already posted, and the verdict result. Carry the skipped list and the verdict result into the Step 8 output.

**Approving**: GitHub rejects an approval or a request for changes on your **own** PR. It returns a 422 with the message "Can not approve your own pull request". That is why Step 2 compares `author.login` against `gh api user` and drops to comments-only mode on a match. If the rejection happens anyway, the script reports it instead of failing the run.

**Why the script, and what it protects you from:**
- In draft mode, every inline comment must arrive together in the one review-creation call, and one bad anchor fails the entire call. Local validation against the fetched `patch` text, before anything is posted, is the only reliable way to keep the whole batch. If the call still fails, the script retries with every finding folded into the review body, instead of losing the review.
- The script sets `side: "RIGHT"`, which is the new-file side, on every inline comment. It only ever anchors to added `+` lines, which matches the anchor policy of the GitLab adapter. So the behavior stays the same whatever host holds the change.
- In direct mode, the script first reads the existing review comments and conversation comments of the PR. It then skips a finding that this account already published. It matches on the same `path` and `line`, or on identical text anywhere on the PR. It never deletes a published comment, so a thread that the author replied to stays intact.
- `--purge` applies to draft mode alone, where the target is an unpublished pending review. It finds its own review by the 🤖 marker in the review body *or* in any of its inline comments. So it still recognizes a pending review whose findings all anchored, and whose body is empty as a result.

## Suggested changes (Step 6)

GitHub renders a fenced `suggestion` block inside an inline review comment as a committable patch. The author clicks **Commit suggestion**, or adds several suggestions to a batch and commits them together. The fence matches the GitLab fence, without the offset syntax:

````
```suggestion
	status := record.Status
```
````

- The block replaces **the commented line, whole**. Keep the full original indentation, and add no leading `+`. Read the exact current text out of the worktree with `sed -n '<line>p' <worktree_path>/<file>`. Do not reconstruct it from the diff.
- The contents of the block can span several lines, so one line can expand into three. A replacement of more than one *existing* line needs the comment itself to span a line range, through `start_line` plus `line`. The bundled script does not send that range, because it anchors one line per comment. So a fix that rewrites a block of existing lines goes in prose instead.
- Only an inline review comment can carry a suggestion block. A finding that the script failed to anchor lands as a conversation comment, where the block renders as inert code. The script warns when that happens, and Step 8 reports the finding as posted without its suggestion.

## Closing lines (Step 8)

- **Draft mode**: "A pending review is ready. Open the PR on GitHub, go to **Files changed → Review changes**, confirm the draft comments, then submit the review to publish it."
- **Approved**: name the PR and say how to reverse the approval. A later review supersedes an earlier one, so `gh pr review <number> --request-changes --body "<reason>"` overrides it. An outright dismissal, through `PUT .../reviews/<review_id>/dismissals`, needs dismissal permission on the branch, so do not offer it as the first option.
- **Request changes**: state that the comments and the summary are published and that the PR is marked as requesting changes. `gh pr review <number> --approve` reverses that state.

## Markup dialect (Step 6, when a comment quotes a work item)

GitHub-flavored Markdown. Fenced code blocks, headings, and `#` and `@` autolinks all render. Emoji shortcodes such as `:robot:` render.
