# Tracker adapter: Jira

Mechanics for triaging a Jira issue. Read this when Step 1 identifies the tracker as Jira.

There are two backends. Pick one at the start of the run and stay on it — mixing them means resolving identity twice for no gain.

## Pick a backend

Check for Atlassian's Teamwork Graph CLI first: `command -v twg`, then `$HOME/.local/bin/twg` if the shell reports `command not found`. A missing binary is the only reason to fall back — an auth or command error is a twg problem to fix, not a signal to switch backends.

- **`twg` is available** → use **Backend A** below. The CLI carries the site and your identity in `~/.config/twg/auth.conf`, so there is no `cloudId` to resolve and no OAuth pause.
- **`twg` is absent** → use **Backend B**, the Atlassian MCP tools.

**Confirm the grammar before an unfamiliar or consequential call**: `twg help describe "<exact path>"` (e.g. `twg help describe "jira workitem comment create"`). The command surface moves between releases, and the flags below were verified against 1.1.1 — treat them as a starting point, not a guarantee. If the `twg` and `twg-jira` skills are installed, they own the fuller command and mutation-safety contract.

## Backend A — the TWG CLI

### Fetch the issue (Step 2)

```
twg jira workitem bulk-get <KEY> --fields summary,status,issuetype,parent,issuelinks,description,comment,attachment --expand renderedFields -o json --output-summary stats
```

**`--expand renderedFields` is what makes this readable.** Without it, `description` and every comment body come back as raw ADF (`{"type":"doc","content":[...]}`) and you burn context reassembling prose from a node tree. With it, the same fields also appear as clean HTML under `renderedFields`, which is what you want to actually read.

Fields sit flat on the item, not nested under a `fields` key. Project the structural data and the prose separately:

```
OUT=<output_files.stdout>
jq -r '.data.items[0].data | {key, summary, type: .issuetype.name, status: .status.name, parent: .parent.key, links: [.issuelinks[]?]}' "$OUT"
jq -r '.data.items[0].data.renderedFields.description' "$OUT"
jq -r '.data.items[0].data.renderedFields.comment.comments[] | "\n--- \(.created) — \(.author.displayName) ---\n\(.body)"' "$OUT"
jq -r '.data.items[0].data.attachment[]? | "\(.id) | \(.filename) | \(.created) | \(.size) bytes | \(.mimeType)"' "$OUT"
```

The comment projection is Step 2's requirement in one call: the whole thread, in order. The parent epic key is `.parent.key`; linked issues are under `.issuelinks`.

`attachment` is not among the fields `bulk-get` returns by default, which is why it is listed explicitly above — omit it and the response gives no hint that the issue has files at all. Note the `.created` date on each one: it is what tells you an attachment landed long before the comment still asking for it.

`bulk-get` takes several keys at once, so use it to hydrate a batch of related issues in one round trip rather than looping `get`.

### Download an attachment (Step 8)

There is no `twg jira attachment` command. Use the CLI's authenticated REST passthrough with the attachment `id` from the projection above:

```
twg api "jira:/rest/api/3/attachment/content/<id>" > "$SCRATCH/<filename>"
```

`twg api` signs the request with the credentials already in `~/.config/twg/auth.conf`, so this needs no token of your own — **don't** read that file to hand-build a `curl`. Redirect to a file rather than letting the body land in your context; these are routinely megabytes. `references/attached-evidence.md` covers what to do with it next.

### Search related issues (Step 6)

```
twg jira workitem query --jql "<JQL>" -o json --output-summary stats --agent-fields data.issues.key,data.issues.summary,data.issues.status
```

