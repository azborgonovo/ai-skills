# Writing a good codebase-investigation subagent prompt

The quality of Step 7's findings depends almost entirely on how well the delegating prompt briefs the agent — a vague prompt gets a vague, hedge-everything report. The agent has no memory of the issue or the conversation; treat it like briefing a colleague who's never seen the report.

## Structure that works

1. **State the user-visible symptom or the requested change in plain terms**, as if explaining the report itself — not the tracker's internal jargon or issue ID. The agent should understand *what a user experiences* (for a bug) or *what new/changed behavior is wanted* (for a change request) before it starts grepping.
2. **Name the repo(s) to search**, and any classes/patterns you already suspect are involved (e.g. from a related issue's service ownership, or a naming convention visible in a sibling feature). It's fine to be wrong here — a good agent will course-correct — but a starting guess focuses the first few searches.
3. **Enumerate exactly what you want back**: file paths, line numbers, actual code snippets (not paraphrases), config values, and — for a bug — an explicit stated hypothesis for why the current code produces the symptom, or — for a change request — a description of how the current code works and a candidate approach for the change. Ask for git history/blame on the relevant code if a recent change looks suspicious.
4. **Cap the scope** ("under 500 words plus code snippets", "focus on the request/response path, not the whole module") so the report comes back usable rather than a full repo tour.
5. If the feature spans multiple repos (e.g. a backend service and its frontend caller), it's usually better to run one agent per repo in parallel than one agent trying to cover both — each one gets a more focused brief and a tighter search space.

## Examples

### Bug investigation

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
   (commit messages referencing other issues, TODO comments, recently added filters/joins).

Report back: exact file paths and line numbers, the specific code/config responsible, and your best
hypothesis for why this reproduces the reported symptom. Keep it under 500 words plus snippets.
```

### Change-request investigation

```
I'm investigating a change request: [plain description of the desired new/changed behavior — what
should work differently and why, including any concrete constraints from the request, e.g. "add CSV
export alongside the existing PDF export" or "the nightly job should process incrementally instead
of re-fetching the full table"].

Investigate the following repo(s) for how this would be implemented:
1. `<path-to-backend-repo>` — [stack, e.g. ".NET backend service"]
2. `<path-to-frontend-repo>` — [stack, e.g. "Vue/TS frontend"]

Please find and report on:
1. How the current behavior/mechanism works today — trace the full call path (controller → service
   → data-access/query layer) for the feature this change extends or modifies.
2. What would need to change to support the new behavior — which layer(s), and any existing
   abstraction the change could reuse vs. one it would need to introduce.
3. Anything that complicates the change — data migration, backward compatibility, other callers of
   the code being modified.
4. Anything in git history/blame suggesting why the current implementation is shaped the way it is
   (a prior deliberate constraint reads differently than an oversight).

Report back: exact file paths and line numbers, the specific code responsible, and a candidate
approach with its tradeoffs. Keep it under 500 words plus snippets.
```

## Anti-patterns

- **"Investigate issue PROJ-123"** — the agent can't fetch the tracker; it has no idea what that
  means without you translating the symptom into plain language first.
- **"Find the bug" / "Find how we'd build this"** — no scope, no repo, no hypothesis or candidate
  approach. You'll get a generic tour of the codebase instead of a targeted answer.
- **Asking for a summary instead of evidence** — "explain how the export feature works" produces
  prose you then can't verify. Asking for file:line + snippets gives you something Step 9 can check.
- **Dispatching against a checkout you haven't confirmed is current** — do the freshness check from
  Step 5 (`git fetch` + compare to the remote default branch, pull or use a worktree as needed)
  *before* launching the agent, not after it reports back. An agent has no way to know its search
  space is missing recent commits, so it will report a plausible-sounding "no such code found"
  instead of an error — the cost of skipping this check lands entirely on you, later, when you trust
  a negative that was only true of a stale copy of the repo.
