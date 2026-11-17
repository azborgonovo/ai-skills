# Tracker adapter: GitHub Issues

Mechanics for fetching work-item context from a GitHub issue.

## Fetch the work item (Step 3)

```
gh issue view <url_or_owner/repo#n> --json title,body,labels,url
```

**A GitHub issue has no acceptance-criteria field and no issue-type field**, which changes what you extract. The body *is* the whole specification. Read its structure, its checklists, and any design doc it links, and treat all of that as the ground truth. Take the split between bug and feature from the labels, which are `bug`, `enhancement`, and `feature`. When the issue carries none of those labels, take the split from how the body frames the work.

When `gh` is absent or unauthenticated, degrade as in Step 3.

## Markup dialect

GitHub-flavored Markdown. Quote issue content word for word when you cite it in an inline comment, and do not reformat it.
