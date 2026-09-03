# Tracker adapter: Jira

Mechanics for triaging a Jira issue. Read this file when Step 1 identifies the tracker as Jira.

There are two backends. Pick one at the start of the run, and stay on it. Mixing them means resolving identity twice for no gain.

## Pick a backend

Check for the Teamwork Graph CLI of Atlassian first. Run `command -v twg`, and then look at `$HOME/.local/bin/twg` when the shell reports `command not found`. A missing binary is the only reason to fall back. An auth error or a command error is a `twg` problem to fix, and not a signal to switch backends.

- When **`twg` is available**, use **Backend A** below. The CLI carries the site and your identity in `~/.config/twg/auth.conf`, so there is no `cloudId` to resolve and no OAuth pause.
- When **`twg` is absent**, use **Backend B**, which is the Atlassian MCP tools.

**Confirm the grammar before an unfamiliar or consequential call**, with `twg help describe "<exact path>"`, for example `twg help describe "jira workitem comment create"`. The command surface moves between releases. The flags below were verified against version 1.1.1, so treat them as a starting point and not as a guarantee. When the `twg` and `twg-jira` skills are installed, they own the fuller command contract and the mutation-safety contract.

## Backend A: the TWG CLI

### Fetch the issue (Step 2)

```
twg jira workitem bulk-get <KEY> --fields summary,status,issuetype,parent,issuelinks,description,comment,attachment --expand renderedFields -o json --output-summary stats
```

**`--expand renderedFields` is what makes this readable.** Without it, `description` and every comment body come back as raw ADF, in the shape `{"type":"doc","content":[...]}`. You then burn context reassembling prose from a node tree. With it, the same fields also appear as clean HTML under `renderedFields`, which is what you want to read.

The fields sit flat on the item, and not nested under a `fields` key. Project the structural data and the prose separately:

```
OUT=<output_files.stdout>
jq -r '.data.items[0].data | {key, summary, type: .issuetype.name, status: .status.name, parent: .parent.key, links: [.issuelinks[]?]}' "$OUT"
jq -r '.data.items[0].data.renderedFields.description' "$OUT"
jq -r '.data.items[0].data.renderedFields.comment.comments[] | "\n--- \(.created) — \(.author.displayName) ---\n\(.body)"' "$OUT"
jq -r '.data.items[0].data.attachment[]? | "\(.id) | \(.filename) | \(.created) | \(.size) bytes | \(.mimeType)"' "$OUT"
```

The comment projection satisfies the Step 2 requirement in one call, because it gives the whole thread in order. The parent epic key is `.parent.key`, and the linked issues sit under `.issuelinks`.

`bulk-get` does not return `attachment` by default, which is why the command above lists it explicitly. Omit it, and the response gives no hint that the issue holds any file. Note the `.created` date on each attachment. That date is what tells you that a file landed long before the comment still asking for it.

`bulk-get` takes several keys at once, so use it to hydrate a batch of related issues in one round trip, instead of looping over `get`.

### Download an attachment (Step 8)

There is no `twg jira attachment` command. Use the authenticated REST passthrough of the CLI, with the attachment `id` from the projection above:

```
twg api "jira:/rest/api/3/attachment/content/<id>" > "$SCRATCH/<filename>"
```

`twg api` signs the request with the credentials already in `~/.config/twg/auth.conf`, so it needs no token of your own. **Do not** read that file to hand-build a `curl` command. Redirect the output to a file, instead of letting the body land in your context, because these files routinely run to megabytes. `references/attached-evidence.md` covers what to do with the file next.

### Search related issues (Step 6)

```
twg jira workitem query --jql "<JQL>" -o json --output-summary stats --agent-fields data.issues.key,data.issues.summary,data.issues.status
```

Two search leads are worth running. The first finds siblings under the same parent epic, through `"parent" = <EPIC-KEY>` or `"Epic Link" = <EPIC-KEY>`, depending on the configuration of the project. The second is a summary keyword search, through `summary ~ "<keyword>"`. Narrow the page size with `--limit` when you need only candidates to scan.

### Post the comment (Step 11)

```
twg jira workitem comment create --issue-id <KEY> --body-format markdown --body "$COMMENT"
```

