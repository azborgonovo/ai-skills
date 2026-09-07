---
name: triage-work-item-fire-06
tags: [triggering]
plugins: ["../../../../../skills/planning"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Before standup I need to know whether github.com/acme/web/issues/1204 is a real bug or the intended behaviour. Check the code and say so on the issue.
