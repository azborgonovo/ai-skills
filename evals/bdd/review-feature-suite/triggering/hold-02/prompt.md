---
name: review-feature-suite-hold-02
tags: [triggering]
plugins: ["../../../../../skills/bdd"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

This one feature file leaks CSS selectors into its steps. Clean it up.
