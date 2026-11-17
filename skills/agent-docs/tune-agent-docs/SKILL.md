---
name: tune-agent-docs
description: >
  Reviews every markdown file in a repository that steers an AI coding agent as one corpus, then
  tightens them. The corpus covers CLAUDE.md, AGENTS.md, GEMINI.md, `.cursor/rules/*.mdc`,
  `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md`, Kiro `.kiro/steering/*.md`,
  and files like them. Use when the user wants to audit, tune, reconcile, or clean up the
  instructions a repo gives its AI agents, or asks why an agent keeps missing, contradicting, or
  burning tokens on its own steering docs. Use it even when the user names one file, because the
  value comes from reading that file next to its neighbors. Checks terminology consistency,
  front-loaded directives, the size of each doc against the stated limit of its format,
  always-loaded content the harness can scope, duplicated guidance, no-op instructions, and the
  degrees of freedom of each instruction. For one `SKILL.md` on its own, use review-skill instead.
argument-hint: "[path or glob, optional. Defaults to the whole repo]"
allowed-tools: [Read, Glob, Grep, Edit, Write, AskUserQuestion]
---

# Tune Agent Docs

An agent that starts work in a repo often loads several steering docs into one context window. The agent pays on every run when these docs disagree or bury their point. It pays the same when they use two words for one thing, or demand more rigor than the task needs. Treat every steering doc in the repo as one corpus.

Work in two phases: **critique first, edit second**. Build the full picture, present the findings, and only then touch a file.

## Find the corpus

Use `Glob` for these conventions, including nested per-directory copies:

