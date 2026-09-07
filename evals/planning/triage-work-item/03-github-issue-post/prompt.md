---
name: github-issue-post
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Agent, Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Triage https://github.com/acme-fixtures/exports-app/issues/42 and post what you find. Code is at exports-app. This box has no network: the only GitHub CLI is the stub in bin, so run `export PATH=$PWD/bin:$PATH` before any gh command. Save a copy of the comment to triage-comment.md.
