---
status: adopted
date: 2024-02-12
decision-makers: Ana Reis, Tom Whelan
---

# DR-0001: Use PostgreSQL as the primary datastore

## Context and Problem Statement

The service keeps orders, sessions, and audit rows in one place. We needed a datastore that the team can run in CI and in production without a second operational skill set.

## Considered Options

### PostgreSQL
**Pros** — one engine for relational rows and JSON documents. The team already operates it.
**Cons** — session writes share capacity with order traffic.

### MongoDB
**Pros** — flexible documents, and no migration step for a shape change.
**Cons** — a second engine to operate, and weaker transactional guarantees than the order flow needs.

## Decision

In the context of storing orders, sessions, and audit rows, facing a small team with one database skill set, we decided for **PostgreSQL**, to achieve one engine to operate and to back up, accepting that session writes share capacity with order traffic.

## Consequences

Session state lives in the same database as orders, so a spike in logins shows up as order latency.
