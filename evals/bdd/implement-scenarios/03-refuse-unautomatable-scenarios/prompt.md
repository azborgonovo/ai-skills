---
name: refuse-unautomatable-scenarios
tags: [behavior]
plugins: ["../../../../skills/bdd"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Can you turn the scenarios in booking-app/features/room-booking.feature into Go tests? The package sits in booking-app. Do as much as you can in one pass, and do not stop to check with me.
