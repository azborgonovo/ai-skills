---
name: bespoke-check-digit-stays-custom
tags: [behavior]
plugins: ["../../../../skills/engineering-practices"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

In warehouse-go, add a validator for our pallet licence plates, with unit tests. They are 11 characters: 10 digits plus a check digit, which is the weighted sum of the digits times their 1-based position, mod 11, written as X when it comes out as 10.
