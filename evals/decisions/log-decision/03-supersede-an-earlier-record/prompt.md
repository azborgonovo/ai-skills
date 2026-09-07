---
name: supersede-an-earlier-record
tags: [behavior]
plugins: ["../../../../skills/decisions"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

The public API is moving off FastAPI onto Litestar, because we keep working around its dependency injection and Litestar gives us real DI plus msgspec serialisation, at the cost of a smaller ecosystem and a rewrite of the routing layer. Write that up in docs/decisions/, and make sure that folder doesn't still read like FastAPI is the plan. Do not stop and wait for me. Put your questions and your full answer in this one reply.
