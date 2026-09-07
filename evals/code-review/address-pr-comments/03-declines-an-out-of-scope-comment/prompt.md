---
name: declines-an-out-of-scope-comment
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

/code-review:address-pr-comments

There is a review comment waiting on https://github.com/acme/orders-service/pull/43 — could you handle it? Run ./build.sh first, and put ./bin first on PATH.
