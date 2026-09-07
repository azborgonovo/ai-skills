---
name: cross-doc-contradiction
tags: [behavior]
plugins: ["../../../../skills/agent-docs"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

our AI coding tools keep behaving differently depending on which one runs on this repo -- can you check our CLAUDE.md, AGENTS.md, and cursor rules and make them consistent? the repo is at cross-doc-contradiction/ and its root has CLAUDE.md, AGENTS.md, and .cursor/rules/testing.mdc
