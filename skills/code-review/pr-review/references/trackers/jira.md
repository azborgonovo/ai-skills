# Tracker adapter: Jira

Mechanics for fetching work-item context from Jira. One fetch gets three things: the summary, the description or acceptance criteria, and the issue type.

## Fetch the work item (Step 3)

Prefer the Teamwork Graph CLI of Atlassian when it is present. Look for it with `command -v twg`, and then at `$HOME/.local/bin/twg` when the shell reports `command not found`. The CLI carries the site and your identity in `~/.config/twg/auth.conf`, so there is no site to resolve:

```
twg jira workitem bulk-get <KEY> --fields summary,description,issuetype --expand renderedFields -o json --output-summary stats
```

**`--expand renderedFields` is required.** Without it, the description arrives as raw ADF, in the shape `{"type":"doc","content":[...]}`, instead of prose. The fields sit flat on the item, and not nested under a `fields` key:

```
OUT=<output_files.stdout>
jq -r '.data.items[0].data | {key, summary, type: .issuetype.name}' "$OUT"
jq -r '.data.items[0].data.renderedFields.description' "$OUT"
```

Read `output_files.stdout`, not `output_files.compact`. The compact view keeps only the key, the summary, and the status, and it drops the description that this fetch exists for.

With no `twg` binary, use the Atlassian MCP tools. Load `mcp__claude_ai_Atlassian__getJiraIssue` through `ToolSearch`, then call it with `issueIdOrKey: "<KEY>"`, `responseContentFormat: "markdown"`, and a `cloudId`. **`cloudId` is the site hostname**, such as `acme.atlassian.net`. Take it from the `…atlassian.net/browse/<KEY>` URL that Step 3 matched. A bare key carries no hostname, so ask the user for the site when nothing in the context supplies one.

## When the fetch fails

Continue the review with no spec, as in Step 3. If `ToolSearch` surfaces only `mcp__claude_ai_Atlassian__authenticate`, the connector is not authorized. Say so and proceed with no spec, instead of opening an OAuth flow in the middle of a review.

## Markup dialect (Step 6, when a comment quotes the work item)

Quote work-item text as it stands, and do not reformat it. The markdown-to-ADF conversion of Jira does not expand emoji shortcodes, so a quoted `:robot:` lands as literal text.
