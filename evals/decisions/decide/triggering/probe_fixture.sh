#!/usr/bin/env bash
# Seeds what the probes assume the working directory already holds: a decision
# directory with records in it. Two hold probes name a path inside it, and
# without the directory those probes would measure a missing folder instead of
# the skill description boundary.
set -euo pipefail

mkdir -p docs/decisions

cat > docs/decisions/DR-0001-monorepo.md <<'EOF'
# DR-0001: One repository for the platform services

- Status: Accepted
- Date: 2024-02-19
- Owner: Platform team

## Context

Five services lived in five repositories with copied CI configuration.

## Decision

Move the platform services into one repository.

## Consequences

- A change that spans services lands in one commit.
- CI must select what to build, because building everything takes too long.
EOF

cat > docs/decisions/DR-0002-grpc-for-internal-calls.md <<'EOF'
# DR-0002: gRPC for internal service calls

- Status: Accepted
- Date: 2024-06-03
- Owner: Platform team

## Context

Internal services spoke JSON over HTTP with hand-written clients.

## Decision

Standardise on gRPC for service-to-service calls. Public endpoints stay REST.

## Consequences

- Clients are generated, so a schema change breaks the build instead of production.
- Browsers cannot call internal services directly. A gateway translates.
EOF

cat > docs/decisions/DR-0004-postgres-over-dynamodb.md <<'EOF'
# DR-0004: Postgres over DynamoDB for the orders store

- Status: Accepted
- Date: 2024-11-12
- Owner: Platform team

## Context

The orders service needed a primary store. The team had run DynamoDB for the
session cache and Postgres for everything else.

## Decision

Use Postgres for the orders store.

## Consequences

- Joins across orders and customers stay in the database, so the service keeps
  no denormalised copy of customer data.
- A single writer limits write throughput. The team accepted that limit because
  orders peak at a few hundred writes a second.
- Operating one engine instead of two keeps the on-call surface small.
EOF
