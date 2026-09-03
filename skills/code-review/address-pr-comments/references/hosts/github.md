# Host adapter: GitHub

Mechanics for addressing comments on a GitHub pull request. Read this file when Step 1 identifies the host as GitHub. The URL has the shape `https://github.com/<owner>/<repo>/pull/<number>`.

## Tooling

Use the `gh` CLI over Bash. No separate MCP connector is needed once `gh auth status` shows that you are logged in. When `gh` is absent or unauthenticated, fall back to the graceful-degradation path in Step 1, which discovers MCP GitHub tools through `ToolSearch`. You can also ask the user to run `gh auth login`.

Listing and resolving threads needs GraphQL. The REST API of GitHub exposes neither the resolved state of a review thread nor a resolve action. Replying uses REST instead, because that is the endpoint that exists for it.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,headRefName,url
```

Extract `title`, `headRefName`, which is the source branch, and `url`. The summary in Step 10 needs all three.

## List open threads (Step 2)

```
gh api graphql -f query='
  query($owner: String!, $repo: String!, $number: Int!, $cursor: String) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $number) {
        reviewThreads(first: 100, after: $cursor) {
          pageInfo { hasNextPage endCursor }
          nodes {
            id
            isResolved
            comments(first: 100) {
              nodes { databaseId body path line author { login } }
            }
          }
        }
      }
    }
  }' -F owner=<owner> -F repo=<repo> -F number=<number>
```

Follow `pageInfo.hasNextPage` and `endCursor` when the PR carries more than 100 threads. Keep only the nodes where `isResolved` is `false`. For each one, capture:
- `id`, which is the GraphQL node ID of the thread, and which you need to resolve it.
- `comments.nodes[0].databaseId`, which is the REST ID of the root comment, and which you need to reply.
- `comments.nodes[].body` and `comments.nodes[].author.login`, which give the full exchange for the classification in Step 4.
- `comments.nodes[0].path` and `comments.nodes[0].line`, which give the inline anchor when they are present. When they are absent, the thread is a general PR-level thread.

## Repo path shape (Step 3)

`<repo_path>` is `<owner>/<repo>`, because GitHub has no nested subgroup concept, unlike GitLab. For example, `https://github.com/acme/my-service` gives `acme/my-service`. This is a relative shape, not an absolute location, so Step 3 searches for the clone instead of assuming a fixed clone root.

## Reply and resolve (Step 8)

**Reply**: post a true threaded reply, against the root comment of the thread. `comment_id` must be that top-level comment, and never a reply inside the thread, because GitHub does not support a reply to a reply. That is exactly why Step 2 captures `comments.nodes[0].databaseId` and not the last one:

```bash
gh api repos/<owner>/<repo>/pulls/<number>/comments/<root_databaseId>/replies -f body='<reply text>'
```

**Resolve**:

```
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: { threadId: $threadId }) { thread { id isResolved } }
  }' -F threadId=<thread_id>
```

Resolving a conversation requires write access to the repo. When this call fails with a permission error, the reply above still posted correctly. Note in the summary that the thread needs a resolve by hand.

## Markup dialect

GitHub-flavored Markdown. Fenced code blocks, headings, and `#` and `@` autolinks all render. Emoji shortcodes such as `:robot:` render.
