# CLAUDE.md

Guidance for the agent working on the Meridian billing service.

## Testing

- Mock all external services in every test, including integration tests, with no exceptions.
  A test that reaches a real Postgres, a real Redis, or a real Stripe endpoint is not accepted.
- Run `pytest -q` before you push.

## Code

- Money is `Decimal`, never `float`. Amounts cross the Stripe boundary as integer cents.
- Every ORM model carries a `tenant_id` column, and every query filters on it.

## Working style

- The agent picks the smallest change that satisfies the request.
- When a request is ambiguous, the agent states the assumption it made in its final answer.
