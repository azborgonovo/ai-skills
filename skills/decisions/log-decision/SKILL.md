---
name: log-decision
description: >
  Drafts a structured document, called a DR, that captures the reasoning behind a significant
  decision. Use when the user invokes /log-decision. Use it also when the conversation reaches a
  decision about architectural trade-offs or technology choices, or reaches anything the user calls
  "hard to reverse", "locked in", or "a big commitment". In those cases, suggest a DR without waiting
  to be asked.
argument-hint: "[decision title]"
allowed-tools: [Read, Glob, Edit, Write, AskUserQuestion]
---

# Log Decision

Capture a Decision Record (DR) for a significant decision that is costly to change.

When the user invokes `/log-decision` with an argument, use `$ARGUMENTS` as the title. With no argument, ask for a title. When the conversation triggered this skill instead, say something like: _"This looks like a significant decision. Would you like me to draft a Decision Record (DR)?"_ Wait for confirmation before you proceed.

If the user has not yet settled on a direction, suggest `/decide` instead.

## Execution steps

### 1. Gather information

Use `AskUserQuestion` for each question, one topic area at a time. Start with the essentials. Never assume: ask whenever something is ambiguous.

Confirm what the conversation already holds instead of asking again. After a `/decide` session, that is the Context and Problem Statement, the Forces and Constraints, and the Considered Options. Then ask for the Decision and for any gap.

**Essentials**, which are always required:

| Field | Guidance |
|---|---|
| **Title** | A short phrase that names the problem and the solution, such as "Use PostgreSQL as primary datastore" |
| **Context and Problem Statement** | The situation that led to the decision, the problem it solves, and any relevant code location or work item |
| **Considered Options** | At least two alternatives, each with a brief description, pros, and cons. Represent a rejected option fairly. |
| **Decision** | The chosen option and why. Prefer the **Y-Statement format**: _"In the context of [situation], facing [concern], we decided [option], to achieve [quality], accepting [downside]."_ Free-form prose also works. |

**Depth**, which you ask about only when the conversation has not covered it: **Forces and Constraints**, **Consequences**, and **More Information**.

**Metadata**, which you ask about only when provenance or governance matters:

| Field | Guidance |
|---|---|
| **Status** | `draft` (not ready for review), `proposed` (the default, open for review), `rejected` (reviewed, not adopted), `adopted` (in effect), `retired` (no longer active, no replacement), or `superseded` (replaced by a newer decision) |
| **Date** | The date of the decision, with today as the default |
| **Decision-makers**, **Consulted**, **Informed** | Who took part, who gave input in two-way communication, and who is kept up to date in one-way communication |

### 2. Find the DR directory, the number, and the file name

1. Look for an existing DR directory in the project root, in this priority order: `docs/decisions/`, then `adr/`, then `.decisions/`. When none exists, create `docs/decisions/`.
2. Find the highest sequence number among the files that match `DR-*.md`, and use `N + 1`. Start at `0001` when no file exists.
3. While you scan, note any DR whose title or content looks related to the current decision. Report those to the user, so they can reference or supersede them.
4. Name the file `DR-NNNN-kebab-title.md`. Kebab-case the title, strip the special characters, and truncate it to roughly 50 characters. For example: `DR-0003-use-postgresql-as-primary-datastore.md`.

### 3. Write the DR file

Fill the template at `${CLAUDE_SKILL_DIR}/assets/dr-template.md`. Remove each optional section that has no content, together with its `<!-- This is an optional element. Feel free to remove. -->` comment. Leave no placeholder text.

Link the PRs or issues that motivated the decision, external docs such as RFCs and benchmarks, and related DRs. Use a relative path between DR files and a full web URL for every other link.

If this DR supersedes an earlier one, add a "Superseded by [DR-NNNN](path)" note to the `## More Information` section of the earlier DR, and append that section when it is absent. Then reference the earlier DR in the `## More Information` section of the new file.

A reader opens the DR months later without this conversation. Write short sentences in the active voice, define a term that such a reader can miss at its first use, and cut filler. Keep every link and quoted value exactly as it is. When a plain-English writing skill such as `simple-english` is available, invoke it and apply its rules to the draft before you write the file.

After you write the file, tell the user the file path and a one-line summary of the decision. Do not offer to improve the DR unless the user asks.
