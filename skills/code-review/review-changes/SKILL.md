---
name: review-changes
description: >
  Reviews the diff between HEAD and a fixed point (commit, branch, tag, or merge-base) against the
  Code Review Pyramid, checking conformance to the originating issue/spec and to the repo's own
  documented standards, then sorts every finding into blocking or non-blocking and resolves them into
  one verdict: Approved, Approved with suggestions, or Request changes. Use when the user wants to
  review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

Pyramid-driven review of the diff between `HEAD` and a fixed point the user supplies, ending in one verdict the reader meets before any detail.

The [Code Review Pyramid](../code-review-pyramid/SKILL.md) orders review attention by how expensive a mistake is to unwind: API semantics at the base, code style at the apex. Read the base hardest.

Where a finding sits in that pyramid says nothing about whether it blocks, and keeping those two axes apart is the job here. A review that blurs "this is wrong" into "I would have done it differently" leaves the reader to work out what actually gates the merge — which is the failure this skill exists to prevent.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`. If they didn't specify one, ask.

Capture the diff once with `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base), and the commit list with `git log <fixed-point>..HEAD --oneline`.

Confirm the ref resolves (`git rev-parse <fixed-point>`) and the diff is non-empty before going further, so a bad ref fails here rather than halfway through a review.

### 2. Gather review context

**The spec** — look for the originating spec, cheapest source first:

1. A path the user passed as an argument.
2. An issue reference in a commit message (`#123`, `Closes #45`, GitLab `!67`, `ABC-123`). Resolve it locally first: a file under `docs/`, `specs/`, or `.scratch/` whose name carries the key costs one `Glob`. Reach for tracker tooling — discovered with a keyword `ToolSearch` or the platform's own CLI — only when nothing local matches.
3. A spec file matching the branch name or feature.
4. If nothing turns up, ask the user where the spec is.

If the user says there isn't one, review without it and report the review as spec-less. That becomes a caveat in step 5, since conformance was never assessed.

**The standards** — two kinds, and both carry weight:

- *Convention docs* — `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `CLAUDE.md`, `AGENTS.md`, or an equivalent. A documented repo standard overrides a generic pyramid question wherever the two disagree, and a documented convention is settled rather than a problem to raise.

  Where a standard constrains data rather than layout — money is always integer cents, identifiers are always UUIDs, timestamps are always UTC — check that the code *enforces* it at runtime and not merely that names and type annotations agree with it. A conforming name on an unvalidated input is the easiest kind of breach to read past, because everything on the surface looks right.
- *Contract docs* — the README, API reference, OpenAPI or schema files: whatever tells callers what they are promised. These decide severity more often than convention docs do. A documented response shape is what makes a field rename a breaking change rather than a naming preference.

Take standards only from the repo under review. A `CLAUDE.md` already in your context from a different repo governs that repo, not this diff.

### 3. Load the pyramid

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill tool with `skill: "code-review-pyramid"`) to load the layer definitions and their questions. If it isn't available, fall back to your own judgment of what belongs at each layer.

Work through every layer's questions rather than stopping at what surfaces first, and spend attention in proportion to the pyramid's order — deepest at API and implementation semantics, lightest at code style, where automation should be doing the work.

### 4. Set the severity bar

Every finding either blocks the change or doesn't, and that split — not the pyramid layer — decides the verdict:

- **Requested change** — the author must act before this lands: something that would cause a defect in production, an unintended breaking change to a user-facing contract, a spec requirement that is missing, partial, or implemented wrongly, or a hard breach of a documented repo standard.
- **Suggestion** — a reasonable author could decline it: judgment calls, optional refactors, naming and formatting preferences, docs or tests no standard mandates, follow-up ideas.

Severity is independent of layer. A code style finding that breaches a documented standard is a requested change; an API semantics observation can be a suggestion.

Hold blocking claims to a higher bar than suggestions, because a false blocker costs the author a round trip and costs you their trust in the next review. Where a claim is cheap to check by running the code, check it — and if a claim won't substantiate, downgrade it or drop it rather than hedging it into the blocking list.

**Test status** — establish it rather than assuming it. Use the CI result if the repo has CI; otherwise run the suite yourself. Either way say which signal you used, and report the status as unverified only when neither is available — "unverified" on a repo where the answer is one command away is a caveat you invented. Treat a test committed skipped or disabled as unverified coverage, not as a passing test.

### 5. Decide the verdict

- **Request changes** — at least one requested change.
- **Approved with suggestions** — no requested changes, but at least one suggestion or at least one caveat.
- **Approved** — nothing to act on and nothing caveated.

Two caveats belong in the summary whatever the verdict comes out as: there was no spec to check conformance against, or test status could not be established. Disclosing them is the point — it is how the reader learns what the review did *not* check, which matters as much under "Request changes" as under an approval.

### 6. Report

Lead with the verdict, then a summary paragraph under all three outcomes — the fixed point and diff scope (commits, files), what the review verified, and any caveat.

```markdown
## <Approved | Approved with suggestions | Request changes>

<summary paragraph>

### Requested changes
1. **[Impl. Semantics]** `svc/user.go:47` — <finding, then what to do about it>
2. **[Tests]** `svc/user_test.go` — <finding>

### Suggestions
1. **[Code Style]** `svc/user.go:12` — <finding>

### Checked and clean
<what you checked and how you established it>

### Path to merge
1. <the requested changes in the order worth addressing them>
```

**Ordering** — sort each list by consequence, worst first. The layer tag is a label, not a sort key: a money-losing implementation defect leads over a naming change one layer below it, because the reader needs the outcome before the detail.

**Layer tags** — `[API Semantics]`, `[Impl. Semantics]`, `[Documentation]`, `[Tests]`, `[Code Style]`. Give each finding exactly one, and when a finding genuinely spans layers use the lowest-numbered one it belongs to. A defect whose effect a caller can observe — a response field of the wrong type, a rejection that used to succeed — reaches Layer 1 however deep in the implementation it originates.

**Every entry under "Checked and clean" is a claim you are making** — so name what you exercised and how you know, not the layers you passed over. "Ran the suite: 9 passed, including a case per acceptance criterion" earns its place; "no floats are used for money" does not unless you tried one. A false all-clear is worse for the reader than silence, because silence invites their own look and an all-clear ends it.

**Citations** — cite `file:line` where the finding has a location. A cross-cutting observation with no single site keeps its tag and drops the citation rather than being pinned to a misleading line number.

**Spec accounting** — when a spec exists, account for every requirement explicitly rather than in prose: name each one and say whether the diff satisfies it. Quote the spec line for anything missing, partial, or implemented wrongly, and separately flag behavior the diff adds that the spec never asked for.

**Nothing manufactured** — report only what the files in front of you substantiate. A layer question that raises nothing belongs under "Checked and clean"; recording that it yielded nothing is worth more to the reader than a finding invented to fill the section.
