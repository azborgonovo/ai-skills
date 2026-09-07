---
name: tune-agent-docs-fire-04
tags: [triggering]
plugins: ["../../../../../skills/agent-docs"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Every session burns a few thousand tokens on our steering docs before any real work starts. Can we trim that?
