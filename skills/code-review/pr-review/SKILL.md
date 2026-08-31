---
name: pr-review
description: >
  Reviews a merge/pull request against its linked work item, then publishes the findings as inline
  comments on the diff and records the verdict on the change — it fetches the change and work-item
  context, isolates the change locally, delegates the review itself to the review-changes skill,
  posts each finding, and approves or requests changes according to that verdict. Ships with adapters
  for GitLab and GitHub as the code host, and Jira and GitHub Issues as the tracker, but degrades
  gracefully to any other host or tracker reachable via tool discovery. User-only: runs only when
  explicitly invoked with /pr-review <MR or PR URL>. When the user wants to review a GitLab MR or
  GitHub PR, code-review a merge/pull request, or evaluate a change's diff against its linked work
  item, suggest running this command rather than doing a manual review.
argument-hint: "<merge/pull request URL> [draft|comments-only]"
allowed-tools: [Read, Bash, Skill, Write, Glob, Grep, ToolSearch]
disable-model-invocation: true
---

# PR/MR Review

Review of a merge or pull request that lands on the change itself: inline comments the author can see, and the verdict recorded as an approval or a request for changes.

## What this skill owns

The reviewing itself belongs to the [review-changes](../review-changes/SKILL.md) skill: it reviews the diff between `HEAD` and a fixed point across the Code Review Pyramid, checks the change against its spec and the repo's own documented standards, splits findings into blocking and non-blocking, and resolves them into one verdict. None of that judgment is restated here — this skill supplies the four things review-changes can't reach from a URL alone:

- resolving the change and its work item, through host and tracker adapters
- isolating the change locally, so the review reads real files at the change's exact head SHA
- rendering the resulting findings as inline comments anchored to the diff
- turning the verdict into the host's own approve / request-changes action

Throughout, "change" is the generic term for what the host calls a merge request (GitLab) or pull request (GitHub, Bitbucket), and "work item" the generic term for whatever the tracker holds (a Jira issue, a GitHub issue). The host- and tracker-specific mechanics live in adapter files under `references/` and load only when you reach the step that needs them, so the always-loaded body stays host-agnostic.

## Modes

The word after the URL chooses how much of the review lands on the change. With no word, both do.

| Invocation | Comments | Verdict |
|---|---|---|
| `/pr-review <url>` | published directly | Approved or Approved with suggestions → **approve**; Request changes → **request changes** |
| `/pr-review <url> comments-only` | published directly | reported in the conversation only |
| `/pr-review <url> draft` | drafts for the user to submit | reported in the conversation only |

**Self-authored changes**: both hosts reject a verdict from the change's own author, so Step 2 compares the author against the authenticated user and drops to `comments-only` when they match. Say so in Step 8's output — the verdict is still worth reading, it just can't be recorded.

## Workflow

### Step 1 — Identify the host and load its adapter

Determine which host the change lives on, primarily from the URL shape:

- `…/-/merge_requests/<n>` → GitLab → read `references/hosts/gitlab.md`
- `github.com/<owner>/<repo>/pull/<n>` → GitHub → read `references/hosts/github.md`

The adapter file is the authority for that host's mechanics: URL parsing, auth check, the exact calls to fetch metadata and diffs, the local-clone path shape, how to post comments in either mode, how to record a verdict, and that host's own gotchas. Read it now and follow it wherever a later step says "per the host adapter."

