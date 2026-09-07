---
name: review-feature-suite-hold-06
tags: [triggering]
plugins: ["../../../../../skills/bdd"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Our unit tests repeat the same assertions in 400 places. De-duplicate them.
