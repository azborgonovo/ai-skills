#!/usr/bin/env bash
# Builds the three synthetic git repositories that the backfill-decisions eval
# cases mine. Git history does not survive a commit into this repository, so the
# fixtures are generated. Every commit has a fixed author, a fixed date and a
# fixed order, so two runs produce the same history.
set -euo pipefail

FIXTURES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# A stashed-away config keeps a global gitconfig, a commit template, a hooks path
# or a signing key out of the generated history.
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_CONFIG_SYSTEM=/dev/null

AUTHOR_NAME="Jamie Rivera"
AUTHOR_EMAIL="jamie.rivera@example.com"

new_repo() {
  rm -rf "$FIXTURES/$1"
  mkdir -p "$FIXTURES/$1"
  cd "$FIXTURES/$1"
  git init -q -b main
  git config user.name "$AUTHOR_NAME"
  git config user.email "$AUTHOR_EMAIL"
}

# snap <iso-date> <subject> — stages the whole tree and commits it at that date.
snap() {
  local date="$1" subject="$2"
  git add -A
  GIT_AUTHOR_NAME="$AUTHOR_NAME" GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" \
  GIT_COMMITTER_NAME="$AUTHOR_NAME" GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL" \
  GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date" \
  git commit -q -m "$subject"
}

manifest() {
  # manifest <name> <dep:version>...
  local name="$1"; shift
  {
    printf '{\n  "name": "%s",\n  "version": "1.0.0",\n  "dependencies": {\n' "$name"
    local first=1 entry
    for entry in "$@"; do
      [ $first -eq 1 ] || printf ',\n'
      first=0
      printf '    "%s": "%s"' "${entry%%:*}" "${entry##*:}"
    done
    printf '\n  }\n}\n'
  } > package.json
}

# --------------------------------------------------------------------------
# planted-repo — four planted decisions and four noise commits, 2022 to 2024.
# --------------------------------------------------------------------------
new_repo planted-repo

mkdir -p src
manifest orders-service express:4.17.1 sqlite3:5.0.2 lodash:4.17.15
cat > README.md <<'EOF'
# orders-service

HTTP API for cusomter orders.
EOF
cat > src/server.js <<'EOF'
const express = require('express');
const app = express();
app.get('/orders', (req, res) => res.json([]));
module.exports = app;
EOF
mkdir -p src/db
cat > src/db/store.js <<'EOF'
const sqlite3 = require('sqlite3');
const db = new sqlite3.Database('./orders.db');
module.exports = db;
EOF
snap "2022-01-10T09:00:00+00:00" "chore: initial commit"

cat > src/signup.js <<'EOF'
module.exports = function signup(req, res) {
  res.status(201).json({ id: 1 });
};
EOF
snap "2022-02-14T11:20:00+00:00" "feat: added a signup endpoint for self-service accounts"

mkdir -p src/queue
manifest orders-service express:4.17.1 sqlite3:5.0.2 lodash:4.17.15 amqplib:0.8.0
cat > src/queue/rabbitmq.js <<'EOF'
const amqp = require('amqplib');

async function publish(queue, payload) {
  const conn = await amqp.connect(process.env.RABBITMQ_URL);
  const ch = await conn.createChannel();
  await ch.assertQueue(queue, { durable: true });
  ch.sendToQueue(queue, Buffer.from(JSON.stringify(payload)));
}

module.exports = { publish };
EOF
snap "2022-03-08T10:15:00+00:00" "feat: adopted RabbitMQ so order dispatch survives a restart"

manifest orders-service express:4.17.1 sqlite3:5.0.2 lodash:4.17.21 amqplib:0.8.0
snap "2022-04-05T08:05:00+00:00" "chore: bumped lodash to 4.17.21"

cat > Dockerfile <<'EOF'
FROM node:16-alpine
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY . .
CMD ["node", "src/server.js"]
EOF
cat > docker-compose.yml <<'EOF'
services:
  api:
    build: .
    ports: ["3000:3000"]
  rabbitmq:
    image: rabbitmq:3-management
EOF
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'EOF'
name: ci
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: npm install
      - run: npm test
EOF
snap "2022-06-21T14:40:00+00:00" "feat: introduced Docker and GitHub Actions so every environment builds the same image"

cat > .eslintrc.json <<'EOF'
{ "extends": "eslint:recommended", "env": { "node": true } }
EOF
snap "2022-08-02T16:10:00+00:00" "style: fixed the lint errors that the new rule set reported"