If there's no adapter file for the host you're facing, degrade gracefully rather than stopping: discover the relevant tools with a keyword `ToolSearch` (or the platform's own CLI/API), confirm the fetch-metadata/fetch-diff/post-comment operations you need exist, and proceed in `comments-only` mode — recording a verdict through an interface you haven't verified is the one part not worth improvising. Tell the user you're running without a dedicated adapter so they know host-specific behavior is best-effort.

### Step 2 — Fetch change metadata

Using the metadata call from the host adapter, fetch the change's title, description, author, source/target branch, the SHAs needed for inline comment positions, its checks/pipeline status, and its web URL.

Compare the author against the authenticated user (the adapter names both calls). On a match, the run is a self-review: switch to `comments-only` for the rest of the workflow.

**If the metadata call fails with an auth error** (401, or a "not logged in" message), the host adapter's CLI/tool isn't authenticated — stop and ask the user to authenticate (the adapter states the exact command), rather than pre-checking auth separately. A success here also proves auth is good for posting in Step 6, since it's the same credentials.

### Step 3 — Resolve the work item and save it as the spec

Scan the title and description for a work-item reference:

- A Jira key (regex `[A-Z][A-Z0-9]+-\d+`), bare or in a full `…atlassian.net/browse/<KEY>` URL → read `references/trackers/jira.md`
- A GitHub issue reference — a full `github.com/<owner>/<repo>/issues/<n>` URL, a cross-repo `<owner>/<repo>#<n>`, or a bare `#<n>` when the change itself is on GitHub in the same repo → read `references/trackers/github.md`

A full URL is unambiguous about which tracker it names; prefer it over a bare key/number if both somehow appear. The tracker is independent of the code host — a GitLab MR can reference a GitHub issue for requirements, and vice versa.

The tracker adapter is the authority for fetching that work item: how to load or authenticate its tools, the exact call to fetch it, and what fields to extract (summary, description/acceptance criteria, issue type). Read it now and follow it as "per the tracker adapter."

Write what you fetched — summary, description, acceptance criteria, and the work item's URL — verbatim to `${TMPDIR:-/tmp}/<change-id>-work-item.md`. Step 5 hands that path to review-changes as the spec, and a file keeps the requirements as the tracker worded them instead of a paraphrase that has already lost the wording a conformance check needs.

If there's no adapter for the tracker you're facing, degrade gracefully the same way as Step 1. If no work-item reference is found at all, or the fetch fails, continue without a spec file — review-changes then reports the review as spec-less, which surfaces in Step 8's output as the caveat that conformance was never assessed.

### Step 4 — Isolate the change in a review worktree

Checking out the change in the user's main clone would switch what's checked out from under them, disrupting whatever branch or uncommitted work they have there. A disposable worktree, detached at the change's head SHA, gives the review its own directory instead — and a detached checkout can't collide with a branch the user already has checked out somewhere else.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}"
python3 "$PLUGIN_ROOT/scripts/setup_worktree.py" \
  --repo-path <repo_path> --purpose review --change-id <mr_iid or pr_number> \
  --source-branch <source_branch> --target-branch <target_branch> --detach-sha <head_sha>
