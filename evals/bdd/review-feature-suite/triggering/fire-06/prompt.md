---
name: review-feature-suite-fire-06
tags: [triggering]
plugins: ["../../../../../skills/bdd"]
max_turns: 3
timeout_seconds: 120
allowed_tools: [Read, Glob, Grep, Skill]
---

Our Cucumber tags are a mess: @regresion, @regression, @smoke and @smoke-test are all in use. Sort out the taxonomy across the suite.
