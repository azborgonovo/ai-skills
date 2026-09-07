---
status: adopted
date: 2024-06-03
decision-makers: Ana Reis, Priya Nandakumar
---

# DR-0003: Serve the public API with FastAPI

## Context and Problem Statement

The public API grew out of a maintenance script. It needed a framework that validates a request and publishes an OpenAPI document that clients can generate from.

## Considered Options

### FastAPI
**Pros** — generated OpenAPI, and the team already writes Pydantic models.
**Cons** — dependency injection is tied to the route signature, so a shared service travels through every handler that needs it.

### Django REST Framework
**Pros** — mature, and it carries batteries for auth and admin.
**Cons** — it brings an ORM and an admin site that this service does not use.

## Decision

In the context of turning a script into a public API, facing a need for request validation and documented endpoints, we decided for **FastAPI**, to achieve generated OpenAPI from the models we already write, accepting that dependency injection stays tied to the route signature.

## Consequences

A shared service reaches a handler as a parameter. A new cross-cutting concern needs a new parameter on every route that uses it.
