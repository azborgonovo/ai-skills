---
name: triage-work-item
description: >
  Triages a tracker work item, which is a bug, a task, or a story, end-to-end against the codebase.
  It reads the item with its full comment thread, links, and parent epic, cross-references related
  items, investigates the codebases behind the affected feature, corroborates with attached evidence
  and observability data, then posts a verified analysis comment back to the item. That comment gives
  the root cause for a bug, or the current behavior, the approach, and the effort for a change
  request. Ships with Jira and GitHub Issues tracker adapters, plus Grafana and CloudWatch
  observability adapters, and degrades to any reachable platform. Use when the user gives a
  work-item URL or key, on Jira (`…atlassian.net/browse/KEY`) or GitHub
  (`github.com/<o>/<r>/issues/<n>`), and asks to triage, investigate, diagnose, or root-cause it,
  even without the word "triage", as in "look into TICKET-123 and post what you find". Do not use it
  to read or summarize a work item with no code investigation, or to write new work items.
argument-hint: "<work-item URL or key> [--dry-run]"
allowed-tools: [Read, Grep, Bash, Agent, ToolSearch, AskUserQuestion, Write]
---

# Triage a tracker work item against the codebase and observability data

In this skill, "work item" is the generic term for a bug, a task, or a story. Jira and GitHub both call the object an "issue". The steps keep that word for the concrete object, an API call, or a CLI call.

The goal is a verified conclusion that a future engineer can act on immediately, backed by evidence that you checked. For a bug, that is a specific code path, configuration value, or data condition. For a change request, it is a validated approach and an effort estimate.

Tracker and observability mechanics live in adapter files under `references/`. Read each one only when you reach the step that needs it.

## Inputs

- **Required**: an issue URL or key. A bare key such as `PROJ-123` does not identify the tracker and the instance. Ask when the context does not make them obvious. The context can be a prior message, a visible hostname, or the repo you are standing in.
- **Optional**: which repos to investigate. When the user names none, see Step 5.
- **Optional**: `--dry-run`, which drafts the comment and never posts it. Treat a clear wish to see the analysis before anything goes out as a dry run too.

## Step 1: Identify the tracker and load its adapter

- A `…atlassian.net/browse/<KEY>` URL, or a bare `PROJ-123` key, is Jira. Read `references/trackers/jira.md`.
- A `github.com/<owner>/<repo>/issues/<n>` URL is GitHub Issues. Read `references/trackers/github.md`.

The adapter is the authority for that tracker: tool loading, the fetch, search, and comment calls, attachments, the markup dialect, and known gotchas. Follow it wherever a later step says "per the tracker adapter".

When no adapter exists for the tracker, degrade instead of stopping. Discover the tools with a keyword `ToolSearch`, or use the platform's CLI or API. Make sure that the fetch, search, and comment operations exist, then proceed. Tell the user that you run without a dedicated adapter, so any tool-specific behavior is best-effort.

## Step 2: Fetch the target issue in full

Use the fetch call from the tracker adapter. Retrieve the **entire** comment thread in order, and not the description alone. A later comment often changes the picture, for example a reassignment or "actually it is Y". The most recent comments carry the most current understanding.

Note the parent epic or tracking issue, and any linked issue. You check these in Step 6, so do not chase them yet.

**List the attachments in the same pass**, even when nothing in the thread points at one. Capture the filename, the type, the size, and the upload date. An attachment, such as a HAR file or a log export, often settles in one read what code can only narrow down. A default fetch often leaves attachments out, so a response with no attachment data is not evidence that none exist. The tracker adapter covers how to list and download them.

**Trust the file list over what the thread says about it.** A description that reads "waiting on the HAR file" can predate the upload by weeks. Compare the upload dates against the dates in the thread.

## Step 3: Classify the item and establish the comment template

Determine whether the item is a **bug** or a **change request**. In a bug, the actual behavior deviates from what the system is intended or documented to do. In a change request, the desired behavior itself changes. A change request also covers non-behavioral work, such as a refactor, a chore, tech debt, or a spike.

Use two signals together:

- **The tracker issue type**, which is Bug against Story, Task, or Feature. It is a starting hint only.
- **The content-level test.** When the description and comments say that the system breaks a promise, it is a bug. When they say that the system must now do something different, it is a change request.

