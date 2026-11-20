# Host adapter: GitLab

Mechanics for addressing comments on a GitLab merge request. The URL has the shape `https://<gitlab-host>/<group>/<subgroups>/<project>/-/merge_requests/<iid>`.

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

Do not pre-check auth, because the metadata call surfaces an auth error anyway. On an auth error, ask with this text, and wait until the user confirms:

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

## Fetch change metadata (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

Extract `title`, `source_branch`, and `web_url`.

## List open threads (Step 2)

```
mcp__glab__glab_api
  args:  ["projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions?per_page=100"]
  flags: { "paginate": true, "output": "ndjson" }
```

Always pass `"output": "ndjson"` on this call. With the default `json` output, the `glab` MCP server returns the array as structured content, and Claude Code rejects it with `expected record, received array`. The `ndjson` output gives one discussion per line.

Each line is a discussion with a `notes` array, which holds one entry per comment in the thread, oldest first. Keep only the discussions where the first note has `"resolvable": true` and `"resolved": false`, because those are the open threads. For each one, capture:
- `id`, which is the discussion ID, and which you need to reply and to resolve.
- `notes[].body` and `notes[].author`, which give the full exchange.
- `notes[0].position.new_path` and `notes[0].position.new_line`, which give the inline anchor when they are present.

## Repo path shape (Step 3)

`<repo_path>` mirrors the GitLab namespace, `<group>/<subgroups>/<project>`. For example, `https://gitlab.com/acme/platform/my-service` gives `acme/platform/my-service`.

## Reply and resolve (Step 8)

**Reply** as a new note inside the existing discussion:

```
POST projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions/<discussion_id>/notes
Body: { "body": "<reply text>" }
```

**Resolve**:

```
PUT projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions/<discussion_id>
Body: { "resolved": true }
```

Resolving requires the Developer role or above on the project. A missing role returns 403.

## Markup dialect

GitLab-flavored Markdown. Fenced code blocks, headings, and links render.