Two search leads worth running: siblings under the same parent epic (`"parent" = <EPIC-KEY>` or `"Epic Link" = <EPIC-KEY>` depending on the project's config), and a summary keyword search (`summary ~ "<keyword>"`). Narrow the page size with `--limit` when you only need candidates to scan.

### Post the comment (Step 11)

```
twg jira workitem comment create --issue-id <KEY> --body-format markdown --body "$COMMENT"
```

`--body-format` accepts `html` (the default), `markdown`, or `plain`. There is no `--body-file` on this command, so build a multi-line body into a shell variable first and pass it as one quoted argument:

```
COMMENT=$(cat "${TMPDIR:-/tmp}/triage-comment.md")
twg jira workitem comment create --issue-id <KEY> --body-format markdown --body "$COMMENT"
```

### Output budget

`twg` writes large payloads to a file and prints a YAML envelope instead of flooding your context. Treat the envelope as a pointer, not the answer, and go to the right file for the job: `output_files.compact` is a good first stop for a *search* result, where key/summary/status is all you need to pick candidates. For a work-item fetch it is the wrong file — it keeps only key, summary, status, and assignee, dropping the description and the entire comment thread — so `jq` the projections above against `output_files.stdout` instead. Use `jq` rather than `rg` on these files: `rg` treats structured JSON as text and re-expands the payload you just avoided.

## Backend B — the Atlassian MCP tools

### Loading the tools

The Atlassian MCP tools are usually deferred; if `mcp__claude_ai_Atlassian__getJiraIssue` isn't already callable, load it first:

```
ToolSearch: select:mcp__claude_ai_Atlassian__getJiraIssue,mcp__claude_ai_Atlassian__addCommentToJiraIssue,mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
```

If ToolSearch only surfaces `mcp__claude_ai_Atlassian__authenticate`, the connector needs OAuth: call `authenticate`, share the returned URL with the user, wait for confirmation, then retry the ToolSearch. Don't proceed to fetching until the real tools are available.

`cloudId` for every Atlassian call is just the site hostname, e.g. `acme.atlassian.net` — extract it from whatever URL you were given. A bare key (`PROJ-123`) has no hostname, so ask for the site if it isn't already visible in context.

### Fetch the issue (Step 2)

Call `getJiraIssue` with `fields: ["*all", "comment"]` and `responseContentFormat: "markdown"`. This returns the description plus the full comment thread; read the whole thread in order.

The parent epic key is on the issue's fields; linked issues (duplicates, relates-to, blocks) are under `issuelinks`. `*all` also brings back `attachment` — read its `filename`/`created`/`size`/`mimeType` entries as Step 2 asks, and keep the `content` URL for each one.

Downloading an attachment is the gap in this backend: `mcp__claude_ai_Atlassian__fetch` resolves an issue or page ARI, not an attachment binary, and there is no MCP tool that returns file bytes. If `twg` is installed, borrow Backend A's `twg api` call for the download alone; otherwise ask the user to fetch the file and give you the local path, and say why you're asking. Guessing at an authenticated `curl` wastes a round trip and risks putting a token where it doesn't belong.

### Search related issues (Step 6)

Use `searchJiraIssuesUsingJql`, with the same two leads as Backend A.

**`searchJiraIssuesUsingJql` results are often huge** and can exceed the tool's token limit, in which case the result gets saved to a file instead of returned inline. When that happens, use `jq` on that file rather than trying to `Read` it directly — pull out just `key`/`summary`/`status` first to scan for candidates before fetching anything in full.

### Post the comment (Step 11)

Call `addCommentToJiraIssue` with `contentFormat: "markdown"`. Jira accepts Markdown here and renders it to its own format, so write the draft in Markdown.

## Markup dialect (Step 4)

Write the comment body in Markdown on either backend — Backend A via `--body-format markdown`, Backend B via `contentFormat: "markdown"`. Standard fenced code blocks, headings, and links render correctly. Jira's own wiki markup (`h2. Heading`, `*bold*`, `[label|url]`) is a third dialect that neither path accepts; `twg` rejects it outright.

Jira's markdown-to-ADF conversion does not expand emoji shortcodes (`:robot:`) the way Slack or GitHub-flavored markdown do — posting `:robot:` renders as the literal text ":robot:", not an emoji. Use the literal Unicode character (🤖) instead, in the attribution line and anywhere else you'd otherwise reach for a shortcode.
