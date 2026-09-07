---
name: review-feature-suite-hold-07
tags: [triggering]
plugins: ["../../../../../skills/bdd"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Count how many scenarios sit in features/ and print the total.
