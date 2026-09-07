---
name: bug-report-missing-reproduction-steps
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Read support-thread.md and log a bug for it in GitHub, using the sandbox CLI at bin/gh — put bin first on PATH so nothing reaches the real tracker.
