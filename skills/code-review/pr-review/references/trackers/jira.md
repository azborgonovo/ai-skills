# Tracker adapter: JIRA

Mechanics for fetching ticket context from JIRA. Read this when Step 3 identifies the linked ticket as a JIRA key (regex `[A-Z][A-Z0-9]+-\d+` found in the change's title or description).

## One-time setup: authorize the Atlassian MCP server

Load `mcp__claude_ai_Atlassian__getJiraIssue` via ToolSearch. If the cloudId cache file (below) is missing, add `mcp__claude_ai_Atlassian__getAccessibleAtlassianResources` to the same ToolSearch call.

**If ToolSearch returns only `mcp__claude_ai_Atlassian__authenticate`** (not `getJiraIssue`), the server needs OAuth before continuing:

1. Call `mcp__claude_ai_Atlassian__authenticate` (no parameters needed).
2. Share the returned authorization URL with the user:
   > Atlassian needs authorization. Please open this URL and complete the login: `<url>`
   > Let me know when done.
3. **Pause** — do not proceed until the user confirms.
4. Once confirmed, retry ToolSearch for `mcp__claude_ai_Atlassian__getJiraIssue`. If it's now available, continue. If it still isn't, skip JIRA context and note it in the summary.

## One-time setup: resolve the cloudId

The cloudId is machine- and org-specific, so it lives in a local cache file — never in this skill:

1. Read `$HOME/.claude/atlassian-cloud-id` (use the expanded absolute path — `~` isn't expanded by file tools). If it exists, its single line is the cloudId; skip discovery.
2. Otherwise call `getAccessibleAtlassianResources` and take the returned resource's `id` (the site-URL form like `acme.atlassian.net` also works as a cloudId). If it returns several sites, ask the user which one their JIRA lives on.
3. Write the resolved value to `$HOME/.claude/atlassian-cloud-id` and tell the user you cached it — every future run then takes the one-file-read fast path below.

## Fetch the ticket (Step 3)

Once auth is established and the cloudId is cached, this is the fast path every run after the first takes: call `getJiraIssue` with `issueIdOrKey: "<KEY>"` and the cached `cloudId`. Extract:
- Summary (the "what")
- Description / acceptance criteria (the "done conditions")
- Issue type (Story / Task / Bug)

If the fetch fails for any reason, continue the review without requirements context — note it in the summary at the end.

## Markup dialect (Step 6, when quoting the ticket in a comment)

Jira's markdown-to-ADF conversion does not expand emoji shortcodes (`:robot:`) the way GitLab/GitHub-flavored markdown do — posting `:robot:` in a comment elsewhere would render as the literal text ":robot:". This adapter is read-only (this skill never posts back to the ticket), so it only matters if you quote ticket content verbatim in an inline comment — quote the text as-is rather than reformatting it.
