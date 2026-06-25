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

BDD runs on three practices: **discovery** (what the system *could* do — a conversation about
concrete examples), **formulation** (what it *should* do — capturing those examples as Gherkin), and
**automation** (what it *actually* does — wiring scenarios to code). This skill lives in formulation
and leans on discovery — as Liz Keogh puts it, "having conversations is more important than capturing
conversations is more important than automating conversations."

Gherkin describes what a system does for a user in problem-domain terminology — not how the
system is built or tested. Writing it collaboratively establishes a shared language for talking
about the system, one the whole team uses all the way down into the code. A good feature file is an
executable specification anyone on the team could read and agree on, and it survives as living
documentation. Each scenario is a concrete, believable example of one behavior.

## Discover before you formulate

Good scenarios come out of a conversation, not a lone author. Real BDD discovery is a workshop where
three perspectives meet — the Product Owner (scope: what's in and out), the Tester (edge
cases and ways it breaks), and the Developer (the details each rule implies). You will often be
working solo from a ticket, so deliberately play all three roles, and map what the user gave you —
a ticket, user story, prose, existing `.feature` files, or related code — the way Example
Mapping does:

- **Rules** — the business rules and acceptance criteria the behavior must satisfy. Each rule
  anchors one or more scenarios (and can group them under a Gherkin `Rule:` where the tool supports
  it).
- **Examples** — one concrete, believable case illustrating each rule; each becomes a scenario.
  Cover the unhappy paths, not just the happy one — missing edge cases are the most common gap.
- **Questions** — anything load-bearing that's unclear or assumed. Wrong assumptions produce
  confident-looking but useless scenarios, so surface these and **ask rather than guess**.

Also settle the actor (role) who uses the capability, any preconditions shared across
scenarios (a `Background` candidate), and whether the user wants tightly single-behavior
scenarios (the default) or a journey spanning several steps (only when they ask).

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

- `Given` sets up context — prefer a meaningful state ("Given Ada is signed in as an Editor")
  over an imperative UI tour of clicks. Include only the preconditions the reader needs.
- `When` performs the single action under test. One `When` per scenario; extra data belongs in
  `Given`, not in more `When` steps.
- `Then` asserts an observable outcome — what changed, what the user sees, what the system
  reports. Never "it works" or "the user is logged in" with no visible signal.

Use `And`/`But` to extend a step type; never `Or` (branching means separate scenarios). Write steps
in third person, present tense, with string values in double quotes.

**Stay at the domain level.** Steps describe what the actor does and what the system does in
problem-domain terminology. Selectors, XPaths, URLs, "wait 2 seconds", HTTP verbs, SQL, and internal schema
do not belong in step text — unless the behavior under test is genuinely about that layer (e.g. a
scenario specifically about an API contract). Leaking mechanics couples the spec to one
implementation and makes it unreadable to non-engineers. Two tests keep steps at the right altitude:

- **Implementation-change test**: "Would this wording need to change if the implementation did — a
  UI redesign, REST→GraphQL, a new login method?" If yes, the step is too low-level; rewrite it in
  terms of intent.
- **1922 test**: could you describe this step to someone working before computers existed? Most
  software automates something a person could once do by hand; phrasing it that way strips out the
  technical assumptions and leaves the real business behavior.

**Use concrete, realistic data.** Believable example values (€80, "SPRING10", "Editor") make the
scenario read as a real specification. Avoid `foo`/`bar`/`test` placeholders unless the scenario is
deliberately about garbage or invalid input.

**Background, Outline, and tables — only when they earn it.**

- `Background`: one per feature, only for state shared by multiple scenarios. If a single
  scenario needs it, put it in that scenario's `Given`.
- `Scenario Outline` + `Examples`: only when the same behavior is exercised with several input
  variations. If the inputs don't change the behavior, a plain `Scenario` is clearer.
- Step data tables and `Examples` tables: use them instead of long `And` chains, with concise
  headers, and keep them to roughly one screen. A table growing without bound is a sign the scenario
  is drifting into pure data-driven testing.

Hold to one shared language across the file — the same term for the same role, object, or state
every time, reusing the words the business already uses. Don't swap "order"/"purchase"/"cart" for one
thing unless the product truly distinguishes them.

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

Re-read the draft as a skeptical teammate — not re-checking every rule above, but hunting the
failures that survive a first pass:

- A business rule from discovery with no scenario, or an assumption you guessed instead of asking.
- A scenario that smuggles in a second behavior or a second `When`, or a `Then` with no observable
  signal ("it works", "the user is logged in").
- A step that would break if the implementation changed — a selector, URL, wait, or SQL that fails
  the implementation-change test.
- Drifting vocabulary: the same role, object, or state called by two different names.
