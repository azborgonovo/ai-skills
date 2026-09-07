---
name: log-decision-hold-06
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Mark DR-0002 as superseded by DR-0007 and update the cross-links between them.
