---
name: triage-work-item-hold-07
tags: [triggering]
plugins: ["../../../../../skills/planning"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

List the open issues in github.com/acme/checkout-api that carry the bug label.
