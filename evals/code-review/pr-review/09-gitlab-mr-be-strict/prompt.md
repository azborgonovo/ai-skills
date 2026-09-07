---
name: gitlab-mr-be-strict
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Review https://gitlab.fixture.test/fixture-org/backend/-/merge_requests/410 — I think it's broken, be strict. This box has no network, so put ./bin first on PATH and use the glab and twg CLIs there, and my clone is at ./mr-410/clone.
