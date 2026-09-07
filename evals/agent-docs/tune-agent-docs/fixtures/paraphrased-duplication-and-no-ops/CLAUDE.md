# CLAUDE.md

Guidance for Claude working on the Meridian orders service.

## General

- Write clean, readable code.
- Follow industry best practices.
- Think carefully before making changes.

## Tests

- Run the full suite with `pytest -q` before opening a pull request.
- Unit tests live in `tests/unit` and integration tests live in `tests/integration`.

## Migrations

- Every database migration must be reversible -- always write the down step.
- The `status` Postgres enum on `orders_v2` needs its own migration, and that migration must set
  `transaction_per_migration = False`. Postgres refuses `ALTER TYPE ... ADD VALUE` inside a
  transaction block, and a combined migration leaves the revision table half-applied.

## Commits

- Write every commit message as a Conventional Commit, in the shape `type(scope): subject`.
- Keep the subject under 72 characters.

## Before you push

1. Format with `black`, line length 100.
2. Check that each commit message follows Conventional Commits, in the shape `type(scope): subject`.
3. Rebase on `main`.
