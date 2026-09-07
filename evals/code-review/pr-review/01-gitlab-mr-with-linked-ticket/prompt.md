---
name: gitlab-mr-with-linked-ticket
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Review this MR for me: https://gitlab.fixture.test/fixture-org/my-service/-/merge_requests/42. This box has no network, so put ./bin first on PATH and use the glab and twg CLIs there, and my clone of the repo is at ./mr-42/clone.
