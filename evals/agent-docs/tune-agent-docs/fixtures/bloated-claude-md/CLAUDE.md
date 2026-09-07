# CLAUDE.md

This file tells the agent how to work in the Meridian billing platform. Read all of it before you
touch anything in this repository.

## Build and test commands

- `make install` installs the Python dependencies into `.venv`.
- `make build` compiles the protobuf stubs and builds the Docker image.
- `make test` runs the unit suite with `pytest -q`.
- `make test-integration` runs the integration suite against the docker-compose stack.
- `make lint` runs `ruff check .` and `black --check .`.
- `make seed` loads the demo tenant into the local Postgres.

## Directory layout

- `src/` - all application code.
- `src/api/` - FastAPI routers and request schemas.
- `src/api/routers/` - one module per resource.
- `src/api/schemas/` - Pydantic request and response models.
- `src/api/deps.py` - dependency-injection providers.
- `src/billing/` - invoice generation and proration.
- `src/billing/proration.py` - proration arithmetic.
- `src/billing/invoices.py` - invoice assembly.
- `src/billing/tax.py` - tax rate lookup.
- `src/payments/` - the Stripe integration.
- `src/payments/webhooks.py` - the webhook receiver.
- `src/payments/refunds.py` - the refund flow.
- `src/payments/client.py` - the Stripe API client wrapper.
- `src/accounts/` - tenants, users, and roles.
- `src/accounts/models.py` - the ORM models for accounts.
- `src/notifications/` - email and webhook fan-out.
- `src/common/` - shared helpers.
- `src/common/db.py` - the SQLAlchemy session factory.
- `src/common/cache.py` - the Redis client wrapper.
- `src/common/logging.py` - structured logging setup.
- `migrations/` - Alembic migrations, one file per revision.
- `tests/` - the whole test suite.
- `tests/unit/` - unit tests, no external services.
- `tests/integration/` - integration tests against docker-compose.
- `tests/fixtures/` - shared pytest fixtures.
- `scripts/` - operational scripts.
- `deploy/` - Helm charts and Kubernetes manifests.
- `docs/` - long-form documentation.

## Dependencies

- `fastapi` 0.111 - the HTTP framework.
- `uvicorn` 0.30 - the ASGI server.
- `pydantic` 2.7 - request and response validation.
- `sqlalchemy` 2.0 - the ORM.
- `alembic` 1.13 - database migrations.
- `psycopg` 3.1 - the Postgres driver.
- `redis` 5.0 - the Redis client.
- `stripe` 9.5 - the payments SDK.
- `celery` 5.4 - the background worker.
- `httpx` 0.27 - the outbound HTTP client.
- `structlog` 24.1 - structured logging.
- `pytest` 8.2 - the test runner.
- `pytest-asyncio` 0.23 - async test support.
- `factory-boy` 3.3 - test object factories.
- `black` 24.4 - the formatter.
- `ruff` 0.4 - the linter.
- `mypy` 1.10 - the type checker.
- `celery-redbeat` 2.2 - the scheduler backend.
- `orjson` 3.10 - fast JSON serialization.
- `tenacity` 8.3 - retry decorators for outbound calls.
- `python-multipart` 0.0.9 - form parsing for file upload.
- `sentry-sdk` 2.3 - error reporting.

## Architecture overview

Meridian is a three-tier web application. The presentation tier is a FastAPI application that
serves JSON over HTTP. The application tier holds the business logic in the `billing`, `payments`,
`accounts`, and `notifications` packages. The data tier is a Postgres database with a Redis cache
in front of the hot paths.

Requests arrive at the API gateway, which terminates TLS and forwards to the uvicorn workers. Each
worker handles a request inside an asyncio event loop. The router validates the request with a
Pydantic schema, then calls into a service module. The service module opens a database session,
does its work, and commits. The response schema serializes the result back to JSON.

Long-running work does not happen inside a request. The service module publishes a Celery task and
returns straight away. The worker pool picks the task up and runs it against the same database.
Failed tasks retry with exponential backoff up to five times, then land in the dead-letter queue.

The system follows a layered architecture. Routers depend on services, services depend on
repositories, and repositories depend on the database. Nothing ever depends upwards. This keeps
the business logic testable without an HTTP client.

## Onboarding checklist

1. Install Docker Desktop and start it.
2. Install Python 3.12 with pyenv.
3. Clone the repository and `cd` into it.
4. Run `make install` to build the virtual environment.
5. Copy `.env.example` to `.env`.
6. Ask the platform team for the Stripe test key and put it in `.env`.
7. Run `docker compose up -d` to start Postgres and Redis.
8. Run `alembic upgrade head` to create the schema.
9. Run `make seed` to load the demo tenant.
10. Run `make test` and check that the suite is green.
11. Run `make test-integration` and check that suite too.
12. Open http://localhost:8000/docs and confirm the API responds.
13. Join the `#meridian-dev` channel.
14. Read the onboarding page on the wiki.

## Deploying to production

Follow every step in order. Do not skip a step, even for a one-line change.

