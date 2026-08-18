# Tracker adapter: Jira

Mechanics for fetching work-item context from Jira. Read this when Step 3 identifies the linked work item as a Jira key (regex `[A-Z][A-Z0-9]+-\d+` found in the change's title or description).

This adapter is read-only — the skill never posts back to the work item — so all it needs is one fetch of three things: summary, description/acceptance criteria, and issue type.

## Fetch the work item (Step 3)

Prefer Atlassian's Teamwork Graph CLI when it's present — `command -v twg`, then `$HOME/.local/bin/twg` if the shell reports `command not found`. It carries the site and your identity in `~/.config/twg/auth.conf`, so there is no site to resolve:

```
twg jira workitem bulk-get <KEY> --fields summary,description,issuetype --expand renderedFields -o json --output-summary stats
```

**`--expand renderedFields` is what makes the description readable.** Without it the description arrives as raw ADF (`{"type":"doc","content":[...]}`) instead of prose, and the acceptance criteria are exactly the part a conformance check cannot afford to misread. Fields sit flat on the item, not nested under a `fields` key:

```
OUT=<output_files.stdout>
jq -r '.data.items[0].data | {key, summary, type: .issuetype.name}' "$OUT"
jq -r '.data.items[0].data.renderedFields.description' "$OUT"
```

Read `output_files.stdout`, not `output_files.compact` — the compact view keeps only key, summary, and status, dropping the description this fetch exists for.

With no `twg` binary, use the Atlassian MCP tools: load `mcp__claude_ai_Atlassian__getJiraIssue` via `ToolSearch`, then call it with `issueIdOrKey: "<KEY>"`, `responseContentFormat: "markdown"`, and a `cloudId`. **`cloudId` is just the site hostname** (`acme.atlassian.net`) — take it from the `…atlassian.net/browse/<KEY>` URL matched in Step 3. A bare key carries no hostname, so ask the user for the site when nothing in context supplies one.

## When the fetch fails

Continue the review without requirements context and note it in the summary — the spec is optional, and Step 8 already reports a spec-less review as a caveat. If `ToolSearch` surfaces only `mcp__claude_ai_Atlassian__authenticate`, the connector isn't authorized: say so and proceed spec-less rather than opening an OAuth flow in the middle of a review.

## Markup dialect (Step 6, when quoting the work item in a comment)

Quote work-item text as-is rather than reformatting it. Jira's markdown-to-ADF conversion doesn't expand emoji shortcodes, so a quoted `:robot:` would land as literal text — one more reason to leave the quote alone.
