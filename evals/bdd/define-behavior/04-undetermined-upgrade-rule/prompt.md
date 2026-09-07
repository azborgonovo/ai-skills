---
name: undetermined-upgrade-rule
tags: [behavior]
plugins: ["../../../../skills/bdd"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Add a scenario to subscription-billing.feature for when a subscriber upgrades to the annual plan halfway through a paid month.
