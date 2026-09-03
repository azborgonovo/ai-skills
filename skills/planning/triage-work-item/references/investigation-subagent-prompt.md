# Writing a good codebase-investigation subagent prompt

The quality of the findings in Step 7 depends almost entirely on how well the delegating prompt briefs the agent. A vague prompt gets back a vague report that hedges everything. The agent has no memory of the issue and no memory of the conversation, so brief it like a colleague who never saw the report.

## Structure that works

1. **State the user-visible symptom, or the requested change, in plain terms**, as if you were explaining the report itself. Do not use the internal jargon of the tracker, and do not use the issue ID. For a bug, the agent must understand *what a user experiences*. For a change request, it must understand *what new or changed behavior someone wants*. It needs that before it starts to grep.
2. **Name the repos to search**, plus any class or pattern that you already suspect is involved. Hints come from the service ownership of a related issue, or from a naming convention visible in a sibling feature. A wrong guess here is fine, because a good agent course-corrects, and a starting guess focuses the first few searches.
3. **Enumerate exactly what you want back**: file paths, line numbers, actual code snippets rather than paraphrases, and configuration values. For a bug, also ask for an explicit stated hypothesis about why the current code produces the symptom. For a change request, ask instead for a description of how the current code works, plus a candidate approach for the change. Ask for git history and blame on the relevant code when a recent change looks suspicious.
4. **Cap the scope.** Give a limit such as "under 500 words plus code snippets", or "focus on the request and response path, not the whole module". A capped report comes back usable, instead of as a full tour of the repo.
5. When the feature spans several repos, such as a backend service and its frontend caller, run one agent per repo in parallel. That usually beats one agent trying to cover both, because each agent gets a more focused brief and a tighter search space.

## Examples

### Bug investigation

```
I am triaging a bug report: [plain description of the user-visible symptom: what they did, what they expected, and what happened instead, including any concrete input or value from the report, such as "filtering by date range from January 2025" or "company X with a large user base"].

Investigate the following repo(s) for the root cause:
1. `<path-to-backend-repo>` — [stack, e.g. ".NET backend service"]
2. `<path-to-frontend-repo>` — [stack, e.g. "Vue/TS frontend"]

Please find and report on:
1. The endpoint or handler that implements this behavior. Trace the full call path: controller, then service, then the data-access or query layer. If you are not sure which controller, search for [naming patterns/keywords from the feature area].
2. The actual query or logic that does the work. Is it paginated or bounded? Are there joins or loops that get expensive at scale? Is a timeout configured, such as a command timeout or an HTTP timeout, and what is its value?
3. The frontend code that calls this endpoint, and how it surfaces errors to the user.
4. Anything in git history or blame that suggests a known or recently introduced limitation: a commit message that references another issue, a TODO comment, or a recently added filter or join.

Report back: exact file paths and line numbers, the specific code or config responsible, and your best hypothesis for why this reproduces the reported symptom. Keep it under 500 words plus snippets.
```

### Change-request investigation

```
I am investigating a change request: [plain description of the desired new or changed behavior: what must work differently and why, including any concrete constraint from the request, such as "add CSV export alongside the existing PDF export" or "the nightly job must process incrementally instead of re-fetching the full table"].

Investigate the following repo(s) for how to implement this:
1. `<path-to-backend-repo>` — [stack, e.g. ".NET backend service"]
2. `<path-to-frontend-repo>` — [stack, e.g. "Vue/TS frontend"]

Please find and report on:
1. How the current behavior or mechanism works today. Trace the full call path, which is controller, then service, then the data-access or query layer, for the feature that this change extends or modifies.
2. What has to change to support the new behavior: which layers, plus any existing abstraction that the change can reuse, against one that it has to introduce.
3. Anything that complicates the change: a data migration, backward compatibility, or other callers of the code being modified.
4. Anything in git history or blame that suggests why the current implementation is shaped the way it is. A prior deliberate constraint reads differently than an oversight.

Report back: exact file paths and line numbers, the specific code responsible, and a candidate approach with its trade-offs. Keep it under 500 words plus snippets.
```

## Anti-patterns

- **"Investigate issue PROJ-123"**: the agent cannot fetch the tracker. The key means nothing to it until you translate the symptom into plain language.
- **"Find the bug", or "Find how we would build this"**: no scope, no repo, and no hypothesis or candidate approach. You get a generic tour of the codebase instead of a targeted answer.
- **Asking for a summary instead of evidence**: "explain how the export feature works" produces prose that you then cannot verify. Asking for `file:line` plus snippets gives you something that Step 9 can check.
- **Dispatching against a checkout that you have not confirmed is current**: run the freshness check from Step 5 *before* you launch the agent, and not after it reports back. An agent has no way to know that its search space is missing recent commits. So a stale checkout produces a plausible-sounding "no such code found", instead of an error.
