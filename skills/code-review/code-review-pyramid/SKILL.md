---
name: code-review-pyramid
description: >
  Knowledge base for the Code Review Pyramid — a framework for structuring code reviews across
  five layers prioritized by cost-of-change. Use when the user asks how to approach a code review,
  wants to understand what to focus on in a review, asks about review priorities, or references
  "the pyramid". Also use when another skill needs a structured review framework (e.g.
  review-changes loads it to apply consistent layer priorities and questions).
---

# Code Review Pyramid

The Code Review Pyramid orders review attention by what a problem costs to fix later. It has five layers, numbered from the base up. Give the base the most manual attention, because a change there is the hardest to reverse. Give the apex the least, and automate its checks where you can. Each layer lists the questions to ask.

*Adapted from the [Code Review Pyramid](https://www.morling.dev/blog/the-code-review-pyramid/) by [Gunnar Morling](https://www.morling.dev/), licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*

## Layer 1: API Semantics

Focus here most.

- API as small as possible, as large as needed?
- Is there one way of doing one thing, not multiple?
- Is it consistent? Does it follow the principle of least surprise?
- Clean split of API/internals, without internals leaking in the API?
- Are there no breaking changes to user-facing parts (API classes, configuration, metrics, log formats, etc.)?
- Is a new API generally useful and not overly specific?

## Layer 2: Implementation Semantics

Focus here.

- Does it satisfy the original requirements?
- Is it logically correct?
- Is there no unnecessary complexity?
- Is it robust? (no concurrency issues, proper error handling)
- Is it performant?
- Is it secure? (e.g. no SQL injection, no sensitive data exposure, etc.)
- Is it observable? (e.g. metrics, logging, tracing, etc.)
- Do newly added dependencies pull their weight? Are their licenses acceptable?

## Layer 3: Documentation

- Are new features reasonably documented?
- Are the relevant kinds of docs covered: README, API docs, user guide, reference docs, etc.?
- Are docs understandable? Are there no significant typos or grammar mistakes?

## Layer 4: Tests

Automate where possible.

- Are all tests passing?
- Are new features reasonably tested?
- Are corner cases tested?
- Is it using unit tests where possible, integration tests where necessary?
- Are there tests for NFRs, e.g. performance?

## Layer 5: Code Style

Automate.

- Is the project's formatting style applied?
- Does it adhere to agreed naming conventions?
- Is it DRY?
- Is the code sufficiently readable? (method lengths, etc.)
