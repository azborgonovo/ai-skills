---
name: define-behavior
description: >
  Writes behavior-driven features and scenarios in Gherkin (`.feature` files) that read as
  specification by example — domain-level, one behavior per scenario, observable outcomes. Use this
  skill whenever the user wants to author or refine Gherkin, BDD scenarios, acceptance criteria,
  Given/When/Then steps, feature files, or Cucumber/SpecFlow/Behave specs — even when they describe
  the behavior in plain prose and don't say "Gherkin". Also use to turn a ticket, user story, or
  acceptance criteria into scenarios, or to clean up scenarios that leak UI/API/DB mechanics. Do not
  use for writing the automation code behind the steps — that is a separate concern.
argument-hint: "[feature description, ticket, or path to a .feature file]"
---

# Define Behavior

Gherkin describes **what** a system does for a user, in the language of the business — not how it is
built or tested. A good feature file is a specification anyone on the team could read and agree on,
where each scenario is a concrete, believable example of one behavior. Write for the human reader
first; the automation that runs these scenarios is a later, separate concern.

## Gather context before writing

Work from whatever the user already gave you — a ticket, a user story, prose, existing `.feature`
files, or related code. Read it, infer the behavior, and draft.

Wrong assumptions produce confident-looking but useless scenarios, so when something load-bearing is
unclear, **ask rather than guess**. The things worth asking about:

- The **behavior or capability** being specified, and the **actor** (role) who uses it.
- The **business rules and edge cases** — what should happen on the unhappy paths, not just the
  happy one. Missing edge cases are the most common gap.
- Any **shared preconditions** across scenarios (candidates for a `Background`).
- Whether the user wants tightly **single-behavior** scenarios (the default) or a **journey** that
  walks several steps — only do the latter when they ask for it.

Over-asking beats inventing requirements. A short clarifying exchange is cheaper than a feature file
that specifies the wrong thing.

## How to write each part

**File and feature.** One `Feature` per file; kebab-case `.feature` filename aligned with the
feature title. Indent the body by 2 spaces. Put a short user story under the title so the value is
explicit:

```gherkin
Feature: Discount codes at checkout
  As a shopper
  I want to apply a discount code to my order
  So that I pay the reduced price I was promised
```

**Scenarios — one behavior each.** Each scenario targets a single behavior and must run
independently of the others. Give it a one-line, behavior-focused title (what is true, not "test
X"). Keep it short — if it runs past ~10 steps or needs a second `When`, it is probably two
scenarios. Map the keywords to Arrange / Act / Assert and keep them in order:

- `Given` sets up context — prefer a meaningful **state** ("Given Ada is signed in as an Editor")
  over an imperative UI tour of clicks. Include only the preconditions the reader needs.
- `When` performs the **single action** under test. One `When` per scenario; extra data belongs in
  `Given`, not in more `When` steps.
- `Then` asserts an **observable** outcome — what changed, what the user sees, what the system
  reports. Never "it works" or "the user is logged in" with no visible signal.

Use `And`/`But` to extend a step type; never `Or` (branching means separate scenarios). Write steps
in third person, present tense, with string values in double quotes.

**Stay at the domain level.** Steps describe what the actor does and what the system does in product
language. Selectors, XPaths, URLs, "wait 2 seconds", HTTP verbs, SQL, and internal schema do not
belong in step text — unless the behavior under test is genuinely about that layer (e.g. a scenario
specifically about an API contract). Leaking mechanics couples the spec to one implementation and
makes it unreadable to non-engineers.

**Use concrete, realistic data.** Believable example values (€80, "SPRING10", "Editor") make the
scenario read as a real specification. Avoid `foo`/`bar`/`test` placeholders unless the scenario is
deliberately about garbage or invalid input.

**Background, Outline, and tables — only when they earn it.**

- `Background`: one per feature, only for state shared by **multiple** scenarios. If a single
  scenario needs it, put it in that scenario's `Given`.
- `Scenario Outline` + `Examples`: only when the **same** behavior is exercised with several input
  variations. If the inputs don't change the behavior, a plain `Scenario` is clearer.
- Step **data tables** and `Examples` tables: use them instead of long `And` chains, with concise
  headers, and keep them to roughly one screen. A table growing without bound is a sign the scenario
  is drifting into pure data-driven testing.

Keep one consistent vocabulary for roles, objects, and states across the file — don't swap
"order"/"purchase"/"cart" for the same thing unless the product truly distinguishes them.

## Examples

**Leaking UI mechanics → domain-level state and action.** The "before" is brittle and unreadable;
the "after" specifies the same behavior in product language.

```gherkin
# Before — imperative, mechanical, no clear behavior
Scenario: Login test
  Given I open "https://app.example.com/login"
  When I type "ada@example.com" into "#email"
  And I type "hunter2" into "#password"
  And I click "#submit"
  And I wait 2 seconds
  Then I see "Dashboard"

# After — declarative, observable, one behavior
Scenario: Registered user reaches their dashboard after signing in
  Given Ada is a registered user with the "Editor" role
  When she signs in with valid credentials
  Then she sees her personal dashboard
```

**Two behaviors crammed together → split, each with an observable outcome.**

```gherkin
# Before — two behaviors, a second When, a vague assertion
Scenario: Discount code
  Given a shopper has €80 of items in their cart
  When they apply the code "SPRING10"
  Then it works
  When they apply the code "BOGUS"
  Then there is an error

# After — one behavior per scenario, concrete observable results
Scenario: Valid code reduces the order total
  Given a shopper has €80 of items in their cart
  When they apply the code "SPRING10"
  Then the order total drops to €72

Scenario: Unknown code is rejected and leaves the total unchanged
  Given a shopper has €80 of items in their cart
  When they apply the code "BOGUS"
  Then the code is rejected with the message "We don't recognise that code"
  And the order total stays at €80
```

**Input variations of one behavior → `Scenario Outline`.**

```gherkin
Scenario Outline: Password strength is enforced at sign-up
  Given a visitor is creating an account
  When they set their password to "<password>"
  Then the password is "<verdict>"

  Examples:
    | password        | verdict  |
    | short           | rejected |
    | correcthorse42  | accepted |
```

## Before you finish

Read the draft once more as a skeptical teammate and check:

- Each scenario specifies **one** behavior, runs independently, and has a single `When`.
- Every `Then` is **observable** — a reader can tell exactly what to look for.
- Steps are domain-level: no selectors, URLs, waits, SQL, or schema unless the behavior is about
  that layer.
- `Given` context is minimal but sufficient; data is concrete and realistic.
- Strict `Given → When → Then` order; vocabulary is consistent; no `Or`.
- `Background`/`Scenario Outline`/tables are used only where they earn their place.
- The feature has a title and user story, lives in a kebab-case `.feature` file, and is indented 2
  spaces.