- `CLAUDE.md`, `CLAUDE.local.md`, and `.claude/rules/**/*.md`
- `AGENTS.md`, `GEMINI.md`, `.cursor/rules/**/*.mdc`, and `.cursorrules`
- `.clinerules` or `.clinerules/**/*.md`, `.windsurfrules` or `.windsurf/rules/**/*.md`, and `.devin/rules/**/*.md`
- `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, and `.kiro/steering/**/*.md`

Include each local or gitignored variant next to its checked-in counterpart, because that pair is a common duplication site.

Then follow every pointer that a corpus doc makes to another markdown file: a "See `docs/x.md` for..." link, an `@import`, or a relative link in a "Where things are" or "further reading" section. Pull each target in without asking, even when it matches no convention, because the doc that points to it delegates its steering there.

Then sweep the remaining `.md` files for agent-directed text that matches no convention and no pointer. The signs are imperative language addressed to "you", "the agent", or "Claude", and frontmatter with an inclusion-like key. Put every candidate to the user with `AskUserQuestion` before you fold any in. Include the ones you are sure about, because the user decides the scope. An unfamiliar file that turns out to be a changelog or a design doc must not get graded as steering prose.

Read every file in the corpus in full, including each pointer target. A line count or a partial skim is not a read, because the findings live in how these docs relate to each other.

## Load the lenses

- **The standards**: find the authoring conventions that govern this corpus, in a `CLAUDE.md`, a `CONTRIBUTING.md`, a docs or skill-authoring style guide, or an equivalent file. Apply them to every doc in the corpus, not only to the docs they were written for. Do not raise a convention the repo already settled as a finding. Take the conventions only from the repo under review, not from another repo's `CLAUDE.md` in your context or from the user's global conventions.
- **Cross-harness format knowledge**: read `references/steering-formats.md` once per review. It holds the frontmatter, the scoping mechanism, and the size ceiling of each format, plus general principles from Anthropic's Skill authoring guidance. Formats change, so never rebuild these facts from memory.

## What to check

- **Token budget**: check this first, because it is the largest lever on what an agent pays before real work. Compare each doc against the ceiling of its own format in the reference. A doc under its ceiling still owes every line a justification against the checks below. Then find content that loads unconditionally, through `alwaysApply: true`, `inclusion: always`, or an unscoped `.claude/rules/*.md`, but matters for one file type or directory. Move it into the conditional-loading mechanism of the harness. Never count a split into `@import` statements as a fix, because imports still load in full.
- **Duplication**: one meaning, one home. Compare guidance by meaning, not by string match, because paraphrase is the common case. Check inside each doc too, where one rule restated three sections apart reads as three rules. Duplication pays its token cost twice, and it becomes a contradiction the day one copy gets edited. Keep one canonical copy plus a pointer or an import, at the narrowest scope that still covers everywhere the guidance applies. Where a restatement circles one idea three times, the repair is often a single word that the model already carries priors for. Repeat that word as a term instead of re-explaining the idea.
- **No-ops**: an instruction the model already follows by default changes nothing and still costs context every session. Examples are "write clean code", "follow best practices", "be careful when editing files", and "think before you change things". Test each sentence on its own: does an agent that never saw this doc behave differently? A live section often carries dead sentences. Delete each sentence that fails the test. A reworded no-op is still a no-op, so do not rewrite it tighter. This is usually the largest single cut available.
- **Structural fit per harness**: when a size or leanness finding calls for a split or a narrower scope, recommend only a mechanism the format supports, per the reference: a nested `CLAUDE.md`, a glob-scoped `.mdc` rule, or a Kiro `fileMatch` file. Where the harness has none, report the size as a leanness finding. Also flag a multi-step procedure in an always-loaded doc. That doc holds what is true every session, and a workflow belongs in an on-demand skill or a path-scoped rule.
- **Consistent terminology**: across the corpus, one role, tool, or convention carries one name. Hunt synonym drift, such as `the agent` against `Claude` against `the assistant`, `skill` against `capability` against `workflow`, and `worktree` against `workspace`. A term used two ways inside one doc is the same defect.
- **Front-loading**: open each instruction, bullet, header, and frontmatter `description` on its actionable verb or keyword. Leading context makes a skimming agent miss the point, and it weakens the retrieval match of the harness.
- **Degrees of freedom**: match the specificity of each instruction to how fragile the thing it governs is. An exact script constrains an agent that needs to reason about a judgment call. Loose prose invites improvisation around an exact operation that must run in order.
- **Negation**: a prohibition names the banned behavior into the agent's context, where it competes with the ban. A doc built from `never`, `do not`, and `MUST NOT` walls must state the behavior it wants instead. Keep a prohibition only for a guardrail with no positive phrasing, and pair it with what to do in its place.
- **Leanness and staleness**: cut what the agent can derive from the codebase, such as directory layouts, dependency lists, and architecture overviews. Keep what it cannot derive, such as pitfalls, rationale, and conventions that differ from the defaults of the tool. A derivable fact is true but free to look up, and a no-op is behavior the model already has. Flag time-boxed conditionals such as "until the migration finishes, do X", because they go stale in silence. A dated fold or an old-patterns section ages better.
- **Frontmatter validity**: check the frontmatter of each doc against the schema of its format in the reference. Examples are a Kiro `inclusion` value outside `always`, `fileMatch`, and `manual`, and a Cursor `.mdc` file that lacks the field of its activation mode. A `SKILL.md` `name` past its length or charset limit is a third.

## Resolve conflicts by scope, not by asking

When two docs contradict each other, resolve it the way the harnesses layer context at runtime. The doc scoped to the narrower area wins for that area over a repo-wide doc that always loads. A narrower doc is a nested `CLAUDE.md`, a rule scoped by `fileMatch` or `paths`, or a glob-scoped `.mdc` file. Fall back to `AskUserQuestion` only when both sides sit at the same scope and precedence gives no signal.

## Present findings, then apply

Open with a one-line verdict. Then list the findings ranked by severity, not grouped by check:

- **Blocking**: an active contradiction between docs, an instruction that will make the agent do the wrong thing, or a doc past a hard format limit. The harness truncates the tail of such a doc in silence.
- **Important**: terminology drift, a buried directive, a no-op, an oversized or always-loaded doc that its harness can scope, or one meaning kept in two places. It also covers a prohibition wall with no positive target, miscalibrated degrees of freedom, and a convention violation.
- **Nit**: cosmetic polish.

Tag each finding with its dimension, its exact file, and its line. Then offer to apply every blocking and important finding, everything, or a subset the user picks. Edit the files directly. A terminology or front-loading fix must land in every occurrence in every corpus file. A partial rename leaves the corpus less consistent than before.

## Before you finish

Re-read the diff as a skeptical teammate, and look for these errors:

- A rename that missed a nested `CLAUDE.md` or a nested rule file.
- A degrees-of-freedom fix that overcorrected into the opposite miscalibration.
- A "contradiction" that was two docs correctly scoped to different areas, now wrongly collapsed into one.
- A scoping fix that narrowed the `paths`, `globs`, or `fileMatchPattern` of a rule past the areas that need it.
- A no-op that got reworded instead of deleted.
- A paraphrase collapsed onto the broader of the two docs, so the surviving copy now applies where the guidance never did.
