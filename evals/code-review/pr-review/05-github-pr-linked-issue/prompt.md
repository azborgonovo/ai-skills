---
name: github-pr-linked-issue
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Review https://github.com/fixture-org/webapp/pull/88 — it's linked to issue fixture-org/webapp#45. This box has no network, so put ./bin first on PATH and use the gh CLI there, and my clone is at ./pr-88/clone.
