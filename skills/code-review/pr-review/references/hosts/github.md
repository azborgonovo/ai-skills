# Host adapter: GitHub

Mechanics for the review of a GitHub pull request. The URL has the shape `https://github.com/<owner>/<repo>/pull/<number>`.

## Tooling

Use the `gh` CLI over Bash. When `gh` is absent or unauthenticated, ask the user to run `! gh auth login`, or fall back to the degradation path of Step 1, which discovers MCP GitHub tools through `ToolSearch`.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,body,author,baseRefName,headRefName,baseRefOid,headRefOid,changedFiles,statusCheckRollup,url
```

Extract these fields:
- `title` and `body`. Scan both for a work-item reference, which Step 3 needs.
- `author.login`. Compare it against the `login` from `gh api user`, to detect a self-authored PR.
- `baseRefName` and `headRefName`.
- `baseRefOid` and `headRefOid`. These are the equivalents of `base_sha` and `head_sha`, and inline comment positions use them.
- `statusCheckRollup`. This is the CI signal handed to review-changes.
- `url`, for the summary note.

## Fetch diffs (Step 4, diff-only fallback)

You need this call only when Step 4 cannot create a worktree.

```
gh api repos/<owner>/<repo>/pulls/<number>/files --paginate
```

Each element carries:
- `filename`, and `previous_filename` for a rename.
- `status`, which is `added`, `removed`, `modified`, or `renamed`.
- `patch`, which is the unified diff string that holds the hunks. **It is absent for a binary file, and for a file that GitHub considers too large to diff.** Treat such a file as diff-unavailable, and skip line-anchored comments on it.

**Truncation check**: `--paginate` handles the page size limit of GitHub. A very large PR can still hit the per-file diff cap of GitHub, where a file over roughly 3000 lines returns no `patch`. When that happens, note in the summary "diff unavailable for N large or binary files, reviewed by reading the file directly".

## Repo path shape (Step 4)

`<repo_path>` is `<owner>/<repo>`. For example, `https://github.com/acme/my-service` gives `acme/my-service`. This is a relative shape, and not an absolute location.

## Post the findings and act on the verdict (Step 6)

The review-creation call of GitHub is **atomic**. One inline comment with a `line` or `path` outside the diff fails the whole call. GitHub rejects it with HTTP 422. It then creates *none* of the comments. The call also **requires a `body`** for the `COMMENT` and `REQUEST_CHANGES` events. So the two modes use different endpoints, through the bundled script **`scripts/post_review_notes_github.py`**, relative to the SKILL.md. The script validates every anchor against the diff of the PR before it posts anything.

| Mode | How comments land | Verdict |
|---|---|---|
| `--mode direct` | one `POST .../pulls/<n>/comments` per anchored finding, and one `POST .../issues/<n>/comments` per unanchored one, so a bad anchor costs only that finding | one bodyless `POST .../pulls/<n>/reviews` with `event: APPROVE`, or with `event: REQUEST_CHANGES` plus the summary body that GitHub demands |
| `--mode draft` (the script's default) | one `PENDING` review that holds every inline comment, with unanchorable findings folded into its body, visible only to the user until they submit it | none |

1. Write the notes file of Step 6 to `${TMPDIR:-/tmp}/pr<number>_notes.json`.

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

**Approving**: GitHub rejects an approval or a request for changes on your **own** PR, with a 422 and the message "Can not approve your own pull request". If that happens despite the Step 2 check, the script reports it instead of failing the run.

**What the script handles for you:**
- In draft mode, if the review-creation call still fails, the script retries with every finding folded into the review body, instead of losing the review.
- The script sets `side: "RIGHT"`, which is the new-file side, on every inline comment.
- `--purge` applies to draft mode alone, where the target is an unpublished pending review. It finds its own review by the 🤖 marker in the review body *or* in any of its inline comments. So it still recognizes a pending review whose findings all anchored, and whose body is empty as a result.

## Suggested changes (Step 6)

GitHub renders a fenced `suggestion` block inside an inline review comment as a committable patch. The author clicks **Commit suggestion**, or adds several suggestions to a batch and commits them together. The fence matches the GitLab fence, without the offset syntax:

````
```suggestion
	status := record.Status
```
````

- The block replaces **the commented line**. Read it with `sed -n '<line>p' <worktree_path>/<file>`.
- The contents of the block can span several lines, so one line can expand into three. A replacement of more than one *existing* line needs the comment itself to span a line range, through `start_line` plus `line`. The bundled script does not send that range, because it anchors one line per comment. So a fix that rewrites a block of existing lines goes in prose instead.
- A finding that the script failed to anchor lands as a conversation comment, where the block renders as inert code. The script warns when that happens, and Step 8 reports the finding as posted without its suggestion.

## Closing lines (Step 8)

- **Draft mode**: "A pending review is ready. Open the PR on GitHub, go to **Files changed → Review changes**, confirm the draft comments, then submit the review to publish it."
- **Approved**: name the PR and say how to reverse the approval. A later review supersedes an earlier one, so `gh pr review <number> --request-changes --body "<reason>"` overrides it. An outright dismissal, through `PUT .../reviews/<review_id>/dismissals`, needs dismissal permission on the branch, so do not offer it as the first option.
- **Request changes**: state that the comments and the summary are published and that the PR is marked as requesting changes. `gh pr review <number> --approve` reverses that state.

## Markup dialect (Step 6, when a comment quotes a work item)

GitHub-flavored Markdown. Fenced code blocks, headings, and `#` and `@` autolinks all render. Emoji shortcodes such as `:robot:` render.
