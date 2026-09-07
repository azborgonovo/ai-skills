---
name: review-changes-fire-05
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Give me a verdict on this branch. Is it good to go, or does it need changes?
