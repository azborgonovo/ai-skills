---
name: match-the-house-style
tags: [behavior]
plugins: ["../../../../skills/decisions"]
max_turns: 25
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

We just agreed to move session storage out of Postgres into Redis, over sticky sessions on the load balancer and over a dedicated session table, because logins then survive a deploy and we accept running one more thing in production. Write it up alongside the records in docs/decisions/. Do not stop and wait for me. Put your questions and your full answer in this one reply.
