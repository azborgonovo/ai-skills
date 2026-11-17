---
name: review-changes
description: >
  Reviews the diff between HEAD and a fixed point, which is a commit, a branch, a tag, or a
  merge-base, against the Code Review Pyramid. Checks the change against the originating issue or
  spec, and against the repo's documented standards. Sorts every finding into blocking or
  non-blocking, and resolves them into one verdict: Approved, Approved with suggestions, or Request
  changes. Use when the user wants to review a branch, a PR, or work-in-progress changes, or asks to
  "review since X".
argument-hint: "<fixed point: a commit, a branch, a tag, or a merge-base>"
---

# Review Changes

Review the diff between `HEAD` and a fixed point that the user supplies, driven by the pyramid. The review ends in one verdict, and the reader meets that verdict before any detail.

The [Code Review Pyramid](../code-review-pyramid/SKILL.md) orders review attention by what a mistake costs to unwind. API semantics sit at the base, and code style sits at the apex. Read the base hardest.

Where a finding sits in that pyramid says nothing about whether it blocks the change. Keep those two axes apart. A review that blurs "this is wrong" into "I have a different preference" leaves the reader to work out what gates the merge.

## Process

### 1. Pin the fixed point

Whatever the user named is the fixed point. It can be a commit SHA, a branch name, a tag, `main`, or `HEAD~5`. When the user named none, ask for one.

Make sure that the ref resolves, with `git rev-parse <fixed-point>`, so that a bad ref fails here and not halfway through the review. Capture the diff once with `git diff <fixed-point>...HEAD`, which compares against the merge-base, and make sure that it is not empty. Capture the commit list with `git log <fixed-point>..HEAD --oneline`.

The caller can name a repository directory, such as a prepared worktree or a clone outside the shell's working directory. Then run every git command with `git -C <dir>`, and read every file under it. A review of the wrong repository looks complete and describes nothing that the caller asked about.

When the caller hands you a diff that it captured itself, for example from a code host with no local clone, review that diff instead of your own. Add the caveat that there is no working tree, because every claim then rests on reading alone.

### 2. Gather review context

**The spec**: look for the originating spec, and try the cheapest source first.

1. A path that the user passed as an argument.
2. An issue reference in a commit message, such as `#123`, `Closes #45`, a GitLab `!67`, or `ABC-123`. Resolve it locally first, because a file under `docs/`, `specs/`, or `.scratch/` whose name carries the key costs one `Glob`. Reach for tracker tooling, discovered with a keyword `ToolSearch` or through the platform's own CLI, only when nothing local matches.
3. A spec file that matches the branch name or the feature.
4. When nothing turns up, ask the user where the spec is.

If the user says that no spec exists, review without one, and report the review as spec-less. That is a caveat in step 5.

**The standards**: there are two kinds, and both carry weight.

