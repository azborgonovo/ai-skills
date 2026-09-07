---
name: local-logger-helper-deviation
tags: [behavior]
plugins: ["../../../../skills/engineering-practices"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Add request-id logging to a new orders route in orders-api, the same way orders-api/src/routes/payments.ts does it.
