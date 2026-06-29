---
name: implement-scenarios
description: >
  Implements automated tests for existing Gherkin scenarios (`.feature` files) the BDD way —
  outside-in and client-first: classify each scenario's best testing strategy, write the test that
  binds to it, watch it fail for the right reason, then drive the UI/API and domain code until it
  passes. Use whenever the user has `.feature` files and wants to automate, implement, wire up, or
  "make pass" their scenarios; turn Gherkin/BDD/SpecFlow/Reqnroll/Cucumber specs into real
  xUnit/NUnit/Vitest/Jest/pytest/Playwright tests; build a feature test-first (TDD) from acceptance
  criteria; decide which scenarios belong in unit vs service (Testcontainers) vs end-to-end tests; or
  keep a traceability link between scenarios and the tests that verify them — even when they don't
  say "BDD" or "TDD". This is BDD's automation step, the one that runs after define-behavior writes
  the Gherkin and review-feature-suite audits it. Do not use it to author or refine the Gherkin
  itself (that is define-behavior) or to reconcile a suite of feature files against each other (that
  is review-feature-suite).
argument-hint: "[path to a .feature file or features directory]"
allowed-tools: [Read, Glob, Grep, Edit, Write, Bash, AskUserQuestion]
---

# Implement Scenarios

BDD runs on three practices: **discovery** (what the system could do), **formulation** (capturing it as Gherkin), and **automation** (wiring scenarios to code so you know what the system actually does). `define-behavior` lives in formulation; this skill is automation. It takes `.feature` files that already exist and makes them executable, working outside-in: for each scenario, write the test that proves the behavior *before* the code that delivers it, then build inward until it passes. As the TDD discipline puts it — if you didn't watch the test fail, you don't know it tests the right thing.

Your distinctive job is the three things generic TDD doesn't cover: **classify** each scenario to the testing strategy that verifies it most cheaply, **bind** a test to it through a stable identifier, and **trace** the link so anyone can see which scenarios are covered. The inner red-green loop that grows the production code is ordinary TDD — drive it well, but the skill's taught core is classify, bind, and trace, not re-teaching unit testing.

Work in two phases, and keep them separate: classify the whole suite and get sign-off *first*, then implement one scenario at a time. Planning benefits from the global view; implementation must not. Writing every test up front and then all the code (horizontal slicing) produces tests that verify imagined behavior rather than real behavior — build vertical slices instead, one scenario fully red-to-green before the next.

## Orient before you automate

The findings that shape every later decision come from the project, so read it before touching anything.

**Steering.** Scan `.kiro/steering/`, `docs/`, and the repo root for standards-style files (`*standards*.md`, `*conventions*.md`, `testing-*.md`, `api-*.md`) and read every one you find. These define the team's preferred test pyramid, frameworks, and conventions. Precedence when sources disagree: an explicit steering document wins, then the repo's existing conventions, then the defaults below. When a steering doc contradicts what the codebase actually does (doc says NUnit, every project references xUnit), **surface the conflict to the user** rather than silently introducing a second framework — adopting both is almost never what they want.

**Stack and tooling.** Detect the language, test frameworks, and whether a Gherkin runner is already in use (SpecFlow/Reqnroll, cucumber-js, behave, godog) from the manifests (`*.csproj`, `package.json`, `pyproject.toml`, `go.mod`) and the existing test setup. What the project already does is a stronger, more current signal than any default.

**Greenfield or brownfield.** Inspect the repo to tell them apart. Brownfield (an app already exists) is the common case: follow the established architecture and add behavior plus its bound test. Greenfield (little or no app yet) needs a **walking skeleton first** — get the thinnest end-to-end path compiling and running before you drive scenario one, so the first acceptance test fails on a real assertion rather than on "nothing builds."

**Current coverage.** Build the trace matrix (see *Traceability*) so you know which scenarios are already covered, which are unverified, and which references are orphaned. Re-runs are incremental: work only the uncovered and unverified scenarios and leave covered ones alone.

## Check that each scenario can be automated

The `.feature` files are authoritative input — this skill does not author or rewrite them. But a scenario with no observable outcome ("Then it works"), or one that smuggles in two behaviors, cannot be bound to an honest assertion; forcing one yields a test that passes while verifying nothing. Run a light automatability check only: is there an observable `Then`, is it a single behavior, is it stated in domain terms rather than pure UI mechanics. When a scenario fails this, **stop and refer it back to `define-behavior`** — fixing Gherkin is that skill's job, not this one's. The only edit this skill ever makes to a `.feature` file is backfilling the scenario's identity tag, never its steps.

## Phase 1: Classify the whole suite

Classify every scenario, then present the plan and get sign-off before writing any code. Misclassification is expensive — a slow, brittle e2e test where a unit test would do is a cost paid on every future run — and the global view lets the user catch it cheaply.

Reason about a bottom-up ladder and pick the **lowest rung that genuinely verifies the behavior**:

- **unit** — behavior that lives in domain logic (a calculation, a rule, a state transition). Test the domain service in-process, no infrastructure.
- **service** — behavior that only exists across real adapters (persistence, messaging, a real HTTP boundary). Test through the service with its real dependencies via Testcontainers.
- **e2e** — a genuine user journey whose value is the path through the UI. Drive it with Playwright.

