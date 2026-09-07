---
name: decide-hold-05
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Read docs/decisions/DR-0004 and tell me whether its consequences section still matches how the system works.
