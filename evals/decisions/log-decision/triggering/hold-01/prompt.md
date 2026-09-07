---
name: log-decision-hold-01
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

I cannot make up my mind between Kafka and SQS for the new pipeline. Help me think it through.
