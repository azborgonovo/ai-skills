---
name: dry-run-with-attachment
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Investigate https://fixtures.atlassian.net/browse/TRIAGE-101 and tell me what you think is going on — don't post anything yet, I want to review it first. The code is at exports-app. This box has no network: the only Jira CLI is the stub in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker command.
