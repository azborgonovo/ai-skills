---
name: review-changes-fire-08
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Take a look at what I have changed since branching off main and sort it into what blocks a merge and what does not.
