#!/usr/bin/env bash
# The probes of this skill span .NET, Go, Express, Python and Java, so the
# directory carries one small service per stack. Without them the model asks
# which project is meant instead of reaching for the skill.
set -euo pipefail

mkdir -p services/api services/ingestion services/notifications services/reporting

cat > services/api/Api.csproj <<'EOF'
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
EOF

cat > services/api/Program.cs <<'EOF'
var builder = WebApplication.CreateBuilder(args);
builder.Services.AddHttpClient("payments", c =>
{
    c.BaseAddress = new Uri("https://payments.internal/");
});

var app = builder.Build();
app.MapGet("/orders/{id}", (string id) => Results.Ok(new { id }));
app.Run();
EOF

cat > services/notifications/package.json <<'EOF'
{
  "name": "notifications",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "express": "^4.19.2"
  }
}
EOF

cat > services/notifications/index.js <<'EOF'
const express = require("express");

const app = express();

app.get("/notifications/:id", (req, res) => {
  res.json({ id: req.params.id });
});

app.listen(3000);
EOF

cat > services/ingestion/pyproject.toml <<'EOF'
[project]
name = "ingestion"
version = "0.1.0"
dependencies = ["httpx"]
EOF

cat > services/ingestion/worker.py <<'EOF'
import httpx


def fetch(url):
    return httpx.get(url).json()
EOF

cat > services/reporting/pom.xml <<'EOF'
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>reporting</artifactId>
  <version>1.0.0</version>
</project>
EOF

cat > go.mod <<'EOF'
module example.com/platform

go 1.22
EOF

cat > README.md <<'EOF'
# Platform

Polyglot services. The API is ASP.NET Core, notifications is Express, ingestion
is Python and reporting is Java.
EOF
