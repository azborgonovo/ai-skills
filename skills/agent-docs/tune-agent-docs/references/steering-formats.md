# Steering doc formats

How each recognized AI-steering format is structured, scoped, and sized, sourced from each vendor's own docs. Consult this before judging a doc's structural fit or frontmatter validity — don't recommend a scoping mechanism a format doesn't have, and don't grade one format's file against another format's size limit. Formats change; treat this file as a starting point to spot-check, not a permanent truth.

## General principles that hold across every format

Drawn mainly from [Anthropic's Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), which frames these as Skill guidance but states them at a level that applies to any markdown an agent reads as instruction:

- **Consistent terminology** — pick one term per concept and use it everywhere in the doc; mixing "API endpoint"/"URL"/"route" for the same thing costs the agent parsing effort for no benefit.
- **Concrete examples over abstract description** — an input/output pair or a code snippet conveys the intended style more reliably than a paragraph describing it.
- **Match degrees of freedom to fragility** — loose, high-freedom language for judgment calls; specific, low-freedom, exact-steps language for fragile or must-follow-in-order operations. Neither should be used for the other's job.
- **No time-sensitive conditionals** — "until the migration finishes, do X" or "before Q3, use the old endpoint" silently goes stale; fold superseded guidance into a clearly labeled old-patterns note instead of a live-sounding conditional.
- **Don't offer more options than the agent needs** — state the default and, only if it matters, the one alternative and when to reach for it; a wall of equally-weighted choices reads as indecision.
- **References stay one level deep** — link every supporting file directly from the entry-point doc; a reference that itself links to another reference risks a partial read.
- **A reference file past roughly 100 lines gets a table of contents** at the top, so a partial read still shows the full scope of what's available.
- **State the target behavior rather than the prohibition** — a "never do X" line puts X in the agent's context with nothing to replace it, so the ban competes with the behavior it just named. Reserve a prohibition for a guardrail that has no positive phrasing, and pair even that one with what to do instead. (This one comes from the skill-writing conventions this repo follows rather than from Anthropic's page above.)
- **Cut instructions the model already follows** — a line that changes no behavior against the plain model pays context for nothing. The test is whether an agent that never read the line would have acted differently.

## Claude Code — `CLAUDE.md`, `AGENTS.md`, `.claude/rules/`

- Claude Code reads `CLAUDE.md`, not `AGENTS.md`, directly. A repo that already maintains an `AGENTS.md` for other agents should have a `CLAUDE.md` that imports it with `@AGENTS.md` (or symlinks to it), optionally followed by Claude-specific additions below the import.
- `CLAUDE.md` files load hierarchically by directory: files above the working directory load in full at launch, root-to-leaf; nested subdirectory `CLAUDE.md` files load on demand once Claude reads a file in that subdirectory. A `CLAUDE.local.md` alongside either loads last at that level and should be gitignored.
- A file can `@path/to/file` import others, up to 4 hops deep; imported content still loads fully into context at launch, so importing organizes a doc without reducing its token cost.
- `.claude/rules/*.md` splits instructions by topic; add YAML frontmatter with a `paths` glob array to scope a rule to matching files only, so it loads on demand instead of every session.
- Target under 200 lines per `CLAUDE.md` — longer files consume more context and measurably reduce instruction adherence.
- Claude Code's own `/doctor` checkup (alias `/checkup`) applies this same review to a checked-in `CLAUDE.md`: it trims content the agent could derive from the codebase itself (directory layouts, dependency lists, architecture overviews), keeps what it can't derive (pitfalls, rationale, conventions that differ from tool defaults), migrates remaining always-loaded content into skills and on-demand nested files, and separately deduplicates a local `CLAUDE.local.md` against its checked-in counterpart. It reports findings and asks before changing anything — the same critique-first discipline this skill follows.
- Source: [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory), [code.claude.com/docs/en/commands](https://code.claude.com/docs/en/commands)

## Claude Skills — `SKILL.md`

- Frontmatter requires `name` (max 64 chars, lowercase letters/numbers/hyphens only, may not contain `anthropic`/`claude`) and `description` (max 1024 chars, non-empty, no XML tags).
- The `description` is the only content loaded for every skill at startup, so it must front-load specific trigger terms and state both what the skill does and when to use it, written in third person.
- Keep the `SKILL.md` body under 500 lines; push bulky or conditionally-needed material into sibling reference files linked one level deep from `SKILL.md` — a reference file costs no tokens until Claude actually reads it.
- Source: [platform.claude.com — Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

## Kiro — `.kiro/steering/*.md`

- Three default files: `product.md` (purpose, users, goals), `tech.md` (stack, tooling, constraints), `structure.md` (file layout, naming, import patterns) — plus any custom file added on top.
- Frontmatter's `inclusion` field controls when a file loads: `always` (every interaction — the default), `fileMatch` with a `fileMatchPattern` glob (only when a matching file is open), or `manual` (loaded on demand via `#steering-file-name` in chat, also surfaced as a slash command).
- Best-practice guidance: one domain per file, a clear descriptive filename, explain the *why* behind a standard rather than stating only the rule, and split a file rather than let it grow to cover several concerns.
- Source: [kiro.dev/docs/steering](https://kiro.dev/docs/steering/)

## Cursor — `.cursor/rules/*.mdc`, legacy `.cursorrules`

- Per-file `.mdc` rules under `.cursor/rules/` are the current format; each carries frontmatter with `description` (what Cursor's agent reads to judge relevance for "apply intelligently" activation), `globs` (auto-attaches the rule when a matching file is opened or edited), and `alwaysApply` (loads for every conversation regardless of context — meant to stay small, not a per-feature default).
- The legacy single `.cursorrules` file is silently ignored in Cursor's Agent mode, so a repo still relying on it for agentic workflows has a doc that looks live but isn't actually read.
- Source: [techsy.io — Cursor rules guide](https://techsy.io/en/blog/cursor-rules-guide)

## Windsurf / Devin Desktop — `.windsurfrules`, `.windsurf/rules/`, `.devin/rules/`

- Windsurf was rebranded to Devin Desktop; `.devin/rules/` is now the primary location, though `.windsurfrules` and `.windsurf/rules/*.md` are still read for compatibility.
- Two systems coexist: the legacy single `.windsurfrules` file, and the newer `.windsurf/rules/` directory of scoped markdown files.
- Hard size limits: a global rules file caps at roughly 6,000 characters, a single workspace rule file at roughly 12,000 characters. A file over the limit doesn't error — it silently gets truncated.
- Source: [thepromptshelf.dev — .windsurfrules guide](https://thepromptshelf.dev/blog/windsurfrules-complete-guide-2026/)

## Cline — `.clinerules`, `.clinerules/*.md`

- A single `.clinerules` file suits a small setup; larger projects split into a `.clinerules/` directory of topic files with conditional loading.
- No hard limit, but adherence degrades in practice beyond roughly 300 lines; keeping a rules file under about 150 lines is the recommended ceiling for reliable behavior.
- Source: [thepromptshelf.dev — Cline rules guide](https://thepromptshelf.dev/blog/cline-rules-complete-guide-2026/)

## GitHub Copilot — `.github/copilot-instructions.md`, `.github/instructions/*.instructions.md`

- `copilot-instructions.md` is a single repo-wide file with no inclusion-mode frontmatter — every instruction in it applies everywhere, all the time.
- `.github/instructions/*.instructions.md` files are separate documents with their own frontmatter, scoped to matching files. Review them as their own corpus members rather than folding them into the repo-wide file's findings — the repo-wide file and a scoped companion covering the same ground is a duplication site like any other pairing in this corpus.
