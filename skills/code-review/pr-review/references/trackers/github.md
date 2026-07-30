# Tracker adapter: GitHub Issues

Mechanics for fetching ticket context from a GitHub issue. Read this when Step 3 identifies the linked ticket as a GitHub issue reference — a full `github.com/<owner>/<repo>/issues/<n>` URL, a cross-repo `<owner>/<repo>#<n>` reference, or a bare `#<n>` when the change itself lives on GitHub in the same repo.

This applies whether or not the change under review also lives on GitHub — the code host and the ticket tracker are independent (a GitLab MR can reference a GitHub issue for requirements, and vice versa).

## Tooling

Use the `gh` CLI over Bash — no separate MCP connector needed once `gh auth status` shows you're logged in. If `gh` isn't installed or authenticated, fall back to the graceful-degradation path from Step 3 (discover MCP GitHub tools via `ToolSearch`).

## Fetch the ticket (Step 3)

```
gh issue view <url_or_owner/repo#n> --json title,body,labels,url
```

Extract:
- `title` (the "what")
- `body` (the "done conditions" — GitHub issues have no dedicated acceptance-criteria field, so treat the body's own structure, checklists, or a linked design doc as the ground truth)
- `labels` — GitHub has no first-class "issue type" field; infer bug vs. feature/task from labels (`bug`, `enhancement`, `feature`) when present, otherwise treat the body's own framing as the signal

If the fetch fails for any reason, continue the review without requirements context — note it in the summary at the end.

## Markup dialect

GitHub-flavored Markdown. This adapter is read-only (this skill never posts back to the ticket) — quote issue content verbatim when citing it in an inline comment rather than reformatting it.
