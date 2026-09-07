---
name: madr-dedup-and-naming
tags: [mechanics]
plugins: ["../../../../skills/decisions"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

/decisions:backfill-decisions

Reconstruct decision records from the git history of madr-repo for any significant decisions we never documented. Do not stop and wait for me. Put your questions and your full answer in this one reply.
