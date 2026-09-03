# Tracker adapter: GitHub Issues

Mechanics for fetching work-item context from a GitHub issue. Read this file when Step 3 identifies the linked work item as a GitHub issue reference. That reference is a full `github.com/<owner>/<repo>/issues/<n>` URL, or a cross-repo `<owner>/<repo>#<n>` reference. It can also be a bare `#<n>`, when the change lives on GitHub in the same repo. The tracker is independent of the code host, so a GitLab MR can reference a GitHub issue for its requirements.

## Fetch the work item (Step 3)

```
gh issue view <url_or_owner/repo#n> --json title,body,labels,url
```

**A GitHub issue has no acceptance-criteria field and no issue-type field**, which changes what you extract. The body *is* the whole specification. Read its structure, its checklists, and any design doc it links, and treat all of that as the ground truth. Take the split between bug and feature from the labels, which are `bug`, `enhancement`, and `feature`. When the issue carries none of those labels, take the split from how the body frames the work.

When `gh` is absent or unauthenticated, fall back to the graceful-degradation path from Step 3. When the fetch fails for any reason, continue the review with no requirements context, and note that in the summary.

## Markup dialect

GitHub-flavored Markdown. This adapter is read-only, so quote issue content word for word when you cite it in an inline comment, and do not reformat it.
