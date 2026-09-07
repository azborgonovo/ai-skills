#!/usr/bin/env bash
# Builds the steering-document corpus that the triggering probes assume: several
# files that tell an agent what to do, long enough and inconsistent enough for
# the prompts about drift, bloat and contradiction to have something to act on.
set -euo pipefail

mkdir -p .github src/api src/worker

cat > CLAUDE.md <<'EOF'
# Project instructions

## Testing
Always run the full test suite before you commit. Use pytest.
Every new function needs a unit test. Coverage must stay above 80 percent.

## Style
Use black for formatting. Line length is 100.
Prefer explicit imports over wildcard imports.

## Commits
Write conventional commits. Use the imperative mood.

## Testing
Run pytest -x on every change. Do not commit failing tests.

## Architecture
The API lives in src/api. The worker lives in src/worker.
Never import from src/worker inside src/api.

## Dependencies
Pin every dependency. Use requirements.txt, not pyproject.toml.

## Testing
Make sure the tests pass. Use the test runner configured in the repo.

## Logging
Use structlog. Never log card numbers or email addresses.

## Database
Migrations live in migrations/. Use alembic. Never edit an applied migration.

## Review
Ask for review before merging to main.
EOF
# Pad the root file so the probe about a 600-line CLAUDE.md finds one.
for i in $(seq 1 80); do
  {
    echo ""
    echo "## Convention $i"
    echo "Follow the house pattern for area $i."
    echo "Do not invent a new pattern where one already exists."
    echo "Ask a maintainer when the pattern is unclear."
    echo "Keep changes in area $i small and reviewable."
    echo "Record any deviation in the pull request description."
  } >> CLAUDE.md
done

cat > AGENTS.md <<'EOF'
# Agent instructions

## Testing
Use unittest. Run python -m unittest discover.
Tests are optional for small changes.

## Style
Use flake8. Line length is 79.

## Commits
Any clear commit message is fine.

## Dependencies
Use pyproject.toml and poetry.
EOF

cat > .cursorrules <<'EOF'
Format with autopep8.
Line length 120.
Write tests when it makes sense.
Import style does not matter.
EOF

cat > .github/copilot-instructions.md <<'EOF'
# Copilot instructions

Prefer concise code. Skip docstrings on private helpers.
Use pytest for tests. Line length is 88.
Commit messages should describe what changed.
EOF

cat > src/api/main.py <<'EOF'
def health():
    return {"status": "ok"}
EOF

cat > src/worker/tasks.py <<'EOF'
def process(job):
    return job["id"]
EOF
