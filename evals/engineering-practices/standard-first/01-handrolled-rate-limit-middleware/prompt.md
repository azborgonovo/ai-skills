---
name: handrolled-rate-limit-middleware
tags: [behavior]
plugins: ["../../../../skills/engineering-practices"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Our public API needs to cap each API key at 100 requests a minute. The project is in ratelimit-api. Write me a middleware that keeps a dictionary of key to request count and resets it every minute.
