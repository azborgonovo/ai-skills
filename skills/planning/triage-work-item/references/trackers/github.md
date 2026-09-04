# Tracker adapter: GitHub Issues

Mechanics for triaging a GitHub issue. Read this file when Step 1 identifies the tracker as GitHub.

**Status**: verified end-to-end against the live `gh` CLI, version 2.96.0, authenticated. The commands `gh issue view <url> --comments --json title,body,comments,labels,milestone,url` and `gh issue list --search … --state all --json number,title,state` ran live and returned the expected fields. The `gh issue comment --body-file` flag is confirmed, and a real post was deliberately never fired. Trust the read and search commands as written. Before you post, confirm that `gh auth status` shows the right account, and that you are commenting on the intended issue.

## Tooling

Use the `gh` CLI over Bash. No MCP connector and no OAuth flow is needed once `gh auth status` shows that you are logged in. When `gh` is absent or unauthenticated, fall back to the graceful-degradation path in Step 1, which discovers MCP GitHub tools through `ToolSearch`. You can also ask the user to run `gh auth login`.

The `gh issue` commands accept the issue URL, in the form `github.com/<owner>/<repo>/issues/<n>`, directly. So you rarely have to split out the owner and the repo yourself.

## Fetch the issue (Step 2)

```
gh issue view <url> --comments --json title,body,comments,labels,milestone,url
```

The `--comments` flag, or the `comments` JSON field, pulls the full discussion thread. GitHub has no first-class "parent epic". The nearest equivalents are the milestone, the labels, and any issue referenced in the body or the timeline. Note the cross-references for Step 6.

**Attachments have no field of their own here.** GitHub inlines them as Markdown links in the body and in the comment text. So the Step 2 attachment pass means scanning that text for upload URLs, rather than reading a list. Pull them out of the JSON that you already fetched:

```
gh issue view <url> --comments --json body,comments \
  | grep -oE 'https://(github\.com/user-attachments/[^)" ]+|[^)" ]*githubusercontent\.com/[^)" ]+)' | sort -u
```

The filename in the URL is usually the only hint about the type that you get, and there is no size until you request it. Download with `gh api <path>` for a private repo, or with `curl -L` for a public one. Redirect the output to the scratchpad, and not into your context. `references/attached-evidence.md` covers what to do with the file.

## Search related issues (Step 6)

```
gh issue list --repo <owner>/<repo> --search "<keywords>" --state all --json number,title,state
```

A result set is normally small enough to read inline. When you scope a very broad search, keep only `number`, `title`, and `state`, and scan those before you fetch any issue in full.

## Post the comment (Step 11)

```
gh issue comment <url> --body-file <path>
```

Write the drafted comment to a file, and pass `--body-file` instead of `--body` with an inline string. The file avoids shell-quoting damage to code fences and to multi-line Markdown.

## Markup dialect (Step 4)

GitHub-flavored Markdown. Fenced code blocks with language hints, task lists, and `#` and `@` autolinks all render. Emoji shortcodes such as `:robot:` render.

A bare commit SHA autolinks only for the repo that holds this issue. An investigation usually reads a different repo, so cite a commit there as an explicit markdown link, or in the qualified `owner/repo@sha` form. Neither form autolinks inside backticks, because a code span suppresses the reference.
