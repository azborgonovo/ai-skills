---
name: rank-findings-by-cost-of-change
tags: [behavior]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Here is the diff for our notification client PR: notifier.diff. I already flagged the bare except and the missing test. What else should I push back on, and what actually has to be fixed before this merges?
