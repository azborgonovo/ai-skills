# Skill authoring guidelines

This repo holds Claude Code skills. SKILL.md files are read by Claude, not primarily by humans,
so formatting should earn its tokens by helping the model parse and weight instructions — not by
looking tidy. Apply these rules when creating a new skill or improving an existing one.

## Horizontal rules (`---`)

Don't use `---` as section separators between steps or sections. The `##`/`###` Markdown headers
already delimit sections, so the rules add tokens (and minor parse noise) with no benefit to
Claude.

The **only** `---` that belong in a SKILL.md are the two YAML frontmatter delimiters at the very
top (opening and closing the `name`/`description` block).

## Bold (`**...**`)

Bold is a signal, not decoration — and signal weakens when it's everywhere. Use it purposefully:

- **Keep it for labeled lead-ins** that act as inline sub-headers, e.g. `**Truncation check**:`,
  `**Why the script**:`. These help the model locate and weight a specific piece of guidance.
- **Keep it for directive anchors** on things that change behaviour, e.g. `**Never** approve`,
  `**Always** post through the script`, `**Critical**`.
- **Drop it when it's purely cosmetic** — bolding a phrase mid-sentence for emphasis it doesn't
  need just dilutes the bold that does matter.

When in doubt, ask: would the model behave differently if this weren't bold? If not, leave it
plain. Don't strip bold wholesale either — losing the useful lead-ins and directives costs more in
clarity than it saves in tokens.

## General principle

Prefer instructions that explain the *why* over rigid `MUST`/`NEVER` walls of formatting. Keep the
always-loaded SKILL.md body lean; push deterministic, repetitive mechanics into bundled
`scripts/` (loaded only when used) rather than inline code the model must re-emit each run.
