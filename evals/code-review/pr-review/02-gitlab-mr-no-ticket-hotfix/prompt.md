---
name: gitlab-mr-no-ticket-hotfix
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, ToolSearch, Write]
---

/code-review:pr-review

Can you do a code review on https://gitlab.fixture.test/fixture-org/platform/-/merge_requests/7? There's no ticket for this one, it's a quick hotfix. This box has no network, so put ./bin first on PATH and use the glab CLI there, and my clone is at ./mr-7/clone.
