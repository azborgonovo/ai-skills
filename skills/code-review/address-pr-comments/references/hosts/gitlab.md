# Host adapter: GitLab

Mechanics for addressing comments on a GitLab merge request. Read this when Step 1 identifies the host as GitLab (URL shape `https://<gitlab-host>/<group>/<subgroups>/<project>/-/merge_requests/<iid>`).

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

**If the first call fails with an auth error** (401, or a "not logged in" message), `glab` isn't authenticated. Stop and ask the user — don't pre-check auth separately, since the metadata call below surfaces it anyway:

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until auth is confirmed.

## Fetch change metadata (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

Extract `title`, `source_branch`, and `web_url` — the summary in Step 10 needs all three.

## List open threads (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions   (per_page: 100)
```

Paginate with the `page` param if the response's `X-Total-Pages` header shows more than one page.

Each element is a discussion with a `notes` array (one per comment in the thread, oldest first). Keep only discussions where the first note has `"resolvable": true` and `"resolved": false` — those are the open threads. For each one, capture:
- `id` — the discussion ID, needed to reply and resolve
- `notes[].body`, `notes[].author` — the full exchange, for classification in Step 4
- `notes[0].position.new_path`, `notes[0].position.new_line` — when present, the inline anchor; absent means it's a general discussion

## Repo path shape (Step 3)

`<repo_path>` mirrors the GitLab namespace: `<group>/<subgroups>/<project>`. For example, `https://gitlab.com/acme/platform/my-service` → `acme/platform/my-service`. This is a relative shape, not an absolute location — GitLab imposes no fixed clone root, so Step 3 searches for it rather than assuming one.

## Reply and resolve (Step 8)

**Reply** — a true threaded reply, posted as a new note inside the existing discussion:

```
POST projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions/<discussion_id>/notes
Body: { "body": "<reply text>" }
```

**Resolve**:

```
PUT projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions/<discussion_id>
Body: { "resolved": true }
```

Resolving requires Developer role or above on the project. If this call comes back 403, the reply above still posted fine — note in the summary that the thread needs resolving by hand due to insufficient permissions.

## Markup dialect

GitLab-flavored Markdown. Fenced code blocks, headings, and links render. Emoji shortcodes (`:robot:`) render.
