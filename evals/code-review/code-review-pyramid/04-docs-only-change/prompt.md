---
name: docs-only-change
tags: [behavior]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Someone opened a PR that only touches the README. The diff is docs-change.diff and the code it describes is in retry_config.py. Do I need to do a full review on this, or can I just merge it?
