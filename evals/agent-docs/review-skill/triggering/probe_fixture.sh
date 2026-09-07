#!/usr/bin/env bash
# Builds the skills tree that the triggering probes assume. The probes name
# specific paths and specific skills, so those have to exist and have to carry
# the weaknesses the prompts describe.
set -euo pipefail

mkdir -p skills/deploy-preview skills/release-notes skills/terraform-modules \
         skills/changelog skills/db-migrations skills/code-review skills/on-call-runbook

cat > skills/deploy-preview/SKILL.md <<'EOF'
---
name: deploy-preview
description: Deploys a preview environment.
---

# Deploy preview

Run the deploy.

## Steps

1. Build the image.
2. Push it.
3. Deploy it.
4. Post the URL.
EOF

cat > skills/release-notes/SKILL.md <<'EOF'
---
name: release-notes
description: Writes release notes from the git history between two tags, grouping entries by conventional-commit type and calling out breaking changes.
---

# Release notes

Read the commits between the two tags. Group them by type. Write the notes.

## Grouping

Put every `feat` under Added. Put every `fix` under Fixed. Put a commit with a
`BREAKING CHANGE` footer under Breaking, at the top.

## Output

Write the notes to CHANGELOG.md, newest release first.
EOF

cat > skills/terraform-modules/SKILL.md <<'EOF'
---
name: terraform-modules
description: helps with terraform
---

# Terraform modules

You should probably use modules. Modules are good. When writing terraform, it is
generally a good idea to think about reuse, and you might want to consider
extracting things. Variables should be typed, usually.

Maybe run terraform fmt. Or terraform validate. It depends.

TODO: add examples here.
EOF

cat > skills/changelog/SKILL.md <<'EOF'
---
name: changelog
description: Changelog helper.
---

# Changelog

Update the changelog file.
EOF

# A long file, so the probe about 400 lines of filler finds one.
{
  cat <<'EOF'
---
name: db-migrations
description: Handles database migrations for the service, covering creation, review, application and rollback of schema changes.
---

# Database migrations

This skill helps with migrations.
EOF
  for i in $(seq 1 80); do
    echo ""
    echo "## Consideration $i"
    echo ""
    echo "It is worth noting that migrations are a crucial part of any robust"
    echo "database workflow. You should always carefully consider the impact."
    echo "This is a pivotal step that must not be underestimated in any way."
  done
} > skills/db-migrations/SKILL.md

cat > skills/code-review/SKILL.md <<'EOF'
---
name: code-review
description: Reviews code changes and reports findings.
---

# Code review

Look at the diff. Find problems. Report them.

## What to look at

Look at correctness. Also look at style. Also performance. Also security. Also
naming. Also tests. Also documentation. Also architecture. Also dependencies.

## Output

Write the findings somewhere useful.
EOF

cat > skills/on-call-runbook/SKILL.md <<'EOF'
---
name: on-call-runbook
description: Guides an on-call engineer through triage of a production alert, from first acknowledgement to handover.
---

# On-call runbook

Acknowledge the alert. Find the blast radius. Mitigate first, diagnose second.

## Acknowledge

Claim the alert in the pager so that a second responder does not duplicate work.

## Mitigate

Roll back the most recent deploy where the alert started inside its window.

## Hand over

Write what you saw, what you changed, and what is still open.
EOF
