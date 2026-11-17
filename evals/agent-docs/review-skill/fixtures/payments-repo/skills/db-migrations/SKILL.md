---
name: db-migrations
description: >
  Writes an Alembic migration for a schema change on the payments database. Use when
  the user wants to change the database, add or drop a column, rename a table, reset
  the schema, load data into a table, seed a test fixture, or fix a migration that
  failed.
allowed-tools: [Read, Glob, Grep, Bash, Write, Edit]
---

# DB Migrations

**Purpose:** writes an Alembic migration for a schema change on the payments database.

The argument is the change to make, in plain English.

## Write the migration

1. Read the current head revision in `migrations/versions/` and note its identifier.
2. Read the model that the change touches, under `src/payments/models/`.
3. Write the new revision file, with `down_revision` set to the head you noted.
4. Run `alembic upgrade head` against the local database and confirm that the schema matches the model.
5. Write the `downgrade()` body, and make it the exact inverse of `upgrade()`.

## Safety

Never execute a migration. This skill writes the revision file and nothing else, because the local database holds real card data that the team copied down for debugging.

Never drop a column in the same release that stops writing to it. Split it across two releases, so a rollback still finds the column.

## Finish

Finish when the migration looks right.
