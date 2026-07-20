---
name: usage-report
description: >
  Report measured token consumption from the usage-budget collector — what sessions, projects, and individual turns actually cost, and whether that cost is predictable from the prompt. Use when the user asks where their tokens went, which work is expensive, or whether a prompt's cost can be estimated up front.
---

## What this reports

The `usage-budget` plugin's `Stop` hook records every turn's measured token cost into `~/.claude/usage-budget/sessions/`. This skill reads that data.

It reports **consumption**, never remaining quota. Claude Code exposes no quota figure to hooks or skills, so any statement about how much budget is left would be fabricated — direct the user to `/usage` for real limits and keep this skill's claims to what was actually spent.

Costs are reported in *weighted tokens*: output, fresh input, and cache-creation tokens at full weight, cache reads at a tenth, since cache reads are billed far cheaper. It approximates relative spend and is not a currency figure. Say "weighted tokens" rather than implying dollars.

## Reporting spend

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/report_usage.py"
```

Totals by project, plus the most expensive individual turns. Useful for "where did my tokens go" and for spotting a single runaway turn.

## Testing whether cost is predictable

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/report_usage.py" --predictive
```

Use this when the user wants cost *estimated ahead of time* — a warning before an expensive prompt, or an estimate learned from similar past prompts.

That idea is unproven, and this mode is how it gets tested rather than assumed. Turn cost is heavily confounded by position in the session: a turn at depth 40 re-reads far more accumulated context than the same request at depth 2, so a table keyed on prompt intent would largely be recording turn depth wearing an intent label. The report splits cost by depth band so the two can be told apart.

Read the result honestly:

- **Spread stays wide within each depth band** — what was asked explains little once position is controlled for. Report that prompt-based estimation has no signal to stand on here, rather than building it anyway with a caveat attached.
- **Spread narrows sharply within bands** — there is real signal, and an estimator conditioned on both intent and depth is worth trying.

With fewer than ~30 scored turns, the honest answer is that there isn't enough data yet. Say so plainly instead of reading a trend into noise.

## Reporting a reference class

When enough data exists and the user asks what some kind of work typically costs, give the **range and median** from comparable past turns, not a single number: "past turns like this ran 40k–300k weighted, median 90k." A point estimate implies a precision this data does not have, and the distribution is heavy-tailed enough that a mean is misleading.

Never gate work on such a number. Without a known quota there is nothing to gate against, and an estimate presented as a limit invites the user to abandon work that would have been fine.
