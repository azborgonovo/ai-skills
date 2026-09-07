---
name: pushes-back-on-a-wrong-comment
tags: [mechanics]
plugins: ["../../../../skills/code-review"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

/code-review:address-pr-comments

Please go through the review feedback on https://github.com/acme/orders-service/pull/42 and deal with it. Run ./build.sh first, and put ./bin first on PATH.
