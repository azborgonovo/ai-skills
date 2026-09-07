---
name: log-decision-hold-04
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Go back through the last two years of git history and write records for the architecture decisions nobody documented.
