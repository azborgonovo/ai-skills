---
name: cloudwatch-current-incident
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Triage https://fixtures.atlassian.net/browse/TRIAGE-104 — the error rate on /api/exports is still climbing right now, so check CloudWatch to confirm before you post. Code is at exports-app. This box has no network: `twg` and `aws` are stubs in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker or CloudWatch command. Save a copy of the comment to triage-comment.md.
