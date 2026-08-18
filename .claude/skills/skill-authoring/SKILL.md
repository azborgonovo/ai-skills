---
name: skill-authoring
description: Conventions for writing or editing a SKILL.md in this repo — horizontal rules, bold usage, line wrapping, spelling, negative instructions, referencing other skills, when to reach for a scripts/ helper, and the bundled `check_skills.py` validator to run before committing. Use whenever creating a new skill or improving an existing one in this repository.
---

This repo holds Claude Code skills. SKILL.md files are read by Claude, not primarily by humans, so formatting should earn its tokens by helping the model parse and weight instructions — not by looking tidy. Apply these rules when creating a new skill or improving an existing one.

### Horizontal rules (`---`)

Don't use `---` as section separators between steps or sections. The `##`/`###` Markdown headers already delimit sections.

The **only** `---` that belong in a SKILL.md are the two YAML frontmatter delimiters at the very top (opening and closing the `name`/`description` block).

### Bold (`**...**`)

Bold is a signal, not decoration — and signal weakens when it's everywhere. Use it purposefully:

- **Keep it for labeled lead-ins** that act as inline sub-headers, e.g. `**Truncation check**:`, `**Why the script**:`. These help the model locate and weight a specific piece of guidance.
- **Keep it for directive anchors** on things that change behavior, e.g. `**Never** approve`, `**Always** post through the script`, `**Critical**`.
- **Drop it when it's purely cosmetic** — bolding a phrase mid-sentence for emphasis it doesn't need just dilutes the bold that does matter.

When in doubt, ask: would the model behave differently if this weren't bold? If not, leave it plain. Don't strip bold wholesale either — losing the useful lead-ins and directives costs more in clarity than it saves in tokens.

### Line wrapping

Don't hard-wrap prose in SKILL.md bodies. Write one line per paragraph (and one line per list item) and let the editor soft-wrap visually.

In the YAML frontmatter, a folded `description: >` block may still wrap across indented lines.

### Spelling

Use American English spelling (`behavior`, `normalize`, `canceled`) so terminology stays consistent across skills. The exception is text quoted verbatim from another source — an example string copied from a sibling skill, a real product's wording — where you keep the original rather than "correcting" the quote.

### Referencing other skills

Reference a sibling skill by name when it lives in the same plugin. Everything under `skills/<plugin>/` installs as one unit, so that pointer always resolves for an installed user — naming the sibling and handing off to it is cheaper and clearer than restating what it already covers.

Keep a skill in a *different* plugin out of the instructions. Plugins install independently, so the skill you point at may not be there, and the reader is left with a step it cannot take. Where one would genuinely help, phrase it as an optional accelerator and keep the fallback local: say what to do when it is absent, and define any vocabulary the guidance needs here rather than importing it from a plugin that may never be installed.

The `description` field is bound by the same rule, and not only where it states a boundary. Naming another plugin's skill anywhere in a description — as a hand-off, as a scope boundary, or inside a trigger phrase — ties this skill's retrieval text to something that may not be installed. State a boundary as what this skill does not do, and write a trigger from what the user would say about their own situation rather than the tool they happened to use to get there.

### Counter-examples and negative instructions

Prefer stating what to do over what to avoid. A bare "don't do X" leaves X sitting in context with no positive target to replace it. A clear positive rule with its reasoning is usually enough on its own.

### Discard a skill that shows no measured lift

A skill earns its place only when its gains outweigh its cost. If an eval against the plain model shows no pass-rate gain while the skill adds token or latency cost, discard it — don't ship it or keep it "just in case."

**Precedent — `consistency-first`**: a drafted skill for keeping generated code aligned with a codebase's existing patterns and vocabulary. Across four eval iterations — easy and hard fixtures, on Opus and Haiku, plus a drift scenario built as its best case — it produced essentially the same code as the plain model while spending ~10% more tokens, because current models already match neighboring code, read steering docs and ADRs unprompted, and re-anchor after local drift on their own. It was discarded on that evidence.

### Environment-specific values

Don't hardcode a value that varies across machines or users — a filesystem path, a clone-root convention, a tool version, a default port — just because it matches your own setup. It reads as generic but only ever runs correctly on a machine shaped like yours; everyone else gets a silent wrong answer or a confusing failure with no clue why.

Prefer discovering the value instead: search a short list of plausible candidates, or derive it from something already known (a repo's remote URL, a config file already on disk). When discovery comes up empty, ask the user directly rather than guessing further — a question is cheap; a wrong guess that "worked when I tested it" is not.

**Precedent — clone-root assumption**: a host-adapter skill for locating a repo's local clone assumed every user clones repos under `~/projects/<org>/<repo>`, because that happened to be true for the machine it was written on. The assumption was copied verbatim into a second skill while generalizing it for a different code host, without being questioned either time — and it failed on the very repo it was written in, which lives under `~/Code/<org>/<repo>` instead. The fix: probe a handful of common roots, then fall back to matching by remote URL, then ask, rather than asserting one absolute path.

### Check the mechanical rules before committing

Several rules here are settled by a machine rather than a reading: the `description` cap, the `name` charset, the two-`---` rule, body length, one line per paragraph. Those drift silently — three descriptions in this repo sat over the 1024-character cap until a full review pass found them. Run the bundled validator over any `SKILL.md` you touched, before the commit that lands it:

```
python .claude/skills/skill-authoring/scripts/check_skills.py
```

With no arguments it checks `skills/` and `.claude/skills/`; pass a path — a tree or a single `SKILL.md` — to check a skill you are authoring in another repo. It exits non-zero on any failure and names the file and the rule.

It is advisory: it reports rather than gates, and a clean run says only that the mechanical rules hold. Everything it stays silent about is still yours to judge — no-ops, duplication, whether the description reads as third person, whether a British spelling is a quote it should keep.

### General principle

Prefer instructions that explain the *why* over rigid `MUST`/`NEVER` walls of formatting, and keep the always-loaded SKILL.md body lean.

Reach for a bundled `scripts/` helper (loaded only when used) when a task is *genuinely deterministic and repeated every run*. Weigh it honestly rather than defaulting to it: much of a skill's value is the model's judgment, which a rigid script can't do and can actively mislead by anchoring the model to the wrong signal, and an existing tool (`Grep`/ripgrep, `Glob`) often already covers the deterministic part with no code to maintain.

When unsure, stay model-only and let evidence decide — if you watch runs independently re-derive the same helper, that's the cue to extract it into `scripts/`.
