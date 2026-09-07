---
name: log-decision-fire-05
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Right, we are locking in one database per customer instead of a shared schema. Two years of migrations ride on this.
