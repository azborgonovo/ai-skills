---
name: log-decision-fire-07
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Fine, decision made: we drop the GraphQL gateway and go REST-only across every service.
