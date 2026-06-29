# Skill authoring guidelines

This repo holds Claude Code skills. SKILL.md files are read by Claude, not primarily by humans, so formatting should earn its tokens by helping the model parse and weight instructions — not by looking tidy. Apply these rules when creating a new skill or improving an existing one.

## Horizontal rules (`---`)

Don't use `---` as section separators between steps or sections. The `##`/`###` Markdown headers already delimit sections.

The **only** `---` that belong in a SKILL.md are the two YAML frontmatter delimiters at the very top (opening and closing the `name`/`description` block).

## Bold (`**...**`)

Bold is a signal, not decoration — and signal weakens when it's everywhere. Use it purposefully:

- **Keep it for labeled lead-ins** that act as inline sub-headers, e.g. `**Truncation check**:`, `**Why the script**:`. These help the model locate and weight a specific piece of guidance.
- **Keep it for directive anchors** on things that change behavior, e.g. `**Never** approve`, `**Always** post through the script`, `**Critical**`.
- **Drop it when it's purely cosmetic** — bolding a phrase mid-sentence for emphasis it doesn't need just dilutes the bold that does matter.

When in doubt, ask: would the model behave differently if this weren't bold? If not, leave it
plain. Don't strip bold wholesale either — losing the useful lead-ins and directives costs more in
clarity than it saves in tokens.

## Line wrapping

Don't hard-wrap prose in SKILL.md bodies. Write one line per paragraph (and one line per list item) and let the editor soft-wrap visually.

In the YAML frontmatter, a folded `description: >` block may still wrap across indented lines.

## Spelling

Use American English spelling (`behavior`, `normalize`, `canceled`) so terminology stays consistent across skills. The exception is text quoted verbatim from another source — an example string copied from a sibling skill, a real product's wording — where you keep the original rather than "correcting" the quote.

## General principle

Prefer instructions that explain the *why* over rigid `MUST`/`NEVER` walls of formatting, and keep the always-loaded SKILL.md body lean.

Reach for a bundled `scripts/` helper (loaded only when used) when a task is *genuinely deterministic and repeated every run*. Weigh it honestly rather than defaulting to it: much of a skill's value is the model's judgment, which a rigid script can't do and can actively mislead by anchoring the model to the wrong signal; An existing tool (`Grep`/ripgrep, `Glob`) often already covers the deterministic part with no code to maintain
When unsure, stay model-only and let evidence decide — if you watch runs independently re-derive the same helper, that's the cue to extract it into `scripts/`.
