---
name: triage-work-item
description: >
  Triages a tracker work item — a bug, task, or story — end-to-end against the codebase: reads the
  item (description, full comment/discussion thread, linked items, parent epic), cross-references
  related items, investigates the actual codebase(s) that implement the affected feature, optionally
  corroborates with an observability platform (logs/traces/metrics), then posts a verified analysis
  comment — root cause for a bug, or current-behavior/approach/effort for a change request — back to
  the item. Works against Jira or GitHub Issues as the tracker
  and Grafana or AWS CloudWatch for observability through per-tool adapter files. TRIGGER when the
  user gives a work-item URL or key — Jira (`…atlassian.net/browse/KEY`) or GitHub
  (`github.com/<o>/<r>/issues/<n>`) — and asks to triage, investigate, diagnose, root-cause, or
  "figure out what's going on with" it, especially when they also want an analysis comment posted
  back — even if they don't say "triage" explicitly (e.g. "can you look into TICKET-123 and post what
  you find", "why is this happening, check the code"). Do not use this for simply reading or
  summarizing a work item with no code investigation intended, and do not use it for writing new
  work items.
argument-hint: "<work-item URL or key> [--dry-run]"
allowed-tools: [Read, Bash, Agent, ToolSearch, AskUserQuestion, Write]
---

# Triage a tracker work item against the codebase and observability data

Throughout this skill "work item" is the generic term for whatever the tracker holds — a bug, task, or story (Jira and GitHub both call the object an "issue," and the steps below keep that word when naming the concrete object or an API/CLI call).

This is an investigation workflow, not a lookup. The value it adds over just reading the work item is a verified conclusion — a specific code path, config value, or data condition for a bug; a validated approach and effort estimate for a change request — that a future engineer can act on immediately, backed by evidence you actually checked rather than plausible-sounding guesses. Every step below exists to either gather that evidence or to guard against reporting something that sounds right but isn't.

The workflow is tool-agnostic; the tracker-specific and observability-specific mechanics live in adapter files under `references/` and load only when you reach the step that needs them. This keeps the always-loaded body focused on judgment — the part that's the same whether the work item lives in Jira or GitHub and whether the telemetry is in Grafana or CloudWatch.

By default, once you've verified your findings, post the comment — don't pause for a separate approval step. The verification step (Step 9) is the safety gate, not a human checkpoint. The one exception is `--dry-run`: if the user passes it (or clearly wants to see the analysis before anything goes out), write the finished comment to a file and show it instead of posting.

## Inputs

- **Required**: an issue URL or key. If given a bare key (e.g. `PROJ-123`) you also need enough to identify the tracker and instance — ask if it isn't obvious from context (a prior message, a hostname already visible, the repo you're standing in).
- **Optional**: which repo(s)/codebase(s) to investigate. If not given, see Step 5.
- **Optional**: `--dry-run` — draft only, never post.

## Step 1 — Identify the tracker and load its adapter

Determine which tracker the issue lives in, primarily from the URL shape:

- `…atlassian.net/browse/<KEY>` or a bare `PROJ-123` key → Jira → read `references/trackers/jira.md`
- `github.com/<owner>/<repo>/issues/<n>` → GitHub Issues → read `references/trackers/github.md`

The adapter file is the authority for that tracker's mechanics: how to load or authenticate its tools, the exact call to fetch an issue with its full comment thread, how to search related issues, how to post a comment, and its comment markup dialect and known gotchas. Read it now and follow it wherever a later step says "per the tracker adapter."

