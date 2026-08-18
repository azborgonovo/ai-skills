# Host adapter: GitLab

Mechanics for reviewing a GitLab merge request. Read this when Step 1 identifies the host as GitLab (URL shape `https://<gitlab-host>/<group>/<subgroups>/<project>/-/merge_requests/<iid>`).

## Parse the URL

From the URL extract:
- `project_path`: everything between the host and `/-/merge_requests/`, e.g. `acme/platform/my-service`
- `project_path_encoded`: URL-encode `/` as `%2F` → `acme%2Fplatform%2Fmy-service`
- `mr_iid`: the MR number

## Tooling

`mcp__glab__glab_api` is a deferred tool — load its schema first:

```
ToolSearch: select:mcp__glab__glab_api
```

**If the first call fails with an auth error** (401, or a "not logged in" message), `glab` isn't authenticated. Stop and ask the user — don't pre-check auth separately, since the metadata call below surfaces it anyway, and a success there proves auth is good for posting later too (same credentials):

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until auth is confirmed.

## Fetch change metadata (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

Extract:
- `title`, `description` — scan both for a work-item reference (Step 3)
- `author.username` — compare against `glab api user`'s `username` to detect a self-authored MR (Step 2)
- `source_branch`, `target_branch`
- `diff_refs.base_sha`, `diff_refs.start_sha`, `diff_refs.head_sha` — needed for inline comment positions
- `head_pipeline.status` (or `pipeline.status`) — the CI signal handed to review-changes, so the review reports test status from GitLab's own run rather than building the MR locally
- `web_url` — for the summary note

## Fetch diffs (Step 4, diff-only fallback)

Only needed when Step 4 can't create a worktree — with one, the review reads the diff from git in the worktree, which has no size cap to work around. Use `limit: 150000` to avoid truncation on large MRs:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/changes   (limit: 150000)
```

The response is the full MR object with an additional `changes` array. Each element has:
- `new_path`, `old_path`
- `diff` — unified diff string (the hunks)
- `new_file`, `deleted_file`, `renamed_file` booleans

**Truncation check**: compare `response.changes.length` with `mr.changes_count` from the metadata call. If they differ, the diff is truncated — note "diff truncated — only N of M files reviewed" in the summary and prioritize the highest-risk files (auth, data access, public API surface).

## Repo path shape (Step 4)

`<repo_path>` mirrors the GitLab namespace: `<group>/<subgroups>/<project>`. For example, `https://gitlab.com/acme/platform/my-service` → `acme/platform/my-service`. This is a relative shape, not an absolute location — GitLab imposes no fixed clone root, so Step 4's script searches for it rather than assuming one.

## Post the findings and act on the verdict (Step 6)

The mechanics of posting are deterministic and easy to get subtly wrong, so they live in a bundled script: **`scripts/post_review_notes_gitlab.py`** (relative to the SKILL.md). It posts an arbitrary number of notes, verifies each one anchored to the diff, falls back gracefully when it can't, and — in the default mode — publishes them and applies the verdict.

1. Write findings to a JSON array — one object per finding:

```json
// /tmp/mr<iid>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the **new-file** line number (integer). `old_path` defaults to `new_path` — set it explicitly only for renamed files (use the pre-rename path).
- Use `"general": true` (or simply omit `new_line`) for a positionless note, which lands as a general discussion comment.
- Leave the marking to the script: it appends a trailing 🤖 to each one, and that marker is how it recognizes its own work on a rerun.

2. Run the script for the mode this run is in. `--mode direct` publishes every note this run created; `--verdict` then acts on the MR:

```bash
# default mode — publish the comments, then approve
python3 <skill_dir>/scripts/post_review_notes_gitlab.py \
  --project <project_path_encoded> --mr <mr_iid> \
  --base-sha <diff_refs.base_sha> --start-sha <diff_refs.start_sha> --head-sha <diff_refs.head_sha> \
  --notes /tmp/mr<iid>_notes.json --purge \
  --mode direct --verdict approve

# default mode, Request changes verdict — needs the summary GitLab will carry as a note
python3 ... --mode direct --verdict request-changes --summary-file /tmp/mr<iid>_summary.md

# comments-only mode — publish the comments, leave approval state alone
python3 ... --mode direct

# draft mode — leave everything as drafts for the user to submit
python3 ...
```

3. Read the per-note summary it prints: each line reports `resolved=True/False` or `general=True`, then a `posted:`/`skipped:` tally and the verdict result. Carry the skipped list and the verdict result into Step 8's output.

**Approving**: the script calls `POST .../approve` with `sha=<head_sha>`, so GitLab returns **409** and refuses if the author pushed while the review was running. That's the right outcome — the review no longer describes the head — so report it and don't retry against the new head without re-reviewing.

**Requesting changes**: GitLab exposes **no API** for a reviewer's `requested_changes` state, on REST or GraphQL — the state is readable but not settable. The script does what it can instead: `POST .../unapprove` to clear any approval this account already holds, then posts the summary as a note. Tell the user in Step 8's output that the merge-blocking reviewer state itself needs a click in the UI.

**Why the script, and what it protects you from:**
- GitLab **always returns HTTP 200** for `draft_notes`, even when it can't resolve the position. The real indicator is the `line_code` field in the response — GitLab only populates it when the position actually anchored to the diff. An unresolvable draft (`line_code` null) silently never publishes as an inline comment. The script detects this, deletes the draft, and re-posts it positionless so the finding is never lost — it just lands as a general discussion comment instead.
- `old_path` is required for inline placement; omitting it silently downgrades to a plain note. The script always sends it.
- Publishing goes one draft at a time (`PUT .../draft_notes/<id>/publish`), never through `draft_notes/bulk_publish` — **that endpoint publishes every pending draft the authenticated user has on the MR**, including ones they wrote by hand and hadn't submitted.
- In direct mode the script reads the MR's existing discussions first and skips a finding this account already published — matched by the same `new_path`/`new_line`, or by identical text anywhere on the MR. It never deletes a published comment, so a thread the author replied to stays intact.
- **Prefer `+` lines as anchors**: pick a `new_line` that appears with a `+` prefix in the diff (added in this MR) — GitLab resolves those reliably. **Context lines (unchanged lines) are unreliable anchors even when they appear inside the hunk** — GitLab often fails to set `line_code` for them. If your finding is on an unchanged line, anchor to the nearest `+` line nearby, or mark it `general` from the start.

## Closing lines (Step 8)

- **Draft mode**: "Draft comments have been posted. Open the MR in GitLab, review the inline notes, then hit **Submit review** to publish."
- **Approved**: name the MR and give the revoke command — `glab mr revoke <mr_iid>` (or `POST .../unapprove`).
- **Request changes**: state that the comments and summary are published, that this account's approval was cleared, and that GitLab has no API for the `requested_changes` reviewer state — so setting it means opening the MR and choosing **Request changes**.

## Markup dialect (Step 6, when quoting a work item in a comment)

GitLab-flavored Markdown. Fenced code blocks, headings, and links render. Emoji shortcodes (`:robot:`) render.
