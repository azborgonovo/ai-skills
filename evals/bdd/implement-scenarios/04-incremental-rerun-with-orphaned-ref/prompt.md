---
name: incremental-rerun-with-orphaned-ref
tags: [behavior]
plugins: ["../../../../skills/bdd"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Some of billing-app/features/invoicing.feature already has tests and some of it does not. Can you work out what is missing there and wire that part up? Do it in one pass, and do not stop to check with me.