When the two signals disagree, **the content wins**, because teams often misuse issue-type fields for workflow reasons. Mention the override in the comment only when it is material to how you framed the investigation.

A non-behavioral task uses the change-request template, because it needs effort and approach, not a root cause. When the item is too sparse to classify, such as a bare one-line title, ask the user through `AskUserQuestion` instead of guessing.

- For a **bug**, use `references/bug-template.md`.
- For a **change request**, use `references/change-request-template.md`.

Open the comment with the attribution line `Triaged with 🤖 using <model> (<effort> effort)`, so readers calibrate their trust. Never drop it. Always fill in `<model>` from your environment context, such as `Sonnet 5`. Fill in `<effort>` only when the session has a concretely known effort or thinking-level setting. Otherwise drop the whole parenthetical, which gives `Triaged with 🤖 using Sonnet 5:`. Use the literal Unicode 🤖, because some trackers, Jira among them, render a `:robot:` shortcode as literal text.

## Step 4: Note the tracker's comment markup dialect

The tracker adapter states which markup dialect to write in, and how the post call expects it. Draft in that dialect in Step 10, so that code fences, headings, and links render.

## Step 5: Scope the codebases to investigate

When the user named the repos, use them. Otherwise:

- Check whether the current directory is a relevant repo, and check any workspace map in a top-level `CLAUDE.md` or `README`.
- When the product area points at a codebase with reasonable confidence, say so and proceed. When the choice is genuinely ambiguous, ask the user. A question costs less than a long investigation on the wrong repo.

The investigation reads a **local checkout** through Read, Grep, and git, so it works the same for any git host.

**Make sure that each repo is current before you dispatch the Step 7 agents against it.** A stale checkout produces a confidently wrong negative: "no such code exists anywhere" reads exactly like a genuine gap, and it can send the investigation to the wrong repo.

- Run `git fetch origin && git log HEAD..origin/<default-branch> --oneline` to find out whether the checkout is behind.
- When it is behind and `git status` shows a clean working tree, run `git pull --ff-only`.
- When uncommitted changes exist, leave the checkout alone and investigate a worktree of the fresh default branch, through `git worktree add` or the `EnterWorktree` tool. Do not stash someone else's work.

## Step 6: Cross-reference related issues

Search the siblings under the same parent epic or tracking issue, and run a keyword search on the summary. The search call and its result handling live in the tracker adapter.

- **A shared epic or a matching keyword is a lead, not a conclusion.** Read an issue before you cite it. Many issues share an epic purely through product-area grouping.
- **Keep a large search payload out of your context.** When a search spills to a file, extract only `key`, `summary`, and `status` through `jq` or a subagent. Scan those before you fetch anything in full.

Run this step concurrently with Step 7.

## Step 7: Investigate the codebase

Delegate this step to one or more background `Agent` calls, Explore or general-purpose, instead of digging through the repo inline. That keeps your context on synthesis and lets Step 6 run in parallel. Brief each agent per `references/investigation-subagent-prompt.md`.

Ask for this back:

- The full call path for the affected behavior, such as controller to service to data-access layer.
- Any configuration value that bounds the behavior, such as a timeout, a batch size, or a feature flag.
- **For a bug**: a stated hypothesis about *why* the code produces the symptom, such as a missing check, a missing index, an unbounded query, or a race condition.
- **For a change request**: how the current mechanism works, plus a candidate approach. The approach names what has to move, and any complication, such as a data migration or affected callers.
- Git history and blame for recent relevant changes. An issue number in a commit message near the code is often the best clue to why the behavior exists.

When the feature spans several codebases, run one agent per codebase in parallel.

## Step 8: Corroborate with runtime evidence

There are two sources, and they age in opposite ways: the files attached to the issue, and whatever the observability platform still retains.

**Take the attachments first**, before Step 7 or alongside it, and not after. An attachment never ages out, and for an old issue it is often the only runtime evidence left. A decisive attachment reshapes the hypothesis that the code investigation tests. `references/attached-evidence.md` covers how to read these files without flooding your context.

### Observability data, when it will actually help

