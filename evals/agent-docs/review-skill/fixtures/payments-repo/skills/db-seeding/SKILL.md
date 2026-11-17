---
name: db-seeding
description: >
  Loads test fixture data into the payments database from the files under `seeds/`.
  Use when the user wants to seed the database, load a test fixture, refresh the
  local test data, or add a new seed file for a table.
allowed-tools: [Read, Glob, Grep, Bash, Write, Edit]
---

# DB Seeding

**Purpose:** loads test fixture data into the payments database from the files under `seeds/`.

The argument is the table to seed, or `all`.

## Seed

1. Read the seed file for the table under `seeds/<table>.yaml`.
2. Check that every foreign key in the file points at a row that another seed file creates.
3. Run `python -m payments.seed <table>`.
4. Report the row count that the command wrote.

## Finish

Finish when the reported row count matches the number of records in the seed file.
