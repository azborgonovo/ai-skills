# Writing a good codebase-investigation subagent prompt

The agent has no memory of the issue or the conversation, so brief it like a colleague who never saw the report. A vague prompt gets back a vague report.

## Structure that works

1. **State the user-visible symptom, or the requested change, in plain terms.** Leave out the issue ID and tracker jargon, because the agent cannot fetch the tracker. For a bug, the agent must understand *what a user experiences*. For a change request, it must understand *what new or changed behavior someone wants*.
2. **Name the repos to search**, plus any class or pattern that you already suspect, such as one from the service ownership of a related issue. A wrong guess is fine, because it still focuses the first searches.
3. **Enumerate exactly what you want back**, per the list in Step 7: file paths, line numbers, actual code snippets rather than paraphrases, and configuration values. A summary without `file:line` gives Step 9 nothing to check.
4. **Cap the scope.** Give a limit such as "under 500 words plus code snippets", or "focus on the request and response path, not the whole module".

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
