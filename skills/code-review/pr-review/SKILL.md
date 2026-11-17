---
name: pr-review
description: >
  Reviews a merge request or pull request against its linked work item, publishes the findings as
  inline comments on the diff, and records the verdict on the change. It fetches the change and the
  work-item context, isolates the change locally, hands the review itself to the review-changes
  skill, posts each finding, and then approves the change or requests changes according to that
  verdict. It ships with adapters for GitLab and GitHub as the code host, and Jira and GitHub Issues
  as the tracker. For any other host or tracker, it degrades to whatever tool discovery can reach.
  This skill is user-only: it runs only when the user invokes /pr-review <MR or PR URL>. When the
  user wants to review a GitLab MR or a GitHub PR, code-review a merge request or pull request, or
  evaluate the diff of a change against its linked work item, suggest this command instead of a
  manual review.
argument-hint: "<merge/pull request URL> [draft|comments-only]"
allowed-tools: [Read, Bash, Skill, Write, Glob, Grep, ToolSearch]
disable-model-invocation: true
---

# PR/MR Review

## What this skill owns

The [review-changes](../review-changes/SKILL.md) skill owns every review judgment: the layers, the spec check, the split into blocking and non-blocking, and the verdict. This skill supplies the four things that review-changes cannot reach from a URL alone:

- It resolves the change and its work item, through host and tracker adapters.
- It isolates the change locally, so the review reads real files at the exact head SHA of the change.
- It renders the findings as inline comments anchored to the diff.
- It turns the verdict into the host's approve action or request-changes action.

A "change" is a merge request on GitLab, or a pull request on GitHub and Bitbucket. A "work item" is whatever the tracker holds, such as a Jira issue or a GitHub issue. The mechanics for each host and tracker live in adapter files under `references/`. Load each one only at the step that needs it.

## Modes

The word after the URL chooses how much of the review lands on the change. With no word, both parts land.

| Invocation | Comments | Verdict |
|---|---|---|
| `/pr-review <url>` | published directly | Approved or Approved with suggestions, so **approve**. Request changes, so **request changes** |
| `/pr-review <url> comments-only` | published directly | reported in the conversation only |
| `/pr-review <url> draft` | drafts for the user to submit | reported in the conversation only |

**Self-authored changes**: a host does not accept a verdict from the author of the change. Step 2 drops a self-review to `comments-only`. Say so in the output of Step 8.

## Workflow

### Step 1: Identify the host and load its adapter

Determine the host from the shape of the URL:

- A URL that contains `…/-/merge_requests/<n>` is GitLab. Read `references/hosts/gitlab.md`.
- A URL that matches `github.com/<owner>/<repo>/pull/<n>` is GitHub. Read `references/hosts/github.md`.

Read the adapter now. It governs every later step that says "per the host adapter".

When no adapter exists for the host, degrade instead of stopping. Discover the tools with a keyword `ToolSearch`, or with the platform's CLI or API. Make sure that the fetch-metadata, fetch-diff, and post-comment operations exist. Then run in `comments-only` mode, because a verdict through an unverified interface is not worth the risk. Tell the user that host-specific behavior is best-effort, because no dedicated adapter exists.

### Step 2: Fetch change metadata

Use the metadata call from the host adapter. Fetch the title, the description, and the author of the change. Fetch its source branch and target branch, the SHAs that inline comment positions need, the checks or pipeline status, and the web URL.

Compare the author against the authenticated user. The adapter names both calls. On a match, switch to `comments-only` for the rest of the workflow.

**If the metadata call fails with an auth error**, such as a 401 or a "not logged in" message, stop. Ask the user to authenticate, and quote the exact command from the adapter. Do not pre-check auth separately. A success here also proves that posting in Step 6 works, because both use the same credentials.

### Step 3: Resolve the work item and save it as the spec

Scan the title and the description for a work-item reference:

- A Jira key, which matches the regex `[A-Z][A-Z0-9]+-\d+`, bare or inside a full `…atlassian.net/browse/<KEY>` URL. Read `references/trackers/jira.md`.
- A GitHub issue reference. That is a full `github.com/<owner>/<repo>/issues/<n>` URL, a cross-repo `<owner>/<repo>#<n>` reference, or a bare `#<n>` when the change sits on GitHub in the same repo. Read `references/trackers/github.md`.

Prefer a full URL over a bare key or number when both appear, because a URL names its tracker without ambiguity. The tracker is independent of the code host. A GitLab MR can reference a GitHub issue, and the reverse also happens.

Read the tracker adapter now. It governs the fetch of the work item, as "per the tracker adapter". The skill never posts back to the work item.

Write what you fetched to `${TMPDIR:-/tmp}/<change-id>-work-item.md`, word for word: the summary, the description, the acceptance criteria, and the URL. A conformance check needs the tracker's exact wording, and a paraphrase loses it.

When no adapter exists for the tracker, degrade as in Step 1. When you find no work-item reference, or the fetch fails, continue with no spec file. review-changes then reports the review as spec-less, and the output of Step 8 carries that caveat.

