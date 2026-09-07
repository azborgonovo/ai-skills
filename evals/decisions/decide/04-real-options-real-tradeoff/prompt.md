---
name: real-options-real-tradeoff
tags: [behavior]
plugins: ["../../../../skills/decisions"]
max_turns: 6
timeout_seconds: 300
allowed_tools: [Read, Glob, Grep, Skill]
---

Our checkout calls a third-party tax API on every request. It is now our slowest dependency and our biggest single point of failure. I see two options: cache the responses for 24 hours, or build our own rate table for the five countries we sell in. I am leaning toward building our own. Push on this with me before I commit. Do not stop and wait for me. Put your questions and your full answer in this one reply.