```

(use `python` instead of `python3` if that's not on `PATH` — some native Windows installs only have the latter)

That first line resolves the shared helper at the plugin root in either install mode. `<repo_path>` is the relative shape the host adapter states (GitLab's namespace, GitHub's `owner/repo`) — the script searches common project roots and, failing that, by remote URL, since there's no one standard clone location to assume. `--target-branch` gets the diff base fetched too, which is what makes the fixed point in Step 5 resolvable locally.

On success it prints `WORKTREE_PATH: <path>`; use that path for every read, `grep`, and `git` call from here on. On any refusal (a dirty or unpushed leftover worktree, a clone it can't find) it prints `STOP: <reason>` and exits non-zero — never force past it, and never fall back to checking out the change in the user's main clone. If it can't locate the clone, ask the user for the path and re-run with `--repo-root <path>` in place of `--repo-path`.

With no worktree, the review is diff-only: fetch every changed file's diff per the host adapter (including its truncation check) and write it to `${TMPDIR:-/tmp}/<change-id>.diff`. Step 5 hands that file over in place of the worktree, and Step 8 carries the limitation as a caveat — no working tree means no claim can be settled by running the code.

### Step 5 — Hand the review to review-changes, then come straight back

Invoke the `review-changes` skill (via the Skill tool with `skill: "review-changes"`), passing:

- **the worktree path**, with the instruction to run every git command as `git -C <worktree_path>` — the shell's own working directory is still the user's main clone, and a review that silently diffs the wrong repo is the one failure mode here worth spelling out
- **the fixed point**: the base SHA from Step 2 (the target branch also works — review-changes diffs three-dot, so either resolves to the merge base). In diff-only mode there is no working tree to diff, so hand over `${TMPDIR:-/tmp}/<change-id>.diff` as the already-captured diff instead, and say so
- **the spec**: the `${TMPDIR:-/tmp}/<change-id>-work-item.md` path from Step 3, or that there is no spec
- **the test signal**: the checks/pipeline status from Step 2, as the CI result to report — this is someone else's repo, freshly fetched, so take the host's verdict rather than building and running its suite unprompted
- **where the report goes**: `${TMPDIR:-/tmp}/<change-id>-review.md`, written as a file rather than printed in the conversation. Step 8's output is the only review the user should have to read, and a report printed here would say the same thing twice — the second time without knowing what actually reached the author
- **how long each finding may run**: 2-4 sentences of continuous prose per entry — name the symbol, state the concrete problem, then the fix or the question — because Step 6 posts those entries verbatim as the inline comments. A requested change asserts the problem and prescribes the fix; a suggestion reads as something the author can decline, often best as a direct question when the code might be deliberate. Longer than one tight paragraph only when the failure mechanism genuinely needs the room (a concurrency race, a security hole, a scope change spanning callers). Two things sit outside that budget: a verbatim quote of an unmet acceptance criterion, and a fenced code block carrying the corrected expression when the fix is shorter to show than to describe

**review-changes runs inside this workflow, not in place of it.** Its process is numbered independently of this one and ends in a step called "Report" — that step is satisfied by writing the file above, and it is not the end of the run. Read the file back and go straight into Step 6 in the same turn: publishing is what this skill exists to do, and a review that stops at the report has produced nothing the author can see.

Its report is the review of record: the verdict, the blocking/non-blocking split, spec accounting, and what it checked and found clean. Steps 6 through 8 turn that report into comments, a verdict action, and output — they don't re-review the change.

If `review-changes` isn't among the available skills, fall back to the `code-review-pyramid` skill (or your own judgment if that's absent too), and produce the same shape yourself: findings tagged by layer, split into requested changes and suggestions, resolved into one verdict.

### Step 6 — Post the findings per the host adapter

Every finding review-changes reported becomes one note object, and its text is **the entry as review-changes wrote it, verbatim** — layer tag, `file:line` citation and all. Don't re-draft, expand, re-explain or trim it: the report and the change should say the same thing, and a rewrite here reliably comes out longer than the entry it replaced. Strip only the list number, which belongs to the report's ordering and means nothing on a standalone comment, and promote a fenced code block into the host's suggestion syntax where the rules below allow it.

The citation stays even though the anchor points at the same line, because the anchor is not guaranteed to survive: when a host can't resolve a position it re-posts the same text positionless (GitLab's `line_code` path, below), and a comment that lost its anchor is exactly the one that needs to name its own file and line.

So a report entry reading

```
1. **[Impl. Semantics]** `svc/user.go:47` — `fetchUser` doesn't handle the case where the DB returns `null`, so the `.Name` access will panic at runtime. Add a nil check or return an early error.
```

posts as

```
**[Impl. Semantics]** `svc/user.go:47` — `fetchUser` doesn't handle the case where the DB returns `null`, so the `.Name` access will panic at runtime. Add a nil check or return an early error.
```

An entry too long to read as an inline comment is an entry to shorten in *both* places — go back and tighten it in the report rather than posting one length and reporting another.

**Anchors**: a finding cited as `file:line` becomes an inline note (`new_path` plus `new_line`); a cross-cutting one with no single site becomes `"general": true` rather than being pinned to a misleading line. `new_line` must be a line added in this change — find it with `grep -n '<snippet>' <worktree_path>/<file>` rather than counting diff lines, and confirm it carries a `+` in `git -C <worktree_path> diff <base_sha>...HEAD -- <file>`. A finding that lands on an unchanged line anchors to the nearest added line or goes general; both host scripts reject or downgrade an anchor the diff doesn't contain.

**Suggested changes**: both hosts render a fenced `suggestion` block inside an inline comment as a patch the author applies in one click, and a finding whose fix is an exact replacement of the lines its comment anchors to belongs in one — the adapter gives the host's syntax. What goes in the block is the whole replacement: the original indentation, valid code on its own, nothing left for the author to fill in, and read verbatim out of the worktree rather than reconstructed from the diff. Prose stays the right answer for a fix spanning several files or non-contiguous lines, for a finding the author has a genuine choice about, for anything landing as a general comment (the block is inert outside the diff), and in diff-only mode, where there's no worktree to read the current line from.

**What stays out of the comments**: the summary paragraph, the "checked and clean" list, and the path to merge all belong to Step 8's output in the conversation. Skip a suggestion no author would act on — a style nit that automation should be catching — and where the same finding recurs across files, post the clearest occurrence once.

**The verdict summary**: only a Request changes verdict in the default mode posts one — GitHub requires a body on that event, and GitLab has nowhere else to state the verdict. Write the one thing the author needs in order to act, not a second copy of the review:

```
I did not approve this <merge request | pull request> yet because <the blocking finding, in one sentence>. <Why that blocks — the defect that would reach production, the contract broken for callers, the acceptance criterion left unmet.> <Where the detail is: the inline comment on `<file>`, or "the N inline comments" when there are several.>
```

Two or three sentences, no headings and no lists. The inline comments carry the mechanism, and the suggestions, the "checked and clean" list and the path to merge all stay in Step 8's output. Write it to `${TMPDIR:-/tmp}/<change-id>-summary.md` and pass it as `--summary-file`; the script marks it, so leave the 🤖 off.

The host adapter names the bundled script that does the posting (`scripts/post_review_notes_gitlab.py` or `scripts/post_review_notes_github.py`, relative to this SKILL.md) and its exact invocation for the mode Step 2 settled on. Both read the same notes-file JSON shape, so the notes file doesn't change with the host; both mark each comment and the verdict summary with a trailing 🤖; both publish comments before touching the verdict, so an approval never lands without its reasoning; and both skip a finding this account already published rather than deleting or duplicating it. Leave the marking to the script — writing it yourself only risks it landing twice.

Read the script's tally afterward: what was posted, what was skipped as already present, and what the verdict action did. Step 8 reports all three.

### Step 7 — Remove the worktree

Remove the worktree this run created, even if earlier steps failed partway (posting errored out, the review was abandoned). If Step 4 hit its STOP check, this run never created one — leave the pre-existing worktree untouched.

```bash
git -C <repo_path> worktree remove "<worktree_path>"
```

If removal is refused, leave the worktree in place and tell the user exactly what git reported, so they can decide what to do with it.

### Step 8 — Output the review

Output the full review in the conversation — the change carries the comments and the verdict, not the reasoning around them. Since Step 5 kept review-changes' report in a file, this is the only review the user reads, so it has to stand on its own. Lead with review-changes' verdict, keep its lists as it wrote them, and add what only this skill knows: where the change and work item live, what the author will actually see, and where a human's own attention is worth spending.

```markdown
## <Approved | Approved with suggestions | Request changes>