1. Check that `main` is green in CI.
2. Run `scripts/changelog.py` to draft the release notes.
3. Open the release notes and edit the summary line.
4. Tag the commit with `git tag -a vX.Y.Z -m "release vX.Y.Z"`.
5. Push the tag with `git push origin vX.Y.Z`.
6. Wait for the release pipeline to build and push the image.
7. Confirm the image digest in the pipeline log matches the tag.
8. Run `helm diff upgrade meridian deploy/chart -f deploy/staging.yaml`.
9. Read the diff and confirm no unexpected resource is replaced.
10. Run `helm upgrade meridian deploy/chart -f deploy/staging.yaml`.
11. Watch the staging rollout with `kubectl rollout status deploy/meridian`.
12. Run the smoke suite with `scripts/smoke.py --env staging`.
13. Check the staging error rate on the Grafana dashboard for ten minutes.
14. Announce the production deploy in `#meridian-releases`.
15. Run `helm diff upgrade meridian deploy/chart -f deploy/prod.yaml`.
16. Run `helm upgrade meridian deploy/chart -f deploy/prod.yaml`.
17. Watch the production rollout with `kubectl rollout status deploy/meridian`.
18. Run `scripts/smoke.py --env prod`.
19. Watch the error rate and the p99 latency for thirty minutes.
20. If either regresses, run `helm rollback meridian` and page the on-call engineer.
21. Close the release ticket and paste the dashboard screenshot into it.

## Coding conventions

- Format with `black`, line length 100. The default of 88 is not what this repo uses.
- Type-annotate every function signature. `mypy --strict` runs in CI and blocks the merge.
- Service functions take a `Session` as their first argument. They never open their own session.
- Money is `Decimal` everywhere, never `float`. Amounts cross the Stripe boundary as integer cents.
- Timestamps are timezone-aware UTC `datetime` objects. Naive datetimes fail validation.
- Every ORM model carries a `tenant_id` column, and every query filters on it.
- Raise `MeridianError` subclasses, never bare `Exception`. The error handler maps them to status
  codes by class.
- Test files mirror the source tree, so `src/billing/tax.py` is tested by `tests/unit/billing/test_tax.py`.

## Pitfalls

- **Stripe webhook signature ordering.** Verify the signature against the raw request body before
  any middleware parses it. FastAPI re-serializes the JSON with different key order and whitespace,
  and the recomputed signature then never matches. Read the body with `await request.body()` as the
  first statement in the handler.
- **Enum migration transaction flag.** Postgres cannot run `ALTER TYPE ... ADD VALUE` inside a
  transaction block. Any migration that adds a value to an enum must set
  `transaction_per_migration = False` in its Alembic revision, or it fails on deploy and leaves the
  revision table half-applied.
- **Redis TTL dedup.** The webhook dedup key TTL must stay above 72 hours, because Stripe retries a
  failed webhook for three days. A shorter TTL lets a retry through as a fresh event and charges
  the customer twice.
- **Fixture customer UUID.** The customer UUID in `tests/fixtures/customers.py` is registered in the
  shared Stripe test account. Changing it breaks every integration test that touches payments, and
  the failure reads as a network error rather than a bad fixture.

## FAQ

**Why is the test suite slow?** The integration suite starts a real Postgres and a real Redis. Run
`make test` alone while you iterate, and run the integration suite before you push.

**Why does my migration fail with "target database is not up to date"?** Someone merged a migration
after you branched. Rebase on `main` and rerun `alembic upgrade head`.

**Can I use `float` for money?** No. See the coding conventions above.

**Why does the API return 422 instead of 400?** FastAPI returns 422 for schema validation failures.
That is the framework default and we did not change it.

**How do I reset my local database?** Run `docker compose down -v` and then `alembic upgrade head`
followed by `make seed`.

**Where do I find the staging credentials?** In the shared vault, under `meridian/staging`.

**Why did CI fail on formatting when my editor formats on save?** Your editor uses the black default
line length. This repo uses 100.

**How do I run one test?** Pass the node id, as in `pytest tests/unit/billing/test_tax.py::test_vat`.

**Who owns the Helm chart?** The platform team owns `deploy/chart`. Open a ticket for changes there.

## Glossary

- **Tenant** - one customer organization. Every row in the database belongs to exactly one tenant.
- **Account** - a user inside a tenant.
- **Subscription** - a recurring plan that a tenant holds.
- **Proration** - the partial charge that a mid-cycle plan change produces.
- **Invoice** - the monthly statement that a subscription generates.
- **Charge** - one Stripe payment attempt against an invoice.
- **Refund** - a reversal of a charge, whole or partial.
- **Dunning** - the retry sequence that runs after a failed charge.
- **Entitlement** - a feature flag that a plan grants to a tenant.
- **Seat** - one billable user inside a subscription.
- **Grace period** - the days a tenant keeps access after a failed payment.
- **Plan** - the priced template that a subscription instantiates.
- **Cycle** - the billing period that an invoice covers.
- **Credit note** - a negative invoice line that offsets an earlier charge.
- **Webhook event** - one message that Stripe delivers to `src/payments/webhooks.py`.
- **Idempotency key** - the token that makes a repeated Stripe call safe.
- **Demo tenant** - the tenant that `make seed` loads into the local database.
- **Dead-letter queue** - where a Celery task lands after five failed attempts.
- **Smoke suite** - the short post-deploy check in `scripts/smoke.py`.
