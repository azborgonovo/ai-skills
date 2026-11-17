---
name: implement-scenarios
description: >
  Implements automated tests for Gherkin scenarios (`.feature` files) that already exist, the BDD
  way: outside-in and client-first. Classifies the best testing strategy for each scenario, writes
  the test that binds to it, watches that test fail for the right reason, then drives the UI, the
  API, and the domain code until it passes. Use whenever the user has `.feature` files and wants to
  automate, implement, wire up, or "make pass" their scenarios. Use it to turn Gherkin, BDD,
  SpecFlow, Reqnroll, or Cucumber specs into real xUnit, NUnit, Vitest, Jest, pytest, or Playwright
  tests, to build a feature test-first (TDD) from acceptance criteria, to decide which scenarios
  belong in unit, service (Testcontainers), or end-to-end tests, or to keep a traceability link
  between scenarios and the tests that verify them. Use it even when the user never says "BDD" or
  "TDD". To author or refine the Gherkin itself, use define-behavior. To reconcile a suite of
  feature files against each other, use review-feature-suite.
argument-hint: "[path to a .feature file or features directory]"
allowed-tools: [Read, Glob, Grep, Edit, Write, Bash, AskUserQuestion]
---

# Implement Scenarios

BDD runs on three practices: discovery finds what the system can do, formulation captures it as Gherkin, and automation wires the scenarios to code. `define-behavior` does formulation. This skill does automation.

Work outside-in. For each scenario, write the test that proves the behavior *before* the code that delivers it, then build inward until it passes. If you did not watch the test fail, you do not know that it tests the right thing.

The inner red-green loop is ordinary TDD. The core of this skill is the three things that generic TDD leaves out. **Classify** each scenario to the cheapest testing strategy that verifies it. **Bind** one test to it through a stable identifier. **Trace** the link, so anyone can see which scenarios are covered.

Work in two phases. First classify the whole suite and get sign-off. Then implement one scenario at a time, fully from red to green, before you start the next. Planning needs the global view, and implementation must not use it. Writing every test up front and then all the code produces tests that verify imagined behavior.

## Orient before you automate

Read the project before you touch anything.

**Steering**: Scan the repo root, `docs/`, and any harness steering directory, such as `.claude/rules/`, `.cursor/rules/`, and `.kiro/steering/`. Read every file that matches `*standards*.md`, `*conventions*.md`, `testing-*.md`, or `api-*.md`. These define the team's test pyramid, frameworks, and conventions. An explicit steering document wins, then the repo's existing conventions, then the defaults below. A steering doc can contradict the codebase, for example when the doc names NUnit and every project references xUnit. **Always** put that conflict in front of the user. Do not add a second framework in silence, because a project almost never wants both.

**Stack and tooling**: Read the manifests (`*.csproj`, `package.json`, `pyproject.toml`, `go.mod`) and the existing test setup. Detect the language, the test frameworks, and any Gherkin runner, such as SpecFlow, Reqnroll, cucumber-js, behave, or godog. What the project already does beats any default.

**Greenfield or brownfield**: In brownfield, the common case, an app exists. Follow its architecture, and add the behavior plus its bound test. In greenfield, little or no app exists. Build a walking skeleton first: the thinnest end-to-end path that compiles and runs. Then the first acceptance test fails on a real assertion instead of on "nothing builds".

**Current coverage**: Build the trace matrix, as described under *Traceability*. A re-run is incremental: work the uncovered and unverified scenarios, and leave the covered ones alone.

## Make sure that each scenario can be automated

The `.feature` files are authoritative input. The only edit that this skill makes to one is a scenario's identity tag. **Never** edit the steps.

Ask three questions of each scenario. Is there an observable `Then`? Is it a single behavior? Is it stated in domain terms instead of pure UI mechanics? A scenario that fails, such as "Then it works" or one with two behaviors, cannot bind to an honest assertion. A forced binding yields a test that passes and verifies nothing. **Stop and refer it back to `define-behavior`**, and report it as uncovered.

## Phase 1: Classify the whole suite

Classify every scenario, then present the plan and get sign-off before you write any code. A slow, brittle end-to-end test in place of a unit test costs time on every run. The global view lets the user catch that cheaply.