- *Convention docs*, such as `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, or an equivalent file. A documented repo standard overrides a generic pyramid question wherever the two disagree, and a documented convention is settled rather than a problem to raise.

  Where a standard constrains data rather than layout, make sure that the code *enforces* it at runtime. Examples are money always held as integer cents, identifiers always UUIDs, and timestamps always UTC. Agreement between the names and the type annotations is not enforcement. A conforming name on an unvalidated input is the easiest kind of breach to read past, because everything on the surface looks right.
- *Contract docs*, such as the README, the API reference, and the OpenAPI or schema files. These tell callers what the code promises them. They decide severity more often than convention docs do. A documented response shape is what makes a field rename a breaking change instead of a naming preference.

Take the standards only from the repo under review. A `CLAUDE.md` that already sits in your context from a different repo governs that repo, not this diff.

### 3. Load the pyramid

Invoke the `code-review-pyramid` skill, which ships in this plugin, to load the layer definitions and their questions.

Work through the questions of every layer, instead of stopping at what surfaces first. Go deepest at API semantics and implementation semantics, and go lightest at code style, where automation must do the work.

### 4. Set the severity bar

Every finding either blocks the change or does not, and that split decides the verdict. The pyramid layer does not.

- **Requested change**: the author must act before this change lands. This covers anything that will cause a defect in production, and an unintended breaking change to a user-facing contract. It covers a spec requirement that is missing, partial, or implemented wrongly. It covers a hard breach of a documented repo standard.
- **Suggestion**: a reasonable author can decline it. This covers judgment calls, optional refactors, naming and formatting preferences, docs or tests that no standard mandates, and follow-up ideas.

A code style finding that breaches a documented standard is a requested change. An observation about API semantics can be a suggestion.

Hold a blocking claim to a higher bar than a suggestion. A false blocker costs the author a round trip, and it costs you their trust in the next review. Where a claim is cheap to settle by running the code, run the code. When a claim does not substantiate, downgrade it or drop it. Never hedge it into the blocking list.

**Test status**: establish it rather than assume it. When a caller hands you a test signal, such as a pipeline result from a code host, report it and do not build the repo yourself. Otherwise use the CI result of the repo, or run the suite yourself when it has no CI. Say which signal you used. Report the status as unverified only when no signal is available. On a repo where the answer is one command away, "unverified" is an invented caveat. Treat a test committed as skipped or disabled as unverified coverage, not as a passing test.

### 5. Decide the verdict

- **Request changes**: at least one requested change.
- **Approved with suggestions**: no requested changes, and at least one suggestion or at least one caveat.
- **Approved**: nothing to act on and nothing caveated.

Two caveats belong in the summary whatever the verdict is: no spec existed to check conformance against, and you cannot establish the test status. They tell the reader what the review did *not* check, which matters under "Request changes" too.

### 6. Report

Lead with the verdict. Then write a summary paragraph under all three outcomes. Cover the fixed point, the diff scope in commits and files, what the review verified, and any caveat.

When the caller supplies a destination for the report, write the report to that path. Print nothing in the conversation, because the caller's own output is what the user reads.

**Finding length**: when a caller states a length budget per finding, write to it. With none given, write one or two sentences per finding: the symbol, the concrete problem, then the fix or the question.

**Plain English**: the author of the change reads these findings, and a caller sometimes posts them word for word. Write short sentences in the active voice, define a term that the reader can miss at its first use, and cut filler. Keep every layer tag, `file:line` citation, symbol name, and code snippet exactly as it is. Where this pulls against the length budget above, the budget wins. When a plain-English writing skill such as `simple-english` is available, invoke it and apply its rules to the report.

```markdown
## <Approved | Approved with suggestions | Request changes>

<summary paragraph>

### Requested changes
1. **[Impl. Semantics]** `svc/user.go:47` — <finding, then what to do about it>
2. **[Tests]** `svc/user_test.go` — <finding>

### Suggestions
1. **[Code Style]** `svc/user.go:12` — <finding>

### Checked and clean
<what you checked, and how you established each result>

### Path to merge
1. <the requested changes, in the order worth addressing them>
```

**Ordering**: sort each list by consequence, worst first. The layer tag is a label, not a sort key. An implementation defect that loses money leads over a naming change one layer below it.

**Layer tags**: use `[API Semantics]`, `[Impl. Semantics]`, `[Documentation]`, `[Tests]`, and `[Code Style]`. Give each finding exactly one tag. When a finding genuinely spans layers, use the lowest-numbered layer that it belongs to. A defect whose effect a caller can observe reaches Layer 1, no matter how deep in the implementation it starts. Examples are a response field of the wrong type, and a rejection where the call used to succeed.

**Every entry under "Checked and clean" is a claim that you are making.** Name what you exercised and how you know it, and do not list the layers you passed over. "Ran the suite: 9 passed, including a case per acceptance criterion" earns its place. "No floats are used for money" does not, unless you tried one. A false all-clear is worse for the reader than silence, because silence invites their own look and an all-clear ends it.

**Citations**: cite `file:line` where the finding has a location. A cross-cutting observation with no single site keeps its tag and drops the citation, instead of getting pinned to a misleading line number.

**Spec accounting**: when a spec exists, account for every requirement explicitly rather than in prose. Name each requirement, and say whether the diff satisfies it. Quote the spec line for anything missing, partial, or implemented wrongly. Separately, flag behavior that the diff adds and the spec never asked for.

**Nothing manufactured**: report only what the files in front of you substantiate. A layer question that raises nothing belongs under "Checked and clean", not as a finding invented to fill a section.
