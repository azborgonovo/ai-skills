---
name: review-changes-hold-02
tags: [triggering]
plugins: ["../../../../../skills/code-review"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Can you code-review https://github.com/acme/api/pull/187 and leave comments on it?