Pick the **lowest rung that genuinely verifies the behavior**:

- **unit**: behavior in domain logic, such as a calculation, a rule, or a state transition. Test the domain service in-process, with no infrastructure.
- **service**: behavior that exists only across real adapters, such as persistence, messaging, or a real HTTP boundary. Test through the service with real dependencies, through Testcontainers.
- **e2e**: a user journey whose value is the path through the UI. Drive it with Playwright.

Steering can add rungs, such as contract tests or UI component tests. Fold them into the same ladder: push the test down until one more step down stops verifying the behavior.

Bind **exactly one** test to each scenario, at its rung. The unit tests that you write in the Phase 2 inner loop stay unbound. Otherwise the matrix balloons, and you rebuild the inverted pyramid.

Present a table that the user can correct: one row per scenario, with the rung, a one-line rationale, and the framework. Add the count of unit, service, and end-to-end tests, because the shape of that distribution is a signal. Use `AskUserQuestion` to confirm the plan and to resolve any ambiguous scenario. Carry the answers into Phase 2.

## Phase 2: Implement one scenario at a time

For each scenario, in order:

1. **Backfill identity.** If the scenario has no `@SCN-NNNN` tag, add one with the next free number in the suite. Never alter an existing ID, because its purpose is to survive a change of title or wording.
2. **Write the bound test, at the classified rung.** Carry the scenario ID as the convention below shows. Where the project already runs Gherkin, through Reqnroll, cucumber-js, or behave, write step bindings, so the `.feature` file stays executable. Otherwise write a plain test that re-expresses the behavior and carries the ID. Do not impose a Cucumber runner on a project that has none.
3. **Watch it fail for the right reason.** Run it. The goal is a real assertion failure. A compile error or a "type not found" error proves nothing about the behavior.
4. **Drive the implementation inward.** Build the UI or API surface that the test needs, then the domain code, with an ordinary inner red-green loop.
5. **Watch it pass.** Run the bound test green, with the rest of the suite still green. Only then move on.

**Honest fallback**: Sometimes a rung's infrastructure cannot start here, such as Docker for Testcontainers, or a browser or running app for Playwright. Then generate the test and report the scenario as unverified. **Never** claim a green result that you did not witness.

A `Scenario Outline` is one behavior with varied data. Give it one `@SCN` tag, and bind one data-driven test that covers every `Examples` row. The runner's per-case output identifies a failing row.

## The scenario-to-test convention

The link is independent of any Gherkin runner. A stable ID sits on the scenario, and the test carries the same literal ID, so one ripgrep extracts it in any language.

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

The idiomatic carrier serves the team's tooling. The **literal ID string is the contract** that the matrix relies on.

## Traceability

The trace matrix is a derived view, never a file kept up to date by hand, so it cannot drift. Regenerate it on demand by reconciling two ripgrep passes:

- Scenario IDs across the `.feature` files, plus the scenarios with no tag.
- ID references across the test tree.

Report each scenario in one of five states:

- **Covered**: a bound test exists and is green.
- **Unverified**: the test exists and did not run here.
- **Uncovered**: no bound test exists.
- **Orphaned-ref**: a test references an ID that no scenario has.
- **Drifted**: the scenario text changed after its bound test was written.

Flag drift for the user to judge. A test rewritten in silence to match a changed specification hides a decision that belongs to the user. Do ripgrep plus judgment, and write no reconciliation script.

## Default frameworks

In greenfield, with nothing to detect, use xUnit for C# and pytest for Python. Use Vitest for TS and JS, or Jest when Jest is already present. Use the standard `testing` package for Go. Use Testcontainers for the service rung and Playwright for end-to-end tests on every stack.

## Before you finish

Re-read your work as a skeptical teammate, and hunt for:

- A bound test that you never watched go from red to green, or one marked green when its infrastructure never started.
- A test that asserts nothing, because you papered over a scenario with no observable outcome instead of referring it back.
- A scenario at end-to-end or unit when another rung verifies it more cheaply or more honestly.
- An inner-loop unit test tagged with a scenario ID by accident.
- A matrix that disagrees with reality: an orphaned reference, an uncovered scenario, or drift that you did not report.
- A conflict between steering and the codebase that you resolved in silence.
