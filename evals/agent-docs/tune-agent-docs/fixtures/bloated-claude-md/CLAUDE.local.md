# CLAUDE.local.md

Local notes for my machine. Not checked in on other people's machines.

## Build and test commands

- `make install` installs the Python dependencies into `.venv`.
- `make build` compiles the protobuf stubs and builds the Docker image.
- `make test` runs the unit suite with `pytest -q`.
- `make test-integration` runs the integration suite against the docker-compose stack.
- `make lint` runs `ruff check .` and `black --check .`.
- `make seed` loads the demo tenant into the local Postgres.

## My local setup

- Postgres listens on 5433 here, so `DATABASE_URL` in my `.env` uses that port.
- I run the worker with `celery -A src.worker worker -l debug` in a second terminal.