AUTHOR_NAME="Priya Nair" AUTHOR_EMAIL="priya.nair@example.com"
manifest orders-service express:4.17.1 pg:8.8.0 lodash:4.17.21 amqplib:0.8.0
cat > src/db/store.js <<'EOF'
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
module.exports = pool;
EOF
cat > docker-compose.yml <<'EOF'
services:
  api:
    build: .
    ports: ["3000:3000"]
  rabbitmq:
    image: rabbitmq:3-management
  postgres:
    image: postgres:14
EOF
mkdir -p migrations
cat > migrations/0001_orders.sql <<'EOF'
CREATE TABLE orders (id SERIAL PRIMARY KEY, customer TEXT NOT NULL);
EOF
snap "2023-02-13T09:30:00+00:00" "feat: migrated persistence from SQLite to PostgreSQL to allow concurrent writes"
AUTHOR_NAME="Jamie Rivera" AUTHOR_EMAIL="jamie.rivera@example.com"

cat > README.md <<'EOF'
# orders-service

HTTP API for customer orders.
EOF
snap "2023-03-01T12:00:00+00:00" "docs: fixed a typo in the readme"

cat > src/webhooks.js <<'EOF'
async function deliver(url, body, attempts = 5) {
  for (let i = 0; i < attempts; i += 1) {
    try { return await post(url, body); } catch (err) { await wait(2 ** i * 100); }
  }
  throw new Error('delivery failed');
}
module.exports = { deliver };
EOF
snap "2023-09-12T15:25:00+00:00" "fix: corrected the retry backoff on webhook delivery"

manifest orders-service express:4.17.1 pg:8.8.0 lodash:4.17.21 @aws-sdk/client-sqs:3.400.0
rm src/queue/rabbitmq.js
cat > src/queue/sqs.js <<'EOF'
const { SQSClient, SendMessageCommand } = require('@aws-sdk/client-sqs');
const client = new SQSClient({});

async function publish(queueUrl, payload) {
  await client.send(new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(payload),
  }));
}

module.exports = { publish };
EOF
cat > docker-compose.yml <<'EOF'
services:
  api:
    build: .
    ports: ["3000:3000"]
  postgres:
    image: postgres:14
EOF
snap "2024-04-16T10:05:00+00:00" "feat: replaced RabbitMQ with Amazon SQS to drop the self-hosted broker"

# --------------------------------------------------------------------------
# madr-repo — an adr/ directory in MADR style, one documented decision and one
# undocumented Docker adoption on 2022-03-22.
# --------------------------------------------------------------------------
new_repo madr-repo

mkdir -p src
manifest billing-api express:4.17.1 sqlite3:5.0.2 lodash:4.17.15
cat > README.md <<'EOF'
# billing-api

Invoicing and payment API.
EOF
cat > src/index.js <<'EOF'
const express = require('express');
const app = express();
module.exports = app;
EOF
snap "2021-11-02T09:00:00+00:00" "chore: initial commit"

mkdir -p adr
cat > adr/0001-layered-architecture.md <<'EOF'
# 1. Layered architecture

Date: 2021-11-20

## Status

Accepted

## Context

The API mixed HTTP handling, business rules and SQL in one module, so a change to
one concern broke the others.

## Decision

Split the code into an HTTP layer, a service layer and a repository layer.

## Consequences

Each layer is testable on its own. A trivial read now crosses three files.
EOF
snap "2021-11-20T13:45:00+00:00" "docs: recorded the layered architecture decision"

manifest billing-api express:4.17.1 pg:8.8.0 lodash:4.17.15
cat > src/repository.js <<'EOF'
const { Pool } = require('pg');
const pool = new Pool({ connectionString: process.env.DATABASE_URL });
module.exports = pool;
EOF
snap "2022-01-18T10:30:00+00:00" "feat: migrated persistence from SQLite to PostgreSQL to allow concurrent writes"

cat > adr/0002-use-postgresql.md <<'EOF'
# 2. Use PostgreSQL

Date: 2022-01-20

## Status

Accepted

## Context

SQLite locked the whole database file on every write, so two concurrent invoice
runs blocked each other.

## Decision

Move persistence to PostgreSQL.

## Consequences

Concurrent writes work. The team now runs a database server in every environment.
EOF
snap "2022-01-20T09:15:00+00:00" "docs: recorded the PostgreSQL decision"

