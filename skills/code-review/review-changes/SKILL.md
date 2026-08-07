---
name: review-changes
description: >
  Reviews the diff between HEAD and a fixed point (commit, branch, tag, or merge-base) using the Code
  Review Pyramid, split across two parallel sub-agents by cost-of-change — Foundation (API and
  implementation semantics, including conformance to the originating issue/spec) and Supporting
  (documentation, tests, and code style) — then reports them base-first. Use when the user wants to
  review a branch, a PR, work-in-progress changes, or asks to "review since X".
---

Pyramid-driven review of the diff between `HEAD` and a fixed point the user supplies.

The [Code Review Pyramid](../code-review-pyramid/SKILL.md) orders review attention by how expensive a mistake is to unwind: API semantics at the base, code style at the apex. This skill splits along that grain into two **parallel sub-agents**, so they don't pollute each other's context:

- **Foundation** — Layers 1-2 (API Semantics, Implementation Semantics), where a mistake is costly and needs the deepest read. Spec conformance lives here, since Layer 2's first question is "does it satisfy the original requirements?"
- **Supporting** — Layers 3-5 (Documentation, Tests, Code Style), where the pyramid says to lean on automation and spend proportionally less manual attention.

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

If the user says there isn't one, the Foundation sub-agent still runs — it skips the requirements check and reports the review as spec-less. Say so in the final report too, so a reader knows conformance was never assessed.

**The standards** — anything in the repo documenting how code should be written: `CODING_STANDARDS.md`, `CONTRIBUTING.md`, `CLAUDE.md`, or an equivalent. A documented repo standard overrides a generic pyramid question wherever the two disagree, so both sub-agents get this list.

### 3. Load the pyramid

If the `code-review-pyramid` skill is listed in the available skills, invoke it (via the Skill tool with `skill: "code-review-pyramid"`) to load the full layer definitions and their questions. If it isn't available, fall back to your own judgment of what belongs at each layer and continue — the split below still holds.

Loading it here rather than in the sub-agents is deliberate: it puts every layer's questions in *your* context, so step 4 can hand each sub-agent its own layer questions directly rather than relying on the sub-agent being able to reach the Skill tool itself.

### 4. Spawn both sub-agents in parallel

**Foundation sub-agent prompt** — include:

- The full diff command and commit list.
- The Layer 1 and Layer 2 questions, **copied verbatim from the pyramid you loaded in step 3** — the sub-agent has no other access to them.
- The path or fetched contents of the spec, and the standards-source list from step 2.
- The brief: "Report — per file/hunk where relevant — (a) API-surface and contract problems: leaked internals, inconsistency, breaking changes to user-facing parts; (b) implementation problems: incorrect logic, unnecessary complexity, concurrency or error-handling gaps, security, observability, dependencies that don't pull their weight; (c) spec requirements that are missing, partial, or implemented wrongly — quote the spec line for each; (d) behavior in the diff the spec didn't ask for (scope creep). Cite the standard (file + rule) when a documented repo standard is what's breached, and treat that standard as overriding any pyramid question it contradicts. Distinguish hard violations from judgment calls. Skip anything tooling enforces. Under 400 words."

**Supporting sub-agent prompt** — include:

- The diff command and commit list.
- The Layer 3, 4, and 5 questions, copied verbatim from the loaded pyramid.
- The standards-source list from step 2.
- The brief: "Report (a) new behavior that should be documented and isn't, across whichever doc kinds this repo keeps; (b) new behavior that isn't reasonably tested, corner cases left uncovered, or the wrong test level for the job; (c) style and naming that breaks a documented convention or crosses into a real readability problem. Report only what a linter, formatter, or CI gate would *not* already catch — this end of the pyramid is meant to be automated, so a finding tooling already enforces is noise. Under 200 words."

### 5. Aggregate

Present the two reports under `## Foundation — API & Implementation Semantics` and `## Supporting — Documentation, Tests & Style`, verbatim or lightly cleaned, Foundation first.

Rank base-first: a Foundation finding outranks a Supporting one by construction — that ordering is the pyramid's whole claim, and the section order already carries it. Within a section, order by severity.

A sub-agent's report is a claim, not a fact. Before relaying a quoted hunk or a `file:line` reference, confirm it actually appears in the diff — a confidently misquoted snippet reads exactly like a real finding.

End with a one-line summary: the count per section, and the worst Foundation finding (if any). Note there too if the review ran without a spec.

## Why split by layer

A single reviewer holding all five layers at once tends to fill its report with the cheap findings — a naming nit is easier to spot and state than a contract that leaks an internal type. Isolating the base from the apex protects the expensive findings twice over: in the sub-agent's context, where style observations can't crowd out the deeper read, and in the reader's attention, where the section order says plainly which findings are worth their time first.

That's also why the two sections get different word budgets. Equal space per layer would flatten the pyramid into a checklist and quietly contradict the framework it's built on.