`--body-format` accepts `html`, which is the default, plus `markdown` and `plain`. This command has no `--body-file` flag, so build a multi-line body into a shell variable first, and pass it as one quoted argument:

```
COMMENT=$(cat "${TMPDIR:-/tmp}/triage-comment.md")
twg jira workitem comment create --issue-id <KEY> --body-format markdown --body "$COMMENT"
```

### Output budget

`twg` writes a large payload to a file, and prints a YAML envelope, so it does not flood your context. Treat the envelope as a pointer rather than the answer, and go to the right file for the job. `output_files.compact` is a good first stop for a *search* result, where the key, the summary, and the status are all you need to pick candidates. For a work-item fetch, `compact` is the wrong file. It keeps only the key, the summary, the status, and the assignee, and it drops the description and the entire comment thread. Run the projections above against `output_files.stdout` instead. Use `jq` rather than `rg` on these files, because `rg` treats structured JSON as text, and it re-expands the payload that you just avoided.

## Backend B: the Atlassian MCP tools

### Loading the tools

The Atlassian MCP tools are usually deferred. When `mcp__claude_ai_Atlassian__getJiraIssue` is not already callable, load it first:

```
ToolSearch: select:mcp__claude_ai_Atlassian__getJiraIssue,mcp__claude_ai_Atlassian__addCommentToJiraIssue,mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
```

When `ToolSearch` surfaces only `mcp__claude_ai_Atlassian__authenticate`, the connector needs OAuth. Call `authenticate`, share the returned URL with the user, wait for their confirmation, then retry the `ToolSearch` call. Do not proceed to the fetch until the real tools are available.

The `cloudId` for every Atlassian call is the site hostname, such as `acme.atlassian.net`. Extract it from whatever URL you were given. A bare key such as `PROJ-123` carries no hostname, so ask for the site when it is not already visible in the context.

### Fetch the issue (Step 2)

Call `getJiraIssue` with `fields: ["*all", "comment"]` and `responseContentFormat: "markdown"`. That call returns the description plus the full comment thread. Read the whole thread in order.

The parent epic key sits on the fields of the issue. The linked issues, which are duplicates, relates-to links, and blocks links, sit under `issuelinks`. `*all` also brings back `attachment`. Read its `filename`, `created`, `size`, and `mimeType` entries, as Step 2 asks, and keep the `content` URL for each one.

Downloading an attachment is the gap in this backend. `mcp__claude_ai_Atlassian__fetch` resolves an issue ARI or a page ARI, and not an attachment binary, and no MCP tool returns file bytes. When `twg` is installed, borrow the `twg api` call from Backend A for the download alone. Otherwise ask the user to fetch the file and give you the local path, and say why you are asking. A guessed authenticated `curl` wastes a round trip, and it risks putting a token where it does not belong.

### Search related issues (Step 6)

Use `searchJiraIssuesUsingJql`, with the same two leads as Backend A.

**The results of `searchJiraIssuesUsingJql` are often huge**, and they can exceed the token limit of the tool. The result is then saved to a file, instead of returned inline. When that happens, use `jq` on that file, instead of trying to `Read` it directly. Pull out `key`, `summary`, and `status` first, and scan those for candidates, before you fetch anything in full.

### Post the comment (Step 11)

Call `addCommentToJiraIssue` with `contentFormat: "markdown"`. Jira accepts Markdown here and renders it to its own format, so write the draft in Markdown.

## Markup dialect (Step 4)

Write the comment body in Markdown on either backend. Backend A takes `--body-format markdown`, and Backend B takes `contentFormat: "markdown"`. Standard fenced code blocks, headings, and links render correctly. The wiki markup of Jira, such as `h2. Heading`, `*bold*`, and `[label|url]`, is a third dialect that neither path accepts, and `twg` rejects it outright.

The markdown-to-ADF conversion of Jira does not expand an emoji shortcode such as `:robot:`, the way Slack or GitHub-flavored markdown does. A posted `:robot:` renders as the literal text ":robot:", and not as an emoji. Use the literal Unicode character 🤖 instead, in the attribution line and everywhere else in the comment.
