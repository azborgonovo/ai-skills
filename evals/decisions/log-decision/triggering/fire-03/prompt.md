---
name: log-decision-fire-03
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Document why we moved the background jobs to SQS, including why we rejected RabbitMQ.
