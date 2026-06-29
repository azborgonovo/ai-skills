---
name: review-feature-suite
description: >
  Reviews a whole suite of `.feature` files against each other and reconciles them — cross-file
  consistency auditing for Gherkin/BDD. Checks that the suite holds one shared language across
  files, reuses step phrasing instead of duplicating it, carries no contradictory or redundant
  scenarios, and stays consistent in tags, naming, and data. Use whenever the user has multiple
  existing `.feature` files (a Cucumber, SpecFlow, Behave, or plain Gherkin suite) and wants to
  check, audit, align, reconcile, or de-duplicate them as a set — including phrasings like "our
  features use different words for the same thing", "do these scenarios contradict each other",
  "find duplicate steps across our features", or "make our feature files consistent". Do not use for
  authoring or refining a single feature in isolation — that is a single-feature concern, handled by
  a skill like define-behavior where one is available.
argument-hint: "[path to a features directory or glob]"
allowed-tools: [Read, Glob, Grep, Edit, AskUserQuestion]
---

# Review Feature Suite

A single `.feature` file can be flawless on its own and still be wrong in the company of its neighbors. The value of a BDD suite is that the whole team shares one language all the way down into the code, that step definitions are written once and reused, and that the features stand as living documentation that doesn't contradict itself. Those properties only exist *across* files, so they can only be checked across files. That is this skill's entire job: read every `.feature` file as one corpus and reconcile it.

Work in two phases: **critique first, edit second.** Build the picture, surface the findings, settle the judgment calls with the user, and only then change files.

## Build the inventory first

The findings live in the relationships between files, so don't read file-by-file and judge as you go — assemble a compact cross-file picture first, then reason over it. Use `Glob` to enumerate the `.feature` files from the path or glob the user gave (default to searching the project), then use `Grep` to pull the raw material across all of them at once rather than holding every full file in context:

- **Steps** — every `Given`/`When`/`Then`/`And`/`But` line, so you can see which phrasings recur and which are near-duplicates.
- **Tags** — every `@tag`, to spot the taxonomy and its typos.
- **Titles** — every `Feature:` and `Scenario:`/`Scenario Outline:` line.
- **Actors and data** — the roles, currency/number/date values, and named entities that recur, so drift in how they're written stands out.

Grep is the deterministic extraction layer; your judgment is what turns that inventory into findings.

## What to check

Four clusters. The first two are usually mechanical to fix once the canonical form is chosen; the third is judgment that you surface rather than resolve; the fourth is lint.

**Shared language.** The same role, object, or state must carry the same name everywhere, reusing the words the business already uses. Hunt synonym drift (`order`/`purchase`/`cart`, `user`/`customer`/`shopper`, `sign in`/`log in`/`authenticate`) and role-name drift (`Editor` vs `editor` vs `Content Editor`). Also flag roles or states that scenarios lean on but the suite never introduces. The fix is to pick one canonical term per concept and use it everywhere — but only after confirming the words really name one thing (see below).

**Step-library consistency.** Steps that mean the same thing should be phrased identically, because each distinct phrasing tends to spawn its own step definition in the automation layer; drift here quietly doubles the code behind the suite. Cluster steps by *behavior*, not by string similarity — `Given I am logged in` and `Given the user is signed in` are the same step despite low lexical overlap, while `Given the cart holds 3 items` and `Given the cart holds 4 items` are deliberately different despite high overlap. Lexical similarity is neither necessary nor sufficient; judge by what the step does. Also flag parameterization drift, where one file hardcodes a value another parameterizes.

**Logical consistency.** This is where the suite can be actively misleading. Look for contradictions — two scenarios that assert different outcomes for the same precondition and action (`SPRING10` gives 10% off in one feature, 15% in another; a rule stated one way here and the opposite there). Look for duplicated behavior specified in two places, which drifts apart under maintenance. Look for orphaned preconditions — a `Given the user has a premium subscription` whose own behavior (how one becomes premium) is specified nowhere. Surface these; do not silently resolve them, because picking a side is a business decision, not a cleanup.

**Conventions and metadata lint.** Consistency in the connective tissue: file naming (kebab-case aligned with the feature title, one `Feature` per file), tag taxonomy (typos like `@regresion`, the same idea tagged two ways), unit/currency/date formatting and the phrasing of observable outcomes (`€72` vs `72 euros`), and scenario-title style (declarative "what is true" rather than "test X", and no duplicate titles across files).

## Resolve ambiguity before fixing

A suite-wide rename is only as good as the canonical form behind it, and several of those choices are genuinely the user's to make — so collect every ambiguous point and ask, via `AskUserQuestion`, before proposing edits. Guessing here is expensive: a wrong canonical term or a silently-chosen side in a contradiction propagates a confident mistake across every file at once.

Ask about, at least:

- **Which synonym is canonical** when several name one concept — don't assume the most frequent one is the one the business prefers.
- **Whether a near-name distinction is intentional** — `order` vs `cart`, `customer` vs `account`, `submit` vs `confirm` may be real product distinctions the suite is right to keep, not drift to collapse.
- **Which outcome is correct** in each contradiction — you surface the conflict; the user decides the truth.
- **Whether duplicated behavior is redundant or deliberate** before merging it away.

Batch these into as few rounds as you can so the user isn't drip-fed questions. Carry the answers into the fixes.

## Critique first, fix second

Present findings before touching anything, ranked by severity rather than grouped by cluster, so the user sees what matters most first:

- **Blocking** — contradictions and anything that makes the suite specify the wrong behavior.
- **Should-fix** — vocabulary drift, duplicate/near-duplicate steps, orphaned preconditions, real convention breaks.
- **Nit** — cosmetic lint.

Tag each finding with its cluster and point at the specific files and lines. Then offer to apply — all blocking and should-fix, everything, or a subset the user picks — and make the edits directly. Two things to get right when applying:

- A vocabulary or step normalization must hit **every** occurrence across **all** files, not just the ones you happened to quote. A half-applied rename leaves the suite more inconsistent than before.
- **Never** auto-resolve a contradiction — apply a side only after the user has chosen it (see *Resolve ambiguity before fixing*).

## Before you finish

Re-read your changes as a skeptical teammate hunting the failures that survive a first pass:

- A rename that missed a file, a `Background`, or a `Scenario Outline` placeholder — leaving the drift you set out to remove.
- A normalization that flattened an intentional distinction the user actually wanted kept.
- A "contradiction" that was really two legitimately different contexts, now wrongly reconciled.
- A canonical term you picked yourself instead of confirming with the user.
