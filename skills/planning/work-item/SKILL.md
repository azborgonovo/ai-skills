---
name: work-item
description: >
  Drafts a well-formed work item with testable acceptance criteria, then creates it in whatever
  tracker is connected, when the user asks for that explicitly. Applies the same standard to tighten
  an existing work item. Use when the user invokes /work-item, or asks to draft, write up, create, or
  fix up a ticket, issue, task, story, bug report, or sub-task, for Jira, GitHub, Azure DevOps,
  Linear, or any other tracker. Use it even when the user names no tracker and never says "ticket",
  as in "log a bug for...", "file an issue about...", "write up a task for...", "can you create a
  story for...", and "this ticket has no acceptance criteria, can you add some". Do NOT use it for
  general prose writing, a PR description, or a commit message, because those follow different
  conventions.
argument-hint: "[one-line description of the work]"
---

# Work Item

Draft a new work item, or fix up an existing one, to one standard: bold-text section headers, a framing section chosen by the nature of the work, and testable acceptance criteria.

This skill defines content only. At the point of creation, use whatever tracker tool the session has connected, such as a Jira MCP tool, `gh issue create`, or an Azure DevOps or Linear API.

When the user invokes `/work-item`, treat `$ARGUMENTS` as a one-line description of the work, and ask follow-up questions to fill any gap. When the conversation triggered this skill instead, use the context that the conversation already established. Do not ask again for what the user already said.

## Execution steps

1. Decide whether the item reports a defect, which means that something is broken, or describes new or changed work. That answer chooses the framing section.
2. Decide whether the item is standalone or a child of a larger parent, with the test under "Applies to" below. That answer decides whether the acceptance criteria are mandatory.
3. Read `assets/work-item-template.md` and draft from its template and worked examples, not from memory, because the exact section names and casing matter. For example, **Acceptance criteria** is bold, has a lowercase c, and has no colon. Write in the plain English that "Writing style" below describes. When you fix up an existing work item, keep what is already there, and add or rewrite only the pieces that are missing or vague.
4. When the user asked only for a draft or a write-up, present the content for review and stop.
5. When the user asked explicitly to create or update the work item, apply the change with the tool that fits the destination tracker. The request is the go-ahead, so do not ask for confirmation once the content is drafted.

## Writing style

A triager next quarter, or a reader outside the team, must understand the work item on one read. Write short sentences in the active voice, define a term that such a reader can miss at its first use, and cut filler.

Keep every quoted error message, identifier, and value exactly as it is. When a plain-English writing skill such as `simple-english` is available, invoke it and apply its rules to the draft, before you present or create the item.

## Applies to

Classify an item by the work itself, and not by the type field of the tracker. A Jira "task", a plain GitHub issue, and an Azure DevOps "user story" are all standalone items by this test.

A standalone item is the top-level thing being tracked. It always gets the full treatment: a framing section, plus mandatory acceptance criteria.

A child item is broken out under a larger parent, such as a Jira sub-task, a GitHub or Linear sub-issue, or an Azure DevOps child work item. It needs its own framing and acceptance criteria only when someone can verify it independently, with its own deploy, its own test, and its own "done" state. A child item that is only a granular checklist entry, already covered by the acceptance criteria of its parent, stays minimal and gets no acceptance criteria section.
