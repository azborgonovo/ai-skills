---
name: review-changes
description: >
  Reviews the diff between HEAD and a fixed point (commit, branch, tag, or merge-base) using the Code
  Review Pyramid, split across two parallel sub-agents by cost-of-change — Foundation (API and
  implementation semantics, including conformance to the originating issue/spec) and Supporting
  (documentation, tests, and code style) — then reports one verdict: Approved, Approved with
  suggestions, or Request changes. Use when the user wants to review a branch, a PR, work-in-progress
  changes, or asks to "review since X".
---

Pyramid-driven review of the diff between `HEAD` and a fixed point the user supplies.

The [Code Review Pyramid](../code-review-pyramid/SKILL.md) orders review attention by how expensive a mistake is to unwind: API semantics at the base, code style at the apex. This skill splits along that grain into two **parallel sub-agents**, so they don't pollute each other's context:

- **Foundation** — Layers 1-2 (API Semantics, Implementation Semantics), where a mistake is costly and needs the deepest read. Spec conformance lives here, since Layer 2's first question is "does it satisfy the original requirements?"
- **Supporting** — Layers 3-5 (Documentation, Tests, Code Style), where the pyramid says to lean on automation and spend proportionally less manual attention.

Both reports converge into a single verdict — **Approved**, **Approved with suggestions**, or **Request changes** — so the reader learns the outcome before the detail.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point — a commit SHA, branch name, tag, `main`, `HEAD~5`, etc. If they didn't specify one, ask for it.

Capture the diff command once: `git diff <fixed-point>...HEAD` (three-dot, so the comparison is against the merge-base). Also note the list of commits via `git log <fixed-point>..HEAD --oneline`.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`) and the diff is non-empty. A bad ref or empty diff should fail here — not inside two parallel sub-agents.

### 2. Gather review context

**The spec** — look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched with whatever tracker tooling is available — discover it with a keyword `ToolSearch` or the platform's own CLI.
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is.

If the user says there isn't one, the Foundation sub-agent still runs — it skips the requirements check and reports the review as spec-less. That becomes a caveat in step 6, capping the verdict below a clean "Approved", since conformance was never assessed.

**The standards** — anything in the repo documenting how code should be written: `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `CLAUDE.md`, or an equivalent. A documented repo standard overrides a generic pyramid question wherever the two disagree, so both sub-agents get this list.

### 3. Load the pyramid

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill tool with `skill: "code-review-pyramid"`) to load the full layer definitions and their questions. If it isn't available, fall back to your own judgment of what belongs at each layer and continue — the split below still holds.

Loading it here rather than in the sub-agents is deliberate: it puts every layer's questions in *your* context, so step 5 can hand each sub-agent its own layer questions directly rather than relying on the sub-agent being able to reach the Skill tool itself.

### 4. Set the severity bar

Every finding either blocks the change or doesn't, and that split — not the pyramid layer — decides the verdict. Both sub-agents label against the same two definitions, so pass this rule verbatim into both briefs in step 5:

- **Requested change** — the author must act on it before this lands: a change that would cause a defect in production, an unintended breaking change to a user-facing contract, a spec requirement that is missing, partial, or implemented wrongly, or a hard breach of a documented repo standard.
- **Suggestion** — a reasonable author could decline it: judgment calls, optional refactors, naming and formatting preferences, docs or tests no standard mandates, follow-up ideas.

Severity is independent of layer. A Supporting finding can be a requested change, and a Foundation finding can be a suggestion. Layer sets the *ordering* within a list; severity sets *which list* a finding lands in.

### 5. Spawn both sub-agents in parallel

Issue both `Agent` calls in a single message, using the `general-purpose` agent type — each needs to read files and run `git`.

**Foundation sub-agent prompt** — include:

- The Layer 1 and Layer 2 questions, verbatim from the pyramid loaded in step 3.
- The diff command and commit list.
- The path or fetched contents of the spec, and the standards-source list from step 2.
- The severity rule from step 4, verbatim.
- The brief: "Work through every question above, not just the ones that surface first. These are the most expensive mistakes in this diff to unwind, so read deeply. Report findings citing `file:line`, each tagged with its pyramid layer and labeled `Requested change` or `Suggestion` per the severity rule above. Quote the spec line for every requirement that is missing, partial, or implemented wrongly, and separately flag behavior in the diff the spec never asked for. Read the repo's standards as a constraint on what 'correct' and 'consistent' mean here — cite the standard (file + rule) when one is what's breached, treat it as overriding any question above that it contradicts, and report a documented convention as settled rather than as a problem. Leave style, naming, formatting, and documentation review to the other reviewer. Open your report with one line stating whether you had a spec to check conformance against. Under 500 words."

**Supporting sub-agent prompt** — include:

- The Layer 3, 4, and 5 questions, verbatim from the pyramid loaded in step 3.
- The diff command and commit list.
- The standards-source list from step 2.
- The severity rule from step 4, verbatim.
- The brief: "Work through every question above, not just the ones that surface first. Documentation, tests, style, naming, and formatting are yours; API and implementation semantics belong to the other reviewer. The repo's standards are the second half of your checklist: they are the conventions the author was expected to follow, so cite the standard (file + rule) whenever the diff breaches one — a breached standard is a requested change, not a nit. Report documentation and test gaps first, then style. Report findings citing `file:line`, each tagged with its pyramid layer and labeled `Requested change` or `Suggestion` per the severity rule above. Open your report with one line answering 'are all tests passing' from an actual CI result, or stating it as unverified. Under 200 words."

### 6. Decide the verdict

Two caveats cap the verdict, because a clean approval should mean the review actually verified what it claims: the Foundation reviewer had no spec to check conformance against, or the Supporting reviewer reported test-passing status as unverified.

- **Request changes** — one or more requested changes.
- **Approved with suggestions** — no requested changes, and either at least one suggestion or at least one caveat.
- **Approved** — nothing to act on, conformance was verified against a spec, and tests were confirmed passing.

### 7. Report

Lead with the verdict, then a summary paragraph under all three — the fixed point and diff scope (commits, files), what the review verified, and any caveat that capped the verdict. Then the findings, merged from both sub-agents into two lists:

```markdown
## <Approved | Approved with suggestions | Request changes>

<summary paragraph>

### Requested changes
1. **[Impl. Semantics]** `svc/user.go:47` — <finding, then what to do about it>
2. **[Tests]** `svc/user_test.go` — <finding>

### Suggestions
1. **[Code Style]** `svc/user.go:12` — <finding>
```
