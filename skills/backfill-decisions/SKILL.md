---
name: backfill-decisions
description: >
  Mine a repository's git history for architecturally significant decisions made in the past and
  retroactively write Decision Records for them, following the log-decision conventions. TRIGGER when:
  the user invokes /backfill-decisions; OR the user wants to document historical or undocumented
  decisions, reconstruct ADRs/DRs from git history, generate ADRs for a legacy or existing codebase,
  document the architecture history, or says things like "we never wrote down why we chose X",
  "why did we choose X?", "backfill our decision log", or "this repo has no ADRs". Do NOT use for a
  decision being made right now — that is /log-decision.
argument-hint: "[time range, path, or topic — e.g. 2023..2024, src/api, \"database\"]"
allowed-tools: [Bash(git:*), Read, Glob, Grep, Write, Edit, AskUserQuestion]
---

# Backfill Decisions Skill

Reconstruct Decision Records (DRs) for significant past decisions by mining git history. This
skill produces *retroactive* DRs — the decision has already been made and adopted; the goal is to
capture the evidence and reasoning that history reveals, honestly marked as a reconstruction.

> **Making a decision now?** Use `/log-decision` to record it while the reasoning is fresh, or
> `/decide` if you're still exploring options. This skill is only for decisions already buried in
> the repository's past.

## Execution Steps

### Phase 0 — Preconditions and Scope

1. Run `git rev-parse --is-inside-work-tree`. If not inside a repository, stop and tell the user.
2. Run `git rev-parse --is-shallow-repository`. If `true`, warn the user that the clone is shallow —
   the history is truncated and mining it would silently miss most decisions — and suggest
   `git fetch --unshallow` before continuing.
3. Gauge the repo: `git rev-list --count HEAD` for commit count, and
   `git log --reverse --date=short --pretty='%ad' | head -1` for the first commit date.
4. Parse `$ARGUMENTS` if provided — any combination of:
   - a **date range** like `2023..2024` → translate to `--since`/`--until` on every `git log`
   - a **path** like `src/api` → append `-- <path>` to every `git log`
   - a **topic keyword** like `"database"` → add it to the grep patterns in Phase 2
5. If more than ~1,500 commits are in scope and no range was given, use `AskUserQuestion`: scan
   the whole history **era-by-era** (one calendar year per era, oldest first — mine and triage
   each era before moving to the next), or let the user pick a narrower range.

### Phase 1 — Inventory Existing DRs (the dedup gate)

1. Locate the DR directory using the same priority order as log-decision: `docs/decisions/`,
   `adr/`, `.decisions/`. Also Glob more broadly for reading (`**/adr/*.md`, `**/decisions/*.md`,
   MADR-style `NNNN-*.md`) since the target repo may use a different convention — but **write**
   new DRs only to the priority-ordered directory (create `docs/decisions/` if none exists).
2. Read the title and opening paragraph of every existing DR. Build a list of covered topics and
   record the highest `DR-NNNN` sequence number.
3. Any mined candidate that matches a covered topic is excluded from triage and reported as
   *"already recorded in DR-NNNN"* instead.

### Phase 2 — Mine Signals

A candidate decision is **architecturally significant** when it hits at least one of:

| Signal class | What counts |
|---|---|
| Technology adoption/replacement | New or removed framework, database, message broker, language, or major library in a dependency manifest |
| Infrastructure & delivery | Dockerfile/compose/k8s/Terraform/Bicep/CI workflow introduced, replaced, or removed |
| Structural reshaping | Top-level directories added or deleted, subsystem extracted/merged/renamed, monorepo restructure |
| Cross-cutting pattern change | Auth mechanism, persistence pattern, API style (REST→gRPC/GraphQL), eventing, caching |
| Costly major upgrades | Version jumps that forced widespread code changes (.NET 6→8, Python 2→3, class components→hooks) |

**Counter-signals — ignore:** routine dependency bumps, formatting/lint commits, bug fixes,
features added within existing patterns, lockfile-only changes.

