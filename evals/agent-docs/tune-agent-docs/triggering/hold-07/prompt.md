---
name: tune-agent-docs-hold-07
tags: [triggering]
plugins: ["../../../../../skills/agent-docs"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Add a line to CLAUDE.md that says we use pnpm and never npm.
