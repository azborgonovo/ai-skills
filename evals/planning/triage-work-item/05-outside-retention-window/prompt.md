---
name: outside-retention-window
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Triage https://fixtures.atlassian.net/browse/TRIAGE-105 — a customer reported this during the outage back in February. Code is at exports-app. This box has no network: `twg` and `aws` are stubs in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker or CloudWatch command. Save a copy of the comment to triage-comment.md.
