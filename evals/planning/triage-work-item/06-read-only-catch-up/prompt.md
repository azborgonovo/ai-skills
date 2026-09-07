---
name: read-only-catch-up
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Give me a quick summary of what https://fixtures.atlassian.net/browse/TRIAGE-101 is about and where it stands — I just need to catch up before standup. This box has no network: the only Jira CLI is the stub in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker command.
