---
name: review-changes-fire-06
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Diff my feature branch against develop and flag anything that blocks a merge.
