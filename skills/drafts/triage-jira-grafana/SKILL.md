---
name: triage-jira-grafana
description: >
  Triages a Jira ticket end-to-end: reads the ticket (description, full comment thread, linked
  issues, parent epic), cross-references related tickets, investigates the actual codebase(s) that
  implement the affected feature, optionally corroborates with Grafana (logs/traces/metrics), then
  posts a verified root-cause analysis comment back to the ticket. TRIGGER when the user gives a
  Jira ticket URL or key and asks to triage, investigate, diagnose, or "figure out what's going on
  with" it, especially when they also want an analysis comment posted back — even if they don't say
  "triage" explicitly (e.g. "can you look into TICKET-123 and post what you find", "why is this
  ticket happening, check the code"). Do not use this for simply
  reading or summarizing a ticket with no code investigation intended, and do not use it for writing
  new tickets.
argument-hint: "<Jira ticket URL or key> [reference comment URL to match style] [--dry-run]"
allowed-tools: [Read, Bash, Agent, ToolSearch, AskUserQuestion, Write]
---

# Triage a Jira ticket against the codebase and Grafana

This is an investigation workflow, not a lookup. The value it adds over just reading the ticket is
verified root cause: a specific code path, config value, or data condition that a future engineer
can act on immediately, backed by evidence you actually checked rather than plausible-sounding
guesses. Every step below exists to either gather that evidence or to guard against reporting
something that sounds right but isn't.

By default, once you've verified your findings, post the comment — don't pause for a separate
approval step. The verification step (Step 7) is the safety gate, not a human checkpoint. The one
exception is `--dry-run`: if the user passes it (or clearly wants to see the analysis before
anything goes out), write the finished comment to a file and show it instead of posting.

## Inputs

- **Required**: a Jira ticket URL (`https://<site>.atlassian.net/browse/<KEY>`) or bare key. If
  bare, you need the site hostname too — ask if it isn't obvious from context (e.g. from a prior
  message in the conversation, or a `.atlassian.net` reference already visible).
- **Optional**: a reference ticket/comment URL whose analysis-comment style you should mirror.
- **Optional**: which repo(s)/codebase(s) to investigate. If not given, see Step 4.
- **Optional**: `--dry-run` — draft only, never post.

## Step 1 — Load the Atlassian tools

The Atlassian MCP tools are usually deferred; if `mcp__claude_ai_Atlassian__getJiraIssue` isn't
already callable, load it first:

```
ToolSearch: select:mcp__claude_ai_Atlassian__getJiraIssue,mcp__claude_ai_Atlassian__addCommentToJiraIssue,mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql
```

If ToolSearch only surfaces `mcp__claude_ai_Atlassian__authenticate`, the connector needs OAuth:
call `authenticate`, share the returned URL with the user, wait for confirmation, then retry the
ToolSearch. Don't proceed to fetching until the real tools are available.

`cloudId` for every Atlassian call is just the site hostname, e.g. `acme.atlassian.net` — extract
it from whatever URL you were given.

## Step 2 — Fetch the target issue in full

Call `getJiraIssue` with `fields: ["*all", "comment"]` and `responseContentFormat: "markdown"`.
Read the **entire** comment thread in order, not just the description — later comments frequently
change the picture: a ticket gets reassigned between teams, refinement discussions narrow down a
fix approach, or a "let's investigate X" comment gets superseded by "actually it's Y" a few
comments later. The most recent comments carry the most current understanding; don't anchor only on
the original report.

Note the parent epic key and any `issuelinks` (duplicates, relates-to, blocks) — you'll check these
in Step 5, but don't chase them yet.

## Step 3 — Establish the comment style to write in

If the user gave a reference ticket/comment, fetch it the same way and study its exact shape:
does it open with a specific emoji-shortcode or label, what section headers does it use and in what
order, does it use inline code snippets, how does it phrase proposed fixes (numbered options with
tradeoffs? a single recommendation?). Mirror that precisely — the point of giving you a reference is
so the output feels like the same author wrote it, not a generic bot template.

If no reference was given, fall back to the structure in `references/default-template.md`. Either
way, the actual content (Step 9) still has to be earned through investigation — the template only
governs shape, not substance.

## Step 4 — Scope the codebase(s) to investigate

If the user already named the repo(s), use them. Otherwise, figure out what's in scope before
guessing blindly:

- Check whether you're already working inside a relevant repo (current directory, or a workspace
  documented in a top-level `CLAUDE.md`/`README` that maps products/teams to repos).
- If the ticket's product area suggests a codebase you can identify with reasonable confidence, say
  so and proceed — but if it's genuinely ambiguous (e.g. a multi-repo organization and no strong
  signal which service owns this behavior), ask the user rather than spending a long investigation
  on the wrong repo.

## Step 5 — Cross-reference related tickets

Search for tickets that might carry extra context: siblings under the same parent epic, and a
keyword/JQL search on the summary. Two things to watch for:

- **`searchJiraIssuesUsingJql` results are often huge** and can exceed the tool's token limit,
  in which case the result gets saved to a file instead of returned inline. When that happens, use
  `jq` on that file rather than trying to `Read` it directly — pull out just `key`/`summary`/`status`
  first to scan for candidates before fetching anything in full.
