# Tracker adapter: Jira

Mechanics for triaging a Jira issue. Read this when Step 1 identifies the tracker as Jira.

## Loading the tools

The Atlassian MCP tools are usually deferred; if `mcp__claude_ai_Atlassian__getJiraIssue` isn't already callable, load it first:

```
ToolSearch: select:mcp__claude_ai_Atlassian__getJiraIssue,mcp__claude_ai_Atlassian__addCommentToJiraIssue,mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
```

If ToolSearch only surfaces `mcp__claude_ai_Atlassian__authenticate`, the connector needs OAuth: call `authenticate`, share the returned URL with the user, wait for confirmation, then retry the ToolSearch. Don't proceed to fetching until the real tools are available.

`cloudId` for every Atlassian call is just the site hostname, e.g. `acme.atlassian.net` — extract it from whatever URL you were given. A bare key (`PROJ-123`) has no hostname, so ask for the site if it isn't already visible in context.

## Fetch the issue (Step 2)

Call `getJiraIssue` with `fields: ["*all", "comment"]` and `responseContentFormat: "markdown"`. This returns the description plus the full comment thread; read the whole thread in order.

The parent epic key is on the issue's fields; linked issues (duplicates, relates-to, blocks) are under `issuelinks`.

## Search related issues (Step 6)

Use `searchJiraIssuesUsingJql`. Two search leads worth running: siblings under the same parent epic (`"parent" = <EPIC-KEY>` or `"Epic Link" = <EPIC-KEY>` depending on the project's config), and a summary keyword search (`summary ~ "<keyword>"`).

**`searchJiraIssuesUsingJql` results are often huge** and can exceed the tool's token limit, in which case the result gets saved to a file instead of returned inline. When that happens, use `jq` on that file rather than trying to `Read` it directly — pull out just `key`/`summary`/`status` first to scan for candidates before fetching anything in full.

## Post the comment (Step 11)

Call `addCommentToJiraIssue` with `contentFormat: "markdown"`. Jira accepts Markdown here and renders it to its own format, so write the draft in Markdown.

## Markup dialect (Step 4)

Write the comment body in Markdown — the `contentFormat: "markdown"` post call handles conversion. Standard fenced code blocks, headings, and links render correctly.

Jira's markdown-to-ADF conversion does not expand emoji shortcodes (`:robot:`) the way Slack or GitHub-flavored markdown do — posting `:robot:` renders as the literal text ":robot:", not an emoji. Use the literal Unicode character (🤖) instead, in the attribution line and anywhere else you'd otherwise reach for a shortcode.