### Step 4: Isolate the change in a review worktree

Review from a disposable worktree, detached at the head SHA of the change. A checkout in the user's main clone disrupts the branch or the uncommitted work that they hold there.

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(dirname "$(dirname "$(readlink -f "<skill_dir>/SKILL.md")")")}"
python3 "$PLUGIN_ROOT/scripts/setup_workspace.py" \
  --repo-path <repo_path> --purpose review --change-id <mr_iid or pr_number> \
  --source-branch <source_branch> --target-branch <target_branch> --detach-sha <head_sha>
```

Use `python` in place of `python3` when `python3` is not on `PATH`. `<repo_path>` is the relative shape that the host adapter states. The script searches for the clone. The `--target-branch` flag also fetches the diff base, so the fixed point of Step 5 resolves locally.

On success the script prints `MODE: worktree`, then `WORKSPACE_PATH: <path>`. Use that path for every read, every `grep`, and every `git` call from here on. On a refusal, the script prints `STOP: <reason>` and exits non-zero. Never force past a refusal, and never fall back to a checkout in the user's main clone. When the script cannot find the clone, ask the user for the path, and re-run with `--repo-root <path>` in place of `--repo-path`.

With no worktree, the review is diff-only. Fetch the diff of every changed file per the host adapter, including its truncation check, and write it to `${TMPDIR:-/tmp}/<change-id>.diff`. When the diff is truncated or a file has no diff, review the riskiest files first. Those are auth, data access, and the public API surface. Step 8 carries the limitation as a caveat, because no claim can be settled by running the code.

### Step 5: Hand the review to review-changes, then come straight back

Invoke the `review-changes` skill through the Skill tool, with `skill: "review-changes"`. Pass these six things:

- **The worktree path**, with the instruction to run every git command as `git -C <worktree_path>`. The shell still sits in the user's main clone, and a review that diffs the wrong repo fails silently.
- **The fixed point**, which is the base SHA from Step 2. In diff-only mode, hand over `${TMPDIR:-/tmp}/<change-id>.diff` as the already-captured diff, and say that you did.
- **The spec**, which is the `${TMPDIR:-/tmp}/<change-id>-work-item.md` path from Step 3. When there is no spec, say that there is none.
- **The test signal**, which is the checks or pipeline status from Step 2, passed as the CI result to report.
- **Where the report goes**, which is `${TMPDIR:-/tmp}/<change-id>-review.md`, written as a file instead of printed in the conversation. The output of Step 8 is the only review that the user reads.
- **The finding-length budget**: 2 to 4 sentences of continuous prose per entry. Step 6 posts those entries word for word. A requested change asserts the problem and prescribes the fix. A suggestion leaves the decision with the author. Phrase it as a direct question when the code can be deliberate, or as an optional fix. Never add a sentence about the comment itself, such as who resolves the thread or who decides. Go past one paragraph only when the failure mechanism needs the room. A concurrency race, a security hole, and a scope change across callers all can. Two things sit outside the budget: a word-for-word quote of an unmet acceptance criterion, and a fenced code block that carries the corrected expression.

**review-changes runs inside this workflow, not in place of it.** It ends in its own step called "Report". Writing the file satisfies that step, and it does not end the run. Read the file back and go straight into Step 6 in the same turn.

That report is the review of record. Steps 6 through 8 turn it into comments, a verdict action, and output. They do not review the change again.

### Step 6: Post the findings per the host adapter

Every finding that review-changes reported becomes one note object. Its text is **the entry as review-changes wrote it, word for word**, including the layer tag and the `file:line` citation. Do not re-draft, expand, or trim it. Strip only the list number. Then promote a fenced code block into the host's suggestion syntax, where the rules below allow it.

Keep the `file:line` citation even on an anchored note, because a note that cannot anchor is re-posted with no position.

**Marking a suggestion**: post each suggestion with `non-blocking` in its layer tag, as in `**[Code Style · non-blocking]**`. The author then tells it apart from a requested change at a glance.

An entry too long to read as an inline comment is an entry to shorten in *both* places. Tighten it in the report, instead of posting one length and reporting another.

**The notes file**: write the findings to a JSON array, with one object per finding. Both host scripts read the same shape:

```json
[
  { "note": "<the entry, word for word>", "new_path": "src/user.go", "new_line": 47 },
  { "note": "<a finding with no good line anchor>", "general": true }
]
```

**Anchors**: a finding cited as `file:line` becomes an inline note, with `new_path` plus `new_line`, the line number in the new file as an integer. A cross-cutting finding with no single site becomes `"general": true`, rather than a note pinned to a misleading line. `new_line` must be a line that this change added. Find it with `grep -n '<snippet>' <worktree_path>/<file>`, then make sure that it carries a `+` in `git -C <worktree_path> diff <base_sha>...HEAD -- <file>`. A finding on an unchanged line anchors to the nearest added line, or it goes general.

**Suggested changes**: a fenced `suggestion` block inside an inline comment renders as a patch that the author applies in one click. Use one when the fix is an exact replacement of the lines that the comment anchors to. The adapter gives the syntax. The block replaces those lines whole: keep the original indentation, add no leading `+`, and leave nothing for the author to fill in. Read the current text out of the worktree with `sed -n`, instead of reconstructing it from the diff. Use prose instead in four cases:

- a fix that spans several files or non-contiguous lines
- a finding that the author has a genuine choice about
- a general comment, where the block renders as inert code
- diff-only mode, where no worktree exists to read from

**What stays out of the comments**: the summary paragraph, the "checked and clean" list, and the path to merge belong to the Step 8 output. Skip a suggestion that no author will act on, such as a style nit that automation must catch. Where the same finding recurs across files, post the clearest occurrence once.

**The verdict summary**: only a Request changes verdict in the default mode posts one, because the host needs the reason on the change. Write the one thing that the author needs to act on:

```
This <merge request | pull request> was not approved because <the blocking finding, in one sentence>. <Why that blocks: the defect that will reach production, the contract broken for callers, or the acceptance criterion left unmet.> <Where the detail is: the inline comment on `<file>`, or "the N inline comments" when there are several.>
```

Write two or three sentences in the third person, with no headings, no lists, and no "I". Keep the passive opening of the template, because it states the verdict without naming a reviewer. When a plain-English writing skill such as `simple-english` is available, apply its rules to the summary. Where they pull against the sentence limit, the limit wins. Write the summary to `${TMPDIR:-/tmp}/<change-id>-summary.md`, and pass it as `--summary-file`.

**The posting script**: the host adapter names it and gives the invocation for the mode that Step 2 settled on. The script marks each comment and the verdict summary with a trailing 🤖, so leave the mark off. It publishes the comments before it touches the verdict. It skips a finding that this account already published, instead of deleting or duplicating it. It downgrades an anchor that the diff does not contain.

The 🤖 marks only what the script posts. The user can later ask you to post a message of their own, such as a question to the author. Post it with no 🤖, because it speaks for the user.

Read the script's tally afterward. It reports what was posted, what was skipped as already present, and what the verdict action did. Step 8 reports all three.

### Step 7: Remove the worktree

Remove the worktree that this run created, even when an earlier step failed partway. When Step 4 hit its STOP check, this run created no worktree, so leave the existing one untouched.

```bash
git -C <repo_path> worktree remove "<worktree_path>"
```

If git refuses the removal, leave the worktree in place, and tell the user exactly what git reported.

### Step 8: Output the review

Output the full review in the conversation. It is the only review that the user reads, so it has to stand on its own. Lead with the verdict from review-changes, and keep its lists as it wrote them. Add what only this skill knows: where the change and the work item live, what the author sees, and where human attention pays off.

```markdown
## <Approved | Approved with suggestions | Request changes>