**Change**: [<title>](<web_url>)
**Work item**: [PROJ-123](<work_item_url>) — <work item summary>
*(or "No work item linked — reviewed without requirements context")*

<review-changes' summary paragraph, plus any caveat this skill added: diff-only review, truncated diff, N of M files reviewed, a diff too large to review at full depth>

### Requested changes
1. **[Impl. Semantics]** `svc/user.go:47` — <finding> *(posted inline)*

### Suggestions
1. **[Code Style]** `svc/user.go:12` — <finding>

### Checked and clean
<what review-changes checked and how it established it>

### Worth your own look
- `<file>`[, `<file>`, ...] — <one-clause reason; group files sharing a reason into one line>

### Path to merge
1. <the requested changes in the order worth addressing them>

### On the change
- <N comments published inline, M in the conversation, K skipped as already posted — or, in draft mode, N drafts awaiting submission>
- <the verdict action taken, or why none was: comments-only mode, a self-authored change, a 409 on a moved head>
- <the reversal or submit line from the host adapter's closing lines>
```

**Marking posted findings** — tag each finding that reached the change with *(posted inline)* or *(posted to the conversation)*, and each one the script skipped with *(already on the change)*. It's the only way the reader can tell what the author sees from what stayed between the two of you.

**Worth your own look** — the files where a human's independent judgment pays off most, whatever the AI found there: files defining or changing a public contract other code depends on (an interface, an exported type, a signature callers rely on), and files carrying business-rule logic (branches encoding a business decision, state transitions, orchestration across domain concerns). Judge by the role a file plays, not its path or language — a controller with real branching of its own ranks; a "domain" file of pure boilerplate doesn't. Be selective; let the criteria do the filtering rather than a number, and omit the section entirely when nothing rises to it.

## Hard constraints

The steps above carry their own reasoning; these four are repeated because each one is either irreversible from the author's side once done, or leaves the run having delivered nothing.

- **Never** end the turn between the review and the posting — review-changes' report is an intermediate artifact, and the run isn't finished until Step 6 has posted and Step 8 has reported. If the user has to ask whether the comments went up, this skill failed.
- **Never** act on the verdict outside the default mode — `draft` and `comments-only` report it in the conversation and leave the change's approval state untouched, as does a self-authored change.
- **Never** delete or overwrite a comment that is already published, on a rerun or otherwise — the author may have replied to it. Reruns skip what's already there instead.
- **Never** check out the change in the user's main clone — always review from the isolated worktree created in Step 4.
