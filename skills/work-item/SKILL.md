---
name: work-item
description: >
  Drafts well-formed work items with testable acceptance criteria, then creates them in whatever tracker is connected if the user explicitly asks for that. Also applies the same standard to tighten up an existing work item. TRIGGER when: the user invokes /work-item; OR asks to draft, write up, create, or fix up a ticket, issue, task, story, bug report, or sub-task — for Jira, GitHub, Azure DevOps, Linear, or any other tracker — even when they don't name a tracker or use the word "ticket" explicitly, e.g. "log a bug for...", "file an issue about...", "write up a task for...", "can you create a story for...", "this ticket has no acceptance criteria, can you add some". Do NOT use for general prose writing, PR descriptions, or commit messages — those follow different conventions.
argument-hint: "[one-line description of the work]"
---

# Work Item Skill

Draft a work item using the shape that already dominates well-formed real tickets: bold-text section headers (not markdown `##`), a framing section chosen by the ticket's nature, and acceptance criteria written as testable, observable outcomes rather than vague statements like "works correctly." The same standard applies whether you're drafting a new ticket from scratch or fixing up an existing one that's missing a piece (most often acceptance criteria) — treat both as the same content problem.

This skill defines content only — it has no opinion on which tracker or tool creates or updates the ticket. Tool selection (a Jira MCP tool, `gh issue create`, an Azure DevOps or Linear API, etc.) is a runtime decision made at the point of creation, based on whatever is connected in the current session.

If invoked via `/work-item`, treat `$ARGUMENTS` as a one-line description of the work; ask follow-up questions to fill any gaps. If triggered by conversation, use the context already established rather than re-asking for things already said.

## Execution steps

1. Determine the work's nature: is it reporting a defect (something broken) or describing new/changed work? This decides the framing section — see `assets/work-item-template.md`.
2. Determine whether it's a standalone item or a child of a larger parent item — see "Applies to" below for the test. This decides whether Acceptance criteria is mandatory.
3. Draft the content following `assets/work-item-template.md`. Read that file for the full template and worked examples before writing — don't rely on a remembered shape, since the exact section names and casing matter (e.g. "Acceptance criteria" is lowercase-c, bold, no colon). When fixing up an existing ticket, keep what's already there and only add or rewrite the pieces that are missing or vague.
4. If the user asked to draft or write up the ticket (not create or update it), present the drafted content for review and stop there.
5. If the user explicitly asked to create or update the ticket, proceed directly: pick whichever tool fits the destination tracker at that moment and apply the change. The request itself is the go-ahead — no extra confirmation gate is needed once content is drafted.

## Applies to

These two questions are about the work itself, not about matching a tracker's type field — a "task" in Jira, a plain issue in GitHub, and a "user story" in Azure DevOps are all standalone items by this test, and the same logic applies whatever the destination tracker calls its types.

A standalone item — the top-level thing being tracked — always gets the full treatment: a framing section and mandatory Acceptance criteria.

A child item — something broken out under a larger parent, whatever the tracker calls it (a Jira sub-task, a GitHub sub-issue, an Azure DevOps child work item, a Linear sub-issue) — is conditional. It needs its own framing and acceptance criteria only when independently verifiable: its own deploy, its own test, its own "done" state (e.g. one of several services being migrated off a queue, each cut over and verified separately). A child item that's just a granular checklist item under a parent whose acceptance criteria already covers it should stay minimal — don't manufacture an acceptance criteria section it doesn't need.

See `assets/work-item-template.md` for the full template, the exact content shape, and worked examples covering each variant.
