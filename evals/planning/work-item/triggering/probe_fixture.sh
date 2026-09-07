#!/usr/bin/env bash
# The probes of this skill describe work on named services, so the directory
# carries those services and a note of what refinement agreed.
set -euo pipefail

mkdir -p services/notifications services/search services/exports docs

cat > README.md <<'EOF'
# Acme platform

Services: notifications, search, exports.
EOF

cat > services/notifications/README.md <<'EOF'
# Notifications

Consumes Google Pub/Sub today. The migration to SQS is agreed and not started.
EOF

cat > services/search/README.md <<'EOF'
# Search

Backs the admin portal search box.
EOF

cat > services/exports/README.md <<'EOF'
# Exports

Builds CSV exports for the reporting tab.
EOF

cat > docs/refinement-notes.md <<'EOF'
# Refinement notes

The queue migration is split per service rather than done in one change. Each
service moves off Pub/Sub on its own, behind its own flag.

Services still to move: notifications, search, exports.
EOF