- **A shared epic or matching keyword is a lead, not a conclusion.** Actually read anything you
  find before citing it. It's common for a ticket to live under the same epic as your target purely
  because of product-area grouping, with zero bearing on this specific bug — treating it as related
  without checking wastes the reader's time and can misdirect the fix.

This step and Step 6 don't depend on each other — run them concurrently rather than back to back.

## Step 6 — Investigate the codebase

Delegate this to one or more background `Agent` calls (Explore or general-purpose) rather than
digging through the repo yourself inline — it keeps your context focused on synthesis and lets you
run it in parallel with Step 5. See `references/investigation-subagent-prompt.md` for a full example
of a prompt that gets good results: it briefs the agent on the user-visible symptom in plain terms,
names specific classes/patterns to look for if you already have hints (e.g. from a related ticket's
service ownership), and asks explicitly for file paths + line numbers + actual code/config snippets,
not summaries.

What you want back, concretely:
- The full call path for the affected behavior (e.g. controller → service → data-access layer).
- Any config values that bound the behavior (timeouts, batch sizes, feature flags).
- Whether the current implementation has an evident gap explaining the symptom (missing check,
  missing index, unbounded query, race condition) — not just "here's the relevant code," but a
  stated hypothesis for *why* it produces the reported symptom.
- Git history/blame for recent, relevant changes — a ticket number referenced in a commit message
  near the affected code is often the single best clue for why current behavior exists.

If the feature spans a backend and a frontend (or multiple services), it's fine to run one agent per
codebase in parallel — just make sure each one gets enough of the user-facing symptom to search
usefully; don't just hand them a file path and hope.

## Step 7 — Corroborate with Grafana, if it's actually going to help

Before querying anything, check the ticket's age against your log/trace retention window (commonly
somewhere in the 14–30 day range for hosted logging/tracing backends — check what applies to your
setup if unsure). If the reported incident is older than that, log lookups will almost certainly
come back empty — skip this step and don't waste a round trip. It's only worth doing for
still-relevant or recurring issues where current data could confirm or refute a hypothesis (e.g. an
ongoing elevated error rate, a currently-slow endpoint you can trace).

When it is worth doing: use the `mcp__grafana__*` tools (`query_loki_logs`, `query_prometheus`,
`tempo_traceql-search`, etc. — `list_datasources` first if you don't already know the relevant
datasource UID) to look for the specific error, timeout, or pattern described in the ticket. Treat
this as corroborating evidence for a hypothesis you already have from the code, not a
starting point — you should already know what you're looking for before you query.

## Step 8 — Verify before you trust the investigation

This is the step that keeps the analysis honest. A subagent's report is a *claim*, not a fact —
it can misstate a line number, paraphrase code loosely, or miss that a config value it found isn't
actually the one wired up to this code path. Before drafting anything:

- Take the 2-3 highest-confidence claims underpinning your root-cause conclusion (usually: the
  specific code that's missing/wrong, and any config value you're citing) and check them yourself
  with `Read` or `grep` on the actual file. Confirm the line number, confirm the surrounding logic
  actually says what was reported.
- If a claim doesn't hold up on inspection, don't just drop it — figure out what's actually true and
  adjust the conclusion. A confidently-wrong root cause is worse than an admittedly-incomplete one.
- Only quote code snippets or cite file:line references in the final comment that you've personally
  confirmed in this step — don't relay a subagent's snippet unverified.

## Step 9 — Draft the analysis

Structure per Step 3 (mirrored reference, or `references/default-template.md`). Regardless of exact
headers used, the content needs to cover:

1. **What's happening** — the mechanism behind the user-visible symptom, in plain terms tied back
   to what was reported.
2. **Root cause** — the specific, verified code path/config/data condition, with real file paths
   and (where it clarifies things) an actual code snippet.
3. **Why it's specific to the reported conditions**, if relevant — e.g. why this particular
   customer/input/timing triggers it when others don't.
4. **Proposed fix(es)** — at least two options where reasonable, each with its tradeoff, plus a
   recommendation if you have one. If there's genuinely only one sane fix, say so rather than
   padding with a strawman alternative.

## Step 10 — Post (or hold, for dry-run)

If `--dry-run` was requested: write the finished comment to a file (report the path) and show it in
the conversation instead of posting. Do not call `addCommentToJiraIssue`.

Otherwise, post it now via `addCommentToJiraIssue` with `contentFormat: "markdown"`. Don't add a
separate "should I post this?" checkpoint — Step 8 is what earns the right to post automatically.

## Hard constraints

- Never cite a file path, line number, code snippet, or config value in the final comment that
  wasn't personally confirmed in Step 8 — subagent reports are leads, not citations.
- Never call `addCommentToJiraIssue` when `--dry-run` is set, no matter how confident the analysis is.
- Never treat a shared parent epic or a keyword match as proof two tickets are related — open and
  read anything before citing it as context.
- Never `Read` a saved large-JQL-result file wholesale — use `jq` to extract what you need, or
  delegate the search/scan to a subagent so the raw payload doesn't land in your own context.
- Skip Grafana/observability lookups for incidents clearly outside your retention window — an empty
  query result from a stale time range isn't informative, it's just noise.