manifest billing-api express:4.17.1 pg:8.8.0 lodash:4.17.21
snap "2022-02-08T11:00:00+00:00" "chore: bumped lodash to 4.17.21"

cat > Dockerfile <<'EOF'
FROM node:16-alpine
WORKDIR /app
COPY package.json .
RUN npm install --production
COPY . .
CMD ["node", "src/index.js"]
EOF
cat > docker-compose.yml <<'EOF'
services:
  api:
    build: .
  postgres:
    image: postgres:14
EOF
snap "2022-03-22T14:20:00+00:00" "feat: introduced Docker and compose so every environment runs the same image"

cat > src/pagination.js <<'EOF'
module.exports = function page(items, size, index) {
  return items.slice(index * size, index * size + size);
};
EOF
snap "2022-04-11T16:05:00+00:00" "fix: corrected the off-by-one in invoice pagination"

# --------------------------------------------------------------------------
# skills-repo — resembles a real tooling repository. It already holds decision
# records under docs/decisions/, and it carries the submodule-to-auto-clone
# reversal that case 2 must find.
# --------------------------------------------------------------------------
new_repo skills-repo

mkdir -p skills/review
cat > README.md <<'EOF'
# agent-skills

Skills and rules for coding agnets.
EOF
cat > .gitignore <<'EOF'
node_modules/
*-workspace/
EOF
cat > skills/review/SKILL.md <<'EOF'
---
name: review
description: Reviews a diff against the review checklist.
---

# Review

Read the diff, then report the findings by severity.
EOF
snap "2023-05-04T09:00:00+00:00" "chore: initial commit"

cat > .gitmodules <<'EOF'
[submodule "external/community-skills"]
	path = external/community-skills
	url = https://example.com/community-skills.git
EOF
mkdir -p external
cat > external/README.md <<'EOF'
Skills from other authors live here as git submodules, pinned to one revision.
EOF
snap "2023-06-15T11:10:00+00:00" "feat: vendored external skills as git submodules to pin their revisions"

mkdir -p docs/decisions
cat > docs/decisions/DR-0001-one-plugin-per-domain.md <<'EOF'
# DR-0001 — One plugin per domain

- Status: adopted
- Date: 2023-07-02
- Deciders: Jamie Rivera

## Context and Problem Statement

A single plugin held every skill, so a user who wanted one skill installed all of
them.

## Decision

Ship one plugin per domain, and keep every skill of that domain inside it.

## Consequences

A user installs only what they need. A shared helper cannot cross a plugin edge.
EOF
snap "2023-07-02T10:00:00+00:00" "docs: recorded the one-plugin-per-domain decision"

cat > external/README.md <<'EOF'
Skills from other authors live here as git submodules, pinned to one revision.
Run `git submodule update --init` after a clone.
EOF
snap "2023-09-19T15:30:00+00:00" "chore: bumped the pinned submodule revisions"

cat > README.md <<'EOF'
# agent-skills

Skills and rules for coding agents.
EOF
snap "2024-02-27T08:45:00+00:00" "docs: fixed a typo in the readme"

rm .gitmodules
rm -rf external
mkdir -p scripts
cat > scripts/clone_external_skills.sh <<'EOF'
#!/usr/bin/env bash
# Clones each external skill repository next to this one, so a fresh clone needs
# no submodule init and the external history stays out of this repository.
set -euo pipefail
SIBLINGS="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
for repo in community-skills partner-skills; do
  [ -d "$SIBLINGS/$repo" ] || git clone "https://example.com/$repo.git" "$SIBLINGS/$repo"
done
EOF
chmod +x scripts/clone_external_skills.sh
cat > README.md <<'EOF'
# agent-skills

Skills and rules for coding agents.

External skills are cloned as sibling repositories. Run
`scripts/clone_external_skills.sh` once after a clone.
EOF
snap "2024-03-11T12:25:00+00:00" "feat: replaced git submodules with an auto-cloned sibling checkout so a fresh clone needs no submodule init"

cat > .github-linter.json <<'EOF'
{ "markdownlint": "0.33.0" }
EOF
snap "2024-05-08T09:50:00+00:00" "chore: pinned the markdownlint version"

cd "$FIXTURES"
for repo in planted-repo madr-repo skills-repo; do
  printf '%s: %s commits\n' "$repo" "$(git -C "$repo" rev-list --count HEAD)"
done
