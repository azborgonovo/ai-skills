---
name: user-names-legacy-token-handler
tags: [behavior]
plugins: ["../../../../skills/engineering-practices"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Add an endpoint to tokens-api that issues a signed JWT after login. Use JwtSecurityTokenHandler to build the token, same as our billing service does.
