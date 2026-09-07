---
name: tune-agent-docs-hold-02
tags: [triggering]
plugins: ["../../../../../skills/agent-docs"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

My release-notes skill never triggers. Look at its SKILL.md and tell me why.
