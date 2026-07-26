# Tracker adapter: GitHub Issues

Mechanics for triaging a GitHub issue. Read this when Step 1 identifies the tracker as GitHub.

**Status**: every command and flag below is verified against the official `gh` CLI reference (July 2026) — the flags, `--state all`, URL arguments, and the `--json` field names all exist as written. Not yet run end-to-end from this skill against a live repo, so confirm `gh auth status` and do one real fetch/comment before trusting output on an issue that matters.

## Tooling

Use the `gh` CLI over Bash — no MCP connector or OAuth dance needed once `gh auth status` shows you're logged in. If `gh` isn't installed or authenticated, fall back to the graceful-degradation path in Step 1 (discover MCP GitHub tools via `ToolSearch`), or ask the user to `gh auth login`.

The issue URL (`github.com/<owner>/<repo>/issues/<n>`) is accepted directly by `gh issue` commands, so you rarely need to split out owner/repo yourself.

## Fetch the issue (Step 2)

```
gh issue view <url> --comments --json title,body,comments,labels,milestone,url
```

`--comments` (or the `comments` JSON field) pulls the full discussion thread. GitHub has no first-class "parent epic"; the nearest equivalents are the milestone, labels, and any issues referenced in the body or timeline — note cross-references for Step 6.

## Search related issues (Step 6)

```
gh issue list --repo <owner>/<repo> --search "<keywords>" --state all --json number,title,state
```

Result sets are normally small enough to read inline. If you scope a very broad search, keep only `number`/`title`/`state` and scan before fetching any issue in full.

## Post the comment (Step 11)

```
gh issue comment <url> --body-file <path>
```

Write the drafted comment to a file and pass `--body-file` rather than `--body` with an inline string — it avoids shell-quoting damage to code fences and multi-line Markdown.

## Markup dialect (Step 4)

GitHub-flavored Markdown. Fenced code blocks with language hints, task lists, and `#`/`@` autolinks all render. Emoji shortcodes (`:robot:`) render.
