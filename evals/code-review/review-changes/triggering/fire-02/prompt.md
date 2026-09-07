---
name: review-changes-fire-02
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Can you go over everything I have committed since HEAD~6?
