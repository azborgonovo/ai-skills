---
name: review-changes-hold-08
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Summarize what changed on this branch for the release notes. I do not need an opinion on the code.
