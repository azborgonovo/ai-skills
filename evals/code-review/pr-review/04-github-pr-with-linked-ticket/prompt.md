---
name: github-pr-with-linked-ticket
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Review this pull request: https://github.com/fixture-org/my-service/pull/123. This box has no network, so put ./bin first on PATH and use the gh CLI there, and my clone is at ./pr-123/clone.