When no observability platform is reachable, skip this part. Otherwise read the matching adapter, `references/observability/grafana.md` or `references/observability/cloudwatch.md`. When no adapter exists for the platform, discover the tools with `ToolSearch` and proceed best-effort, as in Step 1.

Before you query, compare the age of the issue against the retention window. A hosted log or trace backend commonly retains 14 to 30 days, and the adapter notes the platform default. When the incident is older than the window, skip the lookup. A query earns its round trip for a still-relevant or recurring issue, such as an ongoing high error rate or a currently slow endpoint.

Query only to corroborate a hypothesis that the code already gave you, and know what you look for before you query. For a change request, current latency and error-rate numbers can serve as the baseline for "How it works today".

## Step 9: Verify before you trust the investigation

A subagent's report is a *claim*, not a fact. It can misstate a line number, paraphrase code loosely, or cite a configuration value that is not wired to this code path. Before you draft:

- Check the two or three claims that hold up your conclusion yourself, with `Read` or `grep` on the actual file. For a bug, that is the root cause plus any cited configuration value. For a change request, that is how the current behavior works plus what the approach requires. Confirm the line number and the surrounding logic.
- Give extra scrutiny to a *negative* claim, such as "no caller of this endpoint exists". When you skipped the Step 5 freshness check for that repo, run it now.
- When a claim does not hold up, work out what is actually true and adjust the conclusion. A confidently wrong root cause is worse than an admittedly incomplete one.
- Quote a snippet or cite a `file:line` in the comment only when you confirmed it in this step.

## Step 10: Draft the analysis

Read the template chosen in Step 3 before you draft, and cover every section that it marks as required. Write in the tracker's markup dialect from Step 4.

### Keep it tight

A thorough investigation does not need a long comment. Size each section by what the reader needs, not by how much you found:

- **Cite the strongest evidence for a point once.** When several sources confirm one fact, cite the most direct one.
- **Name each file and line once.** Do not close with a list of "files touched" that the sections already named.
- **Match depth to merit, not to symmetry.** Give the clear pick the fuller explanation, and dispatch a weaker alternative in one clause.
- **Show one snippet for a repeated gap.** When the same gap sits in several files, quote one and cite the rest by `file:line`.
- **Quote the shortest excerpt that carries the argument.** Trim a log trace, a request timeline, or a payload to the fields that do the work.
- **Describe an artifact or show it, and not both.** Include the artifact only when the reader must recognize it or act on its exact contents.

A section can run long when the substance needs it, such as a root cause with several interacting factors. Keep it to one tight paragraph even then, with no bulleted sub-structure.

**The test before you post**: read the draft as one message to a colleague who must act on it today. Cut every sentence that does not change what they do. The summary that you give the user in the conversation is a good length calibration. When the comment runs markedly longer, the excess is nearly always transcript: evidence quoted twice, a restated conclusion, or the path you took instead of the finding.

**Posting a follow-up comment**: link or name the earlier comment, and give only what changed. That is the new evidence, and which earlier conclusions it confirms, sharpens, or kills. A correction is different, see Step 11.

### Write it in plain English

The reader is often not the author of the code, and sometimes not an engineer. Write short sentences in the active voice, define a term that such a reader can miss at its first use, and cut filler. Keep every verified `file:line` citation, code snippet, and quoted log line exactly as it is, because a reworded quote is no longer evidence.

Make a cited commit reachable. Derive the repo's web URL from `git remote get-url origin`, and write a markdown link with readable text, such as "the batch-size cap raised in abc1234". When the remote resolves to no web URL, write the short SHA plus the commit subject. The tracker adapter records whether the tracker links a bare SHA.

Where plain English pulls against the length test, the length test wins. When a plain-English writing skill such as `simple-english` is available, apply it to the draft before Step 11.

## Step 11: Post the comment, or hold it for a dry run

For a dry run, write the finished comment to a file, report the path, and show the comment in the conversation. Call no post-comment operation.

Otherwise, post the comment through the tracker adapter's comment call, with no separate approval checkpoint. The Step 9 verification is the safety gate.

**If a comment you already posted turns out wrong**, post a new comment that says explicitly that it supersedes the previous one. A stale checkout is a common cause. Explain what changed and why. Never edit or delete the earlier comment, because readers who saw it need the correction to be visible.