Steering may add rungs (consumer-driven contract tests, UI component tests); fold them into the same bottom-up reasoning. The principle is constant: push the test down until pushing further would stop verifying the behavior. Bind **exactly one** test to each scenario, at its chosen rung. The extra unit tests you write while building the code in Phase 2 are inner-loop tests — leave them unbound, or the matrix balloons and you have rebuilt the inverted pyramid.

Present the classification as a table the user can correct — scenario, chosen rung, one-line rationale, framework — plus the resulting distribution (how many unit/service/e2e), since the shape of that distribution is itself a signal. Use `AskUserQuestion` to confirm the plan and resolve any scenario you found genuinely ambiguous. Carry the answers into Phase 2.

## Phase 2: Implement one scenario at a time

For each scenario, in order, run the full outside-in loop before moving to the next:

1. **Backfill identity.** If the scenario has no `@SCN-NNNN` tag, add one (next free number in the suite). Never alter an existing ID — its whole purpose is to survive title and wording changes.
2. **Write the bound test, at the classified rung.** Reference the scenario's ID through the language's idiomatic carrier (see the convention below). Where the project already runs Gherkin (Reqnroll, cucumber-js, behave), write step bindings so the `.feature` stays executable living documentation; otherwise write a plain test that re-expresses the behavior in code and carries the ID. Default to plain — don't impose a Cucumber runner on a project that has none.
3. **Watch it fail for the right reason.** Run it. A real assertion failure is the goal; a compile error or "type not found" is *not* good enough — it proves nothing about the behavior. In greenfield, the walking skeleton is what lets this be a real failure.
4. **Drive the implementation inward.** Build the UI/API surface the test needs, then the domain code, growing it with an ordinary inner red-green loop. Lean on TDD practice here; keep those inner unit tests unbound.
5. **Watch it pass.** Run the bound test green, with the rest of the suite still green. Only now move to the next scenario.

**Honest fallback.** When a rung's infrastructure genuinely can't start in this environment — no Docker for Testcontainers, no browser or running app for Playwright — generate the test and mark the scenario **unverified** in the report. Never claim a green you did not witness; an unverified-but-honest result is worth more than a fake pass.

A `Scenario Outline` is one behavior with varied data: give it a single `@SCN` tag and bind one data-driven test that covers all `Examples` rows. A failing row is identified by the runner's per-case output, not by separate IDs.

## The scenario-to-test convention

The link is deliberately independent of any Gherkin runner: a stable ID on the scenario, the same literal ID carried in the test. Extraction is then a single ripgrep regardless of language.

```gherkin
@SCN-0042
Scenario: Unknown code is rejected and leaves the total unchanged
  ...
```

```
C#       [Trait("covers", "SCN-0042")]   or a [ScenarioRef("SCN-0042")] attribute
TS/JS    //@covers SCN-0042   (Playwright also: test("...", { tag: "@SCN-0042" }, ...))
Python   @pytest.mark.covers("SCN-0042")   or  # covers: SCN-0042
Go       // covers: SCN-0042
```

The idiomatic carrier is for the team and their tooling; the **literal ID string is the contract** the matrix relies on.

## Traceability

The trace matrix is a **derived view**, never a hand-maintained file — the source of truth is the `@SCN` tags in the `.feature` files and the ID references in the tests, so the view cannot drift out of sync. Regenerate it on demand by reconciling two ripgrep passes:

- scenario IDs (and scenarios lacking a tag) across the `.feature` files,
- ID references across the test tree.

Report each scenario as **covered** (bound test exists and is green), **unverified** (test exists but couldn't run here), **uncovered** (no bound test yet), **orphaned-ref** (a test references an ID that no scenario has), or **drifted** (the scenario's text changed after its bound test was written). Drift is a flag for the user to judge, not something to auto-fix — silently rewriting a test to match a changed spec hides a decision that is theirs to make. This stays grep-plus-judgment for now; only extract a script if you watch runs keep re-deriving the same reconciliation.

## Default frameworks

When greenfield with nothing to detect, scaffold with the mainstream choice for the stack, always overridden by detection or steering: C# → xUnit, TS/JS → Vitest (Jest if already present), Python → pytest, Go → the standard `testing` package; Testcontainers for the service rung and Playwright for e2e across all stacks.

## Before you finish

Re-read your work as a skeptical teammate, hunting the failures that survive a first pass:

- A bound test you never actually watched go from red to green — or one marked green when its infrastructure never started.
- A test that passes while asserting nothing, because the scenario it came from had no observable outcome and you papered over the gap instead of referring it back.
- A scenario pushed up to e2e (or down to unit) when a different rung would verify the same behavior more cheaply or more honestly.
- An inner-loop unit test accidentally tagged with a scenario ID, inflating the matrix.
- A regenerated matrix that disagrees with reality — an orphaned reference, an uncovered scenario, or drift you didn't surface.
- A steering-versus-codebase conflict you resolved silently instead of putting in front of the user.
