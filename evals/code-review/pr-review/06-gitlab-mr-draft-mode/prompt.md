---
name: gitlab-mr-draft-mode
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

/pr-review https://gitlab.fixture.test/fixture-org/my-service/-/merge_requests/55 draft — no network here, so put ./bin first on PATH for glab and twg, and the clone is at ./mr-55/clone.