Run these sweeps (per era when working era-by-era; all read-only):

1. **Keyword sweep of commit subjects:**
   ```
   git log --date=short --pretty='%h|%ad|%an|%s' -i -E --grep='migrat|replac|adopt|switch(ed|ing)? to|introduc|rewrit|deprecat|drop (support|the)|remove (support|the)|upgrade to|consolidat|split out|extract'
   ```
2. **Merge/PR titles** (PR titles often state the decision verbatim):
   ```
   git log --merges --date=short --pretty='%h|%ad|%an|%s'
   ```
3. **Manifest archaeology.** Glob the repo root for manifests that exist (`package.json`,
   `*.csproj`/`Directory.Packages.props`, `go.mod`, `pyproject.toml`/`requirements.txt`,
   `pom.xml`/`build.gradle*`, `Gemfile`, `Cargo.toml`). Per manifest:
   `git log --follow --date=short --pretty='%h|%ad|%s' -- <manifest>`, then
   `git show <hash> -- <manifest>` only for hits that look like adds or removals of top-level
   dependencies — not version bumps.
4. **Infra file births and deaths:**
   ```
   git log --diff-filter=AD --date=short --pretty='%h|%ad|%s' --name-status -- 'Dockerfile*' 'docker-compose*' '*.tf' '*.bicep' '.github/workflows' '.gitlab-ci.yml' 'azure-pipelines*'
   ```
5. **Structural snapshots.** Compare top-level trees at boundary revisions with
   `git ls-tree --name-only <rev>`. When working era-by-era, the boundaries are the era edges;
   in a single-pass scan, sample one revision per year via
   `git rev-list -1 --before=<YYYY-12-31> HEAD` (or just compare the root commit against `HEAD`
   for young repos). A directory appearing or disappearing between boundaries is a structural
   signal — locate the originating commits with `git log --diff-filter=A --oneline -- <dir>`.
6. **Big-bang commits:** `git log --date=short --pretty='%h|%ad|%s' --shortstat` and flag commits
   touching more than ~100 files.

### Phase 3 — Cluster into Candidate Decisions

- Group hits that share a theme (same dependency, subsystem, or directory) **and** a time window —
  commits within a few weeks of each other usually belong to one decision; a migration spans many
  commits.
- Per candidate, assemble an evidence card:
  - inferred title in log-decision's imperative style, e.g. *"Adopt MediatR for in-process messaging"*
  - date range of the cluster
  - 2–5 representative commit hashes (first, last, most descriptive)
  - authors of the cluster's commits: `git shortlog -sn <first>~1..<last> -- <path>` (fall back to
    `git shortlog -sn <last>` if `<first>` is the root commit — plain `<first>..<last>` would
    exclude the first commit, often the most important one)
  - a one-line evidence summary
  - confidence: high / medium / low

  Example evidence card:

  > **Adopt SQS for asynchronous messaging** — 2023-03-02..2023-04-11 · commits `a1b2c3d`,
  > `e4f5a6b`, `c7d8e9f` · authors: J. Doe, M. Silva · evidence: `aws-sdk-sqs` added to
  > package.json, `rabbitmq` removed three weeks later, CI gained an SQS integration test job ·
  > confidence: **high**
- **Reversal detection:** if the same subject was adopted and later removed or replaced (e.g. a
  dependency added in 2022, deleted in 2024), pair them as **two linked candidates**: the original
  (will become `superseded by DR-NNNN`, or `retired` if nothing replaced it) and the reversal
  (`adopted`, referencing the first). Present them as a linked pair in triage.

### Phase 4 — Triage with the User

1. Print a numbered markdown table in chat:
   `# | Proposed DR title | Date | Evidence | Confidence | Note` — notes include
   *"already recorded in DR-NNNN"* exclusions and *"pair: reverses #3"* links. Example row:

   | # | Proposed DR title | Date | Evidence | Confidence | Note |
   |---|---|---|---|---|---|
   | 4 | Adopt SQS for asynchronous messaging | 2023-03 | aws-sdk-sqs added, rabbitmq removed, CI job added | high | pair: reverses #3 |
