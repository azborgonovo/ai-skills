---
name: standard-first
description: >
  Guides technical implementation to always prefer the standard, officially-documented solution over custom or AI-generated code. Use this skill whenever the agent is about to: write new code for a feature, suggest or add a library/package, scaffold a new project, configure a framework, or solve a problem that a built-in framework feature or package might already handle. TRIGGER for any .NET/C#, Node.js/npm, Python, Go, Java, or other language implementation task — especially when the problem sounds like something a built-in framework feature or package registry might already solve (logging enrichment, auth, serialization, retries, health checks, migrations, etc.). Before writing any custom code, check for a technology-specific skill (e.g. dotnet-agent-skills), then fall back to official web docs and package registries. Do not skip this skill just because the answer feels obvious from training data.
argument-hint: "[task description]"
allowed-tools: [WebSearch, WebFetch, Read, Glob, Grep, Edit, Write, Bash]
---

# Standard-First Skill

Before implementing anything, find what already exists — a built-in framework feature, a
well-maintained package, or an official pattern. The simplest solution that fully solves the stated
problem is the right one; do not add custom implementations for problems that an existing package
already covers.

---

## Step 1 — Understand the Stack

Before searching for solutions, read the project's dependency and configuration files to identify
the exact technology stack and what is already installed.

Use `Glob` to find these files, then `Read` them:

| File | What it tells you |
|---|---|
| `*.csproj`, `*.sln`, `global.json` | .NET version, existing NuGet packages |
| `package.json`, `package-lock.json`, `yarn.lock` | Node.js runtime, installed packages |
| `go.mod` | Go module path and dependencies |
| `requirements.txt`, `pyproject.toml`, `Pipfile` | Python packages |
| `pom.xml`, `build.gradle` | Java/Kotlin dependencies |
| `Cargo.toml` | Rust crates |

Reading these files prevents mismatches — e.g., looking up ASP.NET Core 9 docs when the project
targets .NET 6, or suggesting a package that is already installed under a different name.

If no project files are found, ask the user for the tech stack before proceeding.

---

## Step 2 — Check for a Technology-Specific Skill

Before going to the web, check whether a skill is already available for the detected technology.
Look at the `available_skills` list in your context and match against the stack identified in
Step 1.

Examples of what to look for:

| Stack | Skill to look for |
|---|---|
| .NET / C# / ASP.NET Core | `dotnet-agent-skills`, `dotnet`, `csharp` |
| Node.js / npm | `node`, `nodejs`, `javascript` |
| Python | `python`, `django`, `fastapi` |
| Go | `go`, `golang` |
| Java / Kotlin | `java`, `spring` |
| Docker / Kubernetes | `docker`, `kubernetes`, `k8s` |

If a matching skill is available, invoke it and follow its guidance. A dedicated skill has
curated, up-to-date knowledge for that ecosystem and should be preferred over a web
search. Skip Step 3 entirely if the skill covers the task.

If no matching skill is found, continue to Step 3.

---

## Step 3 — Search Before Implementing

For every implementation task, search official sources before writing any code.

### 3a. Check if a package already solves it

The first question is always: does this already exist? Search the relevant package registry:

| Technology | Registry to search |
|---|---|
| .NET / C# | `nuget.org` |
| Node.js | `npmjs.com` |
| Python | `pypi.org` |
| Go | `pkg.go.dev` |
| Java / Kotlin | Maven Central (`mvnrepository.com`) |
| Rust | `crates.io` |

Use `WebSearch` with a query like: `[problem description] nuget` or `serilog log masking nuget`.

A well-maintained package (actively updated, thousands of downloads, clear docs) is almost always
preferable to custom code. It gets security patches, bug fixes, and compatibility updates
automatically.

**Examples of packages that replace custom code:**

- Masking sensitive values in Serilog logs → `Serilog.Enrichers.Sensitive` (not a custom
  `IDestructuringPolicy`)
- Retry logic in HTTP calls → `Polly` (not a hand-rolled retry loop)
- Strongly-typed configuration in ASP.NET Core → built-in `IOptions<T>` (not manual config reads)
- Health checks → built-in `Microsoft.AspNetCore.Diagnostics.HealthChecks` (not a custom endpoint)

### 3b. Fetch and read the official documentation

Once a candidate package or framework feature is identified, use `WebFetch` to retrieve its
official documentation page. Do not rely on training data alone — fetch the current docs.

Prioritise these sources by technology:

| Technology | Primary official source |
|---|---|
| .NET / C# | `learn.microsoft.com/en-us/dotnet/` |
| ASP.NET Core | `learn.microsoft.com/en-us/aspnet/core/` |
| NuGet packages | `nuget.org/packages/[name]` → then follow the package's own docs link |
| Node.js | `nodejs.org/en/docs/` |
| npm packages | The package README on `npmjs.com`, then its own docs site |
| Python stdlib | `docs.python.org/3/library/` |
| Go stdlib | `pkg.go.dev/[module]` |
| Docker | `docs.docker.com` |
| Kubernetes | `kubernetes.io/docs/` |

Read the section relevant to the task. Also look for sections titled "Best practices",
"Recommendations", "Security considerations", "Performance", or "Production guidance" — these are
distinct from the getting-started example and often contain configuration options, ordering
constraints, or caveats that the minimal snippet omits but that matter in real applications.

If the docs recommend a specific registration order, configuration pattern, or combination of
options for the use case at hand, follow that recommendation — not just the minimal snippet.

### 3c. For new project scaffolding

When creating a project from scratch, find and follow the official "Getting Started" guide for the
chosen framework. Do not generate boilerplate from memory — fetch the actual current guide.

Search for: `[framework name] getting started official documentation site:[official-domain]`

Follow the guide's structure, naming conventions, and project layout exactly as shown. The official
guide reflects the current recommended approach and avoids patterns that may have been superseded.

---

## Step 4 — Choose the Simplest Solution

After searching, apply Occam's Razor: prefer the solution with the fewest moving parts that fully
solves the stated problem.

**Decision hierarchy:**
1. **Built-in framework feature** — zero extra dependencies; always prefer if it covers the need
2. **Official or well-maintained package** — prefer over custom code if it cleanly solves it
3. **Custom code** — only when no package or built-in handles the problem adequately

---

## Step 5 — Implement

Implement the solution following the patterns and recommendations from the official docs — not
general patterns from training data. If the official docs specify a configuration structure,
registration order, method signature, or best-practice note, follow it.

"Simplest" means fewest invented parts, not ignoring official guidance. A solution that follows
official best practices is simpler in the long run: it avoids the need to rediscover common
pitfalls that the docs already document.

Every solution must include:

1. **The installation command** — `dotnet add package`, `npm install`, `pip install`, etc.
2. **Working code that follows official recommendations** — the minimal code needed, structured
   according to the official best-practice pattern (not just a copy of the getting-started snippet)
3. **A note on any best-practice deviations** — if the project's existing code diverges from an
   official recommendation, call it out rather than silently matching the deviation

Keep the implementation concise. Show the minimum necessary to solve the problem correctly, not a
comprehensive tutorial.

---

## Principles

- **Skills beat web searches.** A technology-specific skill has curated knowledge for that
  ecosystem. Check `available_skills` before searching the web.
- **Search beats recall.** Official docs change and package APIs evolve. Fetching the current doc
  is more reliable than training data.
