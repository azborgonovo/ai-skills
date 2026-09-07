---
name: no-spec-defective-diff
tags: [behavior]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Review my changes since main. There's no ticket or spec for this one — it came out of a support escalation last week. The repo is at defective-nospec.
