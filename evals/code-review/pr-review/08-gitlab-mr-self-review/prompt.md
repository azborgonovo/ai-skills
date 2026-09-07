---
name: gitlab-mr-self-review
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Review my own MR before I ask the team: https://gitlab.fixture.test/fixture-org/my-service/-/merge_requests/61. This box has no network, so put ./bin first on PATH and use the glab and twg CLIs there, and my clone is at ./mr-61/clone.
