---
name: log-decision-fire-01
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

We picked Postgres over DynamoDB for the orders service. Can you write that up so the team can review it?
