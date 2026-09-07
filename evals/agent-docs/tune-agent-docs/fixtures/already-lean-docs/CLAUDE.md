# ledger-api

Go service that posts double-entry journal lines for the billing platform.

## Commands

- `make test` — unit tests. Needs no database.
- `make test-integration` — needs `make db-up` first; it truncates every table.
- `make lint` — `golangci-lint` with the config in `.golangci.yml`.

## Conventions

- Money is `int64` minor units. There is no `float64` in `internal/ledger/`.
- Every exported function that touches the database takes a `context.Context`
  first and a `*sql.Tx` second. The pool is never used directly outside
  `internal/db/`.
- Errors wrap with `fmt.Errorf("...: %w", err)`. `internal/apierr` maps them to
  status codes at the handler boundary, so handlers return errors rather than
  writing responses.

## Pitfalls

- `postings` has a partial unique index on `(entry_id, side)` that only covers
  rows where `voided_at IS NULL`. A void-and-repost must set `voided_at` in the
  same transaction as the new posting, or the insert fails.
- `TestSettlementRun` reads `testdata/settlement-2026-01.json`. The fixture
  encodes the 2026 bank calendar, so a failure after a holiday change is the
  fixture, not the code.
- The Kafka consumer group is `ledger-api-v2`. Renaming it replays the whole
  topic from the start.
