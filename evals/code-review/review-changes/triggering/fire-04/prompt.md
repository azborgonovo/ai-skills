---
name: review-changes-fire-04
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Review since the v3.2 tag and tell me whether it is safe to merge.
