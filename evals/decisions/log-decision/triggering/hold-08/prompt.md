---
name: log-decision-hold-08
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

The RabbitMQ to SQS switch is already written up in DR-0005. Check whether the code still matches what it says.