**Change**: [<title>](<web_url>)
**Work item**: [PROJ-123](<work_item_url>) — <work item summary>
*(or "No work item linked. Reviewed without requirements context.")*

<the summary paragraph from review-changes, plus any caveat this skill added: a diff-only review, a truncated diff, N of M files reviewed, or a diff too large to review at full depth>

### Requested changes
1. **[Impl. Semantics]** `svc/user.go:47` — <finding> *(posted inline)*

### Suggestions
1. **[Code Style]** `svc/user.go:12` — <finding>

### Checked and clean
<what review-changes checked, and how it established each result>

### Worth your own look
- `<file>`[, `<file>`, ...] — <one-clause reason. Group files that share a reason into one line.>

### Path to merge
1. <the requested changes, in the order worth addressing them>

### On the change
- <N comments published inline, M in the conversation, K skipped as already posted. In draft mode, N drafts awaiting submission.>
- <the verdict action taken, or why none was taken: comments-only mode, a self-authored change, or the host refused because the head moved>
- <the reversal or submit line from the closing lines of the host adapter>
```

**Marking posted findings**: tag each finding that reached the change with *(posted inline)* or *(posted to the conversation)*. Tag each finding that the script skipped with *(already on the change)*.

**Worth your own look**: name the files where the independent judgment of a human pays off most, whatever the AI found there. Two kinds qualify. The first defines or changes a public contract that other code depends on, such as an interface, an exported type, or a signature. The second carries business-rule logic, such as a branch that encodes a business decision, a state transition, or orchestration across domain concerns. Judge by the role of a file, not by its path or its language. Let the criteria filter the list rather than a number, and omit the section when nothing qualifies.

## Hard constraints

Each of these is irreversible for the author, or leaves the run with nothing delivered.

- **Never** end the turn between the review and the posting. The run is not finished until Step 6 has posted and Step 8 has reported.
- **Never** act on the verdict outside the default mode. `draft`, `comments-only`, and a self-authored change leave the approval state of the change untouched.
- **Never** delete or overwrite a published comment, on a rerun or at any other time. The author can have replied to it.
- **Never** check out the change in the user's main clone. Always review from the worktree of Step 4.