2. Then `AskUserQuestion` (one question): **write all high-confidence** / **let me select** /
   **rescan with a different scope**. If "let me select", follow up with `multiSelect: true`
   questions batched four candidates at a time.
3. The user may rename, merge, or split candidates in free text before writing.
4. **Never write a DR for an unconfirmed candidate.** Cap at ~10 DRs per run — continue
   era-by-era in follow-up runs if more remain.

### Phase 5 — Write DRs via the log-decision Workflow

For each confirmed candidate, proceed directly into the log-decision skill's writing steps
(directory, numbering, filename, template) — do not re-ask the user for information already
established by the mining. Apply these retroactive adaptations:

- **Template:** read `${CLAUDE_SKILL_DIR}/../log-decision/assets/dr-template.md`. If that path
  does not resolve, try `$HOME/.claude/skills/log-decision/assets/dr-template.md` (use the
  expanded absolute path — `~` is not expanded by file tools). If neither exists, stop and tell
  the user the log-decision skill is required.
- **File naming:** if the target directory already has an established naming convention (e.g.
  MADR-style `0007-use-postgres.md` without a `DR-` prefix), match that pattern and continue its
  numbering — forking the scheme would split the log in two. Use the log-decision default
  (`DR-NNNN-kebab-title.md`) only when the directory is new or has no consistent pattern.
- **Status:** default `adopted`. Reversal pairs: the original gets `superseded by DR-NNNN`
  (or `retired` if nothing replaced it) and both files cross-link each other in
  `## More Information` — both are new, so write the links directly rather than editing later.
- **Date:** the commit date of the decision (first commit of the cluster, or the merge date) —
  **not today**.
- **Decision-makers:** the cluster's commit authors. Omit `consulted` and `informed` — they are
  unknowable from history.
- **Considered Options:** always include the chosen option, with pros and cons observable from the
  evidence. If history reveals a rejected alternative (the thing that was removed or replaced),
  include it too. Otherwise keep only the chosen option and add the note: *"Alternatives
  considered at the time were not documented."* Do not ask the user and do not invent
  alternatives.
- **Decision:** a Y-statement inferred from the evidence, phrased honestly — e.g. *"In the context
  of [observed situation], we decided to **adopt X** (inferred from history), to achieve
  [observable outcome]."*
- **More Information** (mandatory here, unlike log-decision where it is optional):
  - list the evidence commits as `` `abc1234` (YYYY-MM-DD) — subject ``
  - if subjects contain `#NNN` and `git remote get-url origin` resolves to GitHub or GitLab,
    render them as PR/MR links
  - cross-link paired DRs with relative paths
  - end with a provenance line: *"This DR was reconstructed retroactively from git history on
    YYYY-MM-DD."*
- **Numbering:** continue sequentially from the highest existing number (in whatever naming
  pattern applies). When writing several in one run, number them in chronological order of
  decision date so the log reads sensibly.

### Phase 6 — Wrap Up

Report a table of written files (path, title, status, date). Remind the user these are
reconstructions worth a human review pass, and suggest committing them. Do not offer to improve
the DRs unless asked.

## Principles

- **Evidence over speculation.** Every claim in a backfilled DR must trace to a commit, diff, or
  commit message. Never fabricate alternatives, rationale, or context.
- **Mark reconstructions as such.** Readers must be able to tell a backfilled DR from one written
  at decision time — the provenance line is non-negotiable.
- **Never write without confirmation.** Mining and clustering are autonomous; writing is gated on
  the user's triage.
- **Fewer, well-evidenced DRs beat many speculative ones.** A medium-confidence candidate the user
  doesn't recognize is better skipped than written.
- **All git usage is read-only.** This skill never commits, checks out, or mutates the repository
  beyond writing DR files.