If there's no adapter file for the tracker you're facing, degrade gracefully rather than stopping: discover the relevant tools with a keyword `ToolSearch` (or the platform's own CLI/API), confirm the fetch/search/comment operations you need exist, and proceed. Tell the user you're running without a dedicated adapter so they know citations of tool-specific behavior are best-effort. If the run goes well, that's a signal the tracker earns its own adapter file.

## Step 2 — Fetch the target issue in full

Using the fetch call from the tracker adapter, retrieve the issue with its **entire** comment/discussion thread, in order — not just the description. Later comments frequently change the picture: an issue gets reassigned between teams, refinement discussions narrow down a fix approach, or a "let's investigate X" comment gets superseded by "actually it's Y" a few comments later. The most recent comments carry the most current understanding; don't anchor only on the original report.

Note the parent epic/tracking issue and any linked issues (duplicates, relates-to, blocks) — you'll check these in Step 6, but don't chase them yet.

## Step 3 — Classify the item and establish the comment template

Determine whether this is a **bug** — actual behavior deviates from what the system is intended or documented to do — or a **change request** — the system does what it was built to do, but the desired behavior itself is changing (new/changed behavior), or the work is non-behavioral (refactor, chore, tech debt, spike) with no behavior at stake either way.

Use two signals together, not the tracker's issue-type field alone:

- **Tracker issue type** (Bug vs. Story/Task/Feature) as a starting signal.
- **Content-level test**: does the description/comments say the system fails to do what it's supposed to (a promise it breaks), or that it should now do something different from what it was built to do? The first is a bug; the second is a change request.

When the two disagree — e.g. the issue type is "Story" or "Task" but the content describes broken existing behavior — **the content wins**. Issue-type fields are routinely misused for workflow reasons (a team files a regression as a "Task," or a "Story" is really "fix this"); treat the field as a hint, not the source of truth. Mention the override in the comment only if it's material to how the investigation was framed — don't call out a trivial mismatch.

Non-behavioral tasks (refactor, chore, tech debt, spike) default to the change-request template: effort and approach are exactly what's needed there, and neither "root cause" nor "how it works today vs. what's wrong" fits a pure refactor cleanly enough to force the bug shape.

If the item is too sparse to classify with confidence (e.g. a one-line title, no description, no comments), ask the user (`AskUserQuestion`) rather than guessing — a wrong template choice compounds through the rest of the workflow.

Once classified:

- **Bug** → use `references/bug-template.md`.
- **Change request** (including non-behavioral tasks) → use `references/change-request-template.md`.

Open the comment with an attribution line — `Triaged with 🤖 using <model> (<effort> effort)` — see the chosen template's notes for exactly how to fill in `<model>`/`<effort>`.

## Step 4 — Note the tracker's comment markup dialect

Different trackers render comments differently: Jira via its own wiki/ADF markup (though its comment API accepts Markdown and converts it), GitHub via GitHub-flavored Markdown. The tracker adapter states which dialect to write in and how the post call expects it. Keep this in mind while drafting (Step 10) so code fences, headings, and links render rather than showing as literal characters.

## Step 5 — Scope the codebase(s) to investigate

If the user already named the repo(s), use them. Otherwise, figure out what's in scope before guessing blindly:

- Check whether you're already working inside a relevant repo (current directory, or a workspace documented in a top-level `CLAUDE.md`/`README` that maps products/teams to repos).
- If the issue's product area suggests a codebase you can identify with reasonable confidence, say so and proceed — but if it's genuinely ambiguous (e.g. a multi-repo organization and no strong signal which service owns this behavior), ask the user rather than spending a long investigation on the wrong repo.

This step investigates a **local checkout** with Read/Grep/git — it does not call the git host's API, so it's the same regardless of whether the repo is hosted on GitHub, GitLab, or Bitbucket.

**Before investigating, make sure each repo is current.** These are locally cloned working copies
that can silently drift behind their remote — and a stale checkout doesn't fail loudly, it produces
a *confidently wrong negative*: a subagent searching a checkout that's missing the very commit that
implements the feature will report "no such code exists anywhere," which reads identically to a
genuine gap and can send the whole investigation toward the wrong repo entirely. For each repo in
scope, before dispatching Step 7 agents against it:

- `git fetch origin && git log HEAD..origin/<default-branch> --oneline` to check if you're behind.
- If behind and `git status` shows a clean working tree, fast-forward: `git pull --ff-only`.
- If there are local uncommitted changes you don't want to disturb, investigate against a worktree
  of the fresh default branch instead of touching the existing checkout (`git worktree add` or the
  `EnterWorktree` tool if available) rather than stashing someone's in-progress work.

## Step 6 — Cross-reference related issues

Search for issues that might carry extra context: siblings under the same parent epic/tracking issue, and a keyword search on the summary. The exact search call and its result-handling quirks are in the tracker adapter (some trackers return large result sets that spill to a file and need `jq` rather than a direct `Read`). Two things to watch for regardless of tracker:

- **A shared epic or matching keyword is a lead, not a conclusion.** Actually read anything you find before citing it. It's common for an issue to live under the same epic as your target purely because of product-area grouping, with zero bearing on this specific bug — treating it as related without checking wastes the reader's time and can misdirect the fix.
- **Keep large search payloads out of your context.** If a search spills to a file, extract just `key`/`summary`/`status` (via `jq` or a subagent) to scan for candidates before fetching anything in full.

This step and Step 7 don't depend on each other — run them concurrently rather than back to back.

## Step 7 — Investigate the codebase

Delegate this to one or more background `Agent` calls (Explore or general-purpose) rather than digging through the repo yourself inline — it keeps your context focused on synthesis and lets you run it in parallel with Step 6. See `references/investigation-subagent-prompt.md` for a full example of a prompt that gets good results: it briefs the agent on the user-visible symptom in plain terms, names specific classes/patterns to look for if you already have hints (e.g. from a related issue's service ownership), and asks explicitly for file paths + line numbers + actual code/config snippets, not summaries.

What you want back, concretely:
- The full call path for the affected behavior (e.g. controller → service → data-access layer).
- Any config values that bound the behavior (timeouts, batch sizes, feature flags).
- **For a bug**: whether the current implementation has an evident gap explaining the symptom (missing check, missing index, unbounded query, race condition) — not just "here's the relevant code," but a stated hypothesis for *why* it produces the reported symptom.
- **For a change request**: how the current implementation actually works today (the mechanism the change needs to modify or extend), and a candidate approach for making the change — what would need to move, plus any complicating factors (data migration, backward compatibility, affected callers).
- Git history/blame for recent, relevant changes — an issue number referenced in a commit message near the affected code is often the single best clue for why current behavior exists.

If the feature spans a backend and a frontend (or multiple services), it's fine to run one agent per codebase in parallel — just make sure each one gets enough of the user-facing symptom to search usefully; don't just hand them a file path and hope.

## Step 8 — Corroborate with observability data, if it's actually going to help

If no observability platform is configured or reachable, skip this step — the code investigation stands on its own. When one is available, its mechanics (which tools/CLI, how to pick a datasource, the query languages for logs/metrics/traces) live in an observability adapter: read `references/observability/grafana.md`, `references/observability/cloudwatch.md`, or the file matching your platform. If there's no adapter for your platform, discover the tools with `ToolSearch` and proceed best-effort, same as Step 1.

Before querying anything, check the issue's age against your log/trace retention window (commonly somewhere in the 14–30 day range for hosted logging/tracing backends — the adapter notes the platform's default if known). If the reported incident is older than that, log lookups will almost certainly come back empty — skip and don't waste a round trip. It's only worth doing for still-relevant or recurring issues where current data could confirm or refute a hypothesis (e.g. an ongoing elevated error rate, a currently-slow endpoint you can trace).

Treat this as corroborating evidence for a hypothesis you already have from the code, not a starting point — you should already know what you're looking for before you query. For a change request, this can also serve as baseline evidence for the "How it works today" section (e.g. current latency or error-rate numbers) rather than confirming a failure hypothesis.

## Step 9 — Verify before you trust the investigation

This is the step that keeps the analysis honest. A subagent's report is a *claim*, not a fact — it can misstate a line number, paraphrase code loosely, or miss that a config value it found isn't actually the one wired up to this code path. Before drafting anything:

- Take the 2-3 highest-confidence claims underpinning your conclusion — for a bug, the root cause (the specific code that's missing/wrong, and any config value you're citing); for a change request, your description of how the current behavior works and any claim about what the proposed approach requires — and check them yourself with `Read` or `grep` on the actual file. Confirm the line number, confirm the surrounding logic actually says what was reported.
- Give extra scrutiny to *negative* claims specifically ("this repo has no code related to X", "no caller of this endpoint exists"). A negative finding is much more often the product of a stale local checkout (see Step 5) than an accurate absence — if you didn't personally confirm that repo's checkout was up to date with its remote before the subagent searched it, do that check now before accepting the conclusion.
- If a claim doesn't hold up on inspection, don't just drop it — figure out what's actually true and adjust the conclusion. A confidently-wrong root cause is worse than an admittedly-incomplete one.
- Only quote code snippets or cite file:line references in the final comment that you've personally confirmed in this step — don't relay a subagent's snippet unverified.

## Step 10 — Draft the analysis

Structure per the template chosen in Step 3 (`references/bug-template.md` or `references/change-request-template.md`), in the markup dialect from Step 4.

**For a bug**, regardless of exact headers used, the content needs to cover:

1. **What's happening** — the mechanism behind the user-visible symptom, in plain terms tied back to what was reported.
2. **Root cause** — the specific, verified code path/config/data condition, with real file paths and (where it clarifies things) an actual code snippet.
3. **Why it's specific to the reported conditions**, if relevant — e.g. why this particular customer/input/timing triggers it when others don't.
4. **Proposed fix(es)** — at least two options where reasonable, each with its tradeoff, plus a recommendation if you have one. If there's genuinely only one sane fix, say so rather than padding with a strawman alternative.

**For a change request** (including non-behavioral tasks), the content needs to cover:

1. **How it works today** — the current mechanism/behavior, or (for non-behavioral work) the current state driving the request.
2. **What should change** — the concrete new/changed behavior, or concrete engineering outcome, stated precisely enough that "done" is unambiguous.
3. **Proposed approach** — a candidate implementation path naming the code that would need to change; at least two options where there's a genuine choice, each with its tradeoff, plus a recommendation if you have one.
4. **Risks / open questions**, if relevant — data migration, backward compatibility, affected callers, decisions needing a stakeholder.
5. **Rough effort** — small / medium / large, with a one-line reason tied to what the approach actually touches.

## Step 11 — Post (or hold, for dry-run)

If `--dry-run` was requested: write the finished comment to a file (report the path) and show it in the conversation instead of posting. Do not call any post-comment operation.

Otherwise, post it now via the comment call from the tracker adapter, in that tracker's expected markup. Don't add a separate "should I post this?" checkpoint — Step 9 is what earns the right to post automatically.

**If you later discover a comment you already posted was wrong** (e.g. it was built on a stale
checkout, or a claim didn't survive re-verification), post a new comment that explicitly says it
supersedes the previous one and explains what changed and why. Don't silently edit or delete the
earlier comment — readers who already saw it need the correction to be visible, and the trail of
"here's what I thought, here's what was actually true" is itself useful signal.

## Hard constraints

- Never cite a file path, line number, code snippet, or config value in the final comment that wasn't personally confirmed in Step 9 — subagent reports are leads, not citations.
- Never post a comment when `--dry-run` is set, no matter how confident the analysis is.
- Never treat a shared parent epic or a keyword match as proof two issues are related — open and read anything before citing it as context.
- Never let a large search-result payload land in your own context wholesale — extract what you need with `jq`, or delegate the search/scan to a subagent.
- Skip observability lookups for incidents clearly outside your retention window — an empty query result from a stale time range isn't informative, it's just noise.
- When running without an adapter for a tracker or platform, say so — don't present best-effort tool behavior as if it were verified.
- Never accept a subagent's "no relevant code found" conclusion for a repo without first confirming
  that repo's local checkout is current with its remote (Step 5) — a stale checkout produces exactly
  this failure mode, and it looks identical to a genuine absence until you check.
- Don't assume a tracker's markdown renderer expands emoji shortcodes the way Slack/GitHub-flavored
  markdown does — the tracker adapter notes any rendering quirks (e.g. Jira does not expand
  shortcodes, see `references/trackers/jira.md`); use the literal Unicode emoji if unsure.
- Every posted comment opens with the `Triaged with 🤖 using <model> (<effort> effort)` attribution
  line (model always filled in, effort only when concretely known) — don't drop it.
- Never draft against the wrong template — a change request has no root cause to report, and
  forcing the bug template's language onto it produces a hollow "root cause: N/A" section. Classify
  first (Step 3) and use the matching template.
- When the tracker's issue-type field and the content-level test disagree, follow the content: a
  "Story" or "Task" reporting broken existing behavior is a bug, and a "Bug" whose content actually
  asks for different behavior is a change request.
