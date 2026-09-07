# AGENTS.md

Instructions for the assistant working in this repository.

## Layout

`src/api` holds the HTTP layer, `src/billing` holds invoice logic, and `src/payments` holds the
Stripe integration. The assistant keeps business logic out of the router modules.

## Testing

- Unit tests live in `tests/unit` and integration tests live in `tests/integration`.
- `make seed` must run before the integration suite, or the fixture tenant is missing.

## Commit style

- Claude writes every commit message as a Conventional Commit, in the shape `type(scope): subject`.
- Claude keeps the subject under 72 characters.
- Claude never amends a commit that is already pushed.
