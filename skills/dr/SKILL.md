---
name: dr
description: >
  Record a Decision Record (DR) when a significant, costly-to-change decision is being made.
  TRIGGER when: the user invokes /dr; OR the conversation involves architectural trade-offs,
  significant technology choices (database, framework, API design, infrastructure, data model,
  integration patterns, build-vs-buy), decisions the user describes as "hard to reverse",
  "locked in", "a big commitment", or "can't easily change later", or when the user is
  weighing multiple options with clear long-term consequences. In those cases, proactively
  suggest recording a DR before the decision is finalised.
argument-hint: [title]
allowed-tools: [Read, Glob, Bash, Write, AskUserQuestion]
---

# Decision Record (DR) Skill

Help the user capture a Decision Record (DR) for a significant, costly-to-change decision using the project's DR template.

## When Invoked on Demand (`/dr`)

The user may optionally pass a title as `$ARGUMENTS`. If they do, use it; otherwise ask for one before proceeding.

## When Suggested Automatically

If you detect a high cost-of-change decision in conversation, say:

> "This looks like a decision that could be costly to change later. Would you like to capture a Decision Record for it?"

Wait for explicit confirmation before creating anything.

---

## Execution Steps

### 1. Gather Information

Use `AskUserQuestion` for each question — ask one topic area at a time. Do not present all fields at once. Start with the essentials; ask about optional fields only if the user is engaged in the detail.

**Round 1 — Essentials** (always required):

| Field | Guidance |
|---|---|
| **Title** | Short phrase representing the problem and solution, e.g., "Use PostgreSQL as primary datastore" |
| **Context and Problem Statement** | What situation led to this decision? What problem are you solving? |
| **Considered Options** | What alternatives were evaluated? Aim for at least two. For each: brief description, pros, and cons. Be objective — rejected options should be fairly represented. |
| **Decision** | Which option was chosen and why? Prefer the **Y-Statement format**: _"In the context of [situation], facing [concern], we decided [option], to achieve [quality], accepting [downside]."_ Free-form prose is also fine. |

**Round 2 — Optional depth** (ask only if not already covered in conversation):

| Field | Guidance |
|---|---|
| **Forces and Constraints** | What requirements, assumptions, forces, or constraints shaped the decision? |
| **Consequences** | What are the ramifications — both positive and negative? |
| **More Information** | Additional evidence, links, or related decisions to reference? |

**Round 3 — Metadata** (ask only if the user cares about provenance or governance):

| Field | Guidance |
|---|---|
| **Status** | Use `AskUserQuestion` with options: `draft`, `proposed`, `adopted`, `retired`, `superseded` (default to `proposed`) |
| **Date** | Date of the decision (default to today) |
| **Decision-makers** | Who was involved in making the decision? |
| **Consulted** | Who was consulted (two-way communication)? |
| **Informed** | Who is kept up-to-date (one-way communication)? |

Never assume an answer — if something is ambiguous and it affects the quality of the DR, ask.

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

### 4. Confirm Before Writing

Use `AskUserQuestion` to present a concise summary and confirm before creating the file. Include in the question body:

- **Title:** [title]
- **Decision:** [one sentence]
- **Key trade-off:** [what is being accepted/sacrificed]
- **File:** `[file path]`

Offer two options: `Yes, write the file` and `No, let me revise`. Do not write the file until the user selects the first option.

### 5. Write the DR File

Read the template from `${CLAUDE_SKILL_DIR}/assets/dr-template.md`. Fill every section with the gathered information. For any optional section with no content, remove both the `<!-- This is an optional element. Feel free to remove. -->` comment and the section itself. Do not leave placeholder text.

If the status is `superseded`, find the DR being superseded, add a "Superseded by [DR-NNNN](path)" note to its `## More Information` section (or append the section if absent), and reference that DR in the new file's `## More Information` section.

### 6. Confirm with the User

After writing the file, tell the user:
- The file path that was created
- A one-line summary of the decision captured

Do not offer to improve the DR unless the user asks.
