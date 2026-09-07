---
name: github-pr-comments-only-mode
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

/pr-review https://github.com/fixture-org/my-service/pull/300 comments-only — no network here, so put ./bin first on PATH for gh, and the clone is at ./pr-300/clone.
