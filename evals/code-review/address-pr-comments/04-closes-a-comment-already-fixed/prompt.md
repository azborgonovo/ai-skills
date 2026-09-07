---
name: closes-a-comment-already-fixed
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

/code-review:address-pr-comments

Sort out the open review comment on https://github.com/acme/orders-service/pull/44 please. Run ./build.sh first, and put ./bin first on PATH.
