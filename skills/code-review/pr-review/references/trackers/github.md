# Tracker adapter: GitHub Issues

Mechanics for fetching work-item context from a GitHub issue. Read this when Step 3 identifies the linked work item as a GitHub issue reference — a full `github.com/<owner>/<repo>/issues/<n>` URL, a cross-repo `<owner>/<repo>#<n>`, or a bare `#<n>` when the change itself lives on GitHub in the same repo. The tracker is independent of the code host: a GitLab MR can reference a GitHub issue for its requirements.

## Fetch the work item (Step 3)

```
gh issue view <url_or_owner/repo#n> --json title,body,labels,url
```

**GitHub issues have no acceptance-criteria field and no issue-type field**, which changes what you extract: the body *is* the whole specification, so read its own structure, checklists, and any design doc it links as the ground truth, and take bug-vs-feature from the labels (`bug`, `enhancement`, `feature`) or, absent those, from the body's own framing.

If `gh` isn't installed or authenticated, fall back to the graceful-degradation path from Step 3. If the fetch fails for any reason, continue the review without requirements context and note it in the summary.

## Markup dialect

GitHub-flavored Markdown. This adapter is read-only, so quote issue content verbatim when citing it in an inline comment rather than reformatting it.
