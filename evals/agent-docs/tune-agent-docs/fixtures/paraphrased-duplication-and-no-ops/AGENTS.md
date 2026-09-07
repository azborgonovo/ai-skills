# AGENTS.md

Instructions for Claude working in this repository.

## Working style

- Be careful when editing files.
- Add comments where appropriate.

## Tests

- No PR goes up until `pytest -q` passes locally.
- `make seed` must run before the integration tests, or the fixture tenant is missing and every
  order test fails with a bare `TenantNotFound`.

## Schema

- Migrations need a rollback path; don't ship one you can't undo.

## Rules

- Never use `print` for logging.
- Never commit secrets.
- Never edit files under `generated/`.
