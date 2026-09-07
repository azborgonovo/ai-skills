---
name: bug-classification-agree
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Triage https://fixtures.atlassian.net/browse/TRIAGE-104 and post your findings. Code is at exports-app. This box has no network: the only Jira CLI is the stub in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker command. Save a copy of the comment to triage-comment.md.
