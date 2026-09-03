# Steering doc formats

How each recognized AI-steering format is structured, scoped, and sized, taken from the documentation of each vendor. Read this before you judge the structural fit or the frontmatter validity of a doc. Never recommend a scoping mechanism that a format does not have, and never grade the file of one format against the size limit of another. Formats change, so treat this file as a starting point for a spot-check, not as permanent truth.

## General principles that hold across every format

These come mainly from [Anthropic's Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). That page frames them as Skill guidance, but it states them at a level that applies to any markdown an agent reads as instruction. The four below are the ones that the checks in `SKILL.md` do not already carry, so apply them alongside those checks.

- **Concrete examples over abstract description**: an input and output pair, or a code snippet, carries the intended style more reliably than a paragraph that describes it.
- **Offer no more options than the agent needs**: state the default. Add the one alternative, and when to reach for it, only when the choice matters. A wall of options with equal weight reads as indecision.
- **Keep references one level deep**: link every supporting file directly from the entry-point doc. A reference that links to another reference risks a partial read.
- **Give a reference file over roughly 100 lines a table of contents** at the top. A partial read then still shows the full scope of what the file holds.

## Claude Code: `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`

- Claude Code reads `CLAUDE.md` directly. It does not read `AGENTS.md` directly. A repo that maintains an `AGENTS.md` for other agents needs a `CLAUDE.md` that imports it with `@AGENTS.md`, or that symlinks to it. Claude-specific additions can follow below the import.
- `CLAUDE.md` files load by directory hierarchy. Files above the working directory load in full at launch, from root to leaf. A nested subdirectory `CLAUDE.md` loads on demand, once Claude reads a file in that subdirectory. A `CLAUDE.local.md` next to either file loads last at that level, and it belongs in `.gitignore`.
- A file can import others with `@path/to/file`, up to 4 hops deep. Imported content still loads in full into the context at launch, so an import organizes a doc without cutting its token cost.
- `.claude/rules/*.md` splits instructions by topic. Add YAML frontmatter with a `paths` glob array to scope a rule to matching files, so the rule loads on demand instead of every session.
- Target under 200 lines per `CLAUDE.md`. A longer file consumes more context and measurably reduces instruction adherence.
- The `/doctor` checkup of Claude Code, with the alias `/checkup`, applies this same review to a checked-in `CLAUDE.md`. It trims content the agent can derive from the codebase itself, such as directory layouts, dependency lists, and architecture overviews. It keeps what the agent cannot derive, such as pitfalls, rationale, and conventions that differ from tool defaults. It moves the remaining always-loaded content into skills and on-demand nested files. It also deduplicates a local `CLAUDE.local.md` against its checked-in counterpart. It reports findings and asks before it changes anything, which is the critique-first discipline that this skill follows.
- Source: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory), [code.claude.com/docs/en/commands](https://code.claude.com/docs/en/commands)

## Claude Skills: `SKILL.md`

- The frontmatter requires `name` and `description`. The `name` holds at most 64 characters, uses lowercase letters, numbers, and hyphens only, and cannot contain `anthropic` or `claude`. The `description` holds at most 1024 characters, cannot be empty, and cannot contain XML tags.
- The `description` is the only content that loads for every skill at startup. It must front-load specific trigger terms, and it must state both what the skill does and when to use it, in the third person.
- Keep the `SKILL.md` body under 500 lines. Move bulky or conditionally-needed material into sibling reference files, linked one level deep from `SKILL.md`. A reference file costs no tokens until Claude reads it.
- Source: [platform.claude.com, Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

## Kiro: `.kiro/steering/*.md`

- Kiro has three default files, plus any custom file added on top. `product.md` holds purpose, users, and goals. `tech.md` holds the stack, the tooling, and the constraints. `structure.md` holds the file layout, the naming, and the import patterns.
- The `inclusion` field in the frontmatter controls when a file loads. The value `always` loads it for every interaction, and it is the default. The value `fileMatch`, with a `fileMatchPattern` glob, loads it only when a matching file is open. The value `manual` loads it on demand through `#steering-file-name` in the chat, which also appears as a slash command.
- Kiro recommends one domain per file and a clear descriptive filename. It recommends that a file explains the *why* behind a standard, not only the rule. It recommends that a file gets split rather than grown to cover several concerns.
- Source: [kiro.dev/docs/steering](https://kiro.dev/docs/steering/)

## Cursor: `.cursor/rules/*.mdc`, legacy `.cursorrules`

- Per-file `.mdc` rules under `.cursor/rules/` are the current format. Each rule carries frontmatter with three fields. `description` is what the agent of Cursor reads to judge relevance for "apply intelligently" activation. `globs` auto-attaches the rule when a matching file is opened or edited. `alwaysApply` loads the rule for every conversation, whatever the context, and it is meant to stay small rather than serve as a per-feature default.
- Cursor ignores the legacy single `.cursorrules` file in Agent mode, and it reports nothing. A repo that still relies on that file for agentic workflows has a doc that looks live and is never read.
- Source: [techsy.io, Cursor rules guide](https://techsy.io/en/blog/cursor-rules-guide)

## Windsurf and Devin Desktop: `.windsurfrules`, `.windsurf/rules/`, `.devin/rules/`

- Windsurf was rebranded to Devin Desktop. `.devin/rules/` is now the primary location. `.windsurfrules` and `.windsurf/rules/*.md` are still read for compatibility.
- Two systems coexist: the legacy single `.windsurfrules` file, and the newer `.windsurf/rules/` directory of scoped markdown files.
- The size limits are hard. A global rules file caps at roughly 6,000 characters. A single workspace rule file caps at roughly 12,000 characters. A file over the limit does not raise an error. It is truncated in silence.
- Source: [thepromptshelf.dev, .windsurfrules guide](https://thepromptshelf.dev/blog/windsurfrules-complete-guide-2026/)

## Cline: `.clinerules`, `.clinerules/*.md`

- A single `.clinerules` file fits a small setup. A larger project splits into a `.clinerules/` directory of topic files with conditional loading.
- Cline sets no hard limit, but adherence degrades in practice beyond roughly 300 lines. The recommended ceiling for reliable behavior is about 150 lines.
- Source: [thepromptshelf.dev, Cline rules guide](https://thepromptshelf.dev/blog/cline-rules-complete-guide-2026/)

## GitHub Copilot: `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`

- `copilot-instructions.md` is a single repo-wide file with no inclusion-mode frontmatter. Every instruction in it applies everywhere, all the time.
- `.github/instructions/*.instructions.md` files are separate documents with their own frontmatter, scoped to matching files. Review them as their own corpus members. Do not fold them into the findings of the repo-wide file. The repo-wide file and a scoped companion that covers the same ground form a duplication site, like any other pair in this corpus.
