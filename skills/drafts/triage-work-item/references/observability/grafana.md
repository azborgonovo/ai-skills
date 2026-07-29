# Observability adapter: Grafana

Mechanics for corroborating a hypothesis against Grafana. Read this at Step 8 when Grafana is the available platform. Only reach for it once you already have a specific code-level hypothesis and something concrete to look for — this is corroboration, not exploration.

## Loading the tools

The `mcp__grafana__*` tools may be deferred; load the ones you need with `ToolSearch` if they aren't callable. Core query tools:

- `query_loki_logs` — log search (LogQL)
- `query_prometheus` — metrics (PromQL)
- `tempo_traceql-search` — distributed traces (TraceQL)

Call `list_datasources` first if you don't already know the relevant datasource UID — logs, metrics, and traces are usually separate datasources.

## What to query

Look for the specific error, timeout, or pattern described in the issue:
- **Logs (Loki)**: the exact error message or a request path from your hypothesis, scoped to the relevant service label and time range.
- **Metrics (Prometheus)**: an error-rate or latency series for the endpoint you suspect, to confirm the symptom is real and currently occurring.
- **Traces (Tempo)**: a slow or failing trace for the specific operation, to confirm where time or errors accumulate along the call path.

## Retention window (Step 8 gate)

Hosted Loki/Tempo retention is commonly in the 14–30 day range — check what applies to your setup if unsure. If the reported incident is older than the window, log/trace lookups will come back empty; skip rather than waste a round trip. Prometheus metrics often retain longer, so an aggregate error-rate check can still be useful when raw logs have aged out.
