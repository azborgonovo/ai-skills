# Writing a good codebase-investigation subagent prompt

The quality of Step 6's findings depends almost entirely on how well the delegating prompt briefs
the agent — a vague prompt gets a vague, hedge-everything report. The agent has no memory of the
Jira ticket or the conversation; treat it like briefing a colleague who's never seen the ticket.

## Structure that works

1. **State the user-visible symptom in plain terms**, as if explaining the bug report itself — not
   the ticket's internal jargon or ID. The agent should understand *what a user experiences* before
   it starts grepping.
2. **Name the repo(s) to search**, and any classes/patterns you already suspect are involved (e.g.
   from a related ticket's service ownership, or a naming convention visible in a sibling feature).
   It's fine to be wrong here — a good agent will course-correct — but a starting guess focuses the
   first few searches.
3. **Enumerate exactly what you want back**: file paths, line numbers, actual code snippets (not
   paraphrases), config values, and an explicit stated hypothesis for why the current code produces
   the symptom. Ask for git history/blame on the relevant code if a recent change looks suspicious.
4. **Cap the scope** ("under 500 words plus code snippets", "focus on the request/response path, not
   the whole module") so the report comes back usable rather than a full repo tour.
5. If the feature spans multiple repos (e.g. a backend service and its frontend caller), it's
   usually better to run one agent per repo in parallel than one agent trying to cover both — each
   one gets a more focused brief and a tighter search space.

## Example

```
I'm triaging a bug report: [plain description of the user-visible symptom — what they did, what
they expected, what happened instead, including any concrete inputs/values from the report, e.g.
"filtering by date range from January 2025" or "company X with a large user base"].

Investigate the following repo(s) for the root cause:
1. `<path-to-backend-repo>` — [stack, e.g. ".NET backend service"]
2. `<path-to-frontend-repo>` — [stack, e.g. "Vue/TS frontend"]

Please find and report on:
1. The endpoint/handler that implements this behavior — trace the full call path (controller →
   service → data-access/query layer). If you're not sure which controller, search for [naming
   patterns/keywords from the feature area].
2. The actual query/logic doing the work — is it paginated or bounded? Any joins/loops that could be
   expensive at scale? Any timeout configured (command timeout, HTTP timeout), and what's its value?
3. The frontend code that calls this endpoint, and how it surfaces errors to the user.
4. Anything in git history/blame suggesting this is a known or recently-introduced limitation
   (commit messages referencing other tickets, TODO comments, recently added filters/joins).

Report back: exact file paths and line numbers, the specific code/config responsible, and your best
hypothesis for why this reproduces the reported symptom. Keep it under 500 words plus snippets.
```

## Anti-patterns

- **"Investigate ticket PROJ-123"** — the agent can't fetch Jira; it has no idea what that means
  without you translating the symptom into plain language first.
- **"Find the bug"** — no scope, no repo, no hypothesis. You'll get a generic tour of the codebase
  instead of a targeted answer.
- **Asking for a summary instead of evidence** — "explain how the export feature works" produces
  prose you then can't verify. Asking for file:line + snippets gives you something Step 8 can check.
