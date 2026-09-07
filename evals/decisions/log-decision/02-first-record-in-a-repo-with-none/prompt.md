---
name: first-record-in-a-repo-with-none
tags: [behavior]
plugins: ["../../../../skills/decisions"]
max_turns: 30
timeout_seconds: 900
allowed_tools: [Bash, Edit, Glob, Grep, Read, Skill, Write]
---

We've settled on Terraform for our infrastructure, over Pulumi and over the AWS CDK, because the ops team already reads HCL and we don't want infra to depend on a TypeScript build. Write it down properly so someone can see why in a year, and note that we accept HCL is clunky for anything with real logic. Do not stop and wait for me. Put your questions and your full answer in this one reply.
