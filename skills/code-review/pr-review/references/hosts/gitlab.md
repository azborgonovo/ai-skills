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
- `title`, `description` — scan both for a ticket reference (Step 3)
- `source_branch`, `target_branch`
- `diff_refs.base_sha`, `diff_refs.start_sha`, `diff_refs.head_sha` — needed for inline comment positions
- `web_url` — for the summary note

## Fetch diffs (Step 4)

Use `limit: 150000` to avoid truncation on large MRs:

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/changes   (limit: 150000)
```

The response is the full MR object with an additional `changes` array. Each element has:
- `new_path`, `old_path`
- `diff` — unified diff string (the hunks)
- `new_file`, `deleted_file`, `renamed_file` booleans

**Truncation check**: compare `response.changes.length` with `mr.changes_count` from the metadata call. If they differ, the diff is truncated — note "diff truncated — only N of M files reviewed" in the summary and prioritize the highest-risk files (auth, data access, public API surface).

## Repo path shape (Step 5)

`<repo_path>` mirrors the GitLab namespace: `<group>/<subgroups>/<project>`. For example, `https://gitlab.com/acme/platform/my-service` → `acme/platform/my-service`. This is a relative shape, not an absolute location — GitLab imposes no fixed clone root, so Step 5 searches for it rather than assuming one.

## Post comments as draft notes (Step 7)

Post each finding as a **draft note** — only you can see them until the user submits the review in the GitLab UI, so they can edit or remove comments before they go live.

The mechanics of posting are deterministic and easy to get subtly wrong, so they live in a bundled script: **`scripts/post_review_notes_gitlab.py`** (relative to the SKILL.md). It posts an arbitrary number of notes, verifies each one anchored to the diff, and falls back gracefully when it can't.

1. Write findings to a JSON array — one object per finding:

```json
// /tmp/mr<iid>_notes.json
[
  { "note": "<observation>\n\n<suggested fix if applicable>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

- `new_line` is the **new-file** line number (integer). `old_path` defaults to `new_path` — set it explicitly only for renamed files (use the pre-rename path).
- Use `"general": true` (or simply omit `new_line`) for a positionless note that publishes as a general discussion comment.
- Don't mark the notes yourself — the script appends a trailing 🤖 to each one, and posts one extra positionless note attributing the review as a whole ("Code reviewed using Sonnet 5 (high) 🤖").
- Pass `--model "<name>"` (e.g. `"Sonnet 5"`) so that attribution note names the reviewing model — you always know your own model name from your environment context, so always pass this. Add `--effort "<level>"` only when you have a concrete, known effort/thinking-level setting for this session to report — never guess one just to fill the field.

2. Run the script (it reads `diff_refs` from the metadata call and purges this skill's own prior drafts so reruns don't duplicate):

```bash
python3 <skill_dir>/scripts/post_review_notes_gitlab.py \
  --project <project_path_encoded> --mr <mr_iid> \
  --base-sha <diff_refs.base_sha> --start-sha <diff_refs.start_sha> --head-sha <diff_refs.head_sha> \
  --notes /tmp/mr<iid>_notes.json --model "<your model name>" [--effort "<level>"] --purge
```

3. Read the per-note summary it prints. Each line reports `resolved=True/False` or `general=True`; the attribution note is reported first, on its own line.

**Why the script, and what it protects you from:**
- GitLab **always returns HTTP 200** for `draft_notes`, even when it can't resolve the position. The real indicator is the `line_code` field in the response — GitLab only populates it when the position actually anchored to the diff. An unresolvable draft (`line_code` null) silently never publishes as an inline comment. The script detects this, deletes the draft, and re-posts it positionless so the finding is never lost — it just lands as a general discussion comment instead.
- `old_path` is required for inline placement; omitting it silently downgrades to a plain note. The script always sends it.
- **Prefer `+` lines as anchors**: pick a `new_line` that appears with a `+` prefix in the diff (added in this MR) — GitLab resolves those reliably. **Context lines (unchanged lines) are unreliable anchors even when they appear inside the hunk** — GitLab often fails to set `line_code` for them. If your finding is on an unchanged line, anchor to the nearest `+` line nearby, or mark it `general` from the start.

## Submit instructions (Step 9)

Draft comments have been posted. Open the MR in GitLab, review the inline notes, then hit **Submit review** to publish.

## Markup dialect (Step 4 tracker-note cross-reference)

GitLab-flavored Markdown. Fenced code blocks, headings, and links render. Emoji shortcodes (`:robot:`) render.
