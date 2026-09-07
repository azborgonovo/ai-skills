---
name: planted-decisions-synthetic-repo
tags: [mechanics]
plugins: ["../../../../skills/decisions"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

/decisions:backfill-decisions

The service repo in planted-repo has no ADRs — go through its git history and backfill decision records for the architecturally significant decisions. Do not stop and wait for me. Put your questions and your full answer in this one reply.
