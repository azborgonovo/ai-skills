---
name: stale-checkout-supersede
tags: [behavior]
plugins: ["../../../../skills/planning"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

Did you `git pull` stale-repo/app before investigating https://fixtures.atlassian.net/browse/TRIAGE-108? If not please do, investigate it again, and post your findings again. This box has no network: the only Jira CLI is the stub in bin, so run `export PATH=$PWD/bin:$PATH` before any tracker command. Save a copy of the comment to triage-comment.md.
