# Payments platform

## Skill authoring conventions

These conventions are settled. Apply them to every `SKILL.md` under `skills/`.

**Purpose block**: every body opens with a one-line `**Purpose:**` block that repeats what the skill does. A reader who opens the file part way through a task must not have to go back to the frontmatter.

**Numbered steps**: write the steps of a procedure as a numbered list. Do not use a bullet list for a procedure, because a reviewer here cites a step by its number in code review.

**No `argument-hint`**: frontmatter must not carry `argument-hint`. State the argument in the first line of the body instead, where the model reads it at the same time as the step that uses it.

## Database

Migrations live in `migrations/versions/`. The seed data lives in `seeds/`.
