# CLAUDE.md

Conventions for the Meridian billing service.

## Conventions

- Format every Python file with `black`, line length 100.
- Run the full suite with `pytest -q` before opening a pull request.
- Write every commit message as a Conventional Commit, in the shape `type(scope): subject`.
- Every database migration must be reversible, so always write the down step.
- Money is `Decimal`, never `float`. Amounts cross the Stripe boundary as integer cents.
