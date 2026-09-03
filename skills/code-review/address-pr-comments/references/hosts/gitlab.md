# Host adapter: GitLab

Mechanics for addressing comments on a GitLab merge request. Read this file when Step 1 identifies the host as GitLab. The URL has the shape `https://<gitlab-host>/<group>/<subgroups>/<project>/-/merge_requests/<iid>`.

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

**If the first call fails with an auth error**, which is a 401 or a "not logged in" message, then `glab` is not authenticated. Stop and ask the user. Do not pre-check auth separately, because the metadata call below surfaces the problem anyway. Ask with this text:

> `glab` is not authenticated. Please run `! glab auth login` in the prompt and complete the login flow, then let me know when done.

Do not proceed until the user confirms auth.

## Fetch change metadata (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>
```

Extract `title`, `source_branch`, and `web_url`. The summary in Step 10 needs all three.

## List open threads (Step 2)

```
GET projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions   (per_page: 100)
```

Paginate with the `page` parameter when the `X-Total-Pages` header of the response shows more than one page.

Each element is a discussion with a `notes` array, which holds one entry per comment in the thread, oldest first. Keep only the discussions where the first note has `"resolvable": true` and `"resolved": false`, because those are the open threads. For each one, capture:
- `id`, which is the discussion ID, and which you need to reply and to resolve.
- `notes[].body` and `notes[].author`, which give the full exchange for the classification in Step 4.
- `notes[0].position.new_path` and `notes[0].position.new_line`, which give the inline anchor when they are present. When they are absent, the thread is a general discussion.

## Repo path shape (Step 3)

`<repo_path>` mirrors the GitLab namespace, so it takes the shape `<group>/<subgroups>/<project>`. For example, `https://gitlab.com/acme/platform/my-service` gives `acme/platform/my-service`. This is a relative shape, not an absolute location. GitLab imposes no fixed clone root, so Step 3 searches for the clone instead of assuming one.

## Reply and resolve (Step 8)

**Reply**: post a true threaded reply, as a new note inside the existing discussion:

```
POST projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions/<discussion_id>/notes
Body: { "body": "<reply text>" }
```

**Resolve**:

```
PUT projects/<project_path_encoded>/merge_requests/<mr_iid>/discussions/<discussion_id>
Body: { "resolved": true }
```

Resolving requires the Developer role or above on the project. When this call returns 403, the reply above still posted correctly. Note in the summary that permissions are insufficient and that the thread needs a resolve by hand.

## Markup dialect

GitLab-flavored Markdown. Fenced code blocks, headings, and links render. Emoji shortcodes such as `:robot:` render.
