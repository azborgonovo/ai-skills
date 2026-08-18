# Tracker adapter: JIRA

Mechanics for fetching work-item context from JIRA. Read this when Step 3 identifies the linked work item as a JIRA key (regex `[A-Z][A-Z0-9]+-\d+` found in the change's title or description).

This adapter is read-only — the skill never posts back to the work item — so all it needs is a single fetch. There are two backends; the first one available wins.

## Backend A — the TWG CLI

Check for Atlassian's Teamwork Graph CLI: `command -v twg`, then `$HOME/.local/bin/twg` if the shell reports `command not found`. If it's there, this is the whole adapter — the CLI carries the site and your identity in `~/.config/twg/auth.conf`, so there is no OAuth handshake and no `cloudId` to resolve or cache:

```
twg jira workitem bulk-get <KEY> --fields summary,description,issuetype --expand renderedFields -o json --output-summary stats
```

**`--expand renderedFields` is what makes the description readable.** Without it the description comes back as raw ADF (`{"type":"doc","content":[...]}`) rather than prose, and acceptance criteria are exactly the part you cannot afford to misread.

Fields sit flat on the item, not nested under a `fields` key, so extract the three things this skill needs from `output_files.stdout`:

```
OUT=<output_files.stdout>
jq -r '.data.items[0].data | {key, summary, type: .issuetype.name}' "$OUT"
jq -r '.data.items[0].data.renderedFields.description' "$OUT"
```

- Summary (the "what")
- Description / acceptance criteria (the "done conditions") — the rendered HTML
- Issue type (Story / Task / Bug)

Read `output_files.stdout` rather than `output_files.compact` here: the compact view keeps only key, summary, and status, dropping the description this skill exists to fetch. Confirm flags with `twg help describe "jira workitem bulk-get"` if a call is rejected — the command surface moves between releases.

## Backend B — the Atlassian MCP tools

Take this path only when the `twg` binary is absent.

### One-time setup: authorize the Atlassian MCP server

Load `mcp__claude_ai_Atlassian__getJiraIssue` via ToolSearch. If the cloudId cache file (below) is missing, add `mcp__claude_ai_Atlassian__getAccessibleAtlassianResources` to the same ToolSearch call.

**If ToolSearch returns only `mcp__claude_ai_Atlassian__authenticate`** (not `getJiraIssue`), the server needs OAuth before continuing:

1. Call `mcp__claude_ai_Atlassian__authenticate` (no parameters needed).
2. Share the returned authorization URL with the user:
   > Atlassian needs authorization. Please open this URL and complete the login: `<url>`
   > Let me know when done.
3. **Pause** — do not proceed until the user confirms.
4. Once confirmed, retry ToolSearch for `mcp__claude_ai_Atlassian__getJiraIssue`. If it's now available, continue. If it still isn't, skip JIRA context and note it in the summary.

### One-time setup: resolve the cloudId

The cloudId is machine- and org-specific, so it lives in a local cache file — never in this skill:

1. Read `$HOME/.claude/atlassian-cloud-id` (use the expanded absolute path — `~` isn't expanded by file tools). If it exists, its single line is the cloudId; skip discovery.
2. Otherwise call `getAccessibleAtlassianResources` and take the returned resource's `id` (the site-URL form like `acme.atlassian.net` also works as a cloudId). If it returns several sites, ask the user which one their JIRA lives on.
3. Write the resolved value to `$HOME/.claude/atlassian-cloud-id` and tell the user you cached it — every future run then takes the one-file-read fast path below.

### Fetch the work item (Step 3)

Once auth is established and the cloudId is cached, call `getJiraIssue` with `issueIdOrKey: "<KEY>"` and the cached `cloudId`, extracting the same three things as Backend A.

## When the fetch fails

On either backend: if the fetch fails for any reason, continue the review without requirements context — note it in the summary at the end.

## Markup dialect (Step 6, when quoting the work item in a comment)

Jira's markdown-to-ADF conversion does not expand emoji shortcodes (`:robot:`) the way GitLab/GitHub-flavored markdown do — posting `:robot:` in a comment elsewhere would render as the literal text ":robot:". This adapter is read-only, so it only matters if you quote work-item content verbatim in an inline comment — quote the text as-is rather than reformatting it.
