# Host adapter: GitHub

Mechanics for addressing comments on a GitHub pull request. Read this when Step 1 identifies the host as GitHub (URL shape `https://github.com/<owner>/<repo>/pull/<number>`).

## Tooling

Use the `gh` CLI over Bash — no separate MCP connector needed once `gh auth status` shows you're logged in. If `gh` isn't installed or authenticated, fall back to the graceful-degradation path in Step 1 (discover MCP GitHub tools via `ToolSearch`), or ask the user to `gh auth login`.

Listing and resolving threads needs GraphQL — GitHub's REST API has no endpoint that exposes a review thread's resolved state or a resolve action. Replying uses REST instead, since that's the endpoint that exists for it.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,headRefName,url
```

Extract `title`, `headRefName` (the source branch), and `url` — the summary in Step 10 needs all three.

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

Follow `pageInfo.hasNextPage`/`endCursor` if there are more than 100 threads. Keep only nodes where `isResolved` is `false`. For each one, capture:
- `id` — the thread's GraphQL node ID, needed to resolve it
- `comments.nodes[0].databaseId` — the root comment's REST ID, needed to reply
- `comments.nodes[].body`, `comments.nodes[].author.login` — the full exchange, for classification in Step 4
- `comments.nodes[0].path`, `comments.nodes[0].line` — when present, the inline anchor; absent means it's a general PR-level thread

## Local clone convention (Step 3)

Repos are cloned under `~/projects/<owner>/<repo>` (GitHub has no nested subgroup concept, unlike GitLab). For example, `https://github.com/acme/my-service` would be at `~/projects/acme/my-service`.

## Reply and resolve (Step 8)

**Reply** — a true threaded reply, posted against the thread's root comment. `comment_id` must be that top-level comment, not a reply within the thread — GitHub's replies-to-replies aren't supported, which is exactly why Step 2 captures `comments.nodes[0].databaseId` and not the last one:

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

Resolving a conversation requires write access to the repo. If this call fails with a permission error, the reply above still posted fine — note in the summary that the thread needs resolving by hand.

## Markup dialect

GitHub-flavored Markdown. Fenced code blocks, headings, and `#`/`@` autolinks all render. Emoji shortcodes (`:robot:`) render.
