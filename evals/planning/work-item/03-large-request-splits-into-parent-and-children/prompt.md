---
name: large-request-splits-into-parent-and-children
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

We're moving every service off the shared Postgres instance onto its own database — billing, reporting and notifications each cut over and get verified separately. Write this up for me, but don't create anything in the tracker yet.
