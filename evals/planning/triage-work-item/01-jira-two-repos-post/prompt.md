---
name: jira-two-repos-post
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Agent, Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Can you triage https://fixtures.atlassian.net/browse/TRIAGE-101 and post your analysis as a comment on the issue? The two codebases behind this feature are the checkouts at exports-repo/frontend and exports-repo/backend. This box has no network: the only Jira CLI is the stub in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker command. Save a copy of the comment to triage-comment.md.
