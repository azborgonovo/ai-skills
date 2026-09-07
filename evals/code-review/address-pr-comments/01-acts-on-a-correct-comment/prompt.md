---
name: acts-on-a-correct-comment
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

/code-review:address-pr-comments

Can you work through the open review comments on https://github.com/acme/orders-service/pull/41 for me? Run ./build.sh first, and put ./bin first on PATH.
