# Host adapter: GitLab

Mechanics for the review of a GitLab merge request. The URL has the shape `https://<gitlab-host>/<group>/<subgroups>/<project>/-/merge_requests/<iid>`.

## Parse the URL

Extract three values from the URL:
- `project_path`: everything between the host and `/-/merge_requests/`, for example `acme/platform/my-service`.
- `project_path_encoded`: the same path with each `/` encoded as `%2F`, which gives `acme%2Fplatform%2Fmy-service`.
- `mr_iid`: the MR number.

## Tooling

`mcp__glab__glab_api` is a deferred tool, so load its schema first:

```
ToolSearch: select:mcp__glab__glab_api
```

**If the first call fails with an auth error**, ask the user with this text:

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until the user confirms auth.

## Fetch change metadata (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

Extract these fields:
- `title` and `description`. Scan both for a work-item reference, which Step 3 needs.
- `author.username`. Compare it against the `username` from `glab api user`, to detect a self-authored MR in Step 2.
- `source_branch` and `target_branch`.
- `diff_refs.base_sha`, `diff_refs.start_sha`, and `diff_refs.head_sha`. Inline comment positions need all three.
- `head_pipeline.status`, or `pipeline.status`. This is the CI signal handed to review-changes.
- `web_url`, for the summary note.

## Fetch diffs (Step 4, diff-only fallback)

You need this call only when Step 4 cannot create a worktree. Use `limit: 150000` to prevent truncation on a large MR:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/changes   (limit: 150000)
```

The response is the full MR object plus a `changes` array. Each element carries:
- `new_path` and `old_path`.
- `diff`, which is the unified diff string that holds the hunks.
- The `new_file`, `deleted_file`, and `renamed_file` booleans.

**Truncation check**: compare `response.changes.length` against `mr.changes_count` from the metadata call. If the two differ, the diff is truncated. Note "diff truncated, only N of M files reviewed" in the summary.

## Repo path shape (Step 4)

`<repo_path>` mirrors the GitLab namespace, so it takes the shape `<group>/<subgroups>/<project>`. For example, `https://gitlab.com/acme/platform/my-service` gives `acme/platform/my-service`. This is a relative shape, not an absolute location.

## Post the findings and act on the verdict (Step 6)

The bundled script **`scripts/post_review_notes_gitlab.py`**, relative to the SKILL.md, posts the notes. It confirms that each one anchored to the diff, and it re-posts a note that cannot anchor as a general discussion comment.

1. Write the notes file of Step 6 to `${TMPDIR:-/tmp}/mr<iid>_notes.json`. `old_path` defaults to `new_path`. Set `old_path` explicitly only for a renamed file, and use the pre-rename path.

2. Run the script for the mode of this run. `--mode direct` publishes every note that this run created, and `--verdict` then acts on the MR:

```bash
# default mode: publish the comments, then approve
python3 <skill_dir>/scripts/post_review_notes_gitlab.py \
  --project <project_path_encoded> --mr <mr_iid> \
  --base-sha <diff_refs.base_sha> --start-sha <diff_refs.start_sha> --head-sha <diff_refs.head_sha> \
  --notes ${TMPDIR:-/tmp}/mr<iid>_notes.json --purge \
  --mode direct --verdict approve

# default mode with a Request changes verdict: GitLab carries the summary as a note
python3 ... --mode direct --verdict request-changes --summary-file ${TMPDIR:-/tmp}/mr<iid>_summary.md

# comments-only mode: publish the comments, leave the approval state alone
python3 ... --mode direct

# draft mode: leave everything as drafts for the user to submit
python3 ...
```

3. Read the per-note summary that the script prints. Each line reports `resolved=True/False` or `general=True`. The script then prints a `posted:` and `skipped:` tally, plus the verdict result. Carry the skipped list and the verdict result into the Step 8 output.

**Approving**: the script calls `POST .../approve` with `sha=<head_sha>`. GitLab returns **409** and refuses when the author pushed while the review was running. That refusal is the right outcome, because the review no longer describes the head. Report it, and do not retry against the new head without a new review.

**Requesting changes**: GitLab exposes **no API** for a reviewer's `requested_changes` state, on REST or on GraphQL. The state is readable and not settable. The script does what it can instead. It calls `POST .../unapprove` to clear any approval that this account holds, and then it posts the summary as a note. Tell the user in the Step 8 output that the merge-blocking reviewer state itself needs a click in the UI.

**What the script handles for you:**
- GitLab **always returns HTTP 200** for `draft_notes`, even when it cannot resolve the position. Only a non-null `line_code` in the response proves that the note anchored. The script checks it, and it re-posts an unanchored draft with no position.
- **Never call `draft_notes/bulk_publish`.** That endpoint publishes every pending draft that the authenticated user holds on the MR, including drafts they wrote by hand. The script publishes one draft at a time, through `PUT .../draft_notes/<id>/publish`.
- **A context line, which is an unchanged line, is an unreliable anchor even inside the hunk**, because GitLab often leaves its `line_code` null. That is why Step 6 anchors only to `+` lines.

## Suggested changes (Step 6)

GitLab renders a fenced `suggestion` block inside a **diff note** as an applicable patch. The author clicks **Apply suggestion**, and GitLab commits it.

````
```suggestion:-0+0
        Status = record.GetEnum<OrgSetupStatus>("statusId"),
```
````

- The offsets extend the replaced range around the anchored line. `-0+0` is the default, and a bare ` ```suggestion ` means the same thing: that line alone. `-2+1` replaces the two lines above, the line itself, and the line below. GitLab caps the range at 100 lines above and 100 lines below. The contents of the block can run to any number of lines, so a replacement of one line with three needs no offsets.
- Read the replaced lines with `sed -n '<start>,<end>p' <worktree_path>/<file>`.
- A note that the script re-posted with no position carries its block as inert code. The script warns on that line of its tally, and Step 8 reports the finding as posted without its suggestion.
- One note can carry several blocks, and the author can add each one to a batch and apply them in a single commit.

## Closing lines (Step 8)

- **Draft mode**: "The draft comments are posted. Open the MR in GitLab, review the inline notes, then hit **Submit review** to publish."
- **Approved**: name the MR and give the revoke command, which is `glab mr revoke <mr_iid>`, or `POST .../unapprove`.
- **Request changes**: state that the comments and the summary are published, and that this account cleared its own approval. State that GitLab has no API for the `requested_changes` reviewer state. Setting that state means opening the MR and choosing **Request changes**.

## Markup dialect (Step 6, when a comment quotes a work item)

GitLab-flavored Markdown. Fenced code blocks, headings, and links render. Emoji shortcodes such as `:robot:` render.
