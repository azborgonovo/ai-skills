---
name: tune-agent-docs
description: >
  Reviews every markdown file in a repository that steers an AI coding agent — CLAUDE.md, AGENTS.md,
  GEMINI.md, `.cursor/rules/*.mdc`, `.clinerules`, `.windsurfrules`/`.windsurf/rules`,
  `.github/copilot-instructions.md`, Kiro's `.kiro/steering/*.md`, and similar — together as one
  corpus, then tightens them. Use whenever the user wants to audit, tune, reconcile, or clean up the
  instructions a repo gives its AI agents, or asks why an agent keeps missing or contradicting its
  own steering docs — even when they only name one file, since the value is in reading it alongside
  its neighbors. Checks vocabulary consistency and leading-word front-loading across every doc,
  applies the repo's own doc-authoring conventions where they hold generally, and calibrates each
  instruction's degrees of freedom to the fragility of what it governs. Do not use for a single
  `SKILL.md` in isolation — that is review-skill's job.
argument-hint: "[path or glob, optional — defaults to the whole repo]"
allowed-tools: [Read, Glob, Grep, Edit, AskUserQuestion]
---

# Tune Agent Docs

A repo's AI-steering docs are read by whatever agent shows up, often several loaded into one context window at once — a root `CLAUDE.md` is rarely the only text an agent takes as instruction. When these docs disagree, use different words for the same thing, bury their point, or demand more rigor than the task needs, the agent pays that tax silently, on every run. This skill treats every steering doc in the repo as one corpus, combining review-skill's read-then-tighten mechanics with review-feature-suite's cross-file reconciliation.

Work in two phases: **critique first, edit second**. Build the full picture, surface the findings, and only then touch a file.

## Find the corpus

Use `Glob` for the conventions each harness actually recognizes today — see `references/steering-formats.md` for the current list and each format's own frontmatter and inclusion rules: `CLAUDE.md` (including nested per-directory copies and `.claude/rules/**/*.md`), `AGENTS.md`, `GEMINI.md`, `.cursor/rules/**/*.mdc`, `.cursorrules`, `.clinerules` or `.clinerules/**/*.md`, `.windsurfrules` or `.windsurf/rules/**/*.md`, `.devin/rules/**/*.md`, `.github/copilot-instructions.md`, `.kiro/steering/**/*.md`.

Then sweep the remaining `.md` files in the repo for ones that read as agent-directed despite not matching a known convention — imperative language addressed to "you"/"the agent"/"Claude", or frontmatter carrying an inclusion-like key. Confirm these with the user via `AskUserQuestion` before folding them into the review; an unfamiliar file that turns out to be a changelog or a design doc shouldn't get graded as steering prose.

Read every file in the corpus in full. The findings live in how these docs relate to each other, not in any single one, so build the picture before judging.

## Load the lenses

- **This repo's own conventions** — if a `CLAUDE.md` in the repo carries doc- or skill-authoring guidance, apply it to every doc in the corpus, not only the ones it was written for. A repo that holds its `SKILL.md` files to a standard (no decorative `---`, bold reserved for lead-ins and directives, no hard-wrapping, positive phrasing over bare negatives, explain *why* over `MUST`/`NEVER` walls) should hold its `AGENTS.md` to the same one.
- **Cross-harness format knowledge** — `references/steering-formats.md` holds each recognized format's frontmatter fields, inclusion or scoping mechanism, and size guidance, sourced from each vendor's own docs, plus a set of format-agnostic principles from Anthropic's Skill authoring guidance. Read it once per review; don't re-derive it from training-data recall, since these formats change.

## What to check

- **Vocabulary consistency** — across the whole corpus, the same role, tool, or convention must carry the same name. Hunt synonym drift (`the agent`/`Claude`/`the assistant`, `skill`/`capability`/`workflow`, `worktree`/`workspace`) the way review-feature-suite hunts it across `.feature` files. A term used two ways inside a single doc is the same defect at smaller scale.
- **Leading words** — does each instruction front-load its actionable verb or keyword instead of burying it after throat-clearing? This is review-skill's triggering check, generalized past `description` fields: a bullet, a header, or a frontmatter `description` that leads with context before the directive makes a skimming agent, or the harness's own retrieval match, miss the point.
- **Degrees of freedom** — match each instruction's specificity to how fragile the thing it governs actually is. A judgment call dressed up as an exact, low-freedom script constrains an agent that should be reasoning; an exact, must-follow-in-order operation left as loose, high-freedom prose invites improvisation where none belongs.
- **Leanness and staleness** — flag restatements of what any capable agent already knows, and flag time-boxed conditionals ("until the migration finishes, do X") that will silently go stale; a dated fold or an old-patterns section ages better than a live-sounding conditional.
- **Structural fit per harness** — judge a doc's organization only against what its own format actually supports, per `references/steering-formats.md`. A bloated, multi-concern file is a real finding wherever its harness can split or scope it (a nested `CLAUDE.md`, a glob-scoped `.mdc` rule, a Kiro `fileMatch` steering file); where the harness has no such mechanism, don't recommend one it can't use.
- **Frontmatter validity** — each doc's own frontmatter, checked against its format's actual schema: a Kiro `inclusion` value outside `always`/`fileMatch`/`manual`, a Cursor `.mdc` missing the field its activation mode depends on, a `SKILL.md` `name` that violates the character or charset limit.

## Resolve conflicts by scope, not by asking

When two docs give contradictory guidance for the same thing, resolve it the way these harnesses actually layer context at runtime: the doc scoped to the narrower area — a nested `CLAUDE.md`, a `fileMatch`/`paths`-scoped rule, a glob-scoped `.mdc` file — wins over a repo-wide, always-loaded one, for the area it covers. Fall back to `AskUserQuestion` only when both sides sit at the same scope and precedence gives no signal; that is a genuine tie, not a shortcut around judgment.

## Present findings, then apply

Open with a one-line verdict, then list findings ranked by severity, not grouped by check:

- **Blocking** — active contradictions between docs, or an instruction that will make the agent do the wrong thing.
- **Should-fix** — vocabulary drift, buried leading words, miscalibrated degrees of freedom, convention violations.
- **Nit** — cosmetic polish.

Tag each finding with its dimension and the exact file and line. Then offer to apply — all blocking and should-fix, everything, or a subset the user picks — and edit directly. A vocabulary or leading-word fix must land in every occurrence across every file in the corpus; a partial rename leaves the corpus more inconsistent than before.

## Before you finish

Re-read the diff as a skeptical teammate: a rename that missed a nested `CLAUDE.md` or nested rule file; a degrees-of-freedom fix that overcorrected into the opposite miscalibration; a "contradiction" that was really two docs correctly scoped to different areas, now wrongly collapsed into one.
