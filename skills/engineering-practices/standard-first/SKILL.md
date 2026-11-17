---
name: standard-first
description: >
  Guides technical implementation to always prefer the standard, officially-documented solution over
  custom or AI-generated code. Use when you are about to write new code for a feature, suggest or add
  a library or package, scaffold a new project, or configure a framework, in any language, including
  .NET and C#, Node.js and npm, Python, Go, Java, and the rest. Use it above all when the problem
  sounds like something that a built-in framework feature or a package registry already solves, such
  as logging enrichment, auth, serialization, retries, health checks, or migrations. Do not skip this
  skill because the answer feels obvious from training data.
argument-hint: "[task description]"
allowed-tools: [WebSearch, WebFetch, Read, Glob, Write, Bash]
---

# Standard-First

Before you implement anything, find what already exists: a built-in framework feature, a well-maintained package, or an official pattern.

## Step 1: Understand the stack

Use `Glob` to find the dependency manifests of the project, such as `*.csproj`, `package.json`, `go.mod`, or `pyproject.toml`. Read them, and pin the exact framework version and the installed packages. The version stops you from reading the docs of the wrong release. The package list stops you from proposing a package that the project already has. Grep a lockfile for a package name, and do not read it whole.

When you find no project files, ask the user for the tech stack before you proceed.

## Step 2: Check for a technology-specific skill

Scan the skills available in this session for one that covers the stack. When one matches, invoke it and follow it, and skip Step 3 wherever it covers the task.

## Step 3: Search before you implement

### 3a. Find the candidates

Check first whether the framework has a built-in feature for the need. Then search the package registry of the stack with `WebSearch`, and name the registry in the query, as in `serilog log masking nuget` or `[problem description] npm`. A well-maintained package is actively updated, widely downloaded, and clearly documented.

Examples of a standard solution that replaces custom code:

- For retry logic in HTTP calls, use `Polly`, and not a hand-rolled retry loop.
- For health checks in ASP.NET Core, use the built-in `Microsoft.AspNetCore.Diagnostics.HealthChecks`, and not a custom endpoint.

An existing usage in the codebase is not a standard. When the project already does it a non-standard way, the standard solution still wins.

### 3b. Read the official documentation

Fetch the current documentation of each candidate, because APIs change after training data. When a `find-docs` skill is available, invoke it. Otherwise run `npx ctx7@latest library "<name>"`, then `npx ctx7@latest docs <id> "<focused question matching the task>"`. When neither is available, use `WebFetch` on the official page.

Take the docs from the domain of the vendor, such as `learn.microsoft.com`, and not from a blog or an aggregator. For a package, follow the docs link on its registry listing.

Read the section for the task, plus any section titled "Best practices", "Recommendations", "Security considerations", "Performance", or "Production". Those sections carry the options, the ordering constraints, and the caveats that the minimal snippet omits. Follow what they recommend.

When you scaffold a new project, fetch the official "Getting Started" guide of the framework, and follow its structure, naming, and layout exactly. Do not generate the boilerplate from memory.

## Step 4: Choose the simplest solution

Prefer the solution with the fewest moving parts that fully solves the problem:

1. A built-in framework feature, which adds no dependency.
2. An official or well-maintained package.
3. Custom code. Use it only after no built-in feature and no package handles the problem adequately.

## Step 5: Implement

Implement from the official docs, and not from training-data patterns. Every solution must include three things:

1. **The installation command**, such as `dotnet add package`, `npm install`, or `pip install`, or a statement that no install is needed.
2. **Working code that follows the official recommendations**, and not a copy of the getting-started snippet.
3. **A note on any deviation from a best practice.** When the existing code of the project diverges from an official recommendation, call that out instead of matching the deviation in silence.

Show the minimum code that solves the problem correctly, and not a tutorial.
