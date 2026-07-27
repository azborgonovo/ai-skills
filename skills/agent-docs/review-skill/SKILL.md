---
name: review-skill
description: >
  Reviews and audits an existing skill, then tightens it — a fast, static, read-only audit of a
  `SKILL.md`'s triggering, scope, structure, prose, and domain accuracy, with severity-ranked
  findings applied on approval. Use whenever the user wants to review, critique, audit, lint, tighten, or improve a skill
  they already have, fine-tune a skill drafted with skill-creator, or asks why a skill is too
  verbose, won't trigger, or feels off — even when they just paste a SKILL.md and ask for feedback.
  Defers the empirical loop (running evals, benchmarking, the automated description optimizer,
  packaging) to skill-creator; this is the static counterpart that reads rather than measures.
argument-hint: "[skill name or path to a SKILL.md]"
allowed-tools: [Read, Glob, WebSearch, WebFetch, Bash, Edit, Write]
---

# Review Skill

Audit an existing skill against how good skills actually behave, then tighten it — a close reading that surfaces what undermines the skill and fixes it on the user's say-so. When the user wants measured triggering accuracy or eval-graded iteration, hand off to skill-creator, which owns the empirical description-optimizing loop; don't rebuild that loop here.

Work in two phases: **critique first, edit second.** Never rewrite the skill before the user has seen the findings and chosen what to apply.

## Resolve the target

Take the skill from `$ARGUMENTS` — a skill name (resolve to `skills/<name>/SKILL.md` or the installed `~/.claude/skills/<name>/SKILL.md`) or a direct path. With no argument, review the skill in progress: the `SKILL.md` most recently edited this session or showing in `git status`; if that's ambiguous, confirm which one before reviewing. Read the whole bundle, not just `SKILL.md` — note any `scripts/`, `references/`, `assets/`, and `evals/`, since their presence (or absence) is itself a finding.

## Load the lenses

Two lenses sharpen the review when available. Use each only if present, and do not reconstruct it inline when it's missing — a partial review beats a duplicated rubric that drifts out of sync.

- **Project conventions** — if the repo has a `CLAUDE.md` with skill-authoring guidance, read it and treat its rules as binding for this review (this repo's, for instance, bans `---` section separators, reserves bold for lead-ins and directives, and prefers explaining *why* over `MUST` walls).
- **Shared vocabulary** — if the `writing-great-skills` skill is installed (use `Glob` to find its `GLOSSARY.md`), read it and run the review in its terms: diagnose with its failure-mode catalogue — premature completion, duplication, sediment, sprawl, no-op — and name those terms in findings so they trace back to a single source of truth. If it isn't installed, review with the dimensions below and skip the borrowed terms.

## What to review

Walk these dimensions and collect concrete findings, each tied to specific lines:

- **Triggering** — does the `description` front-load the skill's leading word and cover the real branches a user would actually phrase, without false-trigger overlap with neighboring skills? Flag both gaps and collisions. Static smell-test only; for a measured trigger rate, defer to skill-creator.
- **Scope** — one clear responsibility, with an honest "do not use for…" boundary where it earns its place. Flag scope creep and overlap with skills that already exist.
- **Domain fidelity** — covered below.
- **Prose and leanness** — is the body objective, clear, and lean? Hunt no-ops sentence by sentence, collapse restatements, and call out sediment and sprawl. Recommend pushing deterministic or repetitive mechanics into `scripts/` and bulky reference into `references/` behind a pointer, so the always-loaded body stays legible.
- **Structure and frontmatter** — `name`/`description`/`argument-hint`/`allowed-tools` valid and consistent; headers that earn their place; no contradictory instructions; completion criteria that are checkable rather than vague.

## Domain fidelity

First judge whether the skill is domain-specific — a framework, cloud service, methodology, or business domain — or a generic process skill. Research only when it's domain-specific, and route by the kind of domain:

- Libraries, frameworks, SDKs, CLIs, cloud services → fetch current docs with the `ctx7` CLI (`npx ctx7@latest library "<name>"`, then `npx ctx7@latest docs <id> "<question>"`).
- Methodologies and business or domain concepts → `WebSearch` / `WebFetch` against reputable, primary sources.

Check the skill's terminology, definitions, and recommended patterns against what you find, and flag anything stale, misnamed, or contradicted by the source. Cite the source for every domain finding so the user can weigh its authority — don't correct domain wording from training data alone.

## Present findings, then apply

Open with a one-line verdict: is the skill sound, or does it need work? Then list findings ranked by severity, not grouped by dimension:

- **Blocking** — breaks triggering or correctness, or is contradicted by the domain sources.
- **Should-fix** — real weaknesses: scope creep, sprawl, duplication, vague completion criteria, convention violations.
- **Nit** — optional polish.

Tag each finding with its dimension, and for domain findings include the source consulted. Then offer to apply — all blocking and should-fix, everything, or a subset the user picks — and edit the files directly, showing what changed. Leave the empirical proof that it now triggers and passes evals to skill-creator.
