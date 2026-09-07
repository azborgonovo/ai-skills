---
name: log-decision-fire-02
tags: [triggering]
plugins: ["../../../../../skills/decisions"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Write up an architecture decision record for our choice of Terraform over Pulumi.
