---
name: code-review-pyramid-hold-07
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Set up ESLint and a pre-commit hook in this repo so we stop nitpicking formatting in reviews.
