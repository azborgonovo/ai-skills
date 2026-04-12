---
name: log-decision
description: >
  Draft a structured document (DR) capturing the reasoning for a significant decision. TRIGGER when:
  the user invokes /log-decision; OR the conversation involves a decision that has been reached about
  architectural trade-offs, technology choices, or anything the user describes as "hard to reverse",
  "locked in", or "a big commitment" — in those cases, proactively suggest logging a DR.
argument-hint: "[decision title]"
allowed-tools: [Read, Glob, Edit, Write, AskUserQuestion]
---

# Log Decision Skill

Help the user capture a Decision Record for a significant, costly-to-change decision.

If invoked via `/log-decision`, use `$ARGUMENTS` as the title if provided; otherwise ask for one.
If triggered by a conversation, say something like: _"This looks like a significant decision — would you draft a Decision Record (DR)?"_ Wait for confirmation before proceeding.

> **Not sure yet?** If the user is still exploring options or hasn't settled on a direction,
> suggest `/decide` instead — it's a thinking-partner skill for working through the problem
> before documenting it.

## Execution Steps

### 1. Gather Information

Use `AskUserQuestion` for each question — ask one topic area at a time. Do not present all fields
at once. Start with the essentials; ask about optional fields only if the user is engaged in the
detail.

**If the user has just come from a `/decide` session**, the Context and Problem Statement, Forces
and Constraints, and Considered Options will already be established in the conversation. Confirm
the key points rather than re-asking them, and move straight to the Decision field and any gaps.

**Essentials** (always required):

| Field | Guidance |
|---|---|
| **Title** | Short phrase representing the problem and solution, e.g., "Use PostgreSQL as primary datastore" |
| **Context and Problem Statement** | What situation led to this decision? What problem are you solving? If there are relevant code locations, issues, or tickets that provide context, note them. |
| **Considered Options** | What alternatives were evaluated? Aim for at least two. For each: brief description, pros, and cons. Be objective — rejected options should be fairly represented. |
| **Decision** | Which option was chosen and why? Prefer the **Y-Statement format**: _"In the context of [situation], facing [concern], we decided [option], to achieve [quality], accepting [downside]."_ Free-form prose is also fine. |

**Depth** (ask only if not already covered):

| Field | Guidance |
|---|---|
| **Forces and Constraints** | What requirements, assumptions, forces, or constraints shaped the decision? |
| **Consequences** | What are the ramifications — both positive and negative? |
| **More Information** | Additional evidence, links, or related decisions to reference? Include links to relevant code files, PRs, issues, or external resources (docs, RFCs, benchmarks) where applicable. |

**Metadata** (ask only if provenance or governance matters):

| Field | Guidance |
|---|---|
| **Status** | `draft`, `proposed`, `adopted`, `retired`, `superseded` (default to `proposed`) |
| **Date** | Date of the decision (default to today) |
| **Decision-makers** | Who was involved in making the decision? |
| **Consulted** | Who was consulted (two-way communication)? |
| **Informed** | Who is kept up-to-date (one-way communication)? |

Never assume; ask if something is ambiguous.

### 2. Determine the DR Directory and Next Number

1. Look for an existing DR directory in the project root using this priority order:
   - `docs/decisions/`
   - `adr/`
   - `.decisions/`
2. If none exists, use `docs/decisions/` and create it.
3. Scan existing files matching `DR-*.md` to find the highest sequence number, then use `N + 1`. Start at `0001` if none exist.
4. While scanning, note any DRs whose titles or content appear related to the current decision — surface these to the user so they can be referenced or superseded.

### 3. Derive the File Name

- Kebab-case the title, strip special characters, truncate to ~50 chars.
- Format: `DR-NNNN-kebab-title.md`
- Example: `DR-0003-use-postgresql-as-primary-datastore.md`

### 4. Write the DR File

Read the template from `${CLAUDE_SKILL_DIR}/assets/dr-template.md`. Fill every section with the
gathered information. For any optional section with no content, remove both the
`<!-- This is an optional element. Feel free to remove. -->` comment and the section itself.
Do not leave placeholder text.

When writing the DR, include markdown links wherever relevant: to code files or directories affected
by the decision, to PRs or issues that motivated it, to external docs (RFCs, benchmarks, vendor
pages), and to related DRs. Use relative paths for links
between DR files. Use full web URLs for any other links.

If the status is `superseded`, find the DR being superseded, add a "Superseded by [DR-NNNN](path)"
note to its `## More Information` section (or append the section if absent), and reference that DR
in the new file's `## More Information` section.

After writing, tell the user the file path and a one-line summary of the decision. Do not offer to
improve the DR unless asked.
