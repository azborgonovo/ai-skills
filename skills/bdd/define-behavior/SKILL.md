---
name: define-behavior
description: >
  Writes behavior-driven features and scenarios in Gherkin (`.feature` files) that read as
  specification by example: domain-level, one behavior per scenario, observable outcomes. Use this
  skill whenever the user wants to author or refine Gherkin, BDD scenarios, acceptance criteria,
  Given/When/Then steps, feature files, or Cucumber, SpecFlow, or Behave specs. Use it even when the
  user describes the behavior in plain prose and never says "Gherkin". Use it also to turn a ticket,
  a user story, or acceptance criteria into scenarios, and to clean up scenarios that leak UI, API,
  or database mechanics. Do not use it to write the automation code behind the steps, which is a
  separate concern.
argument-hint: "[feature description, ticket, or path to a .feature file]"
allowed-tools: [Read, Glob, Grep, Edit, Write, AskUserQuestion]
---

# Define Behavior

This skill formulates behavior as Gherkin, and it starts with discovery. The conversation about examples matters more than the capture, and the capture matters more than the automation. Gherkin describes what a system does for a user, in the terminology of the problem domain, and not how the system is built or tested. A good feature file is an executable specification that anyone on the team can read and agree on.

## Discover before you formulate

You often work alone from a work item, so play the three discovery roles yourself. The Product Owner sets the scope, the Tester brings edge cases and failures, and the Developer brings the details that each rule implies. Map the input the way Example Mapping does. The input is a work item, a user story, prose, existing `.feature` files, or related code.

- **Rules**: the business rules and acceptance criteria that the behavior must satisfy. Where the tool supports it, group the scenarios of a rule under a Gherkin `Rule:` keyword.
- **Examples**: one concrete and believable case for each rule. Each example becomes a scenario. Cover the unhappy paths as well as the happy one, because a missing edge case is the most common gap.
- **Questions**: anything load-bearing that is unclear or assumed. Raise each question and **ask rather than guess**. A short clarifying exchange costs less than a feature file that specifies the wrong thing.

Also settle the actor, which is the role that uses the capability. Settle any precondition that several scenarios share, because it is a `Background` candidate. Write tight single-behavior scenarios by default, and write a journey across several steps only on request.

## How to write each part

**File and feature.** Write one `Feature` per file. Name the file in kebab-case, aligned with the feature title, with the `.feature` extension. Indent the body by 2 spaces. Put a short user story (`As a` / `I want` / `So that`) under the title, so the value is explicit.

**Scenarios, one behavior each.** Each scenario targets a single behavior and runs independently of the others. Give it a one-line title that names the behavior, which is what is true, not "test X". If it runs past roughly 10 steps, or if it needs a second `When`, it is usually two scenarios. Map the keywords to Arrange, Act, and Assert, in that order:

- `Given` sets up the context. Include only the preconditions that the reader needs.
- `When` performs the single action under test. Extra data belongs in `Given`.
- `Then` asserts an observable outcome: what changed, what the user sees, or what the system reports. Never write "it works", and never write "the user is logged in" with no visible signal.

Use `And` and `But` to extend a step type. Never use `Or`, because a branch means two scenarios. Write steps in the third person and the present tense, with string values in double quotes.

**Stay at the domain level.** Every step describes what the actor does and what the system does, in domain terms. Prefer a meaningful state, such as "Given Ada is signed in as an Editor", over an imperative tour of clicks. Selectors, XPaths, URLs, "wait 2 seconds", HTTP verbs, SQL, and the internal schema do not belong in step text. The exception is a behavior that is genuinely about that layer, such as an API contract.

- **Implementation-change test**: ask whether the wording has to change when the implementation changes, such as a UI redesign, a move from REST to GraphQL, or a new login method. If yes, the step sits too low. Rewrite it in terms of intent.
- **1922 test**: describe the step to someone who worked before computers existed. What remains is the business behavior.

**Use concrete and realistic data**, such as €80, "SPRING10", and "Editor". Do not use `foo`, `bar`, or `test` placeholders, unless the scenario is deliberately about invalid input.

**Background, Outline, and tables, only when they earn it.**

- `Background`: write at most one per feature, and only for state that several scenarios share. State that one scenario needs goes in its own `Given`.
- `Scenario Outline` with `Examples`: use it only when one behavior runs with several input variations. When the inputs do not change the behavior, a plain `Scenario` is clearer.
- Step data tables and `Examples` tables: use them in place of long `And` chains. Keep the headers concise and each table within roughly one screen. A table that grows without bound means the scenario drifts into pure data-driven testing.

Hold to one shared language across the file. Use the same term for the same role, object, or state every time, and reuse the words that the business already uses. Do not swap "order", "purchase", and "cart" for one thing, unless the product truly distinguishes them.

## Examples

**Leaked UI mechanics, rewritten as domain-level state and action.**

```gherkin
# Before: imperative, mechanical, no clear behavior
Scenario: Login test
  Given I open "https://app.example.com/login"
  When I type "ada@example.com" into "#email"
  And I type "hunter2" into "#password"
  And I click "#submit"
  And I wait 2 seconds
  Then I see "Dashboard"

# After: declarative, observable, one behavior
Scenario: Registered user reaches their dashboard after signing in
  Given Ada is a registered user with the "Editor" role
  When she signs in with valid credentials
  Then she sees her personal dashboard
```

**Two behaviors in one scenario, split so each has an observable outcome.**

```gherkin
# Before: two behaviors, a second When, a vague assertion
Scenario: Discount code
  Given a shopper has €80 of items in their cart
  When they apply the code "SPRING10"
  Then it works
  When they apply the code "BOGUS"
  Then there is an error

# After: one behavior per scenario, concrete observable results
Scenario: Valid code reduces the order total
  Given a shopper has €80 of items in their cart
  When they apply the code "SPRING10"
  Then the order total drops to €72

Scenario: Unknown code is rejected and leaves the total unchanged
  Given a shopper has €80 of items in their cart
  When they apply the code "BOGUS"
  Then the code is rejected with the message "We don't recognize that code"
  And the order total stays at €80
```

## Before you finish

Re-read the draft as a skeptical teammate. Do not re-check every rule above. Hunt the four failures that survive a first pass:

- A business rule from discovery with no scenario, or an assumption you guessed instead of asking about.
- A scenario with a second behavior, a second `When`, or a `Then` with no observable signal.
- A step that fails the implementation-change test.
- Drifting vocabulary, where one role, object, or state carries two names.
