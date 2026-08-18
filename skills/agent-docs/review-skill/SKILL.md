---
name: review-skill
description: >
  Reviews and audits an existing skill, then tightens it — a fast, static, read-only audit of a
  `SKILL.md`'s triggering, scope, structure, prose, and domain accuracy, with severity-ranked
  findings applied on approval. Use whenever the user wants to review, critique, audit, lint, tighten, or improve a skill
  they already have, fine-tune a skill they just drafted, or asks why a skill is too verbose,
  won't trigger, or feels off — even when they just paste a SKILL.md and ask for feedback.
  Reads rather than measures: the empirical loop — running evals, benchmarking, automated
  description optimization, packaging — is out of scope.
argument-hint: "[skill name or path to a SKILL.md]"
allowed-tools: [Read, Glob, WebSearch, WebFetch, Bash, Edit, Write]
---

# Review Skill

Audit an existing skill against how good skills actually behave, then tighten it — a close reading that surfaces what undermines the skill and fixes it on the user's say-so. This is the static half: when the user wants measured triggering accuracy or eval-graded iteration, say that it needs an eval loop rather than building one here, and hand off to a skill-creation skill if one is available in the session.

Work in two phases: **critique first, edit second.** Never rewrite the skill before the user has seen the findings and chosen what to apply.

## Resolve the target

Take the skill from `$ARGUMENTS` — a skill name (glob `skills/**/<name>/SKILL.md`, so a repo that groups its skills under plugin or category directories still resolves, then the installed `~/.claude/skills/<name>/SKILL.md`) or a direct path. With no argument, review the skill in progress: the `SKILL.md` most recently edited this session or showing in `git status`; if that's ambiguous, confirm which one before reviewing. Read the whole bundle, not just `SKILL.md` — note any `scripts/`, `references/`, `assets/`, and `evals/`, since their presence (or absence) is itself a finding.

## What to review

**The standards** — before walking the dimensions, find the authoring conventions this skill is held to: a `CLAUDE.md`, `CONTRIBUTING.md`, a skill-authoring style guide, or an equivalent. A documented convention overrides a generic dimension below wherever the two disagree, and a convention the repo has settled is settled rather than a finding to raise.

Take them only from the repo the skill under review lives in. Resolve a path under `~/.claude/skills/` to its real target first (`readlink -f`) — an installed skill is often a symlink into a source repo, whose conventions do govern it. Only once the resolved path sits in no repo at all, review on the dimensions alone rather than holding the skill to the conventions of whatever repo your shell happens to be in, or to the user's global ones.

Then walk these dimensions and collect concrete findings, each tied to specific lines:

- **Triggering** — does the `description` front-load the skill's leading word and cover the real branches a user would actually phrase, without false-trigger overlap with neighboring skills? Flag both gaps and collisions. Static smell-test only — a measured trigger rate needs an eval run, which this skill does not do.
- **Scope** — one clear responsibility, with an honest "do not use for…" boundary where it earns its place. Flag scope creep and overlap with skills that already exist.
- **Domain fidelity** — covered below.
- **Prose and leanness** — is the body objective, clear, and lean? Hunt *no-ops* sentence by sentence — a line the model already obeys by default, which costs context to say nothing; delete the sentence rather than rewriting it tighter, since a reworded no-op is still a no-op. Collapse restatements: the same meaning in two places costs tokens now and drifts into a contradiction the day one copy gets edited. Call out *sediment*, the stale layers that settle because adding feels safe and removing feels risky, and *sprawl*, length itself even where every line is live and unique. Recommend pushing deterministic or repetitive mechanics into `scripts/` and bulky reference into `references/` behind a pointer, so the always-loaded body stays legible.
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

Tag each finding with its dimension, and for domain findings include the source consulted. Then offer to apply — all blocking and should-fix, everything, or a subset the user picks — and edit the files directly, showing what changed. Empirical proof that it now triggers and passes evals is a separate, measured exercise; say so rather than implying the audit established it.
