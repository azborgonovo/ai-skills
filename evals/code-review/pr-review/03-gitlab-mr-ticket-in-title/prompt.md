---
name: gitlab-mr-ticket-in-title
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Please review https://gitlab.fixture.test/fixture-org/backend/-/merge_requests/201 — the ticket is GH-4521 in the MR title. This box has no network, so put ./bin first on PATH and use the glab and twg CLIs there, and my clone is at ./mr-201/clone.
