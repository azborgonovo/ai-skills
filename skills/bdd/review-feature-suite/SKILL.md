---
name: review-feature-suite
description: >
  Audits a whole suite of Gherkin `.feature` files against each other for cross-file BDD
  consistency, and reconciles them. Makes sure that the suite holds one shared language, reuses step
  phrasing instead of duplicating it, carries no contradictory or redundant scenarios, and stays
  consistent in tags, naming, and data. Use when the user has several `.feature` files, in a
  Cucumber, SpecFlow, Behave, or plain Gherkin suite, and wants to audit, align, reconcile, or
  de-duplicate them as a set. Use it also when the user says "our features use different words for
  the same thing", "do these scenarios contradict each other", "find duplicate steps across our
  features", or "make our feature files consistent". To author or refine one feature on its own,
  use define-behavior.
argument-hint: "[path to a features directory or glob]"
allowed-tools: [Read, Glob, Grep, Edit, AskUserQuestion]
---

# Review Feature Suite

A `.feature` file can be correct on its own and still be wrong next to its neighbors. A BDD suite has value through three properties: the team shares one language, writes each step definition once, and keeps living documentation that does not contradict itself. Those properties exist only across files. So read every `.feature` file as one corpus, and reconcile it.

## Build the inventory first

Assemble a compact cross-file picture before you judge anything. Use `Glob` to enumerate the `.feature` files from the path or glob that the user gave. If the user gave neither, search the project. Then use `Grep` to pull the raw material out of all files at once, instead of holding every full file in context:

- **Steps**: every `Given`, `When`, `Then`, `And`, and `But` line, so you see which phrasings recur and which are near-duplicates.
- **Tags**: every `@tag`, so you see the taxonomy and its typos.
- **Titles**: every `Feature:`, `Scenario:`, and `Scenario Outline:` line.
- **Actors and data**: the roles, the currency, number, and date values, and the named entities that recur, so drift in how they are written stands out.

## What to check

**Shared language.** The same role, object, or state must carry the same name everywhere, and it must reuse the words that the business already uses. Hunt synonym drift, such as `order` against `purchase` against `cart`, `user` against `customer` against `shopper`, and `sign in` against `log in` against `authenticate`. Hunt role-name drift too, such as `Editor` against `editor` against `Content Editor`. Also flag a role or state that scenarios lean on and the suite never introduces. The fix is one canonical term per concept, used everywhere.

**Step-library consistency.** Steps that mean the same thing must use identical phrasing, because each distinct phrasing tends to spawn its own step definition in the automation layer. Cluster steps by *behavior*, not by string similarity. `Given I am logged in` and `Given the user is signed in` are the same step, despite low lexical overlap. `Given the cart holds 3 items` and `Given the cart holds 4 items` are deliberately different, despite high overlap. Also flag parameterization drift, where one file hardcodes a value that another file parameterizes.

**Logical consistency.** Look for contradictions, which are two scenarios that assert different outcomes for the same precondition and action. One example is `SPRING10` that gives 10% off in one feature and 15% off in another. Another is a rule stated one way here and the opposite way there. Look for duplicated behavior specified in two places, because the two copies drift apart under maintenance. Look for orphaned preconditions. One example is `Given the user has a premium subscription`, with no scenario that specifies how a user becomes premium. Report these, because picking a side is a business decision rather than a cleanup.

**Conventions and metadata lint.** File naming must use kebab-case aligned with the feature title, with one `Feature` per file. The tag taxonomy must carry no typos such as `@regresion`, and no single idea tagged two ways. Units, currency, dates, and the phrasing of observable outcomes must match, so `€72` and `72 euros` cannot both appear. Scenario titles must be declarative and say what is true, rather than "test X", and no title can repeat across files.

## Present the findings

Change no file yet. Rank the findings by severity rather than group them by cluster, so the user sees what matters most first:

- **Blocking**: a contradiction, or anything that makes the suite specify the wrong behavior.
- **Important**: vocabulary drift, a duplicate or near-duplicate step, an orphaned precondition, or a real convention break.
- **Nit**: cosmetic lint.

Tag each finding with its cluster, and point at the specific files and lines.

## Settle the judgment calls

Several canonical choices belong to the user, and a wrong one spreads to every file at once. Collect every ambiguous point, and ask through `AskUserQuestion` before you edit. Ask about at least these four things:

- **Which synonym is canonical** for a concept that several names share. Do not assume that the most frequent one is the one that the business prefers.
- **Whether a near-name distinction is intentional.** `order` against `cart`, `customer` against `account`, and `submit` against `confirm` can be real product distinctions.
- **Which outcome is correct** in each contradiction. The user decides the truth.
- **Whether duplicated behavior is redundant or deliberate**, before you merge it away.

In the same round, ask which findings to apply: every blocking and important finding, everything, or a subset the user picks. Use as few rounds as you can.

## Apply the edits

Make the edits directly, and carry the answers into them:

- A vocabulary or step normalization must hit **every** occurrence in **all** files, not only the ones you quoted.
- **Never** resolve a contradiction automatically. Apply a side only after the user chooses it.

## Before you finish

Re-read your changes as a skeptical teammate, and hunt for these failures:

- A rename that missed a file, a `Background`, or a `Scenario Outline` placeholder, which leaves the drift that you set out to remove.
- A normalization that flattened an intentional distinction that the user wanted to keep.
- A "contradiction" that was two legitimately different contexts, now wrongly reconciled.
- A canonical term that you picked yourself instead of confirming with the user.
