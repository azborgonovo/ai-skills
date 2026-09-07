---
name: code-review-pyramid-hold-01
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Review the diff between my branch and main and tell me what is wrong with it.
