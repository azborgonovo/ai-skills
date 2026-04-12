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
allowed-tools: [Read, Glob, Bash, Write]
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

Collect the following through conversation (ask only for what is missing — do not interrogate if the user has already provided the information):

| Field | Question to ask |
|---|---|
| **Title** | Short phrase representing the problem and solution, e.g., "Use PostgreSQL as primary datastore" |
| **Status** | One of: draft, proposed, adopted, retired, superseded (default to `proposed`) |
| **Date** | Date of the decision (default to today) |
| **Decision-makers** _(optional)_ | Who was involved in making the decision? |
| **Consulted** _(optional)_ | Who was consulted (two-way communication)? |
| **Informed** _(optional)_ | Who is kept up-to-date (one-way communication)? |
| **Context and Problem Statement** | What situation led to this decision? What problem are you solving? |
| **Forces and Constraints** _(optional)_ | What requirements, assumptions, forces, or constraints shaped the decision? |
| **Considered Options** | What alternatives were evaluated? For each: brief description, pros, and cons. Include at least two options (one being the chosen option). |
| **Decision** | Which option was chosen and why? (Y-Statement or free format) |
| **Consequences** _(optional)_ | What are the ramifications — both positive and negative? |
| **More Information** _(optional)_ | Any additional evidence, links, or notes? |

You may ask all fields at once in a structured way, or gather them iteratively — adapt to the conversation flow.

### 2. Determine the DR Directory and Next Number

1. Look for an existing DR directory in the project root using this priority order:
   - `docs/decisions/`
   - `adr/`
   - `.decisions/`
2. If none exists, use `docs/decisions/` and create it.
3. Scan existing files matching `DR-*.md` to find the highest sequence number, then use `N + 1`. Start at `0001` if none exist.

### 3. Derive the File Name

- Kebab-case the title, strip special characters, truncate to ~50 chars.
- Format: `DR-NNNN-kebab-title.md`
- Example: `DR-0003-use-postgresql-as-primary-datastore.md`

### 4. Write the DR File

Read the template from `assets/dr-template.md`, located in the same directory as this skill file. Fill every section with the gathered information. For any optional section with no content, remove both the `<!-- This is an optional element. Feel free to remove. -->` comment and the section itself. Do not leave placeholder text.

### 5. Confirm with the User

After writing the file, tell the user:
- The file path that was created
- A one-line summary of the decision captured

Do not ask for further confirmation or offer to improve the DR unless the user asks.
