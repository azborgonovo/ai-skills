# Host adapter: GitHub

Mechanics for addressing comments on a GitHub pull request. The URL has the shape `https://github.com/<owner>/<repo>/pull/<number>`.

## Tooling

Use the `gh` CLI over Bash. When `gh` is absent or not logged in, ask the user to run `gh auth login`, or fall back to the `ToolSearch` path in Step 1.

Listing and resolving threads use GraphQL, because REST exposes neither the resolved state nor a resolve action. Replying uses REST.

## Fetch change metadata (Step 2)

```
gh pr view <url> --json title,headRefName,url
```

Extract `title`, `headRefName`, which is the source branch, and `url`.

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
- `comments.nodes[].body` and `comments.nodes[].author.login`, which give the full exchange.
- `comments.nodes[0].path` and `comments.nodes[0].line`, which give the inline anchor when they are present.

## Repo path shape (Step 3)

`<repo_path>` is `<owner>/<repo>`. For example, `https://github.com/acme/my-service` gives `acme/my-service`.

## Reply and resolve (Step 8)

**Reply** against the root comment of the thread, `comments.nodes[0].databaseId`, because GitHub does not support a reply to a reply:

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

Resolving a conversation requires write access to the repo.

## Markup dialect

GitHub-flavored Markdown. Fenced code blocks, headings, and `#` and `@` autolinks all render.
