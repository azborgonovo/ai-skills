---
name: pareto
description: >
  Process the user's request through the Pareto Principle: rank the causes generating most of the outcome, then spend roughly a fifth of the effort on the interventions that address them and report what that effort bought.
  User-only: runs only when explicitly invoked with /pareto [request]. When the user wants the highest-leverage slice of a large task, asks "what matters most here", wants to cut scope to what actually moves the needle, or wants an 80/20 pass over analysis, planning, test coverage, refactoring, or cleanup, suggest running this command.
  Not for work whose value depends on being complete — security fixes, compliance changes, migrations, or a specific reported bug.
argument-hint: "[request to process]"
disable-model-invocation: true
---

# Pareto

A small subset of causes produces most of the outcome. Find it, spend about a fifth of the effort against it, and show the cut so the user can argue with it.

Estimate roughly throughout. 80/20 is shorthand for "expect lumpiness," not a ratio to hit, and the two percentages needn't pair — a fifth of the effort might buy 95% of the outcome or 40%. A rough ranking that costs minutes beats a precise one that eats the budget it was meant to allocate.

## When this is the wrong tool

Some work is only worth doing completely: security fixes, compliance changes, migrations, a specific reported bug. 80% of a data migration is a corrupted database. Say the request isn't a Pareto candidate, then do it in full or ask.

Declining the framing means declining its shape too. Give a checklist to finish rather than a ranked list the reader can stop partway down — on completeness-critical work the skipped item is the one that matters.

Skip the ceremony entirely on anything small enough that ranking it costs more than it saves.

## Stage 1: rank the causes

Rank causes, not tasks. Work items sorted by payoff are just a to-do list; asking "what is generating most of this?" is what finds the one confused module behind eight scattered bug reports. Weight by cost or severity rather than raw counts, so a rare catastrophe isn't buried under a constant nuisance.

Rank on effect size alone — what a fix would cost plays no part yet. Letting "that's expensive" suppress a cause here buries the finding the user most needs. This produces a ranking, not a shortlist, so stage 2 can still reach into the tail.

Use whatever signal is already visible: error rates, coverage gaps, file churn, the shape of the request. When there's none, rank from priors and label it in a clause — an unlabeled guess reads as measurement.

**When the causes are evenly spread**, say so before spending anything. Five independent bug fixes are five bug fixes. Name the flatness and let the user choose between funding the whole job and taking an arbitrary slice.

## Stage 2: spend a fifth of the effort

Cost the interventions against the top causes, work down by outcome-per-effort until roughly a fifth of the full job's effort is spent, then stop. Effort is the budget; outcome is what you observe and report. The reverse rule — keep going until most of the outcome is covered — authorizes spending whatever it takes.

Both stages earn their place: ranking causes while ignoring cost recommends a rewrite every time, and ranking interventions without first finding causes drifts to cheap triviality — eight one-line fixes that leave the generator untouched.

**Spend the budget on the work, not on deciding what the work is.** The deliverable is the change the user asked for. Buy measurement only when it is cheap and decisive — a check that redirects the whole effort, not a survey that produces a plan. When the honest answer is that the budget buys diagnosis and no improvement, say so plainly as a tradeoff rather than handing over an investigation as though it were the work.

**An unaffordable root cause is a finding, not a skip.** When the biggest cause needs work that swamps the budget, name it with its price. "Most of these failures trace to the retry logic, and fixing it properly is about three days" is the one thing the user cannot get from the diff.

Sweep up near-free wins from the tail while you're in there, incidental to the vital few rather than becoming the work.

Correctness is not optional weight: a slice that leaves the build broken or a migration half-applied is negative value, so whatever keeps the work coherent belongs inside the budget.

## Two shapes of request

**Analysis, planning, review** — the budget caps investigation depth. Lead with the top causes at full depth, compress the tail, and name what you didn't examine. An analysis that hides its own shallowness is worse than a slower one.

**Actual work — coverage, refactoring, cleanup, fixes** — the budget caps the changes made. Do the subset, leave the rest untouched rather than half-applied, and report the line you drew.

## Report the cut

A few sentences, not a section per bullet:

- **The vital few causes** and how you ranked them.
- **What the budget bought** — rough effort share spent against rough outcome share gained, as observations rather than the principle's prediction. Skip any number you can't estimate honestly.
- **What's left**, grouped, separating minor from unaffordable. The second group is the user's next funding decision.
