---
name: log-decision-hold-05
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Renumber the files in docs/decisions so the sequence has no gaps.
