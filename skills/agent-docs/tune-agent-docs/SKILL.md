---
name: tune-agent-docs
description: >
  Reviews every markdown file in a repository that steers an AI coding agent — CLAUDE.md, AGENTS.md,
  GEMINI.md, `.cursor/rules/*.mdc`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md`,
  Kiro's `.kiro/steering/*.md`, and similar — together as one corpus, then tightens them. Use when
  the user wants to audit, tune, reconcile, or clean up the instructions a repo gives its AI agents,
  or asks why an agent keeps missing, contradicting, or burning tokens on its own steering docs —
  even when they name only one file, since the value is in reading it alongside its neighbors. Checks
  terminology consistency, front-loaded directives, each doc's size against its format's stated limit,
  always-loaded content the harness could scope, guidance duplicated across docs or restated within
  one, no-op instructions, and each instruction's degrees of freedom against what it governs. Do not
  use for a single `SKILL.md` in isolation — that is review-skill's job.
argument-hint: "[path or glob, optional — defaults to the whole repo]"
allowed-tools: [Read, Glob, Grep, Edit, Write, AskUserQuestion]
---

# Tune Agent Docs

A repo's AI-steering docs are read by whatever agent shows up, often several loaded into one context window at once — a root `CLAUDE.md` is rarely the only text an agent takes as instruction. When these docs disagree, use different words for the same thing, bury their point, or demand more rigor than the task needs, the agent pays that tax silently, on every run. This skill treats every steering doc in the repo as one corpus: read them all first, then reconcile and tighten them together.

Work in two phases: **critique first, edit second**. Build the full picture, surface the findings, and only then touch a file.

## Find the corpus

Use `Glob` for the conventions each harness actually recognizes today — see `references/steering-formats.md` for the current list and each format's own frontmatter and inclusion rules: `CLAUDE.md` and `CLAUDE.local.md` (including nested per-directory copies and `.claude/rules/**/*.md`), `AGENTS.md`, `GEMINI.md`, `.cursor/rules/**/*.mdc`, `.cursorrules`, `.clinerules` or `.clinerules/**/*.md`, `.windsurfrules` or `.windsurf/rules/**/*.md`, `.devin/rules/**/*.md`, `.github/copilot-instructions.md`, `.github/instructions/**/*.instructions.md`, `.kiro/steering/**/*.md`. Include the local/gitignored variant alongside its checked-in counterpart wherever a harness has one — that pairing is a common duplication site, not a reason to skip either file.

Then follow every pointer a doc already in the corpus makes to another markdown file — a "See `docs/x.md` for..." link, an `@import`, a relative link in a "Where things are" or "further reading" section. A steering doc that tells the agent to consult another file is delegating its steering to it, matching convention or not; pull the target in without asking, since the pointer itself is the corpus doc vouching for its relevance.

Then sweep the remaining `.md` files in the repo for ones that read as agent-directed despite not matching a known convention and not already pulled in by a pointer — imperative language addressed to "you"/"the agent"/"Claude", or frontmatter carrying an inclusion-like key. List every candidate this sweep turns up and put the full list to the user via `AskUserQuestion` before folding any of it in — don't pre-filter the list down to the ones you're unsure of and read the rest silently; the point of asking is the user's call on scope, not a formality to skip once the answer feels obvious. An unfamiliar file that turns out to be a changelog or a design doc shouldn't get graded as steering prose.

Read every file in the corpus in full, including every file pulled in by a pointer — a line count or a partial skim doesn't count as reading it. The findings live in how these docs relate to each other, not in any single one, so build the picture before judging.

## Load the lenses

- **The standards** — the authoring conventions this corpus is held to: a `CLAUDE.md`, `CONTRIBUTING.md`, a docs or skill-authoring style guide, or an equivalent. Apply them to every doc in the corpus rather than only the ones they were written for — a repo that holds its `SKILL.md` files to a standard should hold its `AGENTS.md` to the same one — and treat a convention the repo has settled as settled rather than a finding to raise. Take them only from the repo under review: another repo's `CLAUDE.md` sitting in your context, or the user's own global one, governs its own scope and not this corpus.
- **Cross-harness format knowledge** — `references/steering-formats.md` holds each recognized format's frontmatter fields, inclusion or scoping mechanism, and size guidance, sourced from each vendor's own docs, plus a set of format-agnostic principles from Anthropic's Skill authoring guidance. Read it once per review; don't re-derive it from training-data recall, since these formats change.

## What to check

- **Token budget** — the biggest lever a steering doc has over what an agent pays before it does any real work, and the one worth checking first. Check each doc's length against its own format's stated ceiling in `references/steering-formats.md` (200 lines for `CLAUDE.md`, 500 for `SKILL.md`, per-character caps for Windsurf, and so on). Treat sitting under the ceiling as a starting point rather than a pass: length is a cost whatever its cause, so a doc comfortably inside its limit still owes every line a justification against the checks below. Check whether content is loaded unconditionally — `alwaysApply: true`, `inclusion: always`, an unscoped `.claude/rules/*.md` — when it only matters for one file type or directory, instead of using the harness's own conditional-loading mechanism. A doc split into Claude Code `@import`s is easier to navigate but no smaller, since imports still load in full — don't credit that as a token-budget fix.
- **Duplication** — one meaning, one home. Compare guidance by what it *means*, not by string match: two docs that say the same thing in different words duplicate it as fully as two that say it verbatim, and paraphrase is the common case, since the docs were written at different times by different hands. The same defect runs inside a single doc, where one rule restated three sections apart reads as three rules. Include each checked-in doc against its local counterpart. Duplication pays its token cost twice today and is a contradiction waiting for the day only one copy gets edited; prefer one canonical doc plus a pointer or import over a second copy, and place the survivor at the narrowest scope that still covers everywhere the guidance applies. Where a restatement is really one idea circled three times, the repair is often a single word the model already carries priors for, repeated as a term rather than re-explained as a sentence.
- **No-ops** — an instruction the model already follows by default changes nothing and still costs context every session: "write clean code", "follow best practices", "be careful when editing files", "think before you change things". Steering docs accumulate these because adding a line feels free. Test each sentence in isolation against one question — would an agent that never saw this doc behave differently? Judge sentence by sentence rather than section by section, since a live section carries dead sentences. When a sentence fails, delete the sentence rather than rewriting it tighter; a reworded no-op is still a no-op, and reaching for the rewrite is what leaves these docs long. Be aggressive here — this is usually the largest single cut available.
- **Structural fit per harness** — once a token-budget or leanness finding calls for splitting or scoping a doc, judge the fix only against what its own format actually supports, per `references/steering-formats.md`: a nested `CLAUDE.md`, a glob-scoped `.mdc` rule, a Kiro `fileMatch` steering file. Where the harness has no such mechanism, don't recommend one it can't use — flag the bloat as a leanness finding instead. Also flag content that's actually a multi-step procedure rather than a standing fact: an always-loaded doc should hold what's true every session, not a workflow — that belongs in a skill, loaded on demand, or a path-scoped rule.
- **Consistent terminology** — across the whole corpus, the same role, tool, or convention must carry the same name. Hunt synonym drift (`the agent`/`Claude`/`the assistant`, `skill`/`capability`/`workflow`, `worktree`/`workspace`). A term used two ways inside a single doc is the same defect at smaller scale.
- **Front-loading** — does each instruction open on its actionable verb or keyword instead of burying it after throat-clearing? The check reaches past `description` fields: a bullet, a header, or a frontmatter `description` that leads with context before the directive makes a skimming agent, or the harness's own retrieval match, miss the point. Keep this separate from a *leading word* in the Leitwort sense — a compact pretrained concept the agent thinks with — which belongs to the duplication repair above.
- **Degrees of freedom** — match each instruction's specificity to how fragile the thing it governs actually is. A judgment call dressed up as an exact, low-freedom script constrains an agent that should be reasoning; an exact, must-follow-in-order operation left as loose, high-freedom prose invites improvisation where none belongs.
- **Negation** — a prohibition names the behavior it bans into the agent's context, where it competes with the ban. A doc built from `never`/`do not`/`MUST NOT` walls should state the behavior it wants instead; keep a prohibition for a guardrail that has no positive phrasing, and pair even that one with what to do in its place.
- **Leanness and staleness** — cut what the agent can already derive by reading the codebase itself — directory layouts, dependency lists, architecture overviews — and keep what it can't derive: pitfalls, rationale, and conventions that differ from the tool's defaults. This is a different cut from the no-op check: a derivable fact is true but free to look up, where a no-op is behavior the model already has. Flag time-boxed conditionals ("until the migration finishes, do X") that will silently go stale; a dated fold or an old-patterns section ages better than a live-sounding conditional.
- **Frontmatter validity** — each doc's own frontmatter, checked against its format's actual schema: a Kiro `inclusion` value outside `always`/`fileMatch`/`manual`, a Cursor `.mdc` missing the field its activation mode depends on, a `SKILL.md` `name` that violates the character or charset limit.

## Resolve conflicts by scope, not by asking

When two docs give contradictory guidance for the same thing, resolve it the way these harnesses actually layer context at runtime: the doc scoped to the narrower area — a nested `CLAUDE.md`, a `fileMatch`/`paths`-scoped rule, a glob-scoped `.mdc` file — wins over a repo-wide, always-loaded one, for the area it covers. Fall back to `AskUserQuestion` only when both sides sit at the same scope and precedence gives no signal; that is a genuine tie, not a shortcut around judgment.

## Present findings, then apply

Open with a one-line verdict, then list findings ranked by severity, not grouped by check:

- **Blocking** — active contradictions between docs, an instruction that will make the agent do the wrong thing, or a doc past a hard format limit (Windsurf's character caps, for instance) where the tail is silently truncated and never loads at all.
- **Should-fix** — terminology drift, buried directives, an oversized or unconditionally-loaded doc that its harness could scope, one meaning kept in two places or restated within one doc, no-op instructions, prohibition walls with no positive target, miscalibrated degrees of freedom, convention violations.
- **Nit** — cosmetic polish.

Tag each finding with its dimension and the exact file and line. Then offer to apply — all blocking and should-fix, everything, or a subset the user picks — and edit directly. A terminology or front-loading fix must land in every occurrence across every file in the corpus; a partial rename leaves the corpus more inconsistent than before.

## Before you finish

Re-read the diff as a skeptical teammate: a rename that missed a nested `CLAUDE.md` or nested rule file; a degrees-of-freedom fix that overcorrected into the opposite miscalibration; a "contradiction" that was really two docs correctly scoped to different areas, now wrongly collapsed into one; a scoping fix that narrowed a rule's `paths`/`globs`/`fileMatchPattern` past the areas that genuinely needed it, so the agent stops seeing guidance it still relies on; a no-op that got reworded instead of deleted, so the finding was reported and the line survived; a paraphrase collapsed onto the broader of the two docs, so the surviving copy now applies somewhere the guidance never did.
