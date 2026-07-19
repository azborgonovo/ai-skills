# JIRA context setup

One-time setup for fetching a JIRA ticket: authorizing the Atlassian MCP server and resolving the org's cloudId. Once auth is established and the cloudId is cached, Step 3 needs none of this — it reads the cache file and calls `getJiraIssue` directly.

## Authorize the Atlassian MCP server

Load `mcp__claude_ai_Atlassian__getJiraIssue` via ToolSearch. If the cloudId cache file (below) is missing, add `mcp__claude_ai_Atlassian__getAccessibleAtlassianResources` to the same ToolSearch call.

**If ToolSearch returns only `mcp__claude_ai_Atlassian__authenticate`** (not `getJiraIssue`), the server needs OAuth before continuing:

1. Call `mcp__claude_ai_Atlassian__authenticate` (no parameters needed).
2. Share the returned authorization URL with the user:
   > Atlassian needs authorization. Please open this URL and complete the login: `<url>`
   > Let me know when done.
3. **Pause** — do not proceed until the user confirms.
4. Once confirmed, retry ToolSearch for `mcp__claude_ai_Atlassian__getJiraIssue`. If it's now available, continue. If it still isn't, skip JIRA context and note it in the summary.

## Resolve the cloudId

The cloudId is machine- and org-specific, so it lives in a local cache file — never in this skill:

1. Read `$HOME/.claude/atlassian-cloud-id` (use the expanded absolute path — `~` isn't expanded by file tools). If it exists, its single line is the cloudId; skip discovery.
2. Otherwise call `getAccessibleAtlassianResources` and take the returned resource's `id` (the site-URL form like `acme.atlassian.net` also works as a cloudId). If it returns several sites, ask the user which one their JIRA lives on.
3. Write the resolved value to `$HOME/.claude/atlassian-cloud-id` and tell the user you cached it — every future run then takes the one-file-read fast path.
